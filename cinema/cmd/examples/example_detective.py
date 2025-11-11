#!/usr/bin/env python3
"""
Example: Detective Comic Strip Generation

This example shows how to generate a detective comic strip using the DetectiveMaker pipeline.

Usage:
    # Validate storyline only (no image generation)
    python cinema/cmd/examples/example_detective.py --validate-only
    
    # Generate full comic with images
    python cinema/cmd/examples/example_detective.py
    
    # Resume from existing state
    python cinema/cmd/examples/example_detective.py --resume detective_abc123
"""

import asyncio
import argparse
from cinema.agents.bookwriter.models import Character, PlotConstraints
from cinema.agents.bookwriter.crew import DetectivePlotBuilder, ComicStripStoryBoarding, PlotBuilderWithCritique, PlotCritique
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

    plotcritique = PlotBuilderWithCritique(
        ctx,
        plotbuilder=plotbuilder,
        critique=critique,
    )

    storyboard = ComicStripStoryBoarding(ctx)

    # Initialize DetectiveMaker
    maker = DetectiveMaker(
        plotbuilder=plotcritique,
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
