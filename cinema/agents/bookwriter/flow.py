import logging
from typing import Any, Dict, List, Literal, Optional

from crewai.flow.flow import Flow, listen, or_, router, start
from pydantic import BaseModel, Field

from cinema.agents.bookwriter.crew import (
    BookWriter,
    ComicStripStoryBoarding,
    CritiqueSchema,
    DetectivePlotBuilder,
    DetectivePlotBuilderSchema,
    PlotCritique,
    ScreenplayWriter,
    ScreenplayWriterSchema,
    StripperInputSchema,
)
from cinema.context import DirectorsContext
from cinema.models.comic_output import ComicBookOutput
from cinema.models.detective_output import DetectiveStoryOutput
from cinema.models.novel import Novel
from cinema.pipeline.parallel_comic_generator import ParallelComicGenerator

logger = logging.getLogger(__name__)

MAX_RETRIES = 3


class StoryBuilderOutput(BaseModel):
    storyline: Optional[str] = None
    critique: Optional[str] = None
    screenplay: Optional[str] = None
    storystructure: Optional[DetectiveStoryOutput | ComicBookOutput] = None
    retry_count: int = 0
    errors: list[str] = []  # Store error messages as strings


class StoryBuilderInput(BaseModel):
    plotbuilder: Optional[DetectivePlotBuilderSchema] = None
    stripper: Optional[StripperInputSchema] = None
    critiuqe: Optional[CritiqueSchema] = None
    screenplay: Optional[ScreenplayWriterSchema] = None


class StoryBuilderState(BaseModel):
    id: str = ""
    current_state: Literal[
        "start",
        "plan",
        "critique",
        "screenplay",
        "storyboard",
        "success",
        "error",
    ] = "start"

    input: Optional[StoryBuilderInput] = None
    
    halted_at: Optional[str] = None
    waits_at: Dict[str, bool] = {"storyboard": False}
    output: Optional[StoryBuilderOutput] = None

    # Configuration flags
    skip_storyboard: bool = False  # If True, stop after critique passes


_skippers = {
    "e": True,
}


class StoryBuilder(Flow[StoryBuilderState]):
    ctx: DirectorsContext

    plotbuilder: DetectivePlotBuilder
    critique: PlotCritique
    storyboard: ComicStripStoryBoarding
    screenplay: ScreenplayWriter
    booker: BookWriter

    # Cache crew instances to avoid re-initializing knowledge
    _plotbuilder_crew = None
    _critique_crew = None
    _storyboard_crew = None
    _screenplay_crew = None
    _booker_crew = None

    generation_target: str = "bookerama"  # or "screenplay"
    output_base_dir: Optional[str] = None  # Optional: output directory from pipeline

    def save_state(self):
        """Save flow state to disk for resume capability"""
        import json
        from pathlib import Path
        
        state_dir = Path("output/flow_states")
        state_dir.mkdir(parents=True, exist_ok=True)
        
        state_file = state_dir / f"storybuilder_{self.state.id}.json"
        
        # Serialize state
        state_data = self.state.model_dump()
        
        with open(state_file, 'w') as f:
            json.dump(state_data, f, indent=2)
        
        logger.info(f"💾 Flow state saved to: {state_file}")
        logger.info(f"   Flow ID: {self.state.id}")
        logger.info(f"   Halted at: {self.state.halted_at}")
        logger.info(f"   To resume: --continue {self.state.id}")
    
    @classmethod
    def load_state(cls, flow_id: str) -> dict:
        """Load flow state from disk"""
        import json
        from pathlib import Path
        
        state_file = Path(f"output/flow_states/storybuilder_{flow_id}.json")
        
        if not state_file.exists():
            raise FileNotFoundError(f"Flow state not found: {state_file}")
        
        with open(state_file, 'r') as f:
            state_data = json.load(f)
        
        logger.info(f"📂 Flow state loaded from: {state_file}")
        logger.info(f"   Flow ID: {flow_id}")
        logger.info(f"   Halted at: {state_data.get('halted_at')}")
        
        return state_data
    
    @classmethod
    def resume_from_halt(cls, flow_id: str, **kwargs):
        """Resume a halted flow from saved state"""
        state_data = cls.load_state(flow_id)
        
        # Reset the halt flag for the halted stage
        halted_at = state_data.get('halted_at')
        if halted_at and halted_at in state_data.get('waits_at', {}):
            state_data['waits_at'][halted_at] = False
            logger.info(f"🔄 Resuming from {halted_at}, reset waits_at['{halted_at}'] = False")
        
        # Clear halted_at
        state_data['halted_at'] = None
        
        # Build flow with loaded state
        return cls.build(initial_state=state_data, **kwargs)

    @classmethod
    def build(
        cls,
        ctx: DirectorsContext,
        plotbuilder: DetectivePlotBuilder,
        critique: PlotCritique,
        storyboard: ComicStripStoryBoarding,
        screenplay: ScreenplayWriter,
        booker: BookWriter,
        initial_state: dict | None = None,
        output_base_dir: Optional[str]= None,
        flow_id: Optional[str] = None,
    ):

        if not initial_state:
            initial_state = {}
        
        # Set flow ID if provided (for syncing with detective_{id})
        if flow_id and 'id' not in initial_state:
            initial_state['id'] = flow_id
            logger.info(f"🆔 Flow ID set to: {flow_id}")

        o = cls(**initial_state)
        o.ctx = ctx
        o.output_base_dir = output_base_dir

        o.plotbuilder = plotbuilder
        o.critique = critique
        o.storyboard = storyboard
        o.screenplay = screenplay
        o.booker = booker

        return o

    def update_state(self, now_state: str):
        if self.state.current_state == now_state:
            return

        # should have validation on transition
        self.state.current_state = now_state  # type:ignore

    @start()
    def resume(self):
        logger.info("== " * 10)
        # logger.info(self.state)

        if self.state.output is None:
            self.state.output = StoryBuilderOutput()

        return self.state.current_state

    @router(resume)
    def director(self):
        if self.state.current_state == "start":
            self.update_state("plan")

        logger.info(f"directing to {self.state.current_state}")

        return self.state.current_state

    @listen("plan")
    async def handle_storybuilding(self):
        assert self.state.input is not None, "InputNotFound"
        assert self.state.output is not None, "OutputNotFound"
        assert self.state.input.plotbuilder is not None, "PlotSchemaNotFound"

        logger.info(
            f"[Iteration {self.state.output.retry_count + 1}/{MAX_RETRIES}] Running DetectivePlotBuilder..."
        )

        plot_inputs: dict[str, Any] = self.state.input.plotbuilder.model_dump()

        # Check if feedback exists from previous iteration
        if self.state.output.critique:
            logger.info("Incorporating feedback from previous critique")
            logger.debug(f"Feedback: {self.state.output.critique}")

            plot_inputs["feedback"] = self.state.output.critique
            plot_inputs["storyline"] = self.state.output.storyline

        # Reuse crew instance to avoid re-initializing knowledge
        if self._plotbuilder_crew is None:
            self._plotbuilder_crew = self.plotbuilder.crew()

        plot_result = await self._plotbuilder_crew.kickoff_async(inputs=plot_inputs)

        # Collect narrative structure
        narrative_text = DetectivePlotBuilder.collect(plot_result)
        self.state.output.storyline = narrative_text

        logger.info(
            f"✓ Storyline generated ({len(narrative_text) if narrative_text else 0} chars)"
        )

    @listen(or_("critique", handle_storybuilding))
    async def handle_critique(self):
        assert self.state.input is not None, "InputNotFound"
        assert self.state.output is not None, "OutputNotFound"
        assert self.state.output.storyline is not None, "StorylineNotFound"
        assert self.state.input.plotbuilder is not None

        logger.info("Running PlotCritique...")

        inputs = CritiqueSchema(storyline=self.state.output.storyline)

        self.update_state("critique")

        # Reuse crew instance to avoid re-initializing knowledge
        if self._critique_crew is None:
            self._critique_crew = self.critique.crew()

        result = await self._critique_crew.kickoff_async(
            inputs=inputs.model_dump(),
        )

        critique_result: str = PlotCritique.collect(result)
        self.state.output.critique = critique_result

        logger.info(f"✓ Critique completed ({len(critique_result)} chars.")
        logger.info(f"Critique Result: {critique_result}")

        return

    @router(handle_critique)
    def eval_plotline(self):
        assert self.state.input is not None, "InputNotFound"
        assert self.state.output is not None, "OutputNotFound"
        assert self.state.input.plotbuilder is not None, "PlotSchemaNotFound"
        assert self.state.output.critique is not None, "FeedbackNotFound"

        if _skippers["e"]:
            logger.info("Skipping eval")

            self.update_state(self.generation_target)
            return self.state.current_state

        critique_result = self.state.output.critique

        # Parse verdict from critique
        section = "## Final Binary Verdict"
        splits = critique_result.split(section, 1)

        verdict = "FAIL"
        if len(splits) >= 2:
            verdict_check = splits[1][:200].upper()
            if "- PASS" in verdict_check or "PASS" in verdict_check.split("\n")[0]:
                verdict = "PASS"

        logger.info(f"Evaluating critique verdict: {verdict}")

        if verdict == "PASS":
            logger.info("✓ Critique PASSED")
            self.state.output.critique = None

            # Check if we should skip storyboarding
            if self.state.skip_storyboard:
                logger.info("Skipping storyboard (skip_storyboard=True)")
                self.update_state("success")
            else:
                self.update_state(self.generation_target)  # "screenplay")

        elif self.state.output.retry_count > MAX_RETRIES:  # because 0 indexed
            logger.warning(f"⚠ Max retries ({MAX_RETRIES}) reached")
            logger.info(f"Skipping? {self.state.skip_storyboard}")

            self.state.output.retry_count += 1

            if self.state.skip_storyboard:
                self.update_state("success")
            else:
                self.update_state(self.generation_target)

        else:
            logger.info(
                f"✗ Critique FAILED - retrying with feedback (attempt {self.state.output.retry_count + 1}/{MAX_RETRIES})"
            )
            self.state.output.retry_count += 1
            # Feedback will be picked up in handle_storybuilding via output.critique
            self.update_state("plan")

        return self.state.current_state

    @listen("screenplay")
    async def handle_screenplay(self):
        logger.info("Running Screenplay writing crew...")

        assert self.state.input is not None
        assert self.state.input.stripper is not None
        assert self.state.input.screenplay is not None
        assert self.state.output is not None
        assert self.state.output.storyline is not None

        self.update_state("screenplay")

        screenplay = ScreenplayWriterSchema(
            storyline=self.state.output.storyline,
            art_style=self.state.input.stripper.art_style,
            examples=self.state.input.screenplay.examples,
        )

        if self._screenplay_crew is None:
            self._screenplay_crew = self.screenplay.crew()

        result = await self._screenplay_crew.kickoff_async(
            inputs=screenplay.model_dump(),
        )

        # Collect as DetectiveStoryOutput
        output = ScreenplayWriter.collect(  # type: ignore[attr-defined]
            result,
        )

        self.state.output.screenplay = output
        logger.info("✓ Screenplay Generated generated")

        self.update_state("storyboard")

        return self.state.current_state

    @listen("bookerama")
    async def handle_book_writing(self):
        logger.info("Running Book writing crew...")

        assert self.state.input is not None
        assert self.state.input.stripper is not None
        assert self.state.input.screenplay is not None
        assert self.state.output is not None
        assert self.state.output.storyline is not None

        self.update_state("bookerama")

        # NOTE: Reusing for Novel Crew
        screenplay = ScreenplayWriterSchema(
            storyline=self.state.output.storyline,
            art_style=self.state.input.stripper.art_style,
            examples="",
        )

        if self._booker_crew is None:
            self._booker_crew = self.booker.crew()

        result = await self._booker_crew.kickoff_async(
            inputs=screenplay.model_dump(),
        )

        # Collect as DetectiveStoryOutput
        output = BookWriter.collect(  # type: ignore[attr-defined]
            result,
        )
        self.state.output.screenplay = output

        logger.info("✓ Screenplay Generated generated")

        self.update_state("storyboard")

        return self.state.current_state

    @listen(or_("storyboard", handle_screenplay, handle_book_writing))
    async def handle_storyboarding(self):
        logger.info("Running Parallel Comic Generation...")

        assert self.state.input is not None
        assert self.state.input.stripper is not None
        assert self.state.output is not None
        assert self.state.output.screenplay is not None

        self.update_state("storyboard")
        
        # Check if we should halt at storyboard
        if self.state.waits_at.get("storyboard", False):
            logger.info("⏸️  Flow halted at storyboard stage (waits_at['storyboard'] = True)")
            self.state.halted_at = "storyboard"
            self.save_state()
            return "halted"

        # Parse novel from bookerama output
        logger.info("Parsing novel from screenplay output...")
        novel = Novel.from_str(self.state.output.screenplay)
        logger.info(f"Parsed novel: {novel.title} with {len(novel.chapters)} chapters")

        # Use parallel generator to process chapters
        # If we have access to output directory from pipeline state, pass it
        output_dir = getattr(self, 'output_base_dir', None)
        
        generator = ParallelComicGenerator(
            ctx=self.ctx,
            screenplay=self.state.output.screenplay,
            max_concurrent=3,  # Process 3 chapters at a time
            output_base_dir=output_dir  # Will save chapter JSONs if provided
        )

        comic_output = await generator.generate(
            novel=novel,
            art_style=self.state.input.stripper.art_style
        )

        # Store result
        self.state.output.storystructure = comic_output
        logger.info("✓ Parallel comic generation complete")

        self.update_state("success")
        return self.state.current_state

    @listen(handle_storyboarding)
    def handle_end(self):
        logger.info(f"end state {self.state.current_state}")
        
        # Check if flow was halted
        if self.state.halted_at:
            logger.info(f"⏸️  Flow halted at: {self.state.halted_at}")
            return "halted"
        
        if self.state.current_state == "error":
            return self.state.output and self.state.output.errors

        return "success"

    @listen("success")
    def handle_success(self):
        logger.info("=" * 80)
        logger.info("STORYBUILDER FLOW COMPLETE")
        logger.info("=" * 80)

        if self.state.output:
            logger.info(
                f"Storyline length: {len(self.state.output.storyline) if self.state.output.storyline else 0} chars"
            )
            logger.info(
                f"Critique length: {len(self.state.output.critique) if self.state.output.critique else 0} chars"
            )
            logger.info(
                f"Storystructure: {'Generated' if self.state.output.storystructure else 'None'}"
            )
            logger.info(f"Retry count: {self.state.output.retry_count}")

            if self.state.output.storystructure:
                logger.info(
                    f"Characters: {len(self.state.output.storystructure.characters)}"
                )
                logger.info(
                    f"Narrative structure: {self.state.output.storystructure.narrative_structure}"
                )
                logger.info(f"Art style: {self.state.output.storystructure.art_style}")

        logger.info("=" * 80)
        return self.state.output

    @listen("error")
    def handle_error(self):
        return self.state.output and self.state.output.errors


# ============================================================================
# PlotBuilderWithCritiqueFlow - Plot + Critique Only (No Storyboarding)
# ============================================================================

# class PlotBuilderWithCritiqueState(BaseModel):
#     """State for PlotBuilderWithCritiqueFlow - Plot + Critique only"""
#     current_state: Literal[
#         "start",
#         "plan",
#         "critique",
#         "evaluate",
#         "success",
#         "error",
#     ] = "start"

#     # Input: Type-safe plot structure
#     input: Optional[StoryBuilderInput] = None

#     # Output: storyline + critique (no storystructure)
#     output: Optional[StoryBuilderOutput] = None


# class PlotBuilderWithCritiqueFlow(Flow[PlotBuilderWithCritiqueState]):
#     """
#     Flow for Plot + Critique only (no storyboarding).

#     Flow: start → plan → critique → evaluate → success/error

#     - Runs DetectivePlotBuilder to generate storyline
#     - Runs PlotCritique to validate storyline
#     - Loops back with feedback if critique fails
#     - Terminates on PASS or MAX_RETRIES
#     - Does NOT run storyboarding
#     """

#     ctx: DirectorsContext
#     plotbuilder: DetectivePlotBuilder
#     critique: PlotCritique
#     screenplay: ScreenplayWriter

#     # Cache crew instances to avoid re-initializing knowledge
#     _plotbuilder_crew = None
#     _critique_crew = None
#     _storyboard_crew = None
#     _screenplay_crew = None

#     @classmethod
#     def build(
#         cls,
#         ctx: DirectorsContext,
#         plotbuilder: DetectivePlotBuilder,
#         critique: PlotCritique,
#         screenplay: ScreenplayWriter,
#         initial_state: dict | None = None,
#     ):
#         """Build a new flow instance"""
#         if not initial_state:
#             initial_state = {}

#         o = cls(**initial_state)
#         o.ctx = ctx
#         o.plotbuilder = plotbuilder
#         o.critique = critique
#         o.screenplay = screenplay

#         return o

#     def update_state(self, now_state: str):
#         """Update state with validation"""
#         if self.state.current_state == now_state:
#             return

#         # Validate state transition
#         valid_states = ["start", "plan", "critique", "evaluate", "success", "error"]
#         if now_state not in valid_states:
#             raise ValueError(f"Invalid state: {now_state}")

#         self.state.current_state = now_state  # type: ignore

#     @start()
#     def resume(self):
#         """Entry point - initialize output if needed"""
#         logger.info("="*40)
#         logger.info("PlotBuilderWithCritiqueFlow: Starting")
#         logger.info("="*40)

#         if self.state.output is None:
#             self.state.output = StoryBuilderOutput()

#         return self.state.current_state

#     @router(resume)
#     def director(self):
#         """Route from start to plan"""
#         if self.state.current_state == "start":
#             self.update_state("plan")

#         logger.info(f"Routing to: {self.state.current_state}")
#         return self.state.current_state

#     @listen("plan")
#     async def handle_plotbuilding(self):
#         """Run DetectivePlotBuilder crew to generate storyline"""
#         assert self.state.input is not None, "InputNotFound"
#         assert self.state.input.plotbuilder is not None, "PlotSchemaNotFound"
#         assert self.state.output is not None, "OutputNotFound"

#         logger.info(f"[Iteration {self.state.output.retry_count + 1}/{MAX_RETRIES}] Running DetectivePlotBuilder...")

#         # Convert to dict for kickoff_async
#         plot_inputs: dict[str, Any] = dict(self.state.input.plotbuilder)

#         # Check if feedback exists from previous iteration
#         if self.state.output.critique:
#             logger.info(f"Incorporating feedback from previous critique")
#             plot_inputs["feedback"] = self.state.output.critique
#             plot_inputs["storyline"] = self.state.output.storyline

#         # Reuse crew instance to avoid re-initializing knowledge
#         if self._plotbuilder_crew is None:
#             self._plotbuilder_crew = self.plotbuilder.crew()

#         # Run plotbuilder crew
#         plot_result = await self._plotbuilder_crew.kickoff_async(
#             inputs=plot_inputs
#         )

#         # Collect storyline
#         narrative_text = DetectivePlotBuilder.collect(plot_result)
#         self.state.output.storyline = narrative_text

#         logger.info(f"✓ Storyline generated ({len(narrative_text) if narrative_text else 0} chars)")

#     @listen(handle_plotbuilding)
#     async def handle_critique(self):
#         """Run PlotCritique crew to validate storyline"""
#         assert self.state.output is not None, "OutputNotFound"
#         assert self.state.output.storyline is not None, "StorylineNotFound"

#         logger.info("Running PlotCritique...")

#         self.update_state("critique")

#         # Prepare critique input
#         critique_input = CritiqueSchema(
#             storyline=self.state.output.storyline
#         )

#         # Reuse crew instance to avoid re-initializing knowledge
#         if self._critique_crew is None:
#             self._critique_crew = self.critique.crew()

#         # Run critique crew
#         critique_inputs: dict[str, Any] = dict(critique_input)
#         critique_result = await self._critique_crew.kickoff_async(
#             inputs=critique_inputs
#         )

#         # Collect critique
#         critique_text: str = PlotCritique.collect(critique_result)
#         self.state.output.critique = critique_text

#         logger.info(f"✓ Critique completed ({len(critique_text)} chars)")

#     @router(handle_critique)
#     def eval_critique(self):
#         """
#         Evaluate critique verdict and route accordingly.

#         Routes to:
#         - "success" if critique passes
#         - "success" if max retries reached
#         - "plan" to retry with feedback
#         """
#         assert self.state.input is not None, "InputNotFound"
#         assert self.state.output is not None, "OutputNotFound"
#         assert self.state.output.critique is not None, "CritiqueNotFound"

#         self.update_state("evaluate")

#         critique_text = self.state.output.critique
#         section = "## Final Binary Verdict"

#         splits = critique_text.split(section, 1)

#         verdict = "FAIL"
#         if len(splits) >= 2:
#             verdict_check = splits[1][:200].upper()
#             if "- PASS" in verdict_check or "PASS" in verdict_check.split('\n')[0]:
#                 verdict = "PASS"

#         logger.info(f"Evaluating critique verdict: {verdict}")

#         if verdict == "PASS":
#             logger.info("✓ Critique PASSED - storyline approved")

#             self.state.output.critique = None
#             self.update_state("success")

#         elif self.state.output.retry_count >= MAX_RETRIES - 1:
#             logger.warning(f"⚠ Max retries ({MAX_RETRIES}) reached - accepting storyline")
#             self.update_state("success")

#         else:
#             logger.info(f"✗ Critique FAILED - retrying with feedback")
#             self.state.output.retry_count += 1
#             # Feedback will be picked up in handle_plotbuilding via output.critique
#             self.update_state("plan")

#         return self.state.current_state

#     @listen("success")
#     def handle_success(self):
#         """Return final output"""
#         logger.info("="*80)
#         logger.info("PLOTBUILDER WITH CRITIQUE FLOW COMPLETE")
#         logger.info("="*80)
#         if self.state.output:
#             logger.info(f"Storyline length: {len(self.state.output.storyline) if self.state.output.storyline else 0} chars")
#             logger.info(f"Critique length: {len(self.state.output.critique) if self.state.output.critique else 0} chars")
#             logger.info(f"Retry count: {self.state.output.retry_count}")
#         logger.info("="*80)

#         return self.state.output

#     @listen("error")
#     def handle_error(self):
#         """Handle errors"""
#         logger.error("PlotBuilderWithCritiqueFlow: Error occurred")
#         return self.state.output and self.state.output.errors
