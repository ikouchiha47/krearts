#!/usr/bin/env python3
"""
Review generated pages - display info and open for visual inspection.
"""
import json
import sys
from pathlib import Path
from PIL import Image

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


def review_pages(workflow_id: str):
    """Review generated pages with metadata."""
    
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
    print(f"CHAPTER 1 REVIEW: {ch.get('chapter_title', 'N/A')}")
    print("=" * 80)
    print(f"Summary: {ch.get('chapter_summary', 'N/A')[:200]}...")
    print()
    
    # Review each page
    for scene in ch.get('scenes', []):
        scene_num = scene.get('scene_number')
        
        for page in scene.get('pages', []):
            page_num = page.get('page_number')
            panel_arrangement = page.get('panel_arrangement')
            panels = page.get('panels', [])
            
            # Find corresponding image
            image_file = pages_dir / f"ch1_sc{scene_num}_page{page_num}.png"
            
            print(f"\n{'='*80}")
            print(f"PAGE {page_num} (Scene {scene_num})")
            print(f"{'='*80}")
            print(f"Layout: {panel_arrangement} ({len(panels)} panels)")
            print(f"Description: {page.get('page_description', 'N/A')}")
            
            if image_file.exists():
                img = Image.open(image_file)
                print(f"\n📸 Image: {image_file.name}")
                print(f"   Size: {img.size[0]}x{img.size[1]} ({img.size[0]/img.size[1]:.3f} ratio)")
                print(f"   File size: {image_file.stat().st_size / 1024:.1f} KB")
                print(f"   Mode: {img.mode}")
            else:
                print(f"\n❌ Image not found: {image_file.name}")
            
            # Panel details
            print(f"\n   Panels:")
            for i, panel in enumerate(panels, 1):
                visual_desc = panel.get('visual_description', '')[:100]
                dialogue = panel.get('dialogue', [])
                chars = panel.get('characters_present', [])
                
                print(f"\n   Panel {i}:")
                print(f"      Shot: {panel.get('shot_type')} / {panel.get('camera_angle')}")
                print(f"      Characters: {', '.join(chars) if chars else 'None'}")
                print(f"      Visual: {visual_desc}...")
                
                if dialogue:
                    print(f"      Dialogue:")
                    for d in dialogue:
                        char = d.get('character', 'Unknown')
                        text = d.get('text', '')[:60]
                        print(f"         {char}: \"{text}...\"")
    
    print("\n" + "=" * 80)
    print("REVIEW COMPLETE")
    print("=" * 80)
    print(f"\nTo view images, open: {pages_dir}/")
    print("Use Preview/Finder to visually inspect the generated pages.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python review_pages.py <workflow_id>")
        print("Example: python review_pages.py 6021a791")
        sys.exit(1)
    
    workflow_id = sys.argv[1]
    review_pages(workflow_id)
