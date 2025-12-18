import React from 'react';
import { Link } from 'react-router-dom';
import { BookOpen, Loader2 } from 'lucide-react';
import { WorkflowSummary } from '../api/ApiClient';

interface WorkflowCardProps {
  workflow: WorkflowSummary;
  index: number;
}

const GRADIENTS = [
  'from-purple-500 to-pink-500',
  'from-blue-500 to-cyan-500',
  'from-orange-500 to-red-500',
  'from-green-500 to-teal-500',
  'from-yellow-500 to-orange-500',
  'from-indigo-500 to-purple-500',
];

export const WorkflowCard: React.FC<WorkflowCardProps> = ({ workflow, index }) => {
  const isGenerating = !workflow.storylineDone || !workflow.contentDone;
  const gradient = GRADIENTS[index % GRADIENTS.length];

  return (
    <Link
      to={`/workflow/${workflow.id}`}
      className="block transition-all hover:scale-105 hover:shadow-lg"
    >
      {/* Card Container - White background like e-commerce */}
      <div className="bg-white border-2 border-[var(--ink)] rounded-lg overflow-hidden shadow-md">
        {/* Cover Image - Reduced height */}
        <div className="aspect-[3/2] relative">
          <div className={`w-full h-full bg-gradient-to-br ${gradient} flex items-center justify-center`}>
            <BookOpen className="w-12 h-12 text-white" strokeWidth={2.5} />
          </div>

          {/* Spinner badge for in-progress workflows */}
          {isGenerating && (
            <div className="absolute top-3 right-3 w-8 h-8 bg-[var(--orange)] border-2 border-[var(--ink)] rounded-full flex items-center justify-center shadow-lg">
              <Loader2 className="w-4 h-4 text-white animate-spin" />
            </div>
          )}
        </div>

        {/* Metadata Section - Reduced padding */}
        <div className="p-3 bg-white">
          {/* Title */}
          <h3 className="text-sm font-black uppercase leading-tight mb-2 line-clamp-1">
            {workflow.title}
          </h3>

          {/* Status and Stats in one row */}
          <div className="flex items-center justify-between">
            <span className={`inline-block px-2 py-1 text-[10px] font-bold uppercase rounded ${
              isGenerating 
                ? 'bg-[var(--orange)] text-white' 
                : 'bg-[var(--cream)] text-[var(--ink)]'
            }`}>
              {isGenerating ? 'GEN' : workflow.currentStage}
            </span>
            
            <div className="flex items-center gap-3 text-xs font-bold">
              <span className="text-[var(--muted)]">Ch: {workflow.chaptersGenerated}</span>
              <span className="text-[var(--muted)]">Pg: {workflow.pagesGenerated}</span>
            </div>
          </div>
        </div>
      </div>
    </Link>
  );
};
