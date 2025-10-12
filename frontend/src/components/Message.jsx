import styles from './Message.module.css'
import ReactMarkdown from 'react-markdown'

function Message({ message }) {
  const isUser = message.sender === 'user'
  const isError = message.isError

  return (
    <div className={`${styles.messageWrapper} ${isUser ? styles.userWrapper : styles.aiWrapper}`}>
      <div className={`${styles.message} ${isUser ? styles.userMessage : styles.aiMessage} ${isError ? styles.errorMessage : ''}`}>
        <div className={styles.messageContent}>
          {isUser ? (
            message.text
          ) : (
            <ReactMarkdown>{message.text}</ReactMarkdown>
          )}
        </div>
      </div>
    </div>
  )
}

export default Message
