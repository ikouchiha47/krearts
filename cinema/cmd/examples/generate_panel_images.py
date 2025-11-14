"""
Generate images for the first 10 panels from existing chapter JSON files.

Usage:
    python -m cinema.cmd.examples.generate_panel_images
"""

import asyncio
import json
import logging
import os
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables FIRST
load_dotenv()

# Google GenAI SDK expects GOOGLE_API_KEY, but we use GEMINI_API_KEY
if 'GEMINI_API_KEY' in os.environ and 'GOOGLE_API_KEY' not in os.environ:
    os.environ['GOOGLE_API_KEY'] = os.environ['GEMINI_API_KEY']

# Now import after setting env vars
from cinema.providers.gemini import GeminiMediaGen
from cinema.utils.rate_limiter import RateLimiterManager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def generate_panel_images(
    chapter_json_path: str,
    output_dir: str,
    max_panels: int = 10
):
    """
    Generate images for panels from a chapter JSON file.
    
    Args:
        chapter_json_path: Path to the chapter JSON file
        output_dir: Directory to save generated images
        max_panels: Maximum number of panels to generate (default: 10)
    """
    # Load chapter JSON
    logger.info(f"Loading chapter from: {chapter_json_path}")
    with open(chapter_json_path, 'r') as f:
        chapter_data = json.load(f)
    
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    logger.info(f"Output directory: {output_path}")
    
    # Initialize Gemini client
    # Note: GeminiMediaGen expects GOOGLE_API_KEY to be set in environment
    # We already set it from GEMINI_API_KEY at module level
    rate_limiter = RateLimiterManager()
    
    # Create a custom GeminiMediaGen instance with explicit API key
    from google import genai
    api_key = os.environ.get('GEMINI_API_KEY')
    
    gemini = GeminiMediaGen(rate_limiter=rate_limiter)
    # Override the client with one that has explicit API key
    gemini.client = genai.Client(api_key=api_key)
    
    # Extract panels from chapter
    panels = []
    chapter_title = chapter_data.get("title", "Unknown")
    logger.info(f"Chapter: {chapter_title}")
    
    # Navigate through chapters -> scenes -> pages -> panels
    for chapter in chapter_data.get("chapters", []):
        chapter_num = chapter.get("chapter_number", 0)
        logger.info(f"Processing Chapter {chapter_num}")
        
        for scene in chapter.get("scenes", []):
            scene_num = scene.get("scene_number", 0)
            
            for page in scene.get("pages", []):
                page_num = page.get("page_number", 0)
                
                for panel in page.get("panels", []):
                    panel_num = panel.get("panel_number", 0)
                    visual_desc = panel.get("visual_description", "")
                    
                    if visual_desc:
                        panels.append({
                            "chapter": chapter_num,
                            "scene": scene_num,
                            "page": page_num,
                            "panel": panel_num,
                            "visual_description": visual_desc,
                            "shot_type": panel.get("shot_type", "unknown"),
                            "location": panel.get("location", "unknown"),
                        })
                    
                    if len(panels) >= max_panels:
                        break
                if len(panels) >= max_panels:
                    break
            if len(panels) >= max_panels:
                break
        if len(panels) >= max_panels:
            break
    
    logger.info(f"Found {len(panels)} panels to generate")
    
    # Generate images for each panel
    for i, panel in enumerate(panels, 1):
        logger.info("=" * 80)
        logger.info(f"Generating Panel {i}/{len(panels)}")
        logger.info(f"  Chapter: {panel['chapter']}, Scene: {panel['scene']}, "
                   f"Page: {panel['page']}, Panel: {panel['panel']}")
        logger.info(f"  Shot Type: {panel['shot_type']}")
        logger.info(f"  Location: {panel['location']}")
        
        # Use visual_description as prompt
        prompt = panel['visual_description']
        logger.info(f"  Prompt: {prompt[:100]}...")
        
        try:
            # Generate image
            response = await gemini.generate_content(
                prompt=prompt,
                reference_image=None
            )
            
            # Save image
            filename = f"ch{panel['chapter']}_sc{panel['scene']}_pg{panel['page']}_panel{panel['panel']}.png"
            output_file = output_path / filename
            
            gemini.render_image(str(output_file), response)
            logger.info(f"  ✅ Saved: {filename}")
            
        except Exception as e:
            logger.error(f"  ❌ Failed to generate panel {panel['panel']}: {e}")
            continue
    
    logger.info("=" * 80)
    logger.info(f"✅ Generated {len(panels)} panel images in {output_path}")


async def main():
    """Main entry point"""
    # Use the complete chapter from detective_ce8f9a4a
    chapter_json = "output/detective_ce8f9a4a/chapter_01.json"
    output_dir = "output/detective_ce8f9a4a/images"
    
    logger.info("🎨 Starting panel image generation")
    logger.info(f"Chapter JSON: {chapter_json}")
    logger.info(f"Output directory: {output_dir}")
    logger.info(f"Max panels: 10")
    
    await generate_panel_images(
        chapter_json_path=chapter_json,
        output_dir=output_dir,
        max_panels=10
    )
    
    logger.info("🎉 Done!")


if __name__ == "__main__":
    asyncio.run(main())
