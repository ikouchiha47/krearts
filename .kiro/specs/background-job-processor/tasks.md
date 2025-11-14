# Implementation Plan

- [ ] 1. Set up core data models and enums
  - Create enhanced Job model with dependency tracking fields (func, args, kwargs, depends_on, dependencies_met)
  - Create JobEvent model for event publishing
  - Create JobResult model for execution results
  - Add BackendType enum (SQLITE, SQS)
  - Create custom exception classes (CyclicDependencyError, JobNotFoundError, BackendConnectionError, JobExecutionError)
  - _Requirements: 1.1, 1.2, 2.1, 7.1_

- [ ] 2. Implement backend abstraction layer
- [ ] 2.1 Create JobBackend abstract base class
  - Define abstract methods: enqueue_job, dequeue_job, update_job_status, get_job, get_dependent_jobs, mark_job_ready, get_ready_jobs
  - Add docstrings for each method
  - _Requirements: 7.3, 7.4_

- [ ] 2.2 Implement SQLiteBackend
  - Initialize database schema with jobs table (add depends_on, dependencies_met columns)
  - Initialize job_dependencies junction table for many-to-many relationships
  - Implement enqueue_job with transaction support
  - Implement dequeue_job with row-level locking (SELECT ... FOR UPDATE)
  - Implement update_job_status with optimistic locking
  - Implement get_ready_jobs query (WHERE dependencies_met = TRUE AND status = PENDING)
  - Add connection pooling and WAL mode for concurrency
  - Implement retry logic with exponential backoff for locked database
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [ ] 2.3 Implement SQSBackend
  - Initialize boto3 SQS client with LocalStack endpoint
  - Implement enqueue_job by sending message to SQS queue
  - Implement dequeue_job by receiving messages with visibility timeout
  - Implement update_job_status by updating DynamoDB table (for metadata) and deleting SQS message on completion
  - Implement message visibility timeout extension for long-running jobs
  - Add connection retry logic with exponential backoff
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [ ] 3. Implement NetworkX-based dependency management
- [ ] 3.1 Create JobDAG class
  - Initialize NetworkX DiGraph
  - Implement add_job method with cycle detection using nx.is_directed_acyclic_graph
  - Raise CyclicDependencyError if cycle detected
  - Store job metadata in dictionary keyed by job_id
  - _Requirements: 2.1, 2.3_

- [ ] 3.2 Implement dependency resolution logic
  - Implement get_ready_jobs using topological sort (nx.topological_sort)
  - Implement mark_completed to update job status and find newly ready jobs
  - Implement _are_dependencies_met helper to check if all predecessors are completed
  - Add method to get dependent jobs (successors in graph)
  - _Requirements: 2.2, 2.4, 2.5_

- [ ] 4. Implement event publishing system
- [ ] 4.1 Create EventPublisher class
  - Initialize subscribers dictionary (job_id -> List[Queue])
  - Implement thread-safe publish method using threading.Lock
  - Implement subscribe and unsubscribe methods
  - Add cleanup logic for completed jobs
  - _Requirements: 11.2, 11.4_

- [ ] 4.2 Create StatusStreamer class
  - Initialize with backend and event_publisher
  - Implement subscribe_sse async generator for SSE streaming
  - Implement poll_status for single job status queries
  - Implement poll_batch for multiple job status queries
  - Format SSE events according to spec (data: {json}\n\n)
  - _Requirements: 11.1, 11.3, 12.1, 12.2, 12.3, 12.4, 12.5_

- [ ] 5. Implement worker and daemon process
- [ ] 5.1 Create Worker class
  - Initialize with worker_id, backend, and event_publisher
  - Implement start method to spawn worker thread
  - Implement _work_loop for continuous job processing
  - Implement _execute_job to run job function and capture result
  - Implement _handle_job_failure with retry logic and exponential backoff
  - Publish events for status changes (in_progress, completed, failed, retry)
  - _Requirements: 1.3, 1.4, 1.5, 6.1, 6.2, 6.3, 6.4_

- [ ] 5.2 Create JobDaemon class
  - Initialize with backend, num_workers, and poll_interval
  - Implement start method to initialize worker pool and begin polling
  - Implement _poll_loop to continuously check for ready jobs
  - Implement _get_available_worker to find idle workers
  - Implement stop method for graceful shutdown (wait for running jobs)
  - Add signal handlers for SIGTERM and SIGINT
  - Add logging for daemon lifecycle events
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 9.3_

- [ ] 6. Implement JobProcessor facade
- [ ] 6.1 Create JobProcessor main class
  - Initialize with backend type and configuration
  - Implement backend factory to instantiate SQLiteBackend or SQSBackend
  - Initialize JobDAG for dependency management
  - Initialize StatusStreamer for monitoring
  - Optionally start daemon process if enable_daemon=True
  - _Requirements: 7.1, 7.2, 7.5, 14.2_

- [ ] 6.2 Implement job submission methods
  - Implement submit_job to accept callable, args, kwargs, and dependencies
  - Generate unique job_id if not provided
  - Add job to DAG with dependencies
  - Enqueue job to backend
  - Return job_id to caller without blocking
  - _Requirements: 1.1, 14.1, 14.4_

- [ ] 6.3 Implement job monitoring methods
  - Implement get_status to query job status from backend
  - Implement get_result to retrieve completed job result
  - Implement wait_for_job async method to await completion
  - Implement cancel_job to mark job as cancelled
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 14.3_

- [ ] 7. Implement CrewAI and Flow integration
- [ ] 7.1 Create CrewJobWrapper class
  - Implement wrap_crew_run static method
  - Patch crew.kickoff to capture agent outputs
  - Publish agent_output events during execution
  - Return final crew result
  - _Requirements: 13.1, 13.3, 13.4_

- [ ] 7.2 Create FlowJobWrapper class
  - Implement wrap_flow_run static method
  - Capture flow state transitions
  - Publish flow state events during execution
  - Return final flow result
  - _Requirements: 13.2, 13.3, 13.4_

- [ ] 7.3 Add convenience methods to JobProcessor
  - Implement submit_crew_run that wraps crew in CrewJobWrapper
  - Implement submit_flow_run that wraps flow in FlowJobWrapper
  - Ensure metadata includes crew/flow type for filtering
  - _Requirements: 13.1, 13.2, 13.5_

- [ ] 8. Implement error handling and resilience
- [ ] 8.1 Add backend connection retry logic
  - Implement exponential backoff for connection failures (max 5 attempts)
  - Add connection health checks
  - Log connection errors with context
  - _Requirements: 9.1, 9.2_

- [ ] 8.2 Add worker crash detection
  - Implement heartbeat mechanism for workers
  - Detect stale jobs (running > timeout threshold)
  - Reset stale jobs to PENDING status for retry
  - _Requirements: 9.4_

- [ ] 8.3 Add graceful shutdown handling
  - Implement configurable shutdown timeout
  - Wait for running jobs to complete before exit
  - Save in-progress job state to backend
  - _Requirements: 5.2, 9.3_

- [ ] 9. Create configuration management
- [ ] 9.1 Create configuration classes
  - Create BackendConfig base class
  - Create SQLiteConfig with db_path
  - Create SQSConfig with queue_url, endpoint_url, region
  - Create DaemonConfig with num_workers, poll_interval, shutdown_timeout
  - _Requirements: 7.4, 7.5_

- [ ] 9.2 Add configuration validation
  - Validate backend-specific configuration on initialization
  - Provide helpful error messages for invalid config
  - Set sensible defaults for optional parameters
  - _Requirements: 14.2, 14.5_

- [ ] 10. Add backward compatibility layer
- [ ] 10.1 Create compatibility adapter
  - Implement adapter that wraps JobProcessor with JobTracker interface
  - Map existing JobTracker methods to JobProcessor equivalents
  - Support reading existing SQLite job data
  - _Requirements: 10.1, 10.2, 10.3, 10.4_

- [ ] 10.2 Add synchronous fallback mode
  - Detect if daemon is not running
  - Execute jobs synchronously in fallback mode
  - Log warning about synchronous execution
  - _Requirements: 10.5_

- [ ] 11. Create CLI for daemon management
- [ ] 11.1 Implement daemon start command
  - Create CLI entry point using Click or argparse
  - Accept configuration file path or command-line args
  - Start daemon process and log PID
  - _Requirements: 5.1_

- [ ] 11.2 Implement daemon stop command
  - Send shutdown signal to running daemon
  - Wait for graceful shutdown with timeout
  - Report shutdown status
  - _Requirements: 5.2_

- [ ] 11.3 Implement daemon status command
  - Query daemon process status
  - Display worker count and current jobs
  - Show recent log entries
  - _Requirements: 5.3_

- [ ] 12. Add comprehensive logging
- [ ] 12.1 Configure structured logging
  - Set up logging with configurable levels
  - Add context fields (job_id, worker_id, timestamp)
  - Log to file and console
  - _Requirements: 5.3, 5.4_

- [ ] 12.2 Add key log points
  - Log job submission, execution start, completion, failure
  - Log daemon lifecycle events (start, stop, worker spawn)
  - Log backend operations (enqueue, dequeue, status update)
  - Log errors with full stack traces
  - _Requirements: 5.3, 5.4_

- [ ] 13. Create example usage scripts
- [ ] 13.1 Create simple job example
  - Demonstrate basic job submission and result retrieval
  - Show synchronous wait_for_job usage
  - _Requirements: 14.1, 14.3_

- [ ] 13.2 Create dependency example
  - Demonstrate jobs with dependencies
  - Show DAG construction and execution order
  - _Requirements: 2.1, 2.2, 14.4_

- [ ] 13.3 Create CrewAI integration example
  - Demonstrate crew run submission
  - Show SSE streaming of agent outputs
  - _Requirements: 13.1, 13.3, 11.1_

- [ ] 13.4 Create polling API example
  - Demonstrate status polling
  - Show batch status queries
  - _Requirements: 12.1, 12.4_

- [ ] 14. Update existing pipeline integration
- [ ] 14.1 Update detective_maker.py to use JobProcessor
  - Replace JobTracker with JobProcessor
  - Submit image generation jobs with dependencies
  - Use SSE streaming for progress updates
  - _Requirements: 10.1, 10.2_

- [ ] 14.2 Update movie_maker.py to use JobProcessor
  - Replace JobTracker with JobProcessor
  - Submit video generation jobs with dependencies
  - Maintain existing PipelineState compatibility
  - _Requirements: 10.1, 10.3_

- [ ] 15. Create documentation
- [ ] 15.1 Write API documentation
  - Document JobProcessor public methods
  - Document configuration options
  - Document backend selection guide
  - _Requirements: 14.2, 14.5_

- [ ] 15.2 Write migration guide
  - Document migration steps from JobTracker
  - Provide code examples for common patterns
  - Document breaking changes and workarounds
  - _Requirements: 10.1, 10.2, 10.3_

- [ ] 15.3 Write deployment guide
  - Document SQLite deployment (single instance)
  - Document SQS deployment (distributed)
  - Document LocalStack setup for development
  - _Requirements: 3.1, 4.1_
