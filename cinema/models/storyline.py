"""
Models for storyline components: World Context and Characters
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class WorldContext(BaseModel):
    """World & Era Context from storyline"""
    era_and_time_window: str = Field(default="", description="Era and time period")
    geography_and_setting: str = Field(default="", description="Geographic location and setting")
    culture_and_traditions: str = Field(default="", description="Cultural norms and traditions")
    societal_constructs: str = Field(default="", description="Social structures and definitions")
    geopolitics_and_legal: str = Field(default="", description="Legal and political context")
    technology_and_forensics: str = Field(default="", description="Technology level and forensic capabilities")
    policing_style: str = Field(default="", description="Policing style and jurisdiction")
    media_environment: str = Field(default="", description="Media and public perception")
    thematic_constraints: str = Field(default="", description="Thematic elements and constraints")
    
    # Store the full text block as well
    full_text: str = Field(default="", description="Complete world context text block")
    
    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary for easy access"""
        return {
            "era_and_time_window": self.era_and_time_window,
            "geography_and_setting": self.geography_and_setting,
            "culture_and_traditions": self.culture_and_traditions,
            "societal_constructs": self.societal_constructs,
            "geopolitics_and_legal": self.geopolitics_and_legal,
            "technology_and_forensics": self.technology_and_forensics,
            "policing_style": self.policing_style,
            "media_environment": self.media_environment,
            "thematic_constraints": self.thematic_constraints,
        }


class CharacterDetail(BaseModel):
    """Detailed character information from storyline"""
    name: str = Field(..., description="Character full name")
    physical_traits: str = Field(default="", description="Physical description")
    ethnicity: str = Field(default="", description="Ethnicity")
    age: int = Field(default=0, description="Age")
    quirks: List[str] = Field(default_factory=list, description="Character quirks")
    clothing: str = Field(default="", description="Clothing preferences")
    
    # Detailed sections
    backstory: str = Field(default="", description="Character backstory")
    role: str = Field(default="", description="Character role in story")
    actions_and_locations: str = Field(default="", description="Timeline of actions and locations")
    motivations: str = Field(default="", description="Character motivations")
    world_view_and_cultural_context: str = Field(default="", description="Character's worldview and cultural context")
    identity_anchors: str = Field(default="", description="Core beliefs, values, patterns")
    long_term_goals: str = Field(default="", description="Long-term goals")
    relationships_graph: str = Field(default="", description="Relationship notes")
    triggers_and_stress: str = Field(default="", description="Triggers and stress responses")
    skills_toolkit: str = Field(default="", description="Skills and tools")
    memory_hooks: List[str] = Field(default_factory=list, description="Memory hooks")
    
    # Store the full character text block
    full_text: str = Field(default="", description="Complete character text block")
    
    def to_image_gen_prompt(self) -> str:
        """
        Format character details for image generation.
        Returns: Name, physical traits, ethnicity, age, quirks, backstory, 
                 worldview, and memory hooks
        """
        quirks_text = ", ".join(self.quirks) if self.quirks else "None specified"
        memory_text = "; ".join(self.memory_hooks) if self.memory_hooks else "None specified"
        
        prompt = f"""Character: {self.name}

Physical Traits: {self.physical_traits}
Ethnicity: {self.ethnicity}
Age: {self.age}
Clothing: {self.clothing}

Quirks: {quirks_text}

Backstory:
{self.backstory}

World View and Cultural Context:
{self.world_view_and_cultural_context}

Memory Hooks:
{memory_text}
"""
        return prompt
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage"""
        return {
            "name": self.name,
            "physical_traits": self.physical_traits,
            "ethnicity": self.ethnicity,
            "age": self.age,
            "quirks": self.quirks,
            "clothing": self.clothing,
            "backstory": self.backstory,
            "role": self.role,
            "actions_and_locations": self.actions_and_locations,
            "motivations": self.motivations,
            "world_view_and_cultural_context": self.world_view_and_cultural_context,
            "identity_anchors": self.identity_anchors,
            "long_term_goals": self.long_term_goals,
            "relationships_graph": self.relationships_graph,
            "triggers_and_stress": self.triggers_and_stress,
            "skills_toolkit": self.skills_toolkit,
            "memory_hooks": self.memory_hooks,
            "full_text": self.full_text,
        }


class StorylineMetadata(BaseModel):
    """Metadata from storyline"""
    title: str = Field(default="", description="Story title")
    theme: str = Field(default="", description="Story theme")
    genre: str = Field(default="", description="Story genre")
    adults_only: bool = Field(default=False, description="Adults only flag")
    narrative_structure: str = Field(default="", description="Narrative structure")
    art_style: str = Field(default="", description="Art style")
    story_telling_style: str = Field(default="", description="Storytelling style")
    suited_for: str = Field(default="", description="Suited for (novel, TV, etc)")
    colors: str = Field(default="", description="Color palette")
    cover_concept: str = Field(default="", description="Cover/thumbnail concept")


class ParsedStoryline(BaseModel):
    """Complete parsed storyline with all components"""
    world_context: WorldContext
    characters: List[CharacterDetail]
    metadata: StorylineMetadata
    storyline_text: str = Field(default="", description="Detailed storyline text")
    references: List[str] = Field(default_factory=list, description="Knowledge base references")
    improvement_feedback: str = Field(default="", description="Improvement feedback")
