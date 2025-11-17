"""
Discussion Crew - Orchestrates multi-turn conversations between two characters.
"""

import logging
from typing import List, Optional

from crewai.memory.external.external_memory import ExternalMemory
from crewai.utilities.types import LLMMessage

from cinema.agents.character.crew import CharacterQA, KnowledgeSources
from cinema.context import DirectorsContext
from cinema.models.storyline import Character, Storyline

import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Union

from crewai import Agent
from crewai.knowledge.source.base_file_knowledge_source import BaseFileKnowledgeSource
from crewai.knowledge.source.base_knowledge_source import BaseKnowledgeSource
from crewai.knowledge.source.string_knowledge_source import StringKnowledgeSource
from crewai.utilities.types import LLMMessage

from cinema.context import DirectorsContext
from cinema.models.storyline import Character
from cinema.registry import LLMThinkerIntent
from cinema.providers.shared import CrewConfig
from crewai.project import CrewBase


logger = logging.getLogger(__name__)


class DiscussionTurn:
    """Represents a single turn in a discussion"""
    
    def __init__(
        self,
        turn_number: int,
        speaker: str,
        listener: str,
        prompt: str,
        response: str,
    ):
        self.turn_number = turn_number
        self.speaker = speaker
        self.listener = listener
        self.prompt = prompt
        self.response = response


class DiscussionCrew:
    """Orchestrates a multi-turn conversation between two characters"""
    
    def __init__(
        self,
        ctx: DirectorsContext,
        character1: Character,
        character2: Character,
        storyline: Storyline,
        workflow_id: str,
        enable_memory: bool = True,
    ):
        self.ctx = ctx
        self.character1 = character1
        self.character2 = character2
        self.storyline = storyline
        self.workflow_id = workflow_id
        
        # Create character agents with memory
        self.agent1 = CharacterQA(
            ctx=ctx,
            character=character1,
            workflow_id=workflow_id,
            enable_memory=enable_memory,
        )
        self.agent2 = CharacterQA(
            ctx=ctx,
            character=character2,
            workflow_id=workflow_id,
            enable_memory=enable_memory,
        )
        
        self.agent1.bootstrap()
        self.agent2.bootstrap()
        
        # Conversation state
        self.turns: List[DiscussionTurn] = []
        self.messages1: List[LLMMessage] = []
        self.messages2: List[LLMMessage] = []
        
        # Initialize with storyline context
        self._init_messages()
    
    def _init_messages(self):
        """Initialize message history with storyline context"""
        from typing import cast
        
        system_msg = cast(
            LLMMessage,
            {"role": "system", "content": self.storyline.storyline_text}
        )
        self.messages1 = [system_msg]
        self.messages2 = [system_msg]
    
    async def start_discussion(
        self,
        opening_question: str,
        max_turns: int = 10,
    ) -> List[DiscussionTurn]:
        """
        Start a discussion between two characters.
        
        Args:
            opening_question: The question/prompt to start the discussion
            max_turns: Maximum number of turns (back-and-forth exchanges)
        
        Returns:
            List of discussion turns
        """
        from typing import cast
        
        logger.info(f"Starting discussion between {self.character1.name} and {self.character2.name}")
        logger.info(f"Opening: {opening_question}")
        
        # Turn 1: Character 1 speaks (seeded with opening question)
        prompt1 = f"{opening_question}"
        self.messages1.append(cast(LLMMessage, {"role": "user", "content": prompt1}))
        
        response1 = await self.agent1.kickoff_async(self.messages1)
        
        turn1 = DiscussionTurn(
            turn_number=1,
            speaker=self.character1.name,
            listener=self.character2.name,
            prompt=prompt1,
            response=response1.raw,
        )
        self.turns.append(turn1)
        
        # Add to character 1's history
        self.messages1.append(cast(LLMMessage, {"role": "assistant", "content": response1.raw}))
        
        logger.info(f"Turn 1: {self.character1.name} spoke ({len(response1.raw)} chars)")
        
        # Subsequent turns alternate between characters
        current_speaker = self.agent2
        current_listener = self.agent1
        current_speaker_name = self.character2.name
        current_listener_name = self.character1.name
        current_messages = self.messages2
        last_response = response1.raw
        
        for turn_num in range(2, max_turns + 1):
            # Build prompt for current speaker
            prompt = f"{current_listener_name} just said:\n\n{last_response}\n\nHow do you respond?"
            
            current_messages.append(cast(LLMMessage, {"role": "user", "content": prompt}))
            
            # Get response
            response = await current_speaker.kickoff_async(current_messages)
            
            turn = DiscussionTurn(
                turn_number=turn_num,
                speaker=current_speaker_name,
                listener=current_listener_name,
                prompt=prompt,
                response=response.raw,
            )
            self.turns.append(turn)
            
            # Add to speaker's history
            current_messages.append(cast(LLMMessage, {"role": "assistant", "content": response.raw}))
            
            logger.info(f"Turn {turn_num}: {current_speaker_name} spoke ({len(response.raw)} chars)")
            
            # Swap speakers for next turn
            if current_speaker == self.agent2:
                current_speaker = self.agent1
                current_listener = self.agent2
                current_speaker_name = self.character1.name
                current_listener_name = self.character2.name
                current_messages = self.messages1
            else:
                current_speaker = self.agent2
                current_listener = self.agent1
                current_speaker_name = self.character2.name
                current_listener_name = self.character1.name
                current_messages = self.messages2
            
            last_response = response.raw
        
        logger.info(f"Discussion completed: {len(self.turns)} turns")
        return self.turns
    
    def format_transcript(self) -> str:
        """Format the discussion as a readable transcript"""
        transcript = []
        transcript.append("=" * 80)
        transcript.append(f"DISCUSSION: {self.character1.name} & {self.character2.name}")
        transcript.append("=" * 80)
        transcript.append("")
        
        for turn in self.turns:
            transcript.append(f"--- Turn {turn.turn_number}: {turn.speaker} ---")
            transcript.append("")
            transcript.append(turn.response)
            transcript.append("")
            transcript.append("-" * 80)
            transcript.append("")
        
        return "\n".join(transcript)
    
    def save_transcript(self, filename: str):
        """Save the discussion transcript to a file"""
        from pathlib import Path
        
        output_dir = Path("output") / f"book_{self.workflow_id}" / "discussions"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_file = output_dir / filename
        with open(output_file, 'w') as f:
            f.write(self.format_transcript())
        
        logger.info(f"Transcript saved to: {output_file}")
        return output_file
