import { useState } from 'react';
import './App.css';
import Upload from './components/Upload';
import Library from './components/Library';
import ModelViewer from './components/ModelViewer';
import { Camera, Box } from 'lucide-react';

export type Job = {
  id: number;
  name: string;
  status: string;
  error_message?: string;
  latitude?: number;
  longitude?: number;
  model_path?: string;
  orthophoto_path?: string;
  created_at: string;
};

export const API_URL = import.meta.env.VITE_API_URL || `${window.location.protocol}//${window.location.hostname}:8000`;

function App() {
  const [activeTab, setActiveTab] = useState<'upload' | 'library'>('upload');
  const [viewingJob, setViewingJob] = useState<Job | null>(null);

  return (
    <div className="app-container">
      <header className="header">
        <h1>
          <Camera size={28} color="#60a5fa" />
          Drone 3D Scanner
        </h1>
        <div className="nav-buttons">
          <button 
            style={{ opacity: activeTab === 'upload' && !viewingJob ? 1 : 0.6 }} 
            onClick={() => { setActiveTab('upload'); setViewingJob(null); }}
          >
            New Scan
          </button>
          <button 
            style={{ opacity: activeTab === 'library' && !viewingJob ? 1 : 0.6 }} 
            onClick={() => { setActiveTab('library'); setViewingJob(null); }}
          >
            Library
          </button>
        </div>
      </header>

      <main className="main-content">
        {viewingJob ? (
          <div className="card">
             <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
               <h2><Box size={24} style={{ marginRight: '8px', verticalAlign: 'bottom' }} /> {viewingJob.name} - 3D View</h2>
               <button onClick={() => setViewingJob(null)}>Back to Library</button>
             </div>
             <ModelViewer job={viewingJob} />
          </div>
        ) : activeTab === 'upload' ? (
          <Upload onUploadSuccess={() => setActiveTab('library')} />
        ) : (
          <Library onViewJob={(job) => setViewingJob(job)} />
        )}
      </main>
    </div>
  );
}

export default App;
