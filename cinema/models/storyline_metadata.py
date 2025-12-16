"""
Parser for storyline metadata from DetectivePlotBuilder output.

The storyline is generated as markdown with structured metadata:

## Storyline

### Metadata
- Theme: <description>
- Genre: <description>
- Adults Only: <boolean>
- Narrative Structure: "<linear or non-linear>/<which_specific_structure>"
- Art Style: <description>
- Story Telling Style: <description>
- Suited For: movie, shorts, microdrama, tv-show, novel, short-story, comic book
- Colors: list of color name with their hex codes. (<color_name>(#<hex_code>)...)
- Cover/Thumbnail Image Concept: <description>
"""

import re
from typing import Optional, List, Tuple
from pydantic import BaseModel, Field, field_validator


class ColorPalette(BaseModel):
    """A color with name and hex code"""
    name: str
    hex_code: str
    
    def __str__(self) -> str:
        return f"{self.name}({self.hex_code})"


class StorylineMetadata(BaseModel):
    """
    Structured metadata extracted from storyline markdown output.
    
    This model represents the parsed metadata section from the DetectivePlotBuilder
    crew output. All fields are extracted from the markdown format.
    """
    
    # Core metadata
    title: Optional[str] = Field(default=None, description="Title of the book (1-3 words)")
    theme: str = Field(description="Central theme of the story")
    genre: str = Field(description="Story genre (e.g., Neo-noir detective mystery)")
    adults_only: bool = Field(default=False, description="Whether content is for adults only")
    narrative_structure: str = Field(description="Narrative structure type (e.g., linear/five-act)")
    
    # Visual and style metadata
    art_style: str = Field(description="Visual art style for comic adaptation")
    story_telling_style: str = Field(description="Narrative voice and storytelling approach")
    suited_for: str = Field(description="Target medium (comic book, tv-show, etc.)")
    
    # Color palette
    colors: List[ColorPalette] = Field(default_factory=list, description="Color palette with names and hex codes")
    
    # Cover design
    cover_concept: str = Field(description="Cover/thumbnail image concept description")
    
    # Raw storyline text (full markdown)
    raw_storyline: str = Field(default="", description="Complete storyline markdown text")
    
    @field_validator('colors', mode='before')
    @classmethod
    def parse_colors(cls, v):
        """Convert tuple list to ColorPalette objects if needed"""
        if not v:
            return []
        if isinstance(v, list) and len(v) > 0:
            if isinstance(v[0], tuple):
                return [ColorPalette(name=name, hex_code=hex_code) for name, hex_code in v]
        return v
    
    def to_dict(self) -> dict:
        """Convert to dictionary with colors as tuples for backward compatibility"""
        data = self.model_dump()
        data['colors'] = [(c.name, c.hex_code) for c in self.colors]
        return data


def parse_storyline_metadata(storyline_text: str) -> StorylineMetadata:
    """
    Parse storyline metadata from markdown text.
    
    Args:
        storyline_text: Raw storyline output from DetectivePlotBuilder
        
    Returns:
        StorylineMetadata with parsed fields
    
    Raises:
        ValueError: If required metadata fields are missing
    """
    # Extract metadata section first
    metadata_match = re.search(
        r'### Metadata\s*\n(.*?)(?=\n###|\n##|$)',
        storyline_text,
        re.DOTALL | re.IGNORECASE
    )
    
    if not metadata_match:
        raise ValueError("No metadata section found in storyline")
    
    metadata_section = metadata_match.group(1)
    
    # Parse required fields
    title = _extract_field(metadata_section, r'Title:\s*(.+)')
    
    # Fallback: extract H1 title from top of storyline if not in metadata
    if not title:
        h1_match = re.search(r'^#\s+(.+)$', storyline_text, re.MULTILINE)
        if h1_match:
            title = h1_match.group(1).strip()
    
    theme = _extract_field(metadata_section, r'Theme:\s*(.+)')
    genre = _extract_field(metadata_section, r'Genre:\s*(.+)')
    narrative_structure = _extract_field(metadata_section, r'Narrative Structure:\s*(.+)')
    art_style = _extract_field(metadata_section, r'Art Style:\s*(.+)')
    story_telling_style = _extract_field(metadata_section, r'Story Telling Style:\s*(.+)')
    suited_for = _extract_field(metadata_section, r'Suited For:\s*(.+)')
    cover_concept = _extract_field(metadata_section, r'Cover/Thumbnail Image Concept:\s*(.+)')
    
    # Validate required fields
    if not all([theme, genre, narrative_structure, art_style, story_telling_style, suited_for, cover_concept]):
        missing = []
        if not theme: missing.append("Theme")
        if not genre: missing.append("Genre")
        if not narrative_structure: missing.append("Narrative Structure")
        if not art_style: missing.append("Art Style")
        if not story_telling_style: missing.append("Story Telling Style")
        if not suited_for: missing.append("Suited For")
        if not cover_concept: missing.append("Cover Concept")
        raise ValueError(f"Missing required metadata fields: {', '.join(missing)}")
    
    # Parse optional boolean field
    adults_only_str = _extract_field(metadata_section, r'Adults Only:\s*(.+)')
    adults_only = adults_only_str.strip().lower() in ['true', 'yes', '1'] if adults_only_str else False
    
    # Parse colors
    colors_str = _extract_field(metadata_section, r'Colors:\s*(.+)')
    colors_list = _parse_colors(colors_str) if colors_str else []
    
    # Create metadata object
    metadata = StorylineMetadata(
        title=title,
        theme=theme,
        genre=genre,
        adults_only=adults_only,
        narrative_structure=narrative_structure,
        art_style=art_style,
        story_telling_style=story_telling_style,
        suited_for=suited_for,
        colors=[ColorPalette(name=name, hex_code=hex_code) for name, hex_code in colors_list],
        cover_concept=cover_concept,
        raw_storyline=storyline_text
    )
    
    return metadata


def _extract_field(text: str, pattern: str) -> Optional[str]:
    """Extract a single field value using regex pattern"""
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        value = match.group(1).strip()
        # Remove quotes if present
        value = value.strip('"\'')
        # Remove trailing punctuation
        value = value.rstrip('.,;')
        return value if value else None
    return None


def _parse_colors(colors_str: str) -> List[Tuple[str, str]]:
    """
    Parse color list from format: color_name(#hex), color_name(#hex), ...
    
    Examples:
        "Dark Blue(#1a1a2e), Crimson Red(#c0392b)"
        "noir-black(#000000), blood-red(#8B0000), fog-gray(#808080)"
    """
    colors = []
    
    # Match pattern: word(#hexcode)
    pattern = r'([a-zA-Z\s\-]+)\s*\(#([0-9a-fA-F]{6})\)'
    matches = re.findall(pattern, colors_str)
    
    for name, hex_code in matches:
        colors.append((name.strip(), f"#{hex_code}"))
    
    return colors


def extract_art_style_from_storyline(storyline_text: str) -> Optional[str]:
    """
    Quick extraction of just the art style field.
    Useful for backwards compatibility.
    """
    match = re.search(r'Art Style:\s*(.+)', storyline_text, re.IGNORECASE)
    if match:
        value = match.group(1).strip().strip('"\'').rstrip('.,;')
        return value if value else None
    return None
