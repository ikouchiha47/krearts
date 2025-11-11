#!/usr/bin/env python3
"""
Example: Detective Comic Strip Generation

This example shows how to generate a detective comic strip using the DetectiveMaker pipeline
with Flow-based implementations for controllable critique loop.

Two flow options are available:
1. PlotBuilderWithCritiqueFlow (default): Plot + critique, then separate storyboard
   - Better control with validation checkpoint
   - Can use --validate-only to review storyline before generating images
   
2. StoryBuilder (--use-storybuilder): Full pipeline in one flow
   - Plot + critique + screenplay + storyboard all in one
   - Single state machine, no intermediate checkpoints

Usage:
    # Validate storyline only (no image generation) - default flow
    python cinema/cmd/examples/example_detective.py --validate-only
    
    # Generate full comic with images - default flow
    python cinema/cmd/examples/example_detective.py
    
    # Use full StoryBuilder flow
    python cinema/cmd/examples/example_detective.py --use-storybuilder
    
    # Resume from existing state
    python cinema/cmd/examples/example_detective.py --resume detective_abc123
    
    # Custom art style
    python cinema/cmd/examples/example_detective.py --style "Cyberpunk Comic Style"
"""

import asyncio
import argparse
from cinema.agents.bookwriter.models import Character, PlotConstraints
from cinema.agents.bookwriter.crew import DetectivePlotBuilder, ComicStripStoryBoarding, PlotCritique, ScreenplayWriter
from cinema.agents.bookwriter.flow import PlotBuilderWithCritiqueFlow, StoryBuilder
from cinema.context import DirectorsContext
from cinema.pipeline.detective_maker import DetectiveMaker
from cinema.registry import GeminiHerd


async def main():
    parser = argparse.ArgumentParser(description="Generate detective comic strip")
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Only validate storyline, don't generate images",
    )
    parser.add_argument(
        "--resume", type=str, help="Resume from existing movie_id"
    )
    parser.add_argument(
        "--style",
        type=str,
        default="Noir Comic Book Style",
        help="Art style for comic",
    )
    parser.add_argument(
        "--use-storybuilder",
        action="store_true",
        help="Use full StoryBuilder flow (plot + critique + screenplay + storyboard in one flow)",
    )
    args = parser.parse_args()

    # Define characters
    characters = [
        Character("Detective Morgan", "detective"),
        Character("Victor Ashford", "victim"),
        Character("James Butler", "butler", faction="servants"),
        Character("Margaret Ashford", "wife", faction="family"),
        Character("Dr. Helen Price", "doctor"),
    ]

    # Define plot constraints
    constraints = PlotConstraints(
        killer="James Butler",
        victim="Victor Ashford",
        accomplices=[],
        framed_suspect="Margaret Ashford",
        witnesses=[("Dr. Helen Price", "suspicious activity")],
        alliances=[("James Butler", "Dr. Helen Price")],
        winners=["James Butler"],
        losers=["Margaret Ashford"],
        betrayals=[],
    )

    # Initialize DirectorsContext
    ctx = DirectorsContext(
        llmstore=GeminiHerd,
        debug=True,
    )

    # Initialize crews
    plotbuilder = DetectivePlotBuilder(ctx)
    critique = PlotCritique(ctx)
    storyboard = ComicStripStoryBoarding(ctx)
    screenplay = ScreenplayWriter(ctx)

    # Choose between StoryBuilder (full pipeline) or PlotBuilderWithCritiqueFlow (plot + critique only)
    # if args.use_storybuilder:
        # Use full StoryBuilder flow (plot + critique + screenplay + storyboard in one flow)
    print("Using StoryBuilder (full pipeline flow)")
    flow = StoryBuilder.build(
        ctx=ctx,
        plotbuilder=plotbuilder,
        critique=critique,
        screenplay=screenplay,
        storyboard=storyboard,
    )
    # else:
    #     # Use PlotBuilderWithCritiqueFlow (plot + critique only, then separate storyboard)
    #     # This provides better control with validation checkpoint
    #     print("Using PlotBuilderWithCritiqueFlow (plot + critique, then separate storyboard)")
    #     flow = PlotBuilderWithCritiqueFlow.build(
    #         ctx=ctx,
    #         plotbuilder=plotbuilder,
    #         critique=critique,
    #         screenplay=screenplay,
    #     )

    # Initialize DetectiveMaker with Flow-based implementation
    maker = DetectiveMaker(
        plotbuilder=flow,
        storyboard=storyboard,
        db_path="./cinema_jobs.db",
        art_style=args.style,
        validate_only=args.validate_only,
    )

    if args.resume:
        # Resume existing generation
        print(f"\n📖 Resuming detective comic: {args.resume}")
        state = await maker.resume(args.resume)
    else:
        # Generate new comic
        print(f"\n📖 Generating new detective comic")
        print(f"   Flow: {'StoryBuilder' if args.use_storybuilder else 'PlotBuilderWithCritiqueFlow'}")
        print(f"   Style: {args.style}")
        print(f"   Validate only: {args.validate_only}")
        
        state = await maker.generate(
            constraints=constraints,
            characters=characters,
            base_dir="./output",
        )

    # Show results
    print(f"\n✓ Generation complete!")
    print(f"   Movie ID: {state.movie_id}")
    print(f"   Output: {state.base_dir}")
    
    if args.validate_only:
        print(f"\n⚠️  VALIDATION MODE - No images generated")
        print(f"   Review the storyline and run without --validate-only to generate images")


if __name__ == "__main__":
    asyncio.run(main())
