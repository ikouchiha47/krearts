"""
Workflow Orchestrator - Unified service for workflow operations and job management.

This orchestrator handles:
- State-driven workflow continuation
- Stage-level retry operations
- Job-level retry operations
- Flow-based vs non-flow operation routing
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

from cinema.context import DirectorsContext
from cinema.jobs.storage import JobRepository, get_job_repository
from cinema.server.storage.interface import Job, StorageBackend
from cinema.workflow.interface import WorkflowState, WorkflowType, WorkflowStage
from cinema.workflow.book_workflow import BookWorkflow
from cinema.agents.bookwriter.storage import get_storybuilder_storage

logger = logging.getLogger(__name__)


class WorkflowOrchestrator:
    """Orchestrates workflow operations and job management."""
    
    def __init__(
        self,
        workflow_id: str,
        ctx: DirectorsContext,
        job_repo: Optional[JobRepository] = None,
        storage: Optional[StorageBackend] = None,
    ):
        self.workflow_id = workflow_id
        self.ctx = ctx
        self.job_repo = job_repo or get_job_repository()
        self.storage = storage
        self.workflow = BookWorkflow(workflow_id, ctx)
    
    def _is_flow_based_stage(self, stage: WorkflowStage) -> bool:
        """Determine if a stage uses StoryBuilder flow."""
        return stage in [WorkflowStage.INIT, WorkflowStage.CONTENT]
    
    def _abort_previous_jobs(self, job_type: str) -> int:
        """Mark previous jobs of the same type as aborted.
        
        Returns:
            Number of jobs aborted
        """
        jobs = self.job_repo.list(workflow_id=self.workflow_id)
        aborted_count = 0
        
        for job in jobs:
            if job.type == job_type and job.status in ["pending", "running"]:
                job.status = "aborted"
                job.updated_at = datetime.utcnow()
                self.job_repo.save(job)
                aborted_count += 1
                logger.info(f"   Aborted job {job.id} (type: {job_type})")
        
        return aborted_count
    
    def _create_job(self, job_type: str, metadata: Dict[str, Any]) -> Job:
        """Create a new job with unique ID."""
        from uuid import uuid4
        
        job = Job(
            id=str(uuid4()),
            workflow_id=self.workflow_id,
            type=job_type,
            status="pending",
            metadata=metadata,
        )
        self.job_repo.save(job)
        logger.info(f"   Created job {job.id} (type: {job_type})")
        return job
    
    def _get_existing_job(self, job_type: str) -> Optional[Job]:
        """Check if there's already a pending/running job of this type.
        
        Returns:
            Existing job if found, None otherwise
        """
        jobs = self.job_repo.list(workflow_id=self.workflow_id)
        for job in jobs:
            if job.type == job_type and job.status in ["pending", "running"]:
                return job
        return None
    
    async def continue_workflow(self) -> Job:
        """Continue workflow from current state.
        
        Examines WorkflowState and determines the next operation to perform.
        If a job already exists for that operation, returns it instead of creating a new one.
        
        Returns:
            Job for the next operation (existing or newly created)
        
        Raises:
            ValueError: If workflow state is invalid or complete
        """
        logger.info(f"📋 Continue workflow: {self.workflow_id}")
        
        # Load workflow state
        if not self.storage:
            raise ValueError("Storage backend not configured")
        
        state = await self.storage.load_state(self.workflow_id, WorkflowType.BOOK)
        if not state:
            raise ValueError(f"Workflow {self.workflow_id} not found")
        
        logger.info(f"   Current stage: {state.current_stage.value}")
        logger.info(f"   Storyline done: {state.storyline_done}")
        logger.info(f"   Content done: {state.content_done}")
        logger.info(f"   Characters generated: {state.characters_generated}")
        logger.info(f"   Chapters generated: {len(state.chapters_generated)}")
        
        # Determine next operation based on state
        job_type = None
        job_metadata = {}
        
        if not state.storyline_done:
            logger.info("   → Next: Generate storyline (init)")
            job_type = "book_init"
            job_metadata = self._build_job_metadata_for_stage(WorkflowStage.INIT, state)
        
        elif not state.content_done:
            logger.info("   → Next: Generate content (novel)")
            job_type = "book_content"
            job_metadata = self._build_job_metadata_for_stage(WorkflowStage.CONTENT, state)
        
        elif not state.characters_generated:
            logger.info("   → Next: Generate characters")
            job_type = "character_generation"
            job_metadata = {}
        
        elif not state.chapters_generated:
            logger.info("   → Next: Generate chapters")
            job_type = "book_chapters"
            job_metadata = self._build_job_metadata_for_stage(WorkflowStage.CHAPTERS, state)
        
        else:
            raise ValueError("Workflow is complete - no next operation")
        
        # Check if job already exists
        existing_job = self._get_existing_job(job_type)
        if existing_job:
            logger.info(f"   ✓ Job already exists: {existing_job.id} (status: {existing_job.status})")
            return existing_job
        
        # Create new job
        return self._create_job(job_type, job_metadata)
    
    def _build_job_metadata_for_stage(self, stage: WorkflowStage, state: 'WorkflowState') -> Dict[str, Any]:
        """Build job metadata for a given stage.
        
        Centralizes the logic for creating job metadata to avoid duplication.
        
        Args:
            stage: The workflow stage
            state: The workflow state
            
        Returns:
            Job metadata dictionary
            
        Raises:
            ValueError: If stage requires data that's not available
        """
        if stage == WorkflowStage.INIT:
            return {"config": state.config}
        
        elif stage == WorkflowStage.CONTENT:
            return {"continue_from": False}
        
        elif stage == WorkflowStage.COVER:
            return {}
        
        elif stage == WorkflowStage.CHAPTERS:
            # Get art_style from workflow
            art_style = self.workflow._get_art_style()
            if not art_style:
                raise ValueError("art_style not found in generated content - cannot create chapters job. Ensure storyline/novel has been generated first.")
            logger.info(f"   Using art_style: {art_style}")
            return {
                "chapters": None,
                "continue_from": False,
                "art_style": art_style,
                "aspect_ratio": "4:5",
            }
        
        elif stage == WorkflowStage.PAGES:
            return {
                "pages": None,
                "continue_from": False,
            }
        
        else:
            raise ValueError(f"Unknown stage: {stage}")
    
    async def retry_stage(self) -> Job:
        """Retry the current stage.
        
        Finds existing jobs for the current stage, marks them as aborted,
        and creates a new job for the same stage.
        
        Returns:
            New job for the stage
        
        Raises:
            ValueError: If workflow not found
        """
        logger.info(f"🔄 Retry stage: {self.workflow_id}")
        
        # Load workflow state
        if not self.storage:
            raise ValueError("Storage backend not configured")
        
        state = await self.storage.load_state(self.workflow_id, WorkflowType.BOOK)
        if not state:
            raise ValueError(f"Workflow {self.workflow_id} not found")
        
        stage = state.current_stage
        logger.info(f"   Current stage: {stage.value}")
        
        # Map stage to job type
        stage_to_job_type = {
            WorkflowStage.INIT: "book_init",
            WorkflowStage.CONTENT: "book_content",
            WorkflowStage.COVER: "book_cover",
            WorkflowStage.CHAPTERS: "book_chapters",
            WorkflowStage.PAGES: "book_pages",
        }
        
        job_type = stage_to_job_type.get(stage)
        if not job_type:
            raise ValueError(f"Unknown stage: {stage}")
        
        # Abort previous jobs
        aborted = self._abort_previous_jobs(job_type)
        logger.info(f"   Aborted {aborted} previous jobs")
        
        # Reset flow state if flow-based
        if self._is_flow_based_stage(stage):
            logger.info(f"   Resetting flow state for {stage.value}")
            self._reset_flow_state(stage)
        
        # Build job metadata using centralized logic
        job_metadata = self._build_job_metadata_for_stage(stage, state)
        return self._create_job(job_type, job_metadata)
    
    def _reset_flow_state(self, stage: WorkflowStage):
        """Reset StoryBuilder flow state to beginning of stage.
        
        Args:
            stage: The stage to reset to
        """
        flow_storage = get_storybuilder_storage()
        
        try:
            flow_data = flow_storage.load(self.workflow_id)
        except FileNotFoundError:
            logger.warning(f"   No flow state found for {self.workflow_id}")
            return
        
        # Map stage to flow current_state
        if stage == WorkflowStage.INIT:
            flow_data['current_state'] = 'plan'
            flow_data['halted_at'] = None
        elif stage == WorkflowStage.CONTENT:
            flow_data['current_state'] = 'bookerama'
            flow_data['halted_at'] = None
        
        # Save updated flow state
        flow_storage.save(self.workflow_id, flow_data)
        logger.info(f"   Reset flow state to: {flow_data['current_state']}")
    
    async def retry_job(self, job_id: str) -> Job:
        """Retry a specific job by ID.
        
        Creates a new job with the same type and metadata,
        marks the old job as aborted.
        
        Args:
            job_id: ID of the job to retry
        
        Returns:
            New job
        
        Raises:
            ValueError: If job not found or cannot be retried
        """
        logger.info(f"🔄 Retry job: {job_id}")
        
        # Load job
        job = self.job_repo.get(job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")
        
        # Validate status
        if job.status not in ["failed", "running"]:
            raise ValueError(
                f"Cannot retry job in '{job.status}' status. "
                f"Only 'failed' or 'running' jobs can be retried."
            )
        
        # Check if running job is actually stuck
        if job.status == "running":
            time_since_update = datetime.utcnow() - job.updated_at
            if time_since_update < timedelta(minutes=10):
                raise ValueError(
                    f"Job is still running (updated {int(time_since_update.total_seconds())}s ago). "
                    f"Wait or use 'reset' to force."
                )
        
        logger.info(f"   Job type: {job.type}")
        logger.info(f"   Job status: {job.status}")
        
        # Mark old job as aborted
        job.status = "aborted"
        job.updated_at = datetime.utcnow()
        self.job_repo.save(job)
        logger.info(f"   Marked old job as aborted")
        
        # Create new job with incremented retry count
        # Copy metadata but fix any None values for chapters job
        new_metadata = job.metadata.copy()
        
        if job.type == "book_chapters":
            # Ensure art_style and aspect_ratio are set
            if not new_metadata.get("art_style"):
                art_style = self.workflow._get_art_style()
                if not art_style:
                    raise ValueError("art_style not found in generated content - cannot retry chapter job")
                new_metadata["art_style"] = art_style
                logger.info(f"   Fixed art_style: {art_style}")
            
            if not new_metadata.get("aspect_ratio"):
                new_metadata["aspect_ratio"] = "4:5"
                logger.info(f"   Fixed aspect_ratio: 4:5")
        
        new_job = Job(
            id=str(__import__('uuid').uuid4()),
            workflow_id=job.workflow_id,
            type=job.type,
            status="pending",
            metadata=new_metadata,
            retry_count=job.retry_count + 1,
        )
        self.job_repo.save(new_job)
        logger.info(f"   Created new job {new_job.id} (retry #{new_job.retry_count})")
        
        return new_job
