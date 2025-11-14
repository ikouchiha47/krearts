# Requirements Document

## Introduction

This document specifies requirements for a background job processing system that executes jobs asynchronously using a daemon process. The system will use NetworkX for dependency graph management and support both SQLite and LocalStack SQS as backend storage mechanisms. This replaces the current synchronous job execution model with a scalable, distributed-ready architecture.

## Glossary

- **Job Processor**: The system component responsible for executing jobs asynchronously in the background
- **Daemon Process**: A long-running background service that continuously polls for and executes pending jobs
- **NetworkX**: A Python library for creating and analyzing complex networks and graphs, used here for job dependency management
- **Job DAG**: Directed Acyclic Graph representing job dependencies where nodes are jobs and edges represent execution order constraints
- **SQLite Backend**: Local file-based database storage for job queue and state
- **LocalStack SQS**: AWS SQS emulation service running locally for distributed queue management
- **Job Queue**: A collection of jobs waiting to be executed, ordered by priority and dependencies
- **Worker**: A process that pulls jobs from the queue and executes them
- **Job Status**: The current state of a job (pending, running, completed, failed)
- **Retry Policy**: Rules governing how and when failed jobs should be retried

## Requirements

### Requirement 1: Asynchronous Job Execution

**User Story:** As a developer, I want jobs to execute asynchronously in the background, so that the main application remains responsive and can handle multiple concurrent operations.

#### Acceptance Criteria

1. WHEN a job is submitted to THE Job Processor, THE Job Processor SHALL add the job to the queue without blocking the caller
2. WHEN THE Daemon Process is running, THE Daemon Process SHALL continuously poll the Job Queue for pending jobs
3. WHEN a pending job has no unmet dependencies, THEN THE Worker SHALL execute the job asynchronously
4. WHEN a job is executing, THE Job Processor SHALL update the Job Status to "running" in the backend storage
5. WHEN a job completes successfully, THE Job Processor SHALL update the Job Status to "completed" and trigger dependent jobs

### Requirement 2: NetworkX-Based Dependency Management

**User Story:** As a developer, I want to define job dependencies using a directed acyclic graph, so that jobs execute in the correct order based on their relationships.

#### Acceptance Criteria

1. WHEN jobs are submitted with dependencies, THE Job Processor SHALL construct a Job DAG using NetworkX
2. WHEN determining job execution order, THE Job Processor SHALL use topological sorting on the Job DAG
3. IF a circular dependency is detected, THEN THE Job Processor SHALL raise an error and reject the job submission
4. WHEN a job completes, THE Job Processor SHALL identify all dependent jobs whose dependencies are now satisfied
5. WHEN all dependencies for a job are satisfied, THE Job Processor SHALL mark the job as ready for execution

### Requirement 3: SQLite Backend Support

**User Story:** As a developer, I want to use SQLite as a job queue backend for local development and single-instance deployments, so that I can run the system without external dependencies.

#### Acceptance Criteria

1. WHEN THE Job Processor is configured with SQLite backend, THE Job Processor SHALL store all job data in a SQLite database file
2. WHEN THE Daemon Process polls for jobs, THE Job Processor SHALL query the SQLite database for pending jobs with satisfied dependencies
3. WHEN updating job status, THE Job Processor SHALL use database transactions to ensure consistency
4. WHEN multiple workers access the SQLite backend, THE Job Processor SHALL use row-level locking to prevent race conditions
5. WHEN the database is locked, THE Job Processor SHALL retry the operation with exponential backoff up to 30 seconds

### Requirement 4: LocalStack SQS Backend Support

**User Story:** As a developer, I want to use LocalStack SQS as a job queue backend for distributed deployments, so that multiple workers can process jobs concurrently across different machines.

#### Acceptance Criteria

1. WHEN THE Job Processor is configured with LocalStack SQS backend, THE Job Processor SHALL connect to the LocalStack SQS service
2. WHEN a job is submitted, THE Job Processor SHALL send a message to the SQS queue with job details
3. WHEN THE Daemon Process polls for jobs, THE Job Processor SHALL receive messages from the SQS queue
4. WHEN a job is being processed, THE Job Processor SHALL set the message visibility timeout to prevent duplicate processing
5. WHEN a job completes successfully, THE Job Processor SHALL delete the message from the SQS queue

### Requirement 5: Daemon Process Management

**User Story:** As a system administrator, I want to start, stop, and monitor the daemon process, so that I can control job processing and troubleshoot issues.

#### Acceptance Criteria

1. WHEN the daemon start command is executed, THE Daemon Process SHALL initialize the configured backend and begin polling for jobs
2. WHEN a shutdown signal is received, THE Daemon Process SHALL complete currently running jobs and then exit gracefully
3. WHEN THE Daemon Process is running, THE Daemon Process SHALL log its status and job execution events
4. WHEN THE Daemon Process encounters an error, THE Daemon Process SHALL log the error details and continue processing other jobs
5. WHEN THE Daemon Process is idle, THE Daemon Process SHALL wait for a configurable polling interval before checking for new jobs

### Requirement 6: Job Retry and Error Handling

**User Story:** As a developer, I want failed jobs to be automatically retried with configurable policies, so that transient failures don't require manual intervention.

#### Acceptance Criteria

1. WHEN a job fails, THE Job Processor SHALL check the Retry Policy to determine if retry is allowed
2. WHEN a retry is allowed, THE Job Processor SHALL increment the retry count and requeue the job with exponential backoff delay
3. WHEN the maximum retry count is reached, THE Job Processor SHALL mark the job as permanently failed
4. WHEN a job fails permanently, THE Job Processor SHALL store the error details in the backend storage
5. WHEN a job fails, THE Job Processor SHALL not block dependent jobs if the dependency is marked as optional

### Requirement 7: Backend Configuration and Abstraction

**User Story:** As a developer, I want to switch between SQLite and SQS backends through configuration, so that I can use the appropriate backend for each deployment environment.

#### Acceptance Criteria

1. WHEN THE Job Processor is initialized, THE Job Processor SHALL read the backend type from configuration
2. WHEN the backend type is specified, THE Job Processor SHALL instantiate the appropriate backend implementation
3. WHEN backend operations are performed, THE Job Processor SHALL use a common interface regardless of backend type
4. WHEN backend-specific configuration is provided, THE Job Processor SHALL pass the configuration to the backend implementation
5. WHEN an unsupported backend type is specified, THE Job Processor SHALL raise a configuration error

### Requirement 8: Job Monitoring and Progress Tracking

**User Story:** As a developer, I want to query job status and progress, so that I can monitor execution and debug issues.

#### Acceptance Criteria

1. WHEN a job status query is made, THE Job Processor SHALL return the current status from the backend storage
2. WHEN querying jobs for a movie, THE Job Processor SHALL return all jobs with their current status and metadata
3. WHEN calculating progress, THE Job Processor SHALL compute the percentage of completed jobs versus total jobs
4. WHEN a job is running, THE Job Processor SHALL provide the start time and elapsed duration
5. WHEN a job has failed, THE Job Processor SHALL provide the error message and retry count

### Requirement 9: Graceful Degradation and Resilience

**User Story:** As a system administrator, I want the job processor to handle backend failures gracefully, so that temporary outages don't cause data loss or system crashes.

#### Acceptance Criteria

1. WHEN the backend connection fails, THE Job Processor SHALL retry the connection with exponential backoff
2. WHEN a job execution fails due to backend error, THE Job Processor SHALL preserve the job state and retry later
3. WHEN THE Daemon Process loses connection to the backend, THE Daemon Process SHALL attempt to reconnect without terminating
4. WHEN a worker crashes during job execution, THE Job Processor SHALL detect the stale job and make it available for retry
5. WHEN the backend is unavailable during job submission, THE Job Processor SHALL return an error to the caller without losing the job request

### Requirement 10: Integration with Existing Pipeline

**User Story:** As a developer, I want the background job processor to integrate seamlessly with the existing pipeline code, so that migration requires minimal code changes.

#### Acceptance Criteria

1. WHEN the existing JobTracker is replaced, THE Job Processor SHALL maintain compatibility with the current Job and PipelineState models
2. WHEN jobs are created by the pipeline, THE Job Processor SHALL accept the same job parameters and metadata
3. WHEN the pipeline queries job status, THE Job Processor SHALL provide the same interface as the current JobTracker
4. WHEN migrating to the background processor, THE Job Processor SHALL support reading existing job data from the SQLite database
5. WHEN the daemon is not running, THE Job Processor SHALL provide a synchronous fallback mode for backward compatibility

### Requirement 11: Real-Time Job Status Streaming

**User Story:** As a frontend developer, I want to stream job status updates in real-time using Server-Sent Events (SSE), so that users can see live progress without polling.

#### Acceptance Criteria

1. WHEN a client subscribes to job updates, THE Job Processor SHALL establish an SSE connection and stream status changes
2. WHEN a job status changes, THE Job Processor SHALL push an event to all subscribed SSE clients immediately
3. WHEN a job produces output or logs, THE Job Processor SHALL stream the output to subscribed clients in real-time
4. WHEN an SSE connection is closed, THE Job Processor SHALL clean up resources and stop sending events to that client
5. WHEN multiple clients subscribe to the same job, THE Job Processor SHALL broadcast updates to all subscribers

### Requirement 12: Simple Polling API

**User Story:** As a developer, I want a simple polling API to check job status and retrieve results, so that I can integrate with systems that don't support SSE.

#### Acceptance Criteria

1. WHEN a polling request is made for a job, THE Job Processor SHALL return the current status, progress percentage, and any available results
2. WHEN a job is completed, THE Job Processor SHALL include the output data in the polling response
3. WHEN a job is still running, THE Job Processor SHALL return the elapsed time and estimated completion time if available
4. WHEN polling for multiple jobs, THE Job Processor SHALL return a batch response with status for all requested jobs
5. WHEN a job does not exist, THE Job Processor SHALL return a clear error message indicating the job was not found

### Requirement 13: CrewAI and Flow Integration

**User Story:** As a developer, I want to submit CrewAI crew runs and flow runs as background jobs, so that long-running AI operations don't block the application.

#### Acceptance Criteria

1. WHEN a crew run is submitted, THE Job Processor SHALL wrap the crew execution in a background job with appropriate metadata
2. WHEN a flow run is submitted, THE Job Processor SHALL wrap the flow execution in a background job with appropriate metadata
3. WHEN a crew or flow job is executing, THE Job Processor SHALL capture and stream intermediate outputs and agent messages
4. WHEN a crew or flow job completes, THE Job Processor SHALL store the final result in a format compatible with the original synchronous API
5. WHEN a crew or flow job fails, THE Job Processor SHALL capture the full error context including agent state and conversation history

### Requirement 14: Simple and Intuitive API Design

**User Story:** As a developer, I want an intuitive API that requires minimal boilerplate, so that I can quickly submit jobs and retrieve results without complex setup.

#### Acceptance Criteria

1. WHEN submitting a job, THE Job Processor SHALL accept a simple function or callable with minimal wrapper code required
2. WHEN configuring the processor, THE Job Processor SHALL use sensible defaults that work for common use cases
3. WHEN retrieving job results, THE Job Processor SHALL provide a simple await-style or callback-style interface
4. WHEN working with job dependencies, THE Job Processor SHALL allow expressing dependencies using intuitive syntax
5. WHEN errors occur, THE Job Processor SHALL provide clear, actionable error messages with suggested fixes
