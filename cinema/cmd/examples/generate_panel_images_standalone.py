"""
Generate images for the first 10 panels from existing chapter JSON files.
Standalone version that doesn't use GeminiMediaGen wrapper.

Usage:
    python -m cinema.cmd.examples.generate_panel_images_standalone
"""

import asyncio
import json
import logging
import os
from io import BytesIO
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from PIL import Image

# Load environment variables
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def generate_panel_image(client: genai.Client, prompt: str, output_file: str):
    """Generate a single panel image using Gemini."""
    logger.info("📸 Generating image...")
    logger.debug(f"Prompt: {prompt[:100]}...")
    
    response = await asyncio.to_thread(
        client.models.generate_content,
        model="gemini-2.5-flash-image",
        contents=prompt,
        config={"response_modalities": ["IMAGE"]},
    )
    
    # Save image
    for part in response.candidates[0].content.parts:
        if part.inline_data is not None:
            img = Image.open(BytesIO(part.inline_data.data))
            img.save(output_file)
            logger.info(f"💾 Saved: {output_file}")
            return img
    
    raise Exception("No image data in response")


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
    
    # Get max panels from command line or use default
    if len(sys.argv) > 3:
        max_panels = int(sys.argv[3])
    else:
        max_panels = 10
    
    # Configuration
    chapter_json = f"output/{detective_id}/chapter_{chapter_num:02d}.json"
    output_dir = f"output/{detective_id}/images"
    
    logger.info("🎨 Starting panel image generation")
    logger.info(f"Detective ID: {detective_id}")
    logger.info(f"Chapter JSON: {chapter_json}")
    logger.info(f"Output directory: {output_dir}")
    logger.info(f"Max panels: {max_panels}")
    
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
    
    # Extract panels
    panels = []
    chapter_title = chapter_data.get("title", "Unknown")
    logger.info(f"Chapter: {chapter_title}")
    
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
    
    # Generate images
    for i, panel in enumerate(panels, 1):
        logger.info("=" * 80)
        logger.info(f"Panel {i}/{len(panels)}")
        logger.info(f"  Ch{panel['chapter']} Sc{panel['scene']} Pg{panel['page']} Panel{panel['panel']}")
        logger.info(f"  Shot: {panel['shot_type']}, Location: {panel['location']}")
        
        filename = f"ch{panel['chapter']}_sc{panel['scene']}_pg{panel['page']}_panel{panel['panel']}.png"
        output_file = output_path / filename
        
        try:
            await generate_panel_image(
                client=client,
                prompt=panel['visual_description'],
                output_file=str(output_file)
            )
        except Exception as e:
            logger.error(f"  ❌ Failed: {e}")
            continue
    
    logger.info("=" * 80)
    logger.info(f"🎉 Generated {len(panels)} images in {output_path}")


if __name__ == "__main__":
    asyncio.run(main())
