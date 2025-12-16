import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useApi } from '../api/ApiProvider';
import { WorkflowSummary } from '../api/ApiClient';

export const DashboardPage: React.FC = () => {
  const api = useApi();
  const [workflows, setWorkflows] = useState<WorkflowSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadWorkflows();
  }, []);

  const loadWorkflows = async () => {
    try {
      setLoading(true);
      const data = await api.listWorkflows();
      setWorkflows(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load workflows');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-2xl font-black uppercase tracking-wider">Loading...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-2xl font-black text-[var(--red)]">Error: {error}</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen">
      <header className="comic-header px-10 py-6 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <h1 className="text-3xl">COMICS BOOK</h1>
          <span className="comic-badge px-3 py-1 rounded">
            {workflows.length} PROJECTS
          </span>
        </div>
      </header>

      <main className="p-8">
        <div className="max-w-7xl mx-auto">
          <h2 className="text-5xl font-black uppercase mb-8 tracking-tight">Your Stories</h2>
          
          {workflows.length === 0 ? (
            <div className="text-center py-20">
              <p className="text-2xl font-bold uppercase tracking-wide" style={{ color: 'var(--muted)' }}>
                No workflows yet. Create your first comic!
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {workflows.map((workflow) => (
                <Link
                  key={workflow.id}
                  to={`/workflow/${workflow.id}`}
                  className="comic-card p-6 transition-all cursor-pointer"
                >
                  <div className="flex items-start justify-between mb-4">
                    <h3 className="font-black text-2xl uppercase tracking-tight leading-tight">{workflow.title}</h3>
                    <span className="comic-badge px-2 py-1 rounded text-[10px]">
                      {workflow.currentStage.toUpperCase()}
                    </span>
                  </div>
                  
                  <div className="flex gap-6 text-base font-bold mb-4">
                    <div>
                      <span className="text-3xl font-black">{workflow.chaptersGenerated}</span>
                      <div className="text-xs uppercase tracking-wide" style={{ color: 'var(--muted)' }}>Chapters</div>
                    </div>
                    <div>
                      <span className="text-3xl font-black">{workflow.pagesGenerated}</span>
                      <div className="text-xs uppercase tracking-wide" style={{ color: 'var(--muted)' }}>Pages</div>
                    </div>
                  </div>
                  
                  <div className="text-xs font-mono" style={{ color: 'var(--muted)' }}>
                    #{workflow.id.slice(0, 8)}
                  </div>
                </Link>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
};
