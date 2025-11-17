#!/usr/bin/env python3
"""
Simple test for the new modular pipeline architecture.

Tests:
1. CharacterReferenceGenerator works correctly
2. PanelComposer works correctly
3. SimpleImageGenerator works correctly
4. SOLID principles are properly implemented

Run with: PYTHONPATH=. python -m pytest tests/test_new_architecture.py -v --asyncio-mode=auto
Or: PYTHONPATH=. python tests/test_new_architecture.py
"""

import asyncio
from typing import Any, List
from unittest.mock import MagicMock

from PIL import Image

from cinema.models.detective_output import CharacterProfile, PanelPrompt, DialogueLine
from cinema.pipeline.shared.composers import PanelComposer
from cinema.pipeline.shared.generators import (
    BaseGenerator,
    CharacterReferenceGenerator,
    SimpleImageGenerator,
)


# ============================================================================
# MOCK IMPLEMENTATIONS
# ============================================================================

class MockImageGenerator:
    """Mock image generator that implements ImageGeneratorProtocol"""
    
    def __init__(self):
        self.generated_prompts = []
    
    async def generate_content(self, prompt: str, **kwargs) -> MagicMock:
        """Mock image generation - returns fake response"""
        self.generated_prompts.append(prompt)
        
        # Create mock response with parts (like Gemini)
        mock_response = MagicMock()
        mock_response.parts = [MagicMock()]
        mock_response.parts[0].inline_data = MagicMock()
        mock_response.parts[0].inline_data.data = b"fake_image_data"
        
        return mock_response


class MockMultiImageComposer:
    """Mock multi-image composer that implements MultiImageComposerProtocol"""
    
    def __init__(self):
        self.composed_scenes = []
    
    async def generate_content_with_images(
        self, 
        images: List[Image.Image], 
        prompt: str,
        **kwargs
    ) -> MagicMock:
        """Mock multi-image composition"""
        self.composed_scenes.append({
            "num_images": len(images),
            "prompt": prompt
        })
        
        # Create mock response
        mock_response = MagicMock()
        mock_response.parts = [MagicMock()]
        mock_response.parts[0].inline_data = MagicMock()
        mock_response.parts[0].inline_data.data = b"fake_composed_image"
        
        return mock_response


class MockRateLimiter:
    """Mock rate limiter that implements RateLimiterProtocol"""
    
    def __init__(self):
        self.acquired_resources = []
    
    async def acquire(self, resource: str) -> None:
        """Mock rate limiting"""
        self.acquired_resources.append(resource)


# ============================================================================
# TEST FUNCTIONS
# ============================================================================

async def test_character_reference_generator():
    """Test CharacterReferenceGenerator with mock dependencies"""
    print("\n▶ Testing CharacterReferenceGenerator...")
    
    # Create mock dependencies
    mock_image_gen = MockImageGenerator()
    mock_rate_limiter = MockRateLimiter()
    
    # Create mock transformer
    from cinema.pipeline.shared.transformers import ComicCharacterTransformer
    transformer = ComicCharacterTransformer(art_style="Test Comic Style")
    
    # Create generator (DIP - depends on abstractions, Strategy Pattern)
    generator = CharacterReferenceGenerator(
        image_generator=mock_image_gen,
        transformer=transformer,  # Inject transformer!
        rate_limiter=mock_rate_limiter
    )
    
    # Create test character with all required fields
    character = CharacterProfile(
        name="Test Detective",
        physical_traits="Tall, dark hair, sharp eyes",
        age=35,
        ethnicity="Caucasian",
        quirks=["Always wears a fedora", "Smokes pipe"],
        backstory="A veteran detective with a troubled past",
        role="detective",
        actions_and_locations=[],
        motivations="Seeking justice"
    )
    
    # Test generation (SRP - only generates character references)
    result = await generator.generate(character=character)
    
    # Verify results
    assert result is not None
    assert len(mock_image_gen.generated_prompts) == 1
    assert "Test Comic Style" in mock_image_gen.generated_prompts[0]
    assert "Test Detective" in mock_image_gen.generated_prompts[0]
    assert "character-reference" in mock_rate_limiter.acquired_resources
    
    print("  ✅ CharacterReferenceGenerator passed!")


async def test_panel_composer():
    """Test PanelComposer with mock dependencies"""
    print("\n▶ Testing PanelComposer...")
    
    # Create mock dependencies
    mock_composer = MockMultiImageComposer()
    mock_rate_limiter = MockRateLimiter()
    
    # Create mock transformer
    from cinema.pipeline.shared.transformers import ComicPanelTransformer
    transformer = ComicPanelTransformer(art_style="Test Comic Style")
    
    # Create composer (DIP - depends on abstractions, Strategy Pattern)
    composer = PanelComposer(
        composer=mock_composer,
        transformer=transformer,  # Inject transformer!
        rate_limiter=mock_rate_limiter
    )
    
    # Create test panel with correct format
    panel = PanelPrompt(
        shot_type="close-up",
        visual_description="Detective examining evidence in dim lighting",
        dialogue=[DialogueLine(character="Detective", text="This changes everything...")],
        sound_effects=None,
        emotional_tone="tense and mysterious",
        orientation="Landscape"
    )
    
    # Create fake character images
    fake_images = [
        Image.new('RGB', (100, 100), color='red'),
        Image.new('RGB', (100, 100), color='blue')
    ]
    character_names = ["Detective Morgan", "Suspect Smith"]
    
    # Test composition (SRP - only composes panels)
    result = await composer.generate(
        panel=panel,
        character_images=fake_images,
        character_names=character_names
    )
    
    # Verify results
    assert result is not None
    assert len(mock_composer.composed_scenes) == 1
    scene = mock_composer.composed_scenes[0]
    assert scene["num_images"] == 2
    assert "Test Comic Style" in scene["prompt"]
    assert "Detective examining evidence" in scene["prompt"]
    assert "panel-composition" in mock_rate_limiter.acquired_resources
    
    print("  ✅ PanelComposer passed!")


async def test_simple_image_generator():
    """Test SimpleImageGenerator with mock dependencies"""
    print("\n▶ Testing SimpleImageGenerator...")
    
    # Create mock dependencies
    mock_image_gen = MockImageGenerator()
    mock_rate_limiter = MockRateLimiter()
    
    # Create generator
    generator = SimpleImageGenerator(
        image_generator=mock_image_gen,
        rate_limiter=mock_rate_limiter
    )
    
    # Test generation
    result = await generator.generate(prompt="A detective in a dark alley")
    
    # Verify results
    assert result is not None
    assert len(mock_image_gen.generated_prompts) == 1
    assert "A detective in a dark alley" in mock_image_gen.generated_prompts[0]
    
    print("  ✅ SimpleImageGenerator passed!")


async def test_liskov_substitution():
    """Test that all generators can substitute BaseGenerator (LSP)"""
    print("\n▶ Testing Liskov Substitution Principle...")
    
    # Create different generators
    mock_image_gen = MockImageGenerator()
    mock_rate_limiter = MockRateLimiter()
    
    # Create transformer
    from cinema.pipeline.shared.transformers import ComicCharacterTransformer
    transformer = ComicCharacterTransformer(art_style="Test Style")
    
    generators = [
        CharacterReferenceGenerator(
            image_generator=mock_image_gen,
            transformer=transformer,  # With transformer
            rate_limiter=mock_rate_limiter
        ),
        SimpleImageGenerator(
            image_generator=mock_image_gen,
            rate_limiter=mock_rate_limiter
        )
    ]
    
    # Test that all can be used as BaseGenerator (LSP)
    for generator in generators:
        assert isinstance(generator, BaseGenerator)
        
        # Test polymorphic behavior
        if isinstance(generator, CharacterReferenceGenerator):
            result = await generator.generate(
                character=CharacterProfile(
                    name="Test",
                    physical_traits="Test traits",
                    age=30,
                    quirks=["Test quirk"],
                    backstory="Test backstory",
                    role="detective",
                    actions_and_locations=[],
                    motivations="Test motivations"
                )
            )
        elif isinstance(generator, SimpleImageGenerator):
            result = await generator.generate(prompt="Test prompt")
        
        assert result is not None
    
    print("  ✅ Liskov Substitution Principle passed!")


async def test_dependency_inversion():
    """Test that components depend on abstractions, not concretions (DIP)"""
    print("\n▶ Testing Dependency Inversion Principle...")
    
    # Create different implementations of the same protocol
    mock_image_gen_1 = MockImageGenerator()
    mock_image_gen_2 = MockImageGenerator()
    
    # Create transformers
    from cinema.pipeline.shared.transformers import ComicCharacterTransformer
    transformer_1 = ComicCharacterTransformer(art_style="Style 1")
    transformer_2 = ComicCharacterTransformer(art_style="Style 2")
    
    # Both should work with CharacterReferenceGenerator (DIP)
    generator_1 = CharacterReferenceGenerator(
        image_generator=mock_image_gen_1,  # Implementation 1
        transformer=transformer_1  # Transformer 1
    )
    
    generator_2 = CharacterReferenceGenerator(
        image_generator=mock_image_gen_2,  # Implementation 2
        transformer=transformer_2  # Transformer 2
    )
    
    # Test both work the same way
    character = CharacterProfile(
        name="Test",
        physical_traits="Test",
        age=30,
        quirks=["Test"],
        backstory="Test",
        role="detective",
        actions_and_locations=[],
        motivations="Test"
    )
    
    result_1 = await generator_1.generate(character=character)
    result_2 = await generator_2.generate(character=character)
    
    assert result_1 is not None
    assert result_2 is not None
    assert len(mock_image_gen_1.generated_prompts) == 1
    assert len(mock_image_gen_2.generated_prompts) == 1
    
    print("  ✅ Dependency Inversion Principle passed!")


# ============================================================================
# MAIN TEST RUNNER
# ============================================================================

async def main():
    """Run all tests"""
    print("🧪 Testing New Modular Pipeline Architecture")
    print("=" * 60)
    
    tests = [
        ("CharacterReferenceGenerator", test_character_reference_generator),
        ("PanelComposer", test_panel_composer),
        ("SimpleImageGenerator", test_simple_image_generator),
        ("Liskov Substitution Principle", test_liskov_substitution),
        ("Dependency Inversion Principle", test_dependency_inversion),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            await test_func()
            passed += 1
        except Exception as e:
            print(f"  ❌ {name} failed: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("\n✨ New architecture is working correctly!" if failed == 0 else "\n⚠️  Some tests failed")
    
    return failed == 0


if __name__ == "__main__":
    import sys
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
