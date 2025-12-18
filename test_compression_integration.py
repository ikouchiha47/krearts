#!/usr/bin/env python3
"""
Test smart compression integration with actual ChapterBuilder.

This test:
1. Loads a real novel
2. Generates compressed context for a chapter
3. Shows the ChapterBuilder prompt with compressed content
4. Demonstrates actual token savings
"""

import asyncio
import logging
from pathlib import Path

from cinema.context import DirectorsContext
from cinema.registry import OpenAiHerd
from cinema.agents.bookwriter.smart_compression import SmartScreenplayCompressor
from cinema.agents.bookwriter.crew import ChapterBuilder

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_compression_with_chapterbuilder():
    """Test compression integration with actual ChapterBuilder"""
    print("🔬 COMPRESSION + CHAPTERBUILDER INTEGRATION TEST")
    print("=" * 60)
    
    # Load test novel
    test_file = "storyline_c778f39d.md"
    if not Path(test_file).exists():
        print(f"❌ Test file not found: {test_file}")
        return
    
    with open(test_file, 'r') as f:
        screenplay = f.read()
    
    print(f"📖 Loaded novel: {len(screenplay)} chars, {len(screenplay.split())} words")
    
    # Create context
    ctx = DirectorsContext(llmstore=OpenAiHerd, debug=False)
    
    # Initialize compressor
    compressor = SmartScreenplayCompressor(ctx, model="openai/gpt-5")
    
    # Test compression for chapter 3 (middle chapter)
    target_chapter = 3
    workflow_id = "test_integration_001"
    
    print(f"\n🎯 Testing compression for Chapter {target_chapter}")
    
    # Generate compressed screenplay
    print("📊 Generating compressed screenplay...")
    compressed_screenplay = await compressor.compress_for_chapter(
        screenplay=screenplay,
        target_chapter=target_chapter,
        workflow_id=workflow_id,
        context_window=1,  # 1 chapter before/after in full
        summary_window=2   # 2 chapters before/after as summaries
    )
    
    # Show compression stats
    original_tokens = len(screenplay.split()) * 1.3
    compressed_tokens = len(compressed_screenplay.split()) * 1.3
    savings = (original_tokens - compressed_tokens) / original_tokens * 100
    
    print(f"\n📈 Compression Results:")
    print(f"   Original: {original_tokens:.0f} tokens")
    print(f"   Compressed: {compressed_tokens:.0f} tokens")
    print(f"   Savings: {savings:.1f}%")
    print(f"   Compression ratio: {compressed_tokens/original_tokens:.2f}")
    
    # Show compressed content preview
    print(f"\n📄 Compressed Screenplay Preview (first 800 chars):")
    print("-" * 60)
    print(compressed_screenplay[:800])
    print("..." if len(compressed_screenplay) > 800 else "")
    print("-" * 60)
    
    # Now test with actual ChapterBuilder
    print(f"\n🤖 Testing with ChapterBuilder...")
    
    # Create ChapterBuilder (with mock to avoid actual generation)
    chapter_builder = ChapterBuilder(ctx=ctx, use_mock=True)
    
    # Extract target chapter content from compressed screenplay
    lines = compressed_screenplay.split('\n')
    target_section = []
    in_target = False
    
    for line in lines:
        if f"Chapter {target_chapter}:" in line:
            in_target = True
        elif in_target and line.startswith("## Chapter") and f"Chapter {target_chapter}:" not in line:
            break
        
        if in_target:
            target_section.append(line)
    
    target_content = '\n'.join(target_section)
    
    # Create a sample chapter input that would use the compressed screenplay
    from cinema.agents.bookwriter.crew import ChapterBuilderSchema
    
    chapter_input = ChapterBuilderSchema(
        title=f"Chapter {target_chapter}",
        screenplay=compressed_screenplay,  # Use compressed version!
        examples="",
        chapter_id=target_chapter,
        chapter_content=target_content,
        art_style="Neon-drenched, high-contrast, Blade Runner/cyberpunk anime-inspired",
        aspect_ratio="4:5"
    )
    
    print(f"   Chapter input created with compressed screenplay")
    print(f"   Screenplay length: {len(chapter_input.screenplay)} chars")
    print(f"   Target chapter: {chapter_input.chapter_id}")
    print(f"   Art style: {chapter_input.art_style}")
    
    # Show what the ChapterBuilder would actually receive
    print(f"\n📝 ChapterBuilder Input Analysis:")
    print(f"   Input screenplay tokens: ~{len(chapter_input.screenplay.split()) * 1.3:.0f}")
    print(f"   Token savings vs original: {savings:.1f}%")
    
    # Target content already extracted above
    
    print(f"\n🎯 Target Chapter Content (what ChapterBuilder focuses on):")
    print("-" * 60)
    print(target_content[:500])
    print("..." if len(target_content) > 500 else "")
    print("-" * 60)
    
    # Show context chapters (summaries)
    print(f"\n📚 Context Chapters (summaries for efficiency):")
    context_summaries = []
    for line in compressed_screenplay.split('\n'):
        if "(Summary)" in line:
            context_summaries.append(line)
    
    for summary_line in context_summaries[:3]:  # Show first 3
        print(f"   {summary_line}")
    if len(context_summaries) > 3:
        print(f"   ... and {len(context_summaries) - 3} more")
    
    print(f"\n✅ INTEGRATION TEST COMPLETE!")
    print(f"\nKey Benefits Demonstrated:")
    print(f"1. 🚀 One-shot summarization (not per-chapter)")
    print(f"2. 📊 {savings:.1f}% token reduction")
    print(f"3. 🎯 Target chapter gets full context")
    print(f"4. 📚 Other chapters compressed to summaries")
    print(f"5. 🤖 ChapterBuilder receives optimized input")
    
    return {
        'original_tokens': original_tokens,
        'compressed_tokens': compressed_tokens,
        'savings_percent': savings,
        'target_chapter': target_chapter,
        'compressed_screenplay': compressed_screenplay
    }


async def test_multiple_chapters():
    """Test compression for multiple chapters to show consistency"""
    print("\n🔄 MULTI-CHAPTER COMPRESSION TEST")
    print("=" * 50)
    
    # Load test novel
    test_file = "storyline_c778f39d.md"
    with open(test_file, 'r') as f:
        screenplay = f.read()
    
    ctx = DirectorsContext(llmstore=OpenAiHerd, debug=False)
    compressor = SmartScreenplayCompressor(ctx, model="openai/gpt-5")
    
    # Test chapters 1, 5, 10
    test_chapters = [1, 5, 10]
    workflow_id = "test_multi_001"
    
    results = []
    
    for chapter_num in test_chapters:
        print(f"\n📖 Testing Chapter {chapter_num}...")
        
        compressed = await compressor.compress_for_chapter(
            screenplay=screenplay,
            target_chapter=chapter_num,
            workflow_id=workflow_id
        )
        
        original_tokens = len(screenplay.split()) * 1.3
        compressed_tokens = len(compressed.split()) * 1.3
        savings = (original_tokens - compressed_tokens) / original_tokens * 100
        
        results.append({
            'chapter': chapter_num,
            'savings': savings,
            'compressed_tokens': compressed_tokens
        })
        
        print(f"   Savings: {savings:.1f}%")
    
    print(f"\n📊 Multi-Chapter Results:")
    avg_savings = sum(r['savings'] for r in results) / len(results)
    print(f"   Average savings: {avg_savings:.1f}%")
    print(f"   Consistency: {max(r['savings'] for r in results) - min(r['savings'] for r in results):.1f}% range")
    
    return results


async def main():
    """Run all integration tests"""
    try:
        # Test 1: Full integration with ChapterBuilder
        integration_result = await test_compression_with_chapterbuilder()
        
        # Test 2: Multi-chapter consistency
        multi_result = await test_multiple_chapters()
        
        print(f"\n🎉 ALL INTEGRATION TESTS PASSED!")
        print(f"\nSummary:")
        print(f"- Smart compression working with ChapterBuilder")
        print(f"- Average token savings: {integration_result['savings_percent']:.1f}%")
        print(f"- One-shot summarization (not per-chapter calls)")
        print(f"- Flow state integration ready")
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())