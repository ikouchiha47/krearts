# Text Correction Pipeline Specification

## Problem Statement

AI image generation models (Gemini, DALL-E, Stable Diffusion) produce garbled, misspelled text in comic panels because they're trained on pixels, not language. They don't understand spelling or grammar—only visual patterns of letters.

## Solution Overview

A three-stage pipeline that:
1. **Detects** where the model placed text (using OCR)
2. **Removes** bad text (using inpainting)
3. **Adds** correct text programmatically (using PIL/ImageDraw)

---

## Architecture

```
Generated Image (with bad text)
    ↓
[Stage 1: Text Detection]
    ↓
Text Region Mask
    ↓
[Stage 2: Inpainting]
    ↓
Clean Image (no text)
    ↓
[Stage 3: Text Overlay]
    ↓
Final Panel (with correct text)
```

---

## Stage 1: Text Detection

### Purpose
Automatically locate all text regions in the generated image, regardless of where the model placed them.

### Implementation

```python
import easyocr
import cv2
import numpy as np

class TextDetector:
    def __init__(self):
        self.reader = easyocr.Reader(['en'], gpu=True)
    
    def detect_text_regions(self, image_path: str) -> np.ndarray:
        """
        Detect all text regions in image and return binary mask.
        
        Args:
            image_path: Path to generated comic panel
            
        Returns:
            Binary mask (255 = text region, 0 = background)
        """
        image = cv2.imread(image_path)
        height, width = image.shape[:2]
        
        # Detect text with bounding boxes
        results = self.reader.readtext(image)
        
        # Create binary mask
        mask = np.zeros((height, width), dtype=np.uint8)
        
        for (bbox, text, confidence) in results:
            # Convert bbox to polygon points
            pts = np.array(bbox, dtype=np.int32)
            
            # Fill polygon on mask
            cv2.fillPoly(mask, [pts], 255)
        
        # Dilate mask to catch text edges
        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.dilate(mask, kernel, iterations=2)
        
        return mask
```

### Dependencies
- `easyocr` - Multilingual OCR with GPU support
- `opencv-python` - Image processing

### Configuration
```python
# config/text_detection.yaml
text_detection:
  languages: ['en']
  gpu: true
  confidence_threshold: 0.3
  dilation_kernel_size: 5
  dilation_iterations: 2
```

---

## Stage 2: Inpainting

### Purpose
Remove detected text regions and regenerate clean background using AI inpainting.

### What is Inpainting?
Inpainting is AI-powered "content-aware fill" that:
- Takes an image and a mask
- Regenerates ONLY the masked regions
- Preserves the rest of the image
- Fills in with contextually appropriate content

### Implementation

```python
from diffusers import StableDiffusionInpaintPipeline
import torch
from PIL import Image

class TextInpainter:
    def __init__(self, model_id: str = "runwayml/stable-diffusion-inpainting"):
        self.pipe = StableDiffusionInpaintPipeline.from_pretrained(
            model_id,
            torch_dtype=torch.float16
        )
        self.pipe = self.pipe.to("cuda")
    
    def remove_text(
        self, 
        image_path: str, 
        mask: np.ndarray,
        scene_description: str
    ) -> Image.Image:
        """
        Inpaint text regions to remove garbled text.
        
        Args:
            image_path: Original image with bad text
            mask: Binary mask of text regions
            scene_description: Scene context for inpainting
            
        Returns:
            Clean image with text removed
        """
        # Load image and mask
        image = Image.open(image_path).convert("RGB")
        mask_image = Image.fromarray(mask).convert("L")
        
        # Inpaint masked regions
        result = self.pipe(
            prompt=f"{scene_description}, clean background, no text, high quality",
            negative_prompt="text, letters, words, captions, speech bubbles, typography, writing",
            image=image,
            mask_image=mask_image,
            num_inference_steps=50,
            guidance_scale=7.5,
            strength=0.8
        ).images[0]
        
        return result
```

### Model Options

| Model | Pros | Cons | Use Case |
|-------|------|------|----------|
| SD Inpainting | Fast, good quality | Requires GPU | Production |
| DALL-E Inpainting | Best quality | API cost | High-quality output |
| LaMa | Very fast | Lower quality | Quick fixes |

### Configuration
```python
# config/inpainting.yaml
inpainting:
  model: "runwayml/stable-diffusion-inpainting"
  device: "cuda"
  num_inference_steps: 50
  guidance_scale: 7.5
  strength: 0.8
  negative_prompt: "text, letters, words, captions, speech bubbles"
```

---

## Stage 3: Text Overlay

### Purpose
Add correct, clean text to the image in predictable, readable positions.

### Text Positioning Strategies

#### Strategy A: Caption Bar (Simplest)
Always add text in a black bar at the bottom (like subtitles).

```python
from PIL import Image, ImageDraw, ImageFont

class TextOverlay:
    def __init__(self, font_path: str = "fonts/ComicBold.ttf"):
        self.font = ImageFont.truetype(font_path, 24)
    
    def add_caption_bar(
        self, 
        image: Image.Image, 
        text: str
    ) -> Image.Image:
        """
        Add text in black caption bar at bottom.
        
        Args:
            image: Clean image without text
            text: Correct dialogue/narration
            
        Returns:
            Image with caption bar
        """
        draw = ImageDraw.Draw(image)
        width, height = image.size
        
        # Calculate text size
        bbox = draw.textbbox((0, 0), text, font=self.font)
        text_height = bbox[3] - bbox[1]
        
        # Draw black bar
        bar_height = text_height + 40
        draw.rectangle(
            [(0, height - bar_height), (width, height)],
            fill=(0, 0, 0, 230)
        )
        
        # Draw white text
        text_y = height - bar_height + 20
        draw.text(
            (20, text_y),
            text,
            fill="white",
            font=self.font
        )
        
        return image
```

#### Strategy B: Speech Bubbles (Advanced)
Position speech bubbles near detected character faces.

```python
import face_recognition

class SpeechBubbleOverlay:
    def __init__(self):
        self.font = ImageFont.truetype("fonts/ComicBold.ttf", 20)
    
    def add_speech_bubble(
        self,
        image: Image.Image,
        dialogue: dict  # {"character": "Jack", "text": "Hello"}
    ) -> Image.Image:
        """
        Add speech bubble positioned near character face.
        """
        # Detect faces
        image_np = np.array(image)
        face_locations = face_recognition.face_locations(image_np)
        
        if not face_locations:
            # Fallback to caption bar
            return self.add_caption_bar(image, dialogue['text'])
        
        # Get first face location
        top, right, bottom, left = face_locations[0]
        
        # Position bubble above face
        bubble_x = left
        bubble_y = top - 100
        
        # Draw bubble
        draw = ImageDraw.Draw(image)
        self._draw_bubble_shape(draw, bubble_x, bubble_y, dialogue['text'])
        
        return image
    
    def _draw_bubble_shape(self, draw, x, y, text):
        """Draw rounded rectangle speech bubble with tail"""
        # Get text dimensions
        bbox = draw.textbbox((0, 0), text, font=self.font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # Bubble dimensions
        padding = 20
        bubble_width = text_width + (padding * 2)
        bubble_height = text_height + (padding * 2)
        
        # Draw rounded rectangle
        draw.rounded_rectangle(
            [(x, y), (x + bubble_width, y + bubble_height)],
            radius=15,
            fill="white",
            outline="black",
            width=3
        )
        
        # Draw tail (triangle pointing down)
        tail_points = [
            (x + bubble_width // 2 - 10, y + bubble_height),
            (x + bubble_width // 2 + 10, y + bubble_height),
            (x + bubble_width // 2, y + bubble_height + 20)
        ]
        draw.polygon(tail_points, fill="white", outline="black")
        
        # Draw text
        draw.text(
            (x + padding, y + padding),
            text,
            fill="black",
            font=self.font
        )
```

### Configuration
```python
# config/text_overlay.yaml
text_overlay:
  strategy: "caption_bar"  # or "speech_bubble"
  font:
    family: "fonts/ComicBold.ttf"
    size: 24
    color: "white"
  caption_bar:
    background_color: [0, 0, 0, 230]
    padding: 20
    position: "bottom"
  speech_bubble:
    background_color: "white"
    border_color: "black"
    border_width: 3
    padding: 20
    tail_size: 20
```

---

## Complete Pipeline

```python
# cinema/pipeline/text_correction.py

from typing import Dict
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class TextCorrectionPipeline:
    """
    Complete pipeline for fixing text in AI-generated comic panels.
    """
    
    def __init__(self, config: Dict):
        self.detector = TextDetector()
        self.inpainter = TextInpainter(config['inpainting']['model'])
        self.overlay = TextOverlay(config['text_overlay']['font']['family'])
        self.config = config
    
    def process_panel(
        self,
        image_path: str,
        scene_description: str,
        correct_dialogue: str,
        output_path: str
    ) -> str:
        """
        Fix text in a comic panel.
        
        Args:
            image_path: Path to generated panel with bad text
            scene_description: Scene context for inpainting
            correct_dialogue: The correct text to add
            output_path: Where to save corrected panel
            
        Returns:
            Path to corrected image
        """
        logger.info(f"Processing panel: {image_path}")
        
        # Stage 1: Detect text regions
        logger.info("Stage 1: Detecting text regions...")
        mask = self.detector.detect_text_regions(image_path)
        
        # Check if text was found
        if mask.sum() == 0:
            logger.info("No text detected, skipping inpainting")
            clean_image = Image.open(image_path)
        else:
            # Stage 2: Remove bad text
            logger.info("Stage 2: Inpainting text regions...")
            clean_image = self.inpainter.remove_text(
                image_path,
                mask,
                scene_description
            )
        
        # Stage 3: Add correct text
        logger.info("Stage 3: Adding correct text...")
        final_image = self.overlay.add_caption_bar(
            clean_image,
            correct_dialogue
        )
        
        # Save result
        final_image.save(output_path)
        logger.info(f"Saved corrected panel: {output_path}")
        
        return output_path
    
    def process_batch(
        self,
        panels: list[Dict]  # [{"image": path, "scene": desc, "dialogue": text}]
    ) -> list[str]:
        """Process multiple panels in batch."""
        results = []
        
        for i, panel in enumerate(panels):
            output_path = f"output/corrected_panel_{i}.png"
            result = self.process_panel(
                panel['image'],
                panel['scene'],
                panel['dialogue'],
                output_path
            )
            results.append(result)
        
        return results
```

---

## Integration with Existing System

### Update Panel Generation

```python
# cinema/pipeline/detective_maker.py

class DetectiveMaker:
    def __init__(self):
        self.text_corrector = TextCorrectionPipeline(load_config())
    
    def generate_panel(self, scene_data: Dict) -> str:
        """Generate panel with text correction."""
        
        # Generate image (will have bad text)
        raw_image = self.image_generator.generate(
            prompt=scene_data['visual_description']
        )
        
        # Fix text
        corrected_image = self.text_corrector.process_panel(
            image_path=raw_image,
            scene_description=scene_data['visual_description'],
            correct_dialogue=scene_data['dialogue'],
            output_path=f"output/{scene_data['panel_id']}.png"
        )
        
        return corrected_image
```

---

## Configuration File

```yaml
# config/text_correction.yaml

text_detection:
  languages: ['en']
  gpu: true
  confidence_threshold: 0.3
  dilation_kernel_size: 5
  dilation_iterations: 2

inpainting:
  model: "runwayml/stable-diffusion-inpainting"
  device: "cuda"
  num_inference_steps: 50
  guidance_scale: 7.5
  strength: 0.8
  negative_prompt: "text, letters, words, captions, speech bubbles, typography"

text_overlay:
  strategy: "caption_bar"  # or "speech_bubble"
  font:
    family: "fonts/ComicBold.ttf"
    size: 24
    color: "white"
  caption_bar:
    background_color: [0, 0, 0, 230]
    padding: 20
    position: "bottom"
```

---

## Dependencies

```toml
# pyproject.toml

[tool.poetry.dependencies]
easyocr = "^1.7.0"
opencv-python = "^4.8.0"
diffusers = "^0.25.0"
transformers = "^4.36.0"
torch = "^2.1.0"
pillow = "^10.1.0"
face-recognition = "^1.3.0"  # optional, for speech bubbles
numpy = "^1.24.0"
```

---

## Performance Considerations

### GPU Requirements
- **Text Detection**: 2GB VRAM (EasyOCR)
- **Inpainting**: 8GB VRAM (SD Inpainting)
- **Total**: 10GB VRAM recommended

### Processing Time (per panel)
- Text Detection: ~1-2 seconds
- Inpainting: ~5-10 seconds (50 steps)
- Text Overlay: <1 second
- **Total**: ~6-13 seconds per panel

### Optimization Strategies

1. **Batch Processing**: Process multiple panels in parallel
2. **Conditional Inpainting**: Skip if no text detected
3. **Model Caching**: Keep models loaded in memory
4. **Lower Steps**: Use 30 steps instead of 50 for faster results

```python
# Optimized batch processing
async def process_panels_parallel(panels: list[Dict]) -> list[str]:
    """Process panels in parallel using asyncio."""
    tasks = [
        asyncio.create_task(process_panel_async(panel))
        for panel in panels
    ]
    return await asyncio.gather(*tasks)
```

---

## Testing

```python
# tests/test_text_correction.py

def test_text_detection():
    """Test that text regions are correctly detected."""
    detector = TextDetector()
    mask = detector.detect_text_regions("tests/fixtures/panel_with_text.png")
    
    assert mask.sum() > 0, "Should detect text regions"
    assert mask.dtype == np.uint8, "Mask should be uint8"

def test_inpainting():
    """Test that inpainting removes text."""
    inpainter = TextInpainter()
    result = inpainter.remove_text(
        "tests/fixtures/panel_with_text.png",
        mask=np.ones((512, 512), dtype=np.uint8) * 255,
        scene_description="noir detective office"
    )
    
    assert isinstance(result, Image.Image)
    assert result.size == (512, 512)

def test_text_overlay():
    """Test that text is correctly added."""
    overlay = TextOverlay()
    image = Image.new("RGB", (512, 512), color="white")
    result = overlay.add_caption_bar(image, "Test dialogue")
    
    assert result.size == (512, 512)
    # Verify text was added (check bottom region is darker)
    pixels = np.array(result)
    assert pixels[-50:, :, :].mean() < 50  # Bottom should be dark
```

---

## Future Enhancements

1. **Multi-language Support**: Extend OCR to detect multiple languages
2. **Style Transfer**: Match text style to comic art style
3. **Automatic Positioning**: ML model to predict optimal text placement
4. **Real-time Processing**: Optimize for <3 seconds per panel
5. **Quality Metrics**: Automated scoring of text readability

---

## References

- [EasyOCR Documentation](https://github.com/JaidedAI/EasyOCR)
- [Stable Diffusion Inpainting](https://huggingface.co/runwayml/stable-diffusion-inpainting)
- [PIL ImageDraw](https://pillow.readthedocs.io/en/stable/reference/ImageDraw.html)
- [Face Recognition Library](https://github.com/ageitgey/face_recognition)
