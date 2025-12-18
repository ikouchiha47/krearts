from __future__ import annotations

import os
import re
import uuid
from pathlib import Path
from typing import Optional, List

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel, Field

from cinema.agents.bookwriter.utils import clean_agent_thinking_from_output
from cinema.jobs.storage import get_job_repository
from cinema.server.dependencies import get_book_service, get_storage
from cinema.server.services import BookWorkflowService
from cinema.server.storage.interface import Job


router = APIRouter(prefix="/workflows/book", tags=["book"])
jobs_router = APIRouter(prefix="/jobs", tags=["jobs"])
workflows_router = APIRouter(prefix="/workflows", tags=["workflows"])


def extract_title_from_screenplay(screenplay: str) -> str | None:
    """
    Extract title from screenplay with backward compatibility.
    
    Supports:
    1. New format: "# Title: <title>" (preferred for novel writer)
    2. Old format: "# <title>" (markdown H1 heading)
    3. Handles contaminated outputs with agent thinking logs
    
    Returns:
        Title string if found, None otherwise
    """
    if not screenplay:
        return None
    
    # Clean agent thinking artifacts first
    clean_screenplay = clean_agent_thinking_from_output(screenplay)
    
    # Try new format first: # Title: <title>
    match = re.search(r'^#\s+Title:\s*(.+)$', clean_screenplay, re.MULTILINE | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    
    # Fall back to old format: first # heading that's not agent thinking
    lines = clean_screenplay.split('\n')
    for line in lines:
        line = line.strip()
        
        # Skip agent thinking logs (in case delimiter approach didn't work)
        if line.startswith(('Thought', 'Action', 'Observation', 'Final Answer')):
            continue
            
        # Look for markdown H1 heading
        match = re.match(r'^#\s+(.+)$', line)
        if match:
            title = match.group(1).strip()
            # Skip if it looks like a section heading (contains common keywords)
            if not any(keyword in title.lower() for keyword in ['world', 'context', 'characters', 'storyline', 'references']):
                return title
    
    return None


class InitBookRequest(BaseModel):
    # User-friendly inputs (minimal)
    art_styles: Optional[List[str]] = None  # Multiple art styles from UI
    user_requirements: Optional[str] = None  # Optional seed/requirements text
    
    # Advanced/optional inputs (for power users)
    characters: Optional[str] = None
    killer: Optional[str] = None
    victim: Optional[str] = None
    relationships: Optional[str] = None
    accomplices: Optional[str] = None
    witnesses: Optional[str] = None
    betrayals: Optional[str] = None
    skipper: Optional[dict] = None
    
    # Optional explicit workflow_id (otherwise generated)
    workflow_id: Optional[str] = None


class JobResponse(BaseModel):
    id: str
    workflow_id: str
    type: str
    status: str
    error: Optional[str] = None
    metadata: dict

    @classmethod
    def from_job(cls, job: Job) -> "JobResponse":
        return cls(
            id=job.id,
            workflow_id=job.workflow_id,
            type=job.type,
            status=job.status,
            error=job.error,
            metadata=job.metadata or {},
        )


@router.post("/init", response_model=JobResponse)
async def init_book(
    req: InitBookRequest,
    svc: BookWorkflowService = Depends(get_book_service),
):
    job = await svc.init(req.model_dump(exclude_unset=True))
    return JobResponse.from_job(job)





class ContentRequest(BaseModel):
    continue_from: bool = False


@router.post("/{workflow_id}/content", response_model=JobResponse)
async def generate_content(
    workflow_id: str,
    req: ContentRequest,
    svc: BookWorkflowService = Depends(get_book_service),
):
    job = await svc.generate_content(workflow_id, continue_from=req.continue_from)
    return JobResponse.from_job(job)


def _parse_range(value: Optional[str]) -> Optional[List[int]]:
    if not value or value.lower() == "all":
        return None
    try:
        return [int(x.strip()) for x in value.split(",") if x.strip()]
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid range format, use '1,5' or 'all'")


class ComicGenerationConfig(BaseModel):
    """Comic generation configuration"""
    # Chapter Controls
    total_chapters: Optional[int] = Field(default=None, ge=1, le=50, description="Total chapters (auto-detected if None)")
    pages_per_chapter: Optional[int] = Field(default=5, ge=1, le=25, description="Pages per chapter")
    chapter_style: Optional[str] = Field(default="modern", description="Chapter style: 'classic_dense' or 'modern_cinematic'")
    
    # Page Controls  
    panels_per_page: Optional[int] = Field(default=4, ge=2, le=9, description="Panels per page")
    panel_layout: Optional[str] = Field(default="dynamic", description="Panel layout: 'grid_3x3', 'grid_2x4', 'dynamic', 'custom'")
    panel_transitions: Optional[str] = Field(default="hard_cuts", description="Panel transitions: 'hard_cuts', 'smooth', 'cinematic'")
    
    # Compression Controls
    use_smart_compression: Optional[bool] = Field(default=True, description="Enable smart screenplay compression")
    context_window: Optional[int] = Field(default=1, ge=1, le=3, description="Full chapters before/after target")
    summary_window: Optional[int] = Field(default=2, ge=1, le=5, description="Summary chapters before/after context")


class ChaptersRequest(BaseModel):
    chapters: Optional[str] = None   # "all" or "1,5"
    continue_from: bool = False
    art_style: Optional[str] = None
    aspect_ratio: Optional[str] = None
    
    # Legacy fields (for backward compatibility)
    target_pages_per_chapter: Optional[int] = Field(default=None, description="Legacy: use comic_config.pages_per_chapter instead")
    total_novel_pages: Optional[int] = Field(default=None, description="Legacy: calculated from chapters * pages_per_chapter")
    use_smart_compression: Optional[bool] = Field(default=None, description="Legacy: use comic_config.use_smart_compression instead")
    
    # New comic generation config
    comic_config: Optional[ComicGenerationConfig] = Field(default_factory=ComicGenerationConfig, description="Comic generation configuration")


@router.post("/{workflow_id}/chapters", response_model=JobResponse)
async def generate_chapters(
    workflow_id: str,
    req: ChaptersRequest,
    background_tasks: BackgroundTasks,
    svc: BookWorkflowService = Depends(get_book_service),
    storage = Depends(get_storage),
):
    chapter_list = _parse_range(req.chapters)
    
    # Auto-populate art_style and aspect_ratio if not provided
    art_style = req.art_style
    aspect_ratio = req.aspect_ratio or "4:5"
    
    if not art_style:
        # Get art_style from workflow (same logic as orchestrator)
        from cinema.workflow.book_workflow import BookWorkflow
        from cinema.registry import OpenAiHerd
        from cinema.context import DirectorsContext
        
        ctx = DirectorsContext(llmstore=OpenAiHerd, debug=True)
        wf = BookWorkflow(workflow_id, ctx)
        art_style = wf._get_art_style()
    
    # Handle legacy fields vs new comic_config
    comic_config = req.comic_config or ComicGenerationConfig()
    
    # Legacy compatibility: override comic_config with legacy fields if provided
    if req.target_pages_per_chapter is not None:
        comic_config.pages_per_chapter = req.target_pages_per_chapter
    if req.use_smart_compression is not None:
        comic_config.use_smart_compression = req.use_smart_compression
    if req.total_novel_pages is not None:
        # Calculate pages_per_chapter from total_novel_pages if not explicitly set
        if req.target_pages_per_chapter is None and comic_config.total_chapters:
            comic_config.pages_per_chapter = req.total_novel_pages // comic_config.total_chapters
    
    job = await svc.generate_chapters(
        workflow_id=workflow_id,
        chapters=chapter_list,
        continue_from=req.continue_from,
        art_style=art_style,
        aspect_ratio=aspect_ratio,
        comic_config=comic_config,
        background_tasks=background_tasks,
    )
    return JobResponse.from_job(job)


@router.get("/{workflow_id}/comic-config", response_model=ComicGenerationConfig)
async def get_comic_config(
    workflow_id: str,
    svc: BookWorkflowService = Depends(get_book_service),
):
    """Get comic generation configuration for workflow"""
    return await svc.get_comic_config(workflow_id)


@router.post("/{workflow_id}/comic-config", response_model=ComicGenerationConfig)
async def set_comic_config(
    workflow_id: str,
    config: ComicGenerationConfig,
    svc: BookWorkflowService = Depends(get_book_service),
):
    """Set comic generation configuration for workflow"""
    return await svc.set_comic_config(workflow_id, config)


@router.post("/{workflow_id}/cover", response_model=JobResponse)
async def generate_cover(
    workflow_id: str,
    svc: BookWorkflowService = Depends(get_book_service),
):
    """Generate book cover image"""
    job = await svc.generate_cover(workflow_id=workflow_id)
    return JobResponse.from_job(job)


class PagesRequest(BaseModel):
    pages: Optional[str] = None   # "all" or "1,20"
    continue_from: bool = False


@router.post("/{workflow_id}/pages", response_model=JobResponse)
async def generate_pages(
    workflow_id: str,
    req: PagesRequest,
    svc: BookWorkflowService = Depends(get_book_service),
):
    page_list = _parse_range(req.pages)
    job = await svc.generate_pages(
        workflow_id=workflow_id,
        pages=page_list,
        continue_from=req.continue_from,
    )
    return JobResponse.from_job(job)


# Job status endpoint with detailed progress
@jobs_router.get("/{job_id}/status")
async def get_job_status(job_id: str):
    """Get the status of a background job with detailed progress information"""
    from cinema.agents.bookwriter.storage import get_storybuilder_storage
    
    job_repo = get_job_repository()
    job = job_repo.get(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    
    response = {
        "id": job.id,
        "workflow_id": job.workflow_id,
        "type": job.type,
        "status": job.status,
        "error": job.error,
        "result": job.metadata,
        "progress": None,  # Will be populated for flow-based jobs
    }
    
    # For flow-based jobs (book_init, book_content), get detailed progress from flow state
    if job.type in ["book_init", "book_content"] and job.status == "running":
        try:
            flow_storage = get_storybuilder_storage()
            flow_data = flow_storage.load(job.workflow_id)
            
            # Extract progress information
            current_state = flow_data.get('current_state', 'unknown')
            output = flow_data.get('output', {})
            retry_count = output.get('retry_count', 0)
            
            # Map flow states to user-friendly messages
            state_messages = {
                'plan': 'Generating storyline...',
                'critique': 'Reviewing storyline quality...',
                'evaluate': 'Evaluating critique feedback...',
                'bookerama': 'Writing novel chapters...',
                'screenplay': 'Writing screenplay...',
                'storyboard': 'Creating storyboard...',
                'success': 'Complete',
                'error': 'Error occurred',
            }
            
            response["progress"] = {
                "current_stage": current_state,
                "stage_message": state_messages.get(current_state, current_state),
                "retry_count": retry_count,
                "has_storyline": bool(output.get('storyline')),
                "has_screenplay": bool(output.get('screenplay')),
                "storyline_length": len(output.get('storyline', '')) if output.get('storyline') else 0,
            }
        except FileNotFoundError:
            # Flow state not found yet - job just started
            response["progress"] = {
                "current_stage": "initializing",
                "stage_message": "Starting...",
                "retry_count": 0,
            }
        except Exception as e:
            # Don't fail the whole request if progress lookup fails
            response["progress"] = {
                "current_stage": "unknown",
                "stage_message": "Processing...",
                "error": str(e),
            }
    
    return response


# PATCH job - unified endpoint for job actions (retry, cancel, reset)
class JobActionRequest(BaseModel):
    action: str  # "retry", "cancel", "reset"


@jobs_router.patch("/{job_id}")
async def update_job(job_id: str, req: JobActionRequest, storage = Depends(get_storage)):
    """Update job status with actions: retry, cancel, or reset.
    
    - retry: Reset failed/stuck job to pending (creates new job, aborts old)
    - cancel: Mark running/pending job as cancelled
    - reset: Hard reset to pending (clears retry_count and error)
    """
    from cinema.jobs.storage import get_job_repository
    from datetime import datetime, timedelta
    from cinema.workflow.orchestrator import WorkflowOrchestrator
    from cinema.registry import OpenAiHerd
    from cinema.context import DirectorsContext
    
    job_repo = get_job_repository()
    job = job_repo.get(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    
    action = req.action.lower()
    
    if action == "retry":
        # Use orchestrator for retry (creates new job, aborts old)
        ctx = DirectorsContext(llmstore=OpenAiHerd, debug=True)
        orchestrator = WorkflowOrchestrator(
            workflow_id=job.workflow_id,
            ctx=ctx,
            storage=storage
        )
        
        try:
            new_job = await orchestrator.retry_job(job_id)
            return {
                "status": "retried",
                "message": f"Job {job_id} aborted, new job {new_job.id} created (retry #{new_job.retry_count})",
                "old_job_id": job_id,
                "new_job_id": new_job.id,
                "job": {
                    "id": new_job.id,
                    "type": new_job.type,
                    "status": new_job.status,
                    "retry_count": new_job.retry_count
                }
            }
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
    
    elif action == "cancel":
        # Cancel: for pending or running jobs
        if job.status not in ["pending", "running"]:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot cancel job in '{job.status}' status"
            )
        
        job.status = "cancelled"
        job.updated_at = datetime.utcnow()
        job_repo.save(job)
        
        return {
            "status": "cancelled",
            "message": f"Job {job_id} cancelled",
            "job": {
                "id": job.id,
                "type": job.type,
                "status": job.status
            }
        }
    
    elif action == "reset":
        # Reset: hard reset to pending (clears everything)
        job.status = "pending"
        job.error = None
        job.retry_count = 0
        job.updated_at = datetime.utcnow()
        job_repo.save(job)
        
        return {
            "status": "reset",
            "message": f"Job {job_id} hard reset to pending",
            "job": {
                "id": job.id,
                "type": job.type,
                "status": job.status,
                "retry_count": job.retry_count
            }
        }
    
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown action '{action}'. Valid actions: retry, cancel, reset"
        )


# List jobs for a workflow (optional type/status filters) with detailed progress
@workflows_router.get("/{workflow_id}/jobs")
async def list_workflow_jobs(workflow_id: str, type: Optional[str] = None, status: Optional[str] = None):
    from datetime import datetime, timedelta, timezone
    from cinema.agents.bookwriter.storage import get_storybuilder_storage
    
    repo = get_job_repository()
    jobs = repo.list(workflow_id=workflow_id, status=status)
    if type is not None:
        jobs = [j for j in jobs if j.type == type]
    # sort by updated_at desc
    jobs = sorted(jobs, key=lambda j: j.updated_at, reverse=True)
    
    # Try to load flow state for progress information
    flow_state = None
    try:
        flow_storage = get_storybuilder_storage()
        flow_data = flow_storage.load(workflow_id)
        flow_state = {
            "current_state": flow_data.get('current_state', 'unknown'),
            "output": flow_data.get('output', {}),
        }
    except:
        pass
    
    # Add "is_stuck" flag and progress for running jobs
    now = datetime.now(timezone.utc)
    result = []
    for j in jobs:
        # Handle both timezone-aware and naive datetimes
        updated_at = j.updated_at
        if updated_at.tzinfo is None:
            updated_at = updated_at.replace(tzinfo=timezone.utc)
        time_since_update = now - updated_at
        is_stuck = j.status == "running" and time_since_update > timedelta(minutes=10)
        
        job_data = {
            "id": j.id,
            "workflow_id": j.workflow_id,
            "type": j.type,
            "status": j.status,
            "error": j.error,
            "result": j.metadata,
            "created_at": j.created_at.isoformat(),
            "updated_at": j.updated_at.isoformat(),
            "is_stuck": is_stuck,
            "seconds_since_update": int(time_since_update.total_seconds()),
            "progress": None,
        }
        
        # Add detailed progress for flow-based running jobs
        if j.status == "running" and j.type in ["book_init", "book_content"] and flow_state:
            current_state = flow_state["current_state"]
            output = flow_state["output"]
            
            # Map flow states to user-friendly messages
            state_messages = {
                'plan': 'Generating storyline...',
                'critique': 'Reviewing storyline quality...',
                'evaluate': 'Evaluating critique feedback...',
                'bookerama': 'Writing novel chapters...',
                'screenplay': 'Writing screenplay...',
                'storyboard': 'Creating storyboard...',
                'success': 'Complete',
                'error': 'Error occurred',
            }
            
            job_data["progress"] = {
                "current_stage": current_state,
                "stage_message": state_messages.get(current_state, current_state),
                "retry_count": output.get('retry_count', 0),
                "has_storyline": bool(output.get('storyline')),
                "has_screenplay": bool(output.get('screenplay')),
                "storyline_length": len(output.get('storyline', '')) if output.get('storyline') else 0,
            }
        
        result.append(job_data)
    
    return result


# Continue workflow from current state
@workflows_router.post("/{workflow_id}/continue")
async def continue_workflow(workflow_id: str, storage = Depends(get_storage)):
    """Continue workflow from current state.
    
    Examines workflow state and creates appropriate job for next operation.
    """
    from cinema.workflow.orchestrator import WorkflowOrchestrator
    from cinema.registry import OpenAiHerd
    from cinema.context import DirectorsContext
    
    ctx = DirectorsContext(llmstore=OpenAiHerd, debug=True)
    orchestrator = WorkflowOrchestrator(
        workflow_id=workflow_id,
        ctx=ctx,
        storage=storage
    )
    
    try:
        job = await orchestrator.continue_workflow()
        return {
            "status": "queued",
            "message": f"Next operation queued: {job.type}",
            "job_id": job.id,
            "job_type": job.type
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# Retry stage (current or specific)
class RetryStageRequest(BaseModel):
    stage: Optional[str] = None  # Optional: "init", "content", "chapters", "pages". If None, retries current stage.


@workflows_router.post("/{workflow_id}/retry-stage")
async def retry_stage(
    workflow_id: str, 
    req: RetryStageRequest = RetryStageRequest(),
    storage = Depends(get_storage)
):
    """Retry current stage or reset to a specific stage.
    
    If stage is provided, resets workflow to that stage (allows going back).
    If stage is None, retries the current stage.
    
    Stages: init, content, chapters, pages
    """
    from cinema.workflow.interface import WorkflowType, WorkflowStage
    from cinema.jobs.storage import get_job_repository
    from cinema.agents.bookwriter.storage import get_storybuilder_storage
    from datetime import datetime, timezone
    from uuid import uuid4
    from cinema.server.storage.interface import Job
    
    # Load workflow state
    wf_state = await storage.load_state(workflow_id, WorkflowType.BOOK)
    if not wf_state:
        raise HTTPException(status_code=404, detail=f"Workflow {workflow_id} not found")
    
    # Determine target stage
    if req.stage:
        # Map stage names to WorkflowStage enum
        stage_map = {
            "init": WorkflowStage.INIT,
            "content": WorkflowStage.CONTENT,
            "chapters": WorkflowStage.CHAPTERS,
            "pages": WorkflowStage.PAGES,
        }
        
        if req.stage not in stage_map:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid stage '{req.stage}'. Valid: {list(stage_map.keys())}"
            )
        
        target_stage = stage_map[req.stage]
    else:
        # Use current stage
        target_stage = wf_state.current_stage
    
    # Reset workflow state to target stage
    wf_state.current_stage = target_stage
    
    # Reset completion flags based on stage
    if target_stage == WorkflowStage.INIT:
        wf_state.storyline_done = False
        wf_state.content_done = False
        wf_state.characters_generated = False
        wf_state.chapters_generated = []
        wf_state.pages_generated = []
    elif target_stage == WorkflowStage.CONTENT:
        wf_state.content_done = False
        wf_state.characters_generated = False
        wf_state.chapters_generated = []
        wf_state.pages_generated = []
    elif target_stage == WorkflowStage.CHAPTERS:
        wf_state.chapters_generated = []
        wf_state.pages_generated = []
    elif target_stage == WorkflowStage.PAGES:
        wf_state.pages_generated = []
    
    # Reset flow state if going back to init or content
    if target_stage in [WorkflowStage.INIT, WorkflowStage.CONTENT]:
        try:
            flow_storage = get_storybuilder_storage()
            flow_data = flow_storage.load(workflow_id)
            
            # Reset flow to appropriate state
            if target_stage == WorkflowStage.INIT:
                flow_data['current_state'] = 'plan'
                flow_data['halted_at'] = None
                flow_data['output']['screenplay'] = None
                flow_data['output']['retry_count'] = 0
            elif target_stage == WorkflowStage.CONTENT:
                flow_data['current_state'] = 'bookerama'
                flow_data['halted_at'] = None
                flow_data['output']['screenplay'] = None  # Clear contaminated screenplay
                flow_data['output']['retry_count'] = 0
            
            flow_storage.save(workflow_id, flow_data)
        except FileNotFoundError:
            pass  # Flow state doesn't exist yet
    
    # Save updated workflow state
    await storage.save_state(wf_state)
    
    # Abort any running jobs
    job_repo = get_job_repository()
    jobs = job_repo.list(workflow_id=workflow_id)
    aborted_count = 0
    for job in jobs:
        if job.status in ["pending", "running"]:
            job.status = "aborted"
            job.updated_at = datetime.now(timezone.utc)
            job_repo.save(job)
            aborted_count += 1
    
    # Create new job for the target stage using orchestrator
    from cinema.workflow.orchestrator import WorkflowOrchestrator
    from cinema.registry import OpenAiHerd
    from cinema.context import DirectorsContext
    
    ctx = DirectorsContext(llmstore=OpenAiHerd, debug=True)
    orchestrator = WorkflowOrchestrator(workflow_id, ctx, storage=storage)
    
    # Build job metadata using centralized logic
    try:
        job_metadata = orchestrator._build_job_metadata_for_stage(target_stage, wf_state)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # Map stage to job type
    job_type_map = {
        WorkflowStage.INIT: "book_init",
        WorkflowStage.CONTENT: "book_content",
        WorkflowStage.CHAPTERS: "book_chapters",
        WorkflowStage.PAGES: "book_pages",
    }
    job_type = job_type_map[target_stage]
    
    new_job = Job(
        id=str(uuid4()),
        workflow_id=workflow_id,
        type=job_type,
        status="pending",
        metadata=job_metadata,
    )
    job_repo.save(new_job)
    
    stage_name = req.stage or target_stage.value
    return {
        "status": "reset",
        "message": f"Workflow reset to '{stage_name}' stage",
        "stage": stage_name,
        "aborted_jobs": aborted_count,
        "new_job_id": new_job.id,
        "new_job_type": job_type,
    }


# Get available art styles endpoint
@workflows_router.get("/art-styles")
async def get_art_styles():
    """Get list of available art styles from manifest"""
    from cinema.agents.bookwriter.utils import get_allowed_art_styles
    
    art_styles = get_allowed_art_styles()
    return {"art_styles": art_styles}


# List all workflows endpoint
@workflows_router.get("")
async def list_workflows(storage = Depends(get_storage)):
    """List all workflows"""
    from cinema.agents.bookwriter.storage import get_storybuilder_storage
    
    workflows = await storage.list_workflows("")  # Empty user_id lists all
    flow_storage = get_storybuilder_storage()
    
    result = []
    for wf in workflows:
        # Extract title from StoryBuilder flow state (crew flow) - reads from database
        title = None
        try:
            flow_data = flow_storage.load(wf.id)  # This reads from storybuilder_states table
            screenplay = flow_data.get('output', {}).get('screenplay', '')
            storyline = flow_data.get('output', {}).get('storyline', '')
            
            # Try to get title from screenplay first, then storyline
            title = extract_title_from_screenplay(screenplay)
            if not title and storyline:
                title = extract_title_from_screenplay(storyline)
        except Exception:
            pass
        
        # If no title found, use a placeholder based on stage
        if not title:
            if wf.current_stage.value == "init":
                title = f"Generating storyline... ({wf.id[:8]})"
            elif wf.current_stage.value == "content":
                title = f"Generating novel... ({wf.id[:8]})"
            else:
                title = f"Workflow {wf.id[:8]}"
        
        result.append({
            "id": wf.id,
            "title": title,
            "currentStage": wf.current_stage.value if wf.current_stage else "unknown",
            "chaptersGenerated": len(wf.chapters_generated),  # Return count, not array
            "pagesGenerated": len(wf.pages_generated),  # Return count, not array
            "storylineDone": wf.storyline_done,
            "contentDone": wf.content_done,
            "charactersGenerated": wf.characters_generated,
        })
    
    return result


# Get workflow state endpoint
@workflows_router.get("/{workflow_id}")
async def get_workflow(workflow_id: str, storage = Depends(get_storage)):
    """Get workflow state including screenplay, storyline, etc."""
    import json
    from cinema.agents.bookwriter.storage import get_storybuilder_storage
    from cinema.workflow.interface import WorkflowType
    
    # Load workflow state
    wf = await storage.load_state(workflow_id, WorkflowType.BOOK)
    
    if not wf:
        raise HTTPException(status_code=404, detail=f"Workflow {workflow_id} not found")
    
    # Load crew flow data to get screenplay and storyline
    flow_storage = get_storybuilder_storage()
    title = None
    screenplay = None
    storyline = None
    
    try:
        flow_data = flow_storage.load(workflow_id)
        screenplay = flow_data.get('output', {}).get('screenplay', '')
        storyline = flow_data.get('output', {}).get('storyline', '')
        
        # Extract title from screenplay
        title = extract_title_from_screenplay(screenplay)
    except Exception:
        pass
    
    # Get total chapters from screenplay (expected total)
    total_chapters = 0
    if screenplay:
        total_chapters = screenplay.count('### Chapter')
    
    # If no screenplay, try storyline
    if not total_chapters and storyline:
        total_chapters = storyline.count('### Chapter')
    
    # Get total pages from generated chapters (sum of pages arrays in chapter_json)
    total_pages = 0
    try:
        import sqlite3
        db_path = os.getenv("COMIC_METADATA_SQLITE_PATH", "./cinema_server.db")
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Get total_pages from each chapter's JSON
            cursor.execute("""
                SELECT json_extract(chapter_json, '$.total_pages')
                FROM chapters 
                WHERE workflow_id = ?
            """, (workflow_id,))
            
            for row in cursor.fetchall():
                if row[0]:
                    total_pages += int(row[0])
    except Exception:
        pass
    
    # Get available/blocked actions
    from cinema.workflow.validator import WorkflowStateValidator
    validator = WorkflowStateValidator()
    available_actions = validator._get_available_actions(wf)
    blocked_actions = validator._get_blocked_actions(wf)
    
    # Build stages array dynamically
    stages = [
        {
            "id": "plot",
            "label": "Plot",
            "completed": wf.storyline_done,
            "active": wf.current_stage.value == "init",
        },
        {
            "id": "novel",
            "label": "Novel",
            "completed": wf.content_done,
            "active": wf.current_stage.value == "content",
        },
        {
            "id": "characters",
            "label": "Characters",
            "completed": wf.characters_generated,
            "active": wf.current_stage.value == "chapters" and not wf.characters_generated,
        },
        {
            "id": "chapters",
            "label": "Chapters",
            "completed": len(wf.chapters_generated) > 0,
            "active": wf.current_stage.value == "chapters" and wf.characters_generated,
        },
        {
            "id": "pages",
            "label": "Pages",
            "completed": len(wf.pages_generated) > 0,
            "active": wf.current_stage.value == "pages",
        },
    ]
    
    return {
        "id": wf.id,
        "title": title or "Untitled",
        "currentStage": wf.current_stage.value if wf.current_stage else "unknown",
        "screenplay": screenplay or "",
        "storyline": storyline or "",
        "totalChapters": total_chapters,
        "totalPages": total_pages,
        "chaptersGenerated": wf.chapters_generated,
        "pagesGenerated": wf.pages_generated,
        "coverGenerated": wf.cover_generated,
        "charactersGenerated": wf.characters_generated,
        "storylineDone": wf.storyline_done,
        "contentDone": wf.content_done,
        "stages": stages,  # NEW: Dynamic stages array
        "availableActions": available_actions,
        "blockedActions": blocked_actions,
    }


# List chapters endpoint
@workflows_router.get("/{workflow_id}/chapters")
async def list_chapters(workflow_id: str, storage = Depends(get_storage)):
    """List all chapters for a workflow"""
    import sqlite3
    import json
    
    db_path = os.getenv("COMIC_METADATA_SQLITE_PATH", "./cinema_server.db")
    table = os.getenv("COMIC_METADATA_SQLITE_CHAPTER_TABLE", "chapters")
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute(
        f"SELECT chapter_number, chapter_json FROM {table} WHERE workflow_id = ? ORDER BY chapter_number",
        (workflow_id,)
    )
    
    result = []
    for row in cursor.fetchall():
        comic_data = json.loads(row['chapter_json'])
        chapter_num = row['chapter_number']
        
        # The stored JSON is the full ComicBookOutput, chapters are nested inside
        # Each row stores only ONE chapter in the chapters array at index 0
        chapters_list = comic_data.get('chapters', [])
        
        if chapters_list:
            # Always use index 0 since each row only has one chapter
            chapter_data = chapters_list[0]
            
            # Use chapter title if available, otherwise "Chapter X"
            chapter_title = chapter_data.get('title') or chapter_data.get('chapter_title') or f"Chapter {chapter_num}"
            
            result.append({
                "chapterNumber": chapter_num,
                "title": chapter_title,
                "scenes": len(chapter_data.get('scenes', [])),
                "pages": sum(len(scene.get('pages', [])) for scene in chapter_data.get('scenes', []))
            })
    
    conn.close()
    return result


# List pages endpoint
@workflows_router.get("/{workflow_id}/pages")
async def list_pages(workflow_id: str, storage = Depends(get_storage)):
    """List all pages for a workflow"""
    import sqlite3
    import json
    
    db_path = os.getenv("COMIC_METADATA_SQLITE_PATH", "./cinema_server.db")
    table = os.getenv("COMIC_METADATA_SQLITE_CHAPTER_TABLE", "chapters")
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute(
        f"SELECT chapter_number, chapter_json FROM {table} WHERE workflow_id = ? ORDER BY chapter_number",
        (workflow_id,)
    )
    
    result = []
    page_counter = 0
    
    for row in cursor.fetchall():
        comic_data = json.loads(row['chapter_json'])
        chapter_num = row['chapter_number']
        
        # The stored JSON is the full ComicBookOutput, chapters are nested inside
        # Each row stores only ONE chapter in the chapters array at index 0
        chapters_list = comic_data.get('chapters', [])
        
        if chapters_list:
            # Always use index 0 since each row only has one chapter
            chapter_data = chapters_list[0]
            
            for scene_idx, scene in enumerate(chapter_data.get('scenes', [])):
                for page_idx, page in enumerate(scene.get('pages', [])):
                    page_counter += 1
                    result.append({
                        "number": page_counter,
                        "chapterNumber": chapter_num,
                        "sceneNumber": scene_idx + 1,
                        "pageInScene": page_idx + 1,
                        "description": page.get('description', ''),
                        "imageUrl": page.get('image_url', None),
                    })
    
    conn.close()
    return result


# List characters endpoint  
@workflows_router.get("/{workflow_id}/characters")
async def list_characters(workflow_id: str, storage = Depends(get_storage)):
    """List all characters for a workflow from characters table"""
    from cinema.db.characters import CharacterStore
    
    # Get characters from database
    store = CharacterStore()
    characters_with_images = store.get_characters_with_images(workflow_id)
    
    # If no characters in DB, return empty list
    if not characters_with_images:
        return []
    
    asset_base_url = os.getenv("ASSET_BASE_URL", "")
    asset_base_path = os.getenv("ASSET_BASE_PATH", "./output")
    
    # Build response with character data and image URLs
    result = []
    for char_id, data in characters_with_images.items():
        character = data["character"]
        images_dict = {}
        
        # Convert image paths to URLs
        for view_type, image_path in data["images"].items():
            # Strip asset_base_path prefix if present
            if asset_base_path:
                base_to_strip = asset_base_path.lstrip('./')
                if image_path.startswith(base_to_strip):
                    image_path = image_path[len(base_to_strip):].lstrip('/')
            
            if asset_base_url:
                full_url = f"{asset_base_url.rstrip('/')}/{image_path}"
            else:
                full_url = f"/assets/{image_path}"
            
            images_dict[view_type] = full_url
        
        # Parse role to extract clean role name (remove markdown formatting)
        # Example: "- **Role:** detective" -> "detective"
        # Example: "- **Role:** killer\n- **Primary Detective:** Detective Rowan Vega" -> "killer"
        clean_role = character.role
        if clean_role:
            # Extract role from markdown format
            import re
            role_match = re.search(r'-\s*\*\*Role:\*\*\s*(\w+)', clean_role)
            if role_match:
                clean_role = role_match.group(1)
            else:
                # Fallback: just take first word if no markdown
                clean_role = clean_role.split()[0] if clean_role.split() else clean_role
        
        char_entry = {
            "id": char_id,  # "workflow_id_1"
            "name": character.name,
            "role": clean_role,  # Cleaned role (e.g., "detective", "killer", "victim")
            "ethnicity": character.ethnicity,
            "age": character.age,
            "full_text": character.full_text,  # Full markdown character description
            "images": images_dict,
            "imageUrl": images_dict.get('front', images_dict.get('full_body', ''))  # Fallback to full_body if no front
        }
        result.append(char_entry)
    
    return result


# Generate character images endpoint
@workflows_router.post("/{workflow_id}/characters/generate")
async def generate_character_images(workflow_id: str):
    """Generate character images for a workflow"""
    from cinema.jobs.storage import get_job_repository
    from cinema.server.storage.interface import Job
    import uuid
    import sqlite3
    
    job_repo = get_job_repository()
    
    # Check for existing running/pending job
    existing_jobs = job_repo.list(workflow_id=workflow_id)
    char_jobs = [j for j in existing_jobs if j.type == "character_generation" and j.status in ["pending", "running"]]
    
    if char_jobs:
        return {
            "status": "already_running",
            "message": f"Character generation already in progress (job {char_jobs[0].id})",
            "job_id": char_jobs[0].id
        }
    
    # Check if images already exist in database
    db_path = os.getenv("COMIC_METADATA_SQLITE_PATH", "./cinema_server.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT COUNT(*) as count FROM character_images WHERE workflow_id = ?",
        (workflow_id,)
    )
    image_count = cursor.fetchone()[0]
    conn.close()
    
    if image_count > 0:
        # Check for completed job
        completed_jobs = [j for j in existing_jobs if j.type == "character_generation" and j.status == "completed"]
        if completed_jobs:
            return {
                "status": "already_completed",
                "message": "Character images already generated. Use Retry to regenerate.",
                "job_id": completed_jobs[0].id
            }
    
    # Create new job with status="pending" so worker picks it up
    job_id = str(uuid.uuid4())
    
    job = Job(
        id=job_id,
        workflow_id=workflow_id,
        type="character_generation",
        status="pending",  # Worker will pick this up
        metadata={}
    )
    job_repo.save(job)
    
    return {"status": "queued", "message": "Character image generation queued", "job_id": job_id}


# Deprecated: Use PATCH /jobs/{job_id} with action="retry" instead
# Kept for backward compatibility
@workflows_router.post("/{workflow_id}/characters/retry")
async def retry_character_generation(workflow_id: str):
    """DEPRECATED: Use PATCH /jobs/{job_id} with action='retry' instead.
    
    This endpoint is kept for backward compatibility but will be removed in a future version."""
    from cinema.jobs.storage import get_job_repository
    
    job_repo = get_job_repository()
    jobs = job_repo.list(workflow_id=workflow_id)
    char_jobs = [j for j in jobs if j.type == "character_generation"]
    
    if not char_jobs:
        # No existing job - create new one (upsert style)
        job_id = str(uuid.uuid4())
        new_job = Job(
            id=job_id,
            workflow_id=workflow_id,
            type="character_generation",
            status="pending",
            metadata={"retry": True, "force_regenerate": True}
        )
        job_repo.save(new_job)
        
        return {
            "status": "created",
            "message": f"New character generation job created and queued",
            "job_id": job_id
        }
    
    # Get the most recent job and reset it
    latest_job = sorted(char_jobs, key=lambda j: j.updated_at, reverse=True)[0]
    
    # Reset job to pending
    latest_job.status = "pending"
    latest_job.error = None
    latest_job.metadata = {"retry": True, "force_regenerate": True}
    job_repo.save(latest_job)
    
    return {
        "status": "reset",
        "message": f"Job {latest_job.id} reset to pending. Images cleared for regeneration.",
        "job_id": latest_job.id
    }


# Regenerate a single character
@workflows_router.post("/{workflow_id}/characters/{character_id}/regenerate")
async def regenerate_single_character(workflow_id: str, character_id: str):
    """
    Regenerate images for a single character.
    
    Args:
        workflow_id: Workflow ID (e.g., "d7dd6092")
        character_id: Character ID (e.g., "d7dd6092_1")
    
    Returns:
        Job status with job_id for tracking
    """
    from cinema.jobs.storage import get_job_repository
    from cinema.server.storage.interface import Job
    import uuid
    
    # Delete existing images for this character
    import sqlite3
    conn = sqlite3.connect("cinema_server.db", timeout=30.0)
    conn.execute("PRAGMA journal_mode=WAL")
    cursor = conn.cursor()
    
    # Get image paths before deleting
    cursor.execute("""
        SELECT image_path FROM character_images 
        WHERE character_id = ?
    """, (character_id,))
    
    image_paths = [row[0] for row in cursor.fetchall()]
    
    # Delete from database
    cursor.execute("""
        DELETE FROM character_images 
        WHERE character_id = ?
    """, (character_id,))
    conn.commit()
    conn.close()
    
    # Delete physical files
    for image_path in image_paths:
        try:
            Path(image_path).unlink(missing_ok=True)
        except Exception as e:
            print(f"Warning: Could not delete {image_path}: {e}")
    
    # Create a new job for single character regeneration
    job_repo = get_job_repository()
    job_id = str(uuid.uuid4())
    
    new_job = Job(
        id=job_id,
        workflow_id=workflow_id,
        type="character_generation",
        status="pending",
        metadata={
            "single_character": True,
            "character_id": character_id,
            "force_regenerate": True
        }
    )
    job_repo.save(new_job)
    
    return {
        "status": "created",
        "message": f"Regeneration job created for character {character_id}",
        "job_id": job_id,
        "character_id": character_id
    }
