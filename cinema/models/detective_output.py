"""
Pydantic models for Detective Agent Output
"""

from typing import List, Optional, Literal
import re
from pydantic import BaseModel, Field, field_validator, model_validator


class DialogueLine(BaseModel):
    """Single line of dialogue with character attribution"""
    character: str = Field(..., description="Character name speaking this line (or 'Narrator' for caption boxes)")
    text: str = Field(..., description="The dialogue or caption text")


class PanelPrompt(BaseModel):
    """Image generation prompt for a comic panel"""

    shot_type: Literal[
        "wide",
        "medium",
        "close-up",
        "extreme-close-up",
        "establishing",
    ] = Field(
        ...,
        description=(
            "Camera shot type (canonical, hyphenated): "
            "wide | medium | close-up | extreme-close-up | establishing"
        ),
    )

    @field_validator('shot_type', mode='before')
    @classmethod
    def normalize_shot_type(cls, v: object) -> object:
        """Normalize common shot type variants BEFORE Literal validation.
        Rules:
        - trim
        - lowercase
        - collapse multiple spaces
        - accept underscores; convert to spaces first
        - remove trailing 'shot'
        - replace spaces with '-'
        - normalize closeup variants to 'close-up' and 'extreme-close-up'
        """
        if isinstance(v, str):
            s = v.strip().lower()
            # unify underscores to spaces
            s = s.replace('_', ' ')
            # collapse multiple spaces
            s = re.sub(r"\s+", " ", s)
            # remove trailing 'shot'
            s = re.sub(r"\bshot\b$", "", s).strip()
            # replace spaces with hyphens
            s = s.replace(" ", "-")
            # normalize closeup synonyms
            s = s.replace("closeup", "close-up")
            s = s.replace("extreme-closeup", "extreme-close-up")
            return s

        return v
    
    visual_description: str = Field(
        ...,
        description="Detailed VISUAL-ONLY description for image generation. Must end with orientation (Landscape/Portrait). NO dialogue or captions here.",
    )
    dialogue: List[DialogueLine] = Field(
        default_factory=list, 
        description="List of dialogue lines with character attribution. Use 'Narrator' for caption boxes."
    )
    sound_effects: Optional[str] = Field(
        None, description="Sound effects (POW!, BANG!, etc)"
    )
    emotional_tone: str = Field(..., description="Mood/emotion of the panel")
    orientation: Literal["Landscape", "Portrait"] = Field(
        default="Landscape", description="Image orientation"
    )

    def to_image_prompt(self, art_style: str = "Noir Comic Book Style") -> str:
        """Convert to full image generation prompt"""
        prompt = f"A single comic book panel in {art_style}. "
        prompt += f"{self.shot_type.replace('-', ' ').replace('_', ' ').title()} shot. "
        prompt += f"{self.visual_description}. "
        prompt += f"Emotional tone: {self.emotional_tone}. "
        # Visual storytelling only: forbid any text rendering on the image
        prompt += "Do not render any text, logos, subtitles, or caption boxes. Visual storytelling only. "

        if self.sound_effects:
            prompt += f"Imply sound: {self.sound_effects} (no text on image). "

        prompt += f"{self.orientation}."

        return prompt


class ActionLocation(BaseModel):
    """Single action at a specific time and location with visual panel"""

    timestamp: str = Field(..., description="Date and time of action")
    action: str = Field(..., description="What the person did")
    location: str = Field(..., description="Where the person was")
    role_played: str = Field(
        ..., description="What role the person played in this action"
    )
    alibi: Optional[str] = Field(None, description="Alibi if applicable")

    # Visual panel for this action
    panel: Optional[PanelPrompt] = Field(
        None, description="Comic panel prompt for visualizing this action"
    )
    beats: list[PanelPrompt] = Field(
        default_factory=list,
        description="Optional sequence of 2-3 visual beats to fully convey the moment (use when a single image cannot carry all information). Each beat is a standalone image prompt; no text on images."
    )


class CharacterProfile(BaseModel):
    """Complete character profile with backstory and actions"""

    name: str = Field(..., description="Character's full name")
    physical_traits: str = Field(..., description="Physical appearance description")
    ethnicity: Optional[str] = Field(None, description="Character's ethnicity")
    age: int = Field(..., description="Character's age")
    quirks: List[str] = Field(..., description="Unique personality quirks or habits")
    
    # Backstory
    backstory: str = Field(
        ..., 
        description="Detailed backstory including dark secrets, relationships, and connection to victim"
    )
    
    # Role
    role: Literal["killer", "victim", "accomplice", "witness", "betrayal", "detective", "framed_suspect"] = Field(
        ..., description="Character's role in the story"
    )
    
    # Actions & Timeline
    actions_and_locations: List[ActionLocation] = Field(
        ..., 
        description="Chronological breakdown of actions before, during, and after the crime"
    )
    
    # Motivations
    motivations: str = Field(
        ..., 
        description="Why the character committed their actions, derived from backstory and role"
    )


class DetectiveStoryOutput(BaseModel):
    """Complete detective story output from the detective agent"""
    
    # Characters
    characters: List[CharacterProfile] = Field(
        ..., 
        description="All character profiles with backstories and actions"
    )
    
    # Storyline
    storyline: str = Field(
        ..., 
        description="Complete narrative told using linear or non-linear structure from knowledge base"
    )
    
    # Narrative structure used
    narrative_structure: Literal["linear", "non-linear", "flashback", "parallel"] = Field(
        ..., 
        description="Type of narrative structure used from knowledge base"
    )
    
    # Art style used
    art_style: str = Field(
        default="Noir Comic Book Style",
        description="Art style used for visual generation (e.g., 'Noir Comic Book Style', 'Cyberpunk', 'Anime')"
    )
    
    # Metadata (derived from input constraints)
    killer: str = Field(..., description="Name of the killer")
    victim: str = Field(..., description="Name of the victim")
    accomplices: List[str] = Field(default_factory=list, description="Names of accomplices")
    witnesses: List[str] = Field(default_factory=list, description="Names of witnesses")
    betrayals: List[str] = Field(default_factory=list, description="Names of those who betrayed others")

    # Detective primacy
    primary_detective: str = Field(
        ..., description="Name of the primary detective (must exist in characters with role 'detective')"
    )
    secondary_detectives: list[str] = Field(
        default_factory=list,
        description="Optional secondary detectives (must exist in characters; cannot include primary)")

    @model_validator(mode="before")
    @classmethod
    def ensure_primary_detective_fallback(cls, data: dict[str, object] | object) -> dict[str, object] | object:
        """If primary_detective is missing/empty, set it to the first character with role 'detective'."""
        if isinstance(data, dict):
            primary = data.get("primary_detective")
            if primary is None or (isinstance(primary, str) and primary.strip() == ""):
                chars = data.get("characters") or []
                if isinstance(chars, list):
                    for c in chars:
                        role = c.get("role") if isinstance(c, dict) else getattr(c, "role", None)
                        if role == "detective":
                            name = c.get("name") if isinstance(c, dict) else getattr(c, "name", None)
                            if name:
                                data["primary_detective"] = name
                                break
        return data

    @model_validator(mode="after")
    def validate_detective_primacy(self):
        """Ensure primary detective exists, has correct role, and secondaries are valid names distinct from primary."""
        # Build lookup maps
        name_to_role = {c.name: c.role for c in self.characters}

        # Primary must exist and be role 'detective'
        if self.primary_detective not in name_to_role:
            raise ValueError("primary_detective must be a character name present in characters")
        if name_to_role[self.primary_detective] != "detective":
            raise ValueError("primary_detective must have role 'detective'")

        # Secondary detectives must exist and be unique, and not include primary
        seen: set[str] = set()
        for n in self.secondary_detectives:
            if n == self.primary_detective:
                raise ValueError("secondary_detectives must not include primary_detective")
            if n not in name_to_role:
                raise ValueError(f"secondary_detective '{n}' must be present in characters")
            if n in seen:
                raise ValueError(f"secondary_detectives contains duplicate name '{n}'")
            seen.add(n)

        return self
