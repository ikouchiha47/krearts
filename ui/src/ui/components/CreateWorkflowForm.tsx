import React, { useState, useEffect } from 'react';
import { useApi } from '../api/ApiProvider';
import { useNavigate } from 'react-router-dom';

export const CreateWorkflowForm: React.FC = () => {
  const api = useApi();
  const navigate = useNavigate();
  
  const [artStyles, setArtStyles] = useState<string[]>([]);
  const [selectedStyles, setSelectedStyles] = useState<string[]>([]);
  const [requirements, setRequirements] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadArtStyles();
  }, []);

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
      
      // Navigate to workflow page (API returns workflow_id in snake_case)
      navigate(`/workflow/${job.workflow_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create workflow');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-[var(--paper)] rounded-xl p-6 border-2 border-[var(--ink)] shadow-lg">
      <h2 className="text-2xl font-black uppercase mb-6">CREATE NEW WORKFLOW</h2>
      
      <form onSubmit={handleSubmit}>
        {/* Art Styles */}
        <div className="mb-6">
          <label className="block text-sm font-bold uppercase mb-3">
            ART STYLES (Optional)
          </label>
          <div className="grid grid-cols-2 gap-2">
            {artStyles.map(style => (
              <button
                key={style}
                type="button"
                onClick={() => toggleStyle(style)}
                className={`
                  px-4 py-2 rounded-lg font-bold text-sm uppercase border-2 transition-all
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
            placeholder="e.g., A murder mystery set in 1920s Chicago during prohibition..."
            className="w-full px-4 py-3 rounded-lg border-2 border-[var(--border)] bg-[var(--surface)] text-[var(--ink)] font-mono text-sm resize-none focus:border-[var(--orange)] focus:outline-none"
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

        {/* Submit */}
        <button
          type="submit"
          disabled={loading}
          className="w-full bg-[var(--orange)] text-[var(--ink)] px-6 py-4 rounded-lg font-black uppercase text-lg border-2 border-[var(--ink)] hover:bg-[var(--yellow)] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? 'CREATING...' : 'INIT WORKFLOW'}
        </button>
      </form>
    </div>
  );
};
