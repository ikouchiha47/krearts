from __future__ import annotations

from typing import Optional, List
from uuid import uuid4

from fastapi import HTTPException

from cinema.context import DirectorsContext
from cinema.jobs.storage import JobRepository, get_job_repository
from cinema.server.storage.interface import Job
from cinema.workflow.book_workflow import BookWorkflow
from cinema.workflow.validator import WorkflowStateValidator, ValidationResult

class BookWorkflowService:
    """Application service layer around BookWorkflow.

    This isolates orchestration and job tracking from HTTP/CLI surfaces so
    both can reuse the same core behavior.
    """

    def __init__(
        self,
        ctx: DirectorsContext,
        job_repo: Optional[JobRepository] = None,
        storage = None,
    ) -> None:
        self._ctx = ctx
        self._job_repo = job_repo or get_job_repository()
        self._storage = storage  # Will be injected by dependency
        self._validator = WorkflowStateValidator()  # NEW: State validator

    def _new_job(self, workflow_id: str, type_: str, metadata: dict) -> Job:
        job = Job(
            id=str(uuid4()),
            workflow_id=workflow_id,
            type=type_,
            status="pending",  # Start as pending, background task will set to running
            metadata=metadata,
        )
        self._job_repo.save(job)
        return job
    
    async def _validate_operation(
        self, 
        workflow_id: str, 
        operation: str
    ) -> ValidationResult:
        """Validate operation can be performed."""
        from cinema.workflow.interface import WorkflowType

        assert self._storage is not None
        
        # Load workflow state
        wf_state = await self._storage.load_state(workflow_id, WorkflowType.BOOK)
        if not wf_state:
            raise HTTPException(
                status_code=404,
                detail=f"Workflow {workflow_id} not found"
            )
        
        # Validate
        return self._validator.validate_operation(wf_state, operation)

    async def init(self, payload: dict) -> Job:
        """Initialize a new book workflow (storyline + critique)."""
        from cinema.workflow.interface import WorkflowState, WorkflowType, WorkflowStage
        from pathlib import Path

        assert self._storage is not None

        workflow_id = payload.get("workflow_id") or str(uuid4())[:8]
        output_dir = f"./output/book_{workflow_id}"
        
        # Create workflow entry FIRST so /workflows/{id} works immediately
        workflow_state = WorkflowState(
            id=workflow_id,
            type=WorkflowType.BOOK,
            current_stage=WorkflowStage.INIT,
            storyline_done=False,
            content_done=False,
            cover_generated=False,
            chapters_generated=[],
            pages_generated=[],
            output_dir=output_dir,
            config=payload,
        )
        await self._storage.save_state(workflow_state)
        
        # Now create the job
        job = self._new_job(
            workflow_id,
            "book_init",
            {"config": payload},  # Store full config for worker
        )

        # Job is saved with status="pending"
        # Background worker will pick it up and process it
        return job


    async def generate_content(self, workflow_id: str, continue_from: bool) -> Job:
        """Generate novel content for an existing workflow."""
        
        # Validate prerequisites
        validation = await self._validate_operation(workflow_id, "generate_content")
        if not validation.valid:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "prerequisite_not_met",
                    "operation": "generate_content",
                    **validation.model_dump()
                }
            )

        job = self._new_job(
            workflow_id,
            "book_content",
            {"continue_from": bool(continue_from)},
        )
        
        # Job is saved with status="pending"
        # Background worker will pick it up and process it
        return job

    async def generate_chapters(
        self,
        workflow_id: str,
        chapters: Optional[List[int]],
        continue_from: bool,
        art_style: Optional[str],
        aspect_ratio: Optional[str],
        comic_config = None,  # New: ComicGenerationConfig
        # Legacy parameters (for backward compatibility)
        target_pages_per_chapter: Optional[int] = None,
        total_novel_pages: Optional[int] = None,
        use_smart_compression: Optional[bool] = None,
        background_tasks=None,  # Unused, kept for compatibility
    ) -> Job:
        """Generate comic chapters - job will be processed by background worker."""
        
        # Validate prerequisites
        validation = await self._validate_operation(workflow_id, "generate_chapters")
        if not validation.valid:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "prerequisite_not_met",
                    "operation": "generate_chapters",
                    **validation.model_dump()
                }
            )

        # Handle comic config (new) vs legacy parameters
        if comic_config:
            metadata = {
                "chapters": chapters,
                "continue_from": bool(continue_from),
                "art_style": art_style,
                "aspect_ratio": aspect_ratio,
                "comic_config": comic_config.model_dump(),
                # Legacy fields for backward compatibility
                "target_pages_per_chapter": comic_config.pages_per_chapter,
                "total_novel_pages": (comic_config.total_chapters or 10) * comic_config.pages_per_chapter,
                "use_smart_compression": comic_config.use_smart_compression,
            }
        else:
            # Legacy mode
            metadata = {
                "chapters": chapters,
                "continue_from": bool(continue_from),
                "art_style": art_style,
                "aspect_ratio": aspect_ratio,
                "target_pages_per_chapter": target_pages_per_chapter or 5,
                "total_novel_pages": total_novel_pages or 50,
                "use_smart_compression": use_smart_compression if use_smart_compression is not None else True,
            }

        job = self._new_job(workflow_id, "book_chapters", metadata)
        
        # Job is saved with status="pending"
        # Background worker will pick it up and process it
        
        return job
    
    async def get_comic_config(self, workflow_id: str):
        """Get comic generation configuration for workflow"""
        from cinema.server.controllers import ComicGenerationConfig
        
        # Try to load from workflow state first
        try:
            workflow = BookWorkflow(workflow_id, self._ctx)
            if hasattr(workflow.state, 'comic_config'):
                return ComicGenerationConfig(**workflow.state.comic_config)
        except Exception:
            pass
        
        # Return defaults
        return ComicGenerationConfig()
    
    async def set_comic_config(self, workflow_id: str, config):
        """Set comic generation configuration for workflow"""
        from cinema.server.controllers import ComicGenerationConfig
        
        # Save to workflow state
        try:
            workflow = BookWorkflow(workflow_id, self._ctx)
            workflow.state.comic_config = config.model_dump()
            workflow.save_state()
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to save comic config: {e}")
        
        return config
    
    async def _run_chapters_generation(
        self,
        job_id: str,
        workflow_id: str,
        chapters: Optional[List[int]],
        continue_from: bool,
        art_style: Optional[str],
        aspect_ratio: Optional[str],
    ):
        """Background task for chapters generation."""
        import logging
        import traceback
        logger = logging.getLogger(__name__)
        
        try:
            logger.info(f"🚀 BACKGROUND TASK STARTED for job {job_id}")
            
            job = self._job_repo.get(job_id)
            if not job:
                logger.error(f"❌ Job {job_id} not found in repository!")
                return
                
            job.status = "running"
            self._job_repo.save(job)
            logger.info(f"✅ Job status updated to 'running'")
            
            logger.info(f"📄 Starting chapters generation for workflow {workflow_id}, chapters: {chapters}")
            
            wf = BookWorkflow(workflow_id, self._ctx)
            result = await wf.generate_chapters(
                chapters=chapters,
                continue_from=continue_from,
                art_style=art_style or "Print Comic Noir Style",
                aspect_ratio=aspect_ratio or "4:5",
            )
            logger.info(f"✅ Chapters generation completed: {result}")
            job.status = "completed"
            job.metadata.update(
                {
                    "chapters_generated": result.get("chapters", []),
                    "total_generated": result.get("total_generated"),
                    "output_dir": result.get("output_dir"),
                }
            )
            self._job_repo.save(job)
            logger.info(f"✅ Job {job_id} marked as completed")
        except Exception as e:
            logger.error(f"❌ EXCEPTION in background task: {e}")
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
            job = self._job_repo.get(job_id)
            if job:
                job.status = "failed"
                job.error = str(e) + "\n" + traceback.format_exc()
                self._job_repo.save(job)

    async def generate_cover(self, workflow_id: str) -> Job:
        """Generate book cover image for the given workflow."""
        
        # Validate prerequisites
        validation = await self._validate_operation(workflow_id, "generate_cover")
        if not validation.valid:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "prerequisite_not_met",
                    "operation": "generate_cover",
                    **validation.model_dump()
                }
            )

        job = self._new_job(
            workflow_id,
            "book_cover",
            {},
        )
        
        # Job is saved with status="pending"
        # Background worker will pick it up and process it
        return job

    async def generate_pages(
        self,
        workflow_id: str,
        pages: Optional[List[int]],
        continue_from: bool,
    ) -> Job:
        """Generate page images for the given workflow."""
        
        # Validate prerequisites
        validation = await self._validate_operation(workflow_id, "generate_pages")
        if not validation.valid:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "prerequisite_not_met",
                    "operation": "generate_pages",
                    **validation.model_dump()
                }
            )

        job = self._new_job(
            workflow_id,
            "book_pages",
            {"pages": pages, "continue_from": bool(continue_from)},
        )
        
        # Job is saved with status="pending"
        # Background worker will pick it up and process it
        return job
