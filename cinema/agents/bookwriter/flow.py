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
    errors: list[Exception] = []

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


MAX_RETRIES = 3

class StoryBuilder(Flow[StoryBuilderState]):
    ctx: DirectorsContext

    plotbuilder: DetectivePlotBuilder
    critique: PlotCritique
    storyboard: ComicStripStoryBoarding

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

        plot_inputs: dict[str, Any] = dict(self.state.input.plotbuilder)

        logger.info(f"Planning with feedback {plot_inputs}")

        plot_result = await self.plotbuilder.crew().kickoff_async(inputs=plot_inputs)

        # Collect narrative structure
        narrative_text = DetectivePlotBuilder.collect(plot_result)
        self.state.output.storyline = narrative_text

    @listen(or_("critique", handle_storybuilding))
    async def handle_critique(self):
        assert self.state.input is not None, "InputNotFound"
        assert self.state.output is not None, "OutputNotFound"
        assert self.state.output.storyline is not None, "StorylineNotFound"
        assert self.state.input.plotbuilder is not None

        inputs = CritiqueSchema(
            storyline=self.state.output.storyline
        )

        self.update_state("critique")

        critique_inputs: dict[str, Any] = dict(inputs)
        result = await self.critique.crew().kickoff_async(
            inputs=critique_inputs,
        )

        critique_result: str = PlotCritique.collect(result)
        self.state.output.critique = critique_result

        return

    @router(handle_critique)
    def eval_plotline(self):
        assert self.state.input is not None, "InputNotFound"
        assert self.state.output is not None, "OutputNotFound"
        assert self.state.input.plotbuilder is not None, "PlotSchemaNotFound"
        assert self.state.output.critique is not None, "FeedbackNotFound"

        critique_result = self.state.output.critique
        end_of_result = (critique_result[-100:]).lower()

        logging.info(f"evaluating {end_of_result}")

        if end_of_result.endswith("none") or "none" in end_of_result:
            self.update_state("storyboard")

        elif self.state.output.retry_count > MAX_RETRIES - 1:  # because 0 indexed
            self.update_state("storyboard")

        else:
            logger.info("feedback created issues, circling back")
            self.state.output.retry_count += 1
            self.state.input.plotbuilder["feedback"] = critique_result
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

        storyboard_inputs = stripper.model_dump()
        storyboard_result = await self.storyboard.crew().kickoff_async(
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
                ValueError("Failed to generate detective story output"),
            )

            return

        self.state.output.storystructure = output
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
