# Design Document: Multi-Panel Layout Support

## Overview

This design adds a `ComicPage` model to group 2-3 `ComicPanel` objects with layout metadata, enabling the system to generate multi-panel page compositions that follow creative layout patterns from `knowledge/layouts/panel_arrangements.md`. The design maintains backward compatibility with existing `ComicPanel` structures while introducing a page-based organization layer.

## Architecture

### Current Structure (Before)
```
ComicBookOutput
└── chapters: List[ComicChapter]
    └── scenes: List[ComicScene]
        └── panels: List[ComicPanel]  # Individual panels
```

### New Structure (After)
```
ComicBookOutput
└── chapters: List[ComicChapter]
    └── scenes: List[ComicScene]
        └── pages: List[ComicPage]  # NEW: Groups of 2-3 panels
            └── panels: List[ComicPanel]  # Existing panel model
```

### Key Design Decisions

1. **Additive, Not Replacement**: `ComicPanel` model remains unchanged. `ComicPage` wraps panels.
2. **Scene-Level Change**: `ComicScene.panels` becomes `ComicScene.pages`
3. **2-3 Panel Constraint**: Each page contains 2-3 panels (per `panel_arrangements.md`)
4. **Layout Metadata**: Page-level fields describe arrangement, borders, transitions
5. **Backward Compatibility**: Existing panel fields (orientation, panel_size) remain for individual panel control

## Components and Interfaces

### 1. ComicPage Model

**Location**: `cinema/models/comic_output.py`

```python
class ComicPage(BaseModel):
    """
    A physical comic book page containing 2-3 panels with layout specifications.
    
    Follows layout patterns from knowledge/layouts/panel_arrangements.md
    """
    
    # Page identification
    page_number: int = Field(..., description="Sequential page number in the chapter")
    chapter: int = Field(..., description="Which chapter this page belongs to")
    scene_number: int = Field(..., description="Scene number within the chapter")
    
    # Layout specification (from panel_arrangements.md)
    panel_arrangement: Literal[
        "horizontal-2-panel",
        "horizontal-3-panel",
        "vertical-2-panel",
        "vertical-3-panel",
        "fractured-overlapping",
        "zoom-progression",
        "cross-over-bleed",
        "shattered-exploded",
        "dynamic-grid"
    ] = Field(..., description="How panels are arranged on the page")
    
    panel_borders: Literal[
        "clean-sharp",
        "ragged-dynamic",
        "overlapping",
        "no-borders",
        "subtle-angles"
    ] = Field(
        default="clean-sharp",
        description="Visual style of borders between panels"
    )
    
    panel_transition_style: Optional[Literal[
        "hard-cuts",
        "overlapping-scenes",
        "blended-transitions",
        "diagonal-cuts",
        "frame-within-frame"
    ]] = Field(
        None,
        description="How panels interact visually on the page"
    )
    
    # Panels (2-3 per page)
    panels: List[ComicPanel] = Field(
        ...,
        min_length=2,
        max_length=3,
        description="Panels on this page (2-3 panels)"
    )
    
    # Optional metadata
    page_description: Optional[str] = Field(
        None,
        description="Overall description of the page composition"
    )
```

### 2. Updated ComicScene Model

**Location**: `cinema/models/comic_output.py`

```python
class ComicScene(BaseModel):
    """
    A scene is a sequence of pages in the same location/time.
    Typically 2-4 pages per scene (6-12 panels total).
    """
    
    scene_number: int = Field(..., description="Scene number within chapter")
    chapter: int = Field(..., description="Chapter this scene belongs to")
    
    location: str = Field(..., description="Primary location for this scene")
    time_of_day: Optional[str] = Field(None, description="Time of day")
    
    scene_description: str = Field(
        ...,
        description="Brief description of what happens in this scene"
    )
    
    characters_in_scene: List[str] = Field(
        default_factory=list,
        description="Characters appearing in this scene"
    )
    
    # CHANGED: panels → pages
    pages: List[ComicPage] = Field(
        default_factory=list,
        description="Pages that make up this scene (typically 2-4 pages)"
    )
    
    # Deprecated but kept for backward compatibility
    panels: List[ComicPanel] = Field(
        default_factory=list,
        description="DEPRECATED: Use pages instead. Kept for backward compatibility."
    )
```

### 3. Updated ComicBookOutput Statistics

**Location**: `cinema/models/comic_output.py`

```python
class ComicBookOutput(BaseModel):
    """
    Complete comic book output from a novel.
    
    Expected output:
    - 15 chapters
    - 4-8 scenes per chapter = 60-120 scenes
    - 2-4 pages per scene = 120-480 pages
    - 2-3 panels per page = 240-1440 panels (typically ~400-600 panels)
    """
    
    # ... existing fields ...
    
    # Statistics (for validation)
    total_chapters: int = Field(default=0, description="Total number of chapters")
    total_scenes: int = Field(default=0, description="Total number of scenes")
    total_pages: int = Field(default=0, description="Total number of pages")  # NEW
    total_panels: int = Field(default=0, description="Total number of panels")
    estimated_pages: int = Field(default=0, description="Estimated comic book pages")  # DEPRECATED: use total_pages
```

## Data Models

### Panel Arrangement Types

Based on `knowledge/layouts/panel_arrangements.md`:

| Arrangement | Panels | Description | Use Case |
|-------------|--------|-------------|----------|
| `horizontal-2-panel` | 2 | Two panels side-by-side, dynamic widths | Dialogue exchange, before/after |
| `horizontal-3-panel` | 3 | Three panels horizontally, varied widths | Action sequence, progression |
| `vertical-2-panel` | 2 | Two panels stacked, dynamic heights | Descent/ascent, time passage |
| `vertical-3-panel` | 3 | Three panels stacked, varied heights | Vertical action, falling |
| `fractured-overlapping` | 2-3 | Panels overlap dynamically | Chaos, simultaneous events |
| `zoom-progression` | 3 | Progressive zoom (wide → close-up) | Building suspense, detail focus |
| `cross-over-bleed` | 2-3 | Dominant element bleeds across panels | Powerful reveal, overwhelming force |
| `shattered-exploded` | 2-3 | Broken, jagged panel borders | Impact, psychological distress |
| `dynamic-grid` | 2-3 | Irregular grid with varied sizes | General purpose, flexible |

### Panel Border Types

| Border Type | Description | Visual Effect |
|-------------|-------------|---------------|
| `clean-sharp` | Sharp, clean borders | Professional, controlled |
| `ragged-dynamic` | Rough, energetic borders | Action, chaos |
| `overlapping` | Panels overlap each other | Simultaneous events |
| `no-borders` | Borderless, flowing panels | Dreamlike, seamless |
| `subtle-angles` | Angled borders, visual tension | Dynamic, unstable |

### Panel Transition Types

| Transition | Description | Narrative Effect |
|------------|-------------|------------------|
| `hard-cuts` | Abrupt scene changes | Jarring, sudden |
| `overlapping-scenes` | Scenes bleed into each other | Continuity, flow |
| `blended-transitions` | Gradual visual blend | Smooth, dreamlike |
| `diagonal-cuts` | Diagonal panel divisions | Dynamic, energetic |
| `frame-within-frame` | Nested panel compositions | Flashback, memory |

## Error Handling

### Validation Rules

1. **Panel Count Constraint**
   - Each `ComicPage` must have 2-3 panels
   - Pydantic validation: `min_length=2, max_length=3`
   - Error: `ValueError` if constraint violated

2. **Panel Number Continuity**
   - Panel numbers must be sequential within a chapter
   - Validation in `ComicChapter` post-init
   - Error: Log warning if gaps detected

3. **Page Number Continuity**
   - Page numbers must be sequential within a chapter
   - Validation in `ComicChapter` post-init
   - Error: Log warning if gaps detected

4. **Backward Compatibility**
   - If `ComicScene.panels` is populated (old format), auto-convert to pages
   - Group panels into pages of 2-3 with default layout
   - Log migration warning

### Migration Strategy

```python
def migrate_panels_to_pages(scene: ComicScene) -> None:
    """Convert old panel-based scene to page-based scene"""
    if scene.panels and not scene.pages:
        # Group panels into pages of 2-3
        pages = []
        for i in range(0, len(scene.panels), 3):
            panel_group = scene.panels[i:i+3]
            if len(panel_group) == 1:
                # Single panel - pair with next or make 2-panel page
                continue
            
            page = ComicPage(
                page_number=len(pages) + 1,
                chapter=scene.chapter,
                scene_number=scene.scene_number,
                panel_arrangement="horizontal-3-panel" if len(panel_group) == 3 else "horizontal-2-panel",
                panel_borders="clean-sharp",
                panels=panel_group
            )
            pages.append(page)
        
        scene.pages = pages
        logger.warning(f"Migrated {len(scene.panels)} panels to {len(pages)} pages")
```

## Testing Strategy

### Unit Tests

**File**: `tests/models/test_comic_page.py`

```python
def test_comic_page_creation():
    """Test creating a ComicPage with 2-3 panels"""
    
def test_comic_page_panel_count_validation():
    """Test that pages must have 2-3 panels"""
    
def test_comic_page_layout_types():
    """Test all panel_arrangement literal values"""
    
def test_comic_scene_with_pages():
    """Test ComicScene with pages instead of panels"""
    
def test_backward_compatibility_migration():
    """Test auto-migration from panels to pages"""
```

### Integration Tests

**File**: `tests/integration/test_multi_panel_generation.py`

```python
async def test_parallel_generator_with_pages():
    """Test ParallelComicGenerator produces pages"""
    
async def test_chapterbuilder_crew_page_output():
    """Test chapterbuilder crew generates ComicPage objects"""
    
def test_page_statistics_calculation():
    """Test total_pages calculation in ComicBookOutput"""
```

### Task Description Tests

**File**: `tests/tasks/test_chapterbuilder_task.py`

```python
def test_chapterbuilder_task_includes_page_instructions():
    """Verify task description mentions page grouping"""
    
def test_chapterbuilder_task_references_panel_arrangements():
    """Verify task references panel_arrangements.md"""
```

## Implementation Plan

### Phase 1: Model Updates (Core)
1. Add `ComicPage` model to `cinema/models/comic_output.py`
2. Update `ComicScene` to use `pages` instead of `panels`
3. Add `total_pages` to `ComicBookOutput`
4. Add backward compatibility migration logic
5. Write unit tests for models

### Phase 2: Task Description Updates
1. Update `chapterbuilder` task in `plotbuilder/tasks.yaml`
2. Add instructions for grouping panels into pages
3. Add examples of `ComicPage` structure with layout metadata
4. Reference `knowledge/layouts/panel_arrangements.md`
5. Update `stripper` task similarly (if needed)

### Phase 3: ParallelComicGenerator Integration
1. Update `ParallelComicGenerator` to pass screenplay context
2. Ensure chapter processing produces pages, not individual panels
3. Update statistics calculation (total_pages)
4. Add logging for page generation

### Phase 4: Testing & Validation
1. Write integration tests
2. Test with real novel input
3. Validate page grouping logic
4. Verify layout metadata is populated correctly

### Phase 5: Documentation
1. Update README with new page-based structure
2. Document layout types and their use cases
3. Add examples of multi-panel page generation
4. Update API documentation

## Dependencies

- **Pydantic**: For model validation (min_length, max_length)
- **Existing Models**: `ComicPanel`, `ComicScene`, `ComicChapter`, `ComicBookOutput`
- **Knowledge Base**: `knowledge/layouts/panel_arrangements.md`
- **Task Files**: `cinema/agents/bookwriter/plotbuilder/tasks.yaml`
- **Generator**: `cinema/pipeline/parallel_comic_generator.py`

## Performance Considerations

1. **Memory**: Grouping panels into pages adds one layer of nesting (minimal impact)
2. **Processing**: No change to panel generation logic, only grouping step
3. **Serialization**: JSON output size increases slightly due to page metadata
4. **Backward Compatibility**: Migration adds minimal overhead (one-time per scene)

## Security Considerations

- No security implications (internal data structure change)
- Validation ensures data integrity (2-3 panels per page)

## Future Enhancements

1. **Dynamic Page Sizing**: Allow 1-panel splash pages for dramatic moments
2. **Layout Recommendation**: AI suggests best layout based on panel content
3. **Visual Preview**: Generate visual mockups of page layouts
4. **Layout Templates**: Pre-defined templates for common page compositions
5. **Panel Reordering**: Tools to rearrange panels across pages
