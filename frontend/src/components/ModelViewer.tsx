import '@google/model-viewer';
import { Job, API_URL } from '../App';
import { Download } from 'lucide-react';

interface ModelViewerProps {
  job: Job;
}

export default function ModelViewer({ job }: ModelViewerProps) {
  if (!job.model_path) {
    return (
      <div style={{ padding: '2rem', textAlign: 'center' }}>
        Model is not available.
      </div>
    );
  }

  const modelUrl = `${API_URL}${job.model_path}`;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
      <div className="viewer-container">
        {/* @ts-ignore - model-viewer is a web component */}
        <model-viewer
          src={modelUrl}
          camera-controls
          auto-rotate
          ar
          shadow-intensity="1"
          style={{ width: '100%', height: '100%', backgroundColor: '#111' }}
        >
        {/* @ts-ignore */}
        </model-viewer>
      </div>
      
      <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
        <a 
          href={modelUrl} 
          download 
          target="_blank"
          rel="noopener noreferrer"
          style={{ 
            display: 'inline-flex', 
            alignItems: 'center', 
            gap: '0.5rem', 
            padding: '0.6em 1.2em', 
            background: '#3b82f6', 
            color: 'white', 
            textDecoration: 'none', 
            borderRadius: '8px',
            fontWeight: 500
          }}
        >
          <Download size={18} /> Download 3D Model
        </a>
      </div>
    </div>
  );
}
