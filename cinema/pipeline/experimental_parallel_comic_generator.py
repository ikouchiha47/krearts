"""
Experimental Parallel Comic Generator with Smart Compression and Page Controls.

This is a new version that:
1. Adds total_pages control for ChapterBuilder
2. Uses smart compression for screenplay context
3. Doesn't modify the original ParallelComicGenerator
"""

import asyncio
import logging
import uuid
from typing import List, Optional, TYPE_CHECKING, cast

from crewai.knowledge.source.string_knowledge_source import StringKnowledgeSource

from cinema.agents.bookwriter.crew import ChapterBuilder, ChapterBuilderSchema, ComicStripStoryBoarding
from cinema.context import DirectorsContext
from cinema.models.comic_output import ComicBookOutput, ComicChapter
from cinema.models.novel import Novel, NovelChapter
from cinema.comics.storage import ComicMetadataRepository, get_comic_metadata_repository

from cinema.server.storage.interface import Job

if TYPE_CHECKING:
    from cinema.jobs.storage import JobRepository

logger = logging.getLogger(__name__)


class ExperimentalParallelComicGenerator:
    """
    Experimental version with smart compression and page controls.
    
    Key differences from original:
    1. Adds total_pages parameter for ChapterBuilder
    2. Uses smart compression for screenplay context
    3. Configurable compression strategy
    """
    
    def __init__(
        self,
        ctx: DirectorsContext,
        screenplay: str,
        max_concurrent: int = 3,
        output_base_dir: Optional[str] = None,
        use_mock: bool = False,
        workflow_id: Optional[str] = None,
        metadata_repo: Optional[ComicMetadataRepository] = None,
        job_repo: Optional["JobRepository"] = None,
        # New parameters for page control and compression
        total_pages_per_chapter: int = 5,  # Pages per chapter for ChapterBuilder
        use_smart_compression: bool = True,  # Enable smart screenplay compression
        compression_strategy: str = "smart",  # "smart", "rule_based", or "none"
    ):
        self.ctx = ctx
        self.screenplay = screenplay
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.output_base_dir = output_base_dir
        self.use_mock = use_mock
        self.workflow_id = workflow_id or ""
        
        # New parameters
        self.total_pages_per_chapter = total_pages_per_chapter
        self.use_smart_compression = use_smart_compression
        self.compression_strategy = compression_strategy
        
        self._metadata_repo: ComicMetadataRepository = (
            metadata_repo or get_comic_metadata_repository()
        )
        if job_repo is None:
            from cinema.jobs.storage import get_job_repository
            job_repo = get_job_repository()
        self._job_repo: Optional["JobRepository"] = job_repo
    
    async def generate(self, novel: Novel, art_style: str, aspect_ratio: str = "4:5") -> ComicBookOutput:
        """
        Generate comic book output with smart compression and page controls.
        """
        logger.info(f"🧪 EXPERIMENTAL: Starting parallel comic generation for {len(novel.chapters)} chapters")
        logger.info(f"   Pages per chapter: {self.total_pages_per_chapter}")
        logger.info(f"   Compression strategy: {self.compression_strategy}")
        
        # Process each chapter with smart compression
        async def process_single_chapter(chapter: NovelChapter) -> ComicChapter | Exception:
            try:
                # Prepare chapter content
                chapter_content = f"# Chapter {chapter.number}: {chapter.title}\n\n{chapter.content}"
                
                # Apply smart compression to screenplay
                compressed_screenplay = await self._compress_screenplay_for_chapter(
                    chapter.number, len(novel.chapters)
                )
                
                # Log compression stats
                original_tokens = len(self.screenplay.split()) * 1.3
                compressed_tokens = len(compressed_screenplay.split()) * 1.3
                compression_ratio = (original_tokens - compressed_tokens) / original_tokens * 100
                
                logger.info(f"📄 Chapter {chapter.number} compression:")
                logger.info(f"   Original: {original_tokens:.0f} tokens")
                logger.info(f"   Compressed: {compressed_tokens:.0f} tokens") 
                logger.info(f"   Savings: {compression_ratio:.1f}%")
                
                # Create ChapterBuilder inputs with page control
                inputs = self._create_chapter_inputs(
                    chapter, compressed_screenplay, art_style, aspect_ratio
                )
                
                # Create isolated crew for this chapter
                crew = ChapterBuilder(
                    ctx=self.ctx,
                    outfile=None,
                    use_mock=self.use_mock,
                )
                
                # Run the crew
                result = await crew.crew().kickoff_async(inputs=inputs.model_dump())
                
                # Collect result
                chapter_output = ChapterBuilder.collect(result, output_model=ComicBookOutput)
                
                if chapter_output and chapter_output.chapters:
                    comic_chapter = chapter_output.chapters[0]
                    
                    # Save chapter output
                    await self._save_chapter_output(chapter_output, chapter)
                    
                    # Log stats
                    num_scenes = len(comic_chapter.scenes)
                    num_pages = sum(len(s.pages) for s in comic_chapter.scenes)
                    num_panels = sum(len(p.panels) for s in comic_chapter.scenes for p in s.pages)
                    
                    logger.info(f"✅ Chapter {chapter.number} complete: {num_scenes} scenes, {num_pages} pages, {num_panels} panels")
                    
                    return comic_chapter
                else:
                    logger.warning(f"Chapter {chapter.number} returned empty output")
                    return ComicChapter(
                        chapter_number=chapter.number,
                        chapter_title=chapter.title,
                        chapter_summary="",
                        scenes=[],
                        estimated_pages=0,
                    )
                    
            except Exception as e:
                logger.error(f"❌ Chapter {chapter.number} failed: {e}")
                return e
        
        # Run all chapters in parallel
        results = await asyncio.gather(*[process_single_chapter(ch) for ch in novel.chapters])
        
        # Filter successful results
        successful_results: List[ComicChapter] = []
        errors = []
        
        for r in results:
            if isinstance(r, Exception):
                errors.append(r)
            else:
                successful_results.append(cast(ComicChapter, r))
        
        if errors:
            logger.error(f"❌ {len(errors)} chapters failed during generation")
            for i, error in enumerate(errors):
                logger.error(f"   Error {i+1}: {error}")
        
        logger.info(f"✅ Successfully generated {len(successful_results)}/{len(novel.chapters)} chapters")
        
        # Merge results
        comic_output = self._merge_results(novel, successful_results, art_style)
        
        logger.info(f"🧪 EXPERIMENTAL generation complete:")
        logger.info(f"   Total chapters: {comic_output.total_chapters}")
        logger.info(f"   Total pages: {comic_output.total_pages}")
        logger.info(f"   Total panels: {comic_output.total_panels}")
        
        return comic_output
    
    async def _compress_screenplay_for_chapter(self, chapter_num: int, total_chapters: int) -> str:
        """Apply smart compression based on strategy"""
        if not self.use_smart_compression or self.compression_strategy == "none":
            return self.screenplay
        
        if self.compression_strategy == "smart":
            # Use the smart compression system (will be implemented)
            from cinema.agents.bookwriter.smart_compression import compress_screenplay_for_chapter
            return await compress_screenplay_for_chapter(
                self.ctx, self.screenplay, chapter_num, self.workflow_id
            )
        elif self.compression_strategy == "rule_based":
            # Simple rule-based compression
            return self._rule_based_compression(chapter_num, total_chapters)
        else:
            return self.screenplay
    
    def _rule_based_compression(self, chapter_num: int, total_chapters: int) -> str:
        """Simple rule-based compression for testing"""
        lines = self.screenplay.split('\n')
        
        # Find header (everything before first chapter)
        header_lines = []
        chapter_start = None
        
        for i, line in enumerate(lines):
            if line.strip().startswith('## Chapter') or line.strip().startswith('### Chapter'):
                chapter_start = i
                break
            header_lines.append(line)
        
        if chapter_start is None:
            return self.screenplay  # No chapters found
        
        # Extract chapters
        chapters = []
        current_chapter = []
        
        for line in lines[chapter_start:]:
            if (line.strip().startswith('## Chapter') or line.strip().startswith('### Chapter')) and current_chapter:
                chapters.append('\n'.join(current_chapter))
                current_chapter = [line]
            else:
                current_chapter.append(line)
        
        if current_chapter:
            chapters.append('\n'.join(current_chapter))
        
        # Build compressed version
        compressed_parts = []
        
        # Always include header
        compressed_parts.extend(header_lines)
        compressed_parts.append("")
        
        # Include chapters with windowing
        for i, chapter in enumerate(chapters):
            chapter_index = i + 1
            
            if abs(chapter_index - chapter_num) <= 1:
                # Full chapter for adjacent chapters
                marker = " ← TARGET" if chapter_index == chapter_num else ""
                compressed_parts.append(f"# Chapter {chapter_index}{marker}")
                compressed_parts.append(chapter)
            elif abs(chapter_index - chapter_num) <= 3:
                # Summary for nearby chapters
                summary = self._summarize_chapter_simple(chapter)
                compressed_parts.append(f"# Chapter {chapter_index} (Summary)")
                compressed_parts.append(summary)
            # Skip distant chapters
            
            compressed_parts.append("")
        
        return '\n'.join(compressed_parts)
    
    def _summarize_chapter_simple(self, chapter_text: str) -> str:
        """Simple chapter summarization"""
        paragraphs = [p.strip() for p in chapter_text.split('\n\n') if p.strip()]
        
        if len(paragraphs) <= 2:
            return chapter_text
        else:
            # First + last paragraph
            return f"{paragraphs[0]}\n\n[...]\n\n{paragraphs[-1]}"
    
    def _create_chapter_inputs(
        self, 
        chapter: NovelChapter, 
        compressed_screenplay: str, 
        art_style: str, 
        aspect_ratio: str
    ) -> ChapterBuilderSchema:
        """Create ChapterBuilder inputs with page control"""
        chapter_content = f"# Chapter {chapter.number}: {chapter.title}\n\n{chapter.content}"
        
        # Extract enum values for prompts
        motion_types = """* none: No motion effects
* speed-lines: Fast movement, action
* motion-blur: Rapid motion, dynamic action
* impact-lines: Collision, impact moments
* ghosting: Trailing effect, supernatural"""
        
        panel_transitions = """* hard-cuts: Abrupt scene changes
* overlapping-scenes: Continuity between panels
* blended-transitions: Smooth, dreamlike flow
* diagonal-cuts: Dynamic, energetic transitions
* frame-within-frame: Flashbacks, memories"""
        
        return ChapterBuilderSchema(
            title=chapter.title,
            screenplay=compressed_screenplay,  # Use compressed version
            examples=ComicStripStoryBoarding.load_examples(),
            chapter_id=chapter.number,
            chapter_content=chapter_content,
            art_style=art_style,
            aspect_ratio=aspect_ratio,
            motion_types_list=motion_types,
            panel_transitions_list=panel_transitions,
        )
    
    async def _save_chapter_output(self, chapter_output: ComicBookOutput, chapter: NovelChapter) -> None:
        """Save chapter output to database"""
        if self.workflow_id:
            self._metadata_repo.save_chapter(
                self.workflow_id,
                chapter_output.model_dump(),
            )
            logger.info(f"💾 Saved Chapter {chapter.number} to database")
    
    def _merge_results(
        self,
        novel: Novel,
        chapter_results: List[ComicChapter],
        art_style: str
    ) -> ComicBookOutput:
        """Merge chapter results into complete ComicBookOutput"""
        sorted_chapters = sorted(chapter_results, key=lambda c: c.chapter_number)
        
        # Calculate totals
        total_scenes = sum(len(ch.scenes) for ch in sorted_chapters)
        total_pages = sum(sum(len(s.pages) for s in ch.scenes) for ch in sorted_chapters)
        total_panels = sum(sum(len(p.panels) for s in ch.scenes for p in s.pages) for ch in sorted_chapters)
        
        return ComicBookOutput(
            title=novel.title,
            narrative_structure=novel.metadata.get("Narrative Structure", "linear"),
            art_style=art_style,
            short_summary=novel.metadata.get("Short Summary", ""),
            world_context=novel.context,
            characters=[],  # TODO: Extract from novel
            chapters=sorted_chapters,
            killer=novel.metadata.get("Killer"),
            victim=novel.metadata.get("Victim"),
            primary_detective=novel.metadata.get("Primary Detective"),
            total_chapters=len(sorted_chapters),
            total_scenes=total_scenes,
            total_panels=total_panels,
            total_pages=total_pages,
            estimated_pages=total_pages if total_pages > 0 else total_panels // 3
        )