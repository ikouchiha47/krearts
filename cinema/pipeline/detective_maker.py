"""
Detective Comic Strip generation pipeline implementation.
Follows the same pattern as MovieMaker with JobTracker and GeminiMediaGen integration.

REFACTORED: Now uses modular architecture with SOLID principles.
"""

import asyncio
import json
import logging
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from PIL import Image

from cinema.agents.bookwriter.crew import (
    ComicStripStoryBoarding,
    DetectivePlotBuilder,
    PlotCritique,
    ScreenplayWriter,
)
from cinema.agents.bookwriter.detective import (
    ConsistencyValidator,
    ConstraintTableBuilder,
    TruthTable,
)
from cinema.agents.bookwriter.flow import StoryBuilder, StoryBuilderOutput
from cinema.agents.bookwriter.models import Character, PlotConstraints
from cinema.models.detective_output import DetectiveStoryOutput
from cinema.pipeline.pipeline import Runner

# NEW: Import modular generators and composers
from cinema.pipeline.shared import (
    BaseGenerator,
    CharacterReferenceGenerator,
    PanelComposer,
    SimpleImageGenerator,
)
from cinema.pipeline.state import Job, JobStatus, JobType, PipelineState
from cinema.providers.gemini import GeminiMediaGen

logger = logging.getLogger(__name__)


class PlotStructureBuilder(Runner[Dict[str, Any], Dict[str, Any]]):
    """
    Stage 0: Generate plot structure from constraints.
    Uses graph-based detective system to create logical plot structure.
    """

    def __init__(self):
        # Initialize without crews - just for graph generation
        self.builder = ConstraintTableBuilder()
        self.validator = ConsistencyValidator()
        self.truth_table = TruthTable()

    async def run(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("=== Stage 0: Plot Structure Generation ===")

        constraints = inputs["constraints"]
        characters = inputs["characters"]

        # Step 1: Build graph from constraints
        graph = self.builder.build_from_constraints(constraints, characters)

        # Step 2: Validate consistency
        is_valid, violations = self.validator.validate(graph)

        if not is_valid:
            logger.error("Plot has logical violations!")
            for v in violations:
                logger.error(f"  {v}")
            raise ValueError("Plot is logically inconsistent")

        # Step 3: Build truth table
        self.truth_table.build_from_graph(graph, constraints)
        truth_table = self.truth_table.export()

        # Export plot structure
        plot_structure = {
            "graph": graph.export_to_dict(),
            "truth_table": truth_table,
            "timeline": [
                {
                    "source": rel.source,
                    "target": rel.target,
                    "action": rel.action.value,
                    "time": rel.time,
                    "location": rel.location,
                    "motive": rel.motive,
                    "witnessed_by": rel.witnessed_by,
                }
                for rel in graph.get_action_timeline()
            ],
            "constraints": constraints.to_crew(),  # Convert to CrewAI-compatible format
        }

        logger.info(
            f"✓ Plot structure generated: {len(graph.action_sequences)} actions"
        )

        return {
            **inputs,
            "plot_structure": plot_structure,
            "graph": graph,
        }


class NarrativeBuilderWithStoryBuilder(Runner[Dict[str, Any], DetectiveStoryOutput]):
    """
    Stage 1: Generate narrative using full StoryBuilder flow.

    This uses StoryBuilder which does BOTH storyline generation AND storyboarding
    in a single flow. The flow includes:
    - Plot generation with critique loop
    - Screenplay writing
    - Storyboarding
    """

    def __init__(
        self,
        storybuilder_flow: StoryBuilder,
        art_style: str = "Noir Comic Book Style",
    ):
        self.storybuilder_flow = storybuilder_flow
        self.art_style = art_style

    def _save_flow_state_output(
        self, output: StoryBuilderOutput, plot_structure: Dict[str, Any]
    ) -> None:
        """Save flow state output to JSON file for debugging and analysis."""

        # Create output directory
        output_dir = Path("./output/flow_states")
        output_dir.mkdir(parents=True, exist_ok=True)

        # Generate filename with timestamp
        from datetime import datetime

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = output_dir / f"storybuilder_output_{timestamp}.json"

        # Prepare data for JSON serialization
        output_data = {
            "timestamp": timestamp,
            "flow_type": "StoryBuilder",
            "art_style": self.art_style,
            "output": output.model_dump(),
            "plot_structure": plot_structure,
        }

        # Save to file
        with open(output_file, "w") as f:
            json.dump(output_data, f, indent=2, default=str)

        logger.info(f"✓ Flow state saved to: {output_file}")

    async def run(self, inputs: Dict[str, Any]) -> DetectiveStoryOutput:
        logger.info("=== Stage 1: Narrative Generation (with StoryBuilder Flow) ===")

        plot_structure = inputs["plot_structure"]

        # Build input for story builder flow
        from cinema.agents.bookwriter.crew import DetectivePlotBuilderSchema
        from cinema.agents.bookwriter.flow import (
            ScreenplayWriterSchema,
            StoryBuilderInput,
            StripperInputSchema,
        )

        # Build plot schema
        plot_builder_schema = DetectivePlotBuilderSchema(
            characters=plot_structure["graph"]["characters"],
            relationships=plot_structure["timeline"],
            killer=plot_structure["constraints"]["killer"],
            victim=plot_structure["constraints"]["victim"],
            accomplices=plot_structure["constraints"]["accomplices"],
            witnesses=plot_structure["constraints"]["witnesses"],
            betrayals=plot_structure["constraints"]["betrayals"],
            examples="",
        )

        # Build stripper schema for storyboarding
        stripper_schema = StripperInputSchema(
            art_style=self.art_style,
            examples=ComicStripStoryBoarding.load_examples(),
        )
        screenplay_schema = ScreenplayWriterSchema.model_construct(
            examples=ScreenplayWriter.load_examples(),
        )
        story_input = StoryBuilderInput(
            plotbuilder=plot_builder_schema,
            stripper=stripper_schema,
            screenplay=screenplay_schema,
        )

        # Set input in flow state
        self.storybuilder_flow.state.input = story_input

        # Run the full flow - this will do plan -> critique -> screenplay -> storyboard
        logger.info("Running StoryBuilder flow...")
        await self.storybuilder_flow.kickoff_async()

        # Get output from flow state (kickoff_async may not return the final output directly)
        result = self.storybuilder_flow.state.output

        if not isinstance(result, StoryBuilderOutput):
            logger.error(
                f"Flow state.output is not StoryBuilderOutput, got {type(result)}"
            )
            raise ValueError("Flow did not generate StoryBuilderOutput")

        # Save flow state output to JSON for debugging/analysis
        self._save_flow_state_output(result, plot_structure)

        if not result.storystructure:
            logger.error("Flow did not generate storystructure")
            raise ValueError("Flow did not generate storystructure")

        detective_output = result.storystructure

        # Accept both DetectiveStoryOutput and ComicBookOutput (new format)
        try:
            from cinema.models.comic_output import ComicBookOutput
        except Exception:
            ComicBookOutput = None  # type: ignore

        if isinstance(detective_output, DetectiveStoryOutput):
            logger.info("✓ Narrative generation complete (via StoryBuilder)")
            logger.info(f"  Characters: {len(detective_output.characters)}")
            logger.info(f"  Narrative structure: {detective_output.narrative_structure}")
            logger.info(f"  Retry count: {result.retry_count}")
            return detective_output

        if ComicBookOutput is not None and isinstance(detective_output, ComicBookOutput):
            # Log summary for ComicBookOutput
            logger.info("✓ Narrative generation complete (ComicBookOutput via StoryBuilder)")
            logger.info(f"  Chapters: {len(detective_output.chapters)}")
            logger.info(f"  Total pages: {detective_output.total_pages}")
            logger.info(f"  Total panels: {detective_output.total_panels}")
            # Return as-is; caller will branch accordingly
            return detective_output  # type: ignore[return-value]

        logger.error("Failed to generate supported storystructure type")
        raise ValueError("Failed to generate supported storystructure type")
        


class StorylineValidator(Runner[DetectiveStoryOutput, DetectiveStoryOutput]):
    """
    Stage 2: Validate storyline before proceeding to image generation.
    This is a checkpoint where you can review the narrative before generating images.

    Set VALIDATE_ONLY=True to stop here and review the output.
    Set VALIDATE_ONLY=False to proceed with image generation.
    """

    def __init__(self, validate_only: bool = False):
        self.validate_only = validate_only

    async def run(self, inputs: DetectiveStoryOutput) -> DetectiveStoryOutput:
        logger.info("=== Stage 2: Storyline Validation ===")

        # Count panels
        total_panels = sum(
            len([a for a in char.actions_and_locations if a.panel is not None])
            for char in inputs.characters
        )

        logger.info(f"Storyline: {inputs.storyline[:200]}...")
        logger.info(f"Characters: {len(inputs.characters)}")
        logger.info(f"Total panels: {total_panels}")
        logger.info(f"Narrative structure: {inputs.narrative_structure}")

        if self.validate_only:
            logger.warning("=" * 80)
            logger.warning("VALIDATION ONLY MODE - Stopping before image generation")
            logger.warning(
                "Review the storyline and set validate_only=False to proceed"
            )
            logger.warning("=" * 80)
            # Don't raise exception, just return - pipeline will stop naturally
            return inputs

        logger.info("✓ Validation passed, proceeding to image generation")
        return inputs


class PanelImageGenerator(Runner[PipelineState, PipelineState]):
    """
    Stage 3: Generate comic panel images.
    Generates images for panel jobs using GeminiMediaGen with rate limiting.
    """

    def __init__(self, max_concurrent: int = 3):
        """
        Initialize panel image generator.

        Args:
            max_concurrent: Maximum number of concurrent image generation requests
        """
        self.max_concurrent = max_concurrent

    async def run(self, inputs: PipelineState) -> PipelineState:
        state = inputs
        logger.info("=== Stage 3: Panel Image Generation ===")

        if state.is_stage_complete(JobType.IMAGE):
            logger.info("Panel images already generated, skipping...")
            return state

        # Get image generation jobs
        image_jobs = state.get_jobs_by_type(JobType.IMAGE)
        pending = [
            j for j in image_jobs if j.status in [JobStatus.PENDING, JobStatus.FAILED]
        ]

        if not pending:
            logger.info("No pending panel generation jobs")
            state.mark_stage_complete(JobType.IMAGE)
            return state

        logger.info(f"Generating {len(pending)} comic panels...")
        logger.info(f"Max concurrent requests: {self.max_concurrent}")

        # Import rate limiter
        from cinema.utils.rate_limiter import RateLimiterManager

        rate_limiter = RateLimiterManager()

        gemini = GeminiMediaGen(rate_limiter=rate_limiter)

        # Use semaphore to limit concurrent requests
        import asyncio

        semaphore = asyncio.Semaphore(self.max_concurrent)

        async def generate_panel(job: Job) -> None:
            """Generate a single panel with rate limiting."""
            async with semaphore:
                try:
                    job.status = JobStatus.IN_PROGRESS

                    # Get prompt from job metadata
                    prompt = job.metadata["prompt"]
                    character_name = job.metadata["character_name"]
                    action_index = job.metadata["action_index"]
                    beat_index = job.metadata.get("beat_index")

                    # Build output path
                    # Prefer explicit filename from metadata (scene/chapter based),
                    # otherwise fall back to character-based naming for backward compatibility
                    suffix = f"_{action_index:02d}" + (
                        f"_b{int(beat_index):02d}" if beat_index is not None else ""
                    )
                    default_filename = f"{character_name.replace(' ', '_')}{suffix}.png"
                    output_filename = job.metadata.get("output_filename", default_filename)
                    output_path = state.images_dir / output_filename

                    # Check if cached
                    if output_path.exists() and output_path.stat().st_size > 0:
                        logger.info(f"  ⊙ Cached {output_filename}")
                        job.output_path = str(output_path)
                        job.status = JobStatus.COMPLETED
                        return

                    # Generate image with rate limiting
                    logger.info(f"  📸 Generating {output_filename}")
                    logger.debug(f"     Prompt: {prompt[:100]}...")

                    response = await gemini.generate_content(prompt=prompt)

                    # Save image
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    gemini.render_image(str(output_path), response)

                    job.output_path = str(output_path)
                    job.status = JobStatus.COMPLETED

                    logger.info(f"  ✓ Generated {output_filename}")

                except Exception as e:
                    job.status = JobStatus.FAILED
                    job.error = str(e)
                    logger.error(f"  ✗ Failed {job.id}: {e}")

        # Generate all panels concurrently (with semaphore limiting)
        await asyncio.gather(*[generate_panel(job) for job in pending])

        # Mark stage complete if no failures
        failed_count = len([j for j in image_jobs if j.status == JobStatus.FAILED])
        if failed_count == 0:
            state.mark_stage_complete(JobType.IMAGE)
            logger.info("✅ Panel image generation complete")
        else:
            logger.warning(
                f"Panel generation has {failed_count} failed jobs - will retry on next run"
            )

        return state


# ============================================================================
# JOB EXECUTOR (SOLID Principles)
# ============================================================================


class JobExecutor:
    """
    Executes jobs using generators.

    SOLID Principles:
    - SRP: Only executes jobs
    - OCP: Works with any BaseGenerator
    - LSP: All BaseGenerator subclasses work
    - DIP: Depends on BaseGenerator abstraction
    """

    def __init__(self, max_concurrent: int = 3):
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)

    async def execute_jobs(
        self,
        jobs: List[Job],
        generator: BaseGenerator,
        output_dir: Path,
        file_extension: str = ".png",
    ) -> None:
        """Execute multiple jobs concurrently"""

        async def execute_single(job: Job):
            async with self.semaphore:
                try:
                    job.status = JobStatus.IN_PROGRESS

                    # Build output path
                    filename = (
                        job.metadata.get("output_filename")
                        or f"{job.id}{file_extension}"
                    )
                    output_path = output_dir / filename

                    # Check cache
                    if output_path.exists() and output_path.stat().st_size > 0:
                        logger.info(f"  ⊙ Cached {filename}")
                        job.output_path = str(output_path)
                        job.status = JobStatus.COMPLETED
                        return

                    # Generate content
                    logger.info(f"  🎨 Generating {filename}")

                    # Load character images from paths if present (avoid storing PIL Images in metadata)
                    gen_kwargs = dict(job.metadata)
                    if "character_image_paths" in gen_kwargs:
                        char_image_paths = gen_kwargs.pop("character_image_paths")
                        logger.debug(
                            f"Loading {len(char_image_paths)} character images from paths"
                        )
                        char_images = [
                            Image.open(path)
                            for path in char_image_paths
                            if Path(path).exists()
                        ]
                        gen_kwargs["character_images"] = char_images
                        logger.debug(
                            f"Loaded {len(char_images)} PIL Images for composition"
                        )

                    result = await generator.generate(**gen_kwargs)

                    # Save result
                    output_path.parent.mkdir(parents=True, exist_ok=True)

                    # Handle different result types
                    if hasattr(result, "parts") and result.parts:
                        # Gemini response - extract image data
                        # Need to extract image bytes from response
                        for part in result.candidates[0].content.parts:
                            if hasattr(part, "inline_data") and part.inline_data:
                                output_path.write_bytes(part.inline_data.data)
                                break
                    elif isinstance(result, bytes):
                        output_path.write_bytes(result)
                    else:
                        # Handle PIL Image or other types
                        result.save(output_path)

                    job.output_path = str(output_path)
                    job.status = JobStatus.COMPLETED
                    logger.info(f"  ✓ Generated {filename}")

                except Exception as e:
                    job.status = JobStatus.FAILED
                    job.error = str(e)
                    logger.error(f"  ✗ Failed {job.id}: {e}")

        await asyncio.gather(*[execute_single(job) for job in jobs])


# ============================================================================
# DETECTIVE MAKER (Main Pipeline Orchestrator)
# ============================================================================


class DetectiveMaker:
    """
    Main orchestrator for detective comic strip generation.

    REFACTORED: Now uses modular architecture with SOLID principles.
    - Character reference generation for consistency
    - Panel composition with multi-image support
    - Backward compatible with legacy code
    """

    def __init__(
        self,
        # NEW: Modular generators (SOLID - Dependency Inversion)
        character_generator: Optional[CharacterReferenceGenerator] = None,
        panel_composer: Optional[PanelComposer] = None,
        simple_image_generator: Optional[SimpleImageGenerator] = None,
        # Configuration
        db_path: str = "./cinema_jobs.db",
        art_style: str = "Noir Comic Book Style",
        validate_only: bool = False,
        max_concurrent_images: int = 3,
        # [DEPRECATED - REMOVABLE] Legacy parameters for backward compatibility
        # TODO: Remove after full migration to new architecture
        plotbuilder: Optional[Union[DetectivePlotBuilder, StoryBuilder]] = None,
        storyboard: Optional[ComicStripStoryBoarding] = None,
    ):
        # New modular architecture (SOLID)
        self.character_generator = character_generator
        self.panel_composer = panel_composer
        self.simple_image_generator = simple_image_generator
        self.executor = JobExecutor(max_concurrent_images)

        # [DEPRECATED - REMOVABLE] Legacy support
        self.plotbuilder = plotbuilder
        self.storyboard = storyboard

        # Configuration
        self.art_style = art_style
        self.validate_only = validate_only
        self.max_concurrent_images = max_concurrent_images

        from cinema.pipeline.job_tracker import JobTracker

        self.tracker = JobTracker(db_path)

    async def _generate_character_references(
        self, state: PipelineState, detective_output: DetectiveStoryOutput
    ):
        """Stage 3: Generate character reference images (NEW)"""
        logger.info("=== Stage 3: Character Reference Generation ===")

        if state.is_stage_complete(JobType.CHARACTER_REF):
            logger.info("Character references already generated, skipping...")
            return

        # Create character reference jobs
        char_jobs = []
        for character in detective_output.characters:
            job = Job(
                id=f"char_ref_{character.name.replace(' ', '_')}",
                type=JobType.CHARACTER_REF,
                status=JobStatus.PENDING,
                metadata={
                    "character": character.model_dump(),  # Convert Pydantic model to dict for JSON serialization
                    "output_filename": f"{character.name.replace(' ', '_')}_reference.png",
                },
            )
            state.add_job(job)
            char_jobs.append(job)

        logger.info(f"Generating {len(char_jobs)} character references...")

        # Execute jobs using modular architecture
        output_dir = state.characters_dir

        if not self.character_generator:
            raise ValueError("Character generator is required but not provided")

        await self.executor.execute_jobs(
            jobs=char_jobs,
            generator=self.character_generator,
            output_dir=output_dir,
        )

        # Mark stage complete
        state.mark_stage_complete(JobType.CHARACTER_REF)
        self.tracker.save_state(state)

        completed = len([j for j in char_jobs if j.status == JobStatus.COMPLETED])
        logger.info(f"✓ Generated {completed}/{len(char_jobs)} character references")

    async def _generate_panels_with_composition(
        self, state: PipelineState, detective_output: DetectiveStoryOutput
    ):
        """Stage 4: Generate panel images using character composition (NEW)"""
        logger.info("=== Stage 4: Panel Generation with Character Composition ===")

        if state.is_stage_complete(JobType.IMAGE):
            logger.info("Panel images already generated, skipping...")
            return

        # Get character reference paths
        char_ref_jobs = state.get_jobs_by_type(JobType.CHARACTER_REF)
        character_references = {}
        for job in char_ref_jobs:
            if job.status == JobStatus.COMPLETED and job.output_path:
                # Handle both dict and object
                char_data = job.metadata["character"]
                char_name = (
                    char_data["name"] if isinstance(char_data, dict) else char_data.name
                )
                character_references[char_name] = job.output_path

        logger.info(
            f"Available character references: {list(character_references.keys())}"
        )

        # Create panel jobs with character references
        panel_jobs = []
        panel_counter = 0
        for character in detective_output.characters:
            for idx, action in enumerate(character.actions_and_locations):
                # Identify characters in this scene (for now, just the acting character)
                # TODO: Extract from panel description or add to PanelPrompt model
                characters_in_scene = [character.name]

                # Get character reference paths for this scene
                scene_char_refs = {
                    name: character_references.get(name)
                    for name in characters_in_scene
                    if name in character_references
                }

                # Prefer beats if provided; otherwise fall back to single panel
                if getattr(action, "beats", None):
                    for bidx, beat in enumerate(action.beats):
                        scene_id = f"scene_{panel_counter:04d}"
                        panel_counter += 1
                        job = Job(
                            id=f"panel_{character.name.replace(' ', '_')}_{idx:02d}_b{bidx:02d}",
                            type=JobType.IMAGE,
                            status=JobStatus.PENDING,
                            metadata={
                                "panel": beat.model_dump(),
                                "character_images": [],  # Will be loaded from paths
                                "character_names": characters_in_scene,
                                "character_references": scene_char_refs,
                                "scene_id": scene_id,
                                "output_filename": f"{scene_id}.png",
                                "beat_index": bidx,
                                "action_index": idx,
                                "character_name": character.name,
                            },
                        )
                        state.add_job(job)
                        panel_jobs.append(job)
                else:
                    if action.panel is None:
                        continue
                    scene_id = f"scene_{panel_counter:04d}"
                    panel_counter += 1
                    job = Job(
                        id=f"panel_{character.name.replace(' ', '_')}_{idx:02d}",
                        type=JobType.IMAGE,
                        status=JobStatus.PENDING,
                        metadata={
                            "panel": action.panel.model_dump(),  # Convert Pydantic model to dict for JSON serialization
                            "character_images": [],  # Will be loaded from paths
                            "character_names": characters_in_scene,
                            "character_references": scene_char_refs,
                            "scene_id": scene_id,
                            "output_filename": f"{scene_id}.png",
                            "action_index": idx,
                            "character_name": character.name,
                        },
                    )
                    state.add_job(job)
                    panel_jobs.append(job)

        logger.info(f"Generating {len(panel_jobs)} comic panels...")

        # Store character image paths (not PIL Images) to avoid JSON serialization issues
        logger.debug("Preparing panel jobs with character image paths (not PIL Images)")
        for job in panel_jobs:
            char_image_paths = []
            char_names = []
            for name, ref_path in job.metadata["character_references"].items():
                if ref_path and Path(ref_path).exists():
                    char_image_paths.append(ref_path)
                    char_names.append(name)

            # Store paths, not PIL Images (PIL Images are not JSON serializable)
            job.metadata["character_image_paths"] = char_image_paths
            job.metadata["character_names"] = char_names
            logger.debug(
                f"Job {job.id}: {len(char_image_paths)} character paths, {len(char_names)} names"
            )

        # Execute jobs using panel composer
        output_dir = state.images_dir

        if not self.panel_composer:
            raise ValueError("Panel composer is required but not provided")

        await self.executor.execute_jobs(
            jobs=panel_jobs,
            generator=self.panel_composer,
            output_dir=output_dir,
        )

        # Mark stage complete
        state.mark_stage_complete(JobType.IMAGE)
        self.tracker.save_state(state)

        completed = len([j for j in panel_jobs if j.status == JobStatus.COMPLETED])
        logger.info(f"✓ Generated {completed}/{len(panel_jobs)} comic panels")

    def _save_storyline_analysis(
        self, state: PipelineState, detective_output: DetectiveStoryOutput
    ) -> None:
        """
        Save storyline analysis to a readable text file for review.
        """
        output_file = Path(state.base_dir) / state.movie_id / "storyline_analysis.txt"
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w") as f:
            f.write("=" * 80 + "\n")
            f.write("DETECTIVE COMIC STORYLINE ANALYSIS\n")
            f.write("=" * 80 + "\n\n")

            # Storyline
            f.write("STORYLINE:\n")
            f.write("-" * 80 + "\n")
            f.write(detective_output.storyline + "\n\n")

            # Narrative Structure
            f.write("NARRATIVE STRUCTURE:\n")
            f.write("-" * 80 + "\n")
            f.write(detective_output.narrative_structure + "\n\n")

            # Characters
            f.write("CHARACTERS:\n")
            f.write("-" * 80 + "\n")
            for char in detective_output.characters:
                f.write(f"\n{char.name} ({char.role})\n")
                f.write(f"  Age: {char.age}\n")
                f.write(f"  Physical: {char.physical_traits}\n")
                if char.ethnicity:
                    f.write(f"  Ethnicity: {char.ethnicity}\n")
                f.write(f"  Quirks: {', '.join(char.quirks)}\n")
                f.write(f"  Backstory: {char.backstory}\n")
                f.write(f"  Motivations: {char.motivations}\n")

                # Count panels for this character
                panel_count = len(
                    [a for a in char.actions_and_locations if a.panel is not None]
                )
                f.write(f"  Panels: {panel_count}\n")

                # List actions
                f.write("  Actions:\n")
                for idx, action in enumerate(char.actions_and_locations):
                    f.write(
                        f"    {idx+1}. [{action.timestamp}] {action.action} @ {action.location}\n"
                    )
                    if action.panel:
                        f.write(
                            f"       Panel: {action.panel.shot_type} - {action.panel.emotional_tone}\n"
                        )
                        f.write(
                            f"       Description: {action.panel.visual_description[:100]}...\n"
                        )

            # Summary
            f.write("\n" + "=" * 80 + "\n")
            f.write("SUMMARY:\n")
            f.write("-" * 80 + "\n")
            total_panels = sum(
                len([a for a in char.actions_and_locations if a.panel is not None])
                for char in detective_output.characters
            )
            f.write(f"Total Characters: {len(detective_output.characters)}\n")
            f.write(f"Total Panels: {total_panels}\n")
            f.write(f"Art Style: {self.art_style}\n")
            f.write("=" * 80 + "\n")

        logger.info(f"✓ Storyline analysis saved to: {output_file}")

    def _create_panel_jobs(self, state: PipelineState, detective_output) -> None:
        """
        Create image generation jobs for all panels in detective output.
        Follows MovieMaker pattern of _create_image_jobs(), _create_video_jobs(), etc.
        """
        panel_counter = 0
        for character in detective_output.characters:
            for idx, action in enumerate(character.actions_and_locations):
                if action.panel is None:
                    continue

                # Generate full prompt(s) using panel or beats
                if getattr(action, "beats", None):
                    for bidx, beat in enumerate(action.beats):
                        prompt = beat.to_image_prompt(self.art_style)
                        scene_id = f"scene_{panel_counter:04d}"
                        panel_counter += 1
                        job_id = f"panel_{character.name.replace(' ', '_')}_{idx:02d}_b{bidx:02d}"
                        job = Job(
                            id=job_id,
                            type=JobType.IMAGE,
                            status=JobStatus.PENDING,
                            scene_id=scene_id,
                            character_id=None,
                            metadata={
                                "character_name": character.name,
                                "action_index": idx,
                                "beat_index": bidx,
                                "timestamp": action.timestamp,
                                "action": action.action,
                                "location": action.location,
                                "prompt": prompt,
                                "art_style": self.art_style,
                                "shot_type": beat.shot_type,
                                "emotional_tone": beat.emotional_tone,
                                "orientation": beat.orientation,
                                "output_filename": f"{scene_id}.png",
                            },
                        )
                        state.add_job(job)
                else:
                    if action.panel is None:
                        continue
                    prompt = action.panel.to_image_prompt(self.art_style)
                    scene_id = f"scene_{panel_counter:04d}"
                    panel_counter += 1
                    job_id = f"panel_{character.name.replace(' ', '_')}_{idx:02d}"
                    job = Job(
                        id=job_id,
                        type=JobType.IMAGE,
                        status=JobStatus.PENDING,
                        scene_id=scene_id,
                        character_id=None,
                        metadata={
                            "character_name": character.name,
                            "action_index": idx,
                            "timestamp": action.timestamp,
                            "action": action.action,
                            "location": action.location,
                            "prompt": prompt,
                            "art_style": self.art_style,
                            "shot_type": action.panel.shot_type,
                            "emotional_tone": action.panel.emotional_tone,
                            "orientation": action.panel.orientation,
                            "output_filename": f"{scene_id}.png",
                        },
                    )
                    state.add_job(job)

    async def generate(
        self,
        constraints: PlotConstraints,
        characters: List[Character],
        movie_id: Optional[str] = None,
        base_dir: str = "./output",
    ) -> PipelineState:
        """
        Generate a detective comic strip from plot constraints.

        Args:
            constraints: Plot constraints (killer, victim, etc.)
            characters: List of characters
            movie_id: Unique ID (auto-generated if not provided)
            base_dir: Output directory
        """
        # Generate or use existing movie ID
        if not movie_id:
            movie_id = f"detective_{str(uuid.uuid4())[:8]}"

        logger.info(f"{'='*60}")
        logger.info(f"Detective Comic ID: {movie_id}")
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
            logger.info("Starting new detective comic generation...")
            state = PipelineState.create(movie_id, base_dir)

        # Ensure directories exist
        state.ensure_directories()

        # Stage 0: Plot Structure
        if not state.is_stage_complete(JobType.SCREENPLAY):
            logger.info("=== Stage 0: Plot Structure Generation ===")

            job = Job(
                id=f"plot_{state.movie_id}",
                type=JobType.SCREENPLAY,
                status=JobStatus.IN_PROGRESS,
            )
            state.add_job(job)

            try:
                plot_builder = PlotStructureBuilder()
                plot_result = await plot_builder.run(
                    {"constraints": constraints, "characters": characters}
                )

                # Store plot structure
                state.screenplay_dict = plot_result["plot_structure"]

                job.status = JobStatus.COMPLETED
                state.mark_stage_complete(JobType.SCREENPLAY)

                logger.info("✓ Plot structure generated")

            except Exception as e:
                job.status = JobStatus.FAILED
                job.error = str(e)
                logger.error(f"Plot structure generation failed: {e}")
                raise

            # Save state
            self.tracker.save_state(state)

        # Stage 1: Narrative Generation
        # Check if detective_output is already in screenplay_dict
        detective_output = None
        if state.screenplay_dict and "detective_output" in state.screenplay_dict:
            # Reconstruct from dict
            detective_output = DetectiveStoryOutput.model_validate(
                state.screenplay_dict["detective_output"]
            )
            logger.info("Loaded existing detective output from state")

        if detective_output is None:
            logger.info("=== Stage 1: Narrative Generation ===")

            try:
                # Check if plotbuilder is a Flow or Crew
                if isinstance(self.plotbuilder, StoryBuilder):
                    # Set output directory on the flow so chapter JSONs go to the right place
                    self.plotbuilder.output_base_dir = str(state.base_dir)
                    
                    # Use full StoryBuilder flow (does plot + critique + screenplay + storyboard)
                    narrative_builder = NarrativeBuilderWithStoryBuilder(
                        self.plotbuilder, self.art_style
                    )

                else:
                    # Use traditional Crew-based narrative builder
                    # This expects DetectivePlotBuilder or PlotBuilderWithCritique (Crew objects)
                    # narrative_builder = NarrativeBuilder(
                    #     self.plotbuilder, self.storyboard, self.art_style
                    # )
                    raise Exception("Invalid plotbuilder crew")

                plot_result = {
                    "plot_structure": state.screenplay_dict,
                    "graph": None,  # Will be reconstructed if needed
                }

                detective_output = await narrative_builder.run(plot_result)

                # Store output in screenplay_dict as JSON
                if not state.screenplay_dict:
                    state.screenplay_dict = {}

                # Accept both DetectiveStoryOutput and ComicBookOutput
                try:
                    from cinema.models.comic_output import ComicBookOutput
                except Exception:
                    ComicBookOutput = None  # type: ignore

                if isinstance(detective_output, DetectiveStoryOutput):
                    state.screenplay_dict["detective_output"] = (
                        detective_output.model_dump()
                    )
                    logger.info("✓ Narrative generated (DetectiveStoryOutput)")
                elif ComicBookOutput is not None and isinstance(detective_output, ComicBookOutput):
                    state.screenplay_dict["comic_output"] = (
                        detective_output.model_dump()
                    )
                    logger.info("✓ Narrative generated (ComicBookOutput)")
                else:
                    raise ValueError("Unsupported storystructure type returned by narrative builder")

            except Exception as e:
                logger.error(f"Narrative generation failed: {e}")
                raise

            # Save state
            self.tracker.save_state(state)

        # If we received a ComicBookOutput, skip legacy validation/job creation path
        try:
            from cinema.models.comic_output import ComicBookOutput
        except Exception:
            ComicBookOutput = None  # type: ignore

        if ComicBookOutput is not None and isinstance(detective_output, ComicBookOutput):
            logger.info("=== Detected ComicBookOutput; skipping legacy DetectiveStoryOutput validation and job creation ===")
            # At this point, StoryBuilder handled parallel chapter generation and persistence
            # Save state and return early
            self.tracker.save_state(state)
            return state

        # Stage 2: Validation (legacy DetectiveStoryOutput path)
        logger.info("=== Stage 2: Storyline Validation ===")

        validator = StorylineValidator(validate_only=self.validate_only)
        validated_output = await validator.run(detective_output)

        if self.validate_only:
            # Save storyline to readable file for analysis
            self._save_storyline_analysis(state, validated_output)

            logger.info("=" * 80)
            logger.info("VALIDATION COMPLETE - Review output before proceeding")
            logger.info(f"Output saved to: {state.base_dir}/{state.movie_id}")
            logger.info(
                f"Storyline analysis: {state.base_dir}/{state.movie_id}/storyline_analysis.txt"
            )
            logger.info("Set validate_only=False to generate images")
            logger.info("=" * 80)
            return state

        # Stage 3: Create panel generation jobs
        if not state.is_stage_complete(JobType.IMAGE):
            logger.info("=== Creating Panel Generation Jobs ===")

            self._create_panel_jobs(state, validated_output)

            panel_count = len([j for j in state.jobs if j.type == JobType.IMAGE])
            logger.info(f"✓ Created {panel_count} panel generation jobs")

            # Save state
            self.tracker.save_state(state)

        # Stage 3: Generate character references (NEW)
        if self.character_generator and not self.validate_only:
            await self._generate_character_references(state, detective_output)

        # Stage 4: Generate panel images (UPDATED - can use character references)
        if not self.validate_only:
            if self.panel_composer:
                # Use new modular architecture with character composition
                await self._generate_panels_with_composition(state, detective_output)
            else:
                # [DEPRECATED - REMOVABLE] Fallback to legacy image generation
                panel_generator = PanelImageGenerator(
                    max_concurrent=self.max_concurrent_images
                )
                state = await panel_generator.run(state)

        # Save final state
        self.tracker.save_state(state)

        logger.info(f"{'='*60}")
        logger.info("✓ Detective comic generation complete!")
        progress = self.tracker.get_progress(movie_id)
        logger.info(
            f"Final: {progress['completed']}/{progress['total']} jobs completed"
        )
        logger.info(f"{'='*60}")

        return state

    async def resume(self, movie_id: str, base_dir: str = "./output") -> PipelineState:
        """Resume generation for an existing detective comic"""
        state = self.tracker.load_state(movie_id, base_dir)

        if not state:
            raise ValueError(f"No state found for movie_id: {movie_id}")

        logger.info(f"{'='*60}")
        logger.info(f"Resuming detective comic: {movie_id}")
        progress = self.tracker.get_progress(movie_id)
        logger.info(
            f"Current progress: {progress['completed']}/{progress['total']} jobs"
        )
        logger.info(f"{'='*60}")

        # Load detective_output from state
        detective_output = None
        if state.screenplay_dict and "detective_output" in state.screenplay_dict:
            detective_output = DetectiveStoryOutput.model_validate(
                state.screenplay_dict["detective_output"]
            )
            logger.info("✓ Loaded detective output from state")
        else:
            logger.warning(
                "⚠️  No detective output found in state - some stages may fail"
            )

        # Continue from character reference generation if needed
        if (
            detective_output
            and self.character_generator
            and not state.is_stage_complete(JobType.CHARACTER_REF)
        ):
            await self._generate_character_references(state, detective_output)

        # Continue from panel generation if needed
        if detective_output and not state.is_stage_complete(JobType.IMAGE):
            if self.panel_composer:
                await self._generate_panels_with_composition(
                    state,
                    detective_output,
                )
            else:
                # [DEPRECATED - REMOVABLE] Legacy fallback
                panel_generator = PanelImageGenerator(
                    max_concurrent=self.max_concurrent_images
                )
                state = await panel_generator.run(state)

        # Save state
        self.tracker.save_state(state)

        return state

    def get_status(self, movie_id: str) -> dict:
        """Get current status of a detective comic generation"""
        return self.tracker.get_progress(movie_id)


# class NarrativeBuilderWithCritiqueFlow(Runner[Dict[str, Any], DetectiveStoryOutput]):
#     """
#     Stage 1: Generate narrative descriptions using Flow-based PlotBuilderWithCritique.

#     This uses PlotBuilderWithCritiqueFlow for controllable critique loop iteration.
#     The Flow provides:
#     - Explicit state machine control over the critique loop
#     - Observable iteration state with retry counter
#     - Deterministic routing based on critique verdict
#     - Better debugging capabilities
#     """

#     def __init__(
#         self,
#         plotbuilder_flow: PlotBuilderWithCritiqueFlow,
#         storyboard: ComicStripStoryBoarding,
#         art_style: str = "Noir Comic Book Style",
#     ):
#         self.plotbuilder_flow = plotbuilder_flow
#         self.storyboard = storyboard
#         self.art_style = art_style

#     async def run(self, inputs: Dict[str, Any]) -> DetectiveStoryOutput:
#         logger.info("=== Stage 1: Narrative Generation (with Critique Flow) ===")

#         plot_structure = inputs["plot_structure"]

#         # Build input for plot builder flow
#         from cinema.agents.bookwriter.flow import StoryBuilderInput
#         from cinema.agents.bookwriter.crew import DetectivePlotBuilderSchema

#         # constraints are already in crew-compatible format (markdown strings)
#         plot_builder_schema = DetectivePlotBuilderSchema(
#             characters=plot_structure["graph"]["characters"],
#             relationships=plot_structure["timeline"],
#             killer=plot_structure["constraints"]["killer"],
#             victim=plot_structure["constraints"]["victim"],
#             accomplices=plot_structure["constraints"]["accomplices"],
#             witnesses=plot_structure["constraints"]["witnesses"],
#             betrayals=plot_structure["constraints"]["betrayals"],
#         )

#         story_input = StoryBuilderInput(
#             plotbuilder=plot_builder_schema
#         )

#         # Set input in flow state
#         self.plotbuilder_flow.state.input = story_input

#         # Run the flow - this will iterate through plan -> critique -> evaluate
#         logger.info("Running PlotBuilderWithCritiqueFlow...")
#         result = await self.plotbuilder_flow.kickoff_async()

#         # Extract storyline from flow output
#         if not isinstance(result, StoryBuilderOutput):
#             logger.error("Flow did not return StoryBuilderOutput")
#             raise ValueError("Flow did not return StoryBuilderOutput")

#         narrative_text = result.storyline
#         if not narrative_text:
#             logger.error("Flow did not generate storyline")
#             raise ValueError("Flow did not generate storyline")

#         logger.info(f"✓ Storyline generated with {result.retry_count} critique iterations")

#         # Build input for comic strip storyboarding
#         storyboard_input = {
#             "storyline": narrative_text,
#             "art_style": self.art_style,
#             "examples": ComicStripStoryBoarding.load_examples(),
#         }

#         # Run comic strip storyboarding crew
#         logger.info("Running ComicStripStoryBoarding crew...")
#         storyboard_result = await self.storyboard.crew().kickoff_async(
#             inputs=storyboard_input
#         )

#         # Collect as DetectiveStoryOutput
#         detective_output = ComicStripStoryBoarding.collect(
#             storyboard_result, DetectiveStoryOutput
#         )

#         if not isinstance(detective_output, DetectiveStoryOutput):
#             logger.error("Failed to generate detective story output")
#             raise ValueError("Failed to generate detective story output")

#         logger.info("✓ Narrative generation complete")
#         logger.info(f"  Characters: {len(detective_output.characters)}")
#         logger.info(f"  Narrative structure: {detective_output.narrative_structure}")

#         return detective_output


# class NarrativeBuilder(Runner[Dict[str, Any], DetectiveStoryOutput]):
#     """
#     Stage 1: Generate narrative descriptions using LLM crews.
#     Takes plot structure and generates character profiles, backstories, and storyline.
#
#     NOTE: This uses the basic DetectivePlotBuilder without critique loop.
#     For critique loop support, use NarrativeBuilderWithCritiqueFlow instead.
#     """
#
#     def __init__(
#         self,
#         plotbuilder: DetectivePlotBuilder,
#         storyboard: ComicStripStoryBoarding,
#         art_style: str = "Noir Comic Book Style",
#     ):
#         self.plotbuilder = plotbuilder
#         self.storyboard = storyboard
#         self.art_style = art_style
#
#     async def run(self, inputs: Dict[str, Any]) -> DetectiveStoryOutput:
#         logger.info("=== Stage 1: Narrative Generation ===")
#
#         plot_structure = inputs["plot_structure"]
#
#         # Build input for detective plot builder
#         # Note: constraints are already converted via to_crew() in PlotStructureBuilder
#         plot_input = {
#             "characters": plot_structure["graph"]["characters"],
#             "relationships": plot_structure["timeline"],
#             "storyline": "Generated",
#             **plot_structure["constraints"],  # Already in crew-compatible format
#         }
#
#         # Run detective plot builder crew
#         logger.info("Running DetectivePlotBuilder crew...")
#         plot_result = await self.plotbuilder.crew().kickoff_async(inputs=plot_input)
#
#         # Collect narrative structure
#         narrative_text = DetectivePlotBuilder.collect(plot_result)  # type: ignore[attr-defined]
#
#         # Build input for comic strip storyboarding
#         storyboard_input = {
#             "storyline": narrative_text,
#             "art_style": self.art_style,
#             "examples": ComicStripStoryBoarding.load_examples(),
#         }
#
#         # Run comic strip storyboarding crew
#         logger.info("Running ComicStripStoryBoarding crew...")
#         storyboard_result = await self.storyboard.crew().kickoff_async(
#             inputs=storyboard_input
#         )
#
#         # Collect as DetectiveStoryOutput
#         detective_output = ComicStripStoryBoarding.collect(  # type: ignore[attr-defined]
#             storyboard_result, DetectiveStoryOutput
#         )
#
#         if not isinstance(detective_output, DetectiveStoryOutput):
#             logger.error("Failed to generate detective story output")
#             raise ValueError("Failed to generate detective story output")
#
#         logger.info("✓ Narrative generation complete")
#         logger.info(f"  Characters: {len(detective_output.characters)}")
#         logger.info(f"  Narrative structure: {detective_output.narrative_structure}")
#
#         return detective_output
