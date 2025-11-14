#!/usr/bin/env python3
"""
Example: Detective Comic Strip Generation with NEW MODULAR ARCHITECTURE

This example demonstrates the new modular architecture with SOLID principles:
- Character reference generation for consistent character appearance
- Panel composition using multi-image "ingredients to image" feature
- Modular generators that can be swapped or mocked for testing

Pipeline stages:
1. Plot structure generation from constraints
2. Narrative generation with critique loop (StoryBuilder flow)
3. Character reference generation (NEW - for consistency)
4. Panel generation with character composition (NEW - multi-image)

Features:
- Character references ensure consistent appearance across all panels
- Professional comic book quality with character consistency
- Resumable pipeline with state tracking
- Modular architecture following SOLID principles

Usage:
    # Validate storyline only (no image generation)
    python cinema/cmd/examples/example_detective.py --validate-only

    # Generate full comic with character references and composition
    python cinema/cmd/examples/example_detective.py

    # Resume from existing state
    python cinema/cmd/examples/example_detective.py --resume detective_abc123

    # Custom art style
    python cinema/cmd/examples/example_detective.py --style "Cyberpunk Comic Style"

    # Adjust concurrency for rate limiting
    python cinema/cmd/examples/example_detective.py --max-concurrent 1

Output structure:
    output/detective_abc123/
        ├── characters/          # NEW - Character reference images
        │   ├── Detective_Morgan_reference.png
        │   ├── James_Butler_reference.png
        │   └── ...
        ├── images/              # Comic panels with consistent characters
        │   ├── Detective_Morgan_00.png
        │   ├── Detective_Morgan_01.png
        │   └── ...
        ├── storyline_analysis.txt
        └── detective_abc123_state.json
"""

import argparse
import asyncio
import logging
import os

from crewai.memory.external.external_memory import ExternalMemory
from dotenv import load_dotenv

from cinema.agents.bookwriter.crew import (
    BookWriter,
    ComicStripStoryBoarding,
    DetectivePlotBuilder,
    PlotCritique,
    ScreenplayWriter,
)
from cinema.agents.bookwriter.flow import StoryBuilder
from cinema.agents.bookwriter.models import Character, PlotConstraints
from cinema.context import DirectorsContext
from cinema.pipeline.detective_maker import DetectiveMaker
from cinema.pipeline.shared import (
    CharacterReferenceGenerator,
    ComicCharacterTransformer,
    ComicPanelTransformer,
    PanelComposer,
    SimpleImageGenerator,
)
from cinema.providers.gemini import GeminiMediaGen
from cinema.registry import GeminiHerd, OpenAiHerd
from cinema.utils.rate_limiter import RateLimiterManager

# Load environment variables


load_dotenv()

# Setup logging with LOG_LEVEL from .env
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=logging.DEBUG,#getattr(logging, log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


async def main():
    parser = argparse.ArgumentParser(description="Generate detective comic strip")
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Only validate storyline, don't generate images",
    )
    parser.add_argument("--resume", type=str, help="Resume from existing movie_id")
    parser.add_argument(
        "--style",
        type=str,
        default="Gritty, High Contrast Noir Comic Book Style, Inked images, with haltones",
        help="Art style for comic",
    )
    parser.add_argument(
        "--use-storybuilder",
        action="store_true",
        help="Use full StoryBuilder flow (plot + critique + screenplay + storyboard in one flow)",
    )
    parser.add_argument(
        "--max-concurrent",
        type=int,
        default=3,
        help="Maximum concurrent image generation requests (default: 3)",
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
        # llmstore=GeminiHerd,
        llmstore=OpenAiHerd,
        debug=True,
    )

    categories = [
        {
            "narrative_structures_linear": "Documents different linear narrative storytelling structures",
        },
        {
            "narrative_structures_nonlinear": "Documents different non-linear narrative storytelling structures",
        },
        {
            "art_styles": "Documents various art style used for storytelling, colors, compositions, art styles, print books, combinations"
        },
        {
            "storywriting_detective": "Documents principles and narrative techniques for writing detective style comics"
        },
        {
            "characters": "All list of characters and their personalities",
        },
    ]

    # external_memory = ExternalMemory(
    #     embedder_config={
    #         "provider": "mem0",
    #         "custom_categories": categories,
    #         "config": {
    #             "user_id": "john",
    #             "local_mem0_config": {
    #                 "vector_store": {
    #                     "provider": "qdrant",
    #                     "config": {"host": "localhost", "port": 6333}
    #                 },
    #                 "llm": {
    #                     "provider": "openai",
    #                     "config": {"model": "gpt-4.1"}
    #                 },
    #                 "embedder": {
    #                     "provider": "openai",
    #                     "config": {"model": "text-embedding-3-small"}
    #                 }
    #             },
    #             "infer": True # Optional defaults to True
    #         },
    #     }
    # )
    external_memory = None
    # Initialize crews
    plotbuilder = DetectivePlotBuilder(ctx, external_memory=external_memory)
    critique = PlotCritique(ctx, external_memory=external_memory)
    storyboard = ComicStripStoryBoarding(ctx, external_memory=external_memory)
    screenplay = ScreenplayWriter(ctx, external_memory=external_memory)
    booker = BookWriter(ctx, external_memory=external_memory)

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
        booker=booker,
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

    # NEW: Initialize modular generators with transformers (Strategy Pattern)
    print("\n🎨 Initializing modular image generators with transformers...")

    rate_limiter = RateLimiterManager()
    gemini = GeminiMediaGen(rate_limiter=rate_limiter)

    # Create transformers (Strategy Pattern - domain-specific prompt generation)
    character_transformer = ComicCharacterTransformer(art_style=args.style)
    panel_transformer = ComicPanelTransformer(art_style=args.style)

    print(f"   ✓ ComicCharacterTransformer (style: {args.style})")
    print(f"   ✓ ComicPanelTransformer (style: {args.style})")

    character_generator = CharacterReferenceGenerator(
        image_generator=gemini,
        transformer=character_transformer,
        rate_limiter=rate_limiter,
    )

    panel_composer = PanelComposer(
        composer=gemini,
        transformer=panel_transformer,
        rate_limiter=rate_limiter,
    )

    simple_image_generator = SimpleImageGenerator(
        image_generator=gemini,
        rate_limiter=rate_limiter,
    )

    print("   ✓ CharacterReferenceGenerator (with transformer)")
    print("   ✓ PanelComposer (with transformer)")
    print("   ✓ SimpleImageGenerator (fallback)")

    # Initialize DetectiveMaker with new modular architecture
    print("\n🏗️  Initializing DetectiveMaker pipeline...")
    maker = DetectiveMaker(
        character_generator=character_generator,
        panel_composer=panel_composer,
        simple_image_generator=simple_image_generator,
        # Configuration
        db_path="./cinema_jobs.db",
        art_style=args.style,
        validate_only=args.validate_only,
        max_concurrent_images=args.max_concurrent,
        # [DEPRECATED - REMOVABLE] Legacy support for backward compatibility
        plotbuilder=flow,
        storyboard=storyboard,
    )

    if args.resume:
        # Resume existing generation
        print(f"\n📖 Resuming detective comic: {args.resume}")
        state = await maker.resume(args.resume)
    else:
        # Generate new comic
        print("\n📖 Generating new detective comic")
        print("   Architecture: NEW MODULAR (SOLID principles)")
        print("   Flow: StoryBuilder (full pipeline)")
        print(f"   Style: {args.style}")
        print("   Character refs: Yes (for consistency)")
        print(f"   Validate only: {args.validate_only}")
        print(f"   Max concurrent: {args.max_concurrent}")

        state = await maker.generate(
            constraints=constraints,
            characters=characters,
            base_dir="./output",
        )

    # Show results
    print("\n" + "=" * 70)
    print("✓ Generation complete!")
    print("=" * 70)
    print(f"\n📁 Output directory: ./output/{state.movie_id}")

    if not args.validate_only:
        from pathlib import Path

        char_dir = Path(f"./output/{state.movie_id}/characters")
        if char_dir.exists():
            char_refs = list(char_dir.glob("*.png"))
            print(f"   Character references: {len(char_refs)} files")

        img_dir = Path(f"./output/{state.movie_id}/images")
        if img_dir.exists():
            panels = list(img_dir.glob("*.png"))
            print(f"   Comic panels: {len(panels)} files")

    print(f"\n📊 Pipeline state: ./output/{state.movie_id}/{state.movie_id}_state.json")
    print("\n✨ Done!")
    print(f"   Movie ID: {state.movie_id}")
    print(f"   Output: {state.base_dir}")

    if args.validate_only:
        print(f"\n⚠️  VALIDATION MODE - No images generated")
        print(
            f"   Review the storyline and run without --validate-only to generate images"
        )


if __name__ == "__main__":
    asyncio.run(main())
