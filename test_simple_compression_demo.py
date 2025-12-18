#!/usr/bin/env python3
"""
Simple compression demonstration.

Shows:
1. Full novel with chapters
2. One-shot compression of all chapters
3. Novel with compressed chapters surrounding target chapter (ChapterBuilder prompt)
"""

import asyncio
import logging
from pathlib import Path

from cinema.context import DirectorsContext
from cinema.registry import OpenAiHerd
from cinema.agents.bookwriter.smart_compression import SmartScreenplayCompressor

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def show_novel_structure(screenplay: str):
    """Show the original novel structure"""
    print("📖 ORIGINAL NOVEL STRUCTURE")
    print("=" * 50)
    
    lines = screenplay.split('\n')
    chapters = []
    current_chapter = None
    word_count = 0
    
    for line in lines:
        if line.strip().startswith('## Chapter'):
            if current_chapter:
                chapters.append((current_chapter, word_count))
            current_chapter = line.strip()
            word_count = 0
        elif line.strip():
            word_count += len(line.split())
    
    if current_chapter:
        chapters.append((current_chapter, word_count))
    
    total_words = sum(wc for _, wc in chapters)
    
    print(f"Total chapters: {len(chapters)}")
    print(f"Total words: {total_words:,}")
    print(f"Estimated tokens: {total_words * 1.3:.0f}")
    print()
    
    for i, (chapter_title, words) in enumerate(chapters[:5], 1):
        print(f"{i:2d}. {chapter_title} ({words} words)")
    
    if len(chapters) > 5:
        print(f"    ... and {len(chapters) - 5} more chapters")
    
    print()


async def show_one_shot_compression(compressor, screenplay: str, workflow_id: str):
    """Show one-shot compression of all chapters"""
    print("🚀 ONE-SHOT COMPRESSION")
    print("=" * 50)
    
    # Parse structure
    structure = compressor.parse_novel_structure(screenplay)
    
    print(f"Generating summaries for {len(structure.chapters)} chapters in ONE call...")
    
    # Show original chapter content (first chapter as example)
    if structure.chapters:
        first_chapter = structure.chapters[0]
        print(f"\n📖 ORIGINAL Chapter {first_chapter.number} ({first_chapter.word_count} words):")
        print("-" * 40)
        print(first_chapter.content[:500] + "..." if len(first_chapter.content) > 500 else first_chapter.content)
        print("-" * 40)
    
    # Get all summaries in one shot
    all_summaries = await compressor._get_all_chapter_summaries_oneshot(structure, workflow_id)
    
    print(f"✅ Generated {len(all_summaries)} summaries")
    
    # Show compressed summaries
    print(f"\n📝 COMPRESSED SUMMARIES:")
    for i, (ch_num, summary) in enumerate(list(all_summaries.items())[:3]):
        original_words = next((ch.word_count for ch in structure.chapters if ch.number == ch_num), 0)
        compressed_words = len(summary.compressed_summary.split())
        compression = (1 - compressed_words/original_words) * 100 if original_words > 0 else 0
        
        print(f"\nChapter {ch_num} ({original_words} → {compressed_words} words, {compression:.1f}% compression):")
        print(f"  Key Events: {summary.key_events}")
        print(f"  Character Actions: {summary.character_actions}")
        print(f"  Compressed: {summary.compressed_summary}")
    
    if len(all_summaries) > 3:
        print(f"\n... and {len(all_summaries) - 3} more summaries")
    
    print()
    return all_summaries


async def show_chapterbuilder_prompt(compressor, screenplay: str, target_chapter: int, workflow_id: str):
    """Show what ChapterBuilder would receive"""
    print(f"🤖 CHAPTERBUILDER PROMPT FOR CHAPTER {target_chapter}")
    print("=" * 50)
    
    # Generate compressed screenplay for target chapter
    compressed = await compressor.compress_for_chapter(
        screenplay=screenplay,
        target_chapter=target_chapter,
        workflow_id=workflow_id,
        context_window=1,  # 1 chapter before/after in full
        summary_window=2   # 2 chapters before/after as summaries
    )
    
    # Show compression stats
    original_tokens = len(screenplay.split()) * 1.3
    compressed_tokens = len(compressed.split()) * 1.3
    savings = (original_tokens - compressed_tokens) / original_tokens * 100
    
    print(f"Original novel: {original_tokens:.0f} tokens")
    print(f"Compressed for Chapter {target_chapter}: {compressed_tokens:.0f} tokens")
    print(f"Token savings: {savings:.1f}%")
    print()
    
    print("FULL COMPRESSED SCREENPLAY (what ChapterBuilder receives):")
    print("=" * 80)
    print(compressed)
    print("=" * 80)
    
    # Also show structure analysis
    print(f"\nSTRUCTURE ANALYSIS:")
    lines = compressed.split('\n')
    summary_chapters = []
    full_chapters = []
    target_found = False
    
    for line in lines:
        if line.startswith('## Chapter') and '(Summary)' in line:
            ch_num = line.split()[2].rstrip(':')
            summary_chapters.append(ch_num)
        elif line.startswith('## Chapter'):
            ch_num = line.split()[2].rstrip(':')
            full_chapters.append(ch_num)
            if ch_num == str(target_chapter):
                target_found = True
    
    print(f"📝 Summary chapters: {summary_chapters}")
    print(f"📖 Full chapters: {full_chapters}")
    print(f"🎯 Target chapter {target_chapter}: {'✅ Found' if target_found else '❌ Missing'}")
    
    return compressed


async def main():
    """Run the simple compression demo"""
    print("🔬 SIMPLE COMPRESSION DEMONSTRATION")
    print("=" * 60)
    
    # Load test novel from database (crew flow states)
    screenplay = None
    
    try:
        import sqlite3
        import json
        
        print("📖 Loading novel from database (crew flow states)...")
        conn = sqlite3.connect('cinema_server.db')
        cursor = conn.cursor()
        
        # Get a workflow with screenplay data
        cursor.execute("SELECT state_json FROM storybuilder_states WHERE id = 'd7dd6092'")
        result = cursor.fetchone()
        
        if result:
            state_data = json.loads(result[0])
            screenplay = state_data.get('output', {}).get('screenplay')
            
            if screenplay and len(screenplay) > 5000:
                print(f"✅ Loaded from database: {len(screenplay)} chars")
            else:
                screenplay = None
        
        conn.close()
        
    except Exception as e:
        print(f"⚠️  Database load failed: {e}")
    
    # Fallback to file if database fails
    if not screenplay:
        test_file = "storyline_c778f39d.md"
        if Path(test_file).exists():
            print(f"📖 Fallback: Loading from {test_file}")
            with open(test_file, 'r') as f:
                screenplay = f.read()
        else:
            print(f"❌ No novel found in database or files")
            return
    
    # Create context and compressor
    ctx = DirectorsContext(llmstore=OpenAiHerd, debug=False)
    compressor = SmartScreenplayCompressor(ctx, model="openai/gpt-5")
    workflow_id = "demo_001"
    
    # Step 1: Show original novel structure
    show_novel_structure(screenplay)
    
    # Step 2: Show one-shot compression
    all_summaries = await show_one_shot_compression(compressor, screenplay, workflow_id)
    
    # Step 3: Show ChapterBuilder prompt for chapter 5
    target_chapter = 5
    compressed_screenplay = await show_chapterbuilder_prompt(compressor, screenplay, target_chapter, workflow_id)
    
    print("✅ DEMONSTRATION COMPLETE!")
    print()
    print("Key Points:")
    print("1. 📖 Original novel has full chapters with all content")
    print("2. 🚀 One-shot compression generates ALL summaries in single LLM call")
    print("3. 🤖 ChapterBuilder gets compressed novel with:")
    print("   - Full context for target chapter and neighbors")
    print("   - Summaries for distant chapters")
    print("   - Massive token savings while preserving context")


if __name__ == "__main__":
    asyncio.run(main())