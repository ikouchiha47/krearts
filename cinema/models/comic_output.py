"""
Comic Book Output Models - Captures full narrative from novel.

This model is designed to preserve the richness of a 15-chapter novel
and convert it into a properly paced comic book with 60-100+ panels.
"""

import logging
from typing import List, Literal, Optional
from pydantic import BaseModel, Field, model_validator

logger = logging.getLogger(__name__)


class DialogueLine(BaseModel):
    """Single line of dialogue with character attribution"""
    character: str = Field(..., description="Character name speaking (or 'Narrator' for captions)")
    text: str = Field(..., description="The dialogue or caption text")


class ComicPanel(BaseModel):
    """
    A single comic book panel with complete visual and narrative information.
    
    This captures everything needed to generate a consistent, visually rich panel.
    """
    
    # Panel identification
    panel_number: int = Field(..., description="Sequential panel number in the comic")
    chapter: int = Field(..., description="Which chapter this panel belongs to (1-15)")
    scene_number: int = Field(..., description="Scene number within the chapter")
    
    # Visual composition
    shot_type: Literal[
        "establishing", "wide", "medium", "close-up", "extreme close-up",
        "over-the-shoulder", "two-shot", "group shot"
    ] = Field(..., description="Camera framing type")
    
    camera_angle: Optional[Literal[
        "eye-level", "high-angle", "low-angle", "bird's-eye", "worm's-eye", "dutch-angle"
    ]] = Field(None, description="Camera angle for dramatic effect")
    
    # Visual description
    location: str = Field(..., description="Where this panel takes place")
    
    visual_description: str = Field(
        ...,
        description="Detailed visual description including: setting, lighting, character positions, props, atmosphere. Should be rich and specific."
    )
    
    # Characters and action
    characters_present: List[str] = Field(
        default_factory=list,
        description="List of character names visible in this panel"
    )
    
    primary_action: str = Field(
        ...,
        description="What is happening in this panel - the key action or moment"
    )
    
    # Dialogue and sound
    dialogue: List[DialogueLine] = Field(
        default_factory=list,
        description="Dialogue lines with character attribution"
    )
    
    sound_effects: Optional[str] = Field(
        None,
        description="Sound effects text (e.g., 'CRACK!', 'RUMBLE', 'DRIP DRIP')"
    )
    
    # Emotional and stylistic
    emotional_tone: str = Field(
        ...,
        description="Mood/emotion of the panel (e.g., 'tense', 'melancholic', 'thrilling')"
    )
    
    # Visual techniques (from knowledge/art-styles/styles.md)
    motion_type: Optional[Literal[
        "none", "speed-lines", "motion-blur", "impact-lines", "ghosting"
    ]] = Field(None, description="Type of motion representation")
    
    rendering_style: Optional[Literal[
        "photorealistic-with-overlays", "stylized-volumetric", "flat-graphic"
    ]] = Field(None, description="Rendering fidelity style")
    
    color_palette: Optional[str] = Field(
        None,
        description="Color palette description (e.g., 'desaturated blues with harsh red accent')"
    )
    
    # Layout
    orientation: Literal["Landscape", "Portrait", "Square"] = Field(
        default="Landscape",
        description="Panel orientation"
    )
    
    aspect_ratio: Optional[str] = Field(
        None,
        description="Panel aspect ratio (e.g., '16:9', '9:16', '1:1', '4:3')"
    )
    
    panel_size: Optional[Literal["small", "medium", "large", "splash"]] = Field(
        None,
        description="Relative size of panel on page"
    )


class ComicPage(BaseModel):
    """
    A physical comic book page containing 2-3 panels with layout specifications.
    
    Follows layout patterns from knowledge/layouts/panel_arrangements.md
    """
    
    # Page identification
    page_number: int = Field(..., description="Sequential page number in the chapter")
    chapter: int = Field(..., description="Which chapter this page belongs to")
    scene_number: int = Field(..., description="Scene number within the chapter")
    
    # Layout specification (from panel_arrangements.md)
    panel_arrangement: Literal[
        "horizontal-2-panel",
        "horizontal-3-panel",
        "vertical-2-panel",
        "vertical-3-panel",
        "fractured-overlapping",
        "zoom-progression",
        "cross-over-bleed",
        "shattered-exploded",
        "dynamic-grid"
    ] = Field(..., description="How panels are arranged on the page")
    
    page_aspect_ratio: Optional[str] = Field(
        None,
        description="Page aspect ratio (e.g., '16:9' for horizontal, '9:16' for vertical)"
    )
    
    panel_borders: Literal[
        "clean-sharp",
        "ragged-dynamic",
        "overlapping",
        "no-borders",
        "subtle-angles"
    ] = Field(
        default="clean-sharp",
        description="Visual style of borders between panels"
    )
    
    panel_transition_style: Optional[Literal[
        "hard-cuts",
        "overlapping-scenes",
        "blended-transitions",
        "diagonal-cuts",
        "frame-within-frame"
    ]] = Field(
        None,
        description="How panels interact visually on the page"
    )
    
    # Panels (2-3 per page)
    panels: List[ComicPanel] = Field(
        ...,
        min_length=2,
        max_length=3,
        description="Panels on this page (2-3 panels)"
    )
    
    # Optional metadata
    page_description: Optional[str] = Field(
        None,
        description="Overall description of the page composition"
    )


class ComicScene(BaseModel):
    """
    A scene is a sequence of pages in the same location/time.
    Typically 2-4 pages per scene (4-12 panels total).
    """
    
    scene_number: int = Field(..., description="Scene number within chapter")
    chapter: int = Field(..., description="Chapter this scene belongs to")
    
    location: str = Field(..., description="Primary location for this scene")
    time_of_day: Optional[str] = Field(None, description="Time of day (e.g., 'morning', 'night')")
    
    scene_description: str = Field(
        ...,
        description="Brief description of what happens in this scene"
    )
    
    characters_in_scene: List[str] = Field(
        default_factory=list,
        description="Characters appearing in this scene"
    )
    
    # NEW: Page-based structure
    pages: List[ComicPage] = Field(
        default_factory=list,
        description="Pages that make up this scene (typically 2-4 pages)"
    )
    
    # DEPRECATED: Kept for backward compatibility
    panels: List[ComicPanel] = Field(
        default_factory=list,
        description="DEPRECATED: Use pages instead. Kept for backward compatibility. Panels that make up this scene (typically 3-8 panels)"
    )
    
    # Page layout suggestion
    suggested_page_layout: Optional[str] = Field(
        None,
        description="Suggested panel arrangement (e.g., '3-panel-horizontal', '4-panel-grid')"
    )
    
    @model_validator(mode='after')
    def migrate_panels_to_pages(self) -> 'ComicScene':
        """
        Backward compatibility: Auto-convert panels to pages if panels is populated but pages is empty.
        Groups panels into pages of 2-3 panels each with default layout.
        """
        if self.panels and not self.pages:
            logger.warning(
                f"Scene {self.scene_number} in chapter {self.chapter}: "
                f"Migrating {len(self.panels)} panels to page-based structure"
            )
            
            pages = []
            page_number = 1
            
            # Group panels into pages of 2-3
            i = 0
            while i < len(self.panels):
                # Determine how many panels for this page (prefer 3, but use 2 if needed)
                remaining = len(self.panels) - i
                
                if remaining == 1:
                    # Single panel left - this shouldn't happen in migration, but handle it
                    logger.warning(
                        f"Scene {self.scene_number}: Single panel remaining during migration, "
                        f"skipping panel {self.panels[i].panel_number}"
                    )
                    break
                elif remaining == 2:
                    # Exactly 2 panels left
                    panel_count = 2
                elif remaining == 4:
                    # 4 panels left - split into 2+2
                    panel_count = 2
                else:
                    # 3 or more panels - use 3
                    panel_count = 3
                
                panel_group = self.panels[i:i+panel_count]
                
                # Determine layout based on panel count
                panel_arrangement = "horizontal-3-panel" if panel_count == 3 else "horizontal-2-panel"
                
                page = ComicPage(
                    page_number=page_number,
                    chapter=self.chapter,
                    scene_number=self.scene_number,
                    panel_arrangement=panel_arrangement,
                    panel_borders="clean-sharp",
                    panels=panel_group
                )
                pages.append(page)
                page_number += 1
                i += panel_count
            
            self.pages = pages
            logger.info(
                f"Scene {self.scene_number} in chapter {self.chapter}: "
                f"Successfully migrated {len(self.panels)} panels to {len(pages)} pages"
            )
        
        return self


class ComicChapter(BaseModel):
    """
    A chapter from the novel, converted to comic book scenes.
    Each chapter should have 4-8 scenes, each scene 3-8 panels.
    """
    
    chapter_number: int = Field(..., description="Chapter number (1-15)")
    chapter_title: str = Field(..., description="Chapter title from novel")
    
    chapter_summary: str = Field(
        ...,
        description="Brief summary of what happens in this chapter"
    )
    
    scenes: List[ComicScene] = Field(
        default_factory=list,
        description="Scenes in this chapter (typically 4-8 scenes)"
    )
    
    # Estimated pages
    estimated_pages: Optional[int] = Field(
        None,
        description="Estimated number of comic pages for this chapter"
    )


class CharacterReference(BaseModel):
    """
    Character information for generating consistent reference images.
    """
    
    name: str = Field(..., description="Character's full name")
    role: Literal[
        "detective", "killer", "victim", "witness", "accomplice", 
        "framed_suspect", "betrayal", "supporting"
    ] = Field(..., description="Character's role in the story")
    
    # Physical description
    physical_traits: str = Field(
        ...,
        description="Detailed physical appearance for character reference generation"
    )
    
    age: int = Field(..., description="Character's age")
    ethnicity: Optional[str] = Field(None, description="Character's ethnicity")
    
    # Personality markers
    quirks: List[str] = Field(
        default_factory=list,
        description="Visual quirks and mannerisms"
    )
    
    typical_attire: str = Field(
        ...,
        description="What this character typically wears"
    )
    
    # Story context
    backstory: str = Field(
        ...,
        description="Character's backstory (for context, not visual)"
    )
    
    motivations: str = Field(
        ...,
        description="Character's motivations (for context, not visual)"
    )


class ComicBookOutput(BaseModel):
    """
    Complete comic book output from a novel.
    
    This structure preserves the richness of a 15-chapter novel
    and converts it into a properly paced comic book.
    
    Expected output (configurable based on use case):
    - Social Media: ~30-50 pages, ~100 panels
    - Short Book: ~100-150 pages, ~300 panels (default)
    - Full Book: ~300-400 pages, ~900 panels (future)
    
    Structure:
    - 15 chapters
    - 2-5 scenes per chapter (configurable)
    - 2-4 pages per scene
    - 2-3 panels per page
    """
    
    # Metadata
    title: str = Field(..., description="Comic book title")
    
    narrative_structure: str = Field(
        ...,
        description="Narrative structure (e.g., 'linear', 'non-linear')"
    )
    
    art_style: str = Field(
        ...,
        description="Overall art style (e.g., 'Noir Comic Book Style')"
    )
    
    short_summary: str = Field(
        ...,
        description="Brief summary of the entire story"
    )
    
    # Story context
    world_context: str = Field(
        ...,
        description="World and era context for the story"
    )
    
    # Characters
    characters: List[CharacterReference] = Field(
        default_factory=list,
        description="All characters in the story"
    )
    
    # Story structure
    chapters: List[ComicChapter] = Field(
        default_factory=list,
        description="All chapters converted to comic format (15 chapters expected)"
    )
    
    # Story metadata
    killer: Optional[str] = Field(None, description="Name of the killer (for detective stories)")
    victim: Optional[str] = Field(None, description="Name of the victim")
    primary_detective: Optional[str] = Field(None, description="Name of the detective")
    
    # Statistics (for validation)
    total_chapters: int = Field(default=0, description="Total number of chapters")
    total_scenes: int = Field(default=0, description="Total number of scenes")
    total_panels: int = Field(default=0, description="Total number of panels")
    total_pages: int = Field(default=0, description="Total number of comic book pages")
    estimated_pages: int = Field(
        default=0,
        description="DEPRECATED: Use total_pages instead. Estimated comic book pages"
    )

    @model_validator(mode="after")
    def calculate_statistics(self) -> "ComicBookOutput":
        """
        Calculate total statistics from all chapters.
        Computes total_pages, total_scenes, total_panels, and total_chapters.
        """
        self.total_chapters = len(self.chapters)
        self.total_scenes = 0
        self.total_panels = 0
        self.total_pages = 0

        for chapter in self.chapters:
            self.total_scenes += len(chapter.scenes)

            for scene in chapter.scenes:
                # Count pages (new page-based structure)
                self.total_pages += len(scene.pages)

                # Count panels from pages
                for page in scene.pages:
                    self.total_panels += len(page.panels)

                # Also count panels from legacy panels field (for backward compatibility)
                if scene.panels and not scene.pages:
                    self.total_panels += len(scene.panels)

        # Sync estimated_pages with total_pages for backward compatibility
        if self.total_pages > 0:
            self.estimated_pages = self.total_pages

        logger.info(
            f"Comic statistics: {self.total_chapters} chapters, "
            f"{self.total_scenes} scenes, {self.total_pages} pages, "
            f"{self.total_panels} panels"
        )

        return self


# Backward compatibility alias
DetectiveComicOutput = ComicBookOutput
