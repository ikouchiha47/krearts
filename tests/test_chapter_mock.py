"""
Test ChapterBuilder with use_mock to load existing chapter JSON files.

Usage:
    python -m cinema.cmd.examples.test_chapter_mock
"""

import asyncio
import json
import logging

from dotenv import load_dotenv

from cinema.agents.bookwriter.crew import ChapterBuilder, ChapterBuilderSchema, ComicStripStoryBoarding
from cinema.context import DirectorsContext
from cinema.registry import OpenAiHerd
from cinema.models.comic_output import ComicBookOutput

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def test_mock_chapter():
    """Test loading a chapter from existing JSON file using use_mock=True"""
    
    # Path to existing chapter JSON
    chapter_json = "output/detective_ce8f9a4a/chapter_01.json"
    
    logger.info("=" * 80)
    logger.info("Testing ChapterBuilder with use_mock=True")
    logger.info(f"Loading from: {chapter_json}")
    logger.info("=" * 80)
    
    # Create context
    ctx = DirectorsContext(
        llmstore=OpenAiHerd,
        debug=True
    )
    
    # Create ChapterBuilder with use_mock=True
    crew = ChapterBuilder(
        ctx=ctx,
        outfile=chapter_json,
        use_mock=True,  # This will load from file instead of running the crew
    )
    
    # Prepare dummy inputs (won't be used since we're mocking)
    inputs = ChapterBuilderSchema(
        screenplay="dummy",
        examples="dummy",
        chapter_id=1,
        chapter_content="dummy",
        art_style="Print Comic Noir Style"
    )
    
    logger.info("Running crew.kickoff_async() with use_mock=True...")
    result = await crew.crew().kickoff_async(inputs=inputs.model_dump())
    
    logger.info("✓ Result received from mock")
    logger.info(f"Result type: {type(result)}")
    logger.info(f"Result has raw: {hasattr(result, 'raw')}")
    
    # Parse the raw JSON directly since mock returns raw text
    chapter_output = json.loads(result.raw)
    chapter_output = ComicBookOutput.model_validate(chapter_output)
    
    logger.info("=" * 80)
    logger.info("✓ Successfully loaded chapter from JSON")
    logger.info(f"Title: {chapter_output.title}")
    logger.info(f"Chapters: {len(chapter_output.chapters)}")
    
    if chapter_output.chapters:
        chapter = chapter_output.chapters[0]
        logger.info(f"Chapter {chapter.chapter_number}: {chapter.chapter_title}")
        logger.info(f"  Scenes: {len(chapter.scenes)}")
        
        total_pages = sum(len(scene.pages) for scene in chapter.scenes)
        total_panels = sum(
            len(panel) 
            for scene in chapter.scenes 
            for page in scene.pages 
            for panel in [page.panels]
        )
        
        logger.info(f"  Pages: {total_pages}")
        logger.info(f"  Panels: {total_panels}")
    
    logger.info("=" * 80)
    logger.info("🎉 Mock test successful!")
    
    return chapter_output


if __name__ == "__main__":
    asyncio.run(test_mock_chapter())
