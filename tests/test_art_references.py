#!/usr/bin/env python3
"""
Test script for art style reference loading.

Demonstrates both approaches:
1. Context-aware selection (LLM-driven)
2. Manual selection using labels (hash mapping)
"""

from cinema.workflow.art_style_references import ArtStyleReferenceManager


def test_simple_loading():
    """Test simple reference loading (first N available)."""
    print("=" * 70)
    print("Test 1: Simple Reference Loading")
    print("=" * 70)
    
    manager = ArtStyleReferenceManager()
    
    # Test loading references for different styles
    styles = ["Blueberry", "Akira", "Spider-Verse", "Arcane"]
    
    for style in styles:
        print(f"\n📚 Loading references for: {style}")
        refs = manager.load_references(style, max_references=3)
        print(f"   Loaded {len(refs)} references")


def test_context_aware_loading():
    """Test context-aware reference selection."""
    print("\n" + "=" * 70)
    print("Test 2: Context-Aware Reference Selection")
    print("=" * 70)
    
    manager = ArtStyleReferenceManager()
    
    # Test different scene contexts
    test_cases = [
        {
            "style": "Akira",
            "shot_type": "wide",
            "scene_type": "action",
            "panel_arrangement": None,
            "emotional_tone": "thrilling"
        },
        {
            "style": "Blueberry",
            "shot_type": "close-up",
            "scene_type": None,
            "panel_arrangement": "grid-9-panel",
            "emotional_tone": None
        },
        {
            "style": "Spider-Verse",
            "shot_type": "medium",
            "scene_type": "action",
            "panel_arrangement": None,
            "emotional_tone": "dramatic"
        },
        {
            "style": "Arcane",
            "shot_type": "close-up",
            "scene_type": None,
            "panel_arrangement": None,
            "emotional_tone": "dramatic"
        }
    ]
    
    for i, context in enumerate(test_cases, 1):
        print(f"\n📸 Test Case {i}: {context['style']}")
        print(f"   Context: shot={context['shot_type']}, scene={context['scene_type']}, "
              f"layout={context['panel_arrangement']}, tone={context['emotional_tone']}")
        
        refs = manager.load_references_for_scene(
            art_style=context['style'],
            shot_type=context['shot_type'],
            scene_type=context['scene_type'],
            panel_arrangement=context['panel_arrangement'],
            emotional_tone=context['emotional_tone'],
            max_references=3
        )
        print(f"   ✅ Loaded {len(refs)} context-aware references")


def test_manual_label_selection():
    """Test manual reference selection using labels (hash mapping)."""
    print("\n" + "=" * 70)
    print("Test 3: Manual Label Selection (Hash Mapping)")
    print("=" * 70)
    
    manager = ArtStyleReferenceManager()
    
    # Test manual selection for different styles
    test_cases = [
        ("Akira", "motion_lines"),
        ("Akira", "impact_panel"),
        ("Blueberry", "character_closeup"),
        ("Blueberry", "grid_layout"),
        ("Spider-Verse", "halftone_texture"),
        ("Arcane", "dramatic_lighting"),
    ]
    
    for style, label in test_cases:
        print(f"\n🎯 Getting reference: {style} -> {label}")
        ref = manager.get_reference_by_label(style, label)
        if ref:
            print(f"   ✅ Loaded: {ref.size[0]}x{ref.size[1]} pixels")
        else:
            print(f"   ❌ Not found (image file may not exist yet)")


def test_list_available_labels():
    """Test listing available reference labels."""
    print("\n" + "=" * 70)
    print("Test 4: List Available Reference Labels")
    print("=" * 70)
    
    manager = ArtStyleReferenceManager()
    
    styles = ["Akira", "Blueberry", "Spider-Verse", "Arcane", "Noir", "Watchmen"]
    
    for style in styles:
        print(f"\n📋 Available labels for {style}:")
        labels = manager.list_reference_labels(style)
        
        if labels:
            for label, purpose in labels.items():
                print(f"   • {label}: {purpose}")
        else:
            print(f"   (No labels defined)")


def test_list_available_styles():
    """Test listing available styles with reference images."""
    print("\n" + "=" * 70)
    print("Test 5: List Available Styles")
    print("=" * 70)
    
    manager = ArtStyleReferenceManager()
    
    print("\n📚 Styles with reference images:")
    available = manager.list_available_styles()
    
    if available:
        for style in available:
            print(f"   • {style}")
    else:
        print("   (No reference images found)")
        print("\n   💡 Tip: Add reference images to knowledge/art-styles/references/")


def demo_usage_examples():
    """Show practical usage examples."""
    print("\n" + "=" * 70)
    print("Usage Examples")
    print("=" * 70)
    
    print("""
# Example 1: Simple loading (first N available)
manager = ArtStyleReferenceManager()
refs = manager.load_references("Akira", max_references=3)

# Example 2: Context-aware selection (LLM-driven)
refs = manager.load_references_for_scene(
    art_style="Akira",
    shot_type="wide",
    scene_type="action",
    panel_arrangement="grid-8-panel",
    max_references=3
)

# Example 3: Manual selection by label (hash mapping)
motion_ref = manager.get_reference_by_label("Akira", "motion_lines")
impact_ref = manager.get_reference_by_label("Akira", "impact_panel")

# Example 4: List available labels
labels = manager.list_reference_labels("Akira")
print(labels)
# Output: {'motion_lines': 'Speed lines and motion blur effects', ...}

# Example 5: Use in workflow
from cinema.workflow.book_workflow import BookWorkflow

workflow = BookWorkflow(workflow_id="test", ctx=ctx)
await workflow.generate_pages(
    pages=[1, 2, 3],
    use_style_references=True,  # Enable reference loading
    reference_selection="context-aware"  # or "manual" or "simple"
)
""")


if __name__ == "__main__":
    print("\n🎨 Art Style Reference Loading Tests\n")
    
    try:
        test_simple_loading()
        test_context_aware_loading()
        test_manual_label_selection()
        test_list_available_labels()
        test_list_available_styles()
        demo_usage_examples()
        
        print("\n" + "=" * 70)
        print("✅ All tests completed!")
        print("=" * 70)
        print("\n💡 Next steps:")
        print("   1. Add reference images to knowledge/art-styles/references/")
        print("   2. Use context-aware selection for automatic matching")
        print("   3. Use manual labels for precise control")
        print("   4. Integrate with workflow for page generation")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
