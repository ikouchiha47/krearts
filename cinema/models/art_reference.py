"""
Art Reference Models

Defines the structure for art style reference images with tags,
analysis metadata, and usage context.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from pathlib import Path


class ArtReferenceTag(BaseModel):
    """
    A tag describing what the reference image shows (input characteristics).
    
    Tags describe the reference image itself, NOT what you're generating.
    Example: 'motion_lines' describes what the image shows, not when to use it.
    """
    
    category: str = Field(
        ...,
        description="Tag category (e.g., 'action', 'art_technique', 'color_style', 'subject_matter')"
    )
    value: str = Field(
        ...,
        description="Tag value describing what the image shows (e.g., 'motion_lines', 'halftone', 'dramatic_lighting', 'character_design')"
    )
    weight: float = Field(
        default=1.0,
        description="Tag importance weight (0.0-1.0, higher = more important for this reference)"
    )


class ArtReferenceAnalysis(BaseModel):
    """Analysis metadata extracted from the reference image."""
    
    # Visual characteristics
    dominant_colors: List[str] = Field(
        default_factory=list,
        description="Dominant colors in hex format (e.g., ['#1a1a1a', '#ff0000'])"
    )
    
    color_palette_description: Optional[str] = Field(
        None,
        description="Description of color palette (e.g., 'Muted blues and grays with red accents')"
    )
    
    line_work_style: Optional[str] = Field(
        None,
        description="Line work characteristics (e.g., 'Variable weight, clean', 'Rough sketchy')"
    )
    
    rendering_technique: Optional[str] = Field(
        None,
        description="Rendering approach (e.g., 'Halftone dots', 'Painterly brushwork', 'Flat colors')"
    )
    
    lighting_style: Optional[str] = Field(
        None,
        description="Lighting characteristics (e.g., 'High contrast noir', 'Soft diffused', 'Dramatic rim lighting')"
    )
    
    composition_notes: Optional[str] = Field(
        None,
        description="Composition and framing notes (e.g., 'Rule of thirds', 'Centered symmetry', 'Dynamic diagonal')"
    )
    
    texture_details: Optional[str] = Field(
        None,
        description="Texture and surface qualities (e.g., 'Visible halftone dots', 'Smooth gradients', 'Paper texture')"
    )
    
    # Technical details
    aspect_ratio: Optional[str] = Field(
        None,
        description="Image aspect ratio (e.g., '16:9', '4:5', '1:1')"
    )
    
    resolution: Optional[str] = Field(
        None,
        description="Image resolution (e.g., '1920x1080')"
    )
    
    # AI-generated analysis
    ai_description: Optional[str] = Field(
        None,
        description="AI-generated description of the image style and characteristics"
    )
    
    analyzed_at: Optional[str] = Field(
        None,
        description="Timestamp of analysis (ISO format)"
    )


class ArtReference(BaseModel):
    """
    A reference image with tags, analysis, and usage context.
    
    This is the core object combining:
    - The image file path
    - Descriptive tags for matching
    - Analyzed visual characteristics
    - Text prompt describing the style
    """
    
    # Identity
    id: str = Field(
        ...,
        description="Unique identifier (e.g., 'akira_motion_lines_01')"
    )
    
    name: str = Field(
        ...,
        description="Human-readable name (e.g., 'Akira Motion Lines Example')"
    )
    
    style: str = Field(
        ...,
        description="Art style category (e.g., 'akira', 'spiderverse', 'arcane')"
    )
    
    # File reference
    file_path: str = Field(
        ...,
        description="Relative path to image file (e.g., 'knowledge/art-styles/references/akira/motion_lines.jpg')"
    )
    
    # Tags for matching
    tags: List[ArtReferenceTag] = Field(
        default_factory=list,
        description="Tags categorizing this reference"
    )
    
    # Text description
    text_prompt: str = Field(
        ...,
        description="Text description of the style characteristics for prompting"
    )
    
    purpose: str = Field(
        ...,
        description="What this reference is best used for"
    )
    
    # Analysis metadata
    analysis: Optional[ArtReferenceAnalysis] = Field(
        None,
        description="Analyzed visual characteristics"
    )
    
    # Usage context
    use_for_shot_types: List[str] = Field(
        default_factory=list,
        description="Recommended shot types (e.g., ['wide', 'establishing', 'action'])"
    )
    
    use_for_scene_types: List[str] = Field(
        default_factory=list,
        description="Recommended scene types (e.g., ['action', 'chase', 'fight'])"
    )
    
    use_for_panel_layouts: List[str] = Field(
        default_factory=list,
        description="Recommended panel layouts (e.g., ['grid-8-panel', 'dynamic-grid'])"
    )
    
    use_for_emotional_tones: List[str] = Field(
        default_factory=list,
        description="Recommended emotional tones (e.g., ['thrilling', 'intense', 'dramatic'])"
    )
    
    # Metadata
    source: Optional[str] = Field(
        None,
        description="Source of the reference (e.g., 'Akira Vol. 1, Page 45')"
    )
    
    artist: Optional[str] = Field(
        None,
        description="Original artist (e.g., 'Katsuhiro Otomo')"
    )
    
    notes: Optional[str] = Field(
        None,
        description="Additional notes about this reference"
    )
    
    def get_tags_by_category(self, category: str) -> List[str]:
        """Get all tag values for a specific category."""
        return [tag.value for tag in self.tags if tag.category == category]
    
    def has_tag(self, category: str, value: str) -> bool:
        """Check if reference has a specific tag."""
        return any(
            tag.category == category and tag.value == value
            for tag in self.tags
        )
    
    def get_tag_weight(self, category: str, value: str) -> float:
        """Get the weight of a specific tag."""
        for tag in self.tags:
            if tag.category == category and tag.value == value:
                return tag.weight
        return 0.0
    
    def matches_context(
        self,
        shot_type: Optional[str] = None,
        scene_type: Optional[str] = None,
        panel_layout: Optional[str] = None,
        emotional_tone: Optional[str] = None,
        required_tags: Optional[Dict[str, str]] = None
    ) -> float:
        """
        Calculate match score for given context.
        
        Returns:
            Score from 0.0 to 1.0 (higher = better match)
        """
        score = 0.0
        max_score = 0.0
        
        # Check shot type
        if shot_type:
            max_score += 1.0
            if shot_type in self.use_for_shot_types:
                score += 1.0
        
        # Check scene type
        if scene_type:
            max_score += 1.0
            if scene_type in self.use_for_scene_types:
                score += 1.0
        
        # Check panel layout
        if panel_layout:
            max_score += 1.5  # Higher weight
            if panel_layout in self.use_for_panel_layouts:
                score += 1.5
        
        # Check emotional tone
        if emotional_tone:
            max_score += 0.5
            if emotional_tone in self.use_for_emotional_tones:
                score += 0.5
        
        # Check required tags
        if required_tags:
            for category, value in required_tags.items():
                max_score += 1.0
                if self.has_tag(category, value):
                    weight = self.get_tag_weight(category, value)
                    score += weight
        
        # Normalize to 0-1 range
        if max_score > 0:
            return score / max_score
        return 0.0


class ArtReferenceLibrary(BaseModel):
    """Collection of art references for a specific style."""
    
    style: str = Field(
        ...,
        description="Art style name (e.g., 'akira', 'spiderverse')"
    )
    
    description: str = Field(
        ...,
        description="Description of the art style"
    )
    
    characteristics: List[str] = Field(
        default_factory=list,
        description="Key characteristics of this style"
    )
    
    references: List[ArtReference] = Field(
        default_factory=list,
        description="Collection of reference images"
    )
    
    # Tag categories used in this library
    tag_categories: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="Available tag categories and their possible values"
    )
    
    def get_reference_by_id(self, ref_id: str) -> Optional[ArtReference]:
        """Get a reference by its ID."""
        for ref in self.references:
            if ref.id == ref_id:
                return ref
        return None
    
    def get_references_by_tag(
        self,
        category: str,
        value: str,
        min_weight: float = 0.0
    ) -> List[ArtReference]:
        """Get all references with a specific tag."""
        return [
            ref for ref in self.references
            if ref.has_tag(category, value) and ref.get_tag_weight(category, value) >= min_weight
        ]
    
    def find_best_references(
        self,
        shot_type: Optional[str] = None,
        scene_type: Optional[str] = None,
        panel_layout: Optional[str] = None,
        emotional_tone: Optional[str] = None,
        required_tags: Optional[Dict[str, str]] = None,
        max_results: int = 3
    ) -> List[ArtReference]:
        """
        Find the best matching references for given context.
        
        Returns:
            List of references sorted by match score (best first)
        """
        # Score all references
        scored = [
            (ref, ref.matches_context(shot_type, scene_type, panel_layout, emotional_tone, required_tags))
            for ref in self.references
        ]
        
        # Sort by score (highest first)
        scored.sort(key=lambda x: x[1], reverse=True)
        
        # Return top N
        return [ref for ref, score in scored[:max_results] if score > 0]
    
    def get_all_tags(self) -> Dict[str, List[str]]:
        """Get all unique tags across all references."""
        tags_by_category: Dict[str, set] = {}
        
        for ref in self.references:
            for tag in ref.tags:
                if tag.category not in tags_by_category:
                    tags_by_category[tag.category] = set()
                tags_by_category[tag.category].add(tag.value)
        
        # Convert sets to sorted lists
        return {
            category: sorted(list(values))
            for category, values in tags_by_category.items()
        }


# Example tag categories
# These describe WHAT THE REFERENCE IMAGE SHOWS, not what you're generating
TAG_CATEGORIES = {
    "action": [
        "motion_lines",        # Shows speed lines/motion effects
        "speed_effects",       # Shows velocity/blur effects
        "impact",              # Shows impact moments
        "explosion",           # Shows explosive effects
        "fight",               # Shows combat/fighting
        "chase",               # Shows chase sequences
        "static",              # Shows static/still moments
        "dialogue"             # Shows conversation/dialogue scenes
    ],
    "art_technique": [
        "halftone",            # Uses halftone dot patterns (Spider-Verse)
        "ben_day_dots",        # Uses Ben-Day dot printing
        "ligne_claire",        # Uses clear line style (Blueberry)
        "painterly",           # Uses painterly brushwork (Arcane)
        "flat_colors",         # Uses flat color fills
        "gradients",           # Uses color gradients
        "cross_hatching",      # Uses cross-hatched shading
        "stippling",           # Uses dot-based shading
        "chromatic_aberration" # Uses RGB color separation
    ],
    "color_style": [
        "black_and_white",     # Monochrome
        "high_contrast",       # Strong contrast
        "muted_palette",       # Desaturated colors
        "vibrant_colors",      # Saturated, bold colors
        "monochromatic",       # Single color variations
        "complementary",       # Complementary color scheme
        "analogous",           # Analogous color scheme
        "noir",                # Noir color scheme
        "neon"                 # Neon/cyberpunk colors
    ],
    "lighting": [
        "dramatic",            # High contrast dramatic lighting
        "soft_diffused",       # Soft, even lighting
        "high_contrast",       # Strong light/shadow contrast
        "rim_lighting",        # Backlighting/rim light
        "backlighting",        # Light from behind
        "overhead",            # Light from above
        "natural",             # Natural daylight
        "artificial"           # Artificial/indoor lighting
    ],
    "composition": [
        "rule_of_thirds",      # Uses rule of thirds
        "centered",            # Centered subject
        "symmetrical",         # Symmetrical framing
        "diagonal",            # Diagonal composition
        "dynamic",             # Dynamic, energetic framing
        "static",              # Static, stable framing
        "close_framing",       # Tight framing
        "wide_framing"         # Wide, expansive framing
    ],
    "subject_matter": [
        "character_design",    # Shows character design
        "environment",         # Shows environmental/background
        "mechanical_detail",   # Shows mechanical/technical details
        "organic_forms",       # Shows organic/natural forms
        "architecture",        # Shows architectural elements
        "vehicles",            # Shows vehicle design
        "weapons",             # Shows weapon design
        "clothing",            # Shows clothing/costume design
        "facial_expression",   # Shows facial expressions
        "body_language"        # Shows body language/poses
    ],
    "visual_density": [
        "sparse",              # Minimal detail, lots of negative space
        "moderate",            # Balanced detail level
        "dense",               # High detail, busy composition
        "cluttered"            # Very busy, complex composition
    ],
    "texture": [
        "smooth",              # Smooth, clean surfaces
        "rough",               # Rough, textured surfaces
        "grainy",              # Grainy/noisy texture
        "paper_texture",       # Visible paper texture
        "digital_clean"        # Clean digital rendering
    ]
}
