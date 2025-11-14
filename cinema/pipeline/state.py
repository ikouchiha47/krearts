"""
Pipeline state management for movie generation.
"""

import hashlib
import json
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from cinema.models.move_output import CinematgrapherCrewOutput


class JobStatus(str, Enum):
    """Status of a generation job"""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class JobType(str, Enum):
    """Type of generation job"""

    SCREENPLAY = "screenplay"
    CHARACTER = "character"
    CHARACTER_REF = "character_reference"
    IMAGE = "image"
    VIDEO = "video"
    POST_PRODUCTION = "post_production"


class Job(BaseModel):
    """A single generation job"""

    id: str
    type: JobType
    status: JobStatus = JobStatus.PENDING
    scene_id: Optional[str] = None
    character_id: Optional[int] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    output_path: Optional[str] = None


class PipelineState(BaseModel):
    """
    State passed between pipeline stages.
    Contains screenplay, file paths, and job tracking.
    """

    # Unique ID for this movie generation
    movie_id: str

    # Screenplay data
    screenplay: Optional[CinematgrapherCrewOutput] = None
    screenplay_dict: Optional[Dict[str, Any]] = None
    screenplay_hash: Optional[str] = (
        None  # Hash of screenplay_dict for change detection
    )

    # Directory paths
    base_dir: Path
    characters_dir: Path
    images_dir: Path
    videos_dir: Path
    audio_dir: Path
    output_dir: Path

    # Job tracking
    jobs: List[Job] = Field(default_factory=list)

    # Stage completion flags
    screenplay_complete: bool = False
    characters_complete: bool = False
    images_complete: bool = False
    videos_complete: bool = False
    post_production_complete: bool = False

    class Config:
        arbitrary_types_allowed = True

    @classmethod
    def create(cls, movie_id: str, base_dir: str = "./output") -> "PipelineState":
        """Create a new pipeline state with directory structure"""
        base_path = Path(base_dir) / movie_id

        return cls(
            movie_id=movie_id,
            base_dir=base_path,
            characters_dir=base_path / "characters",
            images_dir=base_path / "images",
            videos_dir=base_path / "videos",
            audio_dir=base_path / "audio",
            output_dir=base_path / "output",
        )

    def ensure_directories(self) -> None:
        """Create all necessary directories"""
        for dir_path in [
            self.base_dir,
            self.characters_dir,
            self.images_dir,
            self.videos_dir,
            self.audio_dir,
            self.output_dir,
        ]:
            dir_path.mkdir(parents=True, exist_ok=True)

    def add_job(self, job: Job) -> None:
        """Add a job to tracking"""
        self.jobs.append(job)

    def get_job(self, job_id: str) -> Optional[Job]:
        """Get job by ID"""
        for job in self.jobs:
            if job.id == job_id:
                return job
        return None

    def get_jobs_by_type(self, job_type: JobType) -> List[Job]:
        """Get all jobs of a specific type"""
        return [j for j in self.jobs if j.type == job_type]

    def get_jobs_by_status(self, status: JobStatus) -> List[Job]:
        """Get all jobs with a specific status"""
        return [j for j in self.jobs if j.status == status]

    def get_pending_jobs(self) -> List[Job]:
        """Get all pending jobs"""
        return self.get_jobs_by_status(JobStatus.PENDING)

    def update_job_status(
        self, job_id: str, status: JobStatus, error: Optional[str] = None
    ) -> None:
        """Update job status"""
        job = self.get_job(job_id)
        if job:
            job.status = status
            job.updated_at = datetime.now()
            if error:
                job.error = error

    def mark_stage_complete(self, stage: JobType) -> None:
        """Mark a stage as complete"""
        if stage == JobType.SCREENPLAY:
            self.screenplay_complete = True
        elif stage == JobType.CHARACTER:
            self.characters_complete = True
        elif stage == JobType.IMAGE:
            self.images_complete = True
        elif stage == JobType.VIDEO:
            self.videos_complete = True
        elif stage == JobType.POST_PRODUCTION:
            self.post_production_complete = True

    def is_stage_complete(self, stage: JobType) -> bool:
        """Check if a stage is complete"""
        if stage == JobType.SCREENPLAY:
            return self.screenplay_complete
        elif stage == JobType.CHARACTER:
            return self.characters_complete
        elif stage == JobType.IMAGE:
            return self.images_complete
        elif stage == JobType.VIDEO:
            return self.videos_complete
        elif stage == JobType.POST_PRODUCTION:
            return self.post_production_complete
        return False

    def get_character_image_path(self, character_id: int, view: str = "front") -> Path:
        """Get path for character reference image"""
        return self.characters_dir / f"char_{character_id}_{view}.png"

    def get_scene_image_path(self, scene_id: str, frame_type: str) -> Path:
        """Get path for scene keyframe image"""
        return self.images_dir / f"{scene_id}_{frame_type}.png"

    def get_scene_video_path(self, scene_id: str) -> Path:
        """Get path for scene video"""
        return self.videos_dir / f"{scene_id}.mp4"

    def get_scene_audio_path(self, scene_id: str) -> Path:
        """Get path for scene audio"""
        return self.audio_dir / f"{scene_id}.mp3"

    def get_final_video_path(self) -> Path:
        """Get path for final assembled video"""
        return self.output_dir / f"{self.movie_id}_final.mp4"

    def compute_screenplay_hash(self) -> Optional[str]:
        """Compute hash of screenplay_dict for change detection"""
        if not self.screenplay_dict:
            return None

        # Sort keys for consistent hashing
        screenplay_json = json.dumps(self.screenplay_dict, sort_keys=True)
        return hashlib.sha256(screenplay_json.encode()).hexdigest()

    def has_screenplay_changed(self, new_screenplay_dict: Dict[str, Any]) -> bool:
        """Check if new screenplay is different from stored one"""
        if not self.screenplay_hash:
            return True  # No previous hash, treat as changed

        new_json = json.dumps(new_screenplay_dict, sort_keys=True)
        new_hash = hashlib.sha256(new_json.encode()).hexdigest()

        return new_hash != self.screenplay_hash
