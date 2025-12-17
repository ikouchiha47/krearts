import asyncio
import logging
from pathlib import Path
from typing import Any, List, NewType, Optional, Type, TypeAlias, TypeVar, Union

from crewai.knowledge.source.base_file_knowledge_source import BaseFileKnowledgeSource
from crewai.knowledge.source.base_knowledge_source import BaseKnowledgeSource
import yaml
from crewai import Agent, Crew, CrewOutput, Knowledge, Task
from crewai.knowledge.source.text_file_knowledge_source import TextFileKnowledgeSource
from crewai.knowledge.source.string_knowledge_source import StringKnowledgeSource
from crewai.memory.external.external_memory import ExternalMemory
from crewai.project import CrewBase
from crewai_tools import DirectoryReadTool, FileReadTool
from pydantic import BaseModel, Field

from cinema.agents.bookwriter.tools.multi_directory_read_tool import MultiDirectoryReadTool
from cinema.agents.bookwriter.utils import clean_agent_thinking_from_output
from cinema.context import DirectorsContext
from cinema.models.detective_output import DetectiveStoryOutput
from cinema.models.comic_output import ComicBookOutput
from cinema.providers.shared import CrewConfig
from cinema.registry import (
    LLMCritiqueIntent,
    LLMExecutorIntent,
    LLMPlannerIntent,
    LLMThinkerIntent,
    ModelConfig,
    OpenAiHerd,
)

# Note: Character and RelationshipGraph are imported in detective.py
# Removed DetectivePlotBuilderSchema as it's unused and causes Pydantic schema errors

logger = logging.getLogger(__name__)

# Constants
KNOWLEDGE_DIR = Path(__file__).parent.parent.parent.parent / "knowledge"

T = TypeVar("T", bound=BaseModel)


class KnowledgeSourceRegistry:
    """Singleton registry for knowledge sources"""
    _instance = None
    _cache: dict[str, TextFileKnowledgeSource] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def get(self, key: str, file_paths: List[str]) -> TextFileKnowledgeSource:
        """Get or create knowledge source for given key and file paths"""
        if key not in self._cache:
            self._cache[key] = TextFileKnowledgeSource(file_paths=file_paths)
        return self._cache[key]

    def set(self, key: str, knowledge_source: TextFileKnowledgeSource) -> None:
        """Set a knowledge source for a given key"""
        self._cache[key] = knowledge_source

    def clear(self) -> None:
        """Clear all cached knowledge sources"""
        self._cache.clear()


# Global registry instance
# inject it in the crews
knowledge_registry = KnowledgeSourceRegistry()


class DetectivePlotBuilderSchema(BaseModel):
    characters: Any  # List of character dicts
    relationships: Any  # List of relationship dicts
    killer: Any
    victim: Any
    accomplices: Any
    witnesses: Any
    betrayals: Any
    allowed_art_styles: str  # Comma-separated list of available art styles
    selected_art_styles: Optional[str] = ""  # User's selected art styles (comma-separated, can be multiple)
    user_requirements: Optional[str] = ""  # Optional seed/requirements from user
    examples: str
    feedback: Optional[str] = ""
    storyline: Optional[str] = ""


class StripperInputSchema(BaseModel):
    art_style: str
    examples: str
    screenplay: Optional[str] = None


class CritiqueSchema(BaseModel):
    storyline: str


class CrewLike:
    outfile: str

    def __init__(self, outfile: str) -> None:
        self.outfile = outfile

    def kickoff(self, inputs: dict, **kwargs):
        print("reading from ", self.outfile)

        data = None
        with open(self.outfile, "r+") as f:
            data = f.read()

        if not data:
            raise ValueError("No results were found")

        return CrewOutput(raw=data)

    async def kickoff_async(self, inputs: dict, **kwargs):
        return await asyncio.to_thread(
            self.kickoff,
            inputs,
            **kwargs,
        )


@CrewBase
class DetectivePlotBuilder:
    agents_config = "plotbuilder/agents.yaml"
    tasks_config = "plotbuilder/tasks.yaml"

    # config: CrewConfig
    # narrative_index_docs: TextFileKnowledgeSource

    namespace: str = "plotbuilder"
    role_name: str = "detective"
    default_outfile: str = "detective_storyline.md"

    # ctx: Optional[DirectorsContext] = None
    # external_memory: Optional[ExternalMemory] = None
    # use_mock: Optional[bool] = False

    def __init__(
        self,
        ctx: DirectorsContext,
        outfile: Optional[str] = None,
        external_memory: Optional[ExternalMemory] = None,
        use_mock: Optional[bool] = False,
    ):
        self.ctx: DirectorsContext = ctx
        self.config: CrewConfig = CrewConfig()
        self.external_memory: Optional[ExternalMemory] = external_memory

        self.outfile: Optional[str] = outfile 
        self.use_mock: bool = bool(use_mock)

        self.narrative_index_docs = knowledge_registry.get(
            "detective_plot",
            [
                "GLOSSARY.md",
                "storywriting/detective/principles.md",
                "storywriting/detective/storytelling-techniques.md",
                "narrative-structures/index.md",
                "art-styles/index.md",
                "art-styles/combinations.md",
                "art-styles/character-guidelines.md"
            ],
        )

        self.config.tools = [
            DirectoryReadTool(directory=str(KNOWLEDGE_DIR / "narrative-structures")),
            DirectoryReadTool(directory=str(KNOWLEDGE_DIR / "art-styles" / "references")),
            FileReadTool(),
        ]

    @classmethod
    def collect(
        cls,
        result: CrewOutput,
        output_model: Optional[Type[T]] = None,
        use_crew_result: bool = True,  # Use clean crew output by default
    ) -> T | str | None:

        if use_crew_result:
            logger.info(f"[DetectivePlotBuilder] Using crew result directly")
            
            if not output_model:
                raw_output = result.raw or ""
                logger.info(f"[DetectivePlotBuilder] Using result.raw (length: {len(raw_output)})")
                return clean_agent_thinking_from_output(raw_output)
            elif output_model and isinstance(result.pydantic, output_model):
                return output_model.model_validate(result.pydantic)

        logger.info(f"[DetectivePlotBuilder] Using task results directly") 
        logger.info(f"[DetectivePlotBuilder] Number of task outputs: {len(result.tasks_output)}")

        for task_output in result.tasks_output:
            if output_model is None:
                logger.info(f"[DetectivePlotBuilder] Returning task raw output (length: {len(task_output.raw)})")
                return clean_agent_thinking_from_output(task_output.raw)

            if isinstance(task_output.pydantic, output_model):
                return output_model.model_validate(task_output.pydantic)

        return None

    @classmethod
    def load_examples(cls):
        try:
            with open(
                Path(__file__).parent / "plotbuilder/examples.yaml",
                "r+",
            ) as f:
                examples_config = yaml.safe_load(f)
                return (
                    examples_config.get("plotbuilder", {})
                    .get("detective", {})
                    .get("examples", "")
                )

        except Exception as e:
            print(e)
            return ""

    def _validate_ctx(self):
        assert self.ctx is not None, "EmptyCtx"

    def get_config(self):
        return self.config

    def bootstrap(self):
        assert self.ctx is not None

        agent = Agent(
            config=self.agents_config[self.namespace][self.role_name],  # type: ignore[index]  # pyright: ignore[reportArgumentType]
            llm=self.ctx.llmstore.load(LLMPlannerIntent),
            tools=self.config.tools,
            verbose=self.ctx.debug,
        )

        task = Task(  # pyright: ignore[reportCallIssue]
            config=self.tasks_config[self.namespace][self.role_name],  # type: ignore[index]  # pyright: ignore[reportArgumentType]
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

        if self.use_mock and self.outfile:
            return CrewLike(self.outfile)

        _ = self.bootstrap()

        return Crew(
            agents=self.config.agents,
            tasks=self.config.tasks,
            verbose=self.ctx.debug,
            # planning=True,
            knowledge_sources=[self.narrative_index_docs],
            external_memory=self.external_memory,
        )


@CrewBase
class PlotCritique:
    agents_config = "plotbuilder/agents.yaml"
    tasks_config = "plotbuilder/tasks.yaml"

    # config: CrewConfig
    # narrative_index_docs: TextFileKnowledgeSource

    role_name: str = "critique"
    default_outfile: str = "critique_storyline.md"

    # ctx: Optional[DirectorsContext] = None
    # external_memory: Optional[ExternalMemory] = None
    # use_mock: Optional[bool] = False

    def __init__(
        self,
        ctx: DirectorsContext,
        outfile: str | None = None,
        external_memory: ExternalMemory | None = None,
        use_mock: bool | None = False,
    ):
        self.ctx: DirectorsContext = ctx
        self.config: CrewConfig = CrewConfig()
        self.external_memory: Optional[ExternalMemory] = external_memory
        self.outfile: Optional[str] = outfile

        self.use_mock: bool = True if use_mock else False

        self.narrative_index_docs = knowledge_registry.get(
            "plot_critique",
            [
                "GLOSSARY.md",
                "storywriting/detective/principles.md",
                "storywriting/detective/storytelling-techniques.md",
                "narrative-structures/index.md",
            ],
        )

        self.config.tools = [
            DirectoryReadTool(directory=str(KNOWLEDGE_DIR / "narrative-structures")),
            FileReadTool(),
        ]

    @classmethod
    def collect(
        cls,
        result: CrewOutput,
        output_model: Optional[Type[T]] = None,
    ) -> T | str | None:

        for task_output in result.tasks_output:
            if not output_model:
                return task_output.raw
            
            if isinstance(task_output.pydantic, output_model):
                return output_model.model_validate(task_output.pydantic)

        return None

    def _validate_ctx(self):
        assert self.ctx is not None, "EmptyCtx"

    def get_config(self):
        return self.config

    def bootstrap(self):
        assert self.ctx is not None

        agent = Agent(
            config=self.agents_config[self.role_name],  # type:ignore[index]  # pyright: ignore[reportArgumentType]
            llm=self.ctx.llmstore.load(LLMCritiqueIntent),
            tools=self.config.tools,
            verbose=self.ctx.debug,
        )

        task = Task(  # pyright: ignore[reportCallIssue]
            config=self.tasks_config[self.role_name],  # type:ignore[index]  # pyright: ignore[reportArgumentType]
            agent=agent,
            output_file=self.outfile,
            markdown=True,
        )

        self.config.agents.append(agent)
        self.config.tasks.append(task)

    def crew(self):
        assert self.ctx is not None

        if self.use_mock and self.outfile:
            return CrewLike(self.outfile)

        self.bootstrap()

        return Crew(
            agents=self.config.agents,
            tasks=self.config.tasks,
            verbose=self.ctx.debug,
            # planning=True,
            knowledge_sources=[self.narrative_index_docs],
            external_memory=self.external_memory,
        )


class ScreenplayWriterSchema(BaseModel):
    storyline: str
    art_style: str
    examples: str
    pages: Optional[int] = 50
    summary: Optional[str] = ""
    words_per_chapter: Optional[int] = 100
    previous_iter_data: str = Field(default="")


@CrewBase
class ScreenplayWriter:
    agents_config = "plotbuilder/agents.yaml"
    tasks_config = "plotbuilder/tasks.yaml"

    config: CrewConfig
    narrative_index_docs: TextFileKnowledgeSource

    ctx: Optional[DirectorsContext] = None
    external_memory: Optional[ExternalMemory] = None
    use_mock: Optional[bool] = False

    role_name: str = "screenplay"
    outfile: str = "screenplay.md"

    def __init__(
        self,
        ctx: DirectorsContext,
        outfile: Optional[str] = None,
        external_memory: Optional[ExternalMemory] = None,
        use_mock: Optional[bool] = False,
    ):
        self.ctx: DirectorsContext = ctx
        self.config = CrewConfig()
        self.external_memory: Optional[ExternalMemory] = external_memory
        self.outfile: Optional[str] = outfile

        self.use_mock = True if use_mock else False

        self.narrative_index_docs = knowledge_registry.get(
            "screenplay",
            [
                "GLOSSARY.md",
                "moviemaking/screenplay-format.md",
                "moviemaking/continuity.md",
                "moviemaking/screen_direction.md",
                "moviemaking/walter_murch_rules.md",
            ],
        )

        self.config.tools = []

    @classmethod
    def collect(
        cls,
        result: CrewOutput,
        output_model: Optional[Type[BaseModel]] = None,
        use_crew_result: bool = True,  # Use clean crew output by default
    ) -> BaseModel | str | None:

        if use_crew_result:
            logger.info(f"[ScreenplayWriter] Using crew result directly")
            
            if not output_model:
                raw_output = result.raw or ""
                logger.info(f"[ScreenplayWriter] Using result.raw (length: {len(raw_output)})")
                return clean_agent_thinking_from_output(raw_output)
            elif output_model and isinstance(result.pydantic, output_model):
                return output_model.model_validate(result.pydantic)

        logger.info(f"[ScreenplayWriter] Using task outputs directly")
        logger.info(f"[ScreenplayWriter] Number of task outputs: {len(result.tasks_output)}")

        for task_output in result.tasks_output:
            if output_model is None:
                return clean_agent_thinking_from_output(task_output.raw)

            if isinstance(task_output.pydantic, output_model):
                return output_model.model_validate(task_output.pydantic)

        return None

    @classmethod
    def load_examples(cls):
        try:
            with open(
                Path(__file__).parent / "plotbuilder/examples.yaml",
                "r+",
            ) as f:
                examples_config = yaml.safe_load(f)
                return examples_config.get(
                    "screenplay",
                    {},
                ).get(
                    "examples",
                    "",
                )

        except Exception as e:
            print(e)
            return ""

    def _validate_ctx(self):
        assert self.ctx is not None, "EmptyCtx"

    def bootstrap(self):
        assert self.ctx is not None

        agent = Agent(
            config=self.agents_config[self.role_name],  # type:ignore[index]
            llm=self.ctx.llmstore.load(LLMPlannerIntent),
            tools=self.config.tools,
            verbose=self.ctx.debug,
        )

        task = Task(
            config=self.tasks_config[self.role_name],  # type:ignore[index],
            agent=agent,
            output_file=self.outfile,
        )

        self.config.agents.append(agent)
        self.config.tasks.append(task)

    def crew(self):
        assert self.ctx is not None, "EmptyCtx"

        if self.use_mock:
            return CrewLike(self.outfile)

        self.bootstrap()

        return Crew(
            agents=self.config.agents,
            tasks=self.config.tasks,
            external_memory=self.external_memory,
            verbose=self.ctx.debug,
        )


class BookWriterSchema(BaseModel):
    storyline: str
    words_per_chapter: Optional[int] = 150
    total_pages: Optional[int] = 50
    art_style: Optional[str] = None
    examples: str = ""
    character_details: list[str] = []
    world_era: str = ""
    previous_iter_data: str = Field(default="")

@CrewBase
class BookWriter:
    agents_config = "plotbuilder/agents.yaml"
    tasks_config = "plotbuilder/tasks.yaml"

    role_name: str = "novelist"
    default_outfile: str = "novel.md"
    max_retries: int = 100

    # ctx: Optional[DirectorsContext] = None
    # external_memory: Optional[ExternalMemory] = None
    # use_mock: Optional[bool] = False

    def __init__(
        self,
        ctx: DirectorsContext,
        outfile: Optional[str] = None,
        external_memory: Optional[ExternalMemory] = None,
        use_mock: Optional[bool] = False,
    ):
        self.ctx: DirectorsContext = ctx
        self.config: CrewConfig = CrewConfig()
        self.external_memory: Optional[ExternalMemory] = external_memory
        self.outfile: Optional[str] = outfile

        self.use_mock: bool = True if use_mock else False

        # Reuse existing knowledge sources
        # "storywriting/detective/principles.md",
        # "storywriting/detective/storytelling-techniques.md",
        # "storywriting/chapter-mapping/linear-novel-mapping.md",
        #  "storywriting/chapter-mapping/non-linear-novel-mapping.md",
        # "storywriting/methods/index.md",

        self.narrative_index_docs = knowledge_registry.get(
            "book_writer",
            [
                "GLOSSARY.md",
                "storywriting/detective/index.md",
                "storywriting/methods/snowflake-method.md",
                "storywriting/chapter-mapping/index.md",
                "narrative-structures/index.md",
            ],
        )

        self.config.tools = [
            MultiDirectoryReadTool(
                directories=[
                    str(KNOWLEDGE_DIR / "narrative-structures"),
                    str(KNOWLEDGE_DIR / "storywriting/detective"),
                    str(KNOWLEDGE_DIR / "storywriting/chapter-mapping"),
                    str(KNOWLEDGE_DIR / "storywriting/methods"),
                ],
            ),
            FileReadTool(),
        ]

    @classmethod
    def collect(
        cls,
        result: CrewOutput,
        output_model: Optional[Type[BaseModel]] = None,
        use_crew_result: bool = True,  # Use clean crew output by default
    ) -> BaseModel | str | None:

        if use_crew_result:
            logger.info(f"[BookWriter] Using crew result directly")
            
            if not output_model:
                raw_output = result.raw or ""
                logger.info(f"[BookWriter] Using result.raw (length: {len(raw_output)})")
                return clean_agent_thinking_from_output(raw_output)
            elif output_model and isinstance(result.pydantic, output_model):
                return output_model.model_validate(result.pydantic)
        
        logger.info(f"[BookWriter] Using task results directly")
        logger.info(f"[BookWriter] Number of task outputs: {len(result.tasks_output)}")

        for task_output in result.tasks_output:
            if output_model is None:
                logger.info(f"[BookWriter] Returning task raw output (length: {len(task_output.raw)})")
                return clean_agent_thinking_from_output(task_output.raw)

            if isinstance(task_output.pydantic, output_model):
                return output_model.model_validate(task_output.pydantic)

        return None

    def bootstrap(self):
        assert self.ctx is not None

        model_config = self.ctx.llmstore.get_model(LLMThinkerIntent)
        logger.info(f"[BookWriter] Using model config: {model_config}")
        assert model_config is not None

        agent = Agent(
            config=self.agents_config[self.role_name],  # type: ignore[index]  # pyright: ignore[reportArgumentType]
            llm=self.ctx.llmstore.load(LLMThinkerIntent),
            tools=self.config.tools,
            max_iter=self.max_retries,
            max_tokens=model_config.max_tokens or 32000,
            verbose=self.ctx.debug,
        )

        task = Task(  # pyright: ignore[reportCallIssue]
            config=self.tasks_config[self.role_name],  # type: ignore[index]  # pyright: ignore[reportArgumentType]
            agent=agent,
            output_file=self.outfile,
            markdown=True,
        )

        self.config.agents.append(agent)
        self.config.tasks.append(task)

    def crew(self):
        assert self.ctx is not None

        if self.use_mock and self.outfile:
            return CrewLike(self.outfile)

        self.bootstrap()

        return Crew(
            agents=self.config.agents,
            tasks=self.config.tasks,
            verbose=self.ctx.debug,
            knowledge_sources=[self.narrative_index_docs],
            external_memory=self.external_memory,
        )


class ChapterBuilderSchema(BaseModel):
    title: str = Field(..., description="title of the chapter, max 1-2 words")
    screenplay: str
    examples: str
    chapter_id: int
    chapter_content: str
    art_style: str
    aspect_ratio: Optional[str] = "4:5"  # or 5:4
    motion_types_list: Optional[str] = None  # Comma-separated list of valid motion_type values
    panel_transitions_list: Optional[str] = None  # Comma-separated list of valid panel_transition_style values

KnowledgeSources: TypeAlias = Union[BaseKnowledgeSource, BaseFileKnowledgeSource]

@CrewBase
class ChapterBuilder:
    agents_config = "plotbuilder/agents.yaml"
    tasks_config = "plotbuilder/tasks.yaml"

    # config: CrewConfig

    role_name: str = "chapterbuilder"
    default_outfile: str = "comic_generator.json"

    # ctx: Optional[DirectorsContext] = None
    # knowledge_sources: List[KnowledgeSources]
    # external_memory: Optional[ExternalMemory] = None
    use_mock: Optional[bool] = False

    def __init__(
        self,
        ctx: DirectorsContext,
        outfile: str | None = None,
        external_memory: ExternalMemory | None = None,
        knowledge_sources: List[KnowledgeSources] | None = None,
        use_mock: bool | None = False,
    ):
        self.ctx: DirectorsContext = ctx
        self.config: CrewConfig = CrewConfig()
        self.external_memory: ExternalMemory | None = external_memory
        self.outfile: str | None = outfile

        self.use_mock: bool = bool(use_mock)
        
        # Use provided knowledge sources or default to GLOSSARY
        _combined_knowledge_sources: List[KnowledgeSources] = [
            knowledge_registry.get("chapter_builder_default", ["GLOSSARY.md"]),
        ]

        if knowledge_sources:
            _combined_knowledge_sources.extend(knowledge_sources)

        self.knowledge_sources = _combined_knowledge_sources

        self.config.tools = [
            MultiDirectoryReadTool(directories=[
                str(KNOWLEDGE_DIR / "storywriting/chapter-mapping"),
                str(KNOWLEDGE_DIR / "moviemaking"),
                str(KNOWLEDGE_DIR / "layout")
            ]),
            FileReadTool(),
        ]

    @classmethod
    def collect(
        cls,
        result: CrewOutput,
        output_model: Optional[Type[T]] = None,
    ) -> T | str | None:
        for task_output in result.tasks_output:
            if not output_model:
                return clean_agent_thinking_from_output(task_output.raw)
            
            if isinstance(task_output.pydantic, output_model):
                return output_model.model_validate(task_output.pydantic)

        return None

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
            config=self.agents_config[self.role_name],  # type:ignore[index]  # pyright: ignore[reportArgumentType]
            llm=self.ctx.llmstore.load(LLMExecutorIntent),
            tools=self.config.tools,
            verbose=self.ctx.debug,
        )

        plotbuilder_task = Task(  # pyright: ignore[reportCallIssue]
            config=self.tasks_config[self.role_name],  # type:ignore[index],  # pyright: ignore[reportArgumentType]
            agent=plotbuilder_agent,
            output_file=self.outfile,
            output_pydantic=ComicBookOutput,  # NEW: Richer model that captures full novel
        )

        self.config.agents.append(plotbuilder_agent)
        self.config.tasks.append(plotbuilder_task)

    def crew(self):
        assert self.ctx is not None, "EmptyCtx"

        if self.use_mock and self.outfile:
            return CrewLike(self.outfile)

        self.bootstrap()

        return Crew(
            agents=self.config.agents,
            tasks=self.config.tasks,
            verbose=self.ctx.debug,
            knowledge_sources=self.knowledge_sources,
            external_memory=self.external_memory,
        )


@CrewBase
class ComicStripStoryBoarding:
    agents_config = "plotbuilder/agents.yaml"
    tasks_config = "plotbuilder/tasks.yaml"

    # config: CrewConfig
    # narrative_index_docs: TextFileKnowledgeSource

    role_name: str = "stripper"
    default_outfile: str = "comic_generator.json"

    # ctx: Optional[DirectorsContext] = None
    # external_memory: Optional[ExternalMemory] = None
    # use_mock: Optional[bool] = False

    def __init__(
        self,
        ctx: DirectorsContext,
        outfile: Optional[str] = None,
        external_memory: Optional[ExternalMemory] = None,
        use_mock: Optional[bool] = False,
    ):
        self.ctx: DirectorsContext = ctx
        self.config: CrewConfig = CrewConfig()
        self.external_memory: Optional[ExternalMemory] = external_memory
        self.outfile: Optional[str] = outfile
        
        self.use_mock: bool = True if use_mock else False

        self.narrative_index_docs = knowledge_registry.get(
            "comic_strip",
            [
                "GLOSSARY.md",
                "layouts/panel_arrangements.md",
                "gemini/image-prompting.md",
                "gemini/video-prompting.md",
            ],
        )

        self.config.tools = [
            MultiDirectoryReadTool(directories=[
                str(KNOWLEDGE_DIR / "moviemaking"),
                str(KNOWLEDGE_DIR / "layout")
            ]),
            FileReadTool(),
        ]

    @classmethod
    def collect(
        cls,
        result: CrewOutput,
        output_model: Optional[Type[T]] = None,
    ) -> T | str | None:

        for task_output in result.tasks_output:
            if not output_model:
                return task_output.raw
            
            if isinstance(task_output.pydantic, output_model):
                return output_model.model_validate(task_output.pydantic)

        return None

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
            config=self.agents_config[self.role_name],  # type:ignore[index]  # pyright: ignore[reportArgumentType]
            llm=self.ctx.llmstore.load(LLMExecutorIntent),
            tools=self.config.tools,
            verbose=self.ctx.debug,
        )

        plotbuilder_task = Task(  # pyright: ignore[reportCallIssue]
            config=self.tasks_config[self.role_name],  # type:ignore[index],  # pyright: ignore[reportArgumentType]
            agent=plotbuilder_agent,
            output_file=self.outfile,
            output_pydantic=ComicBookOutput,  # NEW: Richer model that captures full novel
        )

        self.config.agents.append(plotbuilder_agent)
        self.config.tasks.append(plotbuilder_task)

    def crew(self):
        assert self.ctx is not None, "EmptyCtx"

        if self.use_mock and self.outfile:
            return CrewLike(self.outfile)

        self.bootstrap()

        return Crew(
            agents=self.config.agents,
            tasks=self.config.tasks,
            verbose=self.ctx.debug,
            knowledge_sources=[self.narrative_index_docs],
            external_memory=self.external_memory,
        )



async def main():
    data = None

    with open("novel.md", "r+") as f:
        data = f.read()

    assert data is not None
    assert len(data) > 0

    inputs = {
        "storyline": data,
        "art_style": "Print Comic Noir Style with Halftones",
        "examples": ComicStripStoryBoarding.load_examples()
    }
    ctx = DirectorsContext(
        llmstore=OpenAiHerd,
        debug=True,
    )

    cr = ComicStripStoryBoarding(ctx=ctx, outfile="test.json").crew()
    data = await cr.kickoff_async(inputs=inputs)

    print(data)

if __name__ == "__main__":
    asyncio.run(main())