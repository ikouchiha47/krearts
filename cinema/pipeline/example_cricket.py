"""
Example: Generate The Ashes cricket promo from pre-generated screenplay.
Demonstrates jump cut technique with action sequences.
"""

import asyncio
import json
import logging
import os
from pathlib import Path

from dotenv import load_dotenv

from cinema.pipeline import JobTracker, PipelineState
from cinema.pipeline.movie_maker import (
    AudioGenerator,
    KeyframeGenerator,
    VideoGenerator,
    VideoProcessingPipeline,
    VisualCharacterBuilder,
)
from cinema.pipeline.state import Job, JobStatus, JobType
from cinema.transformers.screenplay_extractors import extract_all_stages

# Load environment variables
load_dotenv()

# Setup logging with LOG_LEVEL from .env
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


async def generate_cricket_promo():
    """
    Generate The Ashes cricket promo from pre-generated screenplay JSON.
    This demonstrates jump cut technique with multiple players in same position.
    """

    # Load the screenplay JSON
    screenplay_path = Path("cricket_ashes_screenplay.json")

    if not screenplay_path.exists():
        logger.error(f"Screenplay file not found: {screenplay_path}")
        return

    logger.info(f"Loading screenplay from {screenplay_path}")
    screenplay_json = json.loads(screenplay_path.read_text())

    # Create movie ID
    movie_id = "ashes_2024_promo"

    # Initialize tracker and state
    tracker = JobTracker("./cinema_jobs.db")
    state = PipelineState.create(movie_id, "./output")
    state.ensure_directories()

    # Set screenplay data
    state.screenplay_dict = screenplay_json

    # Create screenplay job (mark as complete)
    screenplay_job = Job(
        id=f"screenplay_{movie_id}",
        type=JobType.SCREENPLAY,
        status=JobStatus.COMPLETED,
    )
    state.add_job(screenplay_job)
    state.mark_stage_complete(JobType.SCREENPLAY)

    # Extract all stages and create jobs
    logger.info("Extracting generation stages and creating jobs...")
    extracted = extract_all_stages(screenplay_json)

    # Log what we extracted
    logger.info(f"Characters: {len(extracted['characters'].characters)}")
    logger.info(f"Image scenes: {len(extracted['images'].scenes)}")
    logger.info(f"Video scenes: {len(extracted['videos'].videos)}")
    logger.info(f"Post-production scenes: {len(extracted['post_production'].scenes)}")

    # Log the jump cut details
    logger.info("\n" + "=" * 60)
    logger.info("JUMP CUT ANALYSIS")
    logger.info("=" * 60)

    video_stage = extracted["videos"]
    for video in video_stage.videos:
        if video.scene_id == "S1_JumpCut_Batting_Montage":
            logger.info(f"\nScene: {video.scene_id}")
            logger.info(f"Method: {video.method}")
            logger.info(f"Duration: {video.duration}s")
            logger.info(
                "This scene requires 4 SEPARATE video generations with IDENTICAL framing:"
            )
            logger.info("  Cut 1 (2.0s): Steve Smith - cover drive")
            logger.info("  Cut 2 (2.5s): Joe Root - straight drive")
            logger.info("  Cut 3 (2.0s): Pat Cummins - pull shot")
            logger.info("  Cut 4 (2.5s): Ben Stokes - hook shot")
            logger.info(
                "CRITICAL: All cuts must have identical camera position and player position in frame"
            )

    # Create jobs manually
    _create_character_jobs(state, extracted)
    _create_image_jobs(state, extracted)
    _create_video_jobs(state, extracted)
    _create_post_production_jobs(state, extracted)

    logger.info(f"\nCreated {len(state.jobs)} total jobs")

    # Save initial state
    tracker.save_state(state)

    # Run each stage
    logger.info("\n" + "=" * 60)
    logger.info("Starting pipeline execution")
    logger.info("=" * 60 + "\n")

    # Stage 1: Character generation
    char_builder = VisualCharacterBuilder()
    state = await char_builder.run(state)
    tracker.save_state(state)

    # Stage 2: Audio generation
    audio_gen = AudioGenerator()
    state = await audio_gen.run(state)
    tracker.save_state(state)

    # Stage 3: Keyframe generation
    keyframe_gen = KeyframeGenerator()
    state = await keyframe_gen.run(state)
    tracker.save_state(state)

    # Stage 4: Video generation
    video_gen = VideoGenerator()
    state = await video_gen.run(state)
    tracker.save_state(state)

    # Stage 5: Post-production
    post_prod = VideoProcessingPipeline()
    state = await post_prod.run(state)
    tracker.save_state(state)

    # Final summary
    logger.info("\n" + "=" * 60)
    logger.info("✓ Pipeline execution complete!")
    progress = tracker.get_progress(movie_id)
    logger.info(f"Final: {progress['completed']}/{progress['total']} jobs completed")
    logger.info(f"Failed: {progress['failed']} jobs")
    logger.info(f"Output directory: {state.base_dir}")
    logger.info(f"Final video: {state.get_final_video_path()}")
    logger.info("=" * 60)

    # Log generation manifest
    logger.info("\n" + "=" * 60)
    logger.info("GENERATION MANIFEST")
    logger.info("=" * 60)
    manifest = screenplay_json.get("generation_manifest", {})
    for key, value in manifest.items():
        logger.info(f"\n{key}:")
        logger.info(f"  Method: {value.get('method')}")
        logger.info(f"  Duration: {value.get('duration')}s")
        if value.get("trim_to"):
            logger.info(f"  Trim to: {value.get('trim_to')}s")
        logger.info(f"  Post-edit: {value.get('post_edit')}")


def _create_character_jobs(state: PipelineState, extracted: dict) -> None:
    """Create jobs for character generation"""
    characters = extracted["characters"].characters

    for char in characters:
        for view in ["front", "side", "full_body"]:
            job = Job(
                id=f"char_{char.id}_{view}",
                type=JobType.CHARACTER,
                character_id=char.id,
                metadata={"view": view, "name": char.name},
            )
            state.add_job(job)


def _create_image_jobs(state: PipelineState, extracted: dict) -> None:
    """Create jobs for image generation"""
    image_stage = extracted["images"]

    for scene in image_stage.scenes:
        if scene.first_frame:
            job = Job(
                id=f"img_{scene.scene_id}_first",
                type=JobType.IMAGE,
                scene_id=scene.scene_id,
                metadata={"frame_type": "first_frame"},
            )
            state.add_job(job)

        if scene.last_frame:
            job = Job(
                id=f"img_{scene.scene_id}_last",
                type=JobType.IMAGE,
                scene_id=scene.scene_id,
                metadata={"frame_type": "last_frame"},
            )
            state.add_job(job)

        if scene.transition_frame:
            job = Job(
                id=f"img_{scene.scene_id}_transition",
                type=JobType.IMAGE,
                scene_id=scene.scene_id,
                metadata={"frame_type": "transition_frame"},
            )
            state.add_job(job)


def _create_video_jobs(state: PipelineState, extracted: dict) -> None:
    """Create jobs for video generation"""
    video_stage = extracted["videos"]

    for video in video_stage.videos:
        job = Job(
            id=f"video_{video.scene_id}",
            type=JobType.VIDEO,
            scene_id=video.scene_id,
            metadata={"method": video.method, "duration": video.duration},
        )
        state.add_job(job)


def _create_post_production_jobs(state: PipelineState, extracted: dict) -> None:
    """Create jobs for post-production"""
    post_stage = extracted["post_production"]

    for scene in post_stage.scenes:
        job = Job(
            id=f"post_{scene.scene_id}",
            type=JobType.POST_PRODUCTION,
            scene_id=scene.scene_id,
            metadata={
                "has_effects": scene.has_effects(),
                "has_transition": scene.has_transition(),
            },
        )
        state.add_job(job)


if __name__ == "__main__":
    asyncio.run(generate_cricket_promo())
