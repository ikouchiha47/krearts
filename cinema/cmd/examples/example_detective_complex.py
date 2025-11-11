#!/usr/bin/env python3
"""
Example: Complex Detective Story with Multiple Deaths and Plot Twists

This example demonstrates advanced plot features:
- Multiple murders (primary victim + witness elimination)
- Red herrings (planted evidence)
- Plot twists (hidden identity reveal)
- False confessions
- Double-crosses within alliances

Usage:
    # Validate storyline only
    python cinema/cmd/examples/example_detective_complex.py --validate-only
    
    # Generate full comic
    python cinema/cmd/examples/example_detective_complex.py
"""

import asyncio
import argparse
from cinema.agents.bookwriter.models import Character, PlotConstraints
from cinema.agents.bookwriter.crew import DetectivePlotBuilder, ComicStripStoryBoarding
from cinema.context import DirectorsContext
from cinema.pipeline.detective_maker import DetectiveMaker
from cinema.registry import GeminiHerd


async def main():
    parser = argparse.ArgumentParser(
        description="Generate complex detective comic with multiple deaths and twists"
    )
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
        default="Dark Noir Comic Book Style",
        help="Art style for comic",
    )
    args = parser.parse_args()

    # Define characters - more complex cast
    characters = [
        Character("Detective Sarah Chen", "detective"),
        Character("Marcus Blackwood", "victim"),  # Primary victim - wealthy businessman
        Character("Elena Volkov", "killer"),  # The actual killer - business rival
        Character("Thomas Reed", "accomplice", faction="conspirators"),  # Elena's partner
        Character("Dr. James Morrison", "witness"),  # Witness who gets eliminated
        Character("Catherine Blackwood", "wife", faction="family"),  # Framed suspect
        Character("Richard Sterling", "lawyer", faction="family"),  # Red herring
    ]

    # Complex plot with multiple deaths and twists
    constraints = PlotConstraints(
        # Primary murder
        killer="Elena Volkov",
        victim="Marcus Blackwood",
        
        # Accomplice helps with the murder
        accomplices=["Thomas Reed"],
        
        # Frame the wife
        framed_suspect="Catherine Blackwood",
        
        # Witness sees something suspicious
        witnesses=[
            ("Dr. James Morrison", "saw Elena leaving the crime scene"),
        ],
        
        # Alliance between killer and accomplice
        alliances=[
            ("Elena Volkov", "Thomas Reed"),
        ],
        
        # The twist: Thomas double-crosses Elena by eliminating the witness
        # This creates a second murder that complicates the investigation
        betrayals=[
            ("Thomas Reed", "Dr. James Morrison"),  # Kills witness to protect conspiracy
        ],
        
        # Winners and losers
        winners=[],  # Detective solves it - no one wins
        losers=["Elena Volkov", "Thomas Reed", "Catherine Blackwood"],
    )

    # Initialize DirectorsContext
    ctx = DirectorsContext(
        llmstore=GeminiHerd,
        debug=True,
    )

    # Initialize crews
    plotbuilder = DetectivePlotBuilder(ctx)
    storyboard = ComicStripStoryBoarding(ctx)

    # Initialize DetectiveMaker
    maker = DetectiveMaker(
        plotbuilder=plotbuilder,
        storyboard=storyboard,
        db_path="./cinema_jobs.db",
        art_style=args.style,
        validate_only=args.validate_only,
    )

    if args.resume:
        print(f"\n📖 Resuming complex detective comic: {args.resume}")
        state = await maker.resume(args.resume)
    else:
        print(f"\n📖 Generating complex detective comic")
        print(f"   Style: {args.style}")
        print(f"   Plot: Multiple deaths with double-cross")
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
        print(f"\n📊 Plot Summary:")
        print(f"   - Primary murder: Elena kills Marcus")
        print(f"   - Witness elimination: Thomas kills Dr. Morrison (double-cross)")
        print(f"   - Framed: Catherine Blackwood")
        print(f"   - Red herring: Richard Sterling (lawyer with motive)")


if __name__ == "__main__":
    asyncio.run(main())
