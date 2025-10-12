import { useState, useEffect, useRef } from 'react'
import styles from './Chat.module.css'
import Message from './Message'

function Chat({ messages, isLoading, isInitialState, onSendMessage, onFileUpload, uploadedFiles }) {
  const [inputText, setInputText] = useState('')
  const messagesEndRef = useRef(null)
  const fileInputRef = useRef(null)

 
  const examplePrompts = [
    "What are the main topics in my documents?",
    "Summarize the key points",
    "Find information about...",
  ]

  
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isLoading])

  const handleSubmit = (e) => {
    e.preventDefault()
    if (inputText.trim() && !isLoading) {
      onSendMessage(inputText)
      setInputText('')
    }
  }

  const handleExampleClick = (prompt) => {
    setInputText(prompt)
  }

  const handleFileChange = async (e) => {
    const file = e.target.files?.[0]
    if (file) {
      await onFileUpload(file)
    }
  }

  const handleUploadClick = () => {
    fileInputRef.current?.click()
  }

  if (isInitialState) {
    
    return (
      <div className={styles.initialContainer}>
        <h1 className={styles.initialTitle}>Ask about your documents...</h1>
        <p className={styles.initialSubtitle}>Upload documents and start asking questions</p>
        
        {/* File Upload Button */}
        <div className={styles.uploadSection}>
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf"
            onChange={handleFileChange}
            style={{ display: 'none' }}
          />
          <button 
            type="button"
            className={styles.uploadBtn}
            onClick={handleUploadClick}
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M17 8l-5-5-5 5M12 3v12"/>
            </svg>
            Upload Documents
          </button>
          {uploadedFiles && uploadedFiles.length > 0 && (
            <span className={styles.fileCount}>
              {uploadedFiles.length} file{uploadedFiles.length > 1 ? 's' : ''} uploaded
            </span>
          )}
        </div>
        
        <form className={styles.initialForm} onSubmit={handleSubmit}>
          <input
            type="text"
            className={styles.initialInput}
            placeholder="Type your question here..."
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            autoFocus
          />
          <button 
            type="submit" 
            className={styles.initialSubmitBtn}
            disabled={!inputText.trim()}
          >
            Ask
          </button>
        </form>

        <div className={styles.examplePrompts}>
          <p className={styles.exampleLabel}>Try asking:</p>
          {examplePrompts.map((prompt, index) => (
            <button
              key={index}
              className={styles.exampleBtn}
              onClick={() => handleExampleClick(prompt)}
            >
              {prompt}
            </button>
          ))}
        </div>
      </div>
    )
  }

 
  return (
    <div className={styles.chatContainer}>
      <div className={styles.messagesArea}>
        {messages.map((message, index) => {
          const isLastMessage = index === messages.length - 1
          const isStreamingMessage = isLastMessage && message.sender === 'ai' && isLoading
          return (
            <Message 
              key={message.id} 
              message={message} 
              isStreaming={isStreamingMessage}
            />
          )
        })}
        
        {isLoading && messages.length === 0 && (
          <div className={styles.loadingIndicator}>
            <div className={styles.loadingDots}>
              <span></span>
              <span></span>
              <span></span>
            </div>
            <span className={styles.loadingText}>Thinking...</span>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      <form className={styles.inputForm} onSubmit={handleSubmit}>
        <input
          type="text"
          className={styles.input}
          placeholder="Ask a follow-up question..."
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          disabled={isLoading}
        />
        <button 
          type="submit" 
          className={styles.submitBtn}
          disabled={!inputText.trim() || isLoading}
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z"/>
          </svg>
        </button>
      </form>
    </div>
  )
}

export default Chat
