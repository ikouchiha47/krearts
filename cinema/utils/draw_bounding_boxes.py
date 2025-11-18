"""
Utility to draw bounding boxes on images for visualization.
"""
import json
from pathlib import Path
from typing import List, Dict, Tuple
from PIL import Image, ImageDraw, ImageFont
import logging

logger = logging.getLogger(__name__)


def draw_bounding_boxes(
    image_path: str,
    detections: List[Dict],
    output_path: str = None,
    box_color: str = "red",
    text_color: str = "white",
    line_width: int = 3
) -> Image.Image:
    """
    Draw bounding boxes on an image.
    
    Args:
        image_path: Path to the input image
        detections: List of detection dicts with 'label', 'box_2d', 'confidence'
        output_path: Optional path to save the output image
        box_color: Color for bounding box rectangles
        text_color: Color for label text
        line_width: Width of bounding box lines
    
    Returns:
        PIL Image with bounding boxes drawn
    """
    # Load image
    img = Image.open(image_path)
    draw = ImageDraw.Draw(img)
    
    # Try to load a font, fall back to default if not available
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 20)
    except:
        font = ImageFont.load_default()
    
    # Get image dimensions for coordinate conversion
    img_width, img_height = img.size
    
    # Draw each detection
    for detection in detections:
        label = detection.get('label', 'unknown')
        box_2d = detection.get('box_2d', [])
        confidence = detection.get('confidence', 0.0)
        
        if len(box_2d) != 4:
            logger.warning(f"Invalid box_2d for {label}: {box_2d}")
            continue
        
        # Convert normalized coordinates (0-1000) to pixel coordinates
        y_min, x_min, y_max, x_max = box_2d
        
        # Scale to image dimensions
        x1 = int(x_min * img_width / 1000)
        y1 = int(y_min * img_height / 1000)
        x2 = int(x_max * img_width / 1000)
        y2 = int(y_max * img_height / 1000)
        
        # Draw rectangle
        draw.rectangle(
            [(x1, y1), (x2, y2)],
            outline=box_color,
            width=line_width
        )
        
        # Draw label with confidence
        label_text = f"{label} ({confidence:.2f})"
        
        # Get text bounding box for background
        bbox = draw.textbbox((x1, y1 - 25), label_text, font=font)
        
        # Draw background rectangle for text
        draw.rectangle(bbox, fill=box_color)
        
        # Draw text
        draw.text(
            (x1, y1 - 25),
            label_text,
            fill=text_color,
            font=font
        )
    
    # Save if output path provided
    if output_path:
        img.save(output_path)
        logger.info(f"Saved annotated image to: {output_path}")
    
    return img


def draw_bounding_boxes_from_json(
    image_path: str,
    detection_json_path: str = None,
    output_path: str = None
) -> Image.Image:
    """
    Draw bounding boxes from a detection JSON file.
    
    Args:
        image_path: Path to the input image
        detection_json_path: Path to detection JSON (defaults to image_path.detections.json)
        output_path: Path to save output (defaults to image_path with _annotated suffix)
    
    Returns:
        PIL Image with bounding boxes drawn
    """
    image_path = Path(image_path)
    
    # Default detection JSON path
    if detection_json_path is None:
        detection_json_path = image_path.with_suffix('.detections.json')
    else:
        detection_json_path = Path(detection_json_path)
    
    # Default output path
    if output_path is None:
        output_path = image_path.parent / f"{image_path.stem}_annotated{image_path.suffix}"
    else:
        output_path = Path(output_path)
    
    # Load detections
    if not detection_json_path.exists():
        raise FileNotFoundError(f"Detection file not found: {detection_json_path}")
    
    with open(detection_json_path, 'r') as f:
        data = json.load(f)
    
    detections = data.get('detections', [])
    
    logger.info(f"Drawing {len(detections)} bounding boxes on {image_path.name}")
    
    # Draw boxes
    img = draw_bounding_boxes(
        str(image_path),
        detections,
        str(output_path)
    )
    
    return img


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python draw_bounding_boxes.py <image_path> [detection_json_path] [output_path]")
        sys.exit(1)
    
    image_path = sys.argv[1]
    detection_json_path = sys.argv[2] if len(sys.argv) > 2 else None
    output_path = sys.argv[3] if len(sys.argv) > 3 else None
    
    logging.basicConfig(level=logging.INFO)
    
    draw_bounding_boxes_from_json(image_path, detection_json_path, output_path)
    print(f"✅ Annotated image saved")
