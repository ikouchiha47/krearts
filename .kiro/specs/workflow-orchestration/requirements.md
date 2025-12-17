# Workflow Orchestration & Retry System - Requirements

## Introduction

This spec defines a unified workflow orchestration system that handles state-driven operations, job management, and retry logic for the book generation pipeline. The system must handle both flow-based operations (StoryBuilder) and non-flow operations (image generation) through a consistent interface.

## Glossary

- **WorkflowState**: High-level workflow state tracking (init/content/cover/chapters/pages stages)
- **StoryBuilderState**: CrewAI flow state for storyline/novel generation (plan/critique/screenplay/bookerama)
- **Job**: Asynchronous task record with status tracking (pending/running/completed/failed)
- **Orchestrator**: Service that coordinates workflow operations and job creation
- **Flow-based operation**: Operations handled by StoryBuilder flow (init, content generation)
- **Non-flow operation**: Direct operations outside the flow (character/chapter/page image generation)

## Requirements

### Requirement 1: Workflow State Management

**User Story:** As a developer, I want a clear separation between flow-based and non-flow operations, so that the system can handle both types consistently.

#### Acceptance Criteria

1. WHEN the system determines the next operation THEN it SHALL identify whether the operation is flow-based or non-flow based on the current_stage
2. WHEN current_stage is INIT or CONTENT THEN the system SHALL use StoryBuilder flow for execution
3. WHEN current_stage is COVER, CHAPTERS, or PAGES THEN the system SHALL use direct generation functions
4. WHEN character generation is requested THEN the system SHALL execute it as a non-flow operation between CONTENT and CHAPTERS stages
5. WHEN a flow-based operation is resumed THEN the system SHALL restore the StoryBuilderState to the appropriate current_state value

### Requirement 2: Job Creation and Management

**User Story:** As a system administrator, I want jobs to be immutable once created, so that I have a complete audit trail of all operations.

#### Acceptance Criteria

1. WHEN a retry is requested THEN the system SHALL create a new job and mark the old job as "aborted"
2. WHEN a job is created THEN the system SHALL assign it a unique ID and set status to "pending"
3. WHEN a job fails THEN the system SHALL preserve the error information in the job record
4. WHEN listing jobs THEN the system SHALL include all jobs (pending/running/completed/failed/aborted) sorted by updated_at descending
5. WHEN a job has been running for more than 10 minutes without update THEN the system SHALL flag it as "stuck"

### Requirement 3: Workflow-Level Continue Operation

**User Story:** As a user, I want to continue a workflow from where it left off, so that I don't need to know the internal job details.

#### Acceptance Criteria

1. WHEN POST /workflows/{workflow_id}/continue is called THEN the system SHALL examine the WorkflowState to determine the next operation
2. WHEN storyline_done is false THEN the system SHALL create a job for init stage
3. WHEN storyline_done is true AND content_done is false THEN the system SHALL create a job for content generation
4. WHEN content_done is true AND characters_generated is false THEN the system SHALL create a job for character generation
5. WHEN characters_generated is true AND chapters_generated is empty THEN the system SHALL create a job for chapter generation
6. WHEN the continue operation creates a job THEN the system SHALL return the job_id for polling

### Requirement 4: Stage-Level Retry Operation

**User Story:** As a user, I want to retry the current stage when it fails, so that I can recover from errors without manual intervention.

#### Acceptance Criteria

1. WHEN POST /workflows/{workflow_id}/retry-stage is called THEN the system SHALL identify the current stage from WorkflowState
2. WHEN retrying a stage THEN the system SHALL find any existing jobs for that stage and mark them as "aborted"
3. WHEN retrying a stage THEN the system SHALL create a new job for the same stage
4. WHEN retrying a flow-based stage THEN the system SHALL reset the StoryBuilderState to the beginning of that stage
5. WHEN the retry operation completes THEN the system SHALL return the new job_id for polling

### Requirement 5: Specific Operation Endpoints

**User Story:** As a user, I want explicit control over specific operations like character or chapter generation, so that I can trigger them independently.

#### Acceptance Criteria

1. WHEN POST /workflows/{workflow_id}/characters/generate is called THEN the system SHALL validate that content_done is true
2. WHEN POST /workflows/{workflow_id}/chapters/generate is called THEN the system SHALL validate that characters_generated is true
3. WHEN POST /workflows/{workflow_id}/pages/generate is called THEN the system SHALL validate that chapters_generated is not empty
4. WHEN a specific operation is requested THEN the system SHALL create a job with the appropriate type
5. WHEN a specific operation completes THEN the system SHALL update the corresponding WorkflowState flags

### Requirement 6: Job-Level Retry Operation

**User Story:** As a developer, I want to retry specific failed jobs by job_id, so that I can handle granular failures like a single chapter failing.

#### Acceptance Criteria

1. WHEN PATCH /jobs/{job_id} with action="retry" is called THEN the system SHALL validate the job status is "failed" or "stuck"
2. WHEN retrying a job THEN the system SHALL create a new job with the same type and metadata
3. WHEN retrying a job THEN the system SHALL mark the old job as "aborted"
4. WHEN retrying a job THEN the system SHALL increment the retry_count on the new job
5. WHEN a job retry completes THEN the system SHALL return the new job_id

### Requirement 7: Validator Recursion Fix

**User Story:** As a developer, I want the workflow validator to work without infinite recursion, so that workflow state can be retrieved successfully.

#### Acceptance Criteria

1. WHEN validate_operation is called THEN it SHALL NOT call _get_blocked_actions
2. WHEN _get_blocked_actions is called THEN it SHALL check prerequisites directly without calling validate_operation
3. WHEN GET /workflows/{workflow_id} is called THEN it SHALL return workflow state without recursion errors
4. WHEN the validator checks prerequisites THEN it SHALL use simple boolean checks on WorkflowState flags
5. WHEN the validator determines blocked actions THEN it SHALL return a list of operation names that cannot be performed

### Requirement 8: Orchestrator Service

**User Story:** As a developer, I want a unified orchestrator service, so that both API endpoints and autopilot mode use the same logic.

#### Acceptance Criteria

1. WHEN the orchestrator is initialized THEN it SHALL have access to WorkflowState, Job repository, and BookWorkflow
2. WHEN the orchestrator continues a workflow THEN it SHALL use the same logic regardless of whether it's called from API or autopilot
3. WHEN the orchestrator creates a job THEN it SHALL update the WorkflowState appropriately
4. WHEN the orchestrator retries an operation THEN it SHALL handle both flow-based and non-flow operations correctly
5. WHEN the orchestrator completes an operation THEN it SHALL save both WorkflowState and Job state consistently

### Requirement 9: Workflow Not Found Handling

**User Story:** As a user, I want clear error messages when a workflow doesn't exist, so that I understand what went wrong.

#### Acceptance Criteria

1. WHEN GET /workflows/{workflow_id} is called for a non-existent workflow THEN the system SHALL return 404 with message "Workflow not found"
2. WHEN a workflow exists but has no jobs THEN the system SHALL return the workflow state with empty jobs list
3. WHEN a workflow exists but StoryBuilder state is missing THEN the system SHALL return workflow state with title "Generating storyline..."
4. WHEN a workflow is in init stage with no storyline THEN the system SHALL indicate it's in progress
5. WHEN listing workflows THEN the system SHALL only return workflows that exist in the workflow_states table
