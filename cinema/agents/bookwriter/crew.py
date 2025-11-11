from pathlib import Path
from typing import Any, Optional, Type, TypedDict

import yaml
from crewai import Agent, Crew, CrewOutput, Task, Process
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.knowledge.source.text_file_knowledge_source import TextFileKnowledgeSource
from crewai.project import CrewBase
from crewai_tools import DirectoryReadTool, FileReadTool
from pydantic import BaseModel

from cinema.context import DirectorsContext
from cinema.models.detective_output import DetectiveStoryOutput
from cinema.providers.shared import CrewConfig
from cinema.registry import LLMCritiqueIntent, LLMExecutorIntent, LLMPlannerIntent
import logging

# Note: Character and RelationshipGraph are imported in detective.py
# Removed DetectivePlotBuilderSchema as it's unused and causes Pydantic schema errors

logger = logging.getLogger(__name__)


class DetectivePlotBuilderSchema(BaseModel):
    characters: Any  # List of character dicts
    relationships: Any  # List of relationship dicts
    killer: Any
    victim: Any
    accomplices: Any
    witnesses: Any
    betrayals: Any
    feedback: Optional[str] = ""


class StripperInputSchema(BaseModel):
    art_style: str
    examples: str
    storyline: Optional[str] = None


class CritiqueSchema(BaseModel):
    storyline: str


@CrewBase
class DetectivePlotBuilder:
    agents_config = "plotbuilder/agents.yaml"
    tasks_config = "plotbuilder/tasks.yaml"

    config: CrewConfig
    narrative_index_docs: TextFileKnowledgeSource

    ctx: Optional[DirectorsContext] = None

    role_name: str = "detective"
    outfile: str = "detective_storyline.md"

    def __init__(self, ctx: DirectorsContext, outfile: Optional[str] = None):
        self.ctx = ctx
        self.config = CrewConfig()

        if outfile:
            self.outfile = outfile

        self.narrative_index_docs = TextFileKnowledgeSource(
            file_paths=[
                "storywriting/detective/principles.md",
                "storywriting/detective/narrative-techniques.md",
                "narrative-structures/index.md"
            ],
        )

        knowledge_dir = Path(__file__).parent.parent.parent.parent / "knowledge"

        self.config.tools = [
            # Allow agent to explore cinematic styles directory when needed
            DirectoryReadTool(directory=str(knowledge_dir / "narrative-structures")),
            FileReadTool(),
        ]

    @classmethod
    def collect(
        cls,
        result: CrewOutput,
        output_model: Optional[Type[BaseModel]] = None,
    ) -> BaseModel | str | None:

        if not output_model:
            return result.raw

        return output_model.model_validate(result.pydantic)

    def _validate_ctx(self):
        assert self.ctx is not None, "EmptyCtx"

    def get_config(self):
        return self.config

    def bootstrap(self):
        assert self.ctx is not None

        agent = Agent(
            config=self.agents_config[self.role_name],  # type: ignore[index]
            llm=self.ctx.llmstore.load(LLMPlannerIntent),
            tools=self.config.tools,
            verbose=self.ctx.debug,
        )

        task = Task(
            config=self.tasks_config[self.role_name],  # type: ignore[index]
            agent=agent,
            output_file=self.outfile,
            markdown=True,
        )

        # manager = Agent(
        #     config=self.agents_config["manager"],  # type:ignore[index]
        #     llm=self.ctx.llmstore.load(LLMLongPlannerIntent),
        #     tools=self.config.tools,
        #     verbose=self.ctx.debug,
        # )

        self.config.agents.append(agent)
        self.config.tasks.append(task)

        return self

    def crew(self):
        assert self.ctx is not None

        self.bootstrap()

        return Crew(
            agents=self.config.agents,
            tasks=self.config.tasks,
            verbose=self.ctx.debug,
            planning=True,
            knowledge_sources=[self.narrative_index_docs],
        )


@CrewBase
class PlotCritique:
    agents_config = "plotbuilder/agents.yaml"
    tasks_config = "plotbuilder/tasks.yaml"

    config: CrewConfig
    narrative_index_docs: TextFileKnowledgeSource

    ctx: Optional[DirectorsContext] = None

    role_name: str = "critique"
    outfile: str = "critique_storyline.md"

    def __init__(self, ctx: DirectorsContext, outfile: Optional[str] = None):
        self.ctx = ctx
        self.config = CrewConfig()

        if outfile:
            self.outfile = outfile

        self.narrative_index_docs = TextFileKnowledgeSource(
            file_paths=[
                "storywriting/detective/principles.md",
                "storywriting/detective/narrative-techniques.md",
                "narrative-structures/index.md"
            ],
        )

        knowledge_dir = Path(__file__).parent.parent.parent.parent / "knowledge"

        self.config.tools = [
            # Allow agent to explore cinematic styles directory when needed
            DirectoryReadTool(directory=str(knowledge_dir / "narrative-structures")),
            FileReadTool(),
        ]

    @classmethod
    def collect(
        cls,
        result: CrewOutput,
        output_model: Optional[Type[BaseModel]] = None,
    ) -> BaseModel | str | None:

        if not output_model:
            return result.raw

        return output_model.model_validate(result.pydantic)

    def _validate_ctx(self):
        assert self.ctx is not None, "EmptyCtx"

    def get_config(self):
        return self.config

    def bootstrap(self):
        assert self.ctx is not None

        agent = Agent(
            config=self.agents_config[self.role_name],  # type:ignore[index]
            llm=self.ctx.llmstore.load(LLMCritiqueIntent),
            tools=self.config.tools,
            verbose=self.ctx.debug,
        )

        task = Task(
            config=self.tasks_config[self.role_name],  # type:ignore[index]
            agent=agent,
            output_file=f"{self.outfile}",
            markdown=True,
        )

        self.config.agents.append(agent)
        self.config.tasks.append(task)

    def crew(self):
        assert self.ctx is not None

        self.bootstrap()

        return Crew(
            agents=self.config.agents,
            tasks=self.config.tasks,
            verbose=self.ctx.debug,
            planning=True,
            knowledge_sources=[self.narrative_index_docs],
        )


@CrewBase
class ComicStripStoryBoarding:
    agents_config = "plotbuilder/agents.yaml"
    tasks_config = "plotbuilder/tasks.yaml"

    config: CrewConfig
    narrative_index_docs: TextFileKnowledgeSource

    ctx: Optional[DirectorsContext] = None

    role_name: str = "stripper"
    outfile: str = "comic_generator.json"

    def __init__(self, ctx: DirectorsContext, outfile: Optional[str] = None):
        self.ctx = ctx
        self.config = CrewConfig()

        if outfile:
            self.outfile = outfile

        self.narrative_index_docs = TextFileKnowledgeSource(
            file_paths=[
                "art-styles/styles.md",
                "moviemaking/storytelling.md",
                "moviemaking/storyboarding.md",
                "moviemaking/continuity.md",
            ],
        )

        knowledge_dir = Path(__file__).parent.parent.parent.parent / "knowledge"

        self.config.tools = [
            DirectoryReadTool(directory=str(knowledge_dir / "gemini")),
            DirectoryReadTool(directory=str(knowledge_dir / "art-styles")),
            FileReadTool(),
        ]

    @classmethod
    def collect(
        cls,
        result: CrewOutput,
        output_model: Optional[Type[BaseModel]] = None,
    ) -> BaseModel | str | None:

        if not output_model:
            return result.raw

        return output_model.model_validate(result.pydantic)

    @classmethod
    def load_examples(cls):
        try:
            with open(
                Path(__file__).parent / "plotbuilder/examples.yaml",
                "r+",
            ) as f:
                examples_config = yaml.safe_load(f)
                return examples_config["stripper"]["examples"]

        except Exception as e:
            print(e)
            return ""

    def _validate_ctx(self):
        assert self.ctx is not None, "EmptyCtx"

    def bootstrap(self):
        assert self.ctx is not None

        plotbuilder_agent = Agent(
            config=self.agents_config[self.role_name],  # type:ignore[index]
            llm=self.ctx.llmstore.load(LLMExecutorIntent),
            tools=self.config.tools,
            verbose=self.ctx.debug,
        )

        plotbuilder_task = Task(
            config=self.tasks_config[self.role_name],  # type:ignore[index],
            agent=plotbuilder_agent,
            output_file=self.outfile,
            output_pydantic=DetectiveStoryOutput,
        )

        self.config.agents.append(plotbuilder_agent)
        self.config.tasks.append(plotbuilder_task)

    def crew(self):
        assert self.ctx is not None, "EmptyCtx"

        self.bootstrap()

        return Crew(
            agents=self.config.agents,
            tasks=self.config.tasks,
            verbose=self.ctx.debug,
            knowledge_sources=[self.narrative_index_docs],
        )


@CrewBase
class PlotBuilderWithCritique:
    """
    DEPRECATED: Crew-based implementation with hierarchical manager.
    
    This uses a manager agent to orchestrate between PlotBuilder and Critique,
    but provides limited control over the iteration logic.
    
    RECOMMENDED: Use PlotBuilderWithCritiqueFlow from flow.py instead.
    The Flow-based version provides:
    - Explicit state machine control
    - Observable iteration state
    - Deterministic routing logic
    - Better debugging capabilities
    """
    ## not really needed
    agents_config = "plotbuilder/agents.yaml"
    tasks_config = "plotbuilder/tasks.yaml"

    ctx: DirectorsContext

    plotbuilder: DetectivePlotBuilder
    critique: PlotCritique
    manager: BaseAgent

    role_name: str = "manager"

    def __init__(self, ctx, plotbuilder, critique) -> None:
        self.ctx = ctx
        self.plotbuilder = plotbuilder
        self.critique = critique

    def bootstrap(self):
        self.plotbuilder.bootstrap()
        self.critique.bootstrap()

        self.manager = Agent(
            config=self.agents_config[self.role_name],  # type: ignore[index]            
            goal=(
                "Orchestrate collaboration between the DetectivePlotBuilder and Critque to produce a refined storyline."
                "Use the verdict from the critique to refine the plot"
            ),
            llm=self.ctx.llmstore.load(LLMPlannerIntent),
            allow_delegation=True,
            verbose=self.ctx.debug,
            max_iter=3,
        )

        return self

    def crew(self):
        self.bootstrap()

        pbc: CrewConfig = self.plotbuilder.get_config()
        cbc: CrewConfig = self.critique.get_config()
        agents = [
            *pbc.agents,
            *cbc.agents,
        ]

        p_task = pbc.tasks[0]
        c_task = cbc.tasks[0]

        p_task.description = p_task.description + "\n" + c_task.description

        tasks = [
            p_task,
        ]

        logger.info(f"agents count: {len(agents)}")
        logger.info(f"tasks count: {len(tasks)}")

        return Crew(
            agents=agents,
            tasks=tasks,
            manager_agent=self.manager,
            process=Process.hierarchical, 
            verbose=self.ctx.debug,
        )

