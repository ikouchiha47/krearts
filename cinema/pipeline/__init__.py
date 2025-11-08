"""
Cinema pipeline for movie generation.
"""

from cinema.pipeline.job_tracker import JobTracker
from cinema.pipeline.movie_maker import (
    AudioGenerator,
    KeyframeGenerator,
    MovieMaker,
    ScreenplayBuilder,
    VideoGenerator,
    VideoProcessingPipeline,
    VisualCharacterBuilder,
)
from cinema.pipeline.pipeline import Pipeline, Runner
from cinema.pipeline.state import Job, JobStatus, JobType, PipelineState

__all__ = [
    # Core pipeline
    "Pipeline",
    "Runner",
    # State management
    "PipelineState",
    "Job",
    "JobStatus",
    "JobType",
    "JobTracker",
    # Stages
    "ScreenplayBuilder",
    "VisualCharacterBuilder",
    "AudioGenerator",
    "KeyframeGenerator",
    "VideoGenerator",
    "VideoProcessingPipeline",
    # Main orchestrator
    "MovieMaker",
]
