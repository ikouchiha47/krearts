#!/usr/bin/env python3
"""
Critique a detective storyline against established principles.

Usage:
    python -m cinema.cmd.critique_detective detective_storyline.md
"""

import asyncio
import sys
from pathlib import Path

from cinema.agents.bookwriter.critic import DetectivePlotCritic
from cinema.context import DirectorsContext


async def main():
    if len(sys.argv) < 2:
        print("Usage: python -m cinema.cmd.critique_detective <storyline_file.md>")
        print("\nExample:")
        print("  python -m cinema.cmd.critique_detective detective_storyline.md")
        sys.exit(1)

    storyline_file = sys.argv[1]

    if not Path(storyline_file).exists():
        print(f"Error: File not found: {storyline_file}")
        sys.exit(1)

    # Initialize context
    ctx = DirectorsContext()

    # Create critic
    output_file = storyline_file.replace(".md", "_critique.md")
    critic = DetectivePlotCritic(ctx, outfile=output_file)

    print(f"Critiquing storyline: {storyline_file}")
    print(f"Output will be saved to: {output_file}")
    print("-" * 80)

    # Run critique
    critique_report = await critic.critique_from_file(storyline_file)

    print("\n" + "=" * 80)
    print("CRITIQUE COMPLETE")
    print("=" * 80)
    print(f"\nReport saved to: {output_file}")
    print("\nSummary:")
    print("-" * 80)

    # Print first few lines of critique
    lines = critique_report.split("\n")
    for line in lines[:20]:
        print(line)

    if len(lines) > 20:
        print("\n... (see full report in output file)")


if __name__ == "__main__":
    asyncio.run(main())
