#!/usr/bin/env python
"""
Migrate existing detective_{id} output to book workflow format.

This creates the workflow_state.json needed for krearts to work with existing outputs.
"""

import json
import logging
from pathlib import Path
import sys

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def migrate_detective_output(detective_id: str):
    """Migrate detective_{id} to workflow format"""
    
    detective_dir = Path(f"output/detective_{detective_id}")
    
    if not detective_dir.exists():
        logger.error(f"Detective output not found: {detective_dir}")
        return False
    
    logger.info(f"Migrating: {detective_dir}")
    
    # Check what chapters exist
    chapter_files = sorted(detective_dir.glob("chapter_*.json"))
    chapters_generated = []
    
    for chapter_file in chapter_files:
        # Extract chapter number from filename
        chapter_num = int(chapter_file.stem.split('_')[1])
        chapters_generated.append(chapter_num)
    
    logger.info(f"Found {len(chapters_generated)} chapters: {chapters_generated}")
    
    # Check what pages exist
    pages_dir = detective_dir / "pages"
    pages_generated = []
    
    if pages_dir.exists():
        # Build mapping of page files to global page indices
        # First, build the full page list from chapter JSONs
        all_pages = []
        for chapter_file in chapter_files:
            with open(chapter_file, 'r') as f:
                chapter_data = json.load(f)
            
            for chapter in chapter_data.get('chapters', []):
                chapter_num = chapter.get('chapter_number')
                for scene in chapter.get('scenes', []):
                    scene_num = scene.get('scene_number')
                    for page in scene.get('pages', []):
                        page_num = page.get('page_number')
                        all_pages.append({
                            'chapter': chapter_num,
                            'scene': scene_num,
                            'page': page_num,
                            'global_index': len(all_pages) + 1,
                            'filename': f"ch{chapter_num}_sc{scene_num}_page{page_num}.png"
                        })
        
        # Check which page files exist
        for page_info in all_pages:
            page_file = pages_dir / page_info['filename']
            if page_file.exists():
                pages_generated.append(page_info['global_index'])
        
        logger.info(f"Found {len(pages_generated)} existing pages: {sorted(pages_generated)}")
    
    # Create workflow state
    workflow_state = {
        "id": detective_id,
        "type": "book",
        "output_dir": str(detective_dir),
        "current_stage": "pages",  # Ready for page generation
        "storyline_done": True,
        "content_done": True,
        "chapters_generated": chapters_generated,
        "pages_generated": sorted(pages_generated),
        "config": {
            "_note": "Migrated from existing detective output",
            "skipper": {
                "p": True,
                "c": True,
                "w": True,
                "s": True
            }
        }
    }
    
    # Save workflow state
    state_file = detective_dir / "workflow_state.json"
    with open(state_file, 'w') as f:
        json.dump(workflow_state, f, indent=2)
    
    logger.info(f"✅ Created workflow state: {state_file}")
    
    # Check if novel.md exists
    novel_file = detective_dir / "novel.md"
    if not novel_file.exists():
        logger.warning(f"⚠️  No novel.md found - you'll need to add it for chapter regeneration")
        logger.info(f"   Expected: {novel_file}")
    else:
        logger.info(f"✅ Found novel.md")
    
    logger.info("")
    logger.info("=" * 80)
    logger.info("Migration complete!")
    logger.info("=" * 80)
    logger.info(f"You can now use:")
    logger.info(f"  krearts status {detective_id}")
    logger.info(f"  krearts chapters {detective_id} --pages 1,10")
    logger.info("=" * 80)
    
    return True


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python migrate_detective_to_workflow.py <detective_id>")
        print("Example: python migrate_detective_to_workflow.py ce8f9a4a")
        sys.exit(1)
    
    detective_id = sys.argv[1]
    success = migrate_detective_output(detective_id)
    sys.exit(0 if success else 1)
