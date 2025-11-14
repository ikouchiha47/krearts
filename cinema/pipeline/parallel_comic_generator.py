"""
Parallel Comic Generator - Orchestrates chapter-by-chapter comic generation.

This class processes novel chapters in parallel using the existing 
ComicStripStoryBoarding crew, then merges the results in memory.
"""

import asyncio
import logging
from typing import List, Optional, cast

from crewai.knowledge.source.string_knowledge_source import StringKnowledgeSource

from cinema.agents.bookwriter.crew import ChapterBuilder, ChapterBuilderSchema, ComicStripStoryBoarding
from cinema.context import DirectorsContext
from cinema.models.comic_output import ComicBookOutput, ComicChapter
from cinema.models.novel import Novel, NovelChapter

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
        output_base_dir: Optional[str] = None  # Optional: if provided, saves chapter JSONs here
    ):
        self.ctx = ctx
        self.screenplay = screenplay
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.output_base_dir = output_base_dir
        self._screenplay_kb = StringKnowledgeSource(content=self.screenplay)
    
    async def generate(self, novel: Novel, art_style: str) -> ComicBookOutput:
        """
        Generate comic book output from a novel by processing chapters in parallel.
        
        Args:
            novel: Parsed novel with chapters
            art_style: Art style for comic generation
            
        Returns:
            Complete ComicBookOutput with all chapters
        """
        logger.info(f"Starting parallel comic generation for {len(novel.chapters)} chapters")
        logger.info(f"Max concurrent: {self.semaphore._value}")
        
        # Process chapters in parallel - pass chapter content directly
        tasks = [
            self._process_chapter(chapter, art_style)
            for chapter in novel.chapters
        ]
        
        logger.info(f"Processing {len(tasks)} chapters in parallel...")
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
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
    
    async def _process_chapter(
        self,
        chapter: NovelChapter,
        art_style: str
    ) -> ComicChapter:
        """Process a single chapter using ComicStripStoryBoarding"""
        async with self.semaphore:
            logger.info(f"Processing Chapter {chapter.number}: {chapter.title}")
            
            try:
                # Optionally save chapter JSON to output directory
                outfile = None
                if self.output_base_dir:
                    from pathlib import Path
                    output_dir = Path(self.output_base_dir)
                    output_dir.mkdir(parents=True, exist_ok=True)
                    outfile = str(output_dir / f"chapter_{chapter.number:02d}.json")
                
                # Create ComicStripStoryBoarding crew for this chapter
                crew = ChapterBuilder(
                    ctx=self.ctx,
                    outfile=outfile,
                    use_mock=False,
                    knowledge_sources=[self._screenplay_kb],  # NOTE: can be singleton
                )
                
                # Prepare inputs - pass chapter content directly from memory
                chapter_content = f"# Chapter {chapter.number}: {chapter.title}\n\n{chapter.content}"
                
                inputs = ChapterBuilderSchema(
                    screenplay=self.screenplay,
                    examples=ComicStripStoryBoarding.load_examples(),
                    chapter_id=chapter.number,
                    chapter_content=chapter_content,
                    art_style=art_style,
                    aspect_ratio="16:9",  # Default to landscape, can be parameterized later
                )
                
                # Run the crew
                result = await crew.crew().kickoff_async(inputs=inputs.model_dump())
                
                # Collect result
                chapter_output = ComicStripStoryBoarding.collect(
                    result,
                    output_model=ComicBookOutput
                )
                
                # Extract the first (and should be only) chapter from the result
                if chapter_output and chapter_output.chapters:
                    comic_chapter = chapter_output.chapters[0]
                    
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
                    return comic_chapter
                else:
                    logger.warning(f"Chapter {chapter.number} returned empty chapters")
                    # Return empty chapter structure
                    return ComicChapter(
                        chapter_number=chapter.number,
                        chapter_title=chapter.title,
                        chapter_summary="",
                        scenes=[],
                        estimated_pages=0
                    )
                    
            except Exception as e:
                logger.error(f"Error processing Chapter {chapter.number}: {e}")
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
