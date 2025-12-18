import React, { useEffect, useState } from 'react';
import { useApi } from '../api/ApiProvider';
import { WorkflowSummary } from '../api/ApiClient';
import { CreateWorkflowModal } from '../components/CreateWorkflowModal';
import { WorkflowCard } from '../components/WorkflowCard';
import { Plus } from 'lucide-react';

export const DashboardPage: React.FC = () => {
  const api = useApi();
  const [workflows, setWorkflows] = useState<WorkflowSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);

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
        
        <button
          onClick={() => setShowCreateModal(true)}
          className="flex items-center gap-2 bg-[var(--orange)] text-[var(--ink)] px-6 py-3 rounded-lg font-black uppercase border-2 border-[var(--ink)] hover:bg-[var(--yellow)] transition-colors"
        >
          <Plus className="w-5 h-5" />
          NEW WORKFLOW
        </button>
      </header>

      <main className="p-8">
        <div className="max-w-7xl mx-auto">
          <h2 className="text-5xl font-black uppercase mb-8 tracking-tight">Your Stories</h2>
          
          {workflows.length === 0 ? (
            <div className="text-center py-20">
              <div className="text-6xl mb-4">📚</div>
              <p className="text-2xl font-bold uppercase tracking-wide" style={{ color: 'var(--muted)' }}>
                No workflows yet
              </p>
              <p className="text-sm mt-2 mb-6" style={{ color: 'var(--muted)' }}>
                Create your first comic to get started
              </p>
              <button
                onClick={() => setShowCreateModal(true)}
                className="bg-[var(--orange)] text-[var(--ink)] px-8 py-4 rounded-lg font-black uppercase text-lg border-2 border-[var(--ink)] hover:bg-[var(--yellow)] transition-colors"
              >
                CREATE YOUR FIRST STORY
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4">
              {workflows.map((workflow, idx) => (
                <WorkflowCard key={workflow.id} workflow={workflow} index={idx} />
              ))}
            </div>
          )}
        </div>
      </main>

      {/* Create Workflow Modal */}
      <CreateWorkflowModal 
        isOpen={showCreateModal} 
        onClose={() => setShowCreateModal(false)} 
      />
    </div>
  );
};
