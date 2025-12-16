from __future__ import annotations

from typing import Optional, List
from uuid import uuid4
import asyncio

from cinema.context import DirectorsContext
from cinema.jobs.storage import JobRepository, get_job_repository
from cinema.server.storage.interface import Job
from cinema.workflow.book_workflow import BookWorkflow

# Keep references to background tasks to prevent garbage collection
_background_tasks: set = set()

class BookWorkflowService:
    """Application service layer around BookWorkflow.

    This isolates orchestration and job tracking from HTTP/CLI surfaces so
    both can reuse the same core behavior.
    """

    def __init__(
        self,
        ctx: DirectorsContext,
        job_repo: Optional[JobRepository] = None,
    ) -> None:
        self._ctx = ctx
        self._job_repo = job_repo or get_job_repository()

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

    async def init(self, payload: dict) -> Job:
        """Initialize a new book workflow (storyline + critique)."""

        workflow_id = payload.get("workflow_id") or str(uuid4())[:8]
        job = self._new_job(
            workflow_id,
            "book_init",
            {"config_keys": list(payload.keys())},
        )

        # Run workflow execution in background
        asyncio.create_task(self._execute_init(job.id, workflow_id, payload))
        return job
    
    async def _execute_init(self, job_id: str, workflow_id: str, payload: dict):
        """Background task to execute init workflow."""
        job = self._job_repo.get(job_id)
        if not job:
            return
        
        wf = BookWorkflow(workflow_id, self._ctx)
        try:
            job.status = "running"
            self._job_repo.save(job)
            
            result = await wf.init(**payload)
            job.status = "completed"
            job.metadata["output_dir"] = wf.output_dir
            job.metadata["workflow_id"] = workflow_id
            self._job_repo.save(job)
        except Exception as e:  # pragma: no cover - defensive
            job.status = "failed"
            job.error = str(e)
            self._job_repo.save(job)

    async def generate_content(self, workflow_id: str, continue_from: bool) -> Job:
        """Generate novel content for an existing workflow."""

        job = self._new_job(
            workflow_id,
            "book_content",
            {"continue_from": bool(continue_from)},
        )
        
        # Run workflow execution in background
        asyncio.create_task(self._execute_content(job.id, workflow_id, continue_from))
        return job
    
    async def _execute_content(self, job_id: str, workflow_id: str, continue_from: bool):
        """Background task to execute content generation."""
        job = self._job_repo.get(job_id)
        if not job:
            return
        
        wf = BookWorkflow(workflow_id, self._ctx)
        try:
            job.status = "running"
            self._job_repo.save(job)
            
            result = await wf.generate_content(
                continue_from=workflow_id if continue_from else None
            )
            job.status = "completed"
            job.metadata["output_file"] = result.get("output_file")
            self._job_repo.save(job)
        except Exception as e:  # pragma: no cover - defensive
            job.status = "failed"
            job.error = str(e)
            self._job_repo.save(job)

    async def generate_chapters(
        self,
        workflow_id: str,
        chapters: Optional[List[int]],
        continue_from: bool,
        art_style: Optional[str],
        aspect_ratio: Optional[str],
        background_tasks=None,  # Unused, kept for compatibility
    ) -> Job:
        """Generate comic chapters - job will be processed by background worker."""

        job = self._new_job(
            workflow_id,
            "book_chapters",
            {
                "chapters": chapters,
                "continue_from": bool(continue_from),
                "art_style": art_style,
                "aspect_ratio": aspect_ratio,
            },
        )
        
        # Job is saved with status="pending"
        # Background worker will pick it up and process it
        
        return job
    
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

        job = self._new_job(
            workflow_id,
            "book_cover",
            {},
        )
        wf = BookWorkflow(workflow_id, self._ctx)
        try:
            result = await wf.generate_cover()
            job.status = "completed"
            job.metadata.update(
                {
                    "cover_path": result.get("cover_path"),
                    "prompt": result.get("prompt"),
                }
            )
            self._job_repo.save(job)
            return job
        except Exception as e:  # pragma: no cover - defensive
            job.status = "failed"
            job.error = str(e)
            self._job_repo.save(job)
            raise

    async def generate_pages(
        self,
        workflow_id: str,
        pages: Optional[List[int]],
        continue_from: bool,
    ) -> Job:
        """Generate page images for the given workflow (async with background task)."""
        import asyncio

        job = self._new_job(
            workflow_id,
            "book_pages",
            {"pages": pages, "continue_from": bool(continue_from)},
        )
        
        # Run in background task
        asyncio.create_task(
            self._run_pages_generation(job.id, workflow_id, pages, continue_from)
        )
        
        return job
    
    async def _run_pages_generation(
        self,
        job_id: str,
        workflow_id: str,
        pages: Optional[List[int]],
        continue_from: bool,
    ):
        """Background task for pages generation."""
        job = self._job_repo.get(job_id)
        job.status = "running"
        self._job_repo.save(job)
        
        wf = BookWorkflow(workflow_id, self._ctx)
        try:
            result = await wf.generate_pages(
                pages=pages,
                continue_from=continue_from,
            )
            job.status = "completed"
            job.metadata.update(
                {
                    "pages_generated": result.get("pages", []),
                    "total_generated": result.get("total_generated"),
                    "output_dir": result.get("output_dir"),
                }
            )
            self._job_repo.save(job)
        except Exception as e:
            job.status = "failed"
            job.error = str(e)
            self._job_repo.save(job)
