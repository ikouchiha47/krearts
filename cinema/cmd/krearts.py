#!/usr/bin/env python
"""
Krearts CLI - Unified interface for incremental content generation.

Usage:
    # Initialize (generate storyline)
    krearts init book --id detective_abc123
    
    # Generate book content
    krearts book detective_abc123 --continue
    
    # Generate specific chapters
    krearts book detective_abc123 chapters 1,5
    
    # Continue from last chapter
    krearts book detective_abc123 chapters --continue
    
    # Generate specific pages
    krearts chapters detective_abc123 --pages 1,20
    
    # Continue from last page
    krearts chapters detective_abc123 --continue
"""

import asyncio
import logging
import sys
from typing import Optional, List

import click
from dotenv import load_dotenv

from cinema.context import DirectorsContext
from cinema.registry import OpenAiHerd
from cinema.workflow.book_workflow import BookWorkflow
from cinema.workflow.interface import WorkflowType
from cinema.logging_config import (
    setup_logging,
    user_info,
    user_success,
    user_error,
    user_section,
    user_output
)

# Load environment variables
load_dotenv()

# Will be initialized per command
logger = None


@click.group()
def cli():
    """Krearts - Incremental content generation workflow"""
    pass


@cli.command()
@click.argument('workflow_id')
def status(workflow_id: str):
    """Show workflow status"""
    asyncio.run(_show_status(workflow_id))


async def _show_status(workflow_id: str):
    """Show workflow status"""
    from pathlib import Path
    import json
    
    logger.info("=" * 80)
    logger.info(f"Workflow Status: {workflow_id}")
    logger.info("=" * 80)
    
    # Try to load state - support both book_{id} and detective_{id} formats
    output_dir = f"output/book_{workflow_id}"
    state_file = Path(output_dir) / "workflow_state.json"
    
    if not state_file.exists():
        # Try detective_{id} format
        output_dir = f"output/detective_{workflow_id}"
        state_file = Path(output_dir) / "workflow_state.json"
    
    if not state_file.exists():
        logger.error(f"❌ Workflow not found: {workflow_id}")
        logger.info(f"   Expected: output/book_{workflow_id}/workflow_state.json")
        logger.info(f"        or: output/detective_{workflow_id}/workflow_state.json")
        return
    
    with open(state_file, 'r') as f:
        state = json.load(f)
    
    # Show state
    logger.info(f"ID: {state['id']}")
    logger.info(f"Type: {state['type']}")
    logger.info(f"Current Stage: {state['current_stage']}")
    logger.info(f"Output Directory: {state['output_dir']}")
    logger.info("")
    logger.info("Progress:")
    logger.info(f"  ✓ Storyline: {'Done' if state['storyline_done'] else 'Not started'}")
    logger.info(f"  ✓ Content: {'Done' if state['content_done'] else 'Not started'}")
    logger.info(f"  ✓ Chapters: {len(state['chapters_generated'])} generated")
    
    if state['chapters_generated']:
        logger.info(f"     Chapters: {sorted(state['chapters_generated'])}")
        
        # Count pages per chapter
        for chapter in sorted(state['chapters_generated']):
            chapter_file = Path(output_dir) / f"chapter_{chapter:02d}.json"
            if chapter_file.exists():
                with open(chapter_file, 'r') as f:
                    chapter_data = json.load(f)
                
                # Count pages
                total_pages = 0
                for ch in chapter_data.get('chapters', []):
                    for scene in ch.get('scenes', []):
                        total_pages += len(scene.get('pages', []))
                
                logger.info(f"       Chapter {chapter}: {total_pages} pages")
    
    logger.info(f"  ✓ Pages: {len(state['pages_generated'])} generated")
    
    if state['pages_generated']:
        logger.info(f"     Pages: {sorted(state['pages_generated'])[:10]}{'...' if len(state['pages_generated']) > 10 else ''}")
    
    logger.info("=" * 80)
    
    # Show next steps
    if not state['storyline_done']:
        logger.info(f"Next: krearts init book")
    elif not state['content_done']:
        logger.info(f"Next: krearts book {workflow_id} --continue")
    elif not state['chapters_generated']:
        logger.info(f"Next: krearts book {workflow_id} chapters all")
    elif not state['pages_generated']:
        logger.info(f"Next: krearts chapters {workflow_id} --pages 1,10")
    else:
        logger.info(f"Next: krearts chapters {workflow_id} --continue")
    
    logger.info("=" * 80)


@cli.group()
def template():
    """Generate config templates"""
    pass


@template.command()
@click.option('--detective', is_flag=True, help='Detective mystery template')
@click.option('--output', default='book_config.json', help='Output file path')
def book(detective: bool, output: str):
    """Generate book config template"""
    _generate_book_template(detective, output)


def _generate_book_template(detective: bool, output: str):
    """Generate book config template"""
    import json
    
    if detective:
        # Detective mystery template
        template = {
            "_description": "Detective mystery book configuration",
            "characters": "Detective Morgan (52, Irish-English, detective), James Butler (48, British, killer), Victor Ashford (65, British, victim), Dr. Helen Price (38, British, accomplice), Margaret Ashford (42, British, witness)",
            "relationships": "Butler served Ashford family for 30 years, enduring humiliation and witnessing family secrets. Dr. Price was family physician, hiding illegal medical practice that Victor threatened to expose. Margaret is Victor's wife, emotionally neglected for years.",
            "killer": "James Butler",
            "victim": "Victor Ashford",
            "accomplices": "Dr. Helen Price",
            "witnesses": "Margaret Ashford",
            "betrayals": "",
            "art_style": "Print Comic Noir Style with Halftones",
            "genre": "Detective Mystery",
            "setting": "1940s England, Blackwood Manor - a decaying aristocratic estate on rain-lashed countryside",
            "theme": "Revenge, class struggle, and the price of secrets",
            "tone": "Dark, atmospheric, noir",
            "skipper": {
                "_description": "Control which stages use mock/cached data vs actual generation",
                "p": False,
                "c": False,
                "w": False,
                "s": True,
                "_note": "p=plotbuilder, c=critique, w=writer(screenplay/book), s=storyboard. true=skip/mock, false=generate"
            },
            "_example_characters_format": "Name (age, ethnicity, role), Name (age, ethnicity, role)...",
            "_example_relationships": "Describe how characters know each other, their history, conflicts, and motivations",
            "_available_roles": ["detective", "killer", "victim", "accomplice", "witness", "betrayal", "framed_suspect"]
        }
    else:
        # Generic book template
        template = {
            "_description": "Generic book configuration",
            "characters": "Protagonist (age, ethnicity, role), Antagonist (age, ethnicity, role), Supporting Character (age, ethnicity, role)",
            "relationships": "Describe character relationships and history",
            "art_style": "Print Comic Style",
            "genre": "Mystery/Thriller/Drama/Action",
            "setting": "Time period and location",
            "theme": "Central theme or message",
            "tone": "Atmospheric description",
            "skipper": {
                "_description": "Control which stages use mock/cached data vs actual generation",
                "p": False,
                "c": False,
                "w": False,
                "s": True,
                "_note": "p=plotbuilder, c=critique, w=writer(screenplay/book), s=storyboard. true=skip/mock, false=generate"
            },
            "_note": "For detective mysteries, use --detective flag for specialized template"
        }
    
    # Write template
    with open(output, 'w') as f:
        json.dump(template, f, indent=2)
    
    logger.info("=" * 80)
    logger.info(f"✅ Template generated: {output}")
    logger.info(f"   Type: {'Detective Mystery' if detective else 'Generic Book'}")
    logger.info("=" * 80)
    logger.info("Edit the template and use it:")
    logger.info(f"  krearts init book --config {output}")
    logger.info("=" * 80)


@cli.group()
def init():
    """Initialize workflow (generate storyline)"""
    pass


@init.command()
@click.option('--config', type=click.Path(exists=True), help='JSON config file with parameters')
@click.option('--characters', default=None, help='Character descriptions (optional)')
@click.option('--killer', default=None, help='Killer name (optional)')
@click.option('--victim', default=None, help='Victim name (optional)')
def book(config: Optional[str], characters: Optional[str], killer: Optional[str], victim: Optional[str]):
    """Initialize book workflow (generates new ID)"""
    asyncio.run(_init_book(config, characters, killer, victim))


async def _init_book(config: Optional[str], characters: Optional[str], killer: Optional[str], victim: Optional[str]):
    """Initialize book workflow"""
    import uuid
    import json
    
    # Load config from JSON if provided
    config_data = {}
    if config:
        user_info(f"Loading config from: {config}")
        with open(config, 'r') as f:
            config_data = json.load(f)
        user_info(f"Loaded {len(config_data)} parameters")
    
    # CLI options override config file
    if characters:
        config_data['characters'] = characters
    if killer:
        config_data['killer'] = killer
    if victim:
        config_data['victim'] = victim
    
    # Generate new workflow ID
    workflow_id = str(uuid.uuid4())[:8]
    
    # Setup logging for this workflow
    global logger
    logger, log_file, cleanup = setup_logging(workflow_id)
    
    try:
        user_section(f"Initializing Book Workflow")
        user_info(f"ID: {workflow_id}")
        user_info(f"Log file: {log_file}")
        
        ctx = DirectorsContext(llmstore=OpenAiHerd, debug=True)
        workflow = BookWorkflow(workflow_id, ctx)
        
        result = await workflow.init(**config_data)
        
        user_section("Initialization Complete")
        user_success(f"Workflow ID: {workflow_id}")
        user_info(f"Output: output/book_{workflow_id}")
        user_info(f"Critique: {result['critique']}")
        
        # Show storyline content
        user_output("Storyline", result['storyline'], preview_length=1000)
        
        user_info("")
        user_info(f"Next: krearts book {workflow_id} --continue")
        user_info("=" * 80)
        
        return workflow_id
    finally:
        if cleanup:
            cleanup()


@cli.command()
@click.argument('workflow_id')
@click.option('--continue', 'continue_from', is_flag=True, help='Continue from saved state')
@click.option('--chapters', help='Generate specific chapters (e.g., 1,5 or "all")')
def book(workflow_id: str, continue_from: bool, chapters: Optional[str]):
    """Generate book content or chapters"""
    if chapters:
        # Generate chapters
        if chapters.lower() == 'all':
            chapter_list = None  # Will generate all chapters
        else:
            chapter_list = [int(c.strip()) for c in chapters.split(',')]
        asyncio.run(_generate_chapters(workflow_id, chapter_list, False))
    else:
        # Generate book content
        asyncio.run(_generate_book(workflow_id, continue_from))


async def _generate_book(workflow_id: str, continue_from: bool):
    """Generate book content"""
    # Setup logging
    global logger
    logger, log_file, cleanup = setup_logging(workflow_id)
    
    try:
        user_section(f"Generating Book: {workflow_id}")
        user_info(f"Log file: {log_file}")
        
        ctx = DirectorsContext(llmstore=OpenAiHerd, debug=True)
        workflow = BookWorkflow(workflow_id, ctx)
        
        result = await workflow.generate_content(
            continue_from=workflow_id if continue_from else None
        )
        
        user_section("Book Generation Complete")
        user_success(f"Novel saved: {result['output_file']}")
        
        # Show novel content
        user_output("Novel", result['content'], preview_length=1000)
        
        user_info("")
        user_info(f"Next: krearts book {workflow_id} --chapters 1")
        user_info(f"  or: krearts book {workflow_id} --chapters all")
        user_info("=" * 80)
    finally:
        if cleanup:
            cleanup()


async def _generate_chapters(workflow_id: str, chapters: Optional[List[int]], continue_from: bool):
    """Generate chapters"""
    # Setup logging
    global logger
    logger, log_file, cleanup = setup_logging(workflow_id)
    
    try:
        user_section(f"Generating Chapters: {workflow_id}")
        user_info(f"Log file: {log_file}")
        
        ctx = DirectorsContext(llmstore=OpenAiHerd, debug=True)
        workflow = BookWorkflow(workflow_id, ctx)
        
        result = await workflow.generate_chapters(
            chapters=chapters,
            continue_from=continue_from
        )
        
        user_section("Chapter Generation Complete")
        user_success(f"Chapters generated: {result['chapters']}")
        user_info(f"Total generated: {result['total_generated']}")
        user_info(f"Output: {result['output_dir']}")
        
        # Show chapter files created
        if result['chapters']:
            user_info("\nChapter files created:")
            for ch in result['chapters']:
                chapter_file = f"output/book_{workflow_id}/chapter_{ch:02d}.json"
                user_info(f"  - {chapter_file}")
        
        user_info("")
        user_info(f"Next: krearts chapters {workflow_id} --pages 1,20")
        user_info(f"  or: krearts chapters {workflow_id} --continue")
        user_info("=" * 80)
    finally:
        # Restore stdout/stderr
        if cleanup:
            cleanup()


@cli.command()
@click.argument('workflow_id')
@click.option('--pages', help='Generate specific pages (e.g., 1,20 or "all")')
@click.option('--continue', 'continue_from', is_flag=True, help='Continue from last page')
def chapters(workflow_id: str, pages: Optional[str], continue_from: bool):
    """Generate page images from chapters"""
    if pages:
        if pages.lower() == 'all':
            page_list = None  # Will generate all pages
        else:
            page_list = [int(p.strip()) for p in pages.split(',')]
        asyncio.run(_generate_pages(workflow_id, page_list, False))
    else:
        asyncio.run(_generate_pages(workflow_id, None, continue_from))


async def _generate_pages(workflow_id: str, pages: Optional[List[int]], continue_from: bool):
    """Generate pages"""
    # Setup logging
    global logger
    logger, log_file, cleanup = setup_logging(workflow_id)
    
    try:
        user_section(f"Generating Pages: {workflow_id}")
        user_info(f"Log file: {log_file}")
        
        ctx = DirectorsContext(llmstore=OpenAiHerd, debug=True)
        workflow = BookWorkflow(workflow_id, ctx)
        
        result = await workflow.generate_pages(
            pages=pages,
            continue_from=continue_from
        )
        
        user_section("Page Generation Complete")
        user_success(f"Pages generated: {result['pages']}")
        user_info(f"Total generated: {result['total_generated']}")
        user_info(f"Output: {result['output_dir']}")
        user_info("=" * 80)
    finally:
        if cleanup:
            cleanup()


@cli.command()
@click.argument('workflow_id')
@click.option('--chapter', type=int, help='Read specific chapter (e.g., 1)')
@click.option('--list', 'list_chapters', is_flag=True, help='List all available chapters')
@click.option('--novel', is_flag=True, help='Read the full novel')
@click.option('--storyline', is_flag=True, help='Read the storyline')
def read(workflow_id: str, chapter: Optional[int], list_chapters: bool, novel: bool, storyline: bool):
    """Read workflow content (storyline, novel, or chapters)"""
    asyncio.run(_read_content(workflow_id, chapter, list_chapters, novel, storyline))


async def _read_content(workflow_id: str, chapter: Optional[int], list_chapters: bool, novel: bool, storyline: bool):
    """Read and display workflow content"""
    from pathlib import Path
    import json
    
    # Determine output directory
    output_dir = Path(f"output/book_{workflow_id}")
    if not output_dir.exists():
        output_dir = Path(f"output/detective_{workflow_id}")
    
    if not output_dir.exists():
        user_error(f"Workflow not found: {workflow_id}")
        user_info(f"Expected: output/book_{workflow_id}/ or output/detective_{workflow_id}/")
        return
    
    user_section(f"Reading Workflow: {workflow_id}")
    user_info(f"Output: {output_dir}")
    user_info("")
    
    # List chapters
    if list_chapters:
        # First, try to get chapter list from novel
        novel_file = output_dir / "novel.md"
        chapters_from_novel = []
        
        if novel_file.exists():
            try:
                from cinema.models.novel import Novel
                novel = Novel.from_file(str(novel_file))
                chapters_from_novel = [(ch.number, ch.title) for ch in novel.chapters]
                user_info(f"Novel: {novel.title}")
                user_info(f"Total chapters in novel: {len(chapters_from_novel)}")
                user_info("")
            except Exception as e:
                user_info(f"Note: Could not parse novel: {e}")
                user_info("")
        
        # Check which chapters have been generated as comic files
        chapter_files = sorted(output_dir.glob("chapter_*.json"))
        generated_chapters = {}
        
        for ch_file in chapter_files:
            try:
                with open(ch_file, 'r') as f:
                    ch_data = json.load(f)
                    
                    # Handle ComicBookOutput structure (has 'chapters' array)
                    if 'chapters' in ch_data and isinstance(ch_data['chapters'], list):
                        for comic_ch in ch_data['chapters']:
                            ch_num = comic_ch.get('chapter_number')
                            if ch_num:
                                scenes_list = comic_ch.get('scenes', [])
                                scenes = len(scenes_list)
                                
                                # Calculate pages and panels from scenes
                                pages = comic_ch.get('total_pages') or sum(len(s.get('pages', [])) for s in scenes_list)
                                panels = comic_ch.get('total_panels') or sum(
                                    sum(len(p.get('panels', [])) for p in s.get('pages', []))
                                    for s in scenes_list
                                )
                                
                                generated_chapters[ch_num] = {
                                    'title': comic_ch.get('chapter_title') or comic_ch.get('title', 'Untitled'),
                                    'scenes': scenes,
                                    'pages': pages,
                                    'panels': panels,
                                    'file': ch_file.name
                                }
                    # Handle old format (direct chapter object)
                    else:
                        ch_num = ch_data.get('chapter_number', None)
                        if ch_num:
                            scenes = len(ch_data.get('scenes', []))
                            pages = sum(len(s.get('pages', [])) for s in ch_data.get('scenes', []))
                            generated_chapters[ch_num] = {
                                'title': ch_data.get('title', 'Untitled'),
                                'scenes': scenes,
                                'pages': pages,
                                'panels': 0,
                                'file': ch_file.name
                            }
            except Exception as e:
                pass
        
        # Display chapter status
        if chapters_from_novel:
            user_info("Chapter Generation Status:")
            user_info("")
            for ch_num, ch_title in chapters_from_novel:
                if ch_num in generated_chapters:
                    gen = generated_chapters[ch_num]
                    status = "✅ Generated"
                    details = f"{gen['scenes']} scenes, {gen['pages']} pages, {gen['panels']} panels"
                else:
                    status = "⏳ Not generated"
                    details = "pending"
                
                user_info(f"  Chapter {ch_num}: {ch_title}")
                user_info(f"    Status: {status} ({details})")
                user_info("")
        elif generated_chapters:
            user_info(f"Generated chapters ({len(generated_chapters)}):")
            user_info("")
            for ch_num in sorted(generated_chapters.keys()):
                gen = generated_chapters[ch_num]
                user_info(f"  Chapter {ch_num}: {gen['title']}")
                user_info(f"    - {gen['scenes']} scenes, {gen['pages']} pages, {gen['panels']} panels")
                user_info(f"    - File: {gen['file']}")
                user_info("")
        else:
            user_info("No chapters generated yet.")
            if novel_file.exists():
                user_info(f"Generate chapters with: krearts book {workflow_id} --chapters 1")
            else:
                user_info(f"Generate novel first with: krearts book {workflow_id} --continue")
            user_info("")
            return
        
        user_info("=" * 80)
        user_info(f"To read a chapter: krearts read {workflow_id} --chapter 1")
        if chapters_from_novel and len(generated_chapters) < len(chapters_from_novel):
            pending = [ch for ch, _ in chapters_from_novel if ch not in generated_chapters]
            user_info(f"To generate pending: krearts book {workflow_id} --chapters {','.join(map(str, pending[:3]))}")
        user_info("=" * 80)
        return
    
    # Read storyline
    if storyline:
        # Try storyline.md first
        storyline_file = output_dir / "storyline.md"
        if storyline_file.exists():
            with open(storyline_file, 'r') as f:
                content = f.read()
        else:
            # Try flow state
            flow_state_file = Path(f"output/flow_states/storybuilder_{workflow_id}.json")
            if not flow_state_file.exists():
                user_error("Storyline not found")
                user_info(f"Expected: {storyline_file} or {flow_state_file}")
                return
            
            with open(flow_state_file, 'r') as f:
                flow_data = json.load(f)
                content = flow_data.get('output', {}).get('storyline', '')
                if not content:
                    user_error("Storyline not generated yet")
                    return
        
        user_output("Storyline", content, preview_length=2000)
        user_info("")
        user_info(f"Source: {storyline_file if storyline_file.exists() else flow_state_file}")
        user_info("=" * 80)
        return
    
    # Read novel
    if novel:
        novel_file = output_dir / "novel.md"
        if not novel_file.exists():
            user_error("Novel not found")
            user_info("Generate it with: krearts book {workflow_id} --continue")
            return
        
        with open(novel_file, 'r') as f:
            content = f.read()
        
        user_output("Novel", content, preview_length=2000)
        user_info("")
        user_info(f"Full file: {novel_file}")
        user_info("=" * 80)
        return
    
    # Read specific chapter
    if chapter:
        chapter_file = output_dir / f"chapter_{chapter:02d}.json"
        if not chapter_file.exists():
            user_error(f"Chapter {chapter} not found: {chapter_file}")
            user_info(f"Generate it with: krearts book {workflow_id} --chapters {chapter}")
            return
        
        with open(chapter_file, 'r') as f:
            file_data = json.load(f)
        
        # Handle ComicBookOutput structure
        if 'chapters' in file_data and isinstance(file_data['chapters'], list):
            # Find the requested chapter
            ch_data = None
            for comic_ch in file_data['chapters']:
                if comic_ch.get('chapter_number') == chapter:
                    ch_data = comic_ch
                    break
            
            if not ch_data:
                user_error(f"Chapter {chapter} not found in file")
                return
        else:
            # Old format
            ch_data = file_data
        
        # Display chapter info
        title = ch_data.get('chapter_title') or ch_data.get('title', 'Untitled')
        user_info(f"Chapter {ch_data.get('chapter_number', '?')}: {title}")
        user_info("=" * 80)
        user_info("")
        
        # Show summary if available
        summary = ch_data.get('chapter_summary')
        if summary:
            user_info(f"Summary: {summary}")
            user_info("")
        
        scenes = ch_data.get('scenes', [])
        user_info(f"Total Scenes: {len(scenes)}")
        user_info("")
        
        for i, scene in enumerate(scenes, 1):
            scene_num = scene.get('scene_number', i)
            location = scene.get('location', 'Unknown')
            time = scene.get('time_of_day', 'Unknown')
            description = scene.get('scene_description', '')
            
            user_info(f"Scene {scene_num}: {location}")
            user_info(f"  Time: {time}")
            if description:
                desc_preview = description[:100] + "..." if len(description) > 100 else description
                user_info(f"  Description: {desc_preview}")
            
            pages = scene.get('pages', [])
            user_info(f"  Pages: {len(pages)}")
            
            for j, page in enumerate(pages, 1):
                panels = page.get('panels', [])
                user_info(f"    Page {j}: {len(panels)} panels")
                
                # Show first panel description as preview
                if panels:
                    first_panel = panels[0]
                    desc = first_panel.get('description', '')
                    if len(desc) > 100:
                        desc = desc[:100] + "..."
                    user_info(f"      Panel 1: {desc}")
            
            user_info("")
        
        user_info("=" * 80)
        user_info(f"Full file: {chapter_file}")
        user_info(f"To generate images: krearts chapters {workflow_id} --pages 1,20")
        user_info("=" * 80)
        return
    
    # Default: show what's available
    user_info("What would you like to read?")
    user_info("")
    user_info("Options:")
    user_info(f"  krearts read {workflow_id} --storyline     # Read storyline")
    user_info(f"  krearts read {workflow_id} --novel         # Read full novel")
    user_info(f"  krearts read {workflow_id} --list          # List all chapters")
    user_info(f"  krearts read {workflow_id} --chapter 1     # Read chapter 1")
    user_info("=" * 80)


if __name__ == '__main__':
    cli()
