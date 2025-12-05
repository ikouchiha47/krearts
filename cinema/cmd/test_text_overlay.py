#!/usr/bin/env python3
"""
Standalone CLI for testing text overlay placement.

Usage:
    python cinema/cmd/test_text_overlay.py <workflow_id> --chapter 3 --page 1
    python cinema/cmd/test_text_overlay.py <workflow_id> --chapter 3 --pages 1,2,3
    python cinema/cmd/test_text_overlay.py <workflow_id> --chapter 3 --all

This tool:
1. Loads chapter JSON
2. Generates page images (or uses cached)
3. Detects bounding boxes per panel
4. Applies text overlays
5. Saves results for comparison

No state management - just pure image generation and text overlay testing.
"""
import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from typing import List, Optional

import click
from PIL import Image
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from cinema.providers.gemini import GeminiMediaGen
from cinema.utils.comic_text_overlay import ComicTextOverlay
from cinema.utils.draw_bounding_boxes import draw_bounding_boxes_from_json

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)


class TextOverlayTester:
    """Test text overlay placement without state management."""
    
    def __init__(self, workflow_id: str, output_dir: Optional[str] = None):
        self.workflow_id = workflow_id
        self.output_dir = output_dir or f"output/book_{workflow_id}"
        self.test_output_dir = Path(self.output_dir) / "text_overlay_tests"
        self.test_output_dir.mkdir(parents=True, exist_ok=True)
        
        # Check for API key
        if not os.environ.get('GEMINI_API_KEY'):
            raise ValueError("GEMINI_API_KEY not found in environment. Please set it in .env file.")
        
        self.gemini = GeminiMediaGen()
        self.overlay = ComicTextOverlay()
    
    async def regenerate_chapter(self, chapter_num: int):
        """Regenerate chapter JSON using ChapterBuilder."""
        logger.info(f"\n{'='*80}")
        logger.info(f"Regenerating Chapter {chapter_num} JSON")
        logger.info(f"{'='*80}\n")
        
        from cinema.context import DirectorsContext
        from cinema.registry import OpenAiHerd
        from cinema.agents.bookwriter.crew import ChapterBuilder
        from cinema.models.novel import Novel
        
        # Load novel
        novel_file = Path(self.output_dir) / "novel.md"
        if not novel_file.exists():
            raise FileNotFoundError(f"Novel not found: {novel_file}")
        
        novel_text = novel_file.read_text()
        novel = Novel.from_str(novel_text)
        
        if chapter_num > len(novel.chapters):
            raise ValueError(f"Chapter {chapter_num} not found. Novel has {len(novel.chapters)} chapters.")
        
        chapter = novel.chapters[chapter_num - 1]
        
        logger.info(f"📖 Chapter: {chapter.title}")
        logger.info(f"   Content length: {len(chapter.content)} chars")
        
        # Initialize context
        ctx = DirectorsContext(llmstore=OpenAiHerd, debug=False)
        
        # Create ChapterBuilder
        output_file = Path(self.output_dir) / f"chapter_{chapter_num:02d}.json"
        chapter_builder = ChapterBuilder(
            ctx=ctx,
            outfile=str(output_file),
            use_mock=False
        )
        
        # Prepare inputs
        inputs = {
            "screenplay": novel_text,
            "examples": ChapterBuilder.load_examples(),
            "chapter_id": chapter_num,
            "chapter_content": chapter.content,
            "art_style": "Print Comic Noir Style with Halftones",
            "aspect_ratio": "4:5"
        }
        
        logger.info(f"🎬 Running ChapterBuilder...")
        
        # Run crew
        crew = chapter_builder.crew()
        result = await crew.kickoff_async(inputs=inputs)
        
        logger.info(f"✅ Chapter JSON generated: {output_file.name}")
        
        return output_file
    
    def load_chapter(self, chapter_num: int) -> dict:
        """Load chapter JSON."""
        chapter_file = Path(self.output_dir) / f"chapter_{chapter_num:02d}.json"
        if not chapter_file.exists():
            raise FileNotFoundError(f"Chapter file not found: {chapter_file}")
        
        with open(chapter_file, 'r') as f:
            return json.load(f)
    
    def get_page_info(self, chapter_data: dict, page_num: int) -> Optional[dict]:
        """Get page data from chapter."""
        for chapter in chapter_data.get('chapters', []):
            for scene in chapter.get('scenes', []):
                for page in scene.get('pages', []):
                    if page.get('page_number') == page_num:
                        return {
                            'chapter_number': chapter.get('chapter_number'),
                            'scene_number': scene.get('scene_number'),
                            'page_number': page_num,
                            'page_data': page
                        }
        return None
    
    async def generate_page_image(self, page_info: dict, force: bool = False, gemini_text: bool = False) -> Path:
        """Generate page image (or use cached)."""
        ch_num = page_info['chapter_number']
        sc_num = page_info['scene_number']
        pg_num = page_info['page_number']
        
        filename = f"ch{ch_num}_sc{sc_num}_page{pg_num}.png"
        clean_filename = f"ch{ch_num}_sc{sc_num}_page{pg_num}_clean.png"
        output_file = self.test_output_dir / filename
        clean_output_file = self.test_output_dir / clean_filename
        
        if output_file.exists() and not force:
            logger.info(f"✅ Using cached image: {filename}")
            return output_file
        
        logger.info(f"🎨 Generating image: {filename}")
        
        # Build prompt from page data
        page_data = page_info['page_data']
        panels = page_data.get('panels', [])
        panel_arrangement = page_data.get('panel_arrangement', 'vertical-2-panel')
        
        prompt_lines = [
            f"COMIC PAGE GENERATION",
            f"",
            f"Layout: 4:5 portrait, {panel_arrangement}",
            f"Panels: {len(panels)}",
            f"",
        ]
        
        # Always generate clean image first (no text)
        prompt_lines.append(f"IMPORTANT: NO text, speech bubbles, or caption boxes")
        
        prompt_lines.append(f"")
        prompt_lines.append(f"PANELS:")
        
        for i, panel in enumerate(panels, 1):
            visual_desc = panel.get('visual_description', '')
            # Strip redundant info
            visual_desc = visual_desc.replace("A single comic book panel in Print Comic Noir Style. ", "")
            visual_desc = visual_desc.replace("Portrait 4:5.", "").strip()
            
            shot = panel.get('shot_type', '')
            angle = panel.get('camera_angle', '')
            
            prompt_lines.append(f"{i}. [{shot} shot, {angle}] {visual_desc}")
        
        prompt = "\n".join(prompt_lines)
        
        # Stage 1: Generate clean image using GeminiMediaGen
        response = await self.gemini.generate_content(
            prompt=prompt,
            aspect_ratio="4:5"
        )
        
        # Save clean image using GeminiMediaGen's render method
        generated_image = self.gemini.render_image(str(clean_output_file), response)
        logger.info(f"✅ Saved clean image: {clean_filename}")
        
        # Stage 2: Add text if requested
        if gemini_text:
            logger.info(f"📝 Adding text to image (controlled placement)...")
            image_with_text = await self.gemini.add_text_to_image(
                generated_image,
                panels
            )
            image_with_text.save(output_file)
            logger.info(f"✅ Saved with text: {filename}")
            return output_file
        else:
            # No text - just use clean image
            generated_image.save(output_file)
            logger.info(f"✅ Saved: {filename}")
            return output_file
    
    async def detect_bounding_boxes(self, image_path: Path, page_info: dict) -> List[dict]:
        """Detect caption boxes and text elements in the image."""
        logger.info(f"🔍 Detecting caption boxes and text elements...")
        
        image = Image.open(image_path)
        page_data = page_info['page_data']
        panels = page_data.get('panels', [])
        panel_arrangement = page_data.get('panel_arrangement', 'vertical-2-panel')
        
        # Split into panels
        panel_images = self._split_page_into_panels(image, panel_arrangement, len(panels))
        
        all_detections = []
        
        for i, (panel_img, panel_data) in enumerate(zip(panel_images, panels)):
            panel_num = panel_data.get('panel_number', i + 1)
            
            logger.info(f"  Panel {panel_num}: Detecting text elements...")
            
            try:
                # Detect caption boxes instead of objects
                detections = await self.gemini.detect_caption_boxes(panel_img)
                
                if detections:
                    # Map to page coordinates
                    panel_offset = self._get_panel_offset(i, panel_arrangement, image.size, len(panels))
                    
                    for detection in detections:
                        box_2d = detection.get('box_2d', [])
                        if len(box_2d) == 4:
                            detection['box_2d'] = self._map_panel_to_page_coords(
                                box_2d, panel_offset, panel_img.size, image.size
                            )
                            detection['panel_number'] = panel_num
                            all_detections.append(detection)
                    
                    logger.info(f"  Panel {panel_num}: ✅ {len(detections)} objects")
            except Exception as e:
                logger.error(f"  Panel {panel_num}: ❌ {e}")
        
        # Save caption detections
        detection_file = image_path.with_suffix('.captions.json')
        with open(detection_file, 'w') as f:
            json.dump({
                'image': image_path.name,
                'panel_arrangement': panel_arrangement,
                'num_panels': len(panels),
                'caption_boxes': all_detections,
                'detection_type': 'caption_boxes'
            }, f, indent=2)
        
        logger.info(f"✅ Saved caption detections: {detection_file.name}")
        
        return all_detections
    
    def _split_page_into_panels(self, image, panel_arrangement: str, num_panels: int):
        """Split page into panels."""
        width, height = image.size
        panels = []
        
        if 'vertical' in panel_arrangement:
            panel_height = height // num_panels
            for i in range(num_panels):
                y1 = i * panel_height
                y2 = (i + 1) * panel_height if i < num_panels - 1 else height
                panel = image.crop((0, y1, width, y2))
                panels.append(panel)
        elif 'horizontal' in panel_arrangement:
            panel_width = width // num_panels
            for i in range(num_panels):
                x1 = i * panel_width
                x2 = (i + 1) * panel_width if i < num_panels - 1 else width
                panel = image.crop((x1, 0, x2, height))
                panels.append(panel)
        else:
            panels.append(image)
        
        return panels
    
    def _get_panel_offset(self, panel_index: int, panel_arrangement: str, page_size: tuple, num_panels: int) -> tuple:
        """Get panel offset."""
        width, height = page_size
        
        if 'vertical' in panel_arrangement:
            panel_height = height // num_panels
            return (0, panel_index * panel_height)
        elif 'horizontal' in panel_arrangement:
            panel_width = width // num_panels
            return (panel_index * panel_width, 0)
        else:
            return (0, 0)
    
    def _map_panel_to_page_coords(self, box_2d: list, panel_offset: tuple, panel_size: tuple, page_size: tuple) -> list:
        """Map panel coords to page coords."""
        y_min, x_min, y_max, x_max = box_2d
        offset_x, offset_y = panel_offset
        panel_width, panel_height = panel_size
        page_width, page_height = page_size
        
        panel_x1 = x_min * panel_width / 1000
        panel_y1 = y_min * panel_height / 1000
        panel_x2 = x_max * panel_width / 1000
        panel_y2 = y_max * panel_height / 1000
        
        page_x1 = panel_x1 + offset_x
        page_y1 = panel_y1 + offset_y
        page_x2 = panel_x2 + offset_x
        page_y2 = panel_y2 + offset_y
        
        norm_x_min = int(page_x1 * 1000 / page_width)
        norm_y_min = int(page_y1 * 1000 / page_height)
        norm_x_max = int(page_x2 * 1000 / page_width)
        norm_y_max = int(page_y2 * 1000 / page_height)
        
        return [norm_y_min, norm_x_min, norm_y_max, norm_x_max]
    
    def apply_text_overlay(self, image_path: Path, page_info: dict, detections: List[dict]) -> Path:
        """Apply text overlay to image."""
        logger.info(f"📝 Applying text overlay...")
        
        img = Image.open(image_path)
        page_data = page_info['page_data']
        
        # Process each panel
        for panel in page_data.get('panels', []):
            img = self.overlay.add_text_to_panel(img, panel, detections)
        
        # Save with text
        output_file = image_path.parent / f"{image_path.stem}_with_text.png"
        img.save(output_file)
        logger.info(f"✅ Saved with text: {output_file.name}")
        
        return output_file
    
    def create_comparison(self, image_path: Path):
        """Create comparison image with caption boxes visualized."""
        logger.info(f"📊 Creating comparison images...")
        
        # Draw caption boxes
        caption_file = image_path.with_suffix('.captions.json')
        if caption_file.exists():
            annotated_file = image_path.parent / f"{image_path.stem}_captions_annotated.png"
            self._draw_caption_boxes(image_path, caption_file, annotated_file)
            logger.info(f"✅ Saved annotated: {annotated_file.name}")
    
    def _draw_caption_boxes(self, image_path: Path, caption_file: Path, output_path: Path):
        """Draw bounding boxes around detected caption boxes."""
        from PIL import ImageDraw, ImageFont
        
        img = Image.open(image_path)
        draw = ImageDraw.Draw(img)
        
        with open(caption_file, 'r') as f:
            data = json.load(f)
        
        captions = data.get('caption_boxes', [])
        img_width, img_height = img.size
        
        # Color code by type
        colors = {
            'narration_caption': 'yellow',
            'speech_bubble': 'green',
            'thought_bubble': 'blue',
            'text_on_object': 'orange'
        }
        
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 16)
        except:
            font = ImageFont.load_default()
        
        for caption in captions:
            box_2d = caption.get('box_2d', [])
            if len(box_2d) != 4:
                continue
            
            y_min, x_min, y_max, x_max = box_2d
            
            # Convert to pixels
            x1 = int(x_min * img_width / 1000)
            y1 = int(y_min * img_height / 1000)
            x2 = int(x_max * img_width / 1000)
            y2 = int(y_max * img_height / 1000)
            
            # Get color for type
            caption_type = caption.get('type', 'unknown')
            color = colors.get(caption_type, 'red')
            
            # Draw box
            draw.rectangle([(x1, y1), (x2, y2)], outline=color, width=3)
            
            # Draw label
            text = caption.get('text', '')[:30]
            label = f"{caption_type}: {text}..."
            bbox = draw.textbbox((x1, y1 - 20), label, font=font)
            draw.rectangle(bbox, fill=color)
            draw.text((x1, y1 - 20), label, fill='white', font=font)
        
        img.save(output_path)
        logger.info(f"Drew {len(captions)} caption boxes")
    
    async def test_page(self, chapter_num: int, page_num: int, force_regenerate: bool = False, regenerate_chapter: bool = False, gemini_text: bool = False):
        """Test a single page."""
        logger.info(f"\n{'='*80}")
        logger.info(f"Testing Chapter {chapter_num}, Page {page_num}")
        if gemini_text:
            logger.info(f"Mode: Two-stage generation (clean image + controlled text)")
            logger.info(f"  - Narration: Creative liberty")
            logger.info(f"  - Speech/Thought: EXACT text from JSON")
        else:
            logger.info(f"Mode: Clean image only (no text)")
        logger.info(f"{'='*80}\n")
        
        # Regenerate chapter if requested
        if regenerate_chapter:
            await self.regenerate_chapter(chapter_num)
        
        # Load chapter
        chapter_data = self.load_chapter(chapter_num)
        
        # Get page info
        page_info = self.get_page_info(chapter_data, page_num)
        if not page_info:
            logger.error(f"❌ Page {page_num} not found in chapter {chapter_num}")
            return
        
        # Generate image (two-stage if gemini_text=True)
        image_path = await self.generate_page_image(page_info, force=force_regenerate, gemini_text=gemini_text)
        
        logger.info(f"\n{'='*80}")
        logger.info(f"✅ Complete! Output in: {self.test_output_dir}")
        logger.info(f"{'='*80}\n")
        logger.info(f"Files created:")
        
        clean_path = image_path.parent / f"{image_path.stem.replace('_page', '_page')}_clean.png"
        if clean_path.exists():
            logger.info(f"  - {clean_path.name} (clean image without text)")
        
        if gemini_text:
            logger.info(f"  - {image_path.name} (with controlled text)")
        else:
            logger.info(f"  - {image_path.name} (clean image only)")


@click.command()
@click.argument('workflow_id')
@click.option('--chapter', '-c', type=int, required=True, help='Chapter number')
@click.option('--page', '-p', type=int, help='Single page number')
@click.option('--pages', help='Comma-separated page numbers (e.g., 1,2,3)')
@click.option('--all', 'all_pages', is_flag=True, help='Test all pages in chapter')
@click.option('--force', '-f', is_flag=True, help='Force regenerate images')
@click.option('--regenerate-chapter', is_flag=True, help='Regenerate chapter JSON before testing')
@click.option('--gemini-text', is_flag=True, help='Use two-stage generation: clean image + controlled text (narration=creative, dialogue=exact)')
def main(workflow_id: str, chapter: int, page: Optional[int], pages: Optional[str], all_pages: bool, force: bool, regenerate_chapter: bool, gemini_text: bool):
    """
    Test text overlay placement with two-stage generation.
    
    Two-stage approach:
      1. Generate clean image (no text)
      2. Add text with control:
         - Narration: Creative liberty (noir style)
         - Speech/Thought: EXACT text from JSON
    
    Examples:
        # Generate clean image only (no text)
        python cinema/cmd/test_text_overlay.py 43e21caa --chapter 3 --page 5
        
        # Generate with controlled text (two-stage)
        python cinema/cmd/test_text_overlay.py 43e21caa -c 3 -p 5 --gemini-text
        
        # Test multiple pages
        python cinema/cmd/test_text_overlay.py 43e21caa -c 3 --pages 1,2,3 --gemini-text
        
        # Regenerate chapter JSON first, then test
        python cinema/cmd/test_text_overlay.py 43e21caa -c 3 --page 1 --regenerate-chapter --gemini-text
        
        # Force regenerate images even if cached
        python cinema/cmd/test_text_overlay.py 43e21caa -c 3 --page 1 --force --gemini-text
    """
    tester = TextOverlayTester(workflow_id)
    
    # Determine which pages to test
    page_nums = []
    if page:
        page_nums = [page]
    elif pages:
        page_nums = [int(p.strip()) for p in pages.split(',')]
    elif all_pages:
        # Load chapter to get all pages
        chapter_data = tester.load_chapter(chapter)
        for ch in chapter_data.get('chapters', []):
            for scene in ch.get('scenes', []):
                for pg in scene.get('pages', []):
                    page_nums.append(pg.get('page_number'))
    else:
        click.echo("Error: Must specify --page, --pages, or --all")
        sys.exit(1)
    
    # Test each page
    async def run_tests():
        for i, page_num in enumerate(page_nums):
            # Only regenerate chapter once (on first page)
            regen_ch = regenerate_chapter and i == 0
            await tester.test_page(chapter, page_num, force_regenerate=force, regenerate_chapter=regen_ch, gemini_text=gemini_text)
    
    asyncio.run(run_tests())


if __name__ == '__main__':
    main()
