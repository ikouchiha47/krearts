import React, { useState } from 'react';
import { ComicConfigModal } from './ComicConfigModal';

interface ComicConfigButtonProps {
  workflowId: string;
  className?: string;
}

export const ComicConfigButton: React.FC<ComicConfigButtonProps> = ({
  workflowId,
  className = '',
}) => {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [config, setConfig] = useState({
    pages_per_chapter: 5,
    panels_per_page: 4,
    panel_layout: 'dynamic',
    use_smart_compression: true,
  });

  const handleConfigSave = (newConfig: any) => {
    setConfig(newConfig);
    // You might want to trigger a refresh of the UI here
  };

  return (
    <>
      <button
        onClick={() => setIsModalOpen(true)}
        className={`flex items-center gap-2 px-4 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors ${className}`}
      >
        <span>⚙️</span>
        <span>Comic Settings</span>
      </button>

      {/* Config Summary */}
      <div className="mt-2 text-xs text-gray-600 space-y-1">
        <div className="flex justify-between">
          <span>Pages/Chapter:</span>
          <span className="font-medium">{config.pages_per_chapter}</span>
        </div>
        <div className="flex justify-between">
          <span>Panels/Page:</span>
          <span className="font-medium">{config.panels_per_page}</span>
        </div>
        <div className="flex justify-between">
          <span>Layout:</span>
          <span className="font-medium capitalize">{config.panel_layout}</span>
        </div>
        <div className="flex justify-between">
          <span>Compression:</span>
          <span className="font-medium">{config.use_smart_compression ? '✅' : '❌'}</span>
        </div>
      </div>

      <ComicConfigModal
        workflowId={workflowId}
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSave={handleConfigSave}
      />
    </>
  );
};