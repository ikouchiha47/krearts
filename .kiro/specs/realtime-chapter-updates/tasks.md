# Implementation Plan

- [x] 1. Extend RunningJobProgress component to support progress callbacks
  - Add optional `onProgress` prop to component interface
  - Invoke `onProgress` callback on each polling cycle with current job data
  - Ensure backward compatibility with existing usage (onProgress is optional)
  - _Requirements: 5.1, 5.2, 5.4_

- [ ]* 1.1 Write property test for callback invocation
  - **Property 1: Callback invocation consistency**
  - **Validates: Requirements 5.2**

- [ ]* 1.2 Write unit tests for RunningJobProgress
  - Test that onProgress is called on each poll cycle
  - Test that onComplete is still called on job completion
  - Test backward compatibility (component works without onProgress)
  - _Requirements: 5.1, 5.2, 5.4_

- [x] 2. Implement change detection logic in WorkflowPage
  - Add state to track last seen chapters_generated array
  - Create handleJobProgress callback that compares current vs previous chapters
  - Detect new chapters by filtering current array against last seen
  - Update last seen state when new chapters are detected
  - _Requirements: 6.1, 6.2_

- [ ]* 2.1 Write property test for change detection
  - **Property 2: Change detection accuracy**
  - **Validates: Requirements 6.1, 6.2**

- [ ]* 2.2 Write unit tests for change detection logic
  - Test detecting new chapters when array grows
  - Test detecting no changes when array is same
  - Test detecting multiple new chapters at once
  - Test edge cases (empty arrays, undefined metadata)
  - _Requirements: 6.1, 6.2_

- [x] 3. Implement intelligent data refresh triggering
  - Trigger loadWorkflowData() only when new chapters are detected
  - Add console logging for debugging (chapters detected, refresh triggered)
  - Ensure final refresh still happens on job completion
  - _Requirements: 1.2, 2.1, 6.3, 6.5_

- [ ]* 3.1 Write property test for refresh efficiency
  - **Property 3: Polling efficiency**
  - **Validates: Requirements 3.2, 6.5**

- [ ]* 3.2 Write unit tests for refresh triggering
  - Test that refresh is called when new chapters detected
  - Test that refresh is NOT called when no changes
  - Test that final refresh happens on completion
  - _Requirements: 1.2, 2.1, 6.3, 6.5_

- [x] 4. Add race condition protection to loadWorkflowData
  - Add isRefreshing state flag to prevent overlapping refreshes
  - Skip refresh if one is already in progress
  - Clear flag in finally block to ensure cleanup
  - _Requirements: 3.2_

- [ ]* 4.1 Write unit tests for race condition handling
  - Test that concurrent refresh calls are prevented
  - Test that flag is cleared after refresh completes
  - Test that flag is cleared even if refresh fails
  - _Requirements: 3.2_

- [x] 5. Preserve chapter selection during updates
  - Ensure selectedChapter state is not reset during data refresh
  - Verify chapter selection persists across multiple refreshes
  - _Requirements: 1.4_

- [ ]* 5.1 Write property test for state preservation
  - **Property 4: UI state preservation**
  - **Validates: Requirements 1.4**

- [ ]* 5.2 Write unit tests for selection preservation
  - Test that selected chapter remains after data refresh
  - Test that selection works with newly added chapters
  - _Requirements: 1.4_

- [x] 6. Update WorkflowPage to use new callback
  - Pass handleJobProgress to RunningJobProgress component
  - Ensure onComplete callback still works for final refresh
  - Test that polling starts when job is running
  - _Requirements: 1.1, 1.2, 1.5_

- [ ]* 6.1 Write integration test for end-to-end flow
  - Test that UI updates when new chapters are generated
  - Test that polling stops when job completes
  - Test that final refresh happens on completion
  - _Requirements: 1.1, 1.2, 1.3, 1.5_

- [x] 7. Add error handling for polling failures
  - Wrap polling logic in try-catch
  - Log errors but continue polling
  - Ensure interval is not cleared on error
  - _Requirements: 3.3_

- [ ]* 7.1 Write property test for error resilience
  - **Property 5: Error handling resilience**
  - **Validates: Requirements 3.3**

- [ ]* 7.2 Write unit tests for error handling
  - Test that polling continues after API error
  - Test that errors are logged
  - Test that interval is not cleared on error
  - _Requirements: 3.3_

- [x] 8. Add error handling for data refresh failures
  - Use Promise.all with individual catch handlers for each endpoint
  - Fall back to empty arrays if endpoints fail
  - Log errors but don't throw
  - Update state with whatever data succeeded
  - _Requirements: 3.3_

- [ ]* 8.1 Write unit tests for data refresh error handling
  - Test that partial failures don't break the UI
  - Test that successful endpoints still update state
  - Test that errors are logged
  - _Requirements: 3.3_

- [x] 9. Ensure cleanup on component unmount
  - Verify that useEffect cleanup clears polling interval
  - Test that no API calls are made after unmount
  - _Requirements: 3.5_

- [ ]* 9.1 Write unit tests for cleanup
  - Test that interval is cleared on unmount
  - Test that no callbacks are invoked after unmount
  - _Requirements: 3.5_

- [x] 10. Add console logging for debugging
  - Log job status on each poll
  - Log chapters_generated array
  - Log when new chapters are detected
  - Log when data refresh is triggered
  - _Requirements: All (debugging support)_

- [x] 11. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 12. Manual testing and verification
  - Start a chapter generation job
  - Verify chapters appear in sidebar within 3 seconds of completion
  - Verify no unnecessary API calls when nothing changes
  - Verify selected chapter is preserved during updates
  - Verify polling stops when job completes
  - Verify cleanup happens on navigation away
  - _Requirements: All_
