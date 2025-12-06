#!/usr/bin/env python3
"""
Art Reference Management CLI

Commands:
  analyze <style> [directory]  - Analyze reference images and extract characteristics
  list <style>                 - List all references for a style
  show <style> <ref_id>        - Show details for a specific reference
  search <style> --tags        - Search references by tags
"""

import asyncio
import sys
import json
from pathlib import Path
from typing import Optional

from cinema.utils.art_reference_analyzer import analyze_reference_images
from cinema.models.art_reference import ArtReferenceLibrary


def load_library(style: str) -> Optional[ArtReferenceLibrary]:
    """Load reference library for a style."""
    library_file = Path(f"knowledge/art-styles/references/{style}/{style}_references.json")
    
    if not library_file.exists():
        print(f"❌ Library not found: {library_file}")
        print(f"   Run: python manage_art_references.py analyze {style}")
        return None
    
    with open(library_file, 'r') as f:
        data = json.load(f)
    
    return ArtReferenceLibrary(**data)


def cmd_analyze(style: str, directory: Optional[str] = None):
    """Analyze reference images."""
    print(f"🔍 Analyzing reference images for: {style}")
    print()
    
    dir_path = Path(directory) if directory else None
    asyncio.run(analyze_reference_images(style, dir_path))


def cmd_list(style: str):
    """List all references for a style."""
    library = load_library(style)
    if not library:
        return
    
    print(f"📚 References for {style}:")
    print(f"   Total: {len(library.references)}")
    print()
    
    for ref in library.references:
        print(f"   • {ref.name} ({ref.id})")
        print(f"     File: {Path(ref.file_path).name}")
        print(f"     Tags: {len(ref.tags)}")
        
        if ref.analysis:
            print(f"     Technique: {ref.analysis.rendering_technique}")
            print(f"     Colors: {', '.join(ref.analysis.dominant_colors[:3])}")
        
        print()


def cmd_show(style: str, ref_id: str):
    """Show details for a specific reference."""
    library = load_library(style)
    if not library:
        return
    
    ref = library.get_reference_by_id(ref_id)
    if not ref:
        print(f"❌ Reference not found: {ref_id}")
        return
    
    print(f"📸 {ref.name}")
    print(f"   ID: {ref.id}")
    print(f"   Style: {ref.style}")
    print(f"   File: {ref.file_path}")
    print()
    
    print(f"📝 Purpose:")
    print(f"   {ref.purpose}")
    print()
    
    print(f"🏷️  Tags ({len(ref.tags)}):")
    tags_by_category = {}
    for tag in ref.tags:
        if tag.category not in tags_by_category:
            tags_by_category[tag.category] = []
        tags_by_category[tag.category].append(f"{tag.value} ({tag.weight})")
    
    for category, values in tags_by_category.items():
        print(f"   {category}: {', '.join(values)}")
    print()
    
    if ref.analysis:
        print(f"🎨 Visual Analysis:")
        print(f"   Colors: {', '.join(ref.analysis.dominant_colors)}")
        print(f"   Palette: {ref.analysis.color_palette_description}")
        print(f"   Line Work: {ref.analysis.line_work_style}")
        print(f"   Rendering: {ref.analysis.rendering_technique}")
        print(f"   Lighting: {ref.analysis.lighting_style}")
        print(f"   Texture: {ref.analysis.texture_details}")
        print()
    
    print(f"💡 Best Used For:")
    if ref.use_for_shot_types:
        print(f"   Shot Types: {', '.join(ref.use_for_shot_types)}")
    if ref.use_for_scene_types:
        print(f"   Scene Types: {', '.join(ref.use_for_scene_types)}")
    if ref.use_for_panel_layouts:
        print(f"   Panel Layouts: {', '.join(ref.use_for_panel_layouts)}")
    if ref.use_for_emotional_tones:
        print(f"   Emotional Tones: {', '.join(ref.use_for_emotional_tones)}")
    print()
    
    print(f"📄 Style Description:")
    print(f"   {ref.text_prompt}")


def cmd_search(style: str, **kwargs):
    """Search references by tags."""
    library = load_library(style)
    if not library:
        return
    
    # Parse search criteria
    shot_type = kwargs.get('shot_type')
    scene_type = kwargs.get('scene_type')
    panel_layout = kwargs.get('panel_layout')
    emotional_tone = kwargs.get('emotional_tone')
    tag_category = kwargs.get('tag_category')
    tag_value = kwargs.get('tag_value')
    
    print(f"🔍 Searching {style} references...")
    print()
    
    # Search by tags
    if tag_category and tag_value:
        results = library.get_references_by_tag(tag_category, tag_value)
        print(f"   Found {len(results)} references with tag: {tag_category}={tag_value}")
    else:
        # Search by context
        results = library.find_best_references(
            shot_type=shot_type,
            scene_type=scene_type,
            panel_layout=panel_layout,
            emotional_tone=emotional_tone,
            max_results=10
        )
        print(f"   Found {len(results)} matching references")
    
    print()
    for ref in results:
        print(f"   • {ref.name} ({ref.id})")
        if ref.analysis:
            print(f"     {ref.analysis.rendering_technique}")


def cmd_tags(style: str):
    """List all available tags for a style."""
    library = load_library(style)
    if not library:
        return
    
    print(f"🏷️  Available tags for {style}:")
    print()
    
    all_tags = library.get_all_tags()
    
    for category, values in sorted(all_tags.items()):
        print(f"   {category}:")
        for value in values:
            print(f"     • {value}")
        print()


def print_usage():
    """Print usage information."""
    print("""
Art Reference Management CLI

Commands:
  analyze <style> [directory]     Analyze reference images and extract characteristics
  list <style>                    List all references for a style
  show <style> <ref_id>           Show details for a specific reference
  search <style> [options]        Search references by context
  tags <style>                    List all available tags

Examples:
  # Analyze images in default directory
  python manage_art_references.py analyze akira
  
  # Analyze images in custom directory
  python manage_art_references.py analyze spiderverse /path/to/images
  
  # List all references
  python manage_art_references.py list akira
  
  # Show specific reference
  python manage_art_references.py show akira akira_motion_lines
  
  # Search by context
  python manage_art_references.py search akira --shot_type=wide --scene_type=action
  
  # List available tags
  python manage_art_references.py tags akira
""")


def main():
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "analyze":
        if len(sys.argv) < 3:
            print("Usage: analyze <style> [directory]")
            sys.exit(1)
        style = sys.argv[2]
        directory = sys.argv[3] if len(sys.argv) > 3 else None
        cmd_analyze(style, directory)
    
    elif command == "list":
        if len(sys.argv) < 3:
            print("Usage: list <style>")
            sys.exit(1)
        style = sys.argv[2]
        cmd_list(style)
    
    elif command == "show":
        if len(sys.argv) < 4:
            print("Usage: show <style> <ref_id>")
            sys.exit(1)
        style = sys.argv[2]
        ref_id = sys.argv[3]
        cmd_show(style, ref_id)
    
    elif command == "search":
        if len(sys.argv) < 3:
            print("Usage: search <style> [--shot_type=X] [--scene_type=X] [--panel_layout=X]")
            sys.exit(1)
        style = sys.argv[2]
        
        # Parse options
        kwargs = {}
        for arg in sys.argv[3:]:
            if arg.startswith('--'):
                key, value = arg[2:].split('=')
                kwargs[key] = value
        
        cmd_search(style, **kwargs)
    
    elif command == "tags":
        if len(sys.argv) < 3:
            print("Usage: tags <style>")
            sys.exit(1)
        style = sys.argv[2]
        cmd_tags(style)
    
    else:
        print(f"Unknown command: {command}")
        print_usage()
        sys.exit(1)


if __name__ == "__main__":
    main()
