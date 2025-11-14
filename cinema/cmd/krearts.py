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

# Load environment variables
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


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
        logger.info(f"Loading config from: {config}")
        with open(config, 'r') as f:
            config_data = json.load(f)
        logger.info(f"   Loaded {len(config_data)} parameters")
    
    # CLI options override config file
    if characters:
        config_data['characters'] = characters
    if killer:
        config_data['killer'] = killer
    if victim:
        config_data['victim'] = victim
    
    # Generate new workflow ID
    workflow_id = str(uuid.uuid4())[:8]
    
    logger.info("=" * 80)
    logger.info(f"Initializing book workflow")
    logger.info(f"Generated ID: {workflow_id}")
    logger.info("=" * 80)
    
    ctx = DirectorsContext(llmstore=OpenAiHerd, debug=True)
    workflow = BookWorkflow(workflow_id, ctx)
    
    result = await workflow.init(**config_data)
    
    logger.info("=" * 80)
    logger.info("✅ Initialization complete")
    logger.info(f"   ID: {workflow_id}")
    logger.info(f"   Output: output/book_{workflow_id}")
    logger.info(f"   Storyline: {len(result['storyline'])} chars")
    logger.info(f"   Critique: {result['critique']}")
    logger.info("=" * 80)
    logger.info(f"Next: krearts book {workflow_id} --continue")
    logger.info("=" * 80)
    
    return workflow_id


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
    logger.info("=" * 80)
    logger.info(f"Generating book: {workflow_id}")
    logger.info("=" * 80)
    
    ctx = DirectorsContext(llmstore=OpenAiHerd, debug=True)
    workflow = BookWorkflow(workflow_id, ctx)
    
    result = await workflow.generate_content(
        continue_from=workflow_id if continue_from else None
    )
    
    logger.info("=" * 80)
    logger.info("✅ Book generation complete")
    logger.info(f"   Output: {result['output_file']}")
    logger.info("=" * 80)
    logger.info(f"Next: krearts book {workflow_id} chapters 1,5")
    logger.info(f"  or: krearts book {workflow_id} chapters --continue")
    logger.info("=" * 80)


async def _generate_chapters(workflow_id: str, chapters: Optional[List[int]], continue_from: bool):
    """Generate chapters"""
    logger.info("=" * 80)
    logger.info(f"Generating chapters: {workflow_id}")
    logger.info("=" * 80)
    
    ctx = DirectorsContext(llmstore=OpenAiHerd, debug=True)
    workflow = BookWorkflow(workflow_id, ctx)
    
    result = await workflow.generate_chapters(
        chapters=chapters,
        continue_from=continue_from
    )
    
    logger.info("=" * 80)
    logger.info("✅ Chapter generation complete")
    logger.info(f"   Chapters: {result['chapters']}")
    logger.info(f"   Total generated: {result['total_generated']}")
    logger.info("=" * 80)
    logger.info(f"Next: krearts chapters {workflow_id} --pages 1,20")
    logger.info(f"  or: krearts chapters {workflow_id} --continue")
    logger.info("=" * 80)


@cli.command()
@click.argument('workflow_id')
@click.option('--pages', help='Generate specific pages (e.g., 1,20)')
@click.option('--continue', 'continue_from', is_flag=True, help='Continue from last page')
def chapters(workflow_id: str, pages: Optional[str], continue_from: bool):
    """Generate page images from chapters"""
    if pages:
        page_list = [int(p.strip()) for p in pages.split(',')]
        asyncio.run(_generate_pages(workflow_id, page_list, False))
    else:
        asyncio.run(_generate_pages(workflow_id, None, continue_from))


async def _generate_pages(workflow_id: str, pages: Optional[List[int]], continue_from: bool):
    """Generate pages"""
    logger.info("=" * 80)
    logger.info(f"Generating pages: {workflow_id}")
    logger.info("=" * 80)
    
    ctx = DirectorsContext(llmstore=OpenAiHerd, debug=True)
    workflow = BookWorkflow(workflow_id, ctx)
    
    result = await workflow.generate_pages(
        pages=pages,
        continue_from=continue_from
    )
    
    logger.info("=" * 80)
    logger.info("✅ Page generation complete")
    logger.info(f"   Pages: {result['pages']}")
    logger.info(f"   Total generated: {result['total_generated']}")
    logger.info(f"   Output: {result['output_dir']}")
    logger.info("=" * 80)


if __name__ == '__main__':
    cli()
