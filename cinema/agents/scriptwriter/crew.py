from pathlib import Path
from typing import Any, Optional, Type

import yaml
from crewai import Agent, Crew, CrewOutput, Task
from crewai.knowledge.source.text_file_knowledge_source import TextFileKnowledgeSource
from crewai.project import CrewBase
from crewai_tools import DirectoryReadTool, FileReadTool
from pydantic import BaseModel, Field

from cinema.agents.tools.image_analyser import AnalyzeImagesTool
from cinema.context import DirectorsContext
from cinema.models import CinematgrapherCrewOutput
from cinema.providers.shared import CrewConfig, MediaLib
from cinema.registry import LLMPlannerIntent


def to_md_list(items: list[str]):
    return "\n".join([f"- {item}" for item in items])


class ScriptWriterSchema(BaseModel):
    characters: list[str]
    images: list[str]
    script: str
    examples: Optional[str] = ""
    transition_definitons: str = Field(default="")

    def to_crew(self):
        return {
            "characters": to_md_list(self.characters),
            "images": to_md_list(self.images),
            "examples": self.examples,
            "script": self.script,
        }


@CrewBase
class ScriptWriter:
    agents_config = "agents.yaml"
    tasks_config = "tasks.yaml"
    examples_config_file = "examples.yaml"

    config: CrewConfig

    medialib: MediaLib
    transitions_source: TextFileKnowledgeSource
    examples_config: Optional[dict[str, Any]] = None

    ctx: Optional[DirectorsContext] = None

    role_name: str = "script_writer"

    def __init__(
        self,
        ctx: DirectorsContext,
        medialib: MediaLib,
    ):
        self.ctx = ctx
        self.config = CrewConfig()

        # Load transitions vocabulary as knowledge source (always available)
        self.transitions_source = TextFileKnowledgeSource(
            file_paths=["transitions/vocabulary.txt"]
        )

        with open(Path(__file__).parent / "examples.yaml", "r+") as f:
            self.examples_config = yaml.safe_load(f)

        # Initialize tools for additional knowledge exploration
        knowledge_dir = Path(__file__).parent.parent.parent.parent / "knowledge"
        
        self.config.tools = [
            AnalyzeImagesTool(medialib=medialib),
            # Agent can explore director styles ONLY when they serve the cinematic purpose
            DirectoryReadTool(directory=str(knowledge_dir / "cinematic-styles" / "director-styles")),
            # Agent can explore narrative structures when planning story
            DirectoryReadTool(directory=str(knowledge_dir / "narrative-structures")),
            # Agent can read any specific file when needed
            FileReadTool(),
        ]

    @classmethod
    def load_examples(cls):
        try:
            with open(Path(__file__).parent / "examples.yaml", "r+") as f:
                examples_config = yaml.safe_load(f)
                return examples_config["script_writer"]["examples"]

        except Exception as e:
            print(e)
            return ""

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

    # @before_kickoff
    # def prepare_examples(self, inputs):
    #     if not self.examples_config:
    #         return inputs
    #
    #     inputs["examples"] = self.examples_config[self.role_name]["examples"]
    #     return inputs

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
            output_file="script.md",
            markdown=True,
        )

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
            knowledge_sources=[self.transitions_source],
        )


class EnhancerInputSchema(BaseModel):
    script: str
    screenplay: str

    def to_crew(self):
        return self.model_dump()


@CrewBase
class Enhancer:
    agents_config = "agents.yaml"
    tasks_config = "tasks.yaml"

    config: CrewConfig
    gemini_prompting_docs: TextFileKnowledgeSource

    ctx: Optional[DirectorsContext] = None

    role_name: str = "gemini/enhancer"

    def __init__(self, ctx: DirectorsContext):
        self.ctx = ctx
        self.config = CrewConfig()

        # Load Gemini docs and transitions as knowledge sources (always available)
        self.gemini_prompting_docs = TextFileKnowledgeSource(
            file_paths=[
                "gemini/image-prompting.md",
                "gemini/video-prompting.md",
                "gemini/video-gen-workflow.md",
                "transitions/vocabulary.md",
            ]
        )

        # Initialize tools for additional knowledge exploration
        knowledge_dir = Path(__file__).parent.parent.parent.parent / "knowledge"
        
        self.config.tools = [
            # Allow agent to explore cinematic styles directory when needed
            DirectoryReadTool(directory=str(knowledge_dir / "cinematic-styles")),
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

    def bootstrap(self):
        assert self.ctx is not None, "EmptyCtx"

        provider, role = self.role_name.split("/", 1)

        agent = Agent(
            config=self.agents_config[provider][role],  # type: ignore[index]
            llm=self.ctx.llmstore.load(LLMPlannerIntent),
            reasoning=True,
            verbose=self.ctx.debug,
            tools=self.config.tools,
        )

        task = Task(
            config=self.tasks_config[provider][role],  # type: ignore[index]
            agent=agent,
            output_file="gemini_screenplay.md",
            # markdown=True,
            output_pydantic=CinematgrapherCrewOutput,
        )

        self.config.agents.append(agent)
        self.config.tasks.append(task)

        return self

    def crew(self):
        assert self.ctx is not None, "EmptyCtx"

        self.bootstrap()

        return Crew(
            agents=self.config.agents,
            tasks=self.config.tasks,
            verbose=self.ctx.debug,
            knowledge_sources=[self.gemini_prompting_docs],
        )