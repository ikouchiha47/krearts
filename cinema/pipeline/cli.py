#!/usr/bin/env python3
"""
CLI tool for cinema pipeline operations.
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path

from cinema.agents.scriptwriter.crew import Enhancer, ScriptWriter
from cinema.pipeline import JobTracker, MovieMaker


def create_maker(db_path: str = "./cinema_jobs.db") -> MovieMaker:
    """Create MovieMaker instance"""
    # TODO: Initialize with proper context
    # For now, this is a placeholder
    print("Note: ScriptWriter and Enhancer need proper initialization")
    print("This is a demo CLI showing the interface")
    return None


async def cmd_generate(args):
    """Generate a new movie"""
    maker = create_maker(args.db)

    if args.script_file:
        script = Path(args.script_file).read_text()
    else:
        script = args.script

    print(f"Generating movie from script...")
    print(f"Movie ID: {args.movie_id or 'auto-generated'}")
    print(f"Output dir: {args.output}")

    state = await maker.generate(
        script=script,
        movie_id=args.movie_id,
        base_dir=args.output,
    )

    print(f"\n✓ Movie generation complete!")
    print(f"Final video: {state.get_final_video_path()}")


async def cmd_resume(args):
    """Resume a movie generation"""
    maker = create_maker(args.db)

    print(f"Resuming movie: {args.movie_id}")

    state = await maker.resume(
        movie_id=args.movie_id,
        base_dir=args.output,
    )

    print(f"\n✓ Movie generation complete!")
    print(f"Final video: {state.get_final_video_path()}")


def cmd_status(args):
    """Check movie generation status"""
    maker = create_maker(args.db)

    status = maker.get_status(args.movie_id)

    print(f"\nMovie: {args.movie_id}")
    print(f"{'='*50}")
    print(f"Total jobs:     {status['total']}")
    print(f"Completed:      {status['completed']}")
    print(f"Failed:         {status['failed']}")
    print(f"Pending:        {status['pending']}")
    print(f"Progress:       {status['progress']:.1f}%")


def cmd_list(args):
    """List all movies"""
    tracker = JobTracker(args.db)

    # Query all unique movie IDs
    import sqlite3

    with sqlite3.connect(args.db) as conn:
        cursor = conn.execute(
            """
            SELECT DISTINCT movie_id, created_at 
            FROM pipeline_states 
            ORDER BY created_at DESC
        """
        )
        movies = cursor.fetchall()

    if not movies:
        print("No movies found")
        return

    print(f"\nMovies in database:")
    print(f"{'='*50}")

    for movie_id, created_at in movies:
        maker = create_maker(args.db)
        status = maker.get_status(movie_id)

        print(f"\n{movie_id}")
        print(f"  Created: {created_at}")
        print(f"  Progress: {status['progress']:.1f}%")
        print(f"  Status: {status['completed']}/{status['total']} jobs complete")


def cmd_jobs(args):
    """List jobs for a movie"""
    tracker = JobTracker(args.db)

    jobs = tracker.get_jobs_by_movie(args.movie_id)

    if not jobs:
        print(f"No jobs found for movie: {args.movie_id}")
        return

    print(f"\nJobs for {args.movie_id}:")
    print(f"{'='*80}")

    # Group by type
    from collections import defaultdict

    by_type = defaultdict(list)
    for job in jobs:
        by_type[job.type].append(job)

    for job_type, type_jobs in by_type.items():
        print(f"\n{job_type.value.upper()}")
        print(f"{'-'*80}")

        for job in type_jobs:
            status_icon = {
                "pending": "⏳",
                "in_progress": "🔄",
                "completed": "✓",
                "failed": "✗",
                "skipped": "⊘",
            }.get(job.status.value, "?")

            print(f"  {status_icon} {job.id:<30} {job.status.value:<15}", end="")

            if job.scene_id:
                print(f" scene={job.scene_id}", end="")
            if job.character_id:
                print(f" char={job.character_id}", end="")
            if job.error:
                print(f" error={job.error[:30]}...", end="")

            print()


def cmd_export(args):
    """Export screenplay JSON"""
    tracker = JobTracker(args.db)

    state = tracker.load_state(args.movie_id)

    if not state or not state.screenplay_dict:
        print(f"No screenplay found for movie: {args.movie_id}")
        return

    output = args.output or f"{args.movie_id}_screenplay.json"

    with open(output, "w") as f:
        json.dump(state.screenplay_dict, f, indent=2)

    print(f"Screenplay exported to: {output}")


def main():
    parser = argparse.ArgumentParser(
        description="Cinema Pipeline CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate a new movie
  cinema-cli generate --script "A 15-second ad..." --movie-id my_movie

  # Resume a failed generation
  cinema-cli resume my_movie

  # Check status
  cinema-cli status my_movie

  # List all movies
  cinema-cli list

  # View jobs for a movie
  cinema-cli jobs my_movie

  # Export screenplay JSON
  cinema-cli export my_movie
        """,
    )

    parser.add_argument(
        "--db", default="./cinema_jobs.db", help="Path to SQLite database"
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Generate command
    gen_parser = subparsers.add_parser("generate", help="Generate a new movie")
    gen_parser.add_argument("--script", help="Script text")
    gen_parser.add_argument("--script-file", help="Path to script file")
    gen_parser.add_argument("--movie-id", help="Movie ID (auto-generated if not provided)")
    gen_parser.add_argument("--output", default="./output", help="Output directory")

    # Resume command
    resume_parser = subparsers.add_parser("resume", help="Resume a movie generation")
    resume_parser.add_argument("movie_id", help="Movie ID to resume")
    resume_parser.add_argument("--output", default="./output", help="Output directory")

    # Status command
    status_parser = subparsers.add_parser("status", help="Check movie status")
    status_parser.add_argument("movie_id", help="Movie ID")

    # List command
    subparsers.add_parser("list", help="List all movies")

    # Jobs command
    jobs_parser = subparsers.add_parser("jobs", help="List jobs for a movie")
    jobs_parser.add_argument("movie_id", help="Movie ID")

    # Export command
    export_parser = subparsers.add_parser("export", help="Export screenplay JSON")
    export_parser.add_argument("movie_id", help="Movie ID")
    export_parser.add_argument("--output", help="Output file path")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Route to command handler
    if args.command == "generate":
        if not args.script and not args.script_file:
            print("Error: Either --script or --script-file is required")
            sys.exit(1)
        asyncio.run(cmd_generate(args))
    elif args.command == "resume":
        asyncio.run(cmd_resume(args))
    elif args.command == "status":
        cmd_status(args)
    elif args.command == "list":
        cmd_list(args)
    elif args.command == "jobs":
        cmd_jobs(args)
    elif args.command == "export":
        cmd_export(args)


if __name__ == "__main__":
    main()
