"""
Storyline and Character models for parsing detective story data.
"""

import json
import re
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import List, Optional, Dict, Any


@dataclass
class Character:
    """Represents a character from a detective storyline"""
    name: str
    physical_traits: str
    ethnicity: str
    age: int
    quirks: List[str]
    backstory: str
    role: str  # detective, killer, victim, accomplice, witness, betrayal
    actions_locations: str  # Timeline description
    motivations: str
    identity_anchors: str
    long_term_goals: str
    relationships: str
    triggers_stress: str
    skills_toolkit: str
    memory_hooks: List[str]
    
    @staticmethod
    def _clean_text(text: str) -> str:
        """
        Clean text by normalizing quotes and dashes.
        - Replace em-dashes (U+2014) with hyphens (-)
        - Replace curly quotes with straight quotes
        """
        if not text:
            return text
        
        # Replace em-dash (U+2014) with hyphen
        text = text.replace('\u2014', '-')
        
        # Replace curly double quotes with straight quotes
        text = text.replace('\u201c', '"').replace('\u201d', '"')
        
        # Replace curly single quotes with straight quotes  
        text = text.replace('\u2018', "'").replace('\u2019', "'")
        
        return text
    
    def _clean_all_fields(self) -> None:
        """Clean all text fields in the character"""
        self.name = self._clean_text(self.name)
        self.physical_traits = self._clean_text(self.physical_traits)
        self.ethnicity = self._clean_text(self.ethnicity)
        self.backstory = self._clean_text(self.backstory)
        self.role = self._clean_text(self.role)
        self.actions_locations = self._clean_text(self.actions_locations)
        self.motivations = self._clean_text(self.motivations)
        self.identity_anchors = self._clean_text(self.identity_anchors)
        self.long_term_goals = self._clean_text(self.long_term_goals)
        self.relationships = self._clean_text(self.relationships)
        self.triggers_stress = self._clean_text(self.triggers_stress)
        self.skills_toolkit = self._clean_text(self.skills_toolkit)
        
        # Clean list fields
        self.quirks = [self._clean_text(q) for q in self.quirks]
        self.memory_hooks = [self._clean_text(m) for m in self.memory_hooks]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)
    
    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), indent=indent)
    
    def save(self, output_dir: Path) -> Path:
        """Save character to JSON file"""
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Clean all text fields before saving
        self._clean_all_fields()
        
        # Sanitize filename
        filename = self.name.replace(" ", "_").replace('"', "").replace("'", "")
        filepath = output_dir / f"{filename}.json"
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(self.to_json())
        
        return filepath
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Character':
        """Create from dictionary"""
        return cls(**data)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'Character':
        """Create from JSON string"""
        return cls.from_dict(json.loads(json_str))


@dataclass
class Storyline:
    """Represents a complete detective storyline with characters"""
    title: str
    subtitle: str
    world_context: str
    characters: List[Character]
    storyline_text: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_flow_state(cls, flow_id: str) -> 'Storyline':
        """
        Load storyline from flow state JSON file.
        
        Args:
            flow_id: The workflow ID (e.g., "43e21caa" or "43e21caa_gemini_pro")
        
        Returns:
            Storyline object with parsed characters
        """
        flow_state_file = Path(f"output/flow_states/storybuilder_{flow_id}.json")
        
        if not flow_state_file.exists():
            raise FileNotFoundError(f"Flow state not found: {flow_state_file}")
        
        with open(flow_state_file, 'r', encoding='utf-8') as f:
            state = json.load(f)
        
        # Extract storyline text from output
        storyline_text = state.get('output', {}).get('storyline', '')
        
        if not storyline_text:
            raise ValueError(f"No storyline found in flow state: {flow_id}")
        
        # Parse storyline
        return cls.from_markdown(storyline_text)
    
    @classmethod
    def from_markdown(cls, markdown_text: str) -> 'Storyline':
        """Parse storyline from markdown text"""
        
        # Extract title
        title_match = re.search(r'^# (.+)$', markdown_text, re.MULTILINE)
        title = title_match.group(1).strip() if title_match else "Untitled"
        
        # Extract subtitle
        subtitle_match = re.search(r'^## Subtitle: (.+)$', markdown_text, re.MULTILINE)
        subtitle = subtitle_match.group(1).strip() if subtitle_match else ""
        
        # Extract world context
        world_context = cls._extract_section(markdown_text, "## World & Era Context")
        
        # Extract characters
        characters = cls._parse_characters(markdown_text)
        
        # Extract storyline section
        storyline_section = cls._extract_section(markdown_text, "## Storyline")
        
        return cls(
            title=title,
            subtitle=subtitle,
            world_context=world_context,
            characters=characters,
            storyline_text=storyline_section,
        )
    
    @staticmethod
    def _extract_section(text: str, header: str) -> str:
        """Extract content from a markdown section"""
        pattern = rf'{re.escape(header)}\s*\n(.*?)(?=\n##|\Z)'
        match = re.search(pattern, text, re.DOTALL)
        return match.group(1).strip() if match else ""
    
    @staticmethod
    def _parse_characters(text: str) -> List[Character]:
        """Parse all characters from the storyline markdown"""
        characters = []
        
        # Find the Characters section
        char_section_match = re.search(
            r'## Characters\s*\n---\s*\n(.*?)(?=\n## |\Z)',
            text,
            re.DOTALL
        )
        
        if not char_section_match:
            return characters
        
        char_section = char_section_match.group(1)
        
        # Split into individual character blocks
        # Each character starts with ### Character N
        char_blocks = re.split(r'\n---\s*\n### Character \d+\s*\n', char_section)
        
        # First split might have leading content, skip if empty
        if char_blocks and not char_blocks[0].strip():
            char_blocks = char_blocks[1:]
        
        # Also try splitting by just ### Character
        if not char_blocks or len(char_blocks) <= 1:
            char_blocks = re.split(r'\n### Character \d+\s*\n', char_section)
            if char_blocks and not char_blocks[0].strip():
                char_blocks = char_blocks[1:]
        
        for block in char_blocks:
            if not block.strip():
                continue
            
            try:
                char = Storyline._parse_single_character(block)
                if char:
                    characters.append(char)
            except Exception as e:
                print(f"Warning: Failed to parse character block: {e}")
                continue
        
        return characters
    
    @staticmethod
    def _parse_single_character(block: str) -> Optional[Character]:
        """Parse a single character block"""
        
        # Extract name
        name_match = re.search(r'\*\*Name:\*\*\s*(.+?)(?:\n|$)', block)
        if not name_match:
            return None
        name = name_match.group(1).strip()
        
        # Extract physical traits
        physical_match = re.search(r'\*\*Physical Traits:\*\*\s*(.+?)(?:\n|$)', block)
        physical_traits = physical_match.group(1).strip() if physical_match else ""
        
        # Extract ethnicity
        ethnicity_match = re.search(r'\*\*Ethnicity:\*\*\s*(.+?)(?:\n|$)', block)
        ethnicity = ethnicity_match.group(1).strip() if ethnicity_match else ""
        
        # Extract age
        age_match = re.search(r'\*\*Age:\*\*\s*(\d+)', block)
        age = int(age_match.group(1)) if age_match else 0
        
        # Extract quirks (list)
        quirks = []
        quirks_section = re.search(r'\*\*Quirks:\*\*\s*\n((?:- .+\n?)+)', block)
        if quirks_section:
            quirk_lines = quirks_section.group(1).strip().split('\n')
            quirks = [line.strip('- ').strip() for line in quirk_lines if line.strip()]
        
        # Extract backstory
        backstory_match = re.search(r'#### Backstory\s*\n(.*?)(?=\n####|\Z)', block, re.DOTALL)
        backstory = backstory_match.group(1).strip() if backstory_match else ""
        
        # Extract role
        role_match = re.search(r'#### Role\s*\n-?\s*(.+?)(?:\n|$)', block)
        role = role_match.group(1).strip() if role_match else ""
        
        # Extract actions & locations
        actions_match = re.search(r'#### Actions & Locations\s*\n(.*?)(?=\n####|\Z)', block, re.DOTALL)
        actions_locations = actions_match.group(1).strip() if actions_match else ""
        
        # Extract motivations
        motivations_match = re.search(r'#### Motivations\s*\n(.*?)(?=\n####|\Z)', block, re.DOTALL)
        motivations = motivations_match.group(1).strip() if motivations_match else ""
        
        # Extract identity anchors
        identity_match = re.search(r'#### Identity Anchors\s*\n(.*?)(?=\n####|\Z)', block, re.DOTALL)
        identity_anchors = identity_match.group(1).strip() if identity_match else ""
        
        # Extract long-term goals
        goals_match = re.search(r'#### Long-term Goals\s*\n(.*?)(?=\n####|\Z)', block, re.DOTALL)
        long_term_goals = goals_match.group(1).strip() if goals_match else ""
        
        # Extract relationships
        relationships_match = re.search(r'#### Relationships Graph Notes\s*\n(.*?)(?=\n####|\Z)', block, re.DOTALL)
        relationships = relationships_match.group(1).strip() if relationships_match else ""
        
        # Extract triggers and stress
        triggers_match = re.search(r'#### Triggers and Stress Responses\s*\n(.*?)(?=\n####|\Z)', block, re.DOTALL)
        triggers_stress = triggers_match.group(1).strip() if triggers_match else ""
        
        # Extract skills
        skills_match = re.search(r'#### Skills / Toolkit \(Era-Appropriate\)\s*\n(.*?)(?=\n####|\Z)', block, re.DOTALL)
        skills_toolkit = skills_match.group(1).strip() if skills_match else ""
        
        # Extract memory hooks (list)
        memory_hooks = []
        memory_section = re.search(r'#### Memory Hooks\s*\n((?:- .+\n?)+)', block, re.DOTALL)
        if memory_section:
            hook_lines = memory_section.group(1).strip().split('\n')
            memory_hooks = [line.strip('- ').strip() for line in hook_lines if line.strip()]
        
        return Character(
            name=name,
            physical_traits=physical_traits,
            ethnicity=ethnicity,
            age=age,
            quirks=quirks,
            backstory=backstory,
            role=role,
            actions_locations=actions_locations,
            motivations=motivations,
            identity_anchors=identity_anchors,
            long_term_goals=long_term_goals,
            relationships=relationships,
            triggers_stress=triggers_stress,
            skills_toolkit=skills_toolkit,
            memory_hooks=memory_hooks,
        )
    
    def save_characters(self, output_dir: Path) -> List[Path]:
        """Save all characters to JSON files"""
        output_dir = Path(output_dir)
        saved_files = []
        
        for character in self.characters:
            filepath = character.save(output_dir)
            saved_files.append(filepath)
        
        # Create manifest
        manifest = {
            "title": self.title,
            "subtitle": self.subtitle,
            "character_count": len(self.characters),
            "characters": [
                {
                    "name": char.name,
                    "role": char.role,
                    "age": char.age,
                    "file": f"{char.name.replace(' ', '_').replace('\"', '').replace(chr(39), '')}.json"
                }
                for char in self.characters
            ]
        }
        
        manifest_file = output_dir / "character_manifest.json"
        with open(manifest_file, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2)
        
        saved_files.append(manifest_file)
        
        return saved_files
    
    def get_character_by_name(self, name: str) -> Optional[Character]:
        """Get character by name (case-insensitive)"""
        name_lower = name.lower()
        for char in self.characters:
            if char.name.lower() == name_lower:
                return char
        return None
    
    def get_characters_by_role(self, role: str) -> List[Character]:
        """Get all characters with a specific role"""
        return [char for char in self.characters if char.role.lower() == role.lower()]
