import React, { useState, useEffect } from 'react';

interface ComicConfig {
  total_chapters?: number;
  pages_per_chapter: number;
  chapter_style: string;
  panels_per_page: number;
  panel_layout: string;
  panel_transitions: string;
  use_smart_compression: boolean;
  context_window: number;
  summary_window: number;
}

interface ComicConfigModalProps {
  workflowId: string;
  isOpen: boolean;
  onClose: () => void;
  onSave: (config: ComicConfig) => void;
}

const DEFAULT_CONFIG: ComicConfig = {
  pages_per_chapter: 5,
  chapter_style: 'modern_cinematic',
  panels_per_page: 4,
  panel_layout: 'dynamic',
  panel_transitions: 'hard_cuts',
  use_smart_compression: true,
  context_window: 1,
  summary_window: 2,
};

export const ComicConfigModal: React.FC<ComicConfigModalProps> = ({
  workflowId,
  isOpen,
  onClose,
  onSave,
}) => {
  const [config, setConfig] = useState<ComicConfig>(DEFAULT_CONFIG);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isOpen && workflowId) {
      loadConfig();
    }
  }, [isOpen, workflowId]);

  const loadConfig = async () => {
    try {
      const response = await fetch(`/api/workflows/book/${workflowId}/comic-config`);
      if (response.ok) {
        const data = await response.json();
        setConfig({ ...DEFAULT_CONFIG, ...data });
      }
    } catch (error) {
      console.error('Failed to load comic config:', error);
    }
  };

  const handleSave = async () => {
    setLoading(true);
    try {
      const response = await fetch(`/api/workflows/book/${workflowId}/comic-config`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config),
      });
      
      if (response.ok) {
        onSave(config);
        onClose();
      }
    } catch (error) {
      console.error('Failed to save comic config:', error);
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-2xl font-bold">Comic Generation Settings</h2>
            <button
              onClick={onClose}
              className="text-gray-500 hover:text-gray-700"
            >
              ✕
            </button>
          </div>

          <div className="space-y-6">
            {/* Chapter Controls */}
            <div className="border-b pb-4">
              <h3 className="text-lg font-semibold mb-4">📚 Chapter Controls</h3>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-2">
                    Pages per Chapter: {config.pages_per_chapter}
                  </label>
                  <input
                    type="range"
                    min="1"
                    max="25"
                    value={config.pages_per_chapter}
                    onChange={(e) => setConfig({ ...config, pages_per_chapter: parseInt(e.target.value) })}
                    className="w-full"
                  />
                  <div className="flex justify-between text-xs text-gray-500">
                    <span>1 (Short)</span>
                    <span>25 (Long)</span>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">Chapter Style</label>
                  <select
                    value={config.chapter_style}
                    onChange={(e) => setConfig({ ...config, chapter_style: e.target.value })}
                    className="w-full border rounded px-3 py-2"
                  >
                    <option value="classic_dense">Classic Dense (6-9 panels, Blueberry style)</option>
                    <option value="modern_cinematic">Modern Cinematic (3-6 panels, Akira style)</option>
                  </select>
                </div>
              </div>
            </div>

            {/* Page Controls */}
            <div className="border-b pb-4">
              <h3 className="text-lg font-semibold mb-4">📄 Page Controls</h3>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-2">
                    Panels per Page: {config.panels_per_page}
                  </label>
                  <input
                    type="range"
                    min="2"
                    max="9"
                    value={config.panels_per_page}
                    onChange={(e) => setConfig({ ...config, panels_per_page: parseInt(e.target.value) })}
                    className="w-full"
                  />
                  <div className="flex justify-between text-xs text-gray-500">
                    <span>2 (Cinematic)</span>
                    <span>9 (Dense)</span>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">Panel Layout</label>
                  <select
                    value={config.panel_layout}
                    onChange={(e) => setConfig({ ...config, panel_layout: e.target.value })}
                    className="w-full border rounded px-3 py-2"
                  >
                    <option value="dynamic">Dynamic (Varied sizes)</option>
                    <option value="grid_3x3">Grid 3×3 (9 panels, Watchmen style)</option>
                    <option value="grid_2x4">Grid 2×4 (8 panels, Classic style)</option>
                    <option value="custom">Custom</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">Panel Transitions</label>
                  <select
                    value={config.panel_transitions}
                    onChange={(e) => setConfig({ ...config, panel_transitions: e.target.value })}
                    className="w-full border rounded px-3 py-2"
                  >
                    <option value="hard_cuts">Hard Cuts (Traditional)</option>
                    <option value="smooth">Smooth (Flowing)</option>
                    <option value="cinematic">Cinematic (Film-like)</option>
                  </select>
                </div>
              </div>
            </div>

            {/* Compression Controls */}
            <div>
              <h3 className="text-lg font-semibold mb-4">⚡ Smart Compression</h3>
              
              <div className="space-y-4">
                <div className="flex items-center">
                  <input
                    type="checkbox"
                    checked={config.use_smart_compression}
                    onChange={(e) => setConfig({ ...config, use_smart_compression: e.target.checked })}
                    className="mr-2"
                  />
                  <label className="text-sm font-medium">
                    Enable Smart Compression (70% token savings)
                  </label>
                </div>

                {config.use_smart_compression && (
                  <>
                    <div>
                      <label className="block text-sm font-medium mb-2">
                        Context Window: {config.context_window} chapters
                      </label>
                      <input
                        type="range"
                        min="1"
                        max="3"
                        value={config.context_window}
                        onChange={(e) => setConfig({ ...config, context_window: parseInt(e.target.value) })}
                        className="w-full"
                      />
                      <p className="text-xs text-gray-500 mt-1">
                        Full chapters before/after target chapter
                      </p>
                    </div>

                    <div>
                      <label className="block text-sm font-medium mb-2">
                        Summary Window: {config.summary_window} chapters
                      </label>
                      <input
                        type="range"
                        min="1"
                        max="5"
                        value={config.summary_window}
                        onChange={(e) => setConfig({ ...config, summary_window: parseInt(e.target.value) })}
                        className="w-full"
                      />
                      <p className="text-xs text-gray-500 mt-1">
                        Summarized chapters before/after context
                      </p>
                    </div>
                  </>
                )}
              </div>
            </div>
          </div>

          <div className="flex justify-end gap-3 mt-6 pt-4 border-t">
            <button
              onClick={onClose}
              className="px-4 py-2 border rounded hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              onClick={handleSave}
              disabled={loading}
              className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
            >
              {loading ? 'Saving...' : 'Save Settings'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
