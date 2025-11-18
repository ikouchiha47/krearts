"""
Caption and speech bubble placement using bounding box avoidance.

Uses detected bounding boxes to find safe areas for text overlays.
"""
import logging
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class BoundingBox:
    """Bounding box in normalized coordinates (0-1000)."""
    y_min: int
    x_min: int
    y_max: int
    x_max: int
    label: str
    
    @property
    def center(self) -> Tuple[int, int]:
        """Get center point of box."""
        return ((self.y_min + self.y_max) // 2, (self.x_min + self.x_max) // 2)
    
    @property
    def area(self) -> int:
        """Get area of box."""
        return (self.y_max - self.y_min) * (self.x_max - self.x_min)
    
    def overlaps(self, other: 'BoundingBox', threshold: float = 0.1) -> bool:
        """Check if this box overlaps with another box."""
        # Calculate intersection
        x_overlap = max(0, min(self.x_max, other.x_max) - max(self.x_min, other.x_min))
        y_overlap = max(0, min(self.y_max, other.y_max) - max(self.y_min, other.y_min))
        
        if x_overlap == 0 or y_overlap == 0:
            return False
        
        intersection = x_overlap * y_overlap
        min_area = min(self.area, other.area)
        
        return (intersection / min_area) > threshold


@dataclass
class TextPlacement:
    """Suggested placement for text overlay."""
    position: str  # "top", "bottom", "left", "right", "top-left", "top-right", "bottom-left", "bottom-right"
    box: BoundingBox  # Suggested bounding box for text
    confidence: float  # 0.0 to 1.0, how good this placement is
    reason: str  # Why this placement was chosen


class CaptionPlacer:
    """
    Intelligently place captions and speech bubbles avoiding important objects.
    """
    
    def __init__(self, image_width: int = 1000, image_height: int = 1000):
        """
        Initialize caption placer.
        
        Args:
            image_width: Image width in normalized coordinates (default: 1000)
            image_height: Image height in normalized coordinates (default: 1000)
        """
        self.width = image_width
        self.height = image_height
    
    def find_safe_areas(
        self,
        important_objects: List[Dict],
        min_area_size: int = 100000  # Minimum area for text (100x1000 normalized)
    ) -> List[BoundingBox]:
        """
        Find safe areas in the image that don't overlap with important objects.
        
        Args:
            important_objects: List of detected objects with box_2d and label
            min_area_size: Minimum area size for text placement
        
        Returns:
            List of safe area bounding boxes
        """
        # Convert to BoundingBox objects
        boxes = []
        for obj in important_objects:
            box_2d = obj.get('box_2d', [])
            if len(box_2d) == 4:
                boxes.append(BoundingBox(
                    y_min=box_2d[0],
                    x_min=box_2d[1],
                    y_max=box_2d[2],
                    x_max=box_2d[3],
                    label=obj.get('label', 'unknown')
                ))
        
        # Define candidate areas (top, bottom, left, right, corners)
        candidates = [
            # Top strip
            BoundingBox(0, 0, 150, self.width, "top"),
            # Bottom strip
            BoundingBox(self.height - 150, 0, self.height, self.width, "bottom"),
            # Left strip
            BoundingBox(0, 0, self.height, 150, "left"),
            # Right strip
            BoundingBox(0, self.width - 150, self.height, self.width, "right"),
            # Top-left corner
            BoundingBox(0, 0, 200, 300, "top-left"),
            # Top-right corner
            BoundingBox(0, self.width - 300, 200, self.width, "top-right"),
            # Bottom-left corner
            BoundingBox(self.height - 200, 0, self.height, 300, "bottom-left"),
            # Bottom-right corner
            BoundingBox(self.height - 200, self.width - 300, self.height, self.width, "bottom-right"),
        ]
        
        # Filter candidates that don't overlap with important objects
        safe_areas = []
        for candidate in candidates:
            has_overlap = False
            for obj_box in boxes:
                if candidate.overlaps(obj_box, threshold=0.2):
                    has_overlap = True
                    break
            
            # Accept areas with minimal overlap or that meet size requirements
            if (not has_overlap or candidate.area >= min_area_size * 1.5) and candidate.area >= min_area_size:
                safe_areas.append(candidate)
        
        return safe_areas
    
    def suggest_caption_placement(
        self,
        important_objects: List[Dict],
        text_type: str = "caption"  # "caption" or "speech_bubble"
    ) -> Optional[TextPlacement]:
        """
        Suggest the best placement for a caption or speech bubble.
        
        Args:
            important_objects: List of detected objects with box_2d and label
            text_type: Type of text ("caption" for narration, "speech_bubble" for dialogue)
        
        Returns:
            TextPlacement with suggested position and bounding box
        """
        safe_areas = self.find_safe_areas(important_objects)
        
        if not safe_areas:
            logger.warning("No safe areas found, using default top placement")
            return TextPlacement(
                position="top",
                box=BoundingBox(0, 0, 150, self.width, "top"),
                confidence=0.3,
                reason="No safe areas found, using default"
            )
        
        # Prioritize based on text type
        if text_type == "caption":
            # Captions prefer top or bottom
            priority = ["top", "bottom", "top-left", "top-right", "bottom-left", "bottom-right"]
        else:
            # Speech bubbles prefer corners or sides near characters
            priority = ["top-right", "top-left", "bottom-right", "bottom-left", "top", "bottom"]
        
        # Find best match
        for preferred in priority:
            for area in safe_areas:
                if area.label == preferred:
                    return TextPlacement(
                        position=area.label,
                        box=area,
                        confidence=0.9,
                        reason=f"Safe {preferred} area found"
                    )
        
        # Fallback to first safe area
        best_area = safe_areas[0]
        return TextPlacement(
            position=best_area.label,
            box=best_area,
            confidence=0.7,
            reason=f"Using available safe area: {best_area.label}"
        )
    
    def suggest_speech_bubble_placement(
        self,
        important_objects: List[Dict],
        character_name: str
    ) -> Optional[TextPlacement]:
        """
        Suggest placement for a speech bubble near a character's face.
        
        Args:
            important_objects: List of detected objects with box_2d and label
            character_name: Name of the speaking character
        
        Returns:
            TextPlacement with suggested position near character
        """
        # Find character's face
        character_box = None
        for obj in important_objects:
            label = obj.get('label', '').lower()
            if character_name.lower() in label and 'face' in label:
                box_2d = obj.get('box_2d', [])
                if len(box_2d) == 4:
                    character_box = BoundingBox(
                        y_min=box_2d[0],
                        x_min=box_2d[1],
                        y_max=box_2d[2],
                        x_max=box_2d[3],
                        label=obj.get('label', 'unknown')
                    )
                    break
        
        if not character_box:
            logger.warning(f"Character face not found for {character_name}, using default placement")
            return self.suggest_caption_placement(important_objects, text_type="speech_bubble")
        
        # Place bubble near character face
        # Try positions: above, below, left, right of face
        face_center_y, face_center_x = character_box.center
        
        bubble_positions = [
            # Above face
            ("above", BoundingBox(
                max(0, character_box.y_min - 200),
                character_box.x_min,
                character_box.y_min,
                character_box.x_max,
                "above-face"
            )),
            # Below face
            ("below", BoundingBox(
                character_box.y_max,
                character_box.x_min,
                min(self.height, character_box.y_max + 200),
                character_box.x_max,
                "below-face"
            )),
            # Left of face
            ("left", BoundingBox(
                character_box.y_min,
                max(0, character_box.x_min - 250),
                character_box.y_max,
                character_box.x_min,
                "left-of-face"
            )),
            # Right of face
            ("right", BoundingBox(
                character_box.y_min,
                character_box.x_max,
                character_box.y_max,
                min(self.width, character_box.x_max + 250),
                "right-of-face"
            )),
        ]
        
        # Find position with least overlap
        best_placement = None
        best_overlap_count = float('inf')
        
        for position, bubble_box in bubble_positions:
            overlap_count = 0
            for obj in important_objects:
                box_2d = obj.get('box_2d', [])
                if len(box_2d) == 4:
                    obj_box = BoundingBox(box_2d[0], box_2d[1], box_2d[2], box_2d[3], obj.get('label', ''))
                    if bubble_box.overlaps(obj_box, threshold=0.3):
                        overlap_count += 1
            
            if overlap_count < best_overlap_count:
                best_overlap_count = overlap_count
                best_placement = TextPlacement(
                    position=position,
                    box=bubble_box,
                    confidence=1.0 - (overlap_count * 0.2),
                    reason=f"Placed {position} character face with {overlap_count} overlaps"
                )
        
        return best_placement or self.suggest_caption_placement(important_objects, text_type="speech_bubble")


def visualize_text_placement(
    image_path: str,
    detections: List[Dict],
    text_placements: List[TextPlacement],
    output_path: str
):
    """
    Visualize suggested text placements on an image.
    
    Args:
        image_path: Path to input image
        detections: List of detected objects
        text_placements: List of suggested text placements
        output_path: Path to save visualization
    """
    from PIL import Image, ImageDraw, ImageFont
    
    img = Image.open(image_path)
    draw = ImageDraw.Draw(img)
    
    img_width, img_height = img.size
    
    # Draw detected objects in red
    for detection in detections:
        box_2d = detection.get('box_2d', [])
        if len(box_2d) == 4:
            y_min, x_min, y_max, x_max = box_2d
            x1 = int(x_min * img_width / 1000)
            y1 = int(y_min * img_height / 1000)
            x2 = int(x_max * img_width / 1000)
            y2 = int(y_max * img_height / 1000)
            
            draw.rectangle([(x1, y1), (x2, y2)], outline="red", width=2)
    
    # Draw suggested text placements in green
    for placement in text_placements:
        box = placement.box
        x1 = int(box.x_min * img_width / 1000)
        y1 = int(box.y_min * img_height / 1000)
        x2 = int(box.x_max * img_width / 1000)
        y2 = int(box.y_max * img_height / 1000)
        
        draw.rectangle([(x1, y1), (x2, y2)], outline="green", width=3)
        
        # Add label
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 16)
        except:
            font = ImageFont.load_default()
        
        label = f"{placement.position} ({placement.confidence:.2f})"
        draw.text((x1 + 5, y1 + 5), label, fill="green", font=font)
    
    img.save(output_path)
    logger.info(f"Saved text placement visualization to: {output_path}")


if __name__ == "__main__":
    import json
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python caption_placement.py <detection_json_path>")
        sys.exit(1)
    
    detection_file = sys.argv[1]
    
    with open(detection_file, 'r') as f:
        data = json.load(f)
    
    detections = data.get('detections', [])
    
    placer = CaptionPlacer()
    
    # Suggest caption placement
    caption_placement = placer.suggest_caption_placement(detections, text_type="caption")
    print(f"\n📝 Caption placement suggestion:")
    print(f"   Position: {caption_placement.position}")
    print(f"   Box: {caption_placement.box}")
    print(f"   Confidence: {caption_placement.confidence:.2f}")
    print(f"   Reason: {caption_placement.reason}")
    
    # Find safe areas
    safe_areas = placer.find_safe_areas(detections)
    print(f"\n✅ Found {len(safe_areas)} safe areas:")
    for area in safe_areas:
        print(f"   - {area.label}: {area.area} sq units")
