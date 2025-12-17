import React, { useEffect, useState } from 'react';

interface JobProgress {
  current_stage: string;
  stage_message: string;
  retry_count: number;
  has_storyline: boolean;
  has_screenplay: boolean;
  storyline_length: number;
}

interface Job {
  id: string;
  type: string;
  status: string;
  error?: string;
  progress?: JobProgress;
  seconds_since_update: number;
  metadata?: {
    chapters_generated?: number[];
    total_generated?: number;
    output_dir?: string;
    [key: string]: any;
  };
}

interface RunningJobProgressProps {
  workflowId: string;
  onComplete?: () => void;
  onProgress?: (job: Job) => void;
}

export const RunningJobProgress: React.FC<RunningJobProgressProps> = ({ workflowId, onComplete, onProgress }) => {
  const [runningJob, setRunningJob] = useState<Job | null>(null);
  const [failedJob, setFailedJob] = useState<Job | null>(null);

  useEffect(() => {
    if (!workflowId) return;

    let previousRunningJobId: string | null = null;

    const pollJobs = async () => {
      try {
        const response = await fetch(`http://localhost:8000/workflows/${workflowId}/jobs?status=running`);
        if (response.ok) {
          const jobs: Job[] = await response.json();
          const running = jobs.find(j => j.status === 'running');
          
          if (running) {
            setRunningJob(running);
            setFailedJob(null);
            previousRunningJobId = running.id;
            
            // Invoke onProgress callback with current job data
            if (onProgress) {
              onProgress(running);
            }
          } else {
            // Check for recent failures
            const allResponse = await fetch(`http://localhost:8000/workflows/${workflowId}/jobs`);
            if (allResponse.ok) {
              const allJobs: Job[] = await allResponse.json();
              const failed = allJobs.find(j => j.status === 'failed');
              
              if (failed && !previousRunningJobId) {
                setFailedJob(failed);
              } else if (previousRunningJobId) {
                // Job completed
                setRunningJob(null);
                previousRunningJobId = null;
                if (onComplete) onComplete();
              }
            }
          }
        }
      } catch (error) {
        console.error('Failed to poll jobs:', error);
      }
    };

    // Poll immediately
    pollJobs();

    // Then poll every 3 seconds
    const interval = setInterval(pollJobs, 3000);

    return () => clearInterval(interval);
  }, [workflowId, onComplete, onProgress]); // Add callbacks to dependencies

  if (failedJob) {
    return (
      <div className="mx-10 my-4 p-4 bg-[var(--red)] border-2 border-[var(--ink)] rounded">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-2xl">❌</span>
            <div>
              <div className="font-black uppercase text-sm">Job Failed: {failedJob.type}</div>
              <div className="text-xs font-bold mt-1">{failedJob.error || 'Unknown error'}</div>
            </div>
          </div>
          <button
            onClick={async () => {
              try {
                const response = await fetch(`http://localhost:8000/jobs/${failedJob.id}`, {
                  method: 'PATCH',
                  headers: { 'Content-Type': 'application/json' },
                  body: JSON.stringify({ action: 'retry' }),
                });
                if (response.ok) {
                  setFailedJob(null);
                  if (onComplete) onComplete();
                }
              } catch (error) {
                alert('Failed to retry job');
              }
            }}
            className="px-4 py-2 text-xs font-bold uppercase border-2 border-[var(--ink)] rounded hover:bg-[var(--orange)] transition-colors"
          >
            🔄 Retry
          </button>
        </div>
      </div>
    );
  }

  if (!runningJob) return null;

  const progress = runningJob.progress;
  const jobTypeLabels: Record<string, string> = {
    book_init: 'Initializing Story',
    book_content: 'Generating Content',
    book_chapters: 'Generating Chapters',
    book_pages: 'Generating Pages',
    character_generation: 'Generating Characters',
  };

  return (
    <div className="mx-10 my-4 p-4 bg-[var(--yellow)] border-2 border-[var(--ink)] rounded">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="animate-spin text-2xl">⏳</div>
          <div>
            <div className="font-black uppercase text-sm">
              {jobTypeLabels[runningJob.type] || runningJob.type}
            </div>
            {progress && (
              <div className="text-xs font-bold mt-1">
                {progress.stage_message}
                {progress.retry_count > 0 && ` (Attempt ${progress.retry_count + 1})`}
              </div>
            )}
            {!progress && (
              <div className="text-xs font-bold mt-1">Processing...</div>
            )}
          </div>
        </div>
        <div className="text-xs font-bold" style={{ color: 'var(--muted)' }}>
          Running for {Math.floor(runningJob.seconds_since_update / 60)}m {runningJob.seconds_since_update % 60}s
        </div>
      </div>
      
      {/* Progress details */}
      {progress && (
        <div className="mt-3 pt-3 border-t-2 border-[var(--ink)] flex gap-6 text-xs font-bold">
          <div className="flex items-center gap-2">
            <span>{progress.has_storyline ? '✅' : '⏳'}</span>
            <span>Storyline {progress.storyline_length > 0 && `(${Math.floor(progress.storyline_length / 1000)}k chars)`}</span>
          </div>
          <div className="flex items-center gap-2">
            <span>{progress.has_screenplay ? '✅' : '⏳'}</span>
            <span>Novel</span>
          </div>
          <div className="flex items-center gap-2">
            <span>📍</span>
            <span className="uppercase">{progress.current_stage}</span>
          </div>
        </div>
      )}
    </div>
  );
};
