"""
Test script to verify 8-9 panel grid layout support.
"""

from cinema.models.comic_output import ComicPage, ComicPanel, DialogueLine

def test_8_panel_grid():
    """Test creating an 8-panel grid page"""
    panels = []
    for i in range(1, 9):
        panel = ComicPanel(
            panel_number=i,
            chapter=1,
            scene_number=1,
            shot_type="medium",
            location="Test Location",
            visual_description=f"Panel {i} visual description",
            primary_action=f"Action {i}",
            emotional_tone="neutral"
        )
        panels.append(panel)
    
    page = ComicPage(
        page_number=1,
        chapter=1,
        scene_number=1,
        panel_arrangement="grid-8-panel",
        panel_borders="clean-sharp",
        panels=panels
    )
    
    print(f"✅ 8-panel grid page created successfully")
    print(f"   Panel count: {len(page.panels)}")
    print(f"   Layout: {page.panel_arrangement}")
    return page

def test_9_panel_grid():
    """Test creating a 9-panel grid page"""
    panels = []
    for i in range(1, 10):
        panel = ComicPanel(
            panel_number=i,
            chapter=1,
            scene_number=1,
            shot_type="medium",
            location="Test Location",
            visual_description=f"Panel {i} visual description",
            primary_action=f"Action {i}",
            emotional_tone="neutral",
            dialogue=[
                DialogueLine(character="Character A", text=f"Dialogue {i}")
            ]
        )
        panels.append(panel)
    
    page = ComicPage(
        page_number=2,
        chapter=1,
        scene_number=1,
        panel_arrangement="grid-9-panel",
        panel_borders="clean-sharp",
        panels=panels
    )
    
    print(f"✅ 9-panel grid page created successfully")
    print(f"   Panel count: {len(page.panels)}")
    print(f"   Layout: {page.panel_arrangement}")
    return page

def test_all_grid_layouts():
    """Test all grid layout types"""
    grid_layouts = [
        "grid-8-panel",
        "grid-9-panel",
        "classic-grid-8",
        "classic-grid-9",
        "dynamic-8-panel",
        "dynamic-9-panel"
    ]
    
    for layout in grid_layouts:
        panel_count = 8 if "8" in layout else 9
        panels = [
            ComicPanel(
                panel_number=i,
                chapter=1,
                scene_number=1,
                shot_type="medium",
                location="Test",
                visual_description=f"Panel {i}",
                primary_action=f"Action {i}",
                emotional_tone="neutral"
            )
            for i in range(1, panel_count + 1)
        ]
        
        page = ComicPage(
            page_number=1,
            chapter=1,
            scene_number=1,
            panel_arrangement=layout,
            panel_borders="clean-sharp",
            panels=panels
        )
        
        print(f"✅ {layout}: {len(page.panels)} panels")

def test_validation_errors():
    """Test that validation still works"""
    print("\n🧪 Testing validation...")
    
    # Test: Too few panels (should fail)
    try:
        page = ComicPage(
            page_number=1,
            chapter=1,
            scene_number=1,
            panel_arrangement="grid-8-panel",
            panel_borders="clean-sharp",
            panels=[
                ComicPanel(
                    panel_number=1,
                    chapter=1,
                    scene_number=1,
                    shot_type="medium",
                    location="Test",
                    visual_description="Test",
                    primary_action="Test",
                    emotional_tone="neutral"
                )
            ]
        )
        print("❌ Should have failed with 1 panel (min is 2)")
    except Exception as e:
        print(f"✅ Correctly rejected 1 panel: {type(e).__name__}")
    
    # Test: Too many panels (should fail)
    try:
        panels = [
            ComicPanel(
                panel_number=i,
                chapter=1,
                scene_number=1,
                shot_type="medium",
                location="Test",
                visual_description=f"Panel {i}",
                primary_action=f"Action {i}",
                emotional_tone="neutral"
            )
            for i in range(1, 11)  # 10 panels
        ]
        page = ComicPage(
            page_number=1,
            chapter=1,
            scene_number=1,
            panel_arrangement="grid-9-panel",
            panel_borders="clean-sharp",
            panels=panels
        )
        print("❌ Should have failed with 10 panels (max is 9)")
    except Exception as e:
        print(f"✅ Correctly rejected 10 panels: {type(e).__name__}")

if __name__ == "__main__":
    print("🧪 Testing 8-9 Panel Grid Layout Support\n")
    
    print("=" * 50)
    print("Test 1: 8-Panel Grid")
    print("=" * 50)
    test_8_panel_grid()
    
    print("\n" + "=" * 50)
    print("Test 2: 9-Panel Grid")
    print("=" * 50)
    test_9_panel_grid()
    
    print("\n" + "=" * 50)
    print("Test 3: All Grid Layout Types")
    print("=" * 50)
    test_all_grid_layouts()
    
    print("\n" + "=" * 50)
    print("Test 4: Validation")
    print("=" * 50)
    test_validation_errors()
    
    print("\n" + "=" * 50)
    print("✅ All tests completed!")
    print("=" * 50)
