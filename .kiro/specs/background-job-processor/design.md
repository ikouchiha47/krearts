# Design Document

## Overview

The Background Job Processor is an asynchronous job execution system that enables long-running tasks (such as CrewAI crew runs, flow executions, and media generation) to run in the background without blocking the main application. The system uses NetworkX for dependency graph management and supports both SQLite (for local/single-instance deployments) and LocalStack SQS (for distributed deployments) as backend storage.

The design prioritizes simplicity, ease of integration, and real-time observability through Server-Sent Events (SSE) streaming and polling APIs.

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Client Application                        │
│  (Pipeline, CrewAI Flows, API Endpoints)                        │
└────────────┬────────────────────────────────────┬───────────────┘
             │                                    │
             │ Submit Jobs                        │ Query Status/Stream
             │                                    │
             ▼                                    ▼
┌────────────────────────────┐      ┌──────────────────────────────┐
│   JobProcessor (Facade)    │      │   StatusStreamer (SSE/Poll)  │
│  - submit_job()            │      │   - subscribe()              │
│  - submit_crew_run()       │      │   - poll_status()            │
│  - submit_flow_run()       │      │   - get_results()            │
└────────────┬───────────────┘      └──────────────┬───────────────┘
             │                                     │
             │                                     │
             ▼                                     ▼
┌────────────────────────────────────────────────────────────────┐
│                    Job Queue Manager                            │
│  - DAG Builder (NetworkX)                                       │
│  - Dependency Resolver                                          │
│  - Backend Abstraction Layer                                    │
└────────────┬───────────────────────────────────┬───────────────┘
             │                                   │
             │                                   │
    ┌────────▼────────┐                 ┌───────▼────────┐
    │ SQLite Backend  │                 │  SQS Backend   │
    │  - Local Queue  │                 │  - Distributed │
    │  - File-based   │                 │  - LocalStack  │
    └────────┬────────┘                 └───────┬────────┘
             │                                   │
             └───────────────┬───────────────────┘
                             │
                             ▼
                  ┌──────────────────────┐
                  │   Daemon Process     │
                  │  - Worker Pool       │
                  │  - Job Executor      │
                  │  - Event Publisher   │
                  └──────────────────────┘
```

### Component Interaction Flow

1. **Job Submission**: Client submits job → JobProcessor validates → DAG Builder adds to graph → Backend stores job
2. **Job Execution**: Daemon polls backend → Dependency Resolver finds ready jobs → Worker executes → Status updates published
3. **Status Monitoring**: Client subscribes via SSE or polls → StatusStreamer reads from backend → Real-time updates delivered

## Components and Interfaces

### 1. JobProcessor (Main Facade)

The primary interface for submitting and managing jobs.

```python
class JobProcessor:
    """
    Main facade for background job processing.
    Provides simple, intuitive API for job submission and management.
    """
    
    def __init__(
        self,
        backend: BackendType = BackendType.SQLITE,
        backend_config: Optional[Dict[str, Any]] = None,
        enable_daemon: bool = True
    ):
        """
        Initialize job processor with backend configuration.
        
        Args:
            backend: Backend type (SQLITE or SQS)
            backend_config: Backend-specific configuration
            enable_daemon: Whether to auto-start daemon (default: True)
        """
        pass
    
    def submit_job(
        self,
        func: Callable,
        *args,
        job_id: Optional[str] = None,
        depends_on: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> str:
        """
        Submit a job for background execution.
        
        Args:
            func: Function to execute
            args: Positional arguments for func
            job_id: Optional custom job ID
            depends_on: List of job IDs this job depends on
            metadata: Additional metadata
            kwargs: Keyword arguments for func
            
        Returns:
            job_id: Unique identifier for the submitted job
        """
        pass
    
    def submit_crew_run(
        self,
        crew: Any,  # CrewAI Crew instance
        inputs: Dict[str, Any],
        job_id: Optional[str] = None,
        depends_on: Optional[List[str]] = None
    ) -> str:
        """
        Submit a CrewAI crew run as a background job.
        Automatically captures agent outputs and streams them.
        """
        pass
    
    def submit_flow_run(
        self,
        flow: Any,  # CrewAI Flow instance
        inputs: Dict[str, Any],
        job_id: Optional[str] = None,
        depends_on: Optional[List[str]] = None
    ) -> str:
        """
        Submit a CrewAI flow run as a background job.
        Automatically captures flow state and streams progress.
        """
        pass
    
    async def wait_for_job(
        self,
        job_id: str,
        timeout: Optional[float] = None
    ) -> JobResult:
        """
        Async wait for job completion.
        Returns result when job completes or raises on timeout.
        """
        pass
    
    def get_status(self, job_id: str) -> JobStatus:
        """Get current status of a job."""
        pass
    
    def get_result(self, job_id: str) -> Optional[Any]:
        """Get result of completed job."""
        pass
    
    def cancel_job(self, job_id: str) -> bool:
        """Cancel a pending or running job."""
        pass
```

### 2. Backend Abstraction Layer

Provides a unified interface for different storage backends.

```python
class JobBackend(ABC):
    """Abstract base class for job storage backends."""
    
    @abstractmethod
    def enqueue_job(self, job: Job) -> None:
        """Add job to queue."""
        pass
    
    @abstractmethod
    def dequeue_job(self) -> Optional[Job]:
        """Get next ready job from queue."""
        pass
    
    @abstractmethod
    def update_job_status(
        self,
        job_id: str,
        status: JobStatus,
        result: Optional[Any] = None,
        error: Optional[str] = None
    ) -> None:
        """Update job status and result."""
        pass
    
    @abstractmethod
    def get_job(self, job_id: str) -> Optional[Job]:
        """Retrieve job by ID."""
        pass
    
    @abstractmethod
    def get_dependent_jobs(self, job_id: str) -> List[Job]:
        """Get jobs that depend on this job."""
        pass
    
    @abstractmethod
    def mark_job_ready(self, job_id: str) -> None:
        """Mark job as ready for execution (all dependencies met)."""
        pass


class SQLiteBackend(JobBackend):
    """SQLite implementation with row-level locking."""
    
    def __init__(self, db_path: str = "./cinema_jobs.db"):
        self.db_path = db_path
        self._init_schema()
    
    def _init_schema(self) -> None:
        """Initialize database schema with job and dependency tables."""
        pass
    
    # Implement abstract methods with SQLite-specific logic


class SQSBackend(JobBackend):
    """LocalStack SQS implementation for distributed processing."""
    
    def __init__(
        self,
        queue_url: str,
        endpoint_url: str = "http://localhost:4566",
        region: str = "us-east-1"
    ):
        self.queue_url = queue_url
        self.sqs_client = boto3.client(
            'sqs',
            endpoint_url=endpoint_url,
            region_name=region
        )
    
    # Implement abstract methods with SQS-specific logic
```

### 3. DAG Builder and Dependency Resolver

Manages job dependencies using NetworkX.

```python
class JobDAG:
    """
    Manages job dependency graph using NetworkX.
    Ensures acyclic dependencies and determines execution order.
    """
    
    def __init__(self):
        self.graph = nx.DiGraph()
        self._job_metadata: Dict[str, Job] = {}
    
    def add_job(
        self,
        job: Job,
        depends_on: Optional[List[str]] = None
    ) -> None:
        """
        Add job to DAG with dependencies.
        
        Raises:
            CyclicDependencyError: If adding job creates a cycle
        """
        self.graph.add_node(job.id)
        self._job_metadata[job.id] = job
        
        if depends_on:
            for dep_id in depends_on:
                self.graph.add_edge(dep_id, job.id)
        
        # Check for cycles
        if not nx.is_directed_acyclic_graph(self.graph):
            self.graph.remove_node(job.id)
            raise CyclicDependencyError(
                f"Adding job {job.id} would create a circular dependency"
            )
    
    def get_ready_jobs(self) -> List[Job]:
        """
        Get jobs whose dependencies are all satisfied.
        Uses topological sorting to determine execution order.
        """
        ready_jobs = []
        
        for node in nx.topological_sort(self.graph):
            job = self._job_metadata[node]
            
            # Check if all dependencies are completed
            dependencies = list(self.graph.predecessors(node))
            if all(
                self._job_metadata[dep].status == JobStatus.COMPLETED
                for dep in dependencies
            ):
                if job.status == JobStatus.PENDING:
                    ready_jobs.append(job)
        
        return ready_jobs
    
    def mark_completed(self, job_id: str) -> List[str]:
        """
        Mark job as completed and return IDs of newly ready jobs.
        """
        job = self._job_metadata[job_id]
        job.status = JobStatus.COMPLETED
        
        # Find dependent jobs that are now ready
        newly_ready = []
        for dependent_id in self.graph.successors(job_id):
            dependent_job = self._job_metadata[dependent_id]
            if self._are_dependencies_met(dependent_id):
                newly_ready.append(dependent_id)
        
        return newly_ready
    
    def _are_dependencies_met(self, job_id: str) -> bool:
        """Check if all dependencies for a job are completed."""
        dependencies = list(self.graph.predecessors(job_id))
        return all(
            self._job_metadata[dep].status == JobStatus.COMPLETED
            for dep in dependencies
        )
```

### 4. Daemon Process and Worker Pool

Long-running process that executes jobs.

```python
class JobDaemon:
    """
    Daemon process that continuously polls for and executes jobs.
    Manages worker pool and handles graceful shutdown.
    """
    
    def __init__(
        self,
        backend: JobBackend,
        num_workers: int = 4,
        poll_interval: float = 1.0
    ):
        self.backend = backend
        self.num_workers = num_workers
        self.poll_interval = poll_interval
        self.workers: List[Worker] = []
        self.running = False
        self.event_publisher = EventPublisher()
    
    def start(self) -> None:
        """Start daemon and worker pool."""
        self.running = True
        
        # Initialize workers
        for i in range(self.num_workers):
            worker = Worker(
                worker_id=i,
                backend=self.backend,
                event_publisher=self.event_publisher
            )
            self.workers.append(worker)
            worker.start()
        
        # Main polling loop
        self._poll_loop()
    
    def stop(self, graceful: bool = True) -> None:
        """
        Stop daemon and workers.
        
        Args:
            graceful: If True, wait for running jobs to complete
        """
        self.running = False
        
        for worker in self.workers:
            worker.stop(graceful=graceful)
        
        logger.info("Daemon stopped")
    
    def _poll_loop(self) -> None:
        """Main polling loop."""
        while self.running:
            try:
                # Get ready jobs from backend
                ready_jobs = self.backend.get_ready_jobs()
                
                # Distribute to available workers
                for job in ready_jobs:
                    available_worker = self._get_available_worker()
                    if available_worker:
                        available_worker.assign_job(job)
                    else:
                        break  # No workers available, try next iteration
                
                time.sleep(self.poll_interval)
                
            except Exception as e:
                logger.error(f"Error in poll loop: {e}")
                time.sleep(self.poll_interval)
    
    def _get_available_worker(self) -> Optional['Worker']:
        """Find an idle worker."""
        for worker in self.workers:
            if worker.is_idle():
                return worker
        return None


class Worker:
    """Individual worker that executes jobs."""
    
    def __init__(
        self,
        worker_id: int,
        backend: JobBackend,
        event_publisher: EventPublisher
    ):
        self.worker_id = worker_id
        self.backend = backend
        self.event_publisher = event_publisher
        self.current_job: Optional[Job] = None
        self.thread: Optional[threading.Thread] = None
    
    def start(self) -> None:
        """Start worker thread."""
        self.thread = threading.Thread(target=self._work_loop, daemon=True)
        self.thread.start()
    
    def assign_job(self, job: Job) -> None:
        """Assign job to this worker."""
        self.current_job = job
    
    def is_idle(self) -> bool:
        """Check if worker is idle."""
        return self.current_job is None
    
    def _work_loop(self) -> None:
        """Worker execution loop."""
        while True:
            if self.current_job:
                self._execute_job(self.current_job)
                self.current_job = None
            time.sleep(0.1)
    
    def _execute_job(self, job: Job) -> None:
        """Execute a single job."""
        try:
            # Update status to running
            self.backend.update_job_status(
                job.id,
                JobStatus.IN_PROGRESS
            )
            self.event_publisher.publish(JobEvent(
                job_id=job.id,
                event_type="status_change",
                data={"status": "in_progress"}
            ))
            
            # Execute job function
            result = job.func(*job.args, **job.kwargs)
            
            # Update status to completed
            self.backend.update_job_status(
                job.id,
                JobStatus.COMPLETED,
                result=result
            )
            self.event_publisher.publish(JobEvent(
                job_id=job.id,
                event_type="completed",
                data={"result": result}
            ))
            
        except Exception as e:
            # Handle failure and retry logic
            self._handle_job_failure(job, e)
    
    def _handle_job_failure(self, job: Job, error: Exception) -> None:
        """Handle job failure with retry logic."""
        job.retry_count += 1
        
        if job.retry_count < job.max_retries:
            # Requeue with exponential backoff
            delay = 2 ** job.retry_count
            self.backend.requeue_job(job, delay=delay)
            self.event_publisher.publish(JobEvent(
                job_id=job.id,
                event_type="retry",
                data={"retry_count": job.retry_count, "delay": delay}
            ))
        else:
            # Mark as permanently failed
            self.backend.update_job_status(
                job.id,
                JobStatus.FAILED,
                error=str(error)
            )
            self.event_publisher.publish(JobEvent(
                job_id=job.id,
                event_type="failed",
                data={"error": str(error)}
            ))
```

### 5. Status Streamer (SSE and Polling)

Provides real-time status updates via SSE and polling API.

```python
class StatusStreamer:
    """
    Provides real-time job status updates via SSE and polling.
    """
    
    def __init__(self, backend: JobBackend, event_publisher: EventPublisher):
        self.backend = backend
        self.event_publisher = event_publisher
        self.subscribers: Dict[str, List[Queue]] = {}
    
    async def subscribe_sse(
        self,
        job_id: str
    ) -> AsyncGenerator[str, None]:
        """
        Subscribe to job updates via Server-Sent Events.
        
        Yields:
            SSE-formatted event strings
        """
        queue = Queue()
        
        # Register subscriber
        if job_id not in self.subscribers:
            self.subscribers[job_id] = []
        self.subscribers[job_id].append(queue)
        
        try:
            # Send initial status
            job = self.backend.get_job(job_id)
            if job:
                yield f"data: {json.dumps({'status': job.status.value})}\n\n"
            
            # Stream updates
            while True:
                event = await queue.get()
                yield f"data: {json.dumps(event.data)}\n\n"
                
                # Stop streaming if job is terminal
                if event.event_type in ["completed", "failed"]:
                    break
        finally:
            # Cleanup subscriber
            self.subscribers[job_id].remove(queue)
    
    def poll_status(self, job_id: str) -> Dict[str, Any]:
        """
        Poll for job status (non-streaming).
        
        Returns:
            Dictionary with status, progress, and result if available
        """
        job = self.backend.get_job(job_id)
        
        if not job:
            raise JobNotFoundError(f"Job {job_id} not found")
        
        response = {
            "job_id": job.id,
            "status": job.status.value,
            "created_at": job.created_at.isoformat(),
            "updated_at": job.updated_at.isoformat(),
        }
        
        if job.status == JobStatus.IN_PROGRESS:
            response["elapsed_time"] = (
                datetime.now() - job.created_at
            ).total_seconds()
        
        if job.status == JobStatus.COMPLETED:
            response["result"] = job.result
        
        if job.status == JobStatus.FAILED:
            response["error"] = job.error
            response["retry_count"] = job.retry_count
        
        return response
    
    def poll_batch(self, job_ids: List[str]) -> Dict[str, Dict[str, Any]]:
        """Poll status for multiple jobs."""
        return {
            job_id: self.poll_status(job_id)
            for job_id in job_ids
        }


class EventPublisher:
    """
    Publishes job events to subscribers.
    Thread-safe event distribution.
    """
    
    def __init__(self):
        self.subscribers: Dict[str, List[Queue]] = {}
        self.lock = threading.Lock()
    
    def publish(self, event: JobEvent) -> None:
        """Publish event to all subscribers of the job."""
        with self.lock:
            if event.job_id in self.subscribers:
                for queue in self.subscribers[event.job_id]:
                    queue.put_nowait(event)
    
    def subscribe(self, job_id: str, queue: Queue) -> None:
        """Subscribe to events for a job."""
        with self.lock:
            if job_id not in self.subscribers:
                self.subscribers[job_id] = []
            self.subscribers[job_id].append(queue)
    
    def unsubscribe(self, job_id: str, queue: Queue) -> None:
        """Unsubscribe from job events."""
        with self.lock:
            if job_id in self.subscribers:
                self.subscribers[job_id].remove(queue)
```

### 6. CrewAI and Flow Integration

Specialized wrappers for CrewAI crew and flow execution.

```python
class CrewJobWrapper:
    """Wraps CrewAI crew execution for background processing."""
    
    @staticmethod
    def wrap_crew_run(
        crew: Any,
        inputs: Dict[str, Any],
        event_publisher: EventPublisher,
        job_id: str
    ) -> Any:
        """
        Execute crew run with output streaming.
        Captures agent messages and intermediate outputs.
        """
        # Patch crew to capture outputs
        original_execute = crew.kickoff
        
        def patched_execute(*args, **kwargs):
            # Stream agent outputs
            for agent_output in crew._execute_with_streaming(*args, **kwargs):
                event_publisher.publish(JobEvent(
                    job_id=job_id,
                    event_type="agent_output",
                    data={"output": agent_output}
                ))
            
            return original_execute(*args, **kwargs)
        
        crew.kickoff = patched_execute
        
        # Execute crew
        result = crew.kickoff(inputs=inputs)
        
        return result


class FlowJobWrapper:
    """Wraps CrewAI flow execution for background processing."""
    
    @staticmethod
    def wrap_flow_run(
        flow: Any,
        inputs: Dict[str, Any],
        event_publisher: EventPublisher,
        job_id: str
    ) -> Any:
        """
        Execute flow run with state streaming.
        Captures flow state transitions and outputs.
        """
        # Similar pattern to crew wrapper
        # Capture flow state changes and stream them
        pass
```

## Data Models

### Enhanced Job Model

```python
class Job(BaseModel):
    """Enhanced job model with dependency tracking."""
    
    id: str
    type: JobType
    status: JobStatus = JobStatus.PENDING
    
    # Function execution
    func: Optional[Callable] = None
    args: Tuple = ()
    kwargs: Dict[str, Any] = Field(default_factory=dict)
    
    # Dependencies
    depends_on: List[str] = Field(default_factory=list)
    dependencies_met: bool = False
    
    # Metadata
    scene_id: Optional[str] = None
    character_id: Optional[int] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # Execution tracking
    worker_id: Optional[int] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Results and errors
    result: Optional[Any] = None
    error: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    output_path: Optional[str] = None
    
    class Config:
        arbitrary_types_allowed = True


class JobEvent(BaseModel):
    """Event published during job execution."""
    
    job_id: str
    event_type: str  # status_change, agent_output, completed, failed, retry
    data: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.now)


class JobResult(BaseModel):
    """Result of job execution."""
    
    job_id: str
    status: JobStatus
    result: Optional[Any] = None
    error: Optional[str] = None
    execution_time: Optional[float] = None
```

## Error Handling

### Error Types

```python
class JobProcessorError(Exception):
    """Base exception for job processor errors."""
    pass


class CyclicDependencyError(JobProcessorError):
    """Raised when a circular dependency is detected."""
    pass


class JobNotFoundError(JobProcessorError):
    """Raised when a job ID doesn't exist."""
    pass


class BackendConnectionError(JobProcessorError):
    """Raised when backend connection fails."""
    pass


class JobExecutionError(JobProcessorError):
    """Raised when job execution fails."""
    pass
```

### Retry Strategy

- Exponential backoff: delay = 2^retry_count seconds
- Maximum retries: configurable per job (default: 3)
- Failed jobs marked as FAILED after max retries
- Retry events published to subscribers

### Graceful Degradation

- Backend connection failures: retry with exponential backoff (max 5 attempts)
- Worker crashes: jobs marked as PENDING and reassigned
- Daemon shutdown: complete running jobs before exit (configurable timeout)

## Testing Strategy

### Unit Tests

1. **JobDAG Tests**
   - Test cycle detection
   - Test topological sorting
   - Test dependency resolution

2. **Backend Tests**
   - Test SQLite operations (CRUD, locking)
   - Test SQS operations (enqueue, dequeue, visibility timeout)
   - Test backend abstraction layer

3. **Worker Tests**
   - Test job execution
   - Test retry logic
   - Test error handling

### Integration Tests

1. **End-to-End Job Execution**
   - Submit job → Execute → Retrieve result
   - Test with dependencies
   - Test with failures and retries

2. **SSE Streaming**
   - Subscribe to job updates
   - Verify real-time event delivery
   - Test connection cleanup

3. **CrewAI Integration**
   - Submit crew run as background job
   - Verify output streaming
   - Test result retrieval

### Performance Tests

1. **Throughput**
   - Measure jobs/second with varying worker counts
   - Test with SQLite and SQS backends

2. **Latency**
   - Measure time from submission to execution start
   - Measure event delivery latency

3. **Scalability**
   - Test with large DAGs (1000+ jobs)
   - Test with multiple concurrent daemons (SQS only)

## Configuration

### Example Configuration

```python
# SQLite backend (local development)
processor = JobProcessor(
    backend=BackendType.SQLITE,
    backend_config={
        "db_path": "./cinema_jobs.db"
    },
    enable_daemon=True,
    daemon_config={
        "num_workers": 4,
        "poll_interval": 1.0
    }
)

# SQS backend (distributed deployment)
processor = JobProcessor(
    backend=BackendType.SQS,
    backend_config={
        "queue_url": "http://localhost:4566/000000000000/cinema-jobs",
        "endpoint_url": "http://localhost:4566",
        "region": "us-east-1"
    },
    enable_daemon=True,
    daemon_config={
        "num_workers": 8,
        "poll_interval": 0.5
    }
)
```

## Migration Path

### Phase 1: Parallel Implementation
- Implement new JobProcessor alongside existing JobTracker
- Add feature flag to switch between implementations
- Maintain backward compatibility

### Phase 2: Gradual Migration
- Migrate non-critical jobs first
- Monitor performance and stability
- Migrate critical jobs after validation

### Phase 3: Deprecation
- Mark JobTracker as deprecated
- Remove old implementation after full migration
- Update documentation

## Usage Examples

### Simple Job Submission

```python
# Initialize processor
processor = JobProcessor()

# Submit a simple job
job_id = processor.submit_job(
    func=generate_image,
    prompt="A sunset over mountains",
    style="cinematic"
)

# Wait for completion
result = await processor.wait_for_job(job_id)
print(f"Image saved to: {result}")
```

### Job with Dependencies

```python
# Submit jobs with dependencies
screenplay_job = processor.submit_job(
    func=generate_screenplay,
    topic="detective story"
)

character_job = processor.submit_job(
    func=generate_characters,
    screenplay_id=screenplay_job,
    depends_on=[screenplay_job]
)

image_job = processor.submit_job(
    func=generate_character_images,
    character_id=character_job,
    depends_on=[character_job]
)
```

### CrewAI Integration

```python
# Submit crew run
from crewai import Crew

crew = Crew(agents=[...], tasks=[...])

job_id = processor.submit_crew_run(
    crew=crew,
    inputs={"topic": "detective story"}
)

# Stream outputs via SSE
async for event in processor.stream_job(job_id):
    print(f"Agent output: {event['data']}")
```

### Polling API

```python
# Poll for status
status = processor.get_status(job_id)
print(f"Status: {status['status']}")
print(f"Progress: {status.get('progress', 0)}%")

# Get result when complete
if status['status'] == 'completed':
    result = processor.get_result(job_id)
    print(f"Result: {result}")
```
