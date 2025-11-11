"""
Pydantic models for Detective Agent Output
"""

from typing import List, Optional, Literal
from pydantic import BaseModel, Field, field_validator


class PanelPrompt(BaseModel):
    """Image generation prompt for a comic panel"""

    shot_type: Literal[
        "wide", "medium", "close-up", "extreme close-up", "establishing",
        "Wide", "Medium", "Close-up", "Extreme Close-up", "Establishing",
        "Wide Shot", "Medium Shot", "Close-Up", "Extreme Close-Up", "Establishing Shot"
    ] = Field(
        ..., description="Camera shot type (lowercase preferred: wide, medium, close-up, extreme close-up, establishing)"
    )
    
    @field_validator('shot_type', mode='after')
    @classmethod
    def normalize_shot_type(cls, v):
        """Normalize shot type to lowercase and remove 'Shot' suffix for consistency"""
        if isinstance(v, str):
            # Remove "Shot" suffix and normalize to lowercase
            v = v.replace(" Shot", "").replace(" shot", "").strip().lower()
        return v
    visual_description: str = Field(
        ...,
        description="Detailed visual description of the scene for image generation",
    )
    dialogue: Optional[str] = Field(None, description="Dialogue or caption text")
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
        prompt += f"{self.shot_type.replace('_', ' ').title()} shot. "
        prompt += f"{self.visual_description}. "
        prompt += f"Emotional tone: {self.emotional_tone}. "

        if self.dialogue:
            prompt += f"Caption box: '{self.dialogue}'. "

        if self.sound_effects:
            prompt += f"Sound effect: '{self.sound_effects}'. "

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
    
    # Metadata (derived from input constraints)
    killer: str = Field(..., description="Name of the killer")
    victim: str = Field(..., description="Name of the victim")
    accomplices: List[str] = Field(default_factory=list, description="Names of accomplices")
    witnesses: List[str] = Field(default_factory=list, description="Names of witnesses")
    betrayals: List[str] = Field(default_factory=list, description="Names of those who betrayed others")
