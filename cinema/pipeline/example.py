"""
Example usage of the movie generation pipeline with screenplay generation.
"""

import asyncio
import logging
import os

from dotenv import load_dotenv

from cinema.agents.scriptwriter.crew import Enhancer, ScriptWriter, ScriptWriterSchema
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


async def main():
    """Example: Generate a movie from a script"""

    # Initialize MediaLib with optional reference images
    medialib = MediaLib(
        image_urls=[
            # Add reference images here if needed
        ]
    )

    # Initialize DirectorsContext
    ctx = DirectorsContext(
        llmstore=GeminiHerd,
        debug=True,
    )

    # Initialize the agents with proper context
    writer = ScriptWriter(ctx, medialib)
    enhancer = Enhancer(ctx)

    # Create the movie maker
    maker = MovieMaker(
        writer=writer,
        enhancer=enhancer,
        db_path="./cinema_jobs.db",
    )

    # Your script input
    script_input = ScriptWriterSchema(
        script="""
        A 15-second commercial for a productivity app.

        Scene 1: A stressed professional at a messy desk, overwhelmed by tasks.
        Scene 2: They discover the app on their phone.
        Scene 3: Their workspace transforms - organized, calm, productive.
        Scene 4: Close-up of the app logo with tagline: "Work smarter, not harder."
        """,
        characters=[],
        images=medialib.images(),
        examples=ScriptWriter.load_examples(),
    )

    # Generate the movie
    # This will:
    # 1. Generate screenplay
    # 2. Generate character references
    # 3. Generate keyframe images
    # 4. Generate videos
    # 5. Apply post-production and stitch
    state = await maker.generate(
        script_input=script_input,
        # movie_id auto-generated (8-char UUID) for fresh generation each time
        # Or specify movie_id="my_movie_v1" for resumability
        base_dir="./output",
    )

    print("\n✓ Movie generated!")
    print(f"Final video: {state.get_final_video_path()}")
    print(f"All files in: {state.base_dir}")


async def resume_example():
    """Example: Resume a previously started movie"""

    writer = ScriptWriter()
    enhancer = Enhancer()
    maker = MovieMaker(writer, enhancer)

    # Resume from a specific movie ID
    state = await maker.resume(
        movie_id="productivity_app_v1",
        base_dir="./output",
    )

    print(f"✓ Resumed and completed! {state}")


async def check_status():
    """Example: Check status of a movie generation"""

    writer = ScriptWriter()
    enhancer = Enhancer()
    maker = MovieMaker(writer, enhancer)

    # Get status
    status = maker.get_status("productivity_app_v1")

    print("Movie Status:")
    print(f"  Total jobs: {status['total']}")
    print(f"  Completed: {status['completed']}")
    print(f"  Failed: {status['failed']}")
    print(f"  Pending: {status['pending']}")
    print(f"  Progress: {status['progress']:.1f}%")


if __name__ == "__main__":
    # Run the main example
    asyncio.run(main())

    # Or resume an existing one
    # asyncio.run(resume_example())

    # Or check status
    # asyncio.run(check_status())
