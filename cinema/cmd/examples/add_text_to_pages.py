#!/usr/bin/env python3
"""
Add text overlays (dialogue and narration) to generated comic pages.
"""
import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from cinema.utils.text_overlay import ComicTextOverlay
from PIL import Image


def add_text_to_pages(workflow_id: str, output_suffix: str = "_with_text"):
    """Add text overlays to all pages."""
    
    output_dir = Path(f"output/book_{workflow_id}")
    pages_dir = output_dir / "pages"
    chapter_file = output_dir / "chapter_01.json"
    
    if not chapter_file.exists():
        print(f"❌ Chapter file not found: {chapter_file}")
        return
    
    # Load chapter data
    with open(chapter_file) as f:
        data = json.load(f)
    
    chapters = data.get('chapters', [])
    if not chapters:
        print("❌ No chapters found")
        return
    
    ch = chapters[0]
    
    print("=" * 80)
    print(f"Adding Text Overlays: Chapter 1 - {ch.get('chapter_title', 'N/A')}")
    print("=" * 80)
    
    # Initialize text overlay
    overlay = ComicTextOverlay()
    
    # Process each page
    total_processed = 0
    for scene in ch.get('scenes', []):
        scene_num = scene.get('scene_number')
        
        for page in scene.get('pages', []):
            page_num = page.get('page_number')
            panel_arrangement = page.get('panel_arrangement')
            panels = page.get('panels', [])
            
            # Find image file
            image_file = pages_dir / f"ch1_sc{scene_num}_page{page_num}.png"
            
            if not image_file.exists():
                print(f"⚠️  Image not found: {image_file.name}")
                continue
            
            print(f"\n📝 Processing Page {page_num} (Scene {scene_num})...")
            print(f"   Layout: {panel_arrangement}")
            print(f"   Panels: {len(panels)}")
            
            # Check if there's any text to add
            has_text = False
            for panel in panels:
                if panel.get('dialogue') or panel.get('narration'):
                    has_text = True
                    break
            
            if not has_text:
                print(f"   ⊙ No text to add, skipping")
                continue
            
            # Load image
            img = Image.open(image_file)
            
            # Add text overlays
            img_with_text = overlay.add_text_to_page(
                img,
                panels,
                panel_arrangement,
                (img.width, img.height)
            )
            
            # Save with suffix
            output_file = pages_dir / f"ch1_sc{scene_num}_page{page_num}{output_suffix}.png"
            img_with_text.save(output_file)
            
            print(f"   ✅ Saved: {output_file.name}")
            total_processed += 1
    
    print("\n" + "=" * 80)
    print(f"✅ Text overlays added to {total_processed} pages")
    print(f"   Output directory: {pages_dir}/")
    print(f"   Files: *{output_suffix}.png")
    print("=" * 80)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python add_text_to_pages.py <workflow_id> [output_suffix]")
        print("Example: python add_text_to_pages.py 6021a791")
        print("         python add_text_to_pages.py 6021a791 _final")
        sys.exit(1)
    
    workflow_id = sys.argv[1]
    output_suffix = sys.argv[2] if len(sys.argv) > 2 else "_with_text"
    
    add_text_to_pages(workflow_id, output_suffix)
