"""
Generate multi-panel comic book pages from chapter JSON files.

This script:
1. Reads chapter JSON with page/panel structure
2. Generates individual panel images
3. Composites them into full multi-panel pages according to layout

Usage:
    python -m cinema.cmd.examples.generate_comic_pages [DETECTIVE_ID] [CHAPTER_NUM] [MAX_PAGES]
"""

import asyncio
import json
import logging
import os
from io import BytesIO
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from PIL import Image, ImageDraw, ImageFont

# Load environment variables
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# Panel layout configurations (width ratios for different arrangements)
LAYOUT_CONFIGS = {
    "horizontal-2-panel": {"rows": 1, "cols": 2, "ratios": [[1, 1]]},
    "horizontal-3-panel": {"rows": 1, "cols": 3, "ratios": [[1, 1, 1]]},
    "vertical-2-panel": {"rows": 2, "cols": 1, "ratios": [[1], [1]]},
    "vertical-3-panel": {"rows": 3, "cols": 1, "ratios": [[1], [1], [1]]},
    "zoom-progression": {"rows": 3, "cols": 1, "ratios": [[1], [1], [1]]},
    "dynamic-grid": {"rows": 2, "cols": 2, "ratios": [[1, 1], [1, 1]]},
}


async def generate_panel_image(client: genai.Client, prompt: str) -> Image.Image:
    """Generate a single panel image using Gemini."""
    logger.info(f"📝 PROMPT: {prompt}")
    
    response = await asyncio.to_thread(
        client.models.generate_content,
        model="gemini-2.5-flash-image",
        contents=prompt,
        config={"response_modalities": ["IMAGE"]},
    )
    
    # Extract image from response
    for part in response.candidates[0].content.parts:
        if part.inline_data is not None:
            img = Image.open(BytesIO(part.inline_data.data))
            return img
    
    raise Exception("No image data in response")


def composite_page(panel_images: list[Image.Image], layout: str, page_size=(1200, 1600)) -> Image.Image:
    """
    Composite multiple panel images into a single comic page.
    
    Args:
        panel_images: List of PIL Images for each panel
        layout: Panel arrangement type (e.g., "horizontal-2-panel")
        page_size: Final page size (width, height)
    
    Returns:
        Composited page image
    """
    page_width, page_height = page_size
    config = LAYOUT_CONFIGS.get(layout, LAYOUT_CONFIGS["vertical-2-panel"])
    
    # Create blank page
    page = Image.new('RGB', (page_width, page_height), color='white')
    
    rows = config["rows"]
    cols = config["cols"]
    gutter = 20  # Space between panels
    
    # Calculate panel dimensions
    panel_height = (page_height - (rows + 1) * gutter) // rows
    panel_width = (page_width - (cols + 1) * gutter) // cols
    
    # Place panels
    panel_idx = 0
    for row in range(rows):
        for col in range(cols):
            if panel_idx >= len(panel_images):
                break
            
            # Calculate position
            x = gutter + col * (panel_width + gutter)
            y = gutter + row * (panel_height + gutter)
            
            # Resize and paste panel
            panel = panel_images[panel_idx].resize((panel_width, panel_height), Image.Resampling.LANCZOS)
            page.paste(panel, (x, y))
            
            panel_idx += 1
    
    return page


async def generate_comic_page(
    client: genai.Client,
    page_data: dict,
    output_file: str
) -> Image.Image:
    """Generate a complete multi-panel comic page."""
    panel_arrangement = page_data.get("panel_arrangement", "vertical-2-panel")
    panels = page_data.get("panels", [])
    
    logger.info(f"  Generating page with {len(panels)} panels ({panel_arrangement})")
    
    # Generate all panel images
    panel_images = []
    for i, panel in enumerate(panels, 1):
        logger.info(f"    Panel {i}/{len(panels)}...")
        visual_desc = panel.get("visual_description", "")
        
        if not visual_desc:
            logger.warning(f"    Panel {i} has no visual description, skipping")
            continue
        
        try:
            panel_img = await generate_panel_image(client, visual_desc)
            panel_images.append(panel_img)
        except Exception as e:
            logger.error(f"    Failed to generate panel {i}: {e}")
            # Create placeholder
            placeholder = Image.new('RGB', (800, 600), color='gray')
            panel_images.append(placeholder)
    
    # Composite into page
    logger.info(f"  Compositing {len(panel_images)} panels into page...")
    page_image = composite_page(panel_images, panel_arrangement)
    
    # Save page
    page_image.save(output_file)
    logger.info(f"  ✅ Saved: {output_file}")
    
    return page_image


async def main():
    """Main entry point"""
    import sys
    
    # Get detective ID from command line or use default
    if len(sys.argv) > 1:
        detective_id = sys.argv[1]
    else:
        detective_id = "detective_ce8f9a4a"
        logger.info(f"No detective ID provided, using default: {detective_id}")
    
    # Get chapter number from command line or use default
    if len(sys.argv) > 2:
        chapter_num = int(sys.argv[2])
    else:
        chapter_num = 1
        logger.info(f"No chapter number provided, using default: {chapter_num}")
    
    # Get max pages from command line or use default
    if len(sys.argv) > 3:
        max_pages = int(sys.argv[3])
    else:
        max_pages = 3
    
    # Configuration
    chapter_json = f"output/{detective_id}/chapter_{chapter_num:02d}.json"
    output_dir = f"output/{detective_id}/pages"
    
    logger.info("🎨 Starting multi-panel comic page generation")
    logger.info(f"Detective ID: {detective_id}")
    logger.info(f"Chapter JSON: {chapter_json}")
    logger.info(f"Output directory: {output_dir}")
    logger.info(f"Max pages: {max_pages}")
    
    # Load chapter JSON
    logger.info(f"Loading chapter from: {chapter_json}")
    with open(chapter_json, 'r') as f:
        chapter_data = json.load(f)
    
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Initialize Gemini client with explicit API key
    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in environment")
    
    client = genai.Client(api_key=api_key)
    logger.info("✅ Gemini client initialized")
    
    # Extract pages from chapter
    pages = []
    chapter_title = chapter_data.get("title", "Unknown")
    logger.info(f"Chapter: {chapter_title}")
    
    for chapter in chapter_data.get("chapters", []):
        chapter_num_data = chapter.get("chapter_number", 0)
        logger.info(f"Processing Chapter {chapter_num_data}")
        
        for scene in chapter.get("scenes", []):
            scene_num = scene.get("scene_number", 0)
            
            for page in scene.get("pages", []):
                page_num = page.get("page_number", 0)
                
                pages.append({
                    "chapter": chapter_num_data,
                    "scene": scene_num,
                    "page": page_num,
                    "data": page
                })
                
                if len(pages) >= max_pages:
                    break
            if len(pages) >= max_pages:
                break
        if len(pages) >= max_pages:
            break
    
    logger.info(f"Found {len(pages)} pages to generate")
    
    # Generate pages
    for i, page_info in enumerate(pages, 1):
        logger.info("=" * 80)
        logger.info(f"Page {i}/{len(pages)}")
        logger.info(f"  Ch{page_info['chapter']} Sc{page_info['scene']} Page{page_info['page']}")
        
        filename = f"ch{page_info['chapter']}_sc{page_info['scene']}_page{page_info['page']}.png"
        output_file = output_path / filename
        
        try:
            await generate_comic_page(
                client=client,
                page_data=page_info['data'],
                output_file=str(output_file)
            )
        except Exception as e:
            logger.error(f"  ❌ Failed: {e}")
            continue
    
    logger.info("=" * 80)
    logger.info(f"🎉 Generated {len(pages)} multi-panel pages in {output_path}")


if __name__ == "__main__":
    asyncio.run(main())
