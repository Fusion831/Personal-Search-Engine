import { useState } from 'react'
import './App.css'
import Chat from './components/Chat'
import FileUpload from './components/FileUpload'

function App() {
  const [messages, setMessages] = useState([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)
  const [uploadedFiles, setUploadedFiles] = useState([])

 
  const isInitialState = messages.length === 0


  const handleSendMessage = async (question) => {
    const userMessage = { id: Date.now(), text: question, sender: 'user' }
    setMessages(prev => [...prev, userMessage])
    setIsLoading(true)
    setError(null)

    
    const aiMessageId = Date.now() + 1
    const aiMessage = {
      id: aiMessageId,
      text: '',
      sender: 'ai',
      sources: null
    }
    setMessages(prev => [...prev, aiMessage])

    try {
      const response = await fetch('/api/query', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query: question }),
      })

      if (!response.ok) {
        throw new Error('Failed to get response from server')
      }

      
      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let accumulatedText = ''

      while (true) {
        const { done, value } = await reader.read()
        
        if (done) {
          break
        }

        const chunk = decoder.decode(value, { stream: true })
        const lines = chunk.split('\n')

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6) 
            
            if (data === '[DONE]') {
              
              break
            } else if (data.startsWith('[ERROR]')) {
              
              throw new Error(data.slice(8))
            } else {
              
              accumulatedText += data
              setMessages(prev => 
                prev.map(msg => 
                  msg.id === aiMessageId 
                    ? { ...msg, text: accumulatedText }
                    : msg
                )
              )
            }
          }
        }
      }

    } catch (err) {
      setError(err.message)
      
      setMessages(prev => 
        prev.map(msg => 
          msg.id === aiMessageId 
            ? { 
                ...msg, 
                text: 'Sorry, I encountered an error processing your question. Please try again.',
                isError: true 
              }
            : msg
        )
      )
    } finally {
      setIsLoading(false)
    }
  }


  const handleFileUpload = async (file) => {
    const formData = new FormData()
    formData.append('file', file)

    try {
      const response = await fetch('/api/Documents/upload', {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        throw new Error('Failed to upload file')
      }

      const data = await response.json()
      
      
      setUploadedFiles(prev => [...prev, { name: file.name, id: data.task_id }])
      
      return { success: true, data }
    } catch (err) {
      return { success: false, error: err.message }
    }
  }

  return (
    <div className="app">
      <div className={`main-container ${isInitialState ? 'initial-state' : 'conversation-state'}`}>
        <Chat 
          messages={messages}
          isLoading={isLoading}
          isInitialState={isInitialState}
          onSendMessage={handleSendMessage}
          onFileUpload={handleFileUpload}
          uploadedFiles={uploadedFiles}
        />
        
        {!isInitialState && (
          <FileUpload 
            uploadedFiles={uploadedFiles}
            onFileUpload={handleFileUpload}
          />
        )}
      </div>
    </div>
  )
}

export default App
