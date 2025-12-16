from __future__ import annotations

import os
import re
import uuid
from pathlib import Path
from typing import Optional, List

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel

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
    # Mirror CLI config shape loosely
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


class ChaptersRequest(BaseModel):
    chapters: Optional[str] = None   # "all" or "1,5"
    continue_from: bool = False
    art_style: Optional[str] = None
    aspect_ratio: Optional[str] = None


@router.post("/{workflow_id}/chapters", response_model=JobResponse)
async def generate_chapters(
    workflow_id: str,
    req: ChaptersRequest,
    background_tasks: BackgroundTasks,
    svc: BookWorkflowService = Depends(get_book_service),
):
    chapter_list = _parse_range(req.chapters)
    job = await svc.generate_chapters(
        workflow_id=workflow_id,
        chapters=chapter_list,
        continue_from=req.continue_from,
        art_style=req.art_style,
        aspect_ratio=req.aspect_ratio,
        background_tasks=background_tasks,
    )
    return JobResponse.from_job(job)


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


# Job status endpoint
@jobs_router.get("/{job_id}/status")
async def get_job_status(job_id: str):
    """Get the status of a background job"""
    job_repo = get_job_repository()
    job = job_repo.get(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    
    return {
        "id": job.id,
        "workflow_id": job.workflow_id,
        "type": job.type,
        "status": job.status,
        "error": job.error,
        "result": job.metadata,
    }


# List jobs for a workflow (optional type/status filters)
@workflows_router.get("/{workflow_id}/jobs")
async def list_workflow_jobs(workflow_id: str, type: Optional[str] = None, status: Optional[str] = None):
    repo = get_job_repository()
    jobs = repo.list(workflow_id=workflow_id, status=status)
    if type is not None:
        jobs = [j for j in jobs if j.type == type]
    # sort by updated_at desc
    jobs = sorted(jobs, key=lambda j: j.updated_at, reverse=True)
    return [
        {
            "id": j.id,
            "workflow_id": j.workflow_id,
            "type": j.type,
            "status": j.status,
            "error": j.error,
            "result": j.metadata,
            "created_at": j.created_at.isoformat(),
            "updated_at": j.updated_at.isoformat(),
        }
        for j in jobs
    ]


# List all workflows endpoint
@workflows_router.get("")
async def list_workflows(storage = Depends(get_storage)):
    """List all workflows"""
    from cinema.agents.bookwriter.storage import get_storybuilder_storage
    
    workflows = await storage.list_workflows("")  # Empty user_id lists all
    flow_storage = get_storybuilder_storage()
    
    result = []
    for wf in workflows:
        # Skip workflows that haven't completed content generation
        if not wf.content_done:
            continue
            
        # Extract title from StoryBuilder flow state (crew flow) - reads from database
        title = None
        try:
            flow_data = flow_storage.load(wf.id)  # This reads from storybuilder_states table
            screenplay = flow_data.get('output', {}).get('screenplay', '')
            title = extract_title_from_screenplay(screenplay)
        except Exception:
            pass
        
        # Only include workflows with a valid title
        if title:
            result.append({
                "id": wf.id,
                "title": title,
                "currentStage": wf.current_stage.value if wf.current_stage else "unknown",
                "chaptersGenerated": wf.chapters_generated,
                "pagesGenerated": wf.pages_generated,
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
    total_chapters = 0
    total_pages = 0
    
    try:
        flow_data = flow_storage.load(workflow_id)
        screenplay = flow_data.get('output', {}).get('screenplay', '')
        storyline = flow_data.get('output', {}).get('storyline', '')
        
        # Extract title from screenplay
        title = extract_title_from_screenplay(screenplay)
        
        # Try to extract total chapters/pages from storyline (JSON format)
        if storyline:
            try:
                # Storyline might be JSON with ComicBookOutput structure
                storyline_data = json.loads(storyline)
                total_chapters = storyline_data.get('total_chapters', 0)
                total_pages = storyline_data.get('total_pages', 0)
                
                # If not in root, might be in chapters array
                if not total_chapters and 'chapters' in storyline_data:
                    total_chapters = len(storyline_data.get('chapters', []))
                    # Calculate total pages from chapters
                    for chapter in storyline_data.get('chapters', []):
                        for scene in chapter.get('scenes', []):
                            total_pages += len(scene.get('pages', []))
            except (json.JSONDecodeError, AttributeError):
                # Storyline is not JSON, might be markdown
                # Try to count chapters from markdown headings
                chapter_count = storyline.count('## Chapter')
                if chapter_count > 0:
                    total_chapters = chapter_count
    except Exception:
        pass
    
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
        
        char_entry = {
            "id": char_id,  # "workflow_id_1"
            "name": character.name,
            "role": character.role,
            "ethnicity": character.ethnicity,
            "age": character.age,
            "images": images_dict,
            "imageUrl": images_dict.get('front', '')  # UI expects this field
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


# Force retry a job (reset to pending and clear existing images)
@workflows_router.post("/{workflow_id}/characters/retry")
async def retry_character_generation(workflow_id: str):
    """Reset any stuck/failed character generation jobs to pending and clear existing images for regeneration.
    If no job exists, creates a new one (upsert style)."""
    from cinema.jobs.storage import get_job_repository
    import sqlite3
    import shutil
    from pathlib import Path
    
    job_repo = get_job_repository()
    jobs = job_repo.list(workflow_id=workflow_id)
    char_jobs = [j for j in jobs if j.type == "character_generation"]
    
    # Don't delete anything - just reset the job and let generation overwrite existing files/DB entries
    
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
