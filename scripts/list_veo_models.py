#!/usr/bin/env python3
"""
List available Veo models and their capabilities.
"""

import logging
from dotenv import load_dotenv
from google import genai

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def list_models():
    """List all available models"""
    client = genai.Client()
    
    logger.info("Fetching available models...")
    models = client.models.list()
    
    veo_models = []
    for model in models:
        if 'veo' in model.name.lower():
            veo_models.append(model)
            logger.info(f"\n{'='*60}")
            logger.info(f"Model: {model.name}")
            logger.info(f"Display Name: {model.display_name}")
            logger.info(f"Description: {model.description}")
            if hasattr(model, 'supported_generation_methods'):
                logger.info(f"Supported Methods: {model.supported_generation_methods}")
            logger.info(f"{'='*60}")
    
    if not veo_models:
        logger.warning("No Veo models found!")
        logger.info("\nAll available models:")
        for model in models:
            logger.info(f"  - {model.name}")
    
    return veo_models

if __name__ == "__main__":
    list_models()
