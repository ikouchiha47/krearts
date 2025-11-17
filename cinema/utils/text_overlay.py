"""
Text overlay utilities for comic pages.
Adds dialogue bubbles and narration boxes to generated images.
"""
from pathlib import Path
from typing import List, Dict, Any, Tuple
from PIL import Image, ImageDraw, ImageFont
import textwrap


class ComicTextOverlay:
    """Add text overlays (dialogue, narration) to comic page images."""
    
    def __init__(self, font_path: str = None):
        """
        Initialize text overlay system.
        
        Args:
            font_path: Path to TTF font file. If None, uses default system font.
        """
        self.font_path = font_path
        
        # Try to load fonts
        try:
            if font_path and Path(font_path).exists():
                self.dialogue_font = ImageFont.truetype(font_path, 18)
                self.narration_font = ImageFont.truetype(font_path, 16)
                self.character_font = ImageFont.truetype(font_path, 14)
            else:
                # Try common system fonts (smaller, sharper)
                self.dialogue_font = self._load_system_font(18)
                self.narration_font = self._load_system_font(16)
                self.character_font = self._load_system_font(14)
        except Exception as e:
            print(f"⚠️  Font loading failed: {e}, using default")
            self.dialogue_font = ImageFont.load_default()
            self.narration_font = ImageFont.load_default()
            self.character_font = ImageFont.load_default()
    
    def _load_system_font(self, size: int) -> ImageFont.FreeTypeFont:
        """Try to load a system font."""
        font_paths = [
            "/System/Library/Fonts/Helvetica.ttc",  # macOS
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",  # Linux
            "C:\\Windows\\Fonts\\arial.ttf",  # Windows
        ]
        
        for path in font_paths:
            if Path(path).exists():
                return ImageFont.truetype(path, size)
        
        return ImageFont.load_default()
    
    def add_text_to_page(
        self,
        image: Image.Image,
        panels_data: List[Dict[str, Any]],
        panel_layout: str,
        page_size: Tuple[int, int] = (1024, 1280),
        style: str = "below_panel"
    ) -> Image.Image:
        """
        Add text overlays to comic page.
        
        Styles:
        - "below_panel": Caption box below each panel (RECOMMENDED - doesn't cover image)
        - "in_panel": Caption boxes overlaid at bottom of each panel
        - "below_page": Caption bar below entire page
        
        Args:
            image: PIL Image of the page
            panels_data: List of panel data with dialogue/narration
            panel_layout: Layout type (e.g., "vertical-2-panel")
            page_size: Page dimensions
            style: Text overlay style
            
        Returns:
            Image with text overlays
        """
        if style == "below_panel":
            return self._add_below_panel_captions(image, panels_data, panel_layout, page_size)
        elif style == "in_panel":
            return self._add_in_panel_captions(image, panels_data, panel_layout, page_size)
        else:
            return self._add_below_page_captions(image, panels_data)
    
    def _add_below_panel_captions(
        self,
        image: Image.Image,
        panels_data: List[Dict[str, Any]],
        panel_layout: str,
        page_size: Tuple[int, int]
    ) -> Image.Image:
        """
        Add caption boxes overlapping the bottom of each panel.
        Caption sits on the bottom edge of the panel, partially overlaying it.
        """
        # Make a copy to draw on
        img = image.copy()
        draw = ImageDraw.Draw(img)
        
        # Calculate panel positions
        panel_positions = self._calculate_panel_positions(panel_layout, page_size)
        
        # Calculate max caption height needed
        max_caption_height = 0
        for panel_data in panels_data:
            text = panel_data.get('narration') or (panel_data.get('dialogue', [{}])[0].get('text') if panel_data.get('dialogue') else None)
            if text:
                max_chars = int((page_size[0] - 60) / 7)
                wrapped = textwrap.fill(text, width=max_chars)
                lines = wrapped.count('\n') + 1
                cap_height = (lines * 18) + 16
                max_caption_height = max(max_caption_height, cap_height)
        
        if max_caption_height == 0:
            return image
        
        # Extend canvas to fit captions
        gap = 2
        new_height = page_size[1] + max_caption_height + gap + 10  # Extra padding
        canvas = Image.new('RGB', (page_size[0], new_height), color=(255, 255, 255))
        canvas.paste(image, (0, 0))
        
        draw = ImageDraw.Draw(canvas)
        
        # Draw captions below each panel
        for panel_data, (px, py, pw, ph) in zip(panels_data, panel_positions):
            # Get text
            text = panel_data.get('narration')
            character = 'Narrator'
            if not text and panel_data.get('dialogue'):
                d = panel_data['dialogue'][0]
                text = d.get('text')
                character = d.get('character')
            
            if not text:
                continue
            
            # Calculate caption height
            max_chars = int((pw - 40) / 7)
            wrapped = textwrap.fill(text, width=max_chars)
            lines = wrapped.count('\n') + 1
            cap_height = (lines * 18) + 16  # Tight padding
            
            # Position caption just below panel border with 2px gap
            caption_y = py + ph + 2  # 2px gap from bottom border
            caption_x = px + 15  # Small margin from panel edge
            caption_width = pw - 30  # Leave margins
            
            # Draw caption box
            self._draw_caption_box_simple(
                draw, text, character,
                caption_x, caption_y,
                caption_width, cap_height
            )
        
        return canvas
    
    def _draw_caption_box_simple(
        self,
        draw: ImageDraw.ImageDraw,
        text: str,
        character: str,
        x: int,
        y: int,
        width: int,
        height: int
    ):
        """Draw a simple caption box."""
        # Draw border
        draw.rectangle(
            [x, y, x + width, y + height],
            fill=(255, 255, 255),
            outline=(0, 0, 0),
            width=2
        )
        
        # Wrap and draw text
        max_chars = int((width - 20) / 7)
        wrapped = textwrap.fill(text, width=max_chars)
        
        draw.multiline_text(
            (x + 10, y + 10),
            wrapped,
            fill=(0, 0, 0),
            font=self.narration_font,
            spacing=2
        )
    
    def _add_in_panel_captions(
        self,
        image: Image.Image,
        panels_data: List[Dict[str, Any]],
        panel_layout: str,
        page_size: Tuple[int, int]
    ) -> Image.Image:
        """
        Add caption boxes overlaid at bottom of each panel.
        Classic comic book style - captions are part of the panel.
        """
        img = image.copy()
        draw = ImageDraw.Draw(img)
        
        # Calculate panel positions
        panel_positions = self._calculate_panel_positions(panel_layout, page_size)
        
        # Add caption to each panel that has text
        for panel_data, (px, py, pw, ph) in zip(panels_data, panel_positions):
            # Get text
            text = None
            character = None
            
            # Prefer narration for captions
            if panel_data.get('narration'):
                text = panel_data['narration']
                character = 'Narrator'
            elif panel_data.get('dialogue'):
                # Use first dialogue
                d = panel_data['dialogue'][0]
                text = d.get('text')
                character = d.get('character')
            
            if not text:
                continue
            
            # Draw caption at bottom of this panel
            self._draw_in_panel_caption(draw, text, character, px, py, pw, ph)
        
        return img
    
    def _calculate_panel_positions(
        self,
        layout: str,
        page_size: Tuple[int, int]
    ) -> List[Tuple[int, int, int, int]]:
        """Calculate panel positions (x, y, width, height)."""
        page_width, page_height = page_size
        gutter = 20
        
        layout_configs = {
            "vertical-2-panel": {"rows": 2, "cols": 1},
            "vertical-3-panel": {"rows": 3, "cols": 1},
            "horizontal-2-panel": {"rows": 1, "cols": 2},
            "horizontal-3-panel": {"rows": 1, "cols": 3},
            "dynamic-grid": {"rows": 2, "cols": 2},
        }
        
        config = layout_configs.get(layout, {"rows": 2, "cols": 1})
        rows = config["rows"]
        cols = config["cols"]
        
        panel_height = (page_height - (rows + 1) * gutter) // rows
        panel_width = (page_width - (cols + 1) * gutter) // cols
        
        positions = []
        for row in range(rows):
            for col in range(cols):
                x = gutter + col * (panel_width + gutter)
                y = gutter + row * (panel_height + gutter)
                positions.append((x, y, panel_width, panel_height))
        
        return positions
    
    def _draw_in_panel_caption(
        self,
        draw: ImageDraw.ImageDraw,
        text: str,
        character: str,
        panel_x: int,
        panel_y: int,
        panel_width: int,
        panel_height: int
    ):
        """Draw caption box at bottom of panel."""
        # Caption dimensions
        caption_margin = 15
        caption_padding = 10
        max_chars = int((panel_width - 2 * caption_margin - 2 * caption_padding) / 7)
        
        # Wrap text
        wrapped = textwrap.fill(text, width=max_chars)
        lines = wrapped.count('\n') + 1
        
        # Calculate caption size
        line_height = 18
        caption_height = (lines * line_height) + (2 * caption_padding)
        caption_width = panel_width - (2 * caption_margin)
        
        # Position at bottom of panel
        caption_x = panel_x + caption_margin
        caption_y = panel_y + panel_height - caption_height - caption_margin
        
        # Draw caption box
        draw.rectangle(
            [caption_x, caption_y, caption_x + caption_width, caption_y + caption_height],
            fill=(255, 255, 255),
            outline=(0, 0, 0),
            width=2
        )
        
        # Draw text
        text_x = caption_x + caption_padding
        text_y = caption_y + caption_padding
        
        draw.multiline_text(
            (text_x, text_y),
            wrapped,
            fill=(0, 0, 0),
            font=self.narration_font,
            spacing=2
        )
    
    def _add_below_page_captions(
        self,
        image: Image.Image,
        panels_data: List[Dict[str, Any]]
    ) -> Image.Image:
        """Add caption bars below the entire page (old style)."""
        # Collect all text from panels (max 2: one top, one bottom)
        all_text = []
        
        for panel_data in panels_data:
            # Collect dialogue
            dialogue = panel_data.get('dialogue', [])
            for d in dialogue:
                text = d.get('text', '')
                character = d.get('character', '')
                if text:
                    all_text.append({
                        'text': text,
                        'character': character,
                        'type': 'dialogue'
                    })
            
            # Collect narration
            narration = panel_data.get('narration', '')
            if narration:
                all_text.append({
                    'text': narration,
                    'character': 'Narrator',
                    'type': 'narration'
                })
        
        # Limit to 2 text items max
        if len(all_text) > 2:
            all_text = all_text[:2]
        
        if not all_text:
            return image
        
        # Create new canvas with text bars
        return self._create_canvas_with_text_bars(image, all_text)
    
    def _create_canvas_with_text_bars(
        self,
        image: Image.Image,
        text_items: List[Dict[str, str]]
    ) -> Image.Image:
        """
        Create new canvas with tight caption boxes below image.
        
        Args:
            image: Original comic page image
            text_items: List of text items (max 2)
            
        Returns:
            New image with caption boxes
        """
        img_width, img_height = image.size
        
        # Calculate actual text heights needed (tight fit)
        text_heights = []
        for item in text_items:
            height = self._calculate_text_height(item, img_width)
            text_heights.append(height)
        
        # Total height with minimal spacing
        spacing = 8  # Minimal spacing between boxes
        total_text_height = sum(text_heights) + (spacing * (len(text_items) + 1))
        total_height = img_height + total_text_height
        
        # Create new canvas (white background)
        canvas = Image.new('RGB', (img_width, total_height), color=(255, 255, 255))
        draw = ImageDraw.Draw(canvas)
        
        # Paste original image at top
        canvas.paste(image, (0, 0))
        
        # Draw caption boxes below image with tight spacing
        current_y = img_height + spacing
        for i, (text_item, height) in enumerate(zip(text_items, text_heights)):
            self._draw_caption_box(draw, text_item, 0, current_y, img_width, height)
            current_y += height + spacing
        
        return canvas
    
    def _calculate_text_height(self, text_item: Dict[str, str], width: int) -> int:
        """Calculate tight height needed for text."""
        text = text_item['text']
        character = text_item['character']
        
        # Wrap text
        max_chars = int((width - 60) / 7)
        wrapped = textwrap.fill(text, width=max_chars)
        
        # Calculate height based on lines
        lines = wrapped.count('\n') + 1
        line_height = 20
        padding = 16  # Tight padding
        
        # Add space for character name if present
        if character and character != 'Narrator':
            padding += 20
        
        return (lines * line_height) + padding
    
    def _draw_caption_box(
        self,
        draw: ImageDraw.ImageDraw,
        text_item: Dict[str, str],
        x: int,
        y: int,
        width: int,
        height: int
    ):
        """
        Draw a tight comic book caption box.
        
        Professional comic book style:
        - White background, black text
        - Thick black border (2-3px)
        - Minimal padding, tight fit
        - Spans most of width with small margins
        
        Args:
            draw: ImageDraw object
            text_item: Text data with 'text', 'character', 'type'
            x, y: Position
            width, height: Box dimensions
        """
        text = text_item['text']
        character = text_item['character']
        text_type = text_item['type']
        
        # Comic book style
        bg_color = (255, 255, 255)
        text_color = (0, 0, 0)
        border_width = 2
        
        # Tight margins (like real comics)
        margin = 20
        box_width = width - (2 * margin)
        box_x = x + margin
        box_y = y
        box_height = height
        
        # Draw border
        draw.rectangle(
            [box_x, box_y, box_x + box_width, box_y + box_height],
            fill=bg_color,
            outline=text_color,
            width=border_width
        )
        
        # Wrap text tightly
        max_chars = int((box_width - 30) / 7)
        wrapped = textwrap.fill(text, width=max_chars)
        
        # Position text with minimal padding
        text_x = box_x + 12
        text_y = box_y + 8
        
        # Character name (if dialogue)
        if text_type == 'dialogue' and character and character != 'Narrator':
            draw.text(
                (text_x, text_y),
                f"{character.upper()}:",
                fill=text_color,
                font=self.character_font
            )
            text_y += 18
        
        # Main text
        draw.multiline_text(
            (text_x, text_y),
            wrapped,
            fill=text_color,
            font=self.narration_font,
            spacing=2
        )
    



def add_text_to_comic_page(
    image_path: str,
    output_path: str,
    panels_data: List[Dict[str, Any]],
    panel_layout: str,
    page_size: Tuple[int, int] = (1024, 1280)
) -> str:
    """
    Convenience function to add text to a comic page.
    
    Args:
        image_path: Path to input image
        output_path: Path to save output image
        panels_data: Panel data with dialogue/narration
        panel_layout: Layout type
        page_size: Page dimensions
        
    Returns:
        Path to output image
    """
    overlay = ComicTextOverlay()
    
    # Load image
    img = Image.open(image_path)
    
    # Add text
    img_with_text = overlay.add_text_to_page(img, panels_data, panel_layout, page_size)
    
    # Save
    img_with_text.save(output_path)
    
    return output_path
