#!/usr/bin/env python3
"""
CLI for Comic Strip Generation

Usage:
    python cinema/cmd/generate_comic.py --genre detective --style noir
    python cinema/cmd/generate_comic.py --genre satire --style "Pop Art Comic Style"
"""

import argparse
import sys
from pathlib import Path

from cinema.cmd.comic_strip_generator import ComicStripPipeline
from cinema.agents.bookwriter.models import (
    PlotConstraints,
    Character as DetectiveCharacter,
)


# Predefined story templates
STORY_TEMPLATES = {
    "detective": {
        "title": "The Midnight Murder",
        "characters": [
            DetectiveCharacter("Detective Morgan", "detective"),
            DetectiveCharacter("Victor Ashford", "victim"),
            DetectiveCharacter("James Butler", "butler"),
            DetectiveCharacter("Margaret Ashford", "wife"),
            DetectiveCharacter("Dr. Helen Price", "doctor"),
        ],
        "constraints": PlotConstraints(
            killer="James Butler",
            victim="Victor Ashford",
            accomplices=[],
            framed_suspect="Margaret Ashford",
            witnesses=[("Dr. Helen Price", "suspicious activity")],
            alliances=[],
            winners=["James Butler"],
            losers=["Margaret Ashford"],
            betrayals=[]
        )
    },
    "satire": {
        "title": "The Corporate Conspiracy",
        "characters": [
            DetectiveCharacter("CEO Thompson", "victim"),
            DetectiveCharacter("Intern Jenny", "killer"),
            DetectiveCharacter("HR Manager Bob", "accomplice"),
            DetectiveCharacter("Security Guard", "witness"),
        ],
        "constraints": PlotConstraints(
            killer="Intern Jenny",
            victim="CEO Thompson",
            accomplices=["HR Manager Bob"],
            framed_suspect=None,
            witnesses=[("Security Guard", "coffee machine incident")],
            alliances=[("Intern Jenny", "HR Manager Bob")],
            winners=["Intern Jenny", "HR Manager Bob"],
            losers=["CEO Thompson"],
            betrayals=[]
        )
    },
    "folklore": {
        "title": "The Cursed Village",
        "characters": [
            DetectiveCharacter("Village Elder", "victim"),
            DetectiveCharacter("Witch", "killer"),
            DetectiveCharacter("Young Hero", "detective"),
            DetectiveCharacter("Forest Spirit", "witness"),
        ],
        "constraints": PlotConstraints(
            killer="Witch",
            victim="Village Elder",
            accomplices=[],
            framed_suspect=None,
            witnesses=[("Forest Spirit", "dark ritual")],
            alliances=[],
            winners=["Witch"],
            losers=["Village Elder"],
            betrayals=[]
        )
    }
}

ART_STYLES = {
    "noir": "Noir Comic Book Style",
    "cyberpunk": "Cyberpunk Comic Style",
    "anime": "Anime & Manga Style",
    "pop_art": "Pop Art Comic Style",
    "print_comics": "Print Comics Art",
    "print_noir": "Print Comics + Noir",
    "pixel": "Pixel Art Comic Panel (16-bit)",
    "pencil": "Pencil Sketch Comic Style",
}


def main():
    parser = argparse.ArgumentParser(
        description="Generate comic strips from narrative structures"
    )
    
    parser.add_argument(
        "--genre",
        choices=["detective", "satire", "folklore"],
        default="detective",
        help="Story genre template"
    )
    
    parser.add_argument(
        "--style",
        choices=list(ART_STYLES.keys()),
        default="noir",
        help="Art style for the comic"
    )
    
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output directory (default: output/comic_strips/{genre}_{style})"
    )
    
    parser.add_argument(
        "--title",
        type=str,
        default=None,
        help="Custom title (default: uses template title)"
    )
    
    args = parser.parse_args()
    
    # Get template
    template = STORY_TEMPLATES[args.genre]
    art_style = ART_STYLES[args.style]
    
    # Set output directory
    if args.output:
        output_dir = args.output
    else:
        output_dir = f"output/comic_strips/{args.genre}_{args.style}"
    
    # Set title
    title = args.title or template["title"]
    
    print(f"\n{'='*80}")
    print(f"Comic Strip Generator")
    print(f"{'='*80}")
    print(f"Genre: {args.genre}")
    print(f"Style: {art_style}")
    print(f"Title: {title}")
    print(f"Output: {output_dir}")
    print(f"{'='*80}\n")
    
    # Initialize pipeline
    pipeline = ComicStripPipeline(
        output_dir=output_dir,
        art_style=art_style
    )
    
    # Run pipeline
    try:
        storyboard = pipeline.run_full_pipeline(
            constraints=template["constraints"],
            characters=template["characters"],
            title=title
        )
        
        print(f"\n{'='*80}")
        print(f"✓ SUCCESS")
        print(f"{'='*80}")
        print(f"Comic: {storyboard.title}")
        print(f"Pages: {len(storyboard.pages)}")
        print(f"Panels: {storyboard.total_panels}")
        print(f"Characters: {len(storyboard.characters)}")
        print(f"Output: {output_dir}")
        print(f"{'='*80}\n")
        
    except Exception as e:
        print(f"\n✗ ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
