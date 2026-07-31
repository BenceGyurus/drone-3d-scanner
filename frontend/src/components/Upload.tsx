import React, { useState, useRef } from 'react';
import { UploadCloud, CheckCircle, AlertTriangle } from 'lucide-react';
import { API_URL } from '../App';

interface UploadProps {
  onUploadSuccess: () => void;
}

export default function Upload({ onUploadSuccess }: UploadProps) {
  const [file, setFile] = useState<File | null>(null);
  const [name, setName] = useState('');
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setFile(e.target.files[0]);
      if (!name) {
        setName(e.target.files[0].name.split('.')[0]);
      }
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      setFile(e.dataTransfer.files[0]);
      if (!name) {
        setName(e.dataTransfer.files[0].name.split('.')[0]);
      }
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file || !name) return;

    setUploading(true);
    setError(null);

    const formData = new FormData();
    formData.append('video', file);
    formData.append('name', name);

    try {
      const response = await fetch(`${API_URL}/jobs/`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Upload failed');
      }

      onUploadSuccess();
    } catch (err: any) {
      setError(err.message || 'An error occurred during upload.');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="card upload-form">
      <h2>Start a New 3D Scan</h2>
      <p style={{ opacity: 0.8, marginBottom: '2rem' }}>Upload a drone video (.mp4, .mov, .avi) to be processed into a 3D model.</p>

      <form onSubmit={handleSubmit} style={{ width: '100%', maxWidth: '500px' }}>
        <input
          type="text"
          className="input-field"
          placeholder="Scan Name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          required
        />
        
        <div 
          className="file-drop-area"
          onClick={() => fileInputRef.current?.click()}
          onDragOver={(e) => e.preventDefault()}
          onDrop={handleDrop}
        >
          {file ? (
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '1rem' }}>
              <CheckCircle size={48} color="#34d399" />
              <span>{file.name} ({(file.size / (1024 * 1024)).toFixed(2)} MB)</span>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '1rem' }}>
              <UploadCloud size={48} color="#60a5fa" />
              <span>Click to select or drag and drop a video file</span>
            </div>
          )}
        </div>
        
        <input 
          type="file" 
          accept="video/mp4,video/quicktime,video/x-msvideo" 
          ref={fileInputRef}
          style={{ display: 'none' }}
          onChange={handleFileChange}
        />

        {error && (
          <div style={{ marginTop: '1rem', color: '#f87171', display: 'flex', alignItems: 'center', gap: '0.5rem', justifyContent: 'center' }}>
            <AlertTriangle size={18} /> {error}
          </div>
        )}

        <button 
          type="submit" 
          style={{ marginTop: '2rem', width: '100%', padding: '1rem', fontSize: '1.1rem' }}
          disabled={!file || !name || uploading}
        >
          {uploading ? (
            <span style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem' }}>
               <div className="spinner"><UploadCloud size={20} /></div> Uploading...
            </span>
          ) : 'Upload and Process'}
        </button>
      </form>
    </div>
  );
}
