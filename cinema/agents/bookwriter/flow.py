from typing import Any, Literal, Optional

from crewai.flow.flow import Flow, listen, or_, start, router

from pydantic import BaseModel

from cinema.agents.bookwriter.crew import (
    ComicStripStoryBoarding,
    CritiqueSchema,
    DetectivePlotBuilder,
    DetectivePlotBuilderSchema,
    PlotCritique,
    StripperInputSchema
)

from cinema.context import DirectorsContext
from cinema.models.detective_output import DetectiveStoryOutput

import logging


logger = logging.getLogger(__name__)

class StoryBuilderOutput(BaseModel):
    storyline: Optional[str] = None
    critique: Optional[str] = None
    storystructure: Optional[DetectiveStoryOutput] = None
    retry_count: int = 0
    errors: list[str] = []  # Store error messages as strings

class StoryBuilderInput(BaseModel):
    plotbuilder: Optional[DetectivePlotBuilderSchema] = None
    stripper: Optional[StripperInputSchema] = None
    critiuqe: Optional[CritiqueSchema] = None

class StoryBuilderState(BaseModel):
    current_state: Literal[
        "start",
        "plan",
        "critique",
        "storyboard",
        "success",
        "error",
    ] = "start"

    input: Optional[StoryBuilderInput] = None
    output: Optional[StoryBuilderOutput] = None
    
    # Configuration flags
    skip_storyboard: bool = False  # If True, stop after critique passes


MAX_RETRIES = 3

class StoryBuilder(Flow[StoryBuilderState]):
    ctx: DirectorsContext

    plotbuilder: DetectivePlotBuilder
    critique: PlotCritique
    storyboard: ComicStripStoryBoarding
    
    # Cache crew instances to avoid re-initializing knowledge
    _plotbuilder_crew = None
    _critique_crew = None
    _storyboard_crew = None

    @classmethod
    def build(
        cls,
        ctx: DirectorsContext,
        plotbuilder: DetectivePlotBuilder,
        critique: PlotCritique,
        storyboard: ComicStripStoryBoarding,
        initial_state: dict | None = None,
    ):

        if not initial_state:
            initial_state = {}

        o = cls(**initial_state)
        o.ctx = ctx

        o.plotbuilder = plotbuilder
        o.critique = critique
        o.storyboard = storyboard
        
        return o

    def update_state(self, now_state: str):
        if self.state.current_state == now_state:
            return

        # should have validation on transition
        self.state.current_state = now_state  # type:ignore

    @start()
    def resume(self):
        logger.info("== "* 10)
        logger.info(self.state)

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

        logger.info(f"[Iteration {self.state.output.retry_count + 1}/{MAX_RETRIES}] Running DetectivePlotBuilder...")

        plot_inputs: dict[str, Any] = self.state.input.plotbuilder.model_dump()
        
        # Check if feedback exists from previous iteration
        if self.state.output.critique:
            logger.info(f"Incorporating feedback from previous critique")
            plot_inputs["feedback"] = self.state.output.critique

        # Reuse crew instance to avoid re-initializing knowledge
        if self._plotbuilder_crew is None:
            self._plotbuilder_crew = self.plotbuilder.crew()

        plot_result = await self._plotbuilder_crew.kickoff_async(inputs=plot_inputs)

        # Collect narrative structure
        narrative_text = DetectivePlotBuilder.collect(plot_result)
        self.state.output.storyline = narrative_text
        
        logger.info(f"✓ Storyline generated ({len(narrative_text) if narrative_text else 0} chars)")

    @listen(or_("critique", handle_storybuilding))
    async def handle_critique(self):
        assert self.state.input is not None, "InputNotFound"
        assert self.state.output is not None, "OutputNotFound"
        assert self.state.output.storyline is not None, "StorylineNotFound"
        assert self.state.input.plotbuilder is not None

        logger.info("Running PlotCritique...")

        inputs = CritiqueSchema(
            storyline=self.state.output.storyline
        )

        self.update_state("critique")

        # Reuse crew instance to avoid re-initializing knowledge
        if self._critique_crew is None:
            self._critique_crew = self.critique.crew()

        result = await self._critique_crew.kickoff_async(
            inputs=inputs.model_dump(),
        )

        critique_result: str = PlotCritique.collect(result)
        self.state.output.critique = critique_result
        
        logger.info(f"✓ Critique completed ({len(critique_result)} chars)")

        return

    @router(handle_critique)
    def eval_plotline(self):
        assert self.state.input is not None, "InputNotFound"
        assert self.state.output is not None, "OutputNotFound"
        assert self.state.input.plotbuilder is not None, "PlotSchemaNotFound"
        assert self.state.output.critique is not None, "FeedbackNotFound"

        critique_result = self.state.output.critique
        
        # Parse verdict from critique
        section = "## Final Binary Verdict"
        splits = critique_result.split(section, 1)
        
        verdict = "FAIL"
        if len(splits) >= 2:
            verdict_check = splits[1][:200].upper()
            if "- PASS" in verdict_check or "PASS" in verdict_check.split('\n')[0]:
                verdict = "PASS"
        
        logger.info(f"Evaluating critique verdict: {verdict}")

        if verdict == "PASS":
            logger.info("✓ Critique PASSED")
            # Check if we should skip storyboarding
            if self.state.skip_storyboard:
                logger.info("Skipping storyboard (skip_storyboard=True)")
                self.update_state("success")
            else:
                self.update_state("storyboard")

        elif self.state.output.retry_count > MAX_RETRIES - 1:  # because 0 indexed
            logger.warning(f"⚠ Max retries ({MAX_RETRIES}) reached")
            # Check if we should skip storyboarding
            if self.state.skip_storyboard:
                self.update_state("success")
            else:
                self.update_state("storyboard")

        else:
            logger.info(f"✗ Critique FAILED - retrying with feedback (attempt {self.state.output.retry_count + 1}/{MAX_RETRIES})")
            self.state.output.retry_count += 1
            # Feedback will be picked up in handle_storybuilding via output.critique
            self.update_state("plan")
        
        return self.state.current_state

    @listen("storyboard")
    async def handle_storyboarding(self):
        logger.info("Running ComicStripStoryBoarding crew...")
        
        assert self.state.input is not None
        assert self.state.input.stripper is not None
        assert self.state.output is not None

        stripper = self.state.input.stripper
        stripper.storyline = self.state.output.storyline

        # Reuse crew instance to avoid re-initializing knowledge
        if self._storyboard_crew is None:
            self._storyboard_crew = self.storyboard.crew()

        storyboard_inputs = stripper.model_dump()
        storyboard_result = await self._storyboard_crew.kickoff_async(
            inputs=storyboard_inputs
        )

        # Collect as DetectiveStoryOutput
        output = ComicStripStoryBoarding.collect(  # type: ignore[attr-defined]
            storyboard_result, DetectiveStoryOutput
        )

        if not isinstance(output, DetectiveStoryOutput):
            logger.error("Failed to generate detective story output")
            self.update_state("error")
            self.state.output.errors.append(
                "Failed to generate detective story output"
            )

            return

        self.state.output.storystructure = output
        logger.info(f"✓ Storyboard generated with {len(output.characters)} characters")
        self.update_state("success")

    @listen(handle_storyboarding)
    def handle_end(self):
        logger.info(f"end state {self.state.current_state}")
        if self.state.current_state == "error":
            return self.state.output and self.state.output.errors

        return "success"

    @listen("success")
    def handle_success(self):
        return self.state.output

    @listen("error")
    def handle_error(self):
        return self.state.output and self.state.output.errors





# ============================================================================
# PlotBuilderWithCritiqueFlow - Plot + Critique Only (No Storyboarding)
# ============================================================================

class PlotBuilderWithCritiqueState(BaseModel):
    """State for PlotBuilderWithCritiqueFlow - Plot + Critique only"""
    current_state: Literal[
        "start",
        "plan",
        "critique",
        "evaluate",
        "success",
        "error",
    ] = "start"
    
    # Input: Type-safe plot structure
    input: Optional[StoryBuilderInput] = None
    
    # Output: storyline + critique (no storystructure)
    output: Optional[StoryBuilderOutput] = None


class PlotBuilderWithCritiqueFlow(Flow[PlotBuilderWithCritiqueState]):
    """
    Flow for Plot + Critique only (no storyboarding).
    
    Flow: start → plan → critique → evaluate → success/error
    
    - Runs DetectivePlotBuilder to generate storyline
    - Runs PlotCritique to validate storyline
    - Loops back with feedback if critique fails
    - Terminates on PASS or MAX_RETRIES
    - Does NOT run storyboarding
    """
    
    ctx: DirectorsContext
    plotbuilder: DetectivePlotBuilder
    critique: PlotCritique
    
    # Cache crew instances to avoid re-initializing knowledge
    _plotbuilder_crew = None
    _critique_crew = None
    
    @classmethod
    def build(
        cls,
        ctx: DirectorsContext,
        plotbuilder: DetectivePlotBuilder,
        critique: PlotCritique,
        initial_state: dict | None = None,
    ):
        """Build a new flow instance"""
        if not initial_state:
            initial_state = {}
        
        o = cls(**initial_state)
        o.ctx = ctx
        o.plotbuilder = plotbuilder
        o.critique = critique
        
        return o
    
    def update_state(self, now_state: str):
        """Update state with validation"""
        if self.state.current_state == now_state:
            return
        
        # Validate state transition
        valid_states = ["start", "plan", "critique", "evaluate", "success", "error"]
        if now_state not in valid_states:
            raise ValueError(f"Invalid state: {now_state}")
        
        self.state.current_state = now_state  # type: ignore
    
    @start()
    def resume(self):
        """Entry point - initialize output if needed"""
        logger.info("="*40)
        logger.info("PlotBuilderWithCritiqueFlow: Starting")
        logger.info("="*40)
        
        if self.state.output is None:
            self.state.output = StoryBuilderOutput()
        
        return self.state.current_state
    
    @router(resume)
    def director(self):
        """Route from start to plan"""
        if self.state.current_state == "start":
            self.update_state("plan")
        
        logger.info(f"Routing to: {self.state.current_state}")
        return self.state.current_state
    
    @listen("plan")
    async def handle_plotbuilding(self):
        """Run DetectivePlotBuilder crew to generate storyline"""
        assert self.state.input is not None, "InputNotFound"
        assert self.state.input.plotbuilder is not None, "PlotSchemaNotFound"
        assert self.state.output is not None, "OutputNotFound"
        
        logger.info(f"[Iteration {self.state.output.retry_count + 1}/{MAX_RETRIES}] Running DetectivePlotBuilder...")
        
        # Convert to dict for kickoff_async
        plot_inputs: dict[str, Any] = dict(self.state.input.plotbuilder)
        
        # Check if feedback exists from previous iteration
        if self.state.output.critique:
            logger.info(f"Incorporating feedback from previous critique")
            plot_inputs["feedback"] = self.state.output.critique
        
        # Reuse crew instance to avoid re-initializing knowledge
        if self._plotbuilder_crew is None:
            self._plotbuilder_crew = self.plotbuilder.crew()
        
        # Run plotbuilder crew
        plot_result = await self._plotbuilder_crew.kickoff_async(
            inputs=plot_inputs
        )
        
        # Collect storyline
        narrative_text = DetectivePlotBuilder.collect(plot_result)
        self.state.output.storyline = narrative_text
        
        logger.info(f"✓ Storyline generated ({len(narrative_text) if narrative_text else 0} chars)")
    
    @listen(handle_plotbuilding)
    async def handle_critique(self):
        """Run PlotCritique crew to validate storyline"""
        assert self.state.output is not None, "OutputNotFound"
        assert self.state.output.storyline is not None, "StorylineNotFound"
        
        logger.info("Running PlotCritique...")
        
        self.update_state("critique")
        
        # Prepare critique input
        critique_input = CritiqueSchema(
            storyline=self.state.output.storyline
        )
        
        # Reuse crew instance to avoid re-initializing knowledge
        if self._critique_crew is None:
            self._critique_crew = self.critique.crew()
        
        # Run critique crew
        critique_inputs: dict[str, Any] = dict(critique_input)
        critique_result = await self._critique_crew.kickoff_async(
            inputs=critique_inputs
        )
        
        # Collect critique
        critique_text: str = PlotCritique.collect(critique_result)
        self.state.output.critique = critique_text
        
        logger.info(f"✓ Critique completed ({len(critique_text)} chars)")
    
    @router(handle_critique)
    def eval_critique(self):
        """
        Evaluate critique verdict and route accordingly.
        
        Routes to:
        - "success" if critique passes
        - "success" if max retries reached
        - "plan" to retry with feedback
        """
        assert self.state.input is not None, "InputNotFound"
        assert self.state.output is not None, "OutputNotFound"
        assert self.state.output.critique is not None, "CritiqueNotFound"
        
        self.update_state("evaluate")
        
        critique_text = self.state.output.critique
        section = "## Final Binary Verdict"
        
        splits = critique_text.split(section, 1)
        
        verdict = "FAIL"
        if len(splits) >= 2:
            verdict_check = splits[1][:200].upper()
            if "- PASS" in verdict_check or "PASS" in verdict_check.split('\n')[0]:
                verdict = "PASS"
        
        logger.info(f"Evaluating critique verdict: {verdict}")
        
        if verdict == "PASS":
            logger.info("✓ Critique PASSED - storyline approved")
            self.update_state("success")

        elif self.state.output.retry_count >= MAX_RETRIES - 1:
            logger.warning(f"⚠ Max retries ({MAX_RETRIES}) reached - accepting storyline")
            self.update_state("success")

        else:
            logger.info(f"✗ Critique FAILED - retrying with feedback")
            self.state.output.retry_count += 1
            # Feedback will be picked up in handle_plotbuilding via output.critique
            self.update_state("plan")
        
        return self.state.current_state
    
    @listen("success")
    def handle_success(self):
        """Return final output"""
        logger.info("="*40)
        logger.info("PlotBuilderWithCritiqueFlow: Complete")
        logger.info(f"Final retry count: {self.state.output.retry_count if self.state.output else 0}")
        logger.info("="*40)
        
        return self.state.output
    
    @listen("error")
    def handle_error(self):
        """Handle errors"""
        logger.error("PlotBuilderWithCritiqueFlow: Error occurred")
        return self.state.output and self.state.output.errors
