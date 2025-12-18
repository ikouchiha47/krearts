"""
Smart Screenplay Compression using LLMDirect for one-shot summarization.

This system:
1. Uses LLMDirect for fast, single-shot summarization (no CrewAI overhead)
2. Implements your windowing strategy for chapter context
3. Caches summaries to avoid re-summarization
4. Can be tested on existing novels from database
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

from pydantic import BaseModel, Field

from cinema.context import DirectorsContext
from cinema.agents.llm_direct import GenericLLMExecutor

logger = logging.getLogger(__name__)


@dataclass
class ChapterInfo:
    """Information about a single chapter"""
    number: int
    title: str
    content: str
    word_count: int


@dataclass
class NovelStructure:
    """Parsed novel structure"""
    header: str  # World + Era + Characters section
    chapters: List[ChapterInfo]
    total_words: int
    
    @property
    def total_chapters(self) -> int:
        return len(self.chapters)


class ChapterSummary(BaseModel):
    """Output model for LLM chapter summarization"""
    chapter_number: int = Field(..., description="Chapter number")
    key_events: str = Field(..., description="2-3 key plot events in this chapter")
    character_actions: str = Field(..., description="Important character actions and changes")
    visual_details: str = Field(..., description="Key visual/setting details for comic adaptation")
    plot_advancement: str = Field(..., description="How this chapter advances the main plot")
    compressed_summary: str = Field(..., description="2-3 sentence summary for context")


class NovelSummaries(BaseModel):
    """Output model for one-shot novel summarization"""
    chapter_summaries: List[ChapterSummary] = Field(..., description="List of chapter summaries")


class SmartScreenplayCompressor:
    """
    Smart screenplay compression using LLMDirect for one-shot summarization.
    
    Strategy:
    - Parse novel into header + chapters
    - For target chapter i, create context:
      [Header: World + Characters]
      [Ch 1 to i-n: LLM summaries]
      [Ch i-1: Full content] 
      [Ch i: Full content] ← TARGET
      [Ch i+1: Full content]
      [Ch i+1+m to end: LLM summaries]
    """
    
    def __init__(self, ctx: DirectorsContext, model: str = "openai/gpt-5"):
        self.ctx = ctx
        self.model = model
        self.cache: Dict[str, NovelStructure] = {}  # workflow_id -> parsed structure
        self.summary_cache: Dict[str, ChapterSummary] = {}  # chapter_key -> summary
        
        # Create LLM executor for summarization
        # GPT-5 only supports default temperature (1.0)
        temp = 1.0 if "gpt-5" in model else 0.1
        self.llm_executor = GenericLLMExecutor(
            model=model,
            temperature=temp,
            name="chapter_summarizer"
        )
    
    def parse_novel_structure(self, screenplay: str) -> NovelStructure:
        """Parse screenplay into structured components"""
        lines = screenplay.split('\n')
        
        # Find where chapters start
        chapter_start_idx = None
        for i, line in enumerate(lines):
            if (line.strip().startswith('## Chapter') or 
                line.strip().startswith('### Chapter') or
                line.strip().startswith('# Chapter')):
                chapter_start_idx = i
                break
        
        if chapter_start_idx is None:
            # No chapters found, treat entire content as header
            return NovelStructure(
                header=screenplay,
                chapters=[],
                total_words=len(screenplay.split())
            )
        
        # Split header and chapters
        header = '\n'.join(lines[:chapter_start_idx]).strip()
        chapter_lines = lines[chapter_start_idx:]
        
        # Parse individual chapters
        chapters = []
        current_chapter = None
        current_content = []
        
        for line in chapter_lines:
            if (line.strip().startswith('## Chapter') or 
                line.strip().startswith('### Chapter') or
                line.strip().startswith('# Chapter')):
                
                # Save previous chapter
                if current_chapter is not None:
                    content = '\n'.join(current_content).strip()
                    chapters.append(ChapterInfo(
                        number=current_chapter['number'],
                        title=current_chapter['title'],
                        content=content,
                        word_count=len(content.split())
                    ))
                
                # Start new chapter
                title_line = line.strip()
                # Extract chapter number and title
                if ':' in title_line:
                    chapter_part, title_part = title_line.split(':', 1)
                    try:
                        # Extract number from "## Chapter 1" or "### Chapter 1"
                        number = int(chapter_part.split()[-1])
                        title = title_part.strip()
                    except (ValueError, IndexError):
                        number = len(chapters) + 1
                        title = title_line
                else:
                    number = len(chapters) + 1
                    title = title_line
                
                current_chapter = {'number': number, 'title': title}
                current_content = [line]
            else:
                if current_chapter is not None:
                    current_content.append(line)
        
        # Save last chapter
        if current_chapter is not None:
            content = '\n'.join(current_content).strip()
            chapters.append(ChapterInfo(
                number=current_chapter['number'],
                title=current_chapter['title'],
                content=content,
                word_count=len(content.split())
            ))
        
        total_words = sum(ch.word_count for ch in chapters) + len(header.split())
        
        return NovelStructure(
            header=header,
            chapters=chapters,
            total_words=total_words
        )
    
    async def compress_for_chapter(
        self, 
        screenplay: str, 
        target_chapter: int,
        workflow_id: str,
        context_window: int = 1,  # How many chapters before/after to include fully
        summary_window: int = 2   # How many chapters to summarize on each side
    ) -> str:
        """
        Create compressed screenplay context for a specific chapter.
        
        Args:
            screenplay: Full screenplay text
            target_chapter: Chapter number to generate (1-indexed)
            workflow_id: For caching
            context_window: Full chapters before/after target (default: 1)
            summary_window: Summarized chapters before/after context (default: 2)
        
        Returns:
            Compressed screenplay optimized for target chapter
        """
        # Parse structure (with caching)
        cache_key = f"{workflow_id}_structure"
        if cache_key not in self.cache:
            self.cache[cache_key] = self.parse_novel_structure(screenplay)
        
        structure = self.cache[cache_key]
        
        if not structure.chapters:
            # No chapters, return header only
            return structure.header
        
        # Build compressed context
        context_parts = []
        
        # 1. Always include header (world + characters)
        context_parts.append("# Novel Context")
        context_parts.append(structure.header)
        context_parts.append("")
        
        # 2. Build chapter context with windowing
        context_parts.append("# Chapter Context")
        
        total_chapters = len(structure.chapters)
        target_idx = target_chapter - 1  # Convert to 0-indexed
        
        # Define windows
        full_start = max(0, target_idx - context_window)
        full_end = min(total_chapters, target_idx + context_window + 1)
        
        summary_start = max(0, full_start - summary_window)
        summary_end = min(total_chapters, full_end + summary_window)
        
        # Get all chapter summaries in one shot (if needed)
        chapters_needing_summaries = []
        for i in range(summary_start, summary_end):
            if i < full_start or i >= full_end:  # Only chapters outside full context window
                chapters_needing_summaries.append(i)
        
        all_summaries = {}
        if chapters_needing_summaries:
            # Get summaries for chapters that need them
            chapters_to_summarize = [structure.chapters[i] for i in chapters_needing_summaries]
            temp_structure = NovelStructure(
                header=structure.header,
                chapters=chapters_to_summarize,
                total_words=sum(ch.word_count for ch in chapters_to_summarize)
            )
            all_summaries = await self._get_all_chapter_summaries_oneshot(temp_structure, workflow_id)
        
        # Add summarized chapters before full context
        for i in range(summary_start, full_start):
            chapter = structure.chapters[i]
            if chapter.number in all_summaries:
                summary = all_summaries[chapter.number]
                context_parts.append(f"## Chapter {chapter.number}: {chapter.title} (Summary)")
                context_parts.append(summary.compressed_summary)
                context_parts.append("")
        
        # Add full chapters in context window
        for i in range(full_start, full_end):
            if i < total_chapters:
                chapter = structure.chapters[i]
                # Don't add header if content already starts with a chapter header
                content_lines = chapter.content.split('\n')
                if content_lines and (content_lines[0].startswith('### Chapter') or content_lines[0].startswith('## Chapter')):
                    # Content already has header, just add it directly
                    context_parts.append(chapter.content)
                else:
                    # Add header and content
                    context_parts.append(f"## Chapter {chapter.number}: {chapter.title}")
                    context_parts.append(chapter.content)
                context_parts.append("")
        
        # Add summarized chapters after full context
        for i in range(full_end, summary_end):
            chapter = structure.chapters[i]
            if chapter.number in all_summaries:
                summary = all_summaries[chapter.number]
                context_parts.append(f"## Chapter {chapter.number}: {chapter.title} (Summary)")
                context_parts.append(summary.compressed_summary)
                context_parts.append("")
        
        compressed = '\n'.join(context_parts).strip()
        
        # Log compression stats
        original_tokens = structure.total_words * 1.3
        compressed_tokens = len(compressed.split()) * 1.3
        compression_ratio = (original_tokens - compressed_tokens) / original_tokens * 100
        
        logger.info(f"📊 Smart compression for Chapter {target_chapter}:")
        logger.info(f"   Original: {original_tokens:.0f} tokens")
        logger.info(f"   Compressed: {compressed_tokens:.0f} tokens")
        logger.info(f"   Savings: {compression_ratio:.1f}%")
        
        # Save compressed screenplay to file for inspection
        self._save_compressed_screenplay(workflow_id, target_chapter, compressed)
        
        # Log structure of compressed screenplay
        self._log_compressed_structure(compressed, target_chapter)
        
        return compressed
    
    def _save_compressed_screenplay(self, workflow_id: str, target_chapter: int, compressed: str):
        """Save compressed screenplay to file for inspection"""
        from pathlib import Path
        
        output_dir = Path("compression_cache")
        output_dir.mkdir(exist_ok=True)
        
        filename = f"{workflow_id}_ch{target_chapter}_compressed.md"
        output_file = output_dir / filename
        
        with open(output_file, 'w') as f:
            f.write(compressed)
        
        logger.info(f"💾 Saved compressed screenplay to: {output_file}")
    
    def _log_compressed_structure(self, compressed: str, target_chapter: int):
        """Log the structure of the compressed screenplay"""
        lines = compressed.split('\n')
        
        logger.info(f"📋 Compressed screenplay structure:")
        
        for line in lines:
            if line.startswith('# '):
                logger.info(f"   🌍 {line}")
            elif line.startswith('## Chapter') and '(Summary)' in line:
                logger.info(f"   📝 {line}")
            elif line.startswith('## Chapter'):
                if f"Chapter {target_chapter}:" in line:
                    logger.info(f"   🎯 {line} ← TARGET")
                else:
                    logger.info(f"   📖 {line}")
        
        # Count sections
        summary_count = compressed.count('(Summary)')
        full_chapters = compressed.count('## Chapter') - summary_count
        
        logger.info(f"   Summary chapters: {summary_count}")
        logger.info(f"   Full chapters: {full_chapters}")
        logger.info(f"   Target chapter: {target_chapter}")
    
    async def _get_all_chapter_summaries_oneshot(self, structure: NovelStructure, workflow_id: str) -> Dict[int, ChapterSummary]:
        """Get LLM-generated summaries for ALL chapters in one shot"""
        
        # First, try to load from file
        file_summaries = self._load_summaries_from_file(workflow_id)
        if file_summaries:
            # Check if we have all needed chapters
            needed_chapters = {ch.number for ch in structure.chapters}
            available_chapters = set(file_summaries.keys())
            
            if needed_chapters.issubset(available_chapters):
                logger.info(f"🎯 Using cached summaries from file for {len(needed_chapters)} chapters")
                return {ch_num: file_summaries[ch_num] for ch_num in needed_chapters}
        
        # Check if we already have all summaries in memory cache
        all_cached = True
        for chapter in structure.chapters:
            chapter_cache_key = f"{workflow_id}_ch{chapter.number}_summary"
            if chapter_cache_key not in self.summary_cache:
                all_cached = False
                break
        
        if all_cached:
            logger.info(f"🎯 Using cached summaries from memory for {len(structure.chapters)} chapters")
            # Return cached summaries
            return {
                chapter.number: self.summary_cache[f"{workflow_id}_ch{chapter.number}_summary"]
                for chapter in structure.chapters
            }
        
        # Create one-shot summarization prompt for ALL chapters
        chapters_text = []
        for chapter in structure.chapters:
            chapters_text.append(f"## Chapter {chapter.number}: {chapter.title}")
            chapters_text.append(chapter.content)
            chapters_text.append("")
        
        user_input = f"""
Analyze this entire novel and create summaries for ALL chapters at once for comic book adaptation:

{chr(10).join(chapters_text)}

For EACH chapter, provide:
- Key plot developments that advance the story
- Character actions, decisions, and changes  
- Visual/setting details important for comic panels
- How this chapter connects to the overall narrative
- A 2-3 sentence compressed summary

Return summaries for chapters {', '.join(str(ch.number) for ch in structure.chapters)}.
Keep each summary concise but informative for comic generation.
"""
        
        try:
            logger.info(f"🚀 One-shot summarization for {len(structure.chapters)} chapters...")
            
            # Log the actual prompt being sent
            logger.info(f"📝 Sending prompt to LLM:")
            logger.info(f"   Chapters to summarize: {[ch.number for ch in structure.chapters]}")
            logger.info(f"   Total input words: {len(user_input.split())}")
            logger.info(f"   Prompt preview: {user_input[:200]}...")
            
            novel_summaries = await self.llm_executor.kickoff_async(
                role="Novel Summarizer",
                goal="Create concise, informative summaries for ALL chapters in this novel for comic book adaptation",
                backstory="You are an expert at distilling narrative content into essential elements for visual storytelling. You analyze entire novels and create structured summaries for each chapter.",
                user_input=user_input,
                output_model=NovelSummaries,
                expected_output=f"A structured response with summaries for all {len(structure.chapters)} chapters, each containing key events, character actions, visual details, plot advancement, and compressed summary"
            )
            
            # Log the actual response
            logger.info(f"📥 LLM Response received:")
            logger.info(f"   Chapters returned: {len(novel_summaries.chapter_summaries)}")
            
            # Cache all results and log each summary
            summaries_dict = {}
            for summary in novel_summaries.chapter_summaries:
                chapter_cache_key = f"{workflow_id}_ch{summary.chapter_number}_summary"
                self.summary_cache[chapter_cache_key] = summary
                summaries_dict[summary.chapter_number] = summary
                
                # Log actual summary content
                logger.info(f"   Ch{summary.chapter_number}: {summary.compressed_summary[:100]}...")
            
            logger.info(f"✅ One-shot summarization complete: {len(novel_summaries.chapter_summaries)} chapters")
            
            # Save summaries to file for persistence
            self._save_summaries_to_file(workflow_id, summaries_dict)
            
            return summaries_dict
            
        except Exception as e:
            logger.error(f"❌ One-shot summarization failed: {e}")
            logger.info("🔄 Falling back to individual chapter summarization...")
            
            # Fallback to individual chapter summarization
            summaries = {}
            for chapter in structure.chapters:
                summary = await self._get_chapter_summary_individual(chapter, workflow_id)
                summaries[chapter.number] = summary
            
            return summaries
    
    def _save_summaries_to_file(self, workflow_id: str, summaries: Dict[int, ChapterSummary]):
        """Save summaries to file for persistence between tests"""
        from pathlib import Path
        import json
        
        output_dir = Path("compression_cache")
        output_dir.mkdir(exist_ok=True)
        
        summaries_file = output_dir / f"{workflow_id}_summaries.json"
        
        # Convert to serializable format
        summaries_data = {}
        for ch_num, summary in summaries.items():
            summaries_data[str(ch_num)] = {
                'chapter_number': summary.chapter_number,
                'key_events': summary.key_events,
                'character_actions': summary.character_actions,
                'visual_details': summary.visual_details,
                'plot_advancement': summary.plot_advancement,
                'compressed_summary': summary.compressed_summary
            }
        
        with open(summaries_file, 'w') as f:
            json.dump(summaries_data, f, indent=2)
        
        logger.info(f"💾 Saved summaries to: {summaries_file}")
    
    def _load_summaries_from_file(self, workflow_id: str) -> Dict[int, ChapterSummary]:
        """Load summaries from file if they exist"""
        from pathlib import Path
        import json
        
        summaries_file = Path("compression_cache") / f"{workflow_id}_summaries.json"
        
        if not summaries_file.exists():
            return {}
        
        try:
            with open(summaries_file, 'r') as f:
                summaries_data = json.load(f)
            
            summaries = {}
            for ch_num_str, data in summaries_data.items():
                ch_num = int(ch_num_str)
                summary = ChapterSummary(**data)
                summaries[ch_num] = summary
                
                # Also cache in memory
                cache_key = f"{workflow_id}_ch{ch_num}_summary"
                self.summary_cache[cache_key] = summary
            
            logger.info(f"📂 Loaded {len(summaries)} summaries from: {summaries_file}")
            return summaries
            
        except Exception as e:
            logger.warning(f"⚠️  Could not load summaries from {summaries_file}: {e}")
            return {}
            

    
    async def _get_chapter_summary_individual(self, chapter: ChapterInfo, workflow_id: str) -> ChapterSummary:
        """Get LLM-generated summary for a single chapter (fallback method)"""
        cache_key = f"{workflow_id}_ch{chapter.number}_summary"
        
        if cache_key in self.summary_cache:
            return self.summary_cache[cache_key]
        
        # Create summarization prompt
        user_input = f"""
Summarize this chapter for comic book adaptation context:

Chapter {chapter.number}: {chapter.title}

{chapter.content}

Focus on:
- Key plot developments that advance the story
- Character actions, decisions, and changes
- Visual/setting details important for comic panels
- How this chapter connects to the overall narrative

Keep the summary concise but informative for comic generation.
"""
        
        try:
            summary = await self.llm_executor.kickoff_async(
                role="Chapter Summarizer",
                goal="Create a concise, informative summary of this chapter for comic book adaptation",
                backstory="You are an expert at distilling narrative content into essential elements for visual storytelling",
                user_input=user_input,
                output_model=ChapterSummary,
                expected_output="A structured summary with key events, character actions, visual details, plot advancement, and a compressed summary"
            )
            
            # Cache the result
            self.summary_cache[cache_key] = summary
            logger.info(f"✅ Summarized Chapter {chapter.number} ({chapter.word_count} words → {len(summary.compressed_summary.split())} words)")
            
            return summary
            
        except Exception as e:
            logger.warning(f"⚠️  LLM summarization failed for chapter {chapter.number}: {e}")
            # Fallback to rule-based summary
            fallback_summary = self._rule_based_summary(chapter)
            fallback = ChapterSummary(
                chapter_number=chapter.number,
                key_events=fallback_summary,
                character_actions="Character actions not analyzed",
                visual_details="Visual details not analyzed", 
                plot_advancement="Plot advancement not analyzed",
                compressed_summary=fallback_summary
            )
            self.summary_cache[cache_key] = fallback
            return fallback
    
    def _rule_based_summary(self, chapter: ChapterInfo) -> str:
        """Create rule-based summary as fallback"""
        paragraphs = [p.strip() for p in chapter.content.split('\n\n') if p.strip()]
        
        if len(paragraphs) <= 2:
            return chapter.content
        elif len(paragraphs) <= 4:
            return f"{paragraphs[0]} [...] {paragraphs[-1]}"
        else:
            # First paragraph + middle key sentence + last paragraph
            middle_idx = len(paragraphs) // 2
            return f"{paragraphs[0]} [...] {paragraphs[middle_idx]} [...] {paragraphs[-1]}"
    
    def estimate_token_savings(self, screenplay: str, target_chapter: int) -> Dict[str, float]:
        """Estimate token savings from compression"""
        structure = self.parse_novel_structure(screenplay)
        
        original_tokens = structure.total_words * 1.3
        
        # Estimate compressed size
        header_tokens = len(structure.header.split()) * 1.3
        
        # Full chapters (target + adjacent)
        full_chapters = min(3, len(structure.chapters))  # target + 1 before + 1 after
        avg_chapter_tokens = (structure.total_words - len(structure.header.split())) / len(structure.chapters) * 1.3 if structure.chapters else 0
        full_content_tokens = full_chapters * avg_chapter_tokens
        
        # Summarized chapters (assume 80% compression)
        remaining_chapters = len(structure.chapters) - full_chapters
        summary_tokens = remaining_chapters * avg_chapter_tokens * 0.2
        
        estimated_compressed = header_tokens + full_content_tokens + summary_tokens
        
        return {
            'original_tokens': original_tokens,
            'compressed_tokens': estimated_compressed,
            'savings_percent': (original_tokens - estimated_compressed) / original_tokens * 100,
            'compression_ratio': estimated_compressed / original_tokens
        }
    
    async def test_compression_on_novel(self, screenplay: str, workflow_id: str) -> Dict[str, Any]:
        """
        Test compression on an existing novel and return analysis.
        
        This is useful for testing the compression system before using it in production.
        """
        structure = self.parse_novel_structure(screenplay)
        
        logger.info(f"🧪 Testing compression on novel:")
        logger.info(f"   Total chapters: {len(structure.chapters)}")
        logger.info(f"   Total words: {structure.total_words:,}")
        logger.info(f"   Estimated tokens: {structure.total_words * 1.3:.0f}")
        
        # Test compression for a few sample chapters
        test_chapters = [1, len(structure.chapters) // 2, len(structure.chapters)] if structure.chapters else []
        test_results = []
        
        for chapter_num in test_chapters:
            if chapter_num <= len(structure.chapters):
                compressed = await self.compress_for_chapter(screenplay, chapter_num, workflow_id)
                
                original_tokens = structure.total_words * 1.3
                compressed_tokens = len(compressed.split()) * 1.3
                savings = (original_tokens - compressed_tokens) / original_tokens * 100
                
                test_results.append({
                    'chapter': chapter_num,
                    'original_tokens': original_tokens,
                    'compressed_tokens': compressed_tokens,
                    'savings_percent': savings,
                    'compressed_preview': compressed[:500] + "..." if len(compressed) > 500 else compressed
                })
        
        return {
            'novel_structure': {
                'total_chapters': len(structure.chapters),
                'total_words': structure.total_words,
                'header_words': len(structure.header.split()),
                'avg_chapter_words': structure.total_words // len(structure.chapters) if structure.chapters else 0
            },
            'test_results': test_results,
            'summary_cache_size': len(self.summary_cache)
        }


# Convenience functions for integration
async def compress_screenplay_for_chapter(
    ctx: DirectorsContext,
    screenplay: str,
    target_chapter: int,
    workflow_id: str
) -> str:
    """Convenience function for compressing screenplay for a specific chapter"""
    compressor = SmartScreenplayCompressor(ctx)
    return await compressor.compress_for_chapter(screenplay, target_chapter, workflow_id)


async def test_compression_system(
    ctx: DirectorsContext,
    screenplay: str,
    workflow_id: str
) -> Dict[str, Any]:
    """Convenience function for testing compression system"""
    compressor = SmartScreenplayCompressor(ctx)
    return await compressor.test_compression_on_novel(screenplay, workflow_id)