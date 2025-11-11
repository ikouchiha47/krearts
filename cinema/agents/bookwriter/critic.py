"""
Detective Plot Critic
Validates detective storylines against established principles.
"""

import logging
from pathlib import Path
from typing import Optional

from crewai import Agent, Crew, Task
from crewai.knowledge.source.text_file_knowledge_source import TextFileKnowledgeSource
from crewai_tools import DirectoryReadTool, FileReadTool

from cinema.context import DirectorsContext
from cinema.providers.shared import CrewConfig
from cinema.registry import LLMPlannerIntent

logger = logging.getLogger(__name__)


class DetectivePlotCritic:
    """
    Critique detective storylines against principles.
    Validates evidence density, motive concreteness, forensic multilayering, etc.
    """

    agents_config = "plotbuilder/agents.yaml"
    tasks_config = "plotbuilder/tasks.yaml"

    config: CrewConfig
    knowledge_sources: TextFileKnowledgeSource

    ctx: Optional[DirectorsContext] = None
    role_name: str = "critic"
    outfile: str = "detective_critique.md"

    def __init__(self, ctx: DirectorsContext, outfile: Optional[str] = None):
        self.ctx = ctx
        self.config = CrewConfig()

        if outfile:
            self.outfile = outfile

        # Load detective principles and narrative structures
        self.knowledge_sources = TextFileKnowledgeSource(
            file_paths=[
                "storywriting/detective/principles.md",
                "storywriting/detective/narrative-techniques.md",
                "narrative-structures/index.md",
            ],
        )

        knowledge_dir = Path(__file__).parent.parent.parent.parent / "knowledge"

        self.config.tools = [
            DirectoryReadTool(directory=str(knowledge_dir / "storywriting")),
            DirectoryReadTool(directory=str(knowledge_dir / "narrative-structures")),
            FileReadTool(),
        ]

    def bootstrap(self):
        """Initialize critic agent and task"""
        assert self.ctx is not None

        critic_agent = Agent(
            config=self.agents_config[self.role_name],  # type: ignore[index]
            llm=self.ctx.llmstore.load(LLMPlannerIntent),
            tools=self.config.tools,
            verbose=self.ctx.debug,
        )

        critic_task = Task(
            config=self.tasks_config[self.role_name],  # type: ignore[index]
            agent=critic_agent,
            output_file=self.outfile,
            markdown=True,
        )

        self.config.agents.append(critic_agent)
        self.config.tasks.append(critic_task)

        return self

    def crew(self):
        """Create crew for critique"""
        assert self.ctx is not None

        self.bootstrap()

        return Crew(
            agents=self.config.agents,
            tasks=self.config.tasks,
            verbose=self.ctx.debug,
            knowledge_sources=[self.knowledge_sources],
        )

    async def critique_storyline(self, storyline: str) -> str:
        """
        Critique a detective storyline.
        
        Args:
            storyline: The detective storyline markdown text
            
        Returns:
            Critique report as markdown
        """
        logger.info("Starting detective storyline critique...")

        inputs = {"storyline": storyline}

        result = await self.crew().kickoff_async(inputs=inputs)

        logger.info(f"Critique complete. Report saved to: {self.outfile}")

        return result.raw

    async def critique_from_file(self, storyline_file: str) -> str:
        """
        Critique a detective storyline from a file.
        
        Args:
            storyline_file: Path to the storyline markdown file
            
        Returns:
            Critique report as markdown
        """
        with open(storyline_file, "r") as f:
            storyline = f.read()

        return await self.critique_storyline(storyline)
