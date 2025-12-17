"""
Domain event handler for extracting and saving characters from storyline.

This handler listens for storyline completion events and extracts character
data to the database, decoupled from the main flow logic.
"""
from __future__ import annotations

import logging
from typing import Optional

from cinema.workflow.domain_events import DomainEvent
from cinema.transformers.storyline_parser import StorylineParser
from cinema.db.characters import CharacterStore

logger = logging.getLogger(__name__)


class CharacterExtractionHandler:
    """
    Handler that extracts characters from storyline and saves to database.
    
    Triggered when storyline generation completes (before novel generation).
    """
    
    def __init__(self, character_store: Optional[CharacterStore] = None):
        self.character_store = character_store or CharacterStore()
    
    def handle(self, event: DomainEvent) -> None:
        """
        Extract characters from storyline and save to database.
        
        Args:
            event: Domain event containing workflow state with storyline
        """
        workflow_id = event.workflow_id
        state = event.state
        
        # Extract storyline from state
        output = state.get('output', {})
        storyline = output.get('storyline')
        
        if not storyline:
            logger.warning(f"No storyline found in event for workflow {workflow_id}")
            return
        
        logger.info(f"Extracting characters from storyline for workflow {workflow_id}")
        
        try:
            # Parse storyline to extract characters
            parsed = StorylineParser.parse_full_storyline(storyline)
            
            if not parsed.characters:
                logger.warning(f"No characters found in storyline for workflow {workflow_id}")
                return
            
            # Save characters to database
            self.character_store.save_characters(workflow_id, parsed.characters)
            
            logger.info(
                f"✅ Extracted and saved {len(parsed.characters)} characters "
                f"for workflow {workflow_id}"
            )
            
            # Log character names for debugging
            char_names = [char.name for char in parsed.characters]
            logger.debug(f"Characters saved: {', '.join(char_names)}")
            
        except Exception as e:
            logger.error(
                f"Failed to extract characters for workflow {workflow_id}: {e}",
                exc_info=True
            )
