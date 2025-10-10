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

      const data = await response.json()
      
      
      if (data.error) {
        throw new Error(data.error)
      }
      
      
      const aiMessage = {
        id: Date.now() + 1,
        text: data.answer || 'No answer provided',
        sender: 'ai',
        sources: data.source_chunks
      }
      setMessages(prev => [...prev, aiMessage])
    } catch (err) {
      setError(err.message)
      
      const errorMessage = {
        id: Date.now() + 1,
        text: 'Sorry, I encountered an error processing your question. Please try again.',
        sender: 'ai',
        isError: true
      }
      setMessages(prev => [...prev, errorMessage])
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
