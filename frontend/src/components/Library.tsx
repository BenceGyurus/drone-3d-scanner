import { useState, useEffect } from 'react';
import { API_URL, Job } from '../App';
import { Layers, Trash2, Map, RefreshCw } from 'lucide-react';

interface LibraryProps {
  onViewJob: (job: Job) => void;
}

export default function Library({ onViewJob }: LibraryProps) {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchJobs = async () => {
    try {
      const response = await fetch(`${API_URL}/jobs/`);
      const data = await response.json();
      setJobs(data);
    } catch (err) {
      console.error('Failed to fetch jobs', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchJobs();
    const interval = setInterval(fetchJobs, 10000);
    return () => clearInterval(interval);
  }, []);

  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure you want to delete this scan?')) return;
    
    try {
      await fetch(`${API_URL}/jobs/${id}`, { method: 'DELETE' });
      fetchJobs();
    } catch (err) {
      console.error('Failed to delete job', err);
    }
  };

  if (loading) {
    return <div style={{ textAlign: 'center', marginTop: '3rem' }}>Loading scans...</div>;
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h2><Layers style={{ verticalAlign: 'bottom', marginRight: '8px' }} /> Scan Library</h2>
        <button onClick={fetchJobs} style={{ padding: '0.4em 0.8em', fontSize: '0.9em', display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
          <RefreshCw size={16} /> Refresh
        </button>
      </div>

      {jobs.length === 0 ? (
        <div className="card" style={{ textAlign: 'center', marginTop: '2rem', padding: '4rem 2rem' }}>
          <p style={{ opacity: 0.7, fontSize: '1.2rem' }}>No scans available. Upload a video to get started.</p>
        </div>
      ) : (
        <div className="job-list">
          {jobs.map(job => (
            <div key={job.id} className="card job-card">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <h3 style={{ margin: 0 }}>{job.name}</h3>
                <span className={`job-status status-${job.status}`}>
                  {job.status.replace(/_/g, ' ')}
                </span>
              </div>
              
              <div style={{ opacity: 0.6, fontSize: '0.9rem' }}>
                {new Date(job.created_at).toLocaleString()}
              </div>

              {job.error_message && (
                <div style={{ color: '#f87171', fontSize: '0.9rem', marginTop: '0.5rem', background: 'rgba(239, 68, 68, 0.1)', padding: '0.5rem', borderRadius: '4px' }}>
                  {job.error_message}
                </div>
              )}

              <div style={{ display: 'flex', gap: '0.5rem', marginTop: '1rem', paddingTop: '1rem', borderTop: '1px solid rgba(255,255,255,0.1)' }}>
                {job.status === 'COMPLETED' && (
                  <button 
                    style={{ flex: 1, display: 'flex', justifyContent: 'center', gap: '0.5rem', alignItems: 'center' }} 
                    onClick={() => onViewJob(job)}
                  >
                    <Map size={16} /> View 3D
                  </button>
                )}
                <button 
                  style={{ background: 'rgba(239, 68, 68, 0.1)', color: '#f87171' }} 
                  onClick={() => handleDelete(job.id)}
                  title="Delete Scan"
                >
                  <Trash2 size={16} />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
