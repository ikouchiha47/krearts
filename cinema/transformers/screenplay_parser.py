"""
Parser for extracting character information from screenplay format
"""
import re
from typing import List, Dict, Optional
from cinema.models.storyline import CharacterDetail


class ScreenplayCharacterParser:
    """Parse characters from screenplay markdown"""
    
    @staticmethod
    def parse_characters_from_screenplay(screenplay_text: str) -> List[CharacterDetail]:
        """
        Extract character information from screenplay format.
        Screenplay typically has a ## Characters section with basic info.
        """
        characters = []
        
        # Find the Characters section
        chars_pattern = r"##\s*Characters\s*\n(.*?)(?=\n##|\Z)"
        chars_match = re.search(chars_pattern, screenplay_text, re.DOTALL | re.IGNORECASE)
        
        if not chars_match:
            return characters
        
        chars_section = chars_match.group(1)
        
        # Split by character headers (### Character N)
        char_blocks = re.split(r"\n###\s*Character\s+\d+", chars_section)
        
        for block in char_blocks:
            if not block.strip() or block.strip() == "---":
                continue
            
            character = ScreenplayCharacterParser._parse_screenplay_character(block)
            if character:
                characters.append(character)
        
        return characters
    
    @staticmethod
    def _parse_screenplay_character(char_text: str) -> Optional[CharacterDetail]:
        """Parse a single character from screenplay format"""
        
        # Extract name
        name_match = re.search(r"\*\*Name:\*\*\s*(.+?)(?:\n|$)", char_text)
        if not name_match:
            return None
        
        name = name_match.group(1).strip()
        
        # Extract role
        role_match = re.search(r"\*\*Role:\*\*\s*(.+?)(?:\n|$)", char_text)
        role = role_match.group(1).strip() if role_match else ""
        
        # For screenplay, we have minimal info, so we create a basic character
        return CharacterDetail(
            name=name,
            role=role,
            full_text=char_text.strip(),
        )
    
    @staticmethod
    def extract_character_names_from_screenplay(screenplay_text: str) -> List[str]:
        """
        Extract just the character names from screenplay
        """
        characters = ScreenplayCharacterParser.parse_characters_from_screenplay(screenplay_text)
        return [char.name for char in characters]
    
    @staticmethod
    def parse_chapters_from_screenplay(screenplay_text: str) -> Dict[int, str]:
        """
        Extract chapters from screenplay.
        Returns dict of {chapter_number: chapter_content}
        """
        chapters = {}
        
        # Find all chapter sections
        chapter_pattern = r"###\s*Chapter\s+(\d+):\s*(.+?)\n(.*?)(?=\n###\s*Chapter|\n---\n###\s*\*\*ACT|\Z)"
        
        for match in re.finditer(chapter_pattern, screenplay_text, re.DOTALL):
            chapter_num = int(match.group(1))
            chapter_title = match.group(2).strip()
            chapter_content = match.group(3).strip()
            
            chapters[chapter_num] = f"# Chapter {chapter_num}: {chapter_title}\n\n{chapter_content}"
        
        return chapters
    
    @staticmethod
    def get_chapter_count(screenplay_text: str) -> int:
        """Get the number of chapters in the screenplay"""
        chapters = ScreenplayCharacterParser.parse_chapters_from_screenplay(screenplay_text)
        return len(chapters)
