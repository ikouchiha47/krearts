"""
Character Agent Crew - Core classes for character-based agents.

For testing and interactive usage, see:
    cinema/cmd/examples/test_character_qa.py
"""

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


logger = logging.getLogger(__name__)

# Type alias for knowledge sources
KnowledgeSources = Union[BaseKnowledgeSource, BaseFileKnowledgeSource, None]

CHARACTER_TASK_DESC = """
CRITICAL INSTRUCTIONS - YOU MUST FOLLOW THIS FORMAT:

Your response MUST be structured with these four sections. Do NOT skip any section:

## Thoughts
[Your internal reasoning, motivations, and mental state - REQUIRED]

## Observations
[What you notice in the environment, people, or situation - REQUIRED]

## Actions
[Physical actions you take, movements, gestures - REQUIRED]

## Reasoning
[Explicit explanation of WHY you took those actions - REQUIRED]

IMPORTANT:
- All four sections are MANDATORY for every response
- Include the character's thoughts and reasons for any decision taken
- Actions and Reasoning must be coherent with the character's traits
- Maintain consistency with your personality, quirks, and backstory
- If you have past memories, reference them when relevant

This structure is essential for tracking your decisions and maintaining continuity.
"""

class CharacterAgentBuilder:
    """Builder for creating a CrewAI Agent from a Character with optional context"""
    
    character: Character
    ctx: DirectorsContext

    memory: Optional[KnowledgeSources] = None

    _include_relationships: bool = False
    _relationship_context: Optional[str] = None
    _additional_context: List[str] = []
    
    def __init__(
        self,
        ctx: DirectorsContext,
        character: Character,
        memory: Optional[KnowledgeSources] = None,
    ):
        self.character = character
        self.ctx = ctx
        self.memory = memory
        self._additional_context = []
    
    def with_relationships(self, relationship_context: Optional[str] = None) -> "CharacterAgentBuilder":
        """
        Include relationship information in the agent.
        
        Args:
            relationship_context: Optional custom relationship text. 
                                 If None, uses character's built-in relationships.
        """
        self._include_relationships = True
        self._relationship_context = relationship_context
        return self
    
    def with_context(self, context: str) -> "CharacterAgentBuilder":
        """Add additional context to the agent's backstory"""
        self._additional_context.append(context)
        return self
    
    def _build_role(self) -> str:
        """Build normalized role name without special characters"""
        # Normalize name: remove quotes, special chars, use underscores
        import re
        normalized = re.sub(r'["\'/\\]', '', self.character.name)
        normalized = re.sub(r'[^\w\s-]', '', normalized)
        normalized = re.sub(r'[-\s]+', '_', normalized)
        return normalized.strip('_')
    
    def _build_goal(self) -> str:
        """Build goal from character motivations and long-term goals"""
        goal_parts = []
        
        if self.character.long_term_goals:
            goal_parts.append(self.character.long_term_goals)
        
        if self.character.motivations:
            goal_parts.append(self.character.motivations)
        
        return " ".join(goal_parts) if goal_parts else f"Act as {self.character.name}"
    
    def _build_backstory(self) -> str:
        """Build rich backstory including personality and optional relationships"""
        backstory_parts = [self.character.backstory]
        
        # Personality traits
        if self.character.quirks:
            backstory_parts.append("\n\nPersonality Quirks:")
            for quirk in self.character.quirks:
                backstory_parts.append(f"- {quirk}")
        
        # Core beliefs
        if self.character.identity_anchors:
            backstory_parts.append(f"\n\nCore Beliefs:\n{self.character.identity_anchors}")
        
        # Stress responses
        if self.character.triggers_stress:
            backstory_parts.append(f"\n\nUnder Pressure:\n{self.character.triggers_stress}")
        
        # Relationships (optional - only if explicitly requested)
        if self._include_relationships:
            relationship_text = self._relationship_context or self.character.relationships
            if relationship_text:
                backstory_parts.append(f"\n\nKey Relationships:\n{relationship_text}")
        
        # Skills
        if self.character.skills_toolkit:
            backstory_parts.append(f"\n\nSkills:\n{self.character.skills_toolkit}")
        
        # Additional context
        if self._additional_context:
            backstory_parts.append("\n\nAdditional Context:")
            for ctx in self._additional_context:
                backstory_parts.append(ctx)

        return "\n".join(backstory_parts)
    
    def build(self) -> Agent:
        """Create CrewAI Agent from character data"""
        return Agent(
            role=self._build_role(),
            goal=self._build_goal(),
            backstory=self._build_backstory(),
            knowledge_sources=self.memory,
            llm=self.ctx.llmstore.load(LLMThinkerIntent),
            verbose=self.ctx.debug,
            allow_delegation=False,
        )

    def build_task(self):
        """Instructions that enforce structured response format"""
        return CHARACTER_TASK_DESC


class CharacterMemoryStore:
    """Manages character decision memory across interactions"""
    
    def __init__(self, workflow_id: str, character: Character):
        self.workflow_id = workflow_id
        self.character = character
        self.character_dir = self._get_character_dir()
        self.memory_file = self.character_dir / "memory.json"
        self.character_file = self.character_dir / "character.json"
        
        # Initialize storage
        self._initialize_storage()
    
    def _normalize_name(self, name: str) -> str:
        """Normalize character name for filesystem"""
        # Remove quotes, special chars, convert to lowercase with underscores
        normalized = re.sub(r'["\'/\\]', '', name)
        normalized = re.sub(r'[^\w\s-]', '', normalized)
        normalized = re.sub(r'[-\s]+', '_', normalized)
        return normalized.lower().strip('_')
    
    def _get_character_dir(self) -> Path:
        """Get character-specific directory path"""
        base_dir = Path("output") / f"book_{self.workflow_id}" / "characters"
        char_name = self._normalize_name(self.character.name)
        return base_dir / char_name
    
    def _initialize_storage(self):
        """Create directory structure and initialize files"""
        self.character_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize character.json if it doesn't exist
        if not self.character_file.exists():
            character_data = {
                "name": self.character.name,
                "role": self.character.role,
                "created_at": datetime.now().isoformat(),
            }
            with open(self.character_file, 'w') as f:
                json.dump(character_data, f, indent=2)
        
        # Initialize memory.json if it doesn't exist
        if not self.memory_file.exists():
            with open(self.memory_file, 'w') as f:
                json.dump([], f, indent=2)
    
    def add_memory(self, question: str, response: str):
        """
        Add a decision memory entry.
        
        Args:
            question: The question/situation presented
            response: The full response including structured sections
        """
        # Parse structured sections from response
        parsed = self._parse_response(response)
        
        memory_entry = {
            "timestamp": datetime.now().isoformat(),
            "question": question,
            "thoughts": parsed.get("thoughts", ""),
            "observations": parsed.get("observations", ""),
            "actions": parsed.get("actions", ""),
            "reasoning": parsed.get("reasoning", ""),
            "answer": response,
        }
        
        # Load existing memories
        with open(self.memory_file, 'r') as f:
            memories = json.load(f)
        
        # Append new memory
        memories.append(memory_entry)
        
        # Save back
        with open(self.memory_file, 'w') as f:
            json.dump(memories, f, indent=2)
        
        logger.info(f"Added memory entry for {self.character.name}")
    
    def _parse_response(self, response: str) -> dict:
        """Parse structured sections from response"""
        sections = {}
        
        # Extract each section using regex
        patterns = {
            "thoughts": r"##\s*Thoughts\s*\n(.*?)(?=##|\Z)",
            "observations": r"##\s*Observations\s*\n(.*?)(?=##|\Z)",
            "actions": r"##\s*Actions\s*\n(.*?)(?=##|\Z)",
            "reasoning": r"##\s*Reasoning\s*\n(.*?)(?=##|\Z)",
        }
        
        for key, pattern in patterns.items():
            match = re.search(pattern, response, re.DOTALL | re.IGNORECASE)
            if match:
                sections[key] = match.group(1).strip()
        
        return sections
    
    def get_memory_count(self) -> int:
        """Get number of stored memories"""
        if not self.memory_file.exists():
            return 0
        
        with open(self.memory_file, 'r') as f:
            memories = json.load(f)
        
        return len(memories)
    
    def get_memory_text(self, max_recent: int = 10) -> str:
        """
        Get memories as formatted text for knowledge base.
        
        Args:
            max_recent: Maximum number of recent memories to include (0 = all)
        """
        if not self.memory_file.exists():
            return ""
        
        with open(self.memory_file, 'r') as f:
            memories = json.load(f)
        
        if not memories:
            return ""
        
        # Limit to most recent memories if specified
        if max_recent > 0 and len(memories) > max_recent:
            memories = memories[-max_recent:]
            memory_text = f"# Recent Decision Memory for {self.character.name}\n"
            memory_text += f"(Showing last {len(memories)} of {self.get_memory_count()} total memories)\n\n"
        else:
            memory_text = f"# Decision Memory for {self.character.name}\n\n"
        
        # Format memories as text
        for i, entry in enumerate(memories, 1):
            memory_text += f"## Memory {i}\n"
            memory_text += f"**Question:** {entry['question']}\n\n"
            
            if entry.get('thoughts'):
                memory_text += f"**Thoughts:** {entry['thoughts']}\n\n"
            if entry.get('observations'):
                memory_text += f"**Observations:** {entry['observations']}\n\n"
            if entry.get('actions'):
                memory_text += f"**Actions:** {entry['actions']}\n\n"
            if entry.get('reasoning'):
                memory_text += f"**Reasoning:** {entry['reasoning']}\n\n"
            
            memory_text += "---\n\n"
        
        return memory_text


class CharacterQA:
    """Wrapper for character Q&A interactions with memory"""
    
    ctx: DirectorsContext
    character: Character
    agent: Agent
    builder: CharacterAgentBuilder
    memory_store: Optional[CharacterMemoryStore]

    def __init__(
        self, 
        ctx: DirectorsContext, 
        character: Character,
        workflow_id: Optional[str] = None,
        enable_memory: bool = False,
    ) -> None:
        self.ctx = ctx
        self.character = character
        
        # Initialize memory store if enabled
        if enable_memory and workflow_id:
            self.memory_store = CharacterMemoryStore(workflow_id, character)
        else:
            self.memory_store = None

    def bootstrap(self, include_relationships: bool = False):
        """
        Bootstrap the agent.
        
        Args:
            include_relationships: Whether to include relationship context in the agent
        """
        self.builder = CharacterAgentBuilder(ctx=self.ctx, character=self.character)
        
        if include_relationships:
            self.builder.with_relationships()
        
        # Add memory as knowledge source if available
        if self.memory_store:
            memory_text = self.memory_store.get_memory_text()
            if memory_text:
                memory_source = StringKnowledgeSource(content=memory_text)
                self.builder.memory = memory_source
        
        self.agent = self.builder.build()
        return self

    async def kickoff_async(self, messages: List[LLMMessage]):
        """
        Execute agent with messages.
        
        Memory is reloaded before each interaction to include recent decisions.
        Task instructions are added to ensure structured responses.
        """
        # RELOAD memory before each interaction to get latest entries
        if self.memory_store:
            memory_text = self.memory_store.get_memory_text()
            if memory_text:
                # Update agent's knowledge source with latest memories
                memory_source = StringKnowledgeSource(content=memory_text)
                self.agent.knowledge_sources = [memory_source]
                memory_count = self.memory_store.get_memory_count()
                logger.debug(f"Reloaded {memory_count} memories for {self.character.name}")
        
        # Extract the question from messages
        question = ""
        if messages:
            for msg in reversed(messages):
                if msg.get("role") == "user":
                    question = msg.get("content", "")
                    break
        
        # Build enhanced messages with task instructions
        task_instructions = self.builder.build_task()
        enhanced_messages = []
        
        # Add system messages (storyline + task instructions)
        if messages and messages[0].get("role") == "system":
            enhanced_messages.append(messages[0])
            # Add task instructions as system message
            enhanced_messages.append({"role": "system", "content": task_instructions})
            # Add rest of messages
            enhanced_messages.extend(messages[1:])
        else:
            # No system message, add task instructions first
            enhanced_messages.append({"role": "system", "content": task_instructions})
            enhanced_messages.extend(messages)
        
        # Execute agent
        result = await self.agent.kickoff_async(enhanced_messages)
        
        # Store memory if enabled
        if self.memory_store and question and isinstance(question, str):
            self.memory_store.add_memory(question, result.raw)
            logger.info(f"Stored memory entry for {self.character.name}: {question[:50]}...")
        
        return result
