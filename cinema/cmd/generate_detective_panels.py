#!/usr/bin/env python3
"""
Generate comic panels from detective story output using JobTracker pipeline

Usage:
    python cinema/cmd/generate_detective_panels.py detective_output.json --movie-id detective_001
    python cinema/cmd/generate_detective_panels.py detective_output.json --movie-id detective_001 --style "Print Comics + Noir"
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path

from cinema.models.detective_output import (
    DetectiveStoryOutput,
    create_panel_jobs_from_detective_output,
)
from cinema.pipeline.job_tracker import JobTracker
from cinema.pipeline.state import JobStatus
from cinema.providers.gemini import GeminiMediaGen


async def process_panel_jobs(
    jobs: list,
    movie_id: str,
    output_dir: str,
    tracker: JobTracker,
    media_gen: GeminiMediaGen,
):
    """Process panel generation jobs using GeminiMediaGen"""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    for job in jobs:
        print(f"\n📸 Processing: {job.id}")
        print(f"   Character: {job.metadata['character_name']}")
        print(f"   Action: {job.metadata['action']}")
        print(f"   Shot: {job.metadata['shot_type']}")

        try:
            # Update status to in progress
            tracker.update_job_status(job.id, JobStatus.IN_PROGRESS)

            # Generate image using GeminiMediaGen
            prompt = job.metadata["prompt"]
            response = await media_gen.generate_content(prompt)

            # Save image
            filename = f"{job.metadata['character_name'].replace(' ', '_')}_{job.metadata['action_index']:02d}_{job.metadata['timestamp'].replace(' ', '_').replace(':', '-')}.png"
            output_file = str(output_path / filename)

            media_gen.render_image(output_file, response)

            # Update job as completed
            tracker.update_job_status(
                job.id, JobStatus.COMPLETED, output_path=output_file
            )

            print(f"   ✓ Saved to: {output_file}")

        except Exception as e:
            print(f"   ✗ Error: {e}")
            tracker.update_job_status(job.id, JobStatus.FAILED, error=str(e))


async def main_async(args):
    # Load detective output
    input_path = Path(args.input_json)
    if not input_path.exists():
        print(f"Error: File not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    print(f"\n{'='*80}")
    print(f"Detective Panel Generator (JobTracker Pipeline)")
    print(f"{'='*80}")
    print(f"Input: {input_path}")
    print(f"Movie ID: {args.movie_id}")
    print(f"Style: {args.style}")
    print(f"Output: {args.output}")
    print(f"{'='*80}\n")

    # Parse JSON
    with open(input_path, "r") as f:
        data = json.load(f)

    detective_output = DetectiveStoryOutput.model_validate(data)

    print(f"Story: {detective_output.storyline[:100]}...")
    print(f"Characters: {len(detective_output.characters)}")
    print(f"Narrative Structure: {detective_output.narrative_structure}")

    # Create jobs
    print(f"\n📋 Creating panel generation jobs...")
    jobs = create_panel_jobs_from_detective_output(
        detective_output, movie_id=args.movie_id, art_style=args.style
    )

    print(f"Total panels to generate: {len(jobs)}\n")

    # Initialize tracker and media gen
    tracker = JobTracker(db_path=args.db_path)
    media_gen = GeminiMediaGen()

    # Save jobs to tracker
    for job in jobs:
        tracker.save_job(job, movie_id=args.movie_id)

    print(f"✓ Jobs saved to database: {args.db_path}\n")

    # Process jobs
    await process_panel_jobs(jobs, args.movie_id, args.output, tracker, media_gen)

    # Show progress
    progress = tracker.get_progress(args.movie_id)

    print(f"\n{'='*80}")
    print(f"✓ PIPELINE COMPLETE")
    print(f"{'='*80}")
    print(f"Total: {progress['total']}")
    print(f"Completed: {progress['completed']}")
    print(f"Failed: {progress['failed']}")
    print(f"Progress: {progress['progress']:.1f}%")
    print(f"Output: {args.output}")
    print(f"{'='*80}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Generate comic panels from detective story JSON using JobTracker"
    )

    parser.add_argument(
        "input_json", type=str, help="Path to detective story JSON output"
    )

    parser.add_argument(
        "--movie-id",
        type=str,
        required=True,
        help="Movie/project ID for job tracking",
    )

    parser.add_argument(
        "--style",
        type=str,
        default="Noir Comic Book Style",
        help="Art style for panels (default: Noir Comic Book Style)",
    )

    parser.add_argument(
        "--output",
        type=str,
        default="output/detective_panels",
        help="Output directory for generated images",
    )

    parser.add_argument(
        "--db-path",
        type=str,
        default="./cinema_jobs.db",
        help="Path to SQLite job database",
    )

    args = parser.parse_args()

    # Run async main
    asyncio.run(main_async(args))


if __name__ == "__main__":
    main()
