import React, { useEffect, useState } from 'react';
import { useApi } from '../api/ApiProvider';
import { WorkflowSummary } from '../api/ApiClient';
import { CreateWorkflowForm } from '../components/CreateWorkflowForm';
import { WorkflowCard } from '../components/WorkflowCard';

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
          <div className="grid grid-cols-[1fr_400px] gap-8">
            {/* Left: Workflows List */}
            <div>
              <h2 className="text-5xl font-black uppercase mb-8 tracking-tight">Your Stories</h2>
              
              {workflows.length === 0 ? (
                <div className="text-center py-20">
                  <div className="text-6xl mb-4">📚</div>
                  <p className="text-2xl font-bold uppercase tracking-wide" style={{ color: 'var(--muted)' }}>
                    No workflows yet
                  </p>
                  <p className="text-sm mt-2" style={{ color: 'var(--muted)' }}>
                    Create your first comic using the panel on the right →
                  </p>
                </div>
              ) : (
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                  {workflows.map((workflow, idx) => (
                    <WorkflowCard key={workflow.id} workflow={workflow} index={idx} />
                  ))}
              </div>
            )}
          </div>

          {/* Right: Create Workflow Form */}
          <div>
            <CreateWorkflowForm />
          </div>
        </div>
      </div>
    </main>
    </div>
  );
};
