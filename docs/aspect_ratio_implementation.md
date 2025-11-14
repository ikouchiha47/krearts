# Aspect Ratio Implementation

## Overview

Added aspect ratio support to ensure consistent panel and page generation based on layout type.

## Changes Made

### 1. Knowledge Base Update
**File**: `knowledge/layouts/panel_arrangements.md`

Added aspect ratio guidelines:
- **Horizontal layouts** (horizontal-2-panel, horizontal-3-panel): 16:9 (Landscape)
- **Vertical layouts** (vertical-2-panel, vertical-3-panel, zoom-progression): 9:16 (Portrait)
- **Square/Balanced layouts** (dynamic-grid, fractured-overlapping): 1:1 or 4:3
- **Dominant panel layouts** (cross-over-bleed, shattered-exploded): 16:9 or 3:2

### 2. Pydantic Model Updates
**File**: `cinema/models/comic_output.py`

Added fields:
- `ComicPanel.aspect_ratio`: Optional[str] - Panel aspect ratio (e.g., '16:9', '9:16')
- `ComicPage.page_aspect_ratio`: Optional[str] - Page aspect ratio

### 3. Schema Update
**File**: `cinema/agents/bookwriter/crew.py`

Updated `ChapterBuilderSchema`:
```python
class ChapterBuilderSchema(BaseModel):
    screenplay: str
    examples: str
    chapter_id: int
    chapter_content: str
    art_style: str
    aspect_ratio: Optional[str] = "16:9"  # Default to landscape
```

### 4. Task Prompt Update
**File**: `cinema/agents/bookwriter/plotbuilder/tasks.yaml`

Added aspect ratio instructions:
- Choose panel arrangements based on target aspect ratio
- Set `page_aspect_ratio` on ComicPage
- Set `aspect_ratio` on ComicPanel
- Include aspect ratio in visual_description orientation

### 5. Pipeline Update
**File**: `cinema/pipeline/parallel_comic_generator.py`

Pass aspect_ratio to ChapterBuilder:
```python
inputs = ChapterBuilderSchema(
    ...
    aspect_ratio="16:9",  # Default to landscape
)
```

## Usage

### Static Aspect Ratio (Current Implementation)

```python
# In parallel_comic_generator.py
inputs = ChapterBuilderSchema(
    screenplay=self.screenplay,
    examples=ComicStripStoryBoarding.load_examples(),
    chapter_id=chapter.number,
    chapter_content=chapter_content,
    art_style=art_style,
    aspect_ratio="16:9",  # or "9:16", "1:1", etc.
)
```

### Future: Dynamic Aspect Ratio (Seed-based)

For future implementation with seed-based aspect ratio:

1. **First chapter** (seed):
   - Pass `aspect_ratio=""` (empty)
   - LLM chooses best aspect ratio based on content
   - Extract aspect ratio from generated output

2. **Subsequent chapters**:
   - Pass aspect ratio from first chapter
   - Ensures consistency across all chapters
   - Can run in parallel

```python
# Pseudo-code for future implementation
if chapter_num == 1:
    # Seed chapter - let LLM choose
    aspect_ratio = ""
    result = await generate_chapter(aspect_ratio=aspect_ratio)
    seed_aspect_ratio = extract_aspect_ratio(result)
else:
    # Use seed aspect ratio
    aspect_ratio = seed_aspect_ratio
    result = await generate_chapter(aspect_ratio=aspect_ratio)
```

## Aspect Ratio Guidelines

| Layout Type | Aspect Ratio | Orientation | Use Case |
|-------------|--------------|-------------|----------|
| horizontal-2-panel | 16:9 | Landscape | Dialogue, action |
| horizontal-3-panel | 16:9 | Landscape | Wide shots, sequences |
| vertical-2-panel | 9:16 | Portrait | Character focus, descent |
| vertical-3-panel | 9:16 | Portrait | Zoom progression |
| zoom-progression | 9:16 | Portrait | Building suspense |
| dynamic-grid | 1:1 or 4:3 | Square/Landscape | Balanced composition |
| fractured-overlapping | 1:1 | Square | Chaos, impact |
| cross-over-bleed | 16:9 | Landscape | Dramatic reveals |
| shattered-exploded | 16:9 | Landscape | Psychological distress |

## Benefits

1. **Consistency**: All panels in a chapter use the same aspect ratio
2. **Layout Optimization**: Panel arrangements match the aspect ratio
3. **Image Generation**: Gemini can generate images with correct dimensions
4. **Future-proof**: Ready for seed-based dynamic aspect ratio selection
