"""
Example usage of the movie generation pipeline with screenplay generation.
"""

import asyncio
import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from dotenv import load_dotenv

from cinema.agents.scriptwriter.crew import Enhancer, ScriptWriter, ScriptWriterSchema
from cinema.context import DirectorsContext
from cinema.pipeline import MovieMaker
from cinema.providers.shared import MediaLib
from cinema.registry import GeminiHerd, OpenAiHerd

# Load environment variables
load_dotenv()

# Setup logging with LOG_LEVEL from .env
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)
scripts: Optional[Dict[str, Any]] = None


async def main(which_script: str):
    """Example: Generate a movie from a script"""

    # Initialize MediaLib with optional reference images
    assert scripts is not None, "ScriptsNotLoaded"

    script = scripts[which_script]

    medialib = MediaLib.model_construct(
        image_urls=[script.get("images", [])],
        characters=[script.get("characters", [])],
    )

    # Initialize DirectorsContext
    ctx = DirectorsContext(
        llmstore=GeminiHerd,
        debug=True,
    )

    ectx = DirectorsContext(
        llmstore=OpenAiHerd,
        debug=True,
    )

    # Initialize the agents with proper context
    writer = ScriptWriter(ctx, medialib, outfile="script_llm.md")
    enhancer = Enhancer(ectx, outfile="screenplay_llm.json")

    workflow_config = {
        "selection_mode": "llm_intelligent",
        # or "config_default", "always_interpolation"
        "use_llm_for_workflow_decision": True,
        "log_workflow_decisions": True,
        "export_metrics": True,
        "metrics_output_path": "output/workflow_metrics_llm.json",
    }

    # Create the movie maker
    maker = MovieMaker(
        writer=writer,
        enhancer=enhancer,
        db_path="./cinema_jobs.db",
        workflow_config=workflow_config,
    )

    # Your script input
    script_input = ScriptWriterSchema.model_construct(
        script=script["script"],
        characters=medialib.characters,
        images=medialib.image_urls,
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
        # Or specify movie_id="my_movie_v1" for resumability
        base_dir="./output",
    )

    print(f"\n✓ Movie generated! {state.movie_id}")
    print(f"Final video: {state.get_final_video_path()}")
    print(f"All files in: {state.base_dir}")


async def check_status(id: str):
    """Example: Check status of a movie generation"""

    writer = ScriptWriter()
    enhancer = Enhancer()
    maker = MovieMaker(writer, enhancer)

    # Get status
    status = maker.get_status(id)

    print("Movie Status:")
    print(f"  Total jobs: {status['total']}")
    print(f"  Completed: {status['completed']}")
    print(f"  Failed: {status['failed']}")
    print(f"  Pending: {status['pending']}")
    print(f"  Progress: {status['progress']:.1f}%")


if __name__ == "__main__":
    # Run the main example
    with open(Path(__file__).parent / "scripts.yaml", "r+") as f:
        scripts = yaml.safe_load(f)

    script_key = "travel_vlog"
    asyncio.run(main(script_key))

    # Or resume an existing one
    # asyncio.run(resume_example())

    # Or check status
    # asyncio.run(check_status())
