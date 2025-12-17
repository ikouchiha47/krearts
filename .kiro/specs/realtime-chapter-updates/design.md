# Design Document: Real-time Chapter Updates

## Overview

This feature extends the existing polling infrastructure to provide real-time updates of chapter and page data during long-running chapter generation jobs. By leveraging job metadata to detect changes and intelligently polling data endpoints only when necessary, we create a responsive user experience without requiring WebSocket infrastructure.

The solution builds on the existing `RunningJobProgress` component which already polls job status every 3 seconds. We extend this to:
1. Track the `chapters_generated` array in job metadata
2. Detect when new chapters are added
3. Trigger data endpoint refreshes only when changes occur
4. Update the UI immediately with new content

## Architecture

### Current Architecture

```
┌─────────────────┐
│ WorkflowPage    │
│                 │
│ ┌─────────────┐ │
│ │RunningJob   │ │
│ │Progress     │ │  Polls every 3s
│ └──────┬──────┘ │  ────────────────►  GET /workflows/{id}/jobs?status=running
│        │        │
│        │        │  On completion
│        └────────┼──────────────────►  loadWorkflowData()
│                 │                      ├─ GET /workflows/{id}/chapters
│                 │                      ├─ GET /workflows/{id}/pages
│                 │                      └─ GET /workflows/{id}/characters
└─────────────────┘
```

### New Architecture

```
┌─────────────────┐
│ WorkflowPage    │
│                 │
│ ┌─────────────┐ │
│ │RunningJob   │ │  Polls every 3s
│ │Progress     │ │  ────────────────►  GET /workflows/{id}/jobs?status=running
│ └──────┬──────┘ │                      │
│        │        │                      ▼
│        │        │                   Response: {
│        │        │                     metadata: {
│        │        │                       chapters_generated: [1, 2, 3]
│        │        │                     }
│        │        │                   }
│        │        │                      │
│        │        │                      ▼
│        │        │                   Compare with previous state
│        │        │                      │
│        │        │                      ▼
│        │        │                   If new chapters detected
│        │        │  ────────────────►  loadWorkflowData()
│        │        │                      ├─ GET /workflows/{id}/chapters
│        │        │                      ├─ GET /workflows/{id}/pages
│        │        │                      └─ GET /workflows/{id}/characters
│        │        │
│        │        │  On completion
│        └────────┼──────────────────►  loadWorkflowData() (final refresh)
│                 │
└─────────────────┘
```

## Components and Interfaces

### 1. RunningJobProgress Component (Modified)

**Current Interface:**
```typescript
interface RunningJobProgressProps {
  workflowId: string;
  onComplete?: () => void;
}
```

**New Interface:**
```typescript
interface RunningJobProgressProps {
  workflowId: string;
  onComplete?: () => void;
  onProgress?: (job: Job) => void;  // NEW: Called on each poll cycle
}

interface Job {
  id: string;
  type: string;
  status: string;
  error?: string;
  metadata: {
    chapters_generated?: number[];  // Tracks completed chapters
    total_generated?: number;
    output_dir?: string;
  };
  progress?: JobProgress;
  seconds_since_update: number;
}
```

**Behavior:**
- Polls `/workflows/{id}/jobs?status=running` every 3 seconds (unchanged)
- On each poll, invokes `onProgress(job)` callback with current job data (new)
- On completion, invokes `onComplete()` callback (unchanged)
- Cleans up interval on unmount (unchanged)

### 2. WorkflowPage Component (Modified)

**New State:**
```typescript
const [lastSeenChapters, setLastSeenChapters] = useState<number[]>([]);
```

**New Callback:**
```typescript
const handleJobProgress = useCallback((job: Job) => {
  const currentChapters = job.metadata?.chapters_generated || [];
  
  // Detect new chapters by comparing arrays
  const newChapters = currentChapters.filter(
    ch => !lastSeenChapters.includes(ch)
  );
  
  if (newChapters.length > 0) {
    console.log(`New chapters detected: ${newChapters.join(', ')}`);
    
    // Update last seen state
    setLastSeenChapters(currentChapters);
    
    // Refresh data to get new chapters/pages
    loadWorkflowData();
  }
}, [lastSeenChapters, loadWorkflowData]);
```

**Updated Usage:**
```typescript
<RunningJobProgress 
  workflowId={workflowId || ''} 
  onComplete={loadWorkflowData}
  onProgress={handleJobProgress}  // NEW
/>
```

### 3. Backend Job Metadata (Existing)

The backend already provides the necessary metadata. No changes required.

**Worker Updates Job Metadata:**
```python
# In cinema/server/worker.py - book_chapters job handler
job.metadata.update({
    "chapters_generated": result.get("chapters", []),  # e.g., [1, 2, 3]
    "total_generated": result.get("total_generated"),
    "output_dir": result.get("output_dir"),
})
```

**API Returns Job with Metadata:**
```json
{
  "id": "job-123",
  "workflow_id": "abc123",
  "type": "book_chapters",
  "status": "running",
  "metadata": {
    "chapters_generated": [1, 2, 3],
    "total_generated": 3,
    "output_dir": "./output/book_abc123"
  },
  "seconds_since_update": 45
}
```

## Data Models

### Job Response (Existing)

```typescript
interface Job {
  id: string;
  workflow_id: string;
  type: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled' | 'aborted';
  error?: string;
  metadata: {
    chapters_generated?: number[];
    total_generated?: number;
    output_dir?: string;
    pages_generated?: number[];
    // ... other metadata fields
  };
  progress?: {
    current_stage: string;
    stage_message: string;
    retry_count: number;
    has_storyline: boolean;
    has_screenplay: boolean;
    storyline_length: number;
  };
  seconds_since_update: number;
}
```

### Chapter Data (Existing)

```typescript
interface Chapter {
  chapterNumber: number;
  title: string;
  scenes: number;
  pages: number;
}
```

### Page Data (Existing)

```typescript
interface Page {
  number: number;
  chapterNumber: number;
  sceneNumber: number;
  pageInScene: number;
  description: string;
  imageUrl: string | null;
}
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Change Detection Accuracy
*For any* two consecutive job status polls, if the `chapters_generated` array differs, then the system should detect exactly those new chapter numbers that were added.

**Validates: Requirements 6.1, 6.2**

### Property 2: Data Refresh Trigger
*For any* detected new chapter, the system should trigger exactly one data refresh call to load the new chapter and page data.

**Validates: Requirements 1.2, 2.1, 6.3**

### Property 3: UI State Preservation
*For any* data refresh during polling, if the user has a chapter selected, then after the refresh completes, the same chapter should remain selected.

**Validates: Requirements 1.3**

### Property 4: Polling Efficiency
*For any* polling cycle where no new chapters are detected, the system should not make additional calls to the chapters or pages endpoints.

**Validates: Requirements 3.2, 6.5**

### Property 5: Cleanup on Unmount
*For any* component unmount or navigation away from the workflow page, all polling intervals should be cleared and no further API calls should be made.

**Validates: Requirements 3.5**

### Property 6: Final Refresh on Completion
*For any* job that transitions from "running" to "completed", the system should perform exactly one final data refresh regardless of whether new chapters were detected in the last poll.

**Validates: Requirements 1.5**

## Error Handling

### Polling Errors

**Scenario:** Job status endpoint fails during polling

**Handling:**
```typescript
try {
  const response = await fetch(`/workflows/${workflowId}/jobs?status=running`);
  if (!response.ok) {
    console.error('Failed to poll jobs:', response.statusText);
    // Continue polling - don't break the interval
    return;
  }
  // ... process response
} catch (error) {
  console.error('Failed to poll jobs:', error);
  // Continue polling - don't break the interval
}
```

### Data Refresh Errors

**Scenario:** Chapters/pages endpoint fails during refresh

**Handling:**
```typescript
const loadWorkflowData = async () => {
  try {
    const [wf, chs, pgs, chars] = await Promise.all([
      api.getWorkflow(workflowId),
      api.listChapters(workflowId).catch(() => []),  // Fallback to empty
      api.listPages(workflowId).catch(() => []),      // Fallback to empty
      api.listCharacters(workflowId).catch(() => []), // Fallback to empty
    ]);
    // Update state with whatever succeeded
    setWorkflow(wf);
    setChapters(chs);
    setPages(pgs);
    setCharacters(chars);
  } catch (err) {
    console.error('Failed to load workflow:', err);
    // Don't throw - allow polling to continue
  }
};
```

### Race Conditions

**Scenario:** Multiple data refreshes triggered in quick succession

**Handling:**
Use a debounce or flag to prevent overlapping refreshes:

```typescript
const [isRefreshing, setIsRefreshing] = useState(false);

const loadWorkflowData = async () => {
  if (isRefreshing) {
    console.log('Refresh already in progress, skipping');
    return;
  }
  
  setIsRefreshing(true);
  try {
    // ... load data
  } finally {
    setIsRefreshing(false);
  }
};
```

## Testing Strategy

### Unit Tests

**Test 1: Change Detection Logic**
```typescript
describe('handleJobProgress', () => {
  it('should detect new chapters when array grows', () => {
    const lastSeen = [1, 2];
    const current = [1, 2, 3, 4];
    const newChapters = current.filter(ch => !lastSeen.includes(ch));
    expect(newChapters).toEqual([3, 4]);
  });
  
  it('should detect no changes when array is same', () => {
    const lastSeen = [1, 2, 3];
    const current = [1, 2, 3];
    const newChapters = current.filter(ch => !lastSeen.includes(ch));
    expect(newChapters).toEqual([]);
  });
});
```

**Test 2: Callback Invocation**
```typescript
describe('RunningJobProgress', () => {
  it('should call onProgress on each poll cycle', async () => {
    const onProgress = jest.fn();
    render(<RunningJobProgress workflowId="test" onProgress={onProgress} />);
    
    await waitFor(() => {
      expect(onProgress).toHaveBeenCalled();
    }, { timeout: 4000 });
  });
  
  it('should call onComplete when job completes', async () => {
    const onComplete = jest.fn();
    // Mock job transitioning to completed
    render(<RunningJobProgress workflowId="test" onComplete={onComplete} />);
    
    await waitFor(() => {
      expect(onComplete).toHaveBeenCalledTimes(1);
    });
  });
});
```

**Test 3: State Preservation**
```typescript
describe('WorkflowPage chapter selection', () => {
  it('should preserve selected chapter after data refresh', async () => {
    const { getByText } = render(<WorkflowPage />);
    
    // Select chapter 2
    fireEvent.click(getByText('Chapter 2'));
    expect(selectedChapter).toBe(2);
    
    // Trigger data refresh
    await act(async () => {
      await loadWorkflowData();
    });
    
    // Chapter 2 should still be selected
    expect(selectedChapter).toBe(2);
  });
});
```

### Integration Tests

**Test 1: End-to-End Polling Flow**
```typescript
describe('Real-time chapter updates', () => {
  it('should update UI when new chapters are generated', async () => {
    // Mock API responses
    let chaptersGenerated = [1];
    mockJobsEndpoint(() => ({
      metadata: { chapters_generated: chaptersGenerated }
    }));
    
    const { findByText } = render(<WorkflowPage />);
    
    // Wait for initial render
    await findByText('Chapter 1');
    
    // Simulate backend generating chapter 2
    chaptersGenerated = [1, 2];
    
    // Wait for polling to detect and refresh
    await findByText('Chapter 2', {}, { timeout: 5000 });
  });
});
```

**Test 2: Polling Efficiency**
```typescript
describe('Polling efficiency', () => {
  it('should not call data endpoints when no changes detected', async () => {
    const chaptersEndpoint = jest.fn();
    mockChaptersEndpoint(chaptersEndpoint);
    
    // Mock job with static chapters_generated
    mockJobsEndpoint(() => ({
      metadata: { chapters_generated: [1, 2, 3] }
    }));
    
    render(<WorkflowPage />);
    
    // Wait for initial load
    await waitFor(() => expect(chaptersEndpoint).toHaveBeenCalledTimes(1));
    
    // Wait for 2 more poll cycles (6 seconds)
    await new Promise(resolve => setTimeout(resolve, 6000));
    
    // Should not have called chapters endpoint again
    expect(chaptersEndpoint).toHaveBeenCalledTimes(1);
  });
});
```

### Property-Based Tests

Property-based tests will use `fast-check` library for TypeScript to verify universal properties across many random inputs.

**Property Test 1: Change Detection Correctness**
```typescript
import fc from 'fast-check';

describe('Property: Change detection', () => {
  it('should correctly identify new chapters for any array pair', () => {
    fc.assert(
      fc.property(
        fc.array(fc.integer({ min: 1, max: 100 })),  // lastSeen
        fc.array(fc.integer({ min: 1, max: 100 })),  // current
        (lastSeen, current) => {
          const newChapters = current.filter(ch => !lastSeen.includes(ch));
          
          // Property: Every new chapter should be in current but not in lastSeen
          return newChapters.every(ch => 
            current.includes(ch) && !lastSeen.includes(ch)
          );
        }
      ),
      { numRuns: 100 }
    );
  });
});
```

**Property Test 2: Data Refresh Idempotence**
```typescript
describe('Property: Data refresh idempotence', () => {
  it('should produce same result when called multiple times', () => {
    fc.assert(
      fc.property(
        fc.string(),  // workflowId
        async (workflowId) => {
          const result1 = await loadWorkflowData(workflowId);
          const result2 = await loadWorkflowData(workflowId);
          
          // Property: Multiple calls should return equivalent data
          return JSON.stringify(result1) === JSON.stringify(result2);
        }
      ),
      { numRuns: 50 }
    );
  });
});
```

## Performance Considerations

### Polling Frequency

- **Current:** 3 seconds
- **Impact:** Acceptable for real-time feel without overwhelming the server
- **Rationale:** Chapters take 30-60 seconds to generate, so 3-second polling provides ~10-20 updates per chapter

### Data Refresh Cost

- **Chapters endpoint:** Returns lightweight JSON (~1-5 KB per chapter)
- **Pages endpoint:** Returns lightweight JSON (~1-2 KB per page)
- **Total per refresh:** ~10-50 KB depending on content
- **Frequency:** Only when new chapters detected (not every poll)

### Memory Management

- **State tracking:** Single array of chapter numbers (~100 bytes)
- **Cleanup:** Intervals cleared on unmount
- **No memory leaks:** All callbacks use `useCallback` with proper dependencies

## Alternative Approaches Considered

### 1. WebSockets

**Pros:**
- True real-time updates
- Server can push updates immediately

**Cons:**
- Requires WebSocket infrastructure (not currently implemented)
- More complex to maintain
- Overkill for 3-second update frequency
- Requires connection management, reconnection logic

**Decision:** Rejected - polling is simpler and sufficient

### 2. Server-Sent Events (SSE)

**Pros:**
- Simpler than WebSockets
- One-way server-to-client updates

**Cons:**
- Still requires new backend infrastructure
- Browser compatibility issues
- Not necessary for 3-second updates

**Decision:** Rejected - polling is simpler

### 3. Continuous Data Polling

**Pros:**
- Simplest implementation
- No change detection needed

**Cons:**
- Wasteful - polls data endpoints even when nothing changed
- Higher server load
- Unnecessary network traffic

**Decision:** Rejected - intelligent polling with change detection is more efficient

## Implementation Notes

### Backward Compatibility

The changes are fully backward compatible:
- `onProgress` callback is optional
- Existing `onComplete` behavior unchanged
- No breaking changes to props or APIs

### Deployment

No backend changes required - all changes are frontend-only:
1. Update `RunningJobProgress.tsx`
2. Update `WorkflowPage.tsx`
3. Deploy frontend bundle

### Monitoring

Add console logging for debugging:
```typescript
console.log(`[Polling] Job status: ${job.status}`);
console.log(`[Polling] Chapters generated: ${job.metadata?.chapters_generated}`);
console.log(`[Polling] New chapters detected: ${newChapters.join(', ')}`);
console.log(`[Polling] Triggering data refresh`);
```

## Future Enhancements

### 1. Optimistic UI Updates

Show placeholder chapter cards immediately when new chapters are detected, before data loads:

```typescript
if (newChapters.length > 0) {
  // Add placeholder chapters
  setChapters(prev => [
    ...prev,
    ...newChapters.map(num => ({
      chapterNumber: num,
      title: 'Loading...',
      scenes: 0,
      pages: 0,
      isLoading: true
    }))
  ]);
  
  // Then load real data
  loadWorkflowData();
}
```

### 2. Granular Page Updates

Track individual page generation within chapters:

```typescript
interface JobMetadata {
  chapters_generated: number[];
  pages_generated: number[];  // Track individual pages
}
```

### 3. Progress Animations

Animate chapter cards sliding in when new chapters appear:

```typescript
<div className={`chapter-card ${isNew ? 'slide-in' : ''}`}>
  {/* chapter content */}
</div>
```

### 4. Toast Notifications

Show toast when new chapters complete:

```typescript
if (newChapters.length > 0) {
  toast.success(`Chapter ${newChapters.join(', ')} completed!`);
}
```
