"""
Detective Comic Strip generation pipeline implementation.
Follows the same pattern as MovieMaker with JobTracker and GeminiMediaGen integration.
"""

import logging
import uuid
from pathlib import Path
from typing import Any, Dict, Optional, List, Union

from cinema.agents.bookwriter.models import Character, PlotConstraints
from cinema.agents.bookwriter.crew import DetectivePlotBuilder, ComicStripStoryBoarding, PlotBuilderWithCritique, PlotCritique
from cinema.models.detective_output import DetectiveStoryOutput
from cinema.agents.bookwriter.detective import (
    ConstraintTableBuilder,
    ConsistencyValidator,
    TruthTable,
)
from cinema.pipeline.pipeline import Runner
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

        logger.info(f"✓ Plot structure generated: {len(graph.action_sequences)} actions")

        return {
            **inputs,
            "plot_structure": plot_structure,
            "graph": graph,
        }


class NarrativeBuilder(Runner[Dict[str, Any], DetectiveStoryOutput]):
    """
    Stage 1: Generate narrative descriptions using LLM crews.
    Takes plot structure and generates character profiles, backstories, and storyline.
    """

    def __init__(
        self,
        plotbuilder: DetectivePlotBuilder,
        storyboard: ComicStripStoryBoarding,
        art_style: str = "Noir Comic Book Style",
    ):
        self.plotbuilder = plotbuilder
        self.storyboard = storyboard
        self.art_style = art_style

    async def run(self, inputs: Dict[str, Any]) -> DetectiveStoryOutput:
        logger.info("=== Stage 1: Narrative Generation ===")

        plot_structure = inputs["plot_structure"]

        # Build input for detective plot builder
        # Note: constraints are already converted via to_crew() in PlotStructureBuilder
        plot_input = {
            "characters": plot_structure["graph"]["characters"],
            "relationships": plot_structure["timeline"],
            "storyline": "Generated",
            **plot_structure["constraints"],  # Already in crew-compatible format
        }

        # Run detective plot builder crew
        logger.info("Running DetectivePlotBuilder crew...")
        plot_result = await self.plotbuilder.crew().kickoff_async(inputs=plot_input)

        # Collect narrative structure
        narrative_text = DetectivePlotBuilder.collect(plot_result)  # type: ignore[attr-defined]

        # Build input for comic strip storyboarding
        storyboard_input = {
            "storyline": narrative_text,
            "art_style": self.art_style,
            "examples": ComicStripStoryBoarding.load_examples(),
        }

        # Run comic strip storyboarding crew
        logger.info("Running ComicStripStoryBoarding crew...")
        storyboard_result = await self.storyboard.crew().kickoff_async(
            inputs=storyboard_input
        )

        # Collect as DetectiveStoryOutput
        detective_output = ComicStripStoryBoarding.collect(  # type: ignore[attr-defined]
            storyboard_result, DetectiveStoryOutput
        )

        if not isinstance(detective_output, DetectiveStoryOutput):
            logger.error("Failed to generate detective story output")
            raise ValueError("Failed to generate detective story output")

        logger.info("✓ Narrative generation complete")
        logger.info(f"  Characters: {len(detective_output.characters)}")
        logger.info(f"  Narrative structure: {detective_output.narrative_structure}")

        return detective_output


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
            logger.warning("="*80)
            logger.warning("VALIDATION ONLY MODE - Stopping before image generation")
            logger.warning("Review the storyline and set validate_only=False to proceed")
            logger.warning("="*80)
            # Don't raise exception, just return - pipeline will stop naturally
            return inputs

        logger.info("✓ Validation passed, proceeding to image generation")
        return inputs


class PanelImageGenerator(Runner[PipelineState, PipelineState]):
    """
    Stage 3: Generate comic panel images.
    Generates images for panel jobs using GeminiMediaGen.
    """

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

        gemini = GeminiMediaGen()

        for job in pending:
            try:
                job.status = JobStatus.IN_PROGRESS

                # Get prompt from job metadata
                prompt = job.metadata["prompt"]
                character_name = job.metadata["character_name"]
                action_index = job.metadata["action_index"]

                # Build output path
                output_filename = f"{character_name.replace(' ', '_')}_{action_index:02d}.png"
                output_path = state.images_dir / output_filename

                # Check if cached
                if output_path.exists() and output_path.stat().st_size > 0:
                    logger.info(f"  ⊙ Cached {output_filename}")
                    job.output_path = str(output_path)
                    job.status = JobStatus.COMPLETED
                    continue

                # Generate image
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


class DetectiveMaker:
    """
    Main orchestrator for detective comic strip generation.
    Follows the same pattern as MovieMaker with JobTracker integration.
    """

    def __init__(
        self,
        plotbuilder: Union[DetectivePlotBuilder, PlotBuilderWithCritique],
        storyboard: ComicStripStoryBoarding,
        db_path: str = "./cinema_jobs.db",
        art_style: str = "Noir Comic Book Style",
        validate_only: bool = False,
    ):
        self.plotbuilder = plotbuilder
        self.storyboard = storyboard
        self.art_style = art_style
        self.validate_only = validate_only

        from cinema.pipeline.job_tracker import JobTracker

        self.tracker = JobTracker(db_path)
    
    def _save_storyline_analysis(
        self,
        state: PipelineState,
        detective_output: DetectiveStoryOutput
    ) -> None:
        """
        Save storyline analysis to a readable text file for review.
        """
        output_file = Path(state.base_dir) / state.movie_id / "storyline_analysis.txt"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, "w") as f:
            f.write("="*80 + "\n")
            f.write("DETECTIVE COMIC STORYLINE ANALYSIS\n")
            f.write("="*80 + "\n\n")
            
            # Storyline
            f.write("STORYLINE:\n")
            f.write("-"*80 + "\n")
            f.write(detective_output.storyline + "\n\n")
            
            # Narrative Structure
            f.write("NARRATIVE STRUCTURE:\n")
            f.write("-"*80 + "\n")
            f.write(detective_output.narrative_structure + "\n\n")
            
            # Characters
            f.write("CHARACTERS:\n")
            f.write("-"*80 + "\n")
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
                panel_count = len([a for a in char.actions_and_locations if a.panel is not None])
                f.write(f"  Panels: {panel_count}\n")
                
                # List actions
                f.write(f"  Actions:\n")
                for idx, action in enumerate(char.actions_and_locations):
                    f.write(f"    {idx+1}. [{action.timestamp}] {action.action} @ {action.location}\n")
                    if action.panel:
                        f.write(f"       Panel: {action.panel.shot_type} - {action.panel.emotional_tone}\n")
                        f.write(f"       Description: {action.panel.visual_description[:100]}...\n")
            
            # Summary
            f.write("\n" + "="*80 + "\n")
            f.write("SUMMARY:\n")
            f.write("-"*80 + "\n")
            total_panels = sum(
                len([a for a in char.actions_and_locations if a.panel is not None])
                for char in detective_output.characters
            )
            f.write(f"Total Characters: {len(detective_output.characters)}\n")
            f.write(f"Total Panels: {total_panels}\n")
            f.write(f"Art Style: {self.art_style}\n")
            f.write("="*80 + "\n")
        
        logger.info(f"✓ Storyline analysis saved to: {output_file}")
    
    def _create_panel_jobs(
        self, 
        state: PipelineState, 
        detective_output
    ) -> None:
        """
        Create image generation jobs for all panels in detective output.
        Follows MovieMaker pattern of _create_image_jobs(), _create_video_jobs(), etc.
        """
        for character in detective_output.characters:
            for idx, action in enumerate(character.actions_and_locations):
                if action.panel is None:
                    continue
                
                # Generate full prompt using panel's to_image_prompt method
                prompt = action.panel.to_image_prompt(self.art_style)
                
                # Create job ID
                job_id = f"panel_{character.name.replace(' ', '_')}_{idx:02d}"
                
                # Create job with JobType.IMAGE (existing type for image generation)
                job = Job(
                    id=job_id,
                    type=JobType.IMAGE,
                    status=JobStatus.PENDING,
                    scene_id=None,  # Not scene-based, character action-based
                    character_id=None,
                    metadata={
                        "character_name": character.name,
                        "action_index": idx,
                        "timestamp": action.timestamp,
                        "action": action.action,
                        "location": action.location,
                        "prompt": prompt,  # Full structured prompt from panel.to_image_prompt()
                        "art_style": self.art_style,
                        "shot_type": action.panel.shot_type,
                        "emotional_tone": action.panel.emotional_tone,
                        "orientation": action.panel.orientation,
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
                narrative_builder = NarrativeBuilder(
                    self.plotbuilder, self.storyboard, self.art_style
                )

                plot_result = {
                    "plot_structure": state.screenplay_dict,
                    "graph": None,  # Will be reconstructed if needed
                }

                detective_output = await narrative_builder.run(plot_result)

                # Store detective output in screenplay_dict as JSON
                if not state.screenplay_dict:
                    state.screenplay_dict = {}
                state.screenplay_dict["detective_output"] = detective_output.model_dump()

                logger.info("✓ Narrative generated")

            except Exception as e:
                logger.error(f"Narrative generation failed: {e}")
                raise

            # Save state
            self.tracker.save_state(state)

        # Stage 2: Validation
        logger.info("=== Stage 2: Storyline Validation ===")

        validator = StorylineValidator(validate_only=self.validate_only)
        validated_output = await validator.run(detective_output)

        if self.validate_only:
            # Save storyline to readable file for analysis
            self._save_storyline_analysis(state, validated_output)
            
            logger.info("="*80)
            logger.info("VALIDATION COMPLETE - Review output before proceeding")
            logger.info(f"Output saved to: {state.base_dir}/{state.movie_id}")
            logger.info(f"Storyline analysis: {state.base_dir}/{state.movie_id}/storyline_analysis.txt")
            logger.info("Set validate_only=False to generate images")
            logger.info("="*80)
            return state

        # Stage 3: Create panel generation jobs
        if not state.is_stage_complete(JobType.IMAGE):
            logger.info("=== Creating Panel Generation Jobs ===")

            self._create_panel_jobs(state, validated_output)

            panel_count = len([j for j in state.jobs if j.type == JobType.IMAGE])
            logger.info(f"✓ Created {panel_count} panel generation jobs")

            # Save state
            self.tracker.save_state(state)

        # Stage 4: Generate panel images
        panel_generator = PanelImageGenerator()
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

        # Continue from panel generation if needed
        if not state.is_stage_complete(JobType.IMAGE):
            panel_generator = PanelImageGenerator()
            state = await panel_generator.run(state)

        # Save state
        self.tracker.save_state(state)

        return state

    def get_status(self, movie_id: str) -> dict:
        """Get current status of a detective comic generation"""
        return self.tracker.get_progress(movie_id)
