#!/usr/bin/env python3
"""Background worker that processes jobs from SQLite queue.

Run this separately from the API server:
    python -m cinema.server.worker
"""

import asyncio
import logging
import time
from typing import Optional

# Load environment variables first
from dotenv import load_dotenv
load_dotenv()

from cinema.context import DirectorsContext
from cinema.jobs.storage import get_job_repository
from cinema.registry import OpenAiHerd
from cinema.workflow.book_workflow import BookWorkflow

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class JobWorker:
    """Background worker that processes jobs from the SQLite queue."""
    
    def __init__(self, poll_interval: float = 2.0):
        self.poll_interval = poll_interval
        self.job_repo = get_job_repository()
        
        # Initialize context with LLM store (same as server)
        self.ctx = DirectorsContext(llmstore=OpenAiHerd, debug=True)
        self.running = False
    
    async def process_job(self, job_id: str) -> None:
        """Process a single job."""
        job = self.job_repo.get(job_id)
        if not job:
            logger.error(f"Job {job_id} not found!")
            return
        
        logger.info(f"🚀 Processing job {job_id} (type: {job.type})")
        
        # Update to running
        job.status = "running"
        self.job_repo.save(job)
        
        try:
            wf = BookWorkflow(job.workflow_id, self.ctx)
            
            if job.type == "book_chapters":
                # Extract parameters from metadata
                chapters = job.metadata.get("chapters")
                continue_from = job.metadata.get("continue_from", False)
                art_style = job.metadata.get("art_style", "Print Comic Noir Style")
                aspect_ratio = job.metadata.get("aspect_ratio", "4:5")
                
                logger.info(f"   Generating chapters: {chapters}")
                result = await wf.generate_chapters(
                    chapters=chapters,
                    continue_from=continue_from,
                    art_style=art_style,
                    aspect_ratio=aspect_ratio,
                )
                
                job.status = "completed"
                job.metadata.update({
                    "chapters_generated": result.get("chapters", []),
                    "total_generated": result.get("total_generated"),
                    "output_dir": result.get("output_dir"),
                })
                
            elif job.type == "book_pages":
                pages = job.metadata.get("pages")
                continue_from = job.metadata.get("continue_from", False)
                
                logger.info(f"   Generating pages: {pages}")
                result = await wf.generate_pages(
                    pages=pages,
                    continue_from=continue_from,
                )
                
                job.status = "completed"
                job.metadata.update({
                    "pages_generated": result.get("pages", []),
                    "total_generated": result.get("total_generated"),
                    "output_dir": result.get("output_dir"),
                })
                
            elif job.type == "character_generation":
                from cinema.pipeline.shared.generators import generate_character_images_for_workflow
                
                logger.info(f"   Generating character images for workflow {job.workflow_id}")
                await generate_character_images_for_workflow(job.workflow_id, job.id)
                
                # Status is updated inside generate_character_images_for_workflow
                # Refresh job from DB to get updated status
                job = self.job_repo.get(job.id)
                logger.info(f"   Character generation task completed with status: {job.status if job else 'unknown'}")
                
            else:
                logger.warning(f"Unknown job type: {job.type}")
                job.status = "failed"
                job.error = f"Unknown job type: {job.type}"
                self.job_repo.save(job)
            
            # Save job status (for character_generation, this will save the refreshed status from DB)
            if job and job.type != "character_generation":
                self.job_repo.save(job)
                logger.info(f"✅ Job {job_id} completed")
            
        except Exception as e:
            logger.exception(f"❌ Job {job_id} failed: {e}")
            # For character_generation, the error might already be saved, so refresh first
            if job and job.type == "character_generation":
                fresh_job = self.job_repo.get(job.id)
                if fresh_job and fresh_job.status != "failed":
                    fresh_job.status = "failed"
                    fresh_job.error = str(e)
                    self.job_repo.save(fresh_job)
            elif job:
                job.status = "failed"
                job.error = str(e)
                self.job_repo.save(job)
    
    async def run(self) -> None:
        """Main worker loop - poll for pending jobs and process them."""
        self.running = True
        logger.info("🔄 Worker started, polling for jobs...")
        
        while self.running:
            try:
                # Get all pending jobs
                pending_jobs = self.job_repo.list(status="pending")
                
                if pending_jobs:
                    logger.info(f"📋 Found {len(pending_jobs)} pending jobs")
                    
                    # Process each job
                    for job in pending_jobs:
                        await self.process_job(job.id)
                
                # Sleep before next poll
                await asyncio.sleep(self.poll_interval)
                
            except KeyboardInterrupt:
                logger.info("⏹️  Worker stopped by user")
                self.running = False
                break
            except Exception as e:
                logger.exception(f"Worker error: {e}")
                await asyncio.sleep(self.poll_interval)
    
    def stop(self) -> None:
        """Stop the worker."""
        self.running = False


async def main():
    """Run the worker."""
    worker = JobWorker(poll_interval=2.0)
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
