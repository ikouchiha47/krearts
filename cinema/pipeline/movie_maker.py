"""
Movie generation pipeline implementation.
"""

import logging
import uuid
from pathlib import Path
from typing import Any, Dict, Optional

from cinema.agents.scriptwriter.crew import (
    Enhancer,
    EnhancerInputSchema,
    ScriptWriter,
    ScriptWriterSchema,
)
from cinema.models import CinematgrapherCrewOutput
from cinema.pipeline.pipeline import Runner
from cinema.pipeline.state import Job, JobStatus, JobType, PipelineState
from cinema.providers.gemini import GeminiMediaGen
from cinema.transformers.screenplay_extractors import extract_all_stages

logger = logging.getLogger(__name__)


class ScreenplayBuilder(Runner[ScriptWriterSchema, CinematgrapherCrewOutput]):
    """
    Stage 0: Generate screenplay from script.
    Takes ScriptWriterSchema, returns structured screenplay.
    """

    def __init__(self, writer: ScriptWriter, enhancer: Enhancer) -> None:
        self.writer = writer
        self.enhancer = enhancer

    async def run(self, inputs: ScriptWriterSchema) -> CinematgrapherCrewOutput:
        logger.info("Starting screenplay generation...")
        logger.debug(f"Script length: {len(inputs.script)} chars")

        # Generate screenplay
        logger.info("Running ScriptWriter crew...")
        script_output = await self.writer.crew().kickoff_async(
            inputs=inputs.to_crew(),
        )

        screenplay = ScriptWriter.collect(script_output)
        logger.info("ScriptWriter complete, collecting output")

        # Enhance screenplay
        logger.info("Running Enhancer crew...")
        _, meta = self.enhancer.get_meta_config()
        logger.info(f"⚙️ Meta config {meta}")

        enhancer_inputs = EnhancerInputSchema(
            script=inputs.script,
            screenplay=screenplay,
            video_durations=meta.get("video_durations", []),
        )

        enhancer_output = await self.enhancer.crew().kickoff_async(
            inputs=enhancer_inputs.to_crew(),
        )

        structured_script_result = Enhancer.collect(
            enhancer_output,
            CinematgrapherCrewOutput,
        )

        if not isinstance(structured_script_result, CinematgrapherCrewOutput):
            logger.error("Failed to generate structured screenplay")
            raise ValueError("Failed to generate structured screenplay")

        logger.info("Screenplay generation complete")
        return structured_script_result

    def _create_character_jobs(self, state: PipelineState, extracted: dict) -> None:
        """Create jobs for character generation"""
        characters = extracted["characters"].characters

        for char in characters:
            for view in ["front", "side", "full_body", "back"]:
                job = Job(
                    id=f"char_{char.id}_{view}",
                    type=JobType.CHARACTER,
                    character_id=char.id,
                    metadata={"view": view, "name": char.name},
                )
                state.add_job(job)

    def _create_image_jobs(
        self,
        state: PipelineState,
        extracted: dict,
    ) -> None:
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

    def _create_video_jobs(
        self,
        state: PipelineState,
        extracted: dict,
    ) -> None:
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

    def _create_post_production_jobs(
        self, state: PipelineState, extracted: dict
    ) -> None:
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


class VisualCharacterBuilder(Runner[PipelineState, PipelineState]):
    """
    Stage 1: Generate character reference images using seeding chain.

    Uses CharacterReferenceManager to ensure consistent character appearance:
    1. Front view generated first (canonical, no reference)
    2. Side and full_body views seeded from front view
    3. All views maintain consistent character appearance
    """

    async def run(self, inputs: PipelineState) -> PipelineState:
        from cinema.workflow.character_manager import CharacterReferenceManager

        state = inputs
        logger.info("=== Stage 1: Character Reference Generation (Seeding Chain) ===")

        if state.is_stage_complete(JobType.CHARACTER):
            logger.info("Characters already generated, skipping...")
            return state

        # Get character jobs (including failed jobs for retry)
        char_jobs = state.get_jobs_by_type(JobType.CHARACTER)
        pending = [
            j for j in char_jobs if j.status in [JobStatus.PENDING, JobStatus.FAILED]
        ]

        if not pending:
            logger.info("No pending character jobs")
            state.mark_stage_complete(JobType.CHARACTER)
            return state

        if not state.screenplay_dict:
            raise ValueError("No screenplay data available")

        extracted = extract_all_stages(state.screenplay_dict)
        char_stage = extracted["characters"]

        gemini = GeminiMediaGen()
        char_manager = CharacterReferenceManager(gemini)

        # Group jobs by character to use seeding chain
        chars_to_generate = {}
        for job in pending:
            char_id = job.character_id
            if not char_id:
                job.status = JobStatus.SKIPPED
                continue

            if char_id not in chars_to_generate:
                chars_to_generate[char_id] = []
            chars_to_generate[char_id].append(job)

        logger.info(
            f"Generating references for {len(chars_to_generate)} characters using seeding chain..."
        )

        # Generate each character using seeding chain
        for char_id, jobs in chars_to_generate.items():
            try:
                # Get character info
                char = char_stage.get_character(char_id)
                if not char:
                    for job in jobs:
                        job.status = JobStatus.SKIPPED
                    continue

                logger.info(f"🎭 Character: {char.name} (ID: {char_id})")

                # Check if all views already exist (caching)
                all_cached = True
                for job in jobs:
                    view = job.metadata["view"]
                    output_path = state.get_character_image_path(char_id, view)
                    if not (output_path.exists() and output_path.stat().st_size > 0):
                        all_cached = False
                        break

                if all_cached:
                    logger.info(f"  ⊙ All views cached for {char.name}")
                    for job in jobs:
                        view = job.metadata["view"]
                        output_path = state.get_character_image_path(char_id, view)
                        job.output_path = str(output_path)
                        job.status = JobStatus.COMPLETED
                    continue

                # Build character description for CharacterReferenceManager
                character_description = {
                    "physical_appearance": char.description,
                    "style": "",  # Style is embedded in description
                }

                # Generate all views using seeding chain
                # Front → Side → Full Body (all seeded from front)
                logger.info(f"  📸 Generating views with seeding chain...")
                results = await char_manager.generate_character_references(
                    character_id=f"CHAR_{char_id}",
                    character_description=character_description,
                    output_dir=str(state.characters_dir),
                    include_back_view=False,  # Only generate front, side, full_body
                )

                # Update job statuses
                for job in jobs:
                    view = job.metadata["view"]
                    if view in results:
                        job.output_path = results[view]
                        job.status = JobStatus.COMPLETED
                        logger.info(f"  ✓ {char.name} - {view}")
                    else:
                        job.status = JobStatus.FAILED
                        job.error = f"View {view} not generated"
                        logger.error(f"  ✗ {char.name} - {view} not generated")

            except Exception as e:
                for job in jobs:
                    job.status = JobStatus.FAILED
                    job.error = str(e)
                logger.error(f"  ✗ Failed character {char_id}: {e}")

        # Only mark stage complete if no jobs failed
        failed_count = len([j for j in char_jobs if j.status == JobStatus.FAILED])
        if failed_count == 0:
            state.mark_stage_complete(JobType.CHARACTER)
            logger.info("✅ Character generation complete (seeding chain)")
        else:
            logger.warning(
                f"Character stage has {failed_count} failed jobs - will retry on next run"
            )

        return state


class AudioGenerator(Runner[PipelineState, PipelineState]):
    """
    Generate audio from 11labs.
    Extracts durations and timing info.
    """

    async def run(self, inputs: PipelineState) -> PipelineState:
        state = inputs
        logger.info("=== Stage 2: Audio Generation ===")
        # TODO: Implement audio generation
        # For now, return mock durations
        logger.warning("Audio generation not yet implemented, using mock durations...")
        return state


class KeyframeGenerator(Runner[PipelineState, PipelineState]):
    """
    Stage 2: Generate keyframe images for scenes.
    Generates first_frame, last_frame, and transition_frame images.
    """

    async def run(self, inputs: PipelineState) -> PipelineState:
        state = inputs
        logger.info("=== Stage 3: Keyframe Image Generation ===")

        if state.is_stage_complete(JobType.IMAGE):
            logger.info("Keyframes already generated, skipping...")
            return state

        # Get image jobs (including failed jobs for retry)
        image_jobs = state.get_jobs_by_type(JobType.IMAGE)
        pending = [
            j for j in image_jobs if j.status in [JobStatus.PENDING, JobStatus.FAILED]
        ]

        if not pending:
            logger.info("No pending image jobs")
            state.mark_stage_complete(JobType.IMAGE)
            return state

        logger.info(f"Generating {len(pending)} keyframe images...")

        if not state.screenplay_dict:
            raise ValueError("No screenplay data available")

        extracted = extract_all_stages(state.screenplay_dict)
        image_stage = extracted["images"]

        for job in pending:
            try:
                job.status = JobStatus.IN_PROGRESS

                scene_id = job.scene_id
                if not scene_id:
                    job.status = JobStatus.SKIPPED
                    continue

                frame_type = job.metadata["frame_type"]

                # Get scene and prompt
                scene = image_stage.get_scene(scene_id)
                if not scene:
                    job.status = JobStatus.SKIPPED
                    continue

                # Get the appropriate frame spec
                frame_spec = None
                if frame_type == "first_frame":
                    frame_spec = scene.first_frame
                elif frame_type == "last_frame":
                    frame_spec = scene.last_frame
                elif frame_type == "transition_frame":
                    frame_spec = scene.transition_frame

                if not frame_spec:
                    job.status = JobStatus.SKIPPED
                    continue

                # Log prompt in debug mode
                logger.debug(
                    f"Keyframe prompt for {scene_id} ({frame_type}):\n{frame_spec.prompt}"
                )

                # Check if output already exists (caching)
                output_path = state.get_scene_image_path(scene_id, frame_type)

                if output_path.exists() and output_path.stat().st_size > 0:
                    logger.info(f"  ⊙ Cached {scene_id} - {frame_type} (file exists)")
                    job.output_path = str(output_path)
                    job.status = JobStatus.COMPLETED
                    continue

                # Generate image
                await self._generate_image(
                    frame_spec.prompt,
                    output_path,
                    frame_spec.aspect_ratio,
                    frame_spec.character_refs,
                    state,
                )

                job.output_path = str(output_path)
                job.status = JobStatus.COMPLETED

                logger.info(f"  ✓ Generated {scene_id} - {frame_type}")

            except Exception as e:
                job.status = JobStatus.FAILED
                job.error = str(e)
                logger.error(f"  ✗ Failed {job.id}: {e}")

        # Only mark stage complete if no jobs failed
        failed_count = len([j for j in image_jobs if j.status == JobStatus.FAILED])
        if failed_count == 0:
            state.mark_stage_complete(JobType.IMAGE)
        else:
            logger.warning(
                f"Image stage has {failed_count} failed jobs - will retry on next run"
            )

        return state

    async def _generate_image(
        self,
        prompt: str,
        output_path: Path,
        aspect_ratio: str,
        character_refs: list,
        state: PipelineState,
    ) -> None:
        """Generate image using Gemini Imagen with optional character references"""
        output_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            gemini = GeminiMediaGen()

            # TODO: Handle multiple character references
            # For now, use first character reference if available
            reference_image = None
            if character_refs and len(character_refs) > 0:
                char_id = character_refs[0]
                # Use front view as reference
                ref_path = state.get_character_image_path(char_id, "front")
                if ref_path.exists():
                    reference_image = str(ref_path)
                    logger.debug(f"Using character reference: {reference_image}")

            # Generate image
            if reference_image:
                response = await gemini.generate_content(
                    prompt=prompt, reference_image=reference_image
                )
            else:
                response = await gemini.generate_content(prompt=prompt)

            # Save the generated image
            gemini.render_image(str(output_path), response)
            logger.info(f"✓ Keyframe image saved to: {output_path}")

        except Exception as e:
            logger.error(f"Failed to generate keyframe image: {e}")
            raise


class VideoGenerator(Runner[PipelineState, PipelineState]):
    """
    Stage 3: Generate videos using intelligent workflow selection.

    Uses VeoWorkflowOrchestrator to automatically select the optimal workflow
    (interpolation, ingredients, timestamp, etc.) based on scene metadata.
    """

    def __init__(self, workflow_config: Optional[Dict[str, Any]] = None):
        """
        Initialize VideoGenerator with optional workflow configuration.

        Args:
            workflow_config: Optional dict with workflow configuration options
        """
        self.workflow_config = workflow_config or {}

    async def run(self, inputs: PipelineState) -> PipelineState:
        state = inputs
        logger.info(
            "=== Stage 4: Video Generation (Intelligent Workflow Selection) ==="
        )

        if state.is_stage_complete(JobType.VIDEO):
            logger.info("Videos already generated, skipping...")
            return state

        # Get video jobs (including failed jobs for retry)
        video_jobs = state.get_jobs_by_type(JobType.VIDEO)
        pending = [
            j for j in video_jobs if j.status in [JobStatus.PENDING, JobStatus.FAILED]
        ]

        if not pending:
            logger.info("No pending video jobs")
            state.mark_stage_complete(JobType.VIDEO)
            return state

        logger.info(f"Generating {len(pending)} videos with workflow orchestrator...")

        if not state.screenplay_dict:
            raise ValueError("No screenplay data available")

        # Initialize workflow orchestrator
        from cinema.workflow.integration_helpers import (
            convert_pipeline_state_to_asset_map,
            convert_scene_to_classifier_input,
            get_scene_from_screenplay,
        )
        from cinema.workflow.models import WorkflowConfig, WorkflowSelectionMode
        from cinema.workflow.orchestrator import VeoWorkflowOrchestrator

        gemini = GeminiMediaGen()

        # Build WorkflowConfig from pipeline config
        config = WorkflowConfig(
            selection_mode=WorkflowSelectionMode(
                self.workflow_config.get("selection_mode", "llm_intelligent")
            ),
            use_llm_for_workflow_decision=self.workflow_config.get(
                "use_llm_for_workflow_decision", True
            ),
            log_workflow_decisions=self.workflow_config.get(
                "log_workflow_decisions", True
            ),
            export_metrics=self.workflow_config.get("export_metrics", True),
            metrics_output_path=self.workflow_config.get(
                "metrics_output_path", "output/workflow_metrics.json"
            ),
        )

        orchestrator = VeoWorkflowOrchestrator(gemini, config)

        for job in pending:
            try:
                job.status = JobStatus.IN_PROGRESS

                scene_id = job.scene_id
                if not scene_id:
                    job.status = JobStatus.SKIPPED
                    continue

                # Check if output already exists (caching)
                output_path = state.get_scene_video_path(scene_id)

                if output_path.exists() and output_path.stat().st_size > 0:
                    logger.info(f"  ⊙ Cached {scene_id} (file exists)")
                    job.output_path = str(output_path)
                    job.status = JobStatus.COMPLETED
                    continue

                # Get scene from screenplay
                scene = get_scene_from_screenplay(state.screenplay_dict, scene_id)
                if not scene:
                    job.status = JobStatus.SKIPPED
                    logger.warning(f"  ⊙ Scene not found: {scene_id}")
                    continue

                # Convert scene to classifier format
                classifier_scene = convert_scene_to_classifier_input(
                    scene, state.screenplay_dict
                )

                # Build asset map
                asset_map = convert_pipeline_state_to_asset_map(state, scene_id)

                logger.info(f"🎬 Generating video for {scene_id}")
                logger.debug(f"   Available assets: {list(asset_map.keys())}")

                # Use orchestrator to generate video with intelligent workflow selection
                try:
                    video_path, classification = (
                        await orchestrator.generate_video_with_workflow(
                            classifier_scene, asset_map
                        )
                    )

                    # Move generated video to expected location
                    if video_path != str(output_path):
                        output_path.parent.mkdir(parents=True, exist_ok=True)
                        import shutil

                        shutil.move(video_path, str(output_path))
                        video_path = str(output_path)

                    job.output_path = video_path
                    job.status = JobStatus.COMPLETED
                    job.metadata["workflow_type"] = classification.workflow_type.value
                    job.metadata["workflow_reason"] = classification.reason

                    logger.info(
                        f"  ✓ Generated {scene_id} using {classification.workflow_type.value}"
                    )

                except Exception as e:
                    logger.error(
                        f"  ✗ Workflow orchestrator failed for {scene_id}: {e}"
                    )
                    # Fallback to legacy method if orchestrator fails
                    logger.info("  ⚠️  Attempting fallback to legacy generation...")
                    await self._generate_video_legacy(scene, output_path, state)
                    job.output_path = str(output_path)
                    job.status = JobStatus.COMPLETED
                    job.metadata["workflow_type"] = "legacy_fallback"
                    logger.info(f"  ✓ Generated {scene_id} using legacy fallback")

            except Exception as e:
                job.status = JobStatus.FAILED
                job.error = str(e)
                logger.error(f"  ✗ Failed {job.id}: {e}")

        # Export workflow metrics
        if config.export_metrics:
            try:
                orchestrator.export_metrics(config.metrics_output_path)
                logger.info(
                    f"📊 Workflow metrics exported to {config.metrics_output_path}"
                )
            except Exception as e:
                logger.warning(f"Failed to export metrics: {e}")

        # Only mark stage complete if no jobs failed
        failed_count = len([j for j in video_jobs if j.status == JobStatus.FAILED])
        if failed_count == 0:
            state.mark_stage_complete(JobType.VIDEO)
            logger.info("✅ Video generation complete (intelligent workflow selection)")
        else:
            logger.warning(
                f"Video stage has {failed_count} failed jobs - will retry on next run"
            )

        return state

    async def _generate_video_legacy(
        self, scene: Dict[str, Any], output_path: Path, state: PipelineState
    ) -> None:
        """
        Legacy video generation fallback.

        Uses simple heuristics to determine generation method.
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)

        scene_id = scene.get("scene_id", "")
        assert len(scene_id) > 0, "SceneID not found"

        gemini = GeminiMediaGen()

        # Get keyframe descriptions
        keyframe_desc = scene.get("keyframe_description", {})
        has_first = bool(keyframe_desc.get("first_frame_prompt"))
        has_last = bool(keyframe_desc.get("last_frame_prompt"))

        # Build prompt
        prompt = scene.get("video_prompt", scene.get("action_prompt", ""))
        duration = scene.get("duration", 4.0)

        # Determine method
        if has_first and has_last:
            # Interpolation
            first_frame_path = state.get_scene_image_path(
                scene_id,
                "first_frame",
            )
            last_frame_path = state.get_scene_image_path(
                scene_id,
                "last_frame",
            )

            if first_frame_path.exists() and last_frame_path.exists():
                response = await gemini.generate_video(
                    prompt=prompt,
                    image=str(first_frame_path),
                    last_image=str(last_frame_path),
                    duration=duration,
                )
            else:
                raise FileNotFoundError(
                    "Keyframes not found for interpolation",
                )

        elif has_first:
            # Image-to-video
            first_frame_path = state.get_scene_image_path(
                scene_id,
                "first_frame",
            )

            if first_frame_path.exists():
                response = await gemini.generate_video(
                    prompt=prompt,
                    image=str(first_frame_path),
                    duration=duration,
                )
            else:
                raise FileNotFoundError(
                    "First frame not found for image-to-video",
                )

        else:
            # Text-to-video
            response = await gemini.generate_video(
                prompt=prompt,
                duration=duration,
            )

        # Save video
        await gemini.render_video(str(output_path), response)
        logger.info(f"✓ Video saved to: {output_path}")


class VideoProcessingPipeline(Runner[PipelineState, PipelineState]):
    """
    Stage 4: Post-production and video assembly.
    Applies effects, transitions, and stitches videos together.
    """

    async def run(self, inputs: PipelineState) -> PipelineState:
        state = inputs
        logger.info("=== Stage 5: Post-Production & Assembly ===")

        # Check if video stage is complete - post-production depends on it
        if not state.is_stage_complete(JobType.VIDEO):
            logger.warning("Video stage not complete - skipping post-production")
            return state

        if state.is_stage_complete(JobType.POST_PRODUCTION):
            logger.info("Post-production already complete, skipping...")
            return state

        # Get post-production jobs (including failed jobs for retry)
        post_jobs = state.get_jobs_by_type(JobType.POST_PRODUCTION)
        pending = [
            j for j in post_jobs if j.status in [JobStatus.PENDING, JobStatus.FAILED]
        ]

        # Also check for skipped jobs - they might be waiting for video dependencies
        skipped = [j for j in post_jobs if j.status == JobStatus.SKIPPED]

        if not pending and not skipped:
            logger.info("No pending post-production jobs")
            state.mark_stage_complete(JobType.POST_PRODUCTION)
            return state

        # If we have skipped jobs but no pending, check if videos are now available
        if not pending and skipped:
            logger.info(
                "Re-checking skipped post-production jobs for available inputs..."
            )
            # Reset skipped jobs to pending so they can be retried
            for job in skipped:
                job.status = JobStatus.PENDING
            pending = skipped

        logger.info(f"Processing {len(pending)} scenes for post-production...")

        if not state.screenplay_dict:
            raise ValueError("No screenplay data available")

        extracted = extract_all_stages(state.screenplay_dict)
        post_stage = extracted["post_production"]

        # Process each scene
        processed_videos = []

        for job in pending:
            try:
                job.status = JobStatus.IN_PROGRESS

                scene_id = job.scene_id
                if not scene_id:
                    job.status = JobStatus.SKIPPED
                    continue

                # Get post-production spec
                post_spec = post_stage.get_scene(scene_id)
                if not post_spec:
                    job.status = JobStatus.SKIPPED
                    continue

                # Get input video
                input_video = state.get_scene_video_path(scene_id)
                output_video = state.videos_dir / f"{scene_id}_processed.mp4"

                # Check if input video exists
                if not input_video.exists() or input_video.stat().st_size == 0:
                    # Check if the video job failed
                    video_job = state.get_job(f"video_{scene_id}")
                    if video_job and video_job.status == JobStatus.FAILED:
                        logger.warning(
                            f"  ⊙ Skipping {scene_id} - video generation failed: {video_job.error}"
                        )
                        job.status = JobStatus.SKIPPED
                        continue
                    else:
                        logger.warning(
                            f"  ⊙ Skipping {scene_id} - input video missing or empty"
                        )
                        job.status = JobStatus.SKIPPED
                        continue

                # Apply effects and trimming
                await self._process_scene(input_video, output_video, post_spec, state)

                processed_videos.append(
                    {
                        "path": output_video,
                        "scene_id": scene_id,
                        "transition": post_spec.transition_to_next,
                    }
                )

                job.output_path = str(output_video)
                job.status = JobStatus.COMPLETED

                logger.info(f"  ✓ Processed {scene_id}")

            except Exception as e:
                job.status = JobStatus.FAILED
                job.error = str(e)
                logger.error(f"  ✗ Failed {job.id}: {e}")

        # Stitch all videos together
        if processed_videos:
            await self._stitch_videos(processed_videos, state)

        # Only mark stage complete if no jobs failed or skipped due to missing inputs
        failed_count = len([j for j in post_jobs if j.status == JobStatus.FAILED])
        skipped_count = len([j for j in post_jobs if j.status == JobStatus.SKIPPED])

        if failed_count == 0 and skipped_count == 0:
            state.mark_stage_complete(JobType.POST_PRODUCTION)
        else:
            if failed_count > 0:
                logger.warning(
                    f"Post-production stage has {failed_count} failed jobs - will retry on next run"
                )
            if skipped_count > 0:
                logger.warning(
                    f"Post-production stage has {skipped_count} skipped jobs (missing inputs) - waiting for previous stages"
                )

        return state

    async def _process_scene(
        self, input_path, output_path, spec, state: PipelineState
    ) -> None:
        """Apply effects and trimming to a scene"""
        # TODO: Implement ffmpeg processing
        # - Trim video if needed
        # - Apply text overlays
        # - Apply color grading
        # - Mix audio
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.touch()

    async def _stitch_videos(self, videos: list, state: PipelineState) -> None:
        """Stitch all processed videos into final output"""
        # TODO: Implement ffmpeg stitching with transitions
        final_path = state.get_final_video_path()
        final_path.parent.mkdir(parents=True, exist_ok=True)
        final_path.touch()

        logger.info(f"✓ Final video created: {final_path}")


class MovieMaker:
    """
    Main orchestrator for movie generation pipeline.
    Handles resumability, job tracking, and stage coordination.
    """

    def __init__(
        self,
        writer: ScriptWriter,
        enhancer: Enhancer,
        db_path: str = "./cinema_jobs.db",
        workflow_config: Optional[Dict[str, Any]] = None,
    ):
        self.writer = writer
        self.enhancer = enhancer
        self.workflow_config = workflow_config or {}

        # Import here to avoid circular dependency
        from cinema.pipeline.job_tracker import JobTracker

        self.tracker = JobTracker(db_path)

        # Build pipeline with workflow config
        self.pipeline = self._create_pipeline(self.workflow_config)

    def _create_pipeline(self, workflow_config: Optional[Dict[str, Any]] = None):
        """
        Create the full movie generation pipeline.

        Args:
            workflow_config: Optional workflow configuration for VideoGenerator
        """
        from cinema.pipeline.pipeline import Pipeline

        return (
            Pipeline()
            .then(VisualCharacterBuilder())
            .then(AudioGenerator())
            .then(KeyframeGenerator())
            .then(VideoGenerator(workflow_config=workflow_config))
            .then(VideoProcessingPipeline())
        )

    async def generate(
        self,
        script_input: ScriptWriterSchema,
        movie_id: Optional[str] = None,
        base_dir: str = "./output",
        screenplay_json: Optional[dict] = None,
    ) -> PipelineState:
        """
        Generate a movie from script or pre-generated screenplay JSON.
        Can resume from any point if movie_id exists.

        Args:
            script_input: ScriptWriterSchema with script, characters, images (required if screenplay_json not provided)
            movie_id: Unique movie ID (auto-generated if not provided)
            base_dir: Output directory
            screenplay_json: Pre-generated screenplay JSON (skips screenplay generation if provided)
        """
        # Validate inputs
        if not screenplay_json and not script_input:
            raise ValueError("Either script_input or screenplay_json must be provided")

        # Generate or use existing movie ID
        if not movie_id:
            movie_id = str(uuid.uuid4())[:8]

        logger.info(f"{'='*60}")
        logger.info(f"Movie ID: {movie_id}")
        logger.info(f"{'='*60}")

        # Try to load existing state
        state = self.tracker.load_state(movie_id, base_dir)

        if state:
            logger.info("Resuming from existing state...")
            progress = self.tracker.get_progress(movie_id)
            logger.info(
                f"Progress: {progress['completed']}/{progress['total']} jobs complete"
            )
        else:
            logger.info("Starting new movie generation...")
            state = PipelineState.create(movie_id, base_dir)

        # Ensure directories exist
        state.ensure_directories()

        # Generate screenplay if needed
        if not state.is_stage_complete(JobType.SCREENPLAY):
            logger.info("=== Stage 0: Screenplay Generation ===")

            # Validate writer and enhancer are provided
            if not self.writer or not self.enhancer:
                raise ValueError(
                    "writer and enhancer are required for screenplay generation"
                )

            # Create job
            job = Job(
                id=f"screenplay_{state.movie_id}",
                type=JobType.SCREENPLAY,
                status=JobStatus.IN_PROGRESS,
            )
            state.add_job(job)

            try:
                screenplay_builder = ScreenplayBuilder(self.writer, self.enhancer)
                structured_script = await screenplay_builder.run(script_input)

                # Store in state
                state.screenplay = structured_script
                state.screenplay_dict = structured_script.model_dump()

                # Extract all stages and create jobs
                logger.info("Extracting generation stages and creating jobs...")
                extracted = extract_all_stages(state.screenplay_dict)
                self._create_character_jobs(state, extracted)
                self._create_image_jobs(state, extracted)
                self._create_video_jobs(state, extracted)
                self._create_post_production_jobs(state, extracted)

                # Mark complete
                job.status = JobStatus.COMPLETED
                state.mark_stage_complete(JobType.SCREENPLAY)

                num_scenes = len(state.screenplay_dict.get("scenes", []))
                logger.info(f"✓ Screenplay generated: {num_scenes} scenes")
                logger.info(f"✓ Created {len(state.jobs)} jobs")

            except Exception as e:
                job.status = JobStatus.FAILED
                job.error = str(e)
                logger.error(f"Screenplay generation failed: {e}")
                raise

            # Save state after screenplay
            logger.info("Saving state to database...")
            self.tracker.save_state(state)

        # Run the rest of the pipeline
        state = await self.pipeline.execute(state)

        # Save final state
        self.tracker.save_state(state)

        logger.info(f"{'='*60}")
        logger.info("✓ Movie generation complete!")
        progress = self.tracker.get_progress(movie_id)
        logger.info(
            f"Final: {progress['completed']}/{progress['total']} jobs completed"
        )
        logger.info(f"{'='*60}")

        return state

    def _create_character_jobs(
        self,
        state: PipelineState,
        extracted: dict,
    ) -> None:
        """Create jobs for character generation"""
        characters = extracted["characters"].characters

        for char in characters:
            for view in ["front", "side", "full_body", "back"]:
                job = Job(
                    id=f"char_{char.id}_{view}",
                    type=JobType.CHARACTER,
                    character_id=char.id,
                    metadata={"view": view, "name": char.name},
                )
                state.add_job(job)

    def _create_image_jobs(
        self,
        state: PipelineState,
        extracted: dict,
    ) -> None:
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

    def _create_video_jobs(
        self,
        state: PipelineState,
        extracted: dict,
    ) -> None:
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

    def _create_post_production_jobs(
        self, state: PipelineState, extracted: dict
    ) -> None:
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

    async def generate_from_screenplay(
        self,
        screenplay_json: dict,
        movie_id: Optional[str] = None,
        base_dir: str = "./output",
    ) -> PipelineState:
        """
        Generate a movie from pre-generated screenplay JSON.
        Skips screenplay generation stage.

        Args:
            screenplay_json: Pre-generated screenplay JSON
            movie_id: Unique movie ID (auto-generated if not provided)
            base_dir: Output directory
        """
        # Validate screenplay JSON
        required_fields = ["scenes", "video_config", "character_description"]
        missing = [f for f in required_fields if f not in screenplay_json]
        if missing:
            raise ValueError(f"Screenplay JSON missing required fields: {missing}")

        # Generate or use existing movie ID
        if not movie_id:
            movie_id = str(uuid.uuid4())[:8]

        logger.info(f"{'='*60}")
        logger.info(f"Movie ID: {movie_id}")
        logger.info(f"{'='*60}")

        # Try to load existing state
        state = self.tracker.load_state(movie_id, base_dir)

        if state:
            logger.info("Resuming from existing state...")
            progress = self.tracker.get_progress(movie_id)
            percent = progress["completed"] / progress["total"]

            logger.info(f"Progress: {percent} jobs complete")
        else:
            logger.info("Starting new movie generation from screenplay JSON...")
            state = PipelineState.create(movie_id, base_dir)

        # Ensure directories exist
        state.ensure_directories()

        # Load screenplay if needed
        if not state.is_stage_complete(JobType.SCREENPLAY):
            logger.info("=== Stage 0: Loading Pre-Generated Screenplay ===")

            # Create job and mark as complete
            job = Job(
                id=f"screenplay_{state.movie_id}",
                type=JobType.SCREENPLAY,
                status=JobStatus.COMPLETED,
            )
            state.add_job(job)

            # Store screenplay
            state.screenplay_dict = screenplay_json

            # Extract all stages and create jobs
            logger.info("Extracting generation stages and creating jobs...")
            extracted = extract_all_stages(screenplay_json)
            self._create_character_jobs(state, extracted)
            self._create_image_jobs(state, extracted)
            self._create_video_jobs(state, extracted)
            self._create_post_production_jobs(state, extracted)

            state.mark_stage_complete(JobType.SCREENPLAY)

            num_scenes = len(screenplay_json.get("scenes", []))
            logger.info(f"✓ Screenplay loaded: {num_scenes} scenes")
            logger.info(f"✓ Created {len(state.jobs)} jobs")

            # Save state
            logger.info("Saving state to database...")
            self.tracker.save_state(state)

        # Run the rest of the pipeline
        state = await self.pipeline.execute(state)

        # Save final state
        self.tracker.save_state(state)

        logger.info(f"{'='*60}")
        logger.info("✓ Movie generation complete!")
        progress = self.tracker.get_progress(movie_id)
        percent = progress["completed"] / progress["total"]

        logger.info(f"Final: {percent} jobs completed")
        logger.info(f"{'='*60}")

        return state

    async def resume(self, movie_id: str, base_dir: str = "./output") -> PipelineState:
        """Resume generation for an existing movie"""
        state = self.tracker.load_state(movie_id, base_dir)

        if not state:
            raise ValueError(f"No state found for movie_id: {movie_id}")

        logger.info(f"{'='*60}")
        logger.info(f"Resuming movie: {movie_id}")
        progress = self.tracker.get_progress(movie_id)
        logger.info(
            f"Current progress: {progress['completed']}/{progress['total']} jobs"
        )
        logger.info(f"{'='*60}")

        # Continue from where we left off
        state = await self.pipeline.execute(state)

        # Save state
        self.tracker.save_state(state)

        return state

    def get_status(self, movie_id: str) -> dict:
        """Get current status of a movie generation"""
        return self.tracker.get_progress(movie_id)
