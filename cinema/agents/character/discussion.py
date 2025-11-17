"""
Character Discussion Crew - Uses CrewAI with manager agent to coordinate multi-character discussions.
"""

import logging
from pathlib import Path
from typing import List, Optional

from crewai import Agent, Crew, Task, Process
from crewai.project import CrewBase
from pydantic import BaseModel

from cinema.agents.character.crew import CharacterAgentBuilder
from cinema.context import DirectorsContext
from cinema.models.storyline import Character
from cinema.registry import LLMPlannerIntent
from cinema.providers.shared import CrewConfig


logger = logging.getLogger(__name__)

class CharacterDiscussionSchema(BaseModel):
    storyline: str
    discussion_goal: str
    characters: List[Character]

    def _build_character_agendas(self) -> str:
        """Format character agendas for the task description"""
        agendas = []
        for char in self.characters:
            agenda = f"- {char.name} ({char.role}):\n"
            if char.motivations:
                agenda += f"  Motivation: {char.motivations}\n"
            if char.long_term_goals:
                agenda += f"  Goal: {char.long_term_goals}\n"
            agendas.append(agenda)
        return "\n".join(agendas)
    
    def to_crew(self):
        result = dict(
            storyline=self.storyline,
            discussion_goal=self.discussion_goal,
            character_names=", ".join([c.name for c in self.characters]),
            character_agendas=self._build_character_agendas(),
        )

        return result


@CrewBase
class CharacterDiscussionCrew:
    agents_config = "agents.yaml"
    tasks_config = "tasks.yaml"

    config: CrewConfig

    role_name: str = "discussion"
    
    def __init__(
        self,
        ctx: DirectorsContext,
        characters: List[Character],
        workflow_id: Optional[str] = None,
    ):
        self.ctx = ctx
        self.characters = characters
        self.workflow_id = workflow_id

        self.config = CrewConfig()

    def _build_character_agents(self) -> List[Agent]:
        """Build CrewAI agents for each character"""

        agents = []
        
        for character in self.characters:
            builder = CharacterAgentBuilder(
                ctx=self.ctx,
                character=character,
            )
            
            # Add relationships for context
            builder.with_relationships()
            
            agent = builder.build()
            agents.append(agent)
            
            logger.info(f"Built agent for {character.name}")
        
        return agents
    
    def _build_manager_agent(self) -> Agent:
        """Coordinate the discussion"""

        return Agent(
            config=self.agents_config["detective"]["manager"],  # type: ignore[index]
            llm=self.ctx.llmstore.load(LLMPlannerIntent),
            verbose=self.ctx.debug,
            allow_delegation=True,
        )

    def bootstrap(self):
        # Build agents
        self.config.agents.extend(self._build_character_agents())
        self.config.manager_agent = self._build_manager_agent()

        task = Task(
            config=self.tasks_config["discussion"],  # type: ignore[index]
            agent=self.config.manager_agent,
        )

        self.config.tasks.append(task)
        return self

    def crew(self):
        self.bootstrap()

        print(self.config.agents)
        print(self.config.tasks)

        return Crew(
            agents=self.config.agents,
            tasks=self.config.tasks,
            process=Process.hierarchical,
            manager_agent=self.config.manager_agent,
            verbose=self.ctx.debug,
        )

    
    def save_transcript(self, transcript: str, filename: str) -> Path:
        """Save discussion transcript to file"""
        if self.workflow_id:
            output_dir = Path("output") / f"book_{self.workflow_id}" / "discussions"
        else:
            output_dir = Path("output") / "discussions"
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_file = output_dir / filename
        with open(output_file, 'w') as f:
            f.write(transcript)
        
        logger.info(f"Transcript saved to: {output_file}")
        return output_file
