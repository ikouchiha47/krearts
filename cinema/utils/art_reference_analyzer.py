"""
Art Reference Image Analyzer

Uses Gemini Vision to analyze uploaded reference images and extract:
- Visual characteristics (colors, line work, rendering)
- Art techniques (halftone, painterly, etc.)
- Suggested tags and usage context
"""

import asyncio
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from PIL import Image
import json

from cinema.providers.gemini import GeminiMediaGen
from cinema.models.art_reference import (
    ArtReference,
    ArtReferenceTag,
    ArtReferenceAnalysis,
    TAG_CATEGORIES
)

logger = logging.getLogger(__name__)


ANALYSIS_PROMPT = """Analyze this comic book/manga reference image and extract detailed style characteristics.

Provide a comprehensive analysis in JSON format with the following structure:

{{
  "visual_characteristics": {{
    "dominant_colors": ["#hex1", "#hex2", "#hex3"],
    "color_palette_description": "Description of color scheme",
    "line_work_style": "Description of line work (weight, quality, technique)",
    "rendering_technique": "How the image is rendered (halftone, painterly, flat, etc.)",
    "lighting_style": "Lighting characteristics",
    "composition_notes": "Composition and framing approach",
    "texture_details": "Surface textures and patterns visible"
  }},
  
  "art_techniques": {{
    "primary_technique": "Main artistic technique",
    "secondary_techniques": ["technique1", "technique2"],
    "special_effects": ["effect1", "effect2"]
  }},
  
  "suggested_tags": {{
    "panel_type": ["tag1", "tag2"],
    "action": ["tag1", "tag2"],
    "art_technique": ["tag1", "tag2"],
    "color_style": ["tag1", "tag2"],
    "lighting": ["tag1", "tag2"],
    "composition": ["tag1", "tag2"],
    "general_understanding": ["tag1", "tag2"]
  }},
  
  "usage_recommendations": {{
    "best_for_shot_types": ["wide", "close-up", etc.],
    "best_for_scene_types": ["action", "dialogue", etc.],
    "best_for_panel_layouts": ["grid-8-panel", etc.],
    "best_for_emotional_tones": ["dramatic", "tense", etc.]
  }},
  
  "style_description": "A detailed text description of the art style that can be used in image generation prompts",
  
  "key_characteristics": [
    "Characteristic 1",
    "Characteristic 2",
    "Characteristic 3"
  ]
}}

IMPORTANT GUIDELINES:

1. **Colors**: Extract 3-5 dominant colors in hex format. Describe the overall palette.

2. **Line Work**: Describe line weight (thin/thick/variable), quality (clean/rough/sketchy), and technique (ink/digital/pencil).

3. **Rendering**: Identify the rendering approach:
   - Halftone/Ben-Day dots (Spider-Verse, classic comics)
   - Painterly (Arcane, watercolor effects)
   - Flat colors (Pop art, modern comics)
   - Photorealistic with overlays
   - Ligne claire (Blueberry, European comics)

4. **Lighting**: Describe lighting style:
   - High contrast noir
   - Soft diffused
   - Dramatic rim lighting
   - Natural daylight
   - Artificial/neon

5. **Tags**: Select appropriate tags from these categories:
   - panel_type: single_panel, grid-8-panel, grid-9-panel, splash_page, etc.
   - action: motion_lines, speed_effects, impact, explosion, fight, chase, static, dialogue
   - art_technique: halftone, ben_day_dots, ligne_claire, painterly, flat_colors, chromatic_aberration
   - color_style: black_and_white, high_contrast, muted_palette, vibrant_colors, noir, neon
   - lighting: dramatic, soft_diffused, high_contrast, rim_lighting, natural
   - composition: rule_of_thirds, centered, symmetrical, diagonal, dynamic
   - general_understanding: character_design, environment, mechanical_detail, architecture

6. **Usage**: Recommend when this reference should be used based on:
   - Shot types (establishing, wide, medium, close-up, extreme-close-up)
   - Scene types (action, dialogue, atmospheric, dramatic, tense)
   - Panel layouts (grid-8-panel, grid-9-panel, horizontal-3-panel, etc.)
   - Emotional tones (thrilling, tense, relaxed, dramatic, mysterious)

7. **Style Description**: Write a detailed prompt-ready description that captures the essence of this style for image generation.

Return ONLY the JSON object, no additional text."""


class ArtReferenceAnalyzer:
    """Analyzes reference images to extract style characteristics."""
    
    def __init__(self):
        self.gemini = GeminiMediaGen()
    
    async def analyze_image(
        self,
        image_path: Path,
        style_name: str,
        reference_name: Optional[str] = None
    ) -> ArtReference:
        """
        Analyze a reference image and create an ArtReference object.
        
        Args:
            image_path: Path to the reference image
            style_name: Art style category (e.g., 'akira', 'spiderverse')
            reference_name: Optional human-readable name
        
        Returns:
            ArtReference object with analysis
        """
        logger.info(f"🔍 Analyzing reference image: {image_path.name}")
        
        # Load image
        img = Image.open(image_path)
        img_width, img_height = img.size
        aspect_ratio = f"{img_width}:{img_height}"
        
        # Call Gemini for analysis
        logger.info("  Calling Gemini Vision for style analysis...")
        
        from google.genai import types
        config = types.GenerateContentConfig(
            response_modalities=[types.Modality.TEXT],
        )
        
        response = await asyncio.to_thread(
            self.gemini.client.models.generate_content,
            model="gemini-2.0-flash-exp",
            contents=[ANALYSIS_PROMPT, img],
            config=config,
        )
        
        # Parse response
        response_text = (response.text or "").strip()
        logger.debug(f"  Analysis response: {response_text[:200]}...")
        
        # Extract JSON
        import re
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
            else:
                raise ValueError("No JSON found in analysis response")
        
        try:
            analysis_data = json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse analysis JSON: {e}")
            logger.error(f"Response: {response_text}")
            raise
        
        # Build ArtReference object
        ref_id = f"{style_name}_{image_path.stem}"
        ref_name = reference_name or image_path.stem.replace('_', ' ').title()
        
        # Extract visual characteristics
        visual = analysis_data.get('visual_characteristics', {})
        analysis = ArtReferenceAnalysis(
            dominant_colors=visual.get('dominant_colors', []),
            color_palette_description=visual.get('color_palette_description'),
            line_work_style=visual.get('line_work_style'),
            rendering_technique=visual.get('rendering_technique'),
            lighting_style=visual.get('lighting_style'),
            composition_notes=visual.get('composition_notes'),
            texture_details=visual.get('texture_details'),
            aspect_ratio=aspect_ratio,
            resolution=f"{img_width}x{img_height}",
            ai_description=analysis_data.get('style_description'),
            analyzed_at=None  # Will be set when saved
        )
        
        # Extract tags
        suggested_tags = analysis_data.get('suggested_tags', {})
        tags = []
        for category, values in suggested_tags.items():
            for value in values:
                tags.append(ArtReferenceTag(
                    category=category,
                    value=value,
                    weight=1.0
                ))
        
        # Extract usage recommendations
        usage = analysis_data.get('usage_recommendations', {})
        
        # Build ArtReference
        art_ref = ArtReference(
            id=ref_id,
            name=ref_name,
            style=style_name,
            file_path=str(image_path),
            tags=tags,
            text_prompt=analysis_data.get('style_description', ''),
            purpose=f"Reference for {style_name} style",
            analysis=analysis,
            use_for_shot_types=usage.get('best_for_shot_types', []),
            use_for_scene_types=usage.get('best_for_scene_types', []),
            use_for_panel_layouts=usage.get('best_for_panel_layouts', []),
            use_for_emotional_tones=usage.get('best_for_emotional_tones', []),
            source=None,
            artist=None,
            notes=None
        )
        
        logger.info(f"  ✅ Analysis complete: {len(tags)} tags, {len(visual.get('dominant_colors', []))} colors")
        
        return art_ref
    
    async def analyze_directory(
        self,
        directory: Path,
        style_name: str,
        output_file: Optional[Path] = None
    ) -> List[ArtReference]:
        """
        Analyze all images in a directory.
        
        Args:
            directory: Directory containing reference images
            style_name: Art style category
            output_file: Optional path to save analysis results
        
        Returns:
            List of ArtReference objects
        """
        logger.info(f"📁 Analyzing directory: {directory}")
        
        # Find all images
        image_extensions = ['.jpg', '.jpeg', '.png', '.webp']
        image_files = [
            f for f in directory.iterdir()
            if f.is_file() and f.suffix.lower() in image_extensions
        ]
        
        if not image_files:
            logger.warning(f"No images found in {directory}")
            return []
        
        logger.info(f"  Found {len(image_files)} images to analyze")
        
        # Analyze each image
        references = []
        for i, img_file in enumerate(image_files, 1):
            logger.info(f"\n  [{i}/{len(image_files)}] Analyzing: {img_file.name}")
            try:
                ref = await self.analyze_image(img_file, style_name)
                references.append(ref)
            except Exception as e:
                logger.error(f"  ❌ Failed to analyze {img_file.name}: {e}")
                continue
        
        # Save results if output file specified
        if output_file and references:
            self._save_references(references, output_file, style_name)
        
        logger.info(f"\n✅ Analyzed {len(references)}/{len(image_files)} images successfully")
        return references
    
    def _save_references(
        self,
        references: List[ArtReference],
        output_file: Path,
        style_name: str
    ):
        """Save analyzed references to JSON file."""
        from datetime import datetime
        
        # Add timestamp to analysis
        timestamp = datetime.now().isoformat()
        for ref in references:
            if ref.analysis:
                ref.analysis.analyzed_at = timestamp
        
        # Build library structure
        from cinema.models.art_reference import ArtReferenceLibrary
        
        library = ArtReferenceLibrary(
            style=style_name,
            description=f"Reference library for {style_name} style",
            characteristics=[],
            references=references,
            tag_categories=TAG_CATEGORIES
        )
        
        # Save to JSON
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w') as f:
            json.dump(library.model_dump(), f, indent=2)
        
        logger.info(f"💾 Saved analysis to: {output_file}")


async def analyze_reference_images(
    style_name: str,
    directory: Optional[Path] = None
):
    """
    Standalone function to analyze reference images for a style.
    
    Args:
        style_name: Art style name (e.g., 'akira', 'spiderverse')
        directory: Optional directory path (defaults to knowledge/art-styles/references/{style_name})
    """
    if directory is None:
        directory = Path(f"knowledge/art-styles/references/{style_name}")
    
    if not directory.exists():
        print(f"❌ Directory not found: {directory}")
        return
    
    output_file = directory / f"{style_name}_references.json"
    
    analyzer = ArtReferenceAnalyzer()
    references = await analyzer.analyze_directory(directory, style_name, output_file)
    
    if references:
        print(f"\n✅ Analysis complete!")
        print(f"   Analyzed: {len(references)} images")
        print(f"   Saved to: {output_file}")
        print(f"\n📋 Summary:")
        for ref in references:
            print(f"   • {ref.name}")
            print(f"     Tags: {len(ref.tags)}")
            print(f"     Colors: {len(ref.analysis.dominant_colors) if ref.analysis else 0}")
            print(f"     Technique: {ref.analysis.rendering_technique if ref.analysis else 'N/A'}")
    else:
        print(f"\n❌ No images analyzed")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python -m cinema.utils.art_reference_analyzer <style_name> [directory]")
        print("\nExample:")
        print("  python -m cinema.utils.art_reference_analyzer akira")
        print("  python -m cinema.utils.art_reference_analyzer spiderverse /path/to/images")
        sys.exit(1)
    
    style = sys.argv[1]
    directory = Path(sys.argv[2]) if len(sys.argv) > 2 else None
    
    asyncio.run(analyze_reference_images(style, directory))
