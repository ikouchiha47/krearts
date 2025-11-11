"""
Resume a movie generation from failed or incomplete state.
"""

import asyncio
import logging
import os

from dotenv import load_dotenv

from cinema.agents.scriptwriter.crew import Enhancer, ScriptWriter
from cinema.context import DirectorsContext
from cinema.pipeline import MovieMaker
from cinema.providers.shared import MediaLib
from cinema.registry import GeminiHerd

# Load environment variables
load_dotenv()

# Setup logging with LOG_LEVEL from .env
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


async def resume_movie(movie_id: str):
    """Resume a movie generation from existing state"""

    logger.info(f"Resuming movie: {movie_id}")

    # Initialize context and agents
    medialib = MediaLib(image_urls=[])
    ctx = DirectorsContext(llmstore=GeminiHerd, debug=True)
    writer = ScriptWriter(ctx, medialib)
    enhancer = Enhancer(ctx)

    # Create movie maker
    maker = MovieMaker(
        writer=writer,
        enhancer=enhancer,
        db_path="./cinema_jobs.db",
    )

    # Check current status
    status = maker.get_status(movie_id)
    logger.info(f"Current status:")
    logger.info(f"  Total: {status['total']} jobs")
    logger.info(f"  Completed: {status['completed']}")
    logger.info(f"  Failed: {status['failed']}")
    logger.info(f"  Pending: {status['pending']}")
    logger.info(f"  Progress: {status['progress']:.1f}%")

    if status["failed"] == 0 and status["pending"] == 0:
        logger.info("✓ All jobs complete! Nothing to resume.")
        return

    # Resume generation
    logger.info("\nResuming generation...")
    state = await maker.resume(movie_id=movie_id, base_dir="./output")

    # Final status
    final_status = maker.get_status(movie_id)
    logger.info(f"\n{'='*60}")
    logger.info(f"✓ Resume complete!")
    logger.info(f"Final status:")
    logger.info(f"  Completed: {final_status['completed']}/{final_status['total']}")
    logger.info(f"  Failed: {final_status['failed']}")
    logger.info(f"  Progress: {final_status['progress']:.1f}%")
    logger.info(f"{'='*60}")

    if final_status["failed"] > 0:
        logger.warning(
            f"\n⚠️  {final_status['failed']} jobs still failed. Check errors above."
        )


if __name__ == "__main__":
    # Specify the movie_id to resume
    MOVIE_ID = "d40db751"  # Change this to your movie ID

    asyncio.run(resume_movie(MOVIE_ID))
