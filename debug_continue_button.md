# Debug Continue Button Issue

## Problem
After plot generation completes, the continue button is not appearing in the UI.

## Root Cause Analysis

The continue button should appear when:
- `storylineDone` is `true` OR 
- `currentStage` is NOT `'init'`

After `book_init` job completes, the workflow should have:
- `storyline_done = True`
- `current_stage = "content"`

## Debugging Steps

### 1. Check Workflow State After Job Completion

Add this to your browser console after the job completes:

```javascript
// Check workflow state
fetch('http://localhost:8000/workflows/{workflow_id}')
  .then(r => r.json())
  .then(data => {
    console.log('Workflow state:', {
      currentStage: data.currentStage,
      storylineDone: data.storylineDone,
      contentDone: data.contentDone
    });
  });
```

### 2. Check Job Status

```javascript
// Check recent jobs
fetch('http://localhost:8000/workflows/{workflow_id}/jobs')
  .then(r => r.json())
  .then(jobs => {
    console.log('Recent jobs:', jobs.map(j => ({
      type: j.type,
      status: j.status,
      error: j.error
    })));
  });
```

### 3. Manual UI Refresh

If the state is correct but UI isn't updating, try manually refreshing:

```javascript
// Force UI refresh (if you have access to the component)
window.location.reload();
```

## Potential Fixes

### Fix 1: Force UI Refresh After Job Completion

In `WorkflowPage.tsx`, modify the `RunningJobProgress` onComplete callback:

```tsx
<RunningJobProgress 
  workflowId={workflowId || ''} 
  onComplete={() => {
    console.log('Job completed, refreshing workflow data...');
    loadWorkflowData();
    // Force a small delay to ensure backend state is saved
    setTimeout(() => loadWorkflowData(), 1000);
  }}
  onProgress={handleJobProgress}
/>
```

### Fix 2: Add State Validation in Backend

In `cinema/workflow/book_workflow.py`, add logging to `init()` method:

```python
# At the end of init() method, before return
logger.info(f"✅ Storyline generated for: {self.workflow_id}")
logger.info(f"   State: storyline_done={self.state.storyline_done}, current_stage={self.state.current_stage}")
logger.info(f"   Saving state to: {self.state.output_dir}")
self.save_state()
logger.info(f"   State saved successfully")
```

### Fix 3: Check State Repository

The issue might be in the state repository. Check if the state is being saved to the correct location and format.

## Quick Test

1. Start a new workflow
2. Wait for plot generation to complete
3. Check browser network tab for API calls to `/workflows/{id}`
4. Verify the response contains `storylineDone: true` and `currentStage: "content"`
5. If not, check the backend logs for state saving errors

## Expected Behavior

After `book_init` job completes:
1. Workflow state should have `storyline_done = true`, `current_stage = "content"`
2. UI should refresh and show continue button enabled
3. Continue button should call `/workflows/{id}/continue` endpoint
4. This should create a `book_content` job to generate the novel

## Immediate Workaround

If the continue button still doesn't appear, you can manually trigger content generation:

```bash
curl -X POST http://localhost:8000/workflows/{workflow_id}/continue
```

Or use the "Retry Stage" dropdown and select "Novel" to restart content generation.