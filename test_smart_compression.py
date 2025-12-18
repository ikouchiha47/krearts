#!/usr/bin/env python3
"""
Test script for Smart Compression system.

This script:
1. Loads an existing novel from the database/files
2. Tests the smart compression system
3. Shows before/after token counts
4. Demonstrates how summaries look
5. Tests the experimental ParallelComicGenerator
"""

import asyncio
import json
import logging
from pathlib import Path

from cinema.context import DirectorsContext
from cinema.registry import OpenAiHerd
from cinema.agents.bookwriter.smart_compression import SmartScreenplayCompressor, test_compression_system
from cinema.pipeline.experimental_parallel_comic_generator import ExperimentalParallelComicGenerator
from cinema.models.novel import Novel

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_test_novel() -> str:
    """Load a test novel for compression testing"""
    test_files = [
        "storyline_c778f39d.md",  # The large cyberpunk novel
        "detective_storyline.md",
        "screenplay.md"
    ]
    
    for filename in test_files:
        if Path(filename).exists():
            logger.info(f"📖 Loading test novel from {filename}")
            with open(filename, 'r') as f:
                content = f.read()
                if len(content) > 5000:  # Only use substantial content
                    return content
    
    logger.warning("No large test novels found, using sample")
    return """
# Sample Detective Novel

## World & Era Context
The year is 2042 in New San Francisco, a city that scraped the sky after the last great quake...

## Characters
### Character 1
**Name:** Detective Kira Byte
**Role:** detective

## Chapter 1: The Static and the Drizzle
The drizzle of New San Francisco was a constant, a liquid sigh against the permaglass...

## Chapter 2: The Unbreakable Code  
Nova Chen's lab was her sanctuary, a clean white space suspended high above the city's grime...

## Chapter 3: The Mark of the Maker
By the time Kira hacked the lab's lockdown, the air inside was sterile and unnaturally still...
"""


async def test_compression_system_detailed():
    """Test the smart compression system in detail"""
    print("🧪 SMART COMPRESSION SYSTEM TEST")
    print("=" * 50)
    
    # Load test novel
    screenplay = load_test_novel()
    
    # Create context
    ctx = DirectorsContext(llmstore=OpenAiHerd, debug=False)
    
    # Test compression system
    workflow_id = "test_compression_001"
    
    print(f"\n📊 Testing compression on novel:")
    print(f"   Characters: {len(screenplay):,}")
    print(f"   Words: {len(screenplay.split()):,}")
    print(f"   Estimated tokens: {len(screenplay.split()) * 1.3:.0f}")
    
    # Run compression test
    results = await test_compression_system(ctx, screenplay, workflow_id)
    
    print(f"\n📈 Novel Structure Analysis:")
    structure = results['novel_structure']
    print(f"   Total chapters: {structure['total_chapters']}")
    print(f"   Total words: {structure['total_words']:,}")
    print(f"   Header words: {structure['header_words']:,}")
    print(f"   Avg chapter words: {structure['avg_chapter_words']:,}")
    
    print(f"\n🔍 Compression Test Results:")
    for result in results['test_results']:
        print(f"   Chapter {result['chapter']}:")
        print(f"     Original: {result['original_tokens']:.0f} tokens")
        print(f"     Compressed: {result['compressed_tokens']:.0f} tokens")
        print(f"     Savings: {result['savings_percent']:.1f}%")
        print(f"     Preview: {result['compressed_preview'][:200]}...")
        print()
    
    print(f"📝 Summary cache size: {results['summary_cache_size']} chapters")
    
    return results


async def test_experimental_comic_generator():
    """Test the experimental comic generator with compression"""
    print("\n🎨 EXPERIMENTAL COMIC GENERATOR TEST")
    print("=" * 50)
    
    # Load test novel
    screenplay = load_test_novel()
    
    # Create context
    ctx = DirectorsContext(llmstore=OpenAiHerd, debug=False)
    
    # Parse novel
    try:
        novel = Novel.from_str(screenplay)
        print(f"✅ Parsed novel: {novel.title}")
        print(f"   Chapters: {len(novel.chapters)}")
    except Exception as e:
        print(f"❌ Failed to parse novel: {e}")
        return
    
    # Create experimental generator
    generator = ExperimentalParallelComicGenerator(
        ctx=ctx,
        screenplay=screenplay,
        max_concurrent=1,  # Limit for testing
        workflow_id="test_experimental_001",
        use_mock=True,  # Use mock to avoid actual LLM calls
        total_pages_per_chapter=3,  # Test with 3 pages per chapter
        use_smart_compression=True,
        compression_strategy="rule_based"  # Use rule-based for testing
    )
    
    print(f"\n🚀 Testing experimental generation:")
    print(f"   Pages per chapter: {generator.total_pages_per_chapter}")
    print(f"   Compression strategy: {generator.compression_strategy}")
    print(f"   Smart compression: {generator.use_smart_compression}")
    
    # Test compression on first chapter
    if novel.chapters:
        compressed = await generator._compress_screenplay_for_chapter(1, len(novel.chapters))
        
        original_tokens = len(screenplay.split()) * 1.3
        compressed_tokens = len(compressed.split()) * 1.3
        savings = (original_tokens - compressed_tokens) / original_tokens * 100
        
        print(f"\n📊 Chapter 1 compression test:")
        print(f"   Original: {original_tokens:.0f} tokens")
        print(f"   Compressed: {compressed_tokens:.0f} tokens")
        print(f"   Savings: {savings:.1f}%")
        
        print(f"\n📄 Compressed screenplay preview:")
        print(compressed[:800] + "..." if len(compressed) > 800 else compressed)
    
    # Note: We won't actually run the full generation since it requires LLM calls
    print(f"\n✅ Experimental generator setup complete!")
    print(f"   Ready for actual comic generation with compression")


async def compare_compression_strategies():
    """Compare different compression strategies"""
    print("\n⚖️  COMPRESSION STRATEGY COMPARISON")
    print("=" * 50)
    
    screenplay = load_test_novel()
    ctx = DirectorsContext(llmstore=OpenAiHerd, debug=False)
    
    # Test different strategies
    strategies = ["none", "rule_based", "smart"]
    results = {}
    
    for strategy in strategies:
        generator = ExperimentalParallelComicGenerator(
            ctx=ctx,
            screenplay=screenplay,
            workflow_id=f"test_{strategy}",
            compression_strategy=strategy,
            use_smart_compression=(strategy != "none")
        )
        
        if screenplay.count("Chapter") > 0:  # Has chapters
            compressed = await generator._compress_screenplay_for_chapter(1, 3)
            
            original_tokens = len(screenplay.split()) * 1.3
            compressed_tokens = len(compressed.split()) * 1.3
            savings = (original_tokens - compressed_tokens) / original_tokens * 100
            
            results[strategy] = {
                'original_tokens': original_tokens,
                'compressed_tokens': compressed_tokens,
                'savings_percent': savings,
                'compression_ratio': compressed_tokens / original_tokens
            }
    
    print(f"Strategy Comparison:")
    for strategy, data in results.items():
        print(f"   {strategy.upper()}:")
        print(f"     Tokens: {data['compressed_tokens']:.0f} ({data['savings_percent']:.1f}% savings)")
        print(f"     Ratio: {data['compression_ratio']:.2f}")
    
    return results


async def main():
    """Run all compression tests"""
    print("🔬 SMART COMPRESSION TESTING SUITE")
    print("=" * 60)
    
    try:
        # Test 1: Detailed compression system test
        compression_results = await test_compression_system_detailed()
        
        # Test 2: Experimental comic generator test
        await test_experimental_comic_generator()
        
        # Test 3: Compare compression strategies
        strategy_results = await compare_compression_strategies()
        
        print(f"\n✅ ALL TESTS COMPLETED!")
        print(f"\nNext steps:")
        print(f"1. Review compression results and adjust parameters")
        print(f"2. Test with actual ChapterBuilder (remove use_mock=True)")
        print(f"3. Integrate into production workflow")
        print(f"4. Add page controls to API endpoints")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())