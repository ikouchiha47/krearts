import { useEffect, useState, useRef } from 'react';

export type JobStatus = 'not_found' | 'running' | 'completed' | 'failed';

interface JobState {
  status: JobStatus;
  started_at?: string;
  completed_at?: string;
  error?: string;
}

interface UseJobPollerOptions {
  workflowId: string;
  jobType: string; // pass job_id returned from the start endpoint
  enabled?: boolean;
  // How often to poll the status endpoint (ms)
  pollInterval?: number;
  onComplete?: () => void;
  onError?: (error: string) => void;
}

export function useJobPoller({
  workflowId,
  jobType,
  enabled = true,
  // default to 5 seconds
  pollInterval = 5000,
  onComplete,
  onError,
}: UseJobPollerOptions) {
  const [jobState, setJobState] = useState<JobState>({ status: 'not_found' });
  const timeoutRef = useRef<number | null>(null);
  const prevStatusRef = useRef<JobStatus>('not_found');
  const inFlightRef = useRef<boolean>(false);
  const onCompleteRef = useRef<(() => void) | undefined>(onComplete);
  const onErrorRef = useRef<((e: string) => void) | undefined>(onError);

  // Keep callback refs up to date without retriggering polling effect
  useEffect(() => {
    onCompleteRef.current = onComplete;
  }, [onComplete]);
  useEffect(() => {
    onErrorRef.current = onError;
  }, [onError]);

  useEffect(() => {
    // Guard: require enabled + identifiers
    if (!enabled || !workflowId || !jobType) {
      return;
    }

    const tick = async () => {
      if (!enabled || !workflowId || !jobType) return;
      if (inFlightRef.current) return; // avoid overlapping polls
      inFlightRef.current = true;

      try {
        const res = await fetch(`http://localhost:8000/jobs/${jobType}/status`);
        const data: JobState = await res.json();

        setJobState(data);

        // Callback on status change
        if (data.status !== prevStatusRef.current) {
          if (data.status === 'completed') {
            onCompleteRef.current?.();
          } else if (data.status === 'failed' && data.error) {
            onErrorRef.current?.(data.error);
          }
          prevStatusRef.current = data.status;
        }

        // Schedule next tick if still pending/running
        if (data.status !== 'completed' && data.status !== 'failed') {
          timeoutRef.current = window.setTimeout(tick, pollInterval);
        } else {
          timeoutRef.current = null;
        }
      } catch (e) {
        console.error('Failed to poll job status:', e);
        onErrorRef.current?.('Failed to poll job status');
        // stop polling on error
        if (timeoutRef.current) {
          clearTimeout(timeoutRef.current);
          timeoutRef.current = null;
        }
      } finally {
        inFlightRef.current = false;
      }
    };

    // kick off first tick
    tick();

    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
        timeoutRef.current = null;
      }
      inFlightRef.current = false;
    };
  }, [workflowId, jobType, enabled, pollInterval]);

  return jobState;
}
