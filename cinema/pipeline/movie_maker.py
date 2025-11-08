"""
Movie generation pipeline implementation.
"""

import logging
import uuid
from typing import Optional

from cinema.agents.scriptwriter.crew import (
    Enhancer,
    EnhancerInputSchema,
    ScriptWriter,
    ScriptWriterSchema,
)
from cinema.models import CinematgrapherCrewOutput
from cinema.pipeline.pipeline import Runner
from cinema.pipeline.state import Job, JobStatus, JobType, PipelineState
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
        enhancer_inputs = EnhancerInputSchema(
            script=inputs.script,
            screenplay=screenplay,
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
            for view in ["front", "side", "full_body"]:
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
    Stage 1: Generate character reference images.
    Generates side profiles of characters and saves to disk.
    """

    async def run(self, inputs: PipelineState) -> PipelineState:
        state = inputs
        logger.info("=== Stage 1: Character Reference Generation ===")

        if state.is_stage_complete(JobType.CHARACTER):
            logger.info("Characters already generated, skipping...")
            return state

        # Get character jobs
        char_jobs = state.get_jobs_by_type(JobType.CHARACTER)
        pending = [j for j in char_jobs if j.status == JobStatus.PENDING]

        if not pending:
            logger.info("No pending character jobs")
            state.mark_stage_complete(JobType.CHARACTER)
            return state

        logger.info(f"Generating {len(pending)} character images...")

        if not state.screenplay_dict:
            raise ValueError("No screenplay data available")

        extracted = extract_all_stages(state.screenplay_dict)
        char_stage = extracted["characters"]

        for job in pending:
            try:
                job.status = JobStatus.IN_PROGRESS

                char_id = job.character_id
                if not char_id:
                    job.status = JobStatus.SKIPPED
                    continue

                view = job.metadata["view"]

                # Get character and prompt
                char = char_stage.get_character(char_id)
                if not char:
                    job.status = JobStatus.SKIPPED
                    continue

                prompts = char_stage.get_reference_prompts(char_id)
                prompt = prompts.get(view, "")

                # Log prompt in debug mode
                logger.debug(f"Character prompt for {char.name} ({view}):\n{prompt}")

                # Check if output already exists (caching)
                output_path = state.get_character_image_path(char_id, view)
                
                if output_path.exists() and output_path.stat().st_size > 0:
                    logger.info(f"  ⊙ Cached {char.name} - {view} (file exists)")
                    job.output_path = str(output_path)
                    job.status = JobStatus.COMPLETED
                    continue

                # Generate image (mock for now)
                await self._generate_image(prompt, output_path)

                job.output_path = str(output_path)
                job.status = JobStatus.COMPLETED

                logger.info(f"  ✓ Generated {char.name} - {view}")

            except Exception as e:
                job.status = JobStatus.FAILED
                job.error = str(e)
                logger.error(f"  ✗ Failed {job.id}: {e}")

        state.mark_stage_complete(JobType.CHARACTER)
        return state

    async def _generate_image(self, prompt: str, output_path) -> None:
        """Generate image using Imagen (mock implementation)"""
        # TODO: Implement actual image generation
        # For now, just create a placeholder
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.touch()


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

        # Get image jobs
        image_jobs = state.get_jobs_by_type(JobType.IMAGE)
        pending = [j for j in image_jobs if j.status == JobStatus.PENDING]

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

        state.mark_stage_complete(JobType.IMAGE)
        return state

    async def _generate_image(
        self,
        prompt: str,
        output_path,
        aspect_ratio: str,
        character_refs: list,
        state: PipelineState,
    ) -> None:
        """Generate image using Imagen with optional character references"""
        # TODO: Implement actual image generation with character refs
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.touch()


class VideoGenerator(Runner[PipelineState, PipelineState]):
    """
    Stage 3: Generate videos from keyframes.
    Uses different generation strategies based on scene requirements.
    """

    async def run(self, inputs: PipelineState) -> PipelineState:
        state = inputs
        logger.info("=== Stage 4: Video Generation ===")

        if state.is_stage_complete(JobType.VIDEO):
            logger.info("Videos already generated, skipping...")
            return state

        # Get video jobs
        video_jobs = state.get_jobs_by_type(JobType.VIDEO)
        pending = [j for j in video_jobs if j.status == JobStatus.PENDING]

        if not pending:
            logger.info("No pending video jobs")
            state.mark_stage_complete(JobType.VIDEO)
            return state

        logger.info(f"Generating {len(pending)} videos...")

        if not state.screenplay_dict:
            raise ValueError("No screenplay data available")

        extracted = extract_all_stages(state.screenplay_dict)
        video_stage = extracted["videos"]

        for job in pending:
            try:
                job.status = JobStatus.IN_PROGRESS

                scene_id = job.scene_id
                if not scene_id:
                    job.status = JobStatus.SKIPPED
                    continue

                # Get video spec
                video_spec = video_stage.get_video(scene_id)
                if not video_spec:
                    job.status = JobStatus.SKIPPED
                    continue

                # Log prompt in debug mode
                logger.debug(
                    f"Video prompt for {scene_id} ({video_spec.method}):\n"
                    f"Prompt: {video_spec.prompt}\n"
                    f"Negative: {video_spec.negative_prompt}\n"
                    f"Duration: {video_spec.duration}s"
                )

                # Check if output already exists (caching)
                output_path = state.get_scene_video_path(scene_id)
                
                if output_path.exists() and output_path.stat().st_size > 0:
                    logger.info(f"  ⊙ Cached {scene_id} ({video_spec.method}) (file exists)")
                    job.output_path = str(output_path)
                    job.status = JobStatus.COMPLETED
                    continue

                # Generate video based on method
                if video_spec.is_text_to_video():
                    await self._generate_text_to_video(video_spec, output_path)
                elif video_spec.needs_last_frame():
                    await self._generate_interpolation_video(
                        video_spec, output_path, state
                    )
                else:
                    await self._generate_image_to_video(video_spec, output_path, state)

                job.output_path = str(output_path)
                job.status = JobStatus.COMPLETED

                logger.info(f"  ✓ Generated {scene_id} ({video_spec.method})")

            except Exception as e:
                job.status = JobStatus.FAILED
                job.error = str(e)
                logger.error(f"  ✗ Failed {job.id}: {e}")

        state.mark_stage_complete(JobType.VIDEO)
        return state

    async def _generate_text_to_video(self, spec, output_path) -> None:
        """Generate video from text prompt only"""
        # TODO: Implement Veo text-to-video
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.touch()

    async def _generate_image_to_video(
        self, spec, output_path, state: PipelineState
    ) -> None:
        """Generate video from first frame image"""
        # TODO: Implement Veo image-to-video
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.touch()

    async def _generate_interpolation_video(
        self, spec, output_path, state: PipelineState
    ) -> None:
        """Generate video interpolating between first and last frame"""
        # TODO: Implement Veo first+last frame interpolation
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.touch()


class VideoProcessingPipeline(Runner[PipelineState, PipelineState]):
    """
    Stage 4: Post-production and video assembly.
    Applies effects, transitions, and stitches videos together.
    """

    async def run(self, inputs: PipelineState) -> PipelineState:
        state = inputs
        logger.info("=== Stage 5: Post-Production & Assembly ===")

        if state.is_stage_complete(JobType.POST_PRODUCTION):
            logger.info("Post-production already complete, skipping...")
            return state

        # Get post-production jobs
        post_jobs = state.get_jobs_by_type(JobType.POST_PRODUCTION)
        pending = [j for j in post_jobs if j.status == JobStatus.PENDING]

        if not pending:
            logger.info("No pending post-production jobs")
            state.mark_stage_complete(JobType.POST_PRODUCTION)
            return state

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

        state.mark_stage_complete(JobType.POST_PRODUCTION)
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
        writer: ScriptWriter = None,
        enhancer: Enhancer = None,
        db_path: str = "./cinema_jobs.db",
    ):
        self.writer = writer
        self.enhancer = enhancer

        # Import here to avoid circular dependency
        from cinema.pipeline.job_tracker import JobTracker

        self.tracker = JobTracker(db_path)

        # Build pipeline
        self.pipeline = self._create_pipeline()

    def _create_pipeline(self):
        """Create the full movie generation pipeline"""
        from cinema.pipeline.pipeline import Pipeline

        return (
            Pipeline()
            .then(VisualCharacterBuilder())
            .then(AudioGenerator())
            .then(KeyframeGenerator())
            .then(VideoGenerator())
            .then(VideoProcessingPipeline())
        )

    async def generate(
        self,
        script_input: ScriptWriterSchema = None,
        movie_id: Optional[str] = None,
        base_dir: str = "./output",
        screenplay_json: dict = None,
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
                raise ValueError("writer and enhancer are required for screenplay generation")

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

    def _create_character_jobs(self, state: PipelineState, extracted: dict) -> None:
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

    def _create_image_jobs(self, state: PipelineState, extracted: dict) -> None:
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

    def _create_video_jobs(self, state: PipelineState, extracted: dict) -> None:
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
            logger.info(
                f"Progress: {progress['completed']}/{progress['total']} jobs complete"
            )
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
        logger.info(
            f"Final: {progress['completed']}/{progress['total']} jobs completed"
        )
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
