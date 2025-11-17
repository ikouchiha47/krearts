#!/usr/bin/env python3
"""
Test using the EXACT code from the documentation.
"""

import logging
import time
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_image(path: str) -> types.ImageDict:
    """Load image as ImageDict"""
    with open(path, "rb") as f:
        data = f.read()
    return {
        "mime_type": "image/png",
        "image_bytes": data,
    }

def test_exact_docs_example():
    """Test using exact code from docs"""
    
    client = genai.Client()
    
    # Load images as ImageDict
    first_image = load_image("output/d40db751/images/S2_DISCOVERY_first_frame.png")
    last_image = load_image("output/d40db751/images/S2_DISCOVERY_last_frame.png")
    
    prompt = "A smooth transition showing a phone screen with app icons"
    
    logger.info("Testing with EXACT docs example...")
    
    try:
        # EXACT code from docs
        operation = client.models.generate_videos(
            model="veo-3.1-generate-preview",
            prompt=prompt,
            image=first_image,
            config=types.GenerateVideosConfig(
                last_frame=last_image
            ),
        )
        
        logger.info(f"✅ SUCCESS! Operation: {operation.name}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed: {e}")
        return False

if __name__ == "__main__":
    success = test_exact_docs_example()
    if success:
        print("\n🎉 Docs example works!")
    else:
        print("\n❌ Docs example failed - feature might not be available yet")
