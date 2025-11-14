"""
Example: Pause and Resume StoryBuilder Flow

This demonstrates how to:
1. Start a flow with waits_at flag to pause at storyboard
2. Save the flow state
3. Resume the flow from the saved state

Usage:
    # Start with pause at storyboard
    python -m cinema.cmd.examples.flow_resume_example --pause-at storyboard
    
    # Resume from saved state
    python -m cinema.cmd.examples.flow_resume_example --continue <flow_id>
"""

import argparse
import asyncio
import logging

from dotenv import load_dotenv

from cinema.agents.bookwriter.crew import (
    BookWriter,
    ComicStripStoryBoarding,
    DetectivePlotBuilder,
    DetectivePlotBuilderSchema,
    PlotCritique,
    ScreenplayWriter,
    StripperInputSchema,
)
from cinema.agents.bookwriter.flow import StoryBuilder, StoryBuilderInput
from cinema.context import DirectorsContext
from cinema.registry import OpenAiHerd

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def start_flow_with_pause(pause_at: str = "storyboard"):
    """Start a new flow with pause at specified stage"""
    
    logger.info("=" * 80)
    logger.info(f"Starting StoryBuilder Flow with pause at: {pause_at}")
    logger.info("=" * 80)
    
    # Generate a unique flow ID (you can use detective ID here)
    import uuid
    flow_id = str(uuid.uuid4())[:8]
    
    # Create context
    ctx = DirectorsContext(
        llmstore=OpenAiHerd,
        debug=True
    )
    
    # Create crews
    plotbuilder = DetectivePlotBuilder(ctx=ctx)
    critique = PlotCritique(ctx=ctx)
    storyboard = ComicStripStoryBoarding(ctx=ctx)
    screenplay = ScreenplayWriter(ctx=ctx)
    booker = BookWriter(ctx=ctx)
    
    # Create initial state with waits_at flag
    initial_state = {
        "id": flow_id,
        "waits_at": {
            pause_at: True  # Will pause at this stage
        }
    }
    
    # Build flow
    flow = StoryBuilder.build(
        ctx=ctx,
        plotbuilder=plotbuilder,
        critique=critique,
        storyboard=storyboard,
        screenplay=screenplay,
        booker=booker,
        initial_state=initial_state,
        output_base_dir=f"output/detective_{flow_id}",
        flow_id=flow_id
    )
    
    # Prepare inputs (copied from detective_maker.py)
    from cinema.agents.bookwriter.flow import ScreenplayWriterSchema
    
    plot_builder_schema = DetectivePlotBuilderSchema(
        characters="Detective Morgan, James Butler (killer), Victor Ashford (victim)",
        relationships="Butler served Ashford for 30 years",
        killer="James Butler",
        victim="Victor Ashford",
        accomplices="Dr. Helen Price",
        witnesses="Margaret Ashford",
        betrayals="",
        examples="",
    )
    
    stripper_schema = StripperInputSchema(
        art_style="Print Comic Noir Style",
        examples=ComicStripStoryBoarding.load_examples(),
    )
    
    screenplay_schema = ScreenplayWriterSchema.model_construct(
        examples=ScreenplayWriter.load_examples(),
    )
    
    flow.state.input = StoryBuilderInput(
        plotbuilder=plot_builder_schema,
        stripper=stripper_schema,
        screenplay=screenplay_schema,
    )
    
    # Run flow
    logger.info(f"🚀 Starting flow with ID: {flow_id}")
    result = await flow.kickoff_async()
    
    logger.info("=" * 80)
    logger.info(f"Flow Result: {result}")
    logger.info(f"Flow ID: {flow_id}")
    logger.info(f"Halted at: {flow.state.halted_at}")
    logger.info("=" * 80)
    logger.info(f"To resume: python -m cinema.cmd.examples.flow_resume_example --continue {flow_id}")
    logger.info("=" * 80)
    
    return flow_id


async def resume_flow(flow_id: str):
    """Resume a halted flow"""
    
    logger.info("=" * 80)
    logger.info(f"Resuming StoryBuilder Flow: {flow_id}")
    logger.info("=" * 80)
    
    # Create context
    ctx = DirectorsContext(
        llmstore=OpenAiHerd,
        debug=True
    )
    
    # Create crews
    plotbuilder = DetectivePlotBuilder(ctx=ctx)
    critique = PlotCritique(ctx=ctx)
    storyboard = ComicStripStoryBoarding(ctx=ctx)
    screenplay = ScreenplayWriter(ctx=ctx)
    booker = BookWriter(ctx=ctx)
    
    # Resume from saved state
    flow = StoryBuilder.resume_from_halt(
        flow_id=flow_id,
        ctx=ctx,
        plotbuilder=plotbuilder,
        critique=critique,
        storyboard=storyboard,
        screenplay=screenplay,
        booker=booker,
        output_base_dir=f"output/detective_{flow_id}"
    )
    
    # Continue execution
    logger.info(f"▶️  Resuming flow from: {flow.state.current_state}")
    result = await flow.kickoff_async()
    
    logger.info("=" * 80)
    logger.info(f"Flow Result: {result}")
    logger.info("=" * 80)
    
    return result


async def main():
    parser = argparse.ArgumentParser(description="Pause and Resume StoryBuilder Flow")
    parser.add_argument("--pause-at", type=str, default="storyboard", 
                       help="Stage to pause at (default: storyboard)")
    parser.add_argument("--continue", dest="continue_id", type=str,
                       help="Flow ID to resume from")
    
    args = parser.parse_args()
    
    if args.continue_id:
        # Resume mode
        await resume_flow(args.continue_id)
    else:
        # Start mode with pause
        await start_flow_with_pause(pause_at=args.pause_at)


if __name__ == "__main__":
    asyncio.run(main())
