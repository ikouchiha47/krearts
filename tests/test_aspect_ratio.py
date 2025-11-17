#!/usr/bin/env python3
"""
Test script to verify 4:5 aspect ratio is working for character generation.
"""
import asyncio
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from cinema.workflow.character_manager import CharacterReferenceManager
from cinema.providers.gemini import GeminiMediaGen
from PIL import Image


async def test_character_aspect_ratio():
    """Test that character generation produces 4:5 aspect ratio images."""
    
    print("🧪 Testing Character Generation with 4:5 Aspect Ratio")
    print("=" * 60)
    
    # Initialize
    gemini = GeminiMediaGen()
    char_manager = CharacterReferenceManager(gemini)
    
    # Test character description
    test_character = {
        "character_id": "TEST_001",
        "name": "Test Character",
        "physical_appearance": "A young woman with short black hair, wearing a blue jacket",
        "style": "realistic, detailed, professional photography style",
    }
    
    output_dir = "output/test_aspect_ratio"
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    print(f"\n📸 Generating front view for {test_character['name']}...")
    print(f"   Output: {output_dir}")
    
    # Generate just the front view
    try:
        results = await char_manager.generate_character_references(
            character_id=test_character["character_id"],
            character_description=test_character,
            output_dir=output_dir,
            include_back_view=False,  # Skip back view for faster test
        )
        
        print(f"\n✅ Generation complete!")
        print(f"   Generated views: {list(results.keys())}")
        
        # Check dimensions
        print(f"\n📏 Checking image dimensions:")
        for view, path in results.items():
            img = Image.open(path)
            width, height = img.size
            ratio = width / height
            expected_ratio = 4 / 5  # 0.8
            
            print(f"\n   {view.upper()} view:")
            print(f"      Path: {path}")
            print(f"      Size: {width}x{height}")
            print(f"      Ratio: {ratio:.3f} (expected: {expected_ratio:.3f})")
            
            if abs(ratio - expected_ratio) < 0.05:  # Allow 5% tolerance
                print(f"      ✅ Aspect ratio is correct!")
            else:
                print(f"      ❌ Aspect ratio is WRONG! Expected ~0.8, got {ratio:.3f}")
        
        return results
        
    except Exception as e:
        print(f"\n❌ Error during generation: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    results = asyncio.run(test_character_aspect_ratio())
    
    if results:
        print("\n" + "=" * 60)
        print("✅ Test completed successfully!")
        print(f"   Check images in: output/test_aspect_ratio/")
    else:
        print("\n" + "=" * 60)
        print("❌ Test failed!")
        sys.exit(1)
