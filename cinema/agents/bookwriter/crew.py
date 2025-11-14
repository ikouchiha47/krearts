import asyncio
import logging
from pathlib import Path
from typing import Any, List, NewType, Optional, Type, TypeAlias, Union

from crewai.knowledge.source.base_file_knowledge_source import BaseFileKnowledgeSource
from crewai.knowledge.source.base_knowledge_source import BaseKnowledgeSource
import yaml
from crewai import Agent, Crew, CrewOutput, Knowledge, Task
from crewai.knowledge.source.text_file_knowledge_source import TextFileKnowledgeSource
from crewai.knowledge.source.string_knowledge_source import StringKnowledgeSource
from crewai.memory.external.external_memory import ExternalMemory
from crewai.project import CrewBase
from crewai_tools import DirectoryReadTool, FileReadTool
from pydantic import BaseModel

from cinema.agents.bookwriter.tools.multi_directory_read_tool import MultiDirectoryReadTool
from cinema.context import DirectorsContext
from cinema.models.detective_output import DetectiveStoryOutput
from cinema.models.comic_output import ComicBookOutput
from cinema.providers.shared import CrewConfig
from cinema.registry import (
    LLMCritiqueIntent,
    LLMExecutorIntent,
    LLMPlannerIntent,
    LLMThinkerIntent,
    OpenAiHerd,
)

# Note: Character and RelationshipGraph are imported in detective.py
# Removed DetectivePlotBuilderSchema as it's unused and causes Pydantic schema errors

logger = logging.getLogger(__name__)

# Constants
KNOWLEDGE_DIR = Path(__file__).parent.parent.parent.parent / "knowledge"

_skippers = {
    "p": True,  # PlotBuilder
    "c": True,  # Critique
    "w": False,  # ScreenplayWriter/BookWriter
    "s": False,  # ComicStripStoryBoarding/ChapterBuilder 
}


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

    config: CrewConfig
    narrative_index_docs: TextFileKnowledgeSource

    namespace: str = "plotbuilder"
    role_name: str = "detective"
    outfile: str = "detective_storyline.md"

    ctx: Optional[DirectorsContext] = None
    external_memory: Optional[ExternalMemory] = None
    use_mock: Optional[bool] = False

    def __init__(
        self,
        ctx: DirectorsContext,
        outfile: Optional[str] = None,
        external_memory: Optional[ExternalMemory] = None,
        use_mock: Optional[bool] = _skippers["p"],
    ):
        self.ctx = ctx
        self.config = CrewConfig()

        if outfile:
            self.outfile = outfile

        self.use_mock = True if use_mock else False

        self.external_memory = external_memory

        self.narrative_index_docs = knowledge_registry.get(
            "detective_plot",
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
            config=self.agents_config[self.namespace][self.role_name],  # type: ignore[index]
            llm=self.ctx.llmstore.load(LLMPlannerIntent),
            tools=self.config.tools,
            verbose=self.ctx.debug,
        )

        task = Task(
            config=self.tasks_config[self.namespace][self.role_name],  # type: ignore[index]
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

        if self.use_mock:
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


@CrewBase
class PlotCritique:
    agents_config = "plotbuilder/agents.yaml"
    tasks_config = "plotbuilder/tasks.yaml"

    config: CrewConfig
    narrative_index_docs: TextFileKnowledgeSource

    role_name: str = "critique"
    outfile: str = "critique_storyline.md"

    ctx: Optional[DirectorsContext] = None
    external_memory: Optional[ExternalMemory] = None
    use_mock: Optional[bool] = False

    def __init__(
        self,
        ctx: DirectorsContext,
        outfile: Optional[str] = None,
        external_memory: Optional[ExternalMemory] = None,
        use_mock: Optional[bool] = _skippers["c"],
    ):
        self.ctx = ctx
        self.config = CrewConfig()
        self.external_memory = external_memory

        if outfile:
            self.outfile = outfile

        self.use_mock = True if use_mock else False

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
            output_file=self.outfile,
            markdown=True,
        )

        self.config.agents.append(agent)
        self.config.tasks.append(task)

    def crew(self):
        assert self.ctx is not None

        if self.use_mock:
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


@CrewBase
class ScreenplayWriter:
    agents_config = "plotbuilder/agents.yaml"
    tasks_config = "plotbuilder/tasks.yaml"

    config: CrewConfig
    narrative_index_docs: TextFileKnowledgeSource

    ctx: Optional[DirectorsContext] = None
    external_memory: Optional[ExternalMemory] = None
    use_mock: Optional[bool] = _skippers["w"]

    role_name: str = "screenplay"
    outfile: str = "screenplay.md"

    def __init__(
        self,
        ctx: DirectorsContext,
        outfile: Optional[str] = None,
        external_memory: Optional[ExternalMemory] = None,
        use_mock: Optional[bool] = _skippers["w"],
    ):
        self.ctx = ctx
        self.config = CrewConfig()
        self.external_memory = external_memory

        if outfile:
            self.outfile = outfile

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
    words_per_chapter: Optional[int] = 300
    art_style: Optional[str] = None

@CrewBase
class BookWriter:
    agents_config = "plotbuilder/agents.yaml"
    tasks_config = "plotbuilder/tasks.yaml"

    role_name: str = "novelist"
    outfile: str = "novel.md"

    ctx: Optional[DirectorsContext] = None
    external_memory: Optional[ExternalMemory] = None
    use_mock: Optional[bool] = _skippers["w"]

    def __init__(
        self,
        ctx: DirectorsContext,
        outfile: Optional[str] = None,
        external_memory: Optional[ExternalMemory] = None,
        use_mock: Optional[bool] = _skippers["w"],
    ):
        self.ctx = ctx
        self.config = CrewConfig()
        self.external_memory = external_memory

        if outfile:
            self.outfile = outfile

        self.use_mock = True if use_mock else False

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
    ) -> BaseModel | str | None:

        if not output_model:
            return result.raw

        return output_model.model_validate(result.pydantic)

    def bootstrap(self):
        assert self.ctx is not None

        agent = Agent(
            config=self.agents_config[self.role_name],  # type: ignore[index]
            llm=self.ctx.llmstore.load(LLMThinkerIntent),
            tools=self.config.tools,
            max_iter=10,
            verbose=self.ctx.debug,
        )

        task = Task(
            config=self.tasks_config[self.role_name],  # type: ignore[index]
            agent=agent,
            output_file=self.outfile,
            markdown=True,
        )

        self.config.agents.append(agent)
        self.config.tasks.append(task)

    def crew(self):
        assert self.ctx is not None

        if self.use_mock:
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
    screenplay: str
    examples: str
    chapter_id: int
    chapter_content: str
    art_style: str
    aspect_ratio: Optional[str] = "16:9"  # Default to landscape

KnowledgeSources: TypeAlias = Union[BaseKnowledgeSource, BaseFileKnowledgeSource]
@CrewBase
class ChapterBuilder:
    agents_config = "plotbuilder/agents.yaml"
    tasks_config = "plotbuilder/tasks.yaml"

    config: CrewConfig

    role_name: str = "chapterbuilder"
    outfile: str = "comic_generator.json"

    ctx: Optional[DirectorsContext] = None
    knowledge_sources: List[KnowledgeSources]
    external_memory: Optional[ExternalMemory] = None
    use_mock: Optional[bool] = True

    def __init__(
        self,
        ctx: DirectorsContext,
        outfile: Optional[str] = None,
        external_memory: Optional[ExternalMemory] = None,
        knowledge_sources: Optional[List[KnowledgeSources]] = None,
        use_mock: Optional[bool] = _skippers["s"],
    ):
        self.ctx = ctx
        self.config = CrewConfig()
        self.external_memory = external_memory

        if outfile:
            self.outfile = outfile

        self.use_mock = True if use_mock else False
        
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
            output_pydantic=ComicBookOutput,  # NEW: Richer model that captures full novel
        )

        self.config.agents.append(plotbuilder_agent)
        self.config.tasks.append(plotbuilder_task)

    def crew(self):
        assert self.ctx is not None, "EmptyCtx"

        if self.use_mock:
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

    config: CrewConfig
    narrative_index_docs: TextFileKnowledgeSource

    role_name: str = "stripper"
    outfile: str = "comic_generator.json"

    ctx: Optional[DirectorsContext] = None
    external_memory: Optional[ExternalMemory] = None
    use_mock: Optional[bool] = True

    def __init__(
        self,
        ctx: DirectorsContext,
        outfile: Optional[str] = None,
        external_memory: Optional[ExternalMemory] = None,
        use_mock: Optional[bool] = _skippers["s"],
    ):
        self.ctx = ctx
        self.config = CrewConfig()
        self.external_memory = external_memory

        if outfile:
            self.outfile = outfile

        self.use_mock = True if use_mock else False

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
            output_pydantic=ComicBookOutput,  # NEW: Richer model that captures full novel
        )

        self.config.agents.append(plotbuilder_agent)
        self.config.tasks.append(plotbuilder_task)

    def crew(self):
        assert self.ctx is not None, "EmptyCtx"

        if self.use_mock:
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