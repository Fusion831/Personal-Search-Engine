import { useState, useRef } from 'react'
import styles from './FileUpload.module.css'

function FileUpload({ uploadedFiles, onFileUpload }) {
  const [isUploading, setIsUploading] = useState(false)
  const [uploadError, setUploadError] = useState(null)
  const fileInputRef = useRef(null)

  const handleUploadClick = () => {
    fileInputRef.current?.click()
  }

  const handleFileChange = async (e) => {
    const file = e.target.files?.[0]
    if (!file) return

    
    if (file.type !== 'application/pdf') {
      setUploadError('Only PDF files are supported')
      return
    }

    setIsUploading(true)
    setUploadError(null)

    const result = await onFileUpload(file)

    setIsUploading(false)

    if (!result.success) {
      setUploadError(result.error || 'Failed to upload file')
    }

    
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  return (
    <div className={styles.sidebar}>
      <div className={styles.header}>
        <h2 className={styles.title}>Documents</h2>
        <button
          className={styles.uploadBtn}
          onClick={handleUploadClick}
          disabled={isUploading}
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M17 8l-5-5-5 5M12 3v12"/>
          </svg>
          {isUploading ? 'Uploading...' : 'Upload'}
        </button>
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf"
          onChange={handleFileChange}
          style={{ display: 'none' }}
        />
      </div>

      {uploadError && (
        <div className={styles.error}>
          {uploadError}
        </div>
      )}

      <div className={styles.fileList}>
        {uploadedFiles.length === 0 ? (
          <div className={styles.emptyState}>
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
              <path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"/>
              <polyline points="13 2 13 9 20 9"/>
            </svg>
            <p>No documents uploaded yet</p>
            <span>Upload a PDF to get started</span>
          </div>
        ) : (
          uploadedFiles.map((file, index) => (
            <div key={index} className={styles.fileItem}>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"/>
                <polyline points="13 2 13 9 20 9"/>
              </svg>
              <span className={styles.fileName}>{file.name}</span>
            </div>
          ))
        )}
      </div>
    </div>
  )
}

export default FileUpload
