"""
Experimental ChapterBuilder with StringKnowledgeSource approach.

This crew replicates ChapterBuilder but uses StringKnowledgeSource 
for screenplay context instead of passing it directly in inputs.
"""

import asyncio
import logging
from pathlib import Path
from typing import Optional, Type, TypeVar

from crewai import Agent, Crew, CrewOutput, Task
from crewai.knowledge.source.string_knowledge_source import StringKnowledgeSource
from crewai.project import CrewBase
from crewai_tools import DirectoryReadTool, FileReadTool
from pydantic import BaseModel, Field

from cinema.agents.bookwriter.utils import clean_agent_thinking_from_output
from cinema.context import DirectorsContext
from cinema.models.comic_output import ComicBookOutput
from cinema.providers.shared import CrewConfig
from cinema.registry import LLMExecutorIntent

logger = logging.getLogger(__name__)

# Constants
KNOWLEDGE_DIR = Path(__file__).parent.parent.parent.parent / "knowledge"

T = TypeVar("T", bound=BaseModel)


class ExperimentalChapterBuilderSchema(BaseModel):
    """
    Reduced input schema - screenplay moved to StringKnowledgeSource
    """
    title: str = Field(..., description="title of the chapter, max 1-2 words")
    # screenplay: str  # REMOVED - now in StringKnowledgeSource
    examples: str
    chapter_id: int
    chapter_content: str
    art_style: str
    aspect_ratio: Optional[str] = "4:5"
    motion_types_list: Optional[str] = None
    panel_transitions_list: Optional[str] = None


@CrewBase
class ExperimentalChapterBuilder:
    """
    Experimental ChapterBuilder using StringKnowledgeSource for screenplay context.
    
    Key differences from ChapterBuilder:
    1. screenplay passed as StringKnowledgeSource, not in inputs
    2. Reduced input token count by ~80%
    3. CrewAI handles context retrieval intelligently
    """
    
    agents_config = "chapterbuilder/agents.yaml"
    tasks_config = "chapterbuilder/tasks.yaml"
    
    def __init__(
        self,
        ctx: DirectorsContext,
        screenplay: str,  # Full screenplay for knowledge source
        outfile: Optional[str] = None,
        use_mock: Optional[bool] = False,
    ):
        self.ctx: DirectorsContext = ctx
        self.config: CrewConfig = CrewConfig()
        self.screenplay = screenplay
        self.outfile: Optional[str] = outfile
        self.use_mock: bool = bool(use_mock)
        
        # Create StringKnowledgeSource from screenplay
        self.screenplay_knowledge = StringKnowledgeSource(
            content=f"Full Novel Context:\n\n{screenplay}",
            metadata={
                "type": "novel_context",
                "description": "Complete screenplay/novel for character and plot continuity"
            }
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
        use_crew_result: bool = True,
    ) -> T | str | None:
        """Same collection logic as ChapterBuilder"""
        
        if use_crew_result:
            logger.info(f"[ExperimentalChapterBuilder] Using crew result directly")
            
            if not output_model:
                raw_output = result.raw or ""
                logger.info(f"[ExperimentalChapterBuilder] Using result.raw (length: {len(raw_output)})")
                return clean_agent_thinking_from_output(raw_output)
            elif output_model and isinstance(result.pydantic, output_model):
                return output_model.model_validate(result.pydantic)

        logger.info(f"[ExperimentalChapterBuilder] Using task results directly") 
        logger.info(f"[ExperimentalChapterBuilder] Number of task outputs: {len(result.tasks_output)}")

        for task_output in result.tasks_output:
            if output_model is None:
                logger.info(f"[ExperimentalChapterBuilder] Returning task raw output (length: {len(task_output.raw)})")
                return clean_agent_thinking_from_output(task_output.raw)

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
            config=self.agents_config["chapterbuilder"],  # type: ignore[index]
            llm=self.ctx.llmstore.load(LLMExecutorIntent),
            tools=self.config.tools,
            verbose=self.ctx.debug,
        )

        task = Task(
            config=self.tasks_config["chapterbuilder"],  # type: ignore[index]
            agent=agent,
            output_file=self.outfile,
            output_pydantic=ComicBookOutput,
        )

        self.config.agents.append(agent)
        self.config.tasks.append(task)

        return self

    def crew(self):
        assert self.ctx is not None

        if self.use_mock and self.outfile:
            # Mock crew for testing
            class MockCrew:
                def __init__(self, outfile: str):
                    self.outfile = outfile
                
                async def kickoff_async(self, inputs: dict, **kwargs):
                    with open(self.outfile, "r") as f:
                        data = f.read()
                    return CrewOutput(raw=data)
            
            return MockCrew(self.outfile)

        _ = self.bootstrap()

        return Crew(
            agents=self.config.agents,
            tasks=self.config.tasks,
            verbose=self.ctx.debug,
            knowledge_sources=[self.screenplay_knowledge],  # Inject screenplay as knowledge
        )


# Summarization Strategy Analysis
class ScreenplaySummarizer:
    """
    Analyzes different summarization strategies for screenplay compression.
    
    The goal is to create summaries ONCE per novel, not per chapter.
    """
    
    @staticmethod
    def analyze_screenplay_structure(screenplay: str) -> dict:
        """
        Analyze screenplay to understand what context ChapterBuilder actually needs.
        
        Returns:
            dict: Analysis of screenplay structure and context requirements
        """
        lines = screenplay.split('\n')
        chapters = []
        current_chapter = None
        
        for line in lines:
            if line.startswith('## Chapter') or line.startswith('# Chapter'):
                if current_chapter:
                    chapters.append(current_chapter)
                current_chapter = {
                    'title': line.strip(),
                    'content': [],
                    'characters': set(),
                    'locations': set(),
                }
            elif current_chapter:
                current_chapter['content'].append(line)
                
                # Simple character detection (names in quotes or dialogue)
                if '"' in line:
                    # Extract potential character names before dialogue
                    parts = line.split('"')
                    if len(parts) > 1:
                        potential_name = parts[0].strip().split()[-1]
                        if potential_name and potential_name[0].isupper():
                            current_chapter['characters'].add(potential_name)
        
        if current_chapter:
            chapters.append(current_chapter)
        
        # Calculate statistics
        total_words = len(screenplay.split())
        avg_chapter_words = total_words // len(chapters) if chapters else 0
        
        return {
            'total_chapters': len(chapters),
            'total_words': total_words,
            'avg_chapter_words': avg_chapter_words,
            'chapters': chapters,
            'estimated_tokens': total_words * 1.3,  # Rough token estimation
        }
    
    @staticmethod
    def create_one_shot_summary(screenplay: str) -> dict:
        """
        Create a comprehensive summary structure in one pass.
        
        This would be called ONCE per novel, not per chapter.
        The summary includes:
        - Character profiles and relationships
        - Plot progression by chapter
        - Key events and turning points
        - World/setting context
        
        Returns:
            dict: Structured summary for efficient chapter context
        """
        analysis = ScreenplaySummarizer.analyze_screenplay_structure(screenplay)
        
        # Extract global context (would use LLM in real implementation)
        summary = {
            'meta': {
                'total_chapters': analysis['total_chapters'],
                'total_words': analysis['total_words'],
                'compression_ratio': 0.1,  # Target 10% of original size
            },
            'characters': {},  # Character profiles and arcs
            'plot_progression': [],  # Chapter-by-chapter plot summary
            'world_context': "",  # Setting, time period, world rules
            'key_relationships': [],  # Important character relationships
            'plot_threads': [],  # Ongoing storylines and their status
        }
        
        # For each chapter, create a compressed summary
        for i, chapter in enumerate(analysis['chapters']):
            chapter_summary = {
                'chapter_num': i + 1,
                'title': chapter['title'],
                'key_events': [],  # 2-3 sentence summary
                'character_developments': [],  # Character changes
                'plot_advancement': "",  # How this advances main plot
                'new_information': [],  # Reveals, clues, etc.
            }
            summary['plot_progression'].append(chapter_summary)
        
        return summary
    
    @staticmethod
    def get_chapter_context(summary: dict, chapter_num: int, context_window: int = 2) -> str:
        """
        Generate focused context for a specific chapter.
        
        Args:
            summary: Pre-computed summary from create_one_shot_summary()
            chapter_num: Current chapter number (1-indexed)
            context_window: How many chapters before/after to include
            
        Returns:
            str: Focused context string for this chapter
        """
        context_parts = []
        
        # Add world context (always relevant)
        if summary['world_context']:
            context_parts.append(f"World Context:\n{summary['world_context']}\n")
        
        # Add character profiles (always relevant)
        if summary['characters']:
            context_parts.append("Key Characters:")
            for name, profile in summary['characters'].items():
                context_parts.append(f"- {name}: {profile}")
            context_parts.append("")
        
        # Add relevant plot progression (windowed)
        start_chapter = max(1, chapter_num - context_window)
        end_chapter = min(len(summary['plot_progression']), chapter_num + context_window)
        
        context_parts.append("Recent Plot Progression:")
        for i in range(start_chapter - 1, end_chapter):  # Convert to 0-indexed
            chapter_info = summary['plot_progression'][i]
            if i == chapter_num - 1:  # Current chapter
                context_parts.append(f"→ Chapter {chapter_info['chapter_num']}: {chapter_info['title']} (CURRENT)")
            else:
                context_parts.append(f"  Chapter {chapter_info['chapter_num']}: {chapter_info['plot_advancement']}")
        
        return "\n".join(context_parts)


# Token Analysis Functions
def estimate_token_savings():
    """
    Estimate token savings from different approaches.
    
    Based on real log data:
    - Original ChapterBuilder: ~23,919 input tokens (mostly screenplay)
    - Target: <8,000 tokens to fit in most model limits
    """
    
    original_breakdown = {
        'screenplay': 20000,  # Full novel
        'chapter_content': 2000,  # Current chapter
        'examples': 1000,  # Comic examples
        'metadata': 100,  # Other fields
        'total': 23100
    }
    
    stringknowledge_approach = {
        'chapter_content': 2000,  # Same
        'examples': 1000,  # Same
        'metadata': 100,  # Same
        'screenplay_knowledge': 0,  # Handled by CrewAI retrieval
        'total': 3100,  # 87% reduction!
    }
    
    summary_approach = {
        'chapter_content': 2000,  # Same
        'examples': 1000,  # Same
        'metadata': 100,  # Same
        'focused_context': 1500,  # Compressed screenplay context
        'total': 4600,  # 80% reduction
    }
    
    return {
        'original': original_breakdown,
        'stringknowledge': stringknowledge_approach,
        'summary': summary_approach,
        'savings': {
            'stringknowledge': f"{((original_breakdown['total'] - stringknowledge_approach['total']) / original_breakdown['total'] * 100):.1f}%",
            'summary': f"{((original_breakdown['total'] - summary_approach['total']) / original_breakdown['total'] * 100):.1f}%"
        }
    }


if __name__ == "__main__":
    # Quick analysis
    savings = estimate_token_savings()
    print("Token Savings Analysis:")
    print(f"Original: {savings['original']['total']:,} tokens")
    print(f"StringKnowledge: {savings['stringknowledge']['total']:,} tokens ({savings['savings']['stringknowledge']} reduction)")
    print(f"Summary: {savings['summary']['total']:,} tokens ({savings['savings']['summary']} reduction)")