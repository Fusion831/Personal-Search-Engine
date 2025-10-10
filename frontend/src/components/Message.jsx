import styles from './Message.module.css'

function Message({ message }) {
  const isUser = message.sender === 'user'
  const isError = message.isError

  return (
    <div className={`${styles.messageWrapper} ${isUser ? styles.userWrapper : styles.aiWrapper}`}>
      <div className={`${styles.message} ${isUser ? styles.userMessage : styles.aiMessage} ${isError ? styles.errorMessage : ''}`}>
        <div className={styles.messageContent}>
          {message.text}
        </div>
      </div>
    </div>
  )
}

export default Message
