import React, { useState } from 'react';

function FileUpload() {
  
  const [files, setFiles] = useState(['Daksh_Resume.pdf']);

  const handleUploadClick = () => {
    // TODO: Implement file upload functionality
    console.log('Upload button clicked');
  };

  return (
    <div className="file-upload-container">
      <h2>My Documents</h2>
      
      <button 
        className="upload-button"
        onClick={handleUploadClick}
      >
        Upload File
      </button>

      <div className="file-list">
        <h3>Uploaded Files</h3>
        {files.length === 0 ? (
          <p>No files uploaded yet.</p>
        ) : (
          <ul>
            {files.map((fileName, index) => (
              <li key={index}>
                {fileName}
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}

export default FileUpload;
