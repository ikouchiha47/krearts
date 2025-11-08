"""
Example usage of the movie generation pipeline with pre-generated screenplay.
Demonstrates MovieMaker's dual-mode capability (with/without screenplay generation).
"""

import asyncio
import json
import logging
import os
from pathlib import Path

from dotenv import load_dotenv

from cinema.pipeline import MovieMaker

# Load environment variables
load_dotenv()

# Setup logging with LOG_LEVEL from .env
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


async def generate_from_screenplay_json():
    """
    Generate a movie from pre-generated screenplay JSON using MovieMaker.
    This demonstrates the dual-mode capability (with/without screenplay generation).
    """

    # Load the screenplay JSON
    screenplay_path = Path("gemini_screenplay.md")

    if not screenplay_path.exists():
        logger.error(f"Screenplay file not found: {screenplay_path}")
        return

    logger.info(f"Loading screenplay from {screenplay_path}")
    screenplay_json = json.loads(screenplay_path.read_text())

    # Log what we're about to generate
    logger.info(f"Title: {screenplay_json.get('title')}")
    logger.info(f"Scenes: {len(screenplay_json.get('scenes', []))}")
    logger.info(f"Characters: {len(screenplay_json.get('character_description', []))}")

    # Initialize MovieMaker (writer/enhancer not needed for screenplay JSON mode)
    maker = MovieMaker(db_path="./cinema_jobs.db")

    # Generate movie from screenplay JSON (skips screenplay generation)
    state = await maker.generate_from_screenplay(
        screenplay_json=screenplay_json,
        movie_id="vibeflow_headphones",
        base_dir="./output",
    )

    # Final summary
    logger.info(f"\nOutput directory: {state.base_dir}")
    logger.info(f"Final video: {state.get_final_video_path()}")


if __name__ == "__main__":
    asyncio.run(generate_from_screenplay_json())
