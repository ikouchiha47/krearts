"""
Comic book text overlay system with proper styling for different text types.

Follows comic book conventions:
- Speech bubbles: White rounded rectangles with black borders, tail pointing to speaker
- Thought bubbles: Cloud-like shapes with scalloped edges
- Narration captions: Yellow/beige rectangles at top/bottom
- Sound effects: Large, stylized text integrated into the scene
- Whisper: Dashed border speech bubbles
- Shout/Yell: Jagged/spiky borders, bold text
"""
import logging
from typing import List, Dict, Tuple, Optional
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import math

from cinema.utils.caption_placement import CaptionPlacer, TextPlacement

logger = logging.getLogger(__name__)


class ComicTextStyle:
    """Text styling constants for different comic text types."""
    
    # Speech bubble (normal dialogue)
    SPEECH = {
        "bg_color": (255, 255, 255),  # White
        "border_color": (0, 0, 0),  # Black
        "text_color": (0, 0, 0),  # Black
        "border_width": 3,
        "padding": 15,
        "corner_radius": 20,
        "has_tail": True,
        "font_size": 18,
        "font_weight": "normal",
    }
    
    # Thought bubble
    THOUGHT = {
        "bg_color": (255, 255, 255),  # White
        "border_color": (0, 0, 0),  # Black
        "text_color": (0, 0, 0),  # Black
        "border_width": 2,
        "padding": 15,
        "corner_radius": 30,  # More rounded
        "has_tail": True,
        "tail_style": "bubbles",  # Small circles instead of triangle
        "font_size": 16,
        "font_weight": "italic",
    }
    
    # Narration caption
    NARRATION = {
        "bg_color": (255, 255, 240),  # Ivory/off-white
        "border_color": (0, 0, 0),  # Black
        "text_color": (0, 0, 0),  # Black
        "border_width": 2,
        "padding": 10,
        "corner_radius": 3,  # Sharp corners for classic look
        "has_tail": False,
        "font_size": 14,
        "font_weight": "italic",
        "max_width": 250,  # Narrower captions
    }
    
    # Whisper (quiet speech)
    WHISPER = {
        "bg_color": (255, 255, 255),  # White
        "border_color": (0, 0, 0),  # Black
        "text_color": (0, 0, 0),  # Black
        "border_width": 2,
        "border_style": "dashed",
        "padding": 12,
        "corner_radius": 15,
        "has_tail": True,
        "font_size": 14,
        "font_weight": "normal",
    }
    
    # Shout/Yell (loud speech)
    SHOUT = {
        "bg_color": (255, 255, 255),  # White
        "border_color": (0, 0, 0),  # Black
        "text_color": (0, 0, 0),  # Black
        "border_width": 4,
        "border_style": "jagged",
        "padding": 15,
        "corner_radius": 10,
        "has_tail": True,
        "font_size": 20,
        "font_weight": "bold",
    }
    
    # Sound effect (onomatopoeia)
    SOUND_EFFECT = {
        "bg_color": None,  # Transparent
        "border_color": None,
        "text_color": (0, 0, 0),  # Black with white outline
        "text_outline": (255, 255, 255),
        "outline_width": 3,
        "padding": 0,
        "font_size": 32,
        "font_weight": "bold",
        "rotation": 0,  # Can be rotated
    }


class ComicTextOverlay:
    """
    Add text overlays to comic book panels with proper styling.
    """
    
    def __init__(self):
        """Initialize text overlay system."""
        self.placer = CaptionPlacer()
        
        # Try to load fonts
        self.fonts = self._load_fonts()
    
    def _load_fonts(self) -> Dict[str, ImageFont.FreeTypeFont]:
        """Load fonts for different text styles."""
        fonts = {}
        
        # Try common font paths
        font_paths = [
            "/System/Library/Fonts/Helvetica.ttc",
            "/System/Library/Fonts/HelveticaNeue.ttc",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        ]
        
        font_file = None
        for path in font_paths:
            if Path(path).exists():
                font_file = path
                break
        
        if font_file:
            try:
                fonts["normal"] = ImageFont.truetype(font_file, 18)
                fonts["bold"] = ImageFont.truetype(font_file, 20)
                fonts["italic"] = ImageFont.truetype(font_file, 16)
                fonts["large"] = ImageFont.truetype(font_file, 32)
                logger.info(f"Loaded fonts from: {font_file}")
            except Exception as e:
                logger.warning(f"Failed to load fonts: {e}")
                fonts["normal"] = ImageFont.load_default()
                fonts["bold"] = ImageFont.load_default()
                fonts["italic"] = ImageFont.load_default()
                fonts["large"] = ImageFont.load_default()
        else:
            logger.warning("No TrueType fonts found, using default")
            fonts["normal"] = ImageFont.load_default()
            fonts["bold"] = ImageFont.load_default()
            fonts["italic"] = ImageFont.load_default()
            fonts["large"] = ImageFont.load_default()
        
        return fonts
    
    def _detect_text_type(self, dialogue_entry: Dict) -> str:
        """
        Detect the type of text based on content and character.
        
        Args:
            dialogue_entry: Dict with 'character' and 'text' keys
        
        Returns:
            Text type: "narration", "speech", "thought", "whisper", "shout", "sound_effect", "skip"
        """
        character = dialogue_entry.get("character", "").lower()
        text = dialogue_entry.get("text", "")
        
        # Narration/caption
        if character == "narrator":
            return "narration"
        
        # Sound effects (all caps, onomatopoeia) - only dramatic ones
        if text.isupper() and len(text.split()) <= 3:
            # Dramatic sound effects only (not ambient sounds)
            dramatic_sounds = ["BANG", "CRASH", "BOOM", "SLAM", "CRACK", "GUNSHOT",
                             "SMASH", "THUD", "WHAM", "POW", "KABOOM", "SCREECH"]
            if any(pattern in text for pattern in dramatic_sounds):
                return "sound_effect"
            
            # Skip ambient sounds
            ambient_sounds = ["DRIP", "HSSSS", "PATTER", "SPLASH", "RUSTLE", "CREAK",
                            "CLICK", "CLINK", "SHUFFLE", "HISS", "WHOOSH"]
            if any(pattern in text for pattern in ambient_sounds):
                return "skip"
        
        # Thought (internal monologue indicators)
        thought_indicators = ["thought", "thinking", "wondered", "realized"]
        if any(ind in character for ind in thought_indicators):
            return "thought"
        
        # Whisper (quiet speech indicators)
        if "whisper" in text.lower() or text.startswith("*") or text.endswith("*"):
            return "whisper"
        
        # Shout (loud speech indicators)
        if text.isupper() or "!" in text or "yell" in character or "shout" in character:
            return "shout"
        
        # Default to normal speech
        return "speech"
    
    def _wrap_text(self, text: str, font: ImageFont.FreeTypeFont, max_width: int) -> List[str]:
        """Wrap text to fit within max width."""
        words = text.split()
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            bbox = font.getbbox(test_line)
            width = bbox[2] - bbox[0]
            
            if width <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
        
        if current_line:
            lines.append(' '.join(current_line))
        
        return lines
    
    def _draw_speech_bubble(
        self,
        draw: ImageDraw.ImageDraw,
        text: str,
        position: Tuple[int, int],
        style: Dict,
        font: ImageFont.FreeTypeFont,
        max_width: int = 300,
        speaker_pos: Optional[Tuple[int, int]] = None
    ):
        """Draw a speech bubble with text."""
        # Wrap text
        lines = self._wrap_text(text, font, max_width - style["padding"] * 2)
        
        # Calculate bubble size
        line_heights = []
        max_line_width = 0
        for line in lines:
            bbox = font.getbbox(line)
            line_heights.append(bbox[3] - bbox[1])
            max_line_width = max(max_line_width, bbox[2] - bbox[0])
        
        bubble_width = max_line_width + style["padding"] * 2
        bubble_height = sum(line_heights) + style["padding"] * 2 + (len(lines) - 1) * 5
        
        x, y = position
        
        # Draw bubble background
        bubble_box = [x, y, x + bubble_width, y + bubble_height]
        
        if style.get("border_style") == "jagged":
            # Jagged border for shouts
            self._draw_jagged_rectangle(draw, bubble_box, style)
        elif style.get("border_style") == "dashed":
            # Dashed border for whispers
            self._draw_dashed_rectangle(draw, bubble_box, style)
        else:
            # Normal rounded rectangle
            draw.rounded_rectangle(
                bubble_box,
                radius=style["corner_radius"],
                fill=style["bg_color"],
                outline=style["border_color"],
                width=style["border_width"]
            )
        
        # Draw tail if needed
        if style.get("has_tail") and speaker_pos:
            self._draw_bubble_tail(draw, bubble_box, speaker_pos, style)
        
        # Draw text
        text_y = y + style["padding"]
        for line in lines:
            draw.text(
                (x + style["padding"], text_y),
                line,
                fill=style["text_color"],
                font=font
            )
            bbox = font.getbbox(line)
            text_y += (bbox[3] - bbox[1]) + 5
    
    def _draw_jagged_rectangle(self, draw: ImageDraw.ImageDraw, box: List[int], style: Dict):
        """Draw a jagged rectangle for shouts."""
        x1, y1, x2, y2 = box
        
        # Draw filled background
        draw.rectangle(box, fill=style["bg_color"])
        
        # Draw jagged border
        points = []
        step = 15
        
        # Top edge
        for x in range(x1, x2, step):
            points.append((x, y1 + (5 if (x - x1) // step % 2 == 0 else -5)))
        
        # Right edge
        for y in range(y1, y2, step):
            points.append((x2 + (5 if (y - y1) // step % 2 == 0 else -5), y))
        
        # Bottom edge
        for x in range(x2, x1, -step):
            points.append((x, y2 + (5 if (x2 - x) // step % 2 == 0 else -5)))
        
        # Left edge
        for y in range(y2, y1, -step):
            points.append((x1 + (5 if (y2 - y) // step % 2 == 0 else -5), y))
        
        if len(points) > 2:
            draw.polygon(points, outline=style["border_color"], width=style["border_width"])
    
    def _draw_dashed_rectangle(self, draw: ImageDraw.ImageDraw, box: List[int], style: Dict):
        """Draw a dashed rectangle for whispers."""
        x1, y1, x2, y2 = box
        
        # Draw filled background
        draw.rounded_rectangle(
            box,
            radius=style["corner_radius"],
            fill=style["bg_color"]
        )
        
        # Draw dashed border
        dash_length = 10
        gap_length = 5
        
        # Top and bottom
        for x in range(x1, x2, dash_length + gap_length):
            draw.line([(x, y1), (min(x + dash_length, x2), y1)], 
                     fill=style["border_color"], width=style["border_width"])
            draw.line([(x, y2), (min(x + dash_length, x2), y2)], 
                     fill=style["border_color"], width=style["border_width"])
        
        # Left and right
        for y in range(y1, y2, dash_length + gap_length):
            draw.line([(x1, y), (x1, min(y + dash_length, y2))], 
                     fill=style["border_color"], width=style["border_width"])
            draw.line([(x2, y), (x2, min(y + dash_length, y2))], 
                     fill=style["border_color"], width=style["border_width"])
    
    def _draw_bubble_tail(
        self,
        draw: ImageDraw.ImageDraw,
        bubble_box: List[int],
        speaker_pos: Tuple[int, int],
        style: Dict
    ):
        """Draw a tail pointing from bubble to speaker."""
        bx1, by1, bx2, by2 = bubble_box
        sx, sy = speaker_pos
        
        # Find closest point on bubble edge
        bubble_center_x = (bx1 + bx2) // 2
        bubble_center_y = (by1 + by2) // 2
        
        # Determine which side of bubble to attach tail
        if sy < by1:  # Speaker above
            tail_start = (bubble_center_x, by1)
        elif sy > by2:  # Speaker below
            tail_start = (bubble_center_x, by2)
        elif sx < bx1:  # Speaker left
            tail_start = (bx1, bubble_center_y)
        else:  # Speaker right
            tail_start = (bx2, bubble_center_y)
        
        # Draw triangular tail
        tail_width = 20
        angle = math.atan2(sy - tail_start[1], sx - tail_start[0])
        
        p1 = tail_start
        p2 = (
            int(tail_start[0] + tail_width * math.cos(angle + math.pi / 6)),
            int(tail_start[1] + tail_width * math.sin(angle + math.pi / 6))
        )
        p3 = (
            int(tail_start[0] + tail_width * math.cos(angle - math.pi / 6)),
            int(tail_start[1] + tail_width * math.sin(angle - math.pi / 6))
        )
        
        draw.polygon([p1, p2, p3], fill=style["bg_color"], outline=style["border_color"])
    
    def _draw_sound_effect(
        self,
        draw: ImageDraw.ImageDraw,
        text: str,
        position: Tuple[int, int],
        style: Dict,
        font: ImageFont.FreeTypeFont
    ):
        """Draw a sound effect with outline."""
        x, y = position
        
        # Draw text outline
        if style.get("text_outline"):
            outline_width = style.get("outline_width", 3)
            for dx in range(-outline_width, outline_width + 1):
                for dy in range(-outline_width, outline_width + 1):
                    if dx != 0 or dy != 0:
                        draw.text(
                            (x + dx, y + dy),
                            text,
                            fill=style["text_outline"],
                            font=font
                        )
        
        # Draw main text
        draw.text((x, y), text, fill=style["text_color"], font=font)
    
    def add_text_to_panel(
        self,
        image: Image.Image,
        panel_data: Dict,
        detections: List[Dict]
    ) -> Image.Image:
        """
        Add all text overlays to a panel image.
        
        Args:
            image: PIL Image of the panel
            panel_data: Panel metadata with dialogue, narration, sound_effects
            detections: Detected bounding boxes for important objects
        
        Returns:
            Image with text overlays added
        """
        img = image.copy()
        draw = ImageDraw.Draw(img)
        
        img_width, img_height = img.size
        
        # Scale placer to image dimensions
        self.placer.width = int(1000 * img_width / img_width)  # Keep normalized
        self.placer.height = int(1000 * img_height / img_height)
        
        # Process dialogue
        dialogue = panel_data.get("dialogue", [])
        for entry in dialogue:
            text_type = self._detect_text_type(entry)
            text = entry.get("text", "")
            character = entry.get("character", "")
            
            if not text or text_type == "skip":
                continue
            
            # Get style for text type
            style = getattr(ComicTextStyle, text_type.upper(), ComicTextStyle.SPEECH)
            
            # Get font
            font_key = style.get("font_weight", "normal")
            font = self.fonts.get(font_key, self.fonts["normal"])
            
            # Find placement
            if text_type == "sound_effect":
                # Sound effects go in center or near action
                placement = TextPlacement(
                    position="center",
                    box=None,
                    confidence=1.0,
                    reason="Sound effect"
                )
                pos_x = img_width // 2
                pos_y = img_height // 3
                self._draw_sound_effect(draw, text, (pos_x, pos_y), style, self.fonts["large"])
            
            elif text_type == "narration":
                # Skip overly long narration (more than 100 chars)
                if len(text) > 100:
                    logger.debug(f"Skipping long narration: {len(text)} chars")
                    continue
                
                # Narration goes in corner caption box (not spanning full width)
                placement = self.placer.suggest_caption_placement(detections, text_type="caption")
                if placement:
                    # Place in top-left or top-right corner, not full width
                    if "left" in placement.position or placement.position == "top":
                        x = 10  # Left corner
                    else:
                        x = img_width - 260  # Right corner
                    
                    y = 10  # Top of panel
                    max_width = style.get("max_width", 250)
                    
                    self._draw_speech_bubble(draw, text, (x, y), style, font, max_width=max_width)
            
            else:
                # Speech/thought bubbles near character
                placement = self.placer.suggest_speech_bubble_placement(detections, character)
                if placement:
                    x = int(placement.box.x_min * img_width / 1000)
                    y = int(placement.box.y_min * img_height / 1000)
                    
                    # Find speaker position for tail
                    speaker_pos = None
                    for det in detections:
                        if character.lower() in det.get("label", "").lower():
                            box = det.get("box_2d", [])
                            if len(box) == 4:
                                speaker_pos = (
                                    int((box[1] + box[3]) / 2 * img_width / 1000),
                                    int((box[0] + box[2]) / 2 * img_height / 1000)
                                )
                                break
                    
                    self._draw_speech_bubble(draw, text, (x, y), style, font, speaker_pos=speaker_pos)
        
        # Process sound effects field - only dramatic ones
        sound_effects = panel_data.get("sound_effects")
        if sound_effects:
            # Check if it's a dramatic sound effect
            dramatic_sounds = ["BANG", "CRASH", "BOOM", "SLAM", "CRACK", "GUNSHOT",
                             "SMASH", "THUD", "WHAM", "POW", "KABOOM", "SCREECH"]
            if any(sound in sound_effects.upper() for sound in dramatic_sounds):
                style = ComicTextStyle.SOUND_EFFECT
                pos_x = img_width // 2
                pos_y = img_height // 4
                self._draw_sound_effect(draw, sound_effects, (pos_x, pos_y), style, self.fonts["large"])
        
        return img


if __name__ == "__main__":
    import json
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python comic_text_overlay.py <image_path> <detection_json_path>")
        sys.exit(1)
    
    image_path = sys.argv[1]
    detection_path = sys.argv[2]
    
    # Load detections
    with open(detection_path, 'r') as f:
        data = json.load(f)
    
    detections = data.get('detections', [])
    
    # Load image
    img = Image.open(image_path)
    
    # Example panel data
    panel_data = {
        "dialogue": [
            {"character": "Narrator", "text": "The warehouse squatted on the waterfront—rusted tin, broken glass."},
            {"character": "Jack", "text": "Another body. Another case."}
        ],
        "sound_effects": "DRIP DRIP"
    }
    
    # Add text
    overlay = ComicTextOverlay()
    result = overlay.add_text_to_panel(img, panel_data, detections)
    
    # Save
    output_path = Path(image_path).parent / f"{Path(image_path).stem}_with_text.png"
    result.save(output_path)
    print(f"✅ Saved image with text to: {output_path}")
