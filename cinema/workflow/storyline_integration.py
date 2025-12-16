"""
Integration helper for storyline parsing and BookWriter workflow
- Parses world context on-the-fly from storybuilder_states
- Stores characters in dedicated characters table for reuse
"""
import sqlite3
from typing import Optional, Dict, Any
from cinema.transformers.storyline_parser import StorylineParser
from cinema.models.storyline import ParsedStoryline
from cinema.agents.bookwriter.crew import BookWriterSchema
from cinema.db.characters import CharacterStore


class StorylineIntegration:
    """
    Helper for parsing storyline and managing character data.
    - World context: parsed on-the-fly (not stored)
    - Characters: stored in characters table for reuse
    """
    
    def __init__(self, db_path: str = "cinema_server.db"):
        self.db_path = db_path
        self.char_store = CharacterStore(db_path)
        self._world_cache: Dict[str, str] = {}  # Cache world context text
    
    def get_storyline_from_db(self, workflow_id: str) -> str:
        """
        Extract storyline text from storybuilder_states table
        
        Args:
            workflow_id: The workflow ID to retrieve
            
        Returns:
            Storyline markdown text
            
        Raises:
            ValueError: If storyline not found
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT json_extract(state_json, '$.output.storyline')
                FROM storybuilder_states
                WHERE id = ?
            """, (workflow_id,))
            
            row = cursor.fetchone()
            if row and row[0]:
                return row[0]
            
            raise ValueError(f"No storyline found for workflow_id: {workflow_id}")
    
    def get_screenplay_from_db(self, workflow_id: str) -> Optional[str]:
        """
        Extract screenplay text from storybuilder_states table
        
        Args:
            workflow_id: The workflow ID to retrieve
            
        Returns:
            Screenplay markdown text or None if not found
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT json_extract(state_json, '$.output.screenplay')
                FROM storybuilder_states
                WHERE id = ?
            """, (workflow_id,))
            
            row = cursor.fetchone()
            if row and row[0]:
                return row[0]
            
            return None
    
    def parse_and_store_characters(self, workflow_id: str, storyline_text: Optional[str] = None) -> ParsedStoryline:
        """
        Parse storyline and store characters in database
        
        Args:
            workflow_id: The workflow ID
            storyline_text: Optional storyline text. If not provided, will fetch from DB
            
        Returns:
            ParsedStoryline object
        """
        # Get storyline if not provided
        if storyline_text is None:
            storyline_text = self.get_storyline_from_db(workflow_id)
        
        # Parse the storyline
        parsed = StorylineParser.parse_full_storyline(storyline_text)
        
        # Store characters in database
        self.char_store.save_characters(workflow_id, parsed.characters)
        
        # Cache world context
        self._world_cache[workflow_id] = parsed.world_context.full_text
        
        return parsed
    
    def get_world_context_text(self, workflow_id: str) -> str:
        """
        Get world context text (parsed on-the-fly or from cache)
        
        Args:
            workflow_id: The workflow ID
            
        Returns:
            World context full text
        """
        # Check cache first
        if workflow_id in self._world_cache:
            return self._world_cache[workflow_id]
        
        # Parse from database
        storyline_text = self.get_storyline_from_db(workflow_id)
        world_context = StorylineParser.parse_world_context(storyline_text)
        
        # Cache it
        self._world_cache[workflow_id] = world_context.full_text
        
        return world_context.full_text
    
    def get_art_style(self, workflow_id: str) -> str:
        """
        Get art style from storyline metadata
        
        Args:
            workflow_id: The workflow ID
            
        Returns:
            Art style string from metadata
        """
        storyline_text = self.get_storyline_from_db(workflow_id)
        metadata = StorylineParser.parse_metadata(storyline_text)
        return metadata.art_style
    
    def prepare_bookwriter_input(
        self,
        workflow_id: str,
        storyline_text: Optional[str] = None,
        words_per_chapter: int = 150,
        total_pages: int = 50,
        art_style: Optional[str] = None,
        examples: str = "",
        ensure_characters_stored: bool = True,
    ) -> Dict[str, Any]:
        """
        Prepare complete input for BookWriterSchema
        
        Args:
            workflow_id: The workflow ID
            storyline_text: Optional storyline text. If not provided, will fetch from DB
            words_per_chapter: Words per chapter (default: 150)
            total_pages: Total pages (default: 50)
            art_style: Optional art style override
            examples: Examples text for the agent
            ensure_characters_stored: If True, parse and store characters if not in DB
            
        Returns:
            Dictionary ready for BookWriterSchema(**dict)
        """
        # Get storyline
        if storyline_text is None:
            storyline_text = self.get_storyline_from_db(workflow_id)
        
        # Get world context (parsed on-the-fly)
        world_era = self.get_world_context_text(workflow_id)
        
        # Get characters from database
        character_details = self.char_store.get_character_full_texts(workflow_id)
        
        # If no characters in DB and ensure_characters_stored is True, parse and store
        if not character_details and ensure_characters_stored:
            parsed = self.parse_and_store_characters(workflow_id, storyline_text)
            character_details = [char.full_text for char in parsed.characters]
            
            # Use metadata art style if not provided
            if art_style is None:
                art_style = parsed.metadata.art_style
        
        # If still no art style, parse metadata
        if art_style is None:
            metadata = StorylineParser.parse_metadata(storyline_text)
            art_style = metadata.art_style
        
        # Prepare input dict
        return {
            "storyline": storyline_text,
            "world_era": world_era,
            "character_details": character_details,
            "words_per_chapter": words_per_chapter,
            "total_pages": total_pages,
            "art_style": art_style or "",
            "examples": examples,
        }
    
    def create_bookwriter_schema(
        self,
        workflow_id: str,
        storyline_text: Optional[str] = None,
        words_per_chapter: int = 150,
        total_pages: int = 50,
        art_style: Optional[str] = None,
        examples: str = "",
    ) -> BookWriterSchema:
        """
        Create a BookWriterSchema instance with all required data
        
        Args:
            workflow_id: The workflow ID
            storyline_text: Optional storyline text. If not provided, will fetch from DB
            words_per_chapter: Words per chapter (default: 150)
            total_pages: Total pages (default: 50)
            art_style: Optional art style override
            examples: Examples text for the agent
            
        Returns:
            BookWriterSchema instance ready to use
        """
        input_dict = self.prepare_bookwriter_input(
            workflow_id=workflow_id,
            storyline_text=storyline_text,
            words_per_chapter=words_per_chapter,
            total_pages=total_pages,
            art_style=art_style,
            examples=examples,
        )
        
        return BookWriterSchema(**input_dict)
    
    def get_characters_for_image_gen(self, workflow_id: str, ensure_stored: bool = True) -> Dict[str, str]:
        """
        Get character details formatted for image generation
        
        Args:
            workflow_id: The workflow ID
            ensure_stored: If True, parse and store characters if not in DB
            
        Returns:
            Dict mapping character names to formatted prompts
        """
        # Try to get from database first
        prompts = self.char_store.get_characters_for_image_gen(workflow_id)
        
        # If not in DB and ensure_stored is True, parse and store
        if not prompts and ensure_stored:
            self.parse_and_store_characters(workflow_id)
            prompts = self.char_store.get_characters_for_image_gen(workflow_id)
        
        return prompts


# Convenience functions for quick access

def get_bookwriter_input(
    workflow_id: str,
    words_per_chapter: int = 150,
    total_pages: int = 50,
    examples: str = "",
    db_path: str = "cinema_server.db",
) -> Dict[str, Any]:
    """
    Quick function to get BookWriter input dict
    
    Usage:
        input_dict = get_bookwriter_input("c778f39d")
        schema = BookWriterSchema(**input_dict)
    """
    integration = StorylineIntegration(db_path)
    return integration.prepare_bookwriter_input(
        workflow_id=workflow_id,
        words_per_chapter=words_per_chapter,
        total_pages=total_pages,
        examples=examples,
        ensure_characters_stored=True,
    )


def get_character_prompts(
    workflow_id: str,
    db_path: str = "cinema_server.db",
) -> Dict[str, str]:
    """
    Quick function to get character image generation prompts
    
    Usage:
        prompts = get_character_prompts("c778f39d")
        for char_name, prompt in prompts.items():
            generate_image(char_name, prompt)
    """
    integration = StorylineIntegration(db_path)
    return integration.get_characters_for_image_gen(workflow_id)


def parse_workflow_storyline(
    workflow_id: str,
    db_path: str = "cinema_server.db",
) -> ParsedStoryline:
    """
    Quick function to parse and store a workflow's storyline characters
    
    Usage:
        parsed = parse_workflow_storyline("c778f39d")
        print(f"Found {len(parsed.characters)} characters")
    """
    integration = StorylineIntegration(db_path)
    return integration.parse_and_store_characters(workflow_id)
