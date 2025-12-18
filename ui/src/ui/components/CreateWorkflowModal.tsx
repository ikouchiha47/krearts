import React, { useState, useEffect } from 'react';
import { useApi } from '../api/ApiProvider';
import { useNavigate } from 'react-router-dom';
import { X } from 'lucide-react';

interface CreateWorkflowModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const CreateWorkflowModal: React.FC<CreateWorkflowModalProps> = ({ isOpen, onClose }) => {
  const api = useApi();
  const navigate = useNavigate();
  
  const [artStyles, setArtStyles] = useState<string[]>([]);
  const [selectedStyles, setSelectedStyles] = useState<string[]>([]);
  const [requirements, setRequirements] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen) {
      loadArtStyles();
    }
  }, [isOpen]);

  const loadArtStyles = async () => {
    try {
      const response = await fetch('http://localhost:8000/workflows/art-styles');
      const data = await response.json();
      setArtStyles(data.art_styles || []);
    } catch (err) {
      console.error('Failed to load art styles:', err);
      setArtStyles(['noir', 'cyberpunk', 'anime', 'manga', 'superhero']); // Fallback
    }
  };

  const toggleStyle = (style: string) => {
    setSelectedStyles(prev =>
      prev.includes(style)
        ? prev.filter(s => s !== style)
        : [...prev, style]
    );
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const job = await api.initBook({
        art_styles: selectedStyles.length > 0 ? selectedStyles : undefined,
        user_requirements: requirements || undefined,
      });
      
      // Navigate to workflow page
      navigate(`/workflow/${job.workflow_id}`);
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create workflow');
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    if (!loading) {
      setSelectedStyles([]);
      setRequirements('');
      setError(null);
      onClose();
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-[var(--paper)] rounded-xl border-2 border-[var(--ink)] shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b-2 border-[var(--border)]">
          <h2 className="text-2xl font-black uppercase">CREATE NEW WORKFLOW</h2>
          <button
            onClick={handleClose}
            disabled={loading}
            className="p-2 hover:bg-[var(--surface)] rounded-lg transition-colors disabled:opacity-50"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6">
          {/* Art Styles */}
          <div className="mb-6">
            <label className="block text-sm font-bold uppercase mb-3">
              ART STYLES (Optional)
            </label>
            <div className="grid grid-cols-3 gap-2">
              {artStyles.map(style => (
                <button
                  key={style}
                  type="button"
                  onClick={() => toggleStyle(style)}
                  disabled={loading}
                  className={`
                    px-3 py-2 rounded-lg font-bold text-xs uppercase border-2 transition-all disabled:opacity-50
                    ${selectedStyles.includes(style)
                      ? 'bg-[var(--orange)] border-[var(--orange)] text-[var(--ink)]'
                      : 'bg-transparent border-[var(--border)] text-[var(--muted)] hover:border-[var(--orange)]'
                    }
                  `}
                >
                  {style}
                </button>
              ))}
            </div>
            {selectedStyles.length > 0 && (
              <p className="text-xs mt-2" style={{ color: 'var(--muted)' }}>
                Selected: {selectedStyles.join(' + ')}
              </p>
            )}
          </div>

          {/* User Requirements */}
          <div className="mb-6">
            <label className="block text-sm font-bold uppercase mb-3">
              STORY REQUIREMENTS (Optional)
            </label>
            <textarea
              value={requirements}
              onChange={(e) => setRequirements(e.target.value)}
              disabled={loading}
              placeholder="e.g., A murder mystery set in 1920s Chicago during prohibition..."
              className="w-full px-4 py-3 rounded-lg border-2 border-[var(--border)] bg-[var(--surface)] text-[var(--ink)] font-mono text-sm resize-none focus:border-[var(--orange)] focus:outline-none disabled:opacity-50"
              rows={4}
            />
            <p className="text-xs mt-2" style={{ color: 'var(--muted)' }}>
              Describe the setting, era, themes, or any specific requirements
            </p>
          </div>

          {/* Quick Start Guide */}
          <div className="mb-6 p-4 rounded-lg bg-[var(--surface)] border border-[var(--border)]">
            <h3 className="text-xs font-bold uppercase mb-2" style={{ color: 'var(--muted)' }}>
              QUICK START
            </h3>
            <ul className="text-xs space-y-1" style={{ color: 'var(--muted)' }}>
              <li>• Select art style(s) or leave blank for AI to choose</li>
              <li>• Add story requirements or start fresh</li>
              <li>• Click to initialize workflow</li>
              <li>• Begin generating content</li>
            </ul>
          </div>

          {/* Error */}
          {error && (
            <div className="mb-4 p-3 rounded-lg bg-red-900/20 border border-red-500 text-red-200 text-sm">
              {error}
            </div>
          )}

          {/* Actions */}
          <div className="flex gap-3">
            <button
              type="button"
              onClick={handleClose}
              disabled={loading}
              className="flex-1 bg-transparent border-2 border-[var(--border)] text-[var(--muted)] px-6 py-3 rounded-lg font-bold uppercase hover:border-[var(--ink)] hover:text-[var(--ink)] transition-colors disabled:opacity-50"
            >
              CANCEL
            </button>
            <button
              type="submit"
              disabled={loading}
              className="flex-1 bg-[var(--orange)] text-[var(--ink)] px-6 py-3 rounded-lg font-black uppercase border-2 border-[var(--ink)] hover:bg-[var(--yellow)] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'CREATING...' : 'INIT WORKFLOW'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};