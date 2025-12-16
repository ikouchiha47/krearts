"""
Parser for extracting world context and character details from storyline markdown
"""
import re
from typing import List, Optional, Tuple
from cinema.models.storyline import (
    WorldContext,
    CharacterDetail,
    StorylineMetadata,
    ParsedStoryline,
)


class StorylineParser:
    """Parse storyline markdown to extract structured data"""
    
    @staticmethod
    def parse_world_context(storyline_text: str) -> WorldContext:
        """
        Extract World & Era Context section from storyline
        """
        # Find the World & Era Context section
        world_pattern = r"##\s*World\s*&\s*Era\s*Context\s*\n(.*?)(?=\n##|\Z)"
        match = re.search(world_pattern, storyline_text, re.DOTALL | re.IGNORECASE)
        
        if not match:
            return WorldContext()
        
        world_text = match.group(1).strip()
        
        # Parse individual fields
        def extract_field(field_name: str) -> str:
            pattern = rf"-\s*\*?\*?{field_name}:?\*?\*?:?\s*(.*?)(?=\n-|\Z)"
            field_match = re.search(pattern, world_text, re.IGNORECASE | re.DOTALL)
            if field_match:
                return field_match.group(1).strip()
            return ""
        
        return WorldContext(
            era_and_time_window=extract_field("Era and Time Window"),
            geography_and_setting=extract_field("Geography and Setting"),
            culture_and_traditions=extract_field("Culture and Traditions"),
            societal_constructs=extract_field("Societal Constructs"),
            geopolitics_and_legal=extract_field("Geopolitics and Legal Context"),
            technology_and_forensics=extract_field("Technology Level and Forensics"),
            policing_style=extract_field("Policing Style and Jurisdiction"),
            media_environment=extract_field("Media Environment"),
            thematic_constraints=extract_field("Thematic Constraints"),
            full_text=world_text,
        )
    
    @staticmethod
    def parse_characters(storyline_text: str) -> List[CharacterDetail]:
        """
        Extract all character sections from storyline
        """
        characters = []
        
        # Find the Characters section
        chars_pattern = r"##\s*Characters\s*\n(.*?)(?=\n##\s*Storyline|\Z)"
        chars_match = re.search(chars_pattern, storyline_text, re.DOTALL | re.IGNORECASE)
        
        if not chars_match:
            return characters
        
        chars_section = chars_match.group(1)
        
        # Split by character headers (### Character N)
        char_blocks = re.split(r"\n###\s*Character\s+\d+", chars_section)
        
        for block in char_blocks:
            if not block.strip() or block.strip() == "---":
                continue
            
            character = StorylineParser._parse_single_character(block)
            if character:
                characters.append(character)
        
        return characters
    
    @staticmethod
    def _parse_single_character(char_text: str) -> Optional[CharacterDetail]:
        """Parse a single character block"""
        
        # Extract name
        name_match = re.search(r"\*\*Name:\*\*\s*(.+?)(?:\n|$)", char_text)
        if not name_match:
            return None
        
        name = name_match.group(1).strip()
        
        # Extract basic fields
        def extract_basic_field(field_name: str) -> str:
            pattern = rf"\*\*{field_name}:\*\*\s*(.+?)(?=\n\*\*|\n####|\Z)"
            match = re.search(pattern, char_text, re.DOTALL)
            if match:
                return match.group(1).strip()
            return ""
        
        physical_traits = extract_basic_field("Physical Traits")
        ethnicity = extract_basic_field("Ethnicity")
        clothing = extract_basic_field("Clothing")
        
        # Extract age
        age_match = re.search(r"\*\*Age:\*\*\s*(\d+)", char_text)
        age = int(age_match.group(1)) if age_match else 0
        
        # Extract quirks (list)
        quirks = []
        quirks_match = re.search(r"\*\*Quirks:\*\*\s*\n((?:-\s*.+\n?)+)", char_text)
        if quirks_match:
            quirks_text = quirks_match.group(1)
            quirks = [q.strip("- ").strip() for q in quirks_text.split("\n") if q.strip()]
        
        # Extract sections with headers
        def extract_section(section_name: str) -> str:
            pattern = rf"####\s*{section_name}\s*\n(.*?)(?=\n####|\n---|\Z)"
            match = re.search(pattern, char_text, re.DOTALL | re.IGNORECASE)
            if match:
                return match.group(1).strip()
            return ""
        
        backstory = extract_section("Backstory")
        role = extract_section("Role")
        actions = extract_section("Actions & Locations")
        motivations = extract_section("Motivations")
        world_view = extract_section("World View and Cultural Context")
        identity = extract_section("Identity Anchors")
        goals = extract_section("Long-term Goals")
        relationships = extract_section("Relationships Graph Notes")
        triggers = extract_section("Triggers and Stress Responses")
        skills = extract_section("Skills / Toolkit")
        
        # Extract memory hooks (list)
        memory_hooks = []
        memory_match = re.search(
            r"####\s*Memory Hooks\s*\n((?:-\s*.+\n?)+)",
            char_text,
            re.DOTALL
        )
        if memory_match:
            memory_text = memory_match.group(1)
            memory_hooks = [m.strip("- ").strip() for m in memory_text.split("\n") if m.strip()]
        
        return CharacterDetail(
            name=name,
            physical_traits=physical_traits,
            ethnicity=ethnicity,
            age=age,
            quirks=quirks,
            clothing=clothing,
            backstory=backstory,
            role=role,
            actions_and_locations=actions,
            motivations=motivations,
            world_view_and_cultural_context=world_view,
            identity_anchors=identity,
            long_term_goals=goals,
            relationships_graph=relationships,
            triggers_and_stress=triggers,
            skills_toolkit=skills,
            memory_hooks=memory_hooks,
            full_text=char_text.strip(),
        )
    
    @staticmethod
    def parse_metadata(storyline_text: str) -> StorylineMetadata:
        """Extract storyline metadata"""
        
        # Find metadata section
        meta_pattern = r"###\s*Metadata\s*\n(.*?)(?=\n###|\Z)"
        match = re.search(meta_pattern, storyline_text, re.DOTALL | re.IGNORECASE)
        
        if not match:
            return StorylineMetadata()
        
        meta_text = match.group(1)
        
        def extract_meta_field(field_name: str) -> str:
            pattern = rf"-\s*\*?\*?{field_name}:?\*?\*?:?\s*(.+?)(?=\n-|\Z)"
            field_match = re.search(pattern, meta_text, re.IGNORECASE)
            if field_match:
                return field_match.group(1).strip()
            return ""
        
        # Parse adults_only boolean
        adults_text = extract_meta_field("Adults Only").lower()
        adults_only = adults_text in ["yes", "true", "1"]
        
        return StorylineMetadata(
            title=extract_meta_field("Title"),
            theme=extract_meta_field("Theme"),
            genre=extract_meta_field("Genre"),
            adults_only=adults_only,
            narrative_structure=extract_meta_field("Narrative Structure"),
            art_style=extract_meta_field("Art Style"),
            story_telling_style=extract_meta_field("Story Telling Style"),
            suited_for=extract_meta_field("Suited For"),
            colors=extract_meta_field("Colors"),
            cover_concept=extract_meta_field("Cover/Thumbnail Image Concept"),
        )
    
    @staticmethod
    def parse_storyline_text(storyline_text: str) -> str:
        """Extract the detailed storyline section"""
        pattern = r"###\s*Detailed Storyline\s*\n(.*?)(?=\n---|\n##\s*References|\Z)"
        match = re.search(pattern, storyline_text, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return ""
    
    @staticmethod
    def parse_references(storyline_text: str) -> List[str]:
        """Extract knowledge base references"""
        pattern = r"##\s*References\s*\n(.*?)(?=\n##|\Z)"
        match = re.search(pattern, storyline_text, re.DOTALL | re.IGNORECASE)
        
        if not match:
            return []
        
        refs_text = match.group(1)
        # Extract items in square brackets
        refs = re.findall(r"-\s*\[(.+?)\]", refs_text)
        return refs
    
    @staticmethod
    def parse_feedback(storyline_text: str) -> str:
        """Extract improvement feedback"""
        pattern = r"##\s*Improvement Feedback\s*\n(.*?)(?=\n##|\Z)"
        match = re.search(pattern, storyline_text, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return ""
    
    @classmethod
    def parse_full_storyline(cls, storyline_text: str) -> ParsedStoryline:
        """
        Parse complete storyline markdown into structured data
        """
        return ParsedStoryline(
            world_context=cls.parse_world_context(storyline_text),
            characters=cls.parse_characters(storyline_text),
            metadata=cls.parse_metadata(storyline_text),
            storyline_text=cls.parse_storyline_text(storyline_text),
            references=cls.parse_references(storyline_text),
            improvement_feedback=cls.parse_feedback(storyline_text),
        )
