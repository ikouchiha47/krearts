import React, { useState } from 'react';

interface WorkflowConfigProps {
  disabled: boolean;
  onSave: (config: { totalChapters: number; pagesPerChapter: number }) => void;
}

export const WorkflowConfig: React.FC<WorkflowConfigProps> = ({ disabled, onSave }) => {
  const [totalChapters, setTotalChapters] = useState(3);
  const [pagesPerChapter, setPagesPerChapter] = useState(8);

  const handleSave = () => {
    onSave({ totalChapters, pagesPerChapter });
  };

  return (
    <div className="space-y-4">
      <h4 className="text-xs font-bold uppercase text-[var(--ink)] border-b border-[var(--border)] pb-2 mb-3">
        ⚙️ Generation Settings
      </h4>
      
      <div className="space-y-3">
        <div>
          <label className="block text-xs font-medium text-[var(--muted)] mb-1">
            Total Chapters (for bookwriter):
          </label>
          <input
            type="number"
            min="1"
            max="50"
            className="w-full px-3 py-2 text-xs border-2 border-[var(--border)] rounded bg-[var(--paper)] text-[var(--ink)]"
            value={totalChapters}
            onChange={(e) => setTotalChapters(parseInt(e.target.value) || 15)}
            disabled={disabled}
          />
          <p className="text-xs text-[var(--muted)] mt-1">
            How many chapters the novel should have
          </p>
        </div>

        <div>
          <label className="block text-xs font-medium text-[var(--muted)] mb-1">
            Pages per Chapter (for chapterbuilder):
          </label>
          <input
            type="number"
            min="1"
            max="20"
            className="w-full px-3 py-2 text-xs border-2 border-[var(--border)] rounded bg-[var(--paper)] text-[var(--ink)]"
            value={pagesPerChapter}
            onChange={(e) => setPagesPerChapter(parseInt(e.target.value) || 8)}
            disabled={disabled}
          />
          <p className="text-xs text-[var(--muted)] mt-1">
            How many comic pages each chapter should have
          </p>
        </div>

        <button
          type="button"
          onClick={handleSave}
          disabled={disabled}
          className="w-full px-4 py-3 text-xs font-bold uppercase border-2 border-[var(--ink)] rounded bg-[var(--orange)] text-[var(--ink)] hover:bg-[var(--yellow)] transition-colors disabled:opacity-50"
        >
          Save Settings
        </button>
      </div>
    </div>
  );
};