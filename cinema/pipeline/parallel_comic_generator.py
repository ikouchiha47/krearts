"""
Parallel Comic Generator - Orchestrates chapter-by-chapter comic generation.

This class processes novel chapters in parallel using the existing 
ComicStripStoryBoarding crew, then merges the results in memory.
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


class ParallelComicGenerator:
    """
    Orchestrates parallel chapter-by-chapter comic generation.
    
    Uses the existing ComicStripStoryBoarding crew to process each chapter
    independently, then merges results into a complete ComicBookOutput.
    """
    
    def __init__(
        self,
        ctx: DirectorsContext,
        screenplay: str,
        max_concurrent: int = 3,
        output_base_dir: Optional[str] = None,  # Optional: if provided, saves chapter JSONs here
        use_mock: bool = False,  # If True, use existing chapter JSONs instead of generating
        workflow_id: Optional[str] = None,
        metadata_repo: Optional[ComicMetadataRepository] = None,
        job_repo: Optional["JobRepository"] = None,
    ):
        self.ctx = ctx
        self.screenplay = screenplay
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.output_base_dir = output_base_dir
        self.use_mock = use_mock
        self.workflow_id = workflow_id or ""
        self._metadata_repo: ComicMetadataRepository = (
            metadata_repo or get_comic_metadata_repository()
        )
        if job_repo is None:
            # Import lazily to avoid circular imports at module import time
            from cinema.jobs.storage import get_job_repository

            job_repo = get_job_repository()
        self._job_repo: Optional["JobRepository"] = job_repo
    
    async def generate(self, novel: Novel, art_style: str, aspect_ratio: str = "4:5") -> ComicBookOutput:
        """
        Generate comic book output from a novel by processing chapters in parallel.
        
        Args:
            novel: Parsed novel with chapters
            art_style: Art style for comic generation
            aspect_ratio: Aspect ratio for panels (default: "4:5" portrait)
            
        Returns:
            Complete ComicBookOutput with all chapters
        """
        logger.info(f"Starting parallel comic generation for {len(novel.chapters)} chapters")
        logger.info(f"Max concurrent: {self.semaphore._value}")
        
        # Create base crew instance
        base_crew = ChapterBuilder(
            ctx=self.ctx,
            outfile=None,
            use_mock=self.use_mock,
        )
        
        # Process each chapter with individual error handling
        # This allows saving successful chapters even if others fail
        logger.info(f"Processing {len(novel.chapters)} chapters in parallel with individual error handling...")
        
        async def process_single_chapter(chapter: NovelChapter) -> ComicChapter | Exception:
            try:
                # Prepare inputs for this chapter
                chapter_content = f"# Chapter {chapter.number}: {chapter.title}\n\n{chapter.content}"
                
                # Extract enum values from Pydantic models to inject into prompts
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
                
                inputs = ChapterBuilderSchema(
                    title=chapter.title,
                    screenplay=self.screenplay,
                    examples=ComicStripStoryBoarding.load_examples(),
                    chapter_id=chapter.number,
                    chapter_content=chapter_content,
                    art_style=art_style,
                    aspect_ratio=aspect_ratio,
                    motion_types_list=motion_types,  # For task YAML injection
                    panel_transitions_list=panel_transitions,  # For task YAML injection
                )
                
                # Create isolated crew copy for this chapter
                crew_copy = base_crew.crew().copy()
                raw_result = await crew_copy.kickoff_async(inputs=inputs.model_dump())
                
                # Collect and parse the result
                from cinema.models.comic_output import ComicBookOutput
                chapter_output = ChapterBuilder.collect(raw_result, output_model=ComicBookOutput)
                
                # Save immediately after successful generation
                await self._save_chapter_output(chapter_output, chapter)
                
                # Calculate stats from the first chapter in the output
                comic_chapter = chapter_output.chapters[0] if chapter_output.chapters else None
                if comic_chapter:
                    num_scenes = len(comic_chapter.scenes)
                    num_pages = sum(len(s.pages) for s in comic_chapter.scenes)
                    num_panels = sum(len(p.panels) for s in comic_chapter.scenes for p in s.pages)
                    
                    logger.info(f"✓ Chapter {chapter.number} complete: {num_scenes} scenes, {num_pages} pages, {num_panels} panels")
                
                return comic_chapter
            except Exception as e:
                logger.error(f"✗ Chapter {chapter.number} failed: {e}")
                return e
        
        # Run all chapters in parallel with asyncio.gather
        results = await asyncio.gather(*[process_single_chapter(ch) for ch in novel.chapters])
        
        # Check for errors
        errors = [r for r in results if isinstance(r, Exception)]
        if errors:
            logger.error(f"Encountered {len(errors)} errors during generation:")
            for i, error in enumerate(errors):
                logger.error(f"  Error {i+1}: {error}")
        
        # Filter out errors and get successful results
        successful_results: List[ComicChapter] = []
        for r in results:
            if not isinstance(r, Exception):
                successful_results.append(cast(ComicChapter, r))

        logger.info(f"Successfully generated {len(successful_results)}/{len(novel.chapters)} chapters")
        
        # Merge results into final ComicBookOutput
        comic_output = self._merge_results(novel, successful_results, art_style)
        
        logger.info(f"✓ Comic generation complete:")
        logger.info(f"  Total chapters: {comic_output.total_chapters}")
        logger.info(f"  Total scenes: {comic_output.total_scenes}")
        logger.info(f"  Total pages: {comic_output.total_pages}")
        logger.info(f"  Total panels: {comic_output.total_panels}")
        
        return comic_output
    
    async def _save_chapter_output(self, chapter_output: ComicBookOutput, chapter: NovelChapter) -> None:
        """Save chapter output to database immediately after generation"""
        if self.workflow_id:
            self._metadata_repo.save_chapter(
                self.workflow_id,
                chapter_output.model_dump(),
            )
            logger.info(f"💾 Saved Chapter {chapter.number} to database")
    
    async def _process_chapter(
        self,
        chapter: NovelChapter,
        art_style: str,
        aspect_ratio: str = "4:5"
    ) -> ComicChapter:
        """Process a single chapter using ComicStripStoryBoarding"""
        async with self.semaphore:
            logger.info(f"Processing Chapter {chapter.number}: {chapter.title}")

            job: Optional[Job] = None
            if self.workflow_id and self._job_repo is not None:
                job = Job(
                    id=str(uuid.uuid4()),
                    workflow_id=self.workflow_id,
                    type="book_chapter",
                    status="running",
                    metadata={
                        "chapter_number": chapter.number,
                        "chapter_title": chapter.title,
                        "art_style": art_style,
                    },
                )
                await asyncio.to_thread(self._job_repo.save, job)

            try:
                # Create ComicStripStoryBoarding crew for this chapter
                # Let each crew load its own knowledge to avoid duplicate ID errors
                crew = ChapterBuilder(
                    ctx=self.ctx,
                    outfile=None,
                    use_mock=self.use_mock,  # Use skipper config
                )
                
                # Prepare inputs - pass chapter content directly from memory
                chapter_content = f"# Chapter {chapter.number}: {chapter.title}\n\n{chapter.content}"
                
                inputs = ChapterBuilderSchema(
                    title=chapter.title,
                    screenplay=self.screenplay,
                    examples=ComicStripStoryBoarding.load_examples(),
                    chapter_id=chapter.number,
                    chapter_content=chapter_content,
                    art_style=art_style,
                    aspect_ratio=aspect_ratio,  # Configurable aspect ratio
                )
                
                # Run the crew
                result = await crew.crew().kickoff_async(inputs=inputs.model_dump())
                
                # Collect result
                chapter_output = ComicStripStoryBoarding.collect(
                    result,
                    output_model=ComicBookOutput,
                )
                
                # Extract the first (and should be only) chapter from the result
                if chapter_output and chapter_output.chapters:
                    comic_chapter = chapter_output.chapters[0]

                    # Persist chapter metadata via repository (file/sqlite backend)
                    if self.workflow_id:
                        self._metadata_repo.save_chapter(
                            self.workflow_id,
                            chapter_output.model_dump(),
                        )

                    # Calculate chapter statistics
                    num_scenes = len(comic_chapter.scenes)
                    num_pages = 0
                    num_panels = 0

                    for scene in comic_chapter.scenes:
                        num_pages += len(scene.pages)
                        for page in scene.pages:
                            num_panels += len(page.panels)

                        # Fallback to legacy panels count if no pages
                        if not scene.pages and scene.panels:
                            num_panels += len(scene.panels)

                    logger.info(
                        f"✓ Chapter {chapter.number} complete: "
                        f"{num_scenes} scenes, {num_pages} pages, {num_panels} panels"
                    )

                    if job is not None:
                        job.status = "completed"
                        job.metadata.update(
                            {
                                "scenes": num_scenes,
                                "pages": num_pages,
                                "panels": num_panels,
                            }
                        )
                        await asyncio.to_thread(self._job_repo.save, job)

                    return comic_chapter
                else:
                    logger.warning(f"Chapter {chapter.number} returned empty chapters")
                    # Return empty chapter structure
                    if job is not None:
                        job.status = "failed"
                        job.error = "empty_chapter_output"
                        await asyncio.to_thread(self._job_repo.save, job)
                    return ComicChapter(
                        chapter_number=chapter.number,
                        chapter_title=chapter.title,
                        chapter_summary="",
                        scenes=[],
                        estimated_pages=0,
                    )

            except Exception as e:
                logger.error(f"Error processing Chapter {chapter.number}: {e}")
                if job is not None:
                    job.status = "failed"
                    job.error = str(e)
                    await asyncio.to_thread(self._job_repo.save, job)
                raise
    
    def _merge_results(
        self,
        novel: Novel,
        chapter_results: List[ComicChapter],
        art_style: str
    ) -> ComicBookOutput:
        """Merge individual chapter results into complete ComicBookOutput"""
        
        # Sort chapters by number
        sorted_chapters = sorted(chapter_results, key=lambda c: c.chapter_number)
        
        # Calculate totals from page-based structure
        total_scenes = 0
        total_pages = 0
        total_panels = 0
        
        for chapter in sorted_chapters:
            total_scenes += len(chapter.scenes)
            
            for scene in chapter.scenes:
                # Count pages (new page-based structure)
                total_pages += len(scene.pages)
                
                # Count panels from pages
                for page in scene.pages:
                    total_panels += len(page.panels)
                
                # Also count panels from legacy panels field (for backward compatibility)
                if scene.panels and not scene.pages:
                    total_panels += len(scene.panels)
        
        logger.info(f"Calculated statistics: {total_scenes} scenes, {total_pages} pages, {total_panels} panels")
        
        # Extract characters from first chapter (they should be consistent)
        characters = []
        if sorted_chapters and sorted_chapters[0].scenes:
            # We'll need to extract characters from the novel metadata or first chapter
            # For now, leave empty - this can be enhanced later
            pass
        
        return ComicBookOutput(
            title=novel.title,
            narrative_structure=novel.metadata.get("Narrative Structure", "linear"),
            art_style=art_style,
            short_summary=novel.metadata.get("Short Summary", ""),
            world_context=novel.context,
            characters=characters,  # TODO: Extract from novel or chapters
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
