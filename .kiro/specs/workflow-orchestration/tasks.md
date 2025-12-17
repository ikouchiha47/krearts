# Workflow Orchestration & Retry System - Implementation Tasks

## Task 1: Fix Validator Recursion Bug (CRITICAL)

- [ ] 1.1 Remove `_get_blocked_actions` call from `validate_operation` method
  - Remove line 133 in validator.py that calls `_get_blocked_actions`
  - Update ValidationResult to not include `blocked_actions` field
  - _Requirements: 7.1, 7.2, 7.3_

- [ ] 1.2 Rewrite `_get_blocked_actions` to check prerequisites directly
  - Iterate through PREREQUISITES dict
  - Check each prerequisite flag directly on WorkflowState
  - Do NOT call validate_operation
  - Return list of blocked operation names
  - _Requirements: 7.2, 7.4, 7.5_

- [ ] 1.3 Test validator fix
  - Test GET /workflows/{workflow_id} returns successfully
  - Verify no recursion errors in logs
  - Verify blocked_actions list is correct
  - _Requirements: 7.3_

## Task 2: Create WorkflowOrchestrator Service

- [ ] 2.1 Create `cinema/workflow/orchestrator.py` with WorkflowOrchestrator class
  - Initialize with workflow_id, context, job_repo, storage
  - Add method to determine if operation is flow-based
  - Add method to load both WorkflowState and StoryBuilderState
  - _Requirements: 8.1, 8.2_

- [ ] 2.2 Implement `continue_workflow` method
  - Load WorkflowState
  - Determine next operation based on state flags
  - Create appropriate job
  - Return job for polling
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 8.2_

- [ ] 2.3 Implement `retry_stage` method
  - Load WorkflowState to get current_stage
  - Find existing jobs for that stage
  - Mark old jobs as "aborted"
  - Create new job for the stage
  - Reset StoryBuilderState if flow-based
  - Return new job
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [ ] 2.4 Implement `retry_job` method
  - Load job by job_id
  - Validate job status (failed or stuck)
  - Create new job with same type/metadata
  - Mark old job as "aborted"
  - Increment retry_count
  - Return new job
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

- [ ] 2.5 Add flow-based operation handling
  - Method to resume StoryBuilder flow with correct state
  - Method to map WorkflowStage to StoryBuilderState
  - Handle flow state restoration
  - _Requirements: 1.2, 1.5, 8.4_

- [ ] 2.6 Add non-flow operation handling
  - Method to call direct generation functions
  - Handle character generation
  - Handle chapter generation
  - Handle page generation
  - _Requirements: 1.3, 1.4, 8.4_

## Task 3: Update Job Model and Repository

- [ ] 3.1 Add "aborted" status to Job model
  - Update Job status type to include "aborted"
  - Update job repository to handle aborted status
  - _Requirements: 2.1_

- [ ] 3.2 Add job creation helper that marks old jobs as aborted
  - Method: `create_job_and_abort_previous`
  - Find previous jobs of same type for workflow
  - Mark them as aborted
  - Create new job
  - _Requirements: 2.1, 2.2_

- [ ] 3.3 Update job listing to include stuck detection
  - Already implemented in controllers.py
  - Verify it works correctly
  - _Requirements: 2.5_

## Task 4: Add Workflow-Level API Endpoints

- [ ] 4.1 Add POST /workflows/{workflow_id}/continue endpoint
  - Use WorkflowOrchestrator.continue_workflow
  - Return job_id and status
  - Handle workflow not found
  - _Requirements: 3.1, 3.6, 9.1, 9.2_

- [ ] 4.2 Add POST /workflows/{workflow_id}/retry-stage endpoint
  - Use WorkflowOrchestrator.retry_stage
  - Return new job_id
  - Handle workflow not found
  - _Requirements: 4.1, 4.5, 9.1_

- [ ] 4.3 Update PATCH /jobs/{job_id} to use orchestrator
  - Replace inline retry logic with WorkflowOrchestrator.retry_job
  - Keep same API contract
  - _Requirements: 6.1, 6.5_

## Task 5: Update Specific Operation Endpoints

- [ ] 5.1 Update POST /workflows/{workflow_id}/characters/generate
  - Use WorkflowOrchestrator for validation and job creation
  - Ensure WorkflowState is updated on completion
  - _Requirements: 5.1, 5.4, 5.5_

- [ ] 5.2 Update POST /workflows/{workflow_id}/chapters/generate
  - Use WorkflowOrchestrator for validation and job creation
  - Ensure WorkflowState is updated on completion
  - _Requirements: 5.2, 5.4, 5.5_

- [ ] 5.3 Update POST /workflows/{workflow_id}/pages/generate
  - Use WorkflowOrchestrator for validation and job creation
  - Ensure WorkflowState is updated on completion
  - _Requirements: 5.3, 5.4, 5.5_

## Task 6: Update Worker to Handle Aborted Jobs

- [ ] 6.1 Update worker to skip "aborted" jobs
  - Check job status before processing
  - Skip if status is "aborted"
  - Log skip event
  - _Requirements: 2.1_

- [ ] 6.2 Update worker to mark old jobs as aborted when starting new one
  - When processing a job, check for other running jobs of same type
  - Mark them as aborted
  - Continue with current job
  - _Requirements: 2.1_

## Task 7: Update BookWorkflowService to Use Orchestrator

- [ ] 7.1 Refactor BookWorkflowService.init to use orchestrator
  - Keep same API contract
  - Delegate to orchestrator
  - _Requirements: 8.2, 8.3_

- [ ] 7.2 Refactor BookWorkflowService.generate_content to use orchestrator
  - Keep same API contract
  - Delegate to orchestrator
  - _Requirements: 8.2, 8.3_

- [ ] 7.3 Refactor BookWorkflowService.generate_chapters to use orchestrator
  - Keep same API contract
  - Delegate to orchestrator
  - _Requirements: 8.2, 8.3_

## Task 8: Testing and Validation

- [ ] 8.1 Test workflow continue from each stage
  - Test continue from init (no storyline)
  - Test continue from content (storyline done)
  - Test continue from characters (content done)
  - Test continue from chapters (characters done)
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [ ] 8.2 Test stage retry for each stage
  - Test retry init stage
  - Test retry content stage
  - Test retry character generation
  - Test retry chapter generation
  - Verify old jobs marked as aborted
  - _Requirements: 4.1, 4.2, 4.3, 4.4_

- [ ] 8.3 Test job-level retry
  - Create failed job
  - Retry by job_id
  - Verify new job created
  - Verify old job marked as aborted
  - _Requirements: 6.1, 6.2, 6.3, 6.4_

- [ ] 8.4 Test workflow not found scenarios
  - Test GET with non-existent workflow_id
  - Test continue with non-existent workflow_id
  - Verify 404 responses
  - _Requirements: 9.1, 9.2_

## Task 9: Documentation

- [ ] 9.1 Update API_ENDPOINTS_REFERENCE.md
  - Document new continue endpoint
  - Document new retry-stage endpoint
  - Document updated job retry endpoint
  - Include examples

- [ ] 9.2 Update JOB_RETRY_API.md
  - Document orchestrator architecture
  - Document flow vs non-flow operations
  - Document state mapping
  - Include workflow diagrams

## Priority Order

1. **CRITICAL**: Task 1 (Fix recursion bug) - Blocks everything
2. **HIGH**: Task 2 (Create orchestrator) - Core functionality
3. **HIGH**: Task 3 (Update job model) - Required for orchestrator
4. **MEDIUM**: Task 4 (API endpoints) - User-facing features
5. **MEDIUM**: Task 5 (Update operations) - Consistency
6. **MEDIUM**: Task 6 (Update worker) - Job handling
7. **LOW**: Task 7 (Refactor service) - Code cleanup
8. **LOW**: Task 8 (Testing) - Validation
9. **LOW**: Task 9 (Documentation) - Reference
