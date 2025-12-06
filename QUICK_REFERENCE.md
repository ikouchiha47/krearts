# Quick Reference Card

## 🎨 Art Reference System

### Add & Analyze Images
```bash
# Add images to directory
cp ~/images/*.jpg knowledge/art-styles/references/akira/

# Analyze all images
python manage_art_references.py analyze akira

# View results
python manage_art_references.py list akira
```

### Use in Code
```python
from cinema.workflow.art_style_references import ArtStyleReferenceManager

manager = ArtStyleReferenceManager()

# Context-aware (automatic)
refs = manager.load_references_for_scene(
    art_style="Akira",
    shot_type="wide",
    scene_type="action",
    max_references=3
)

# Manual (hash mapping)
ref = manager.get_reference_by_label("akira", "motion_lines")

# Simple (first N)
refs = manager.load_references("Akira", max_references=3)
```

---

## 📐 Grid Layouts

### Available Layouts
- `grid-8-panel` - 2x4 or 4x2 grid
- `grid-9-panel` - 3x3 grid
- `classic-grid-8` - Traditional 8-panel
- `classic-grid-9` - Traditional 9-panel (Watchmen style)
- `dynamic-8-panel` - Varied sizes (Akira style)
- `dynamic-9-panel` - Varied sizes (Blueberry style)

### Create Grid Page
```python
from cinema.models.comic_output import ComicPage, ComicPanel

# Create 9 panels
panels = [ComicPanel(...) for i in range(9)]

# Create page with 3x3 grid
page = ComicPage(
    page_number=1,
    chapter=1,
    scene_number=1,
    panel_arrangement="grid-9-panel",
    panels=panels
)
```

---

## 💬 Text Strategies

### Strategy 1: LLM-Generated (Fast)
```python
await workflow.generate_pages(
    pages=[1, 2, 3],
    gemini_text=True  # Generate with text
)
```

### Strategy 3: Post-Process (Recommended)
```python
await workflow.generate_pages(
    pages=[1, 2, 3],
    gemini_text=False  # Clean + add text after (default)
)
```

---

## 🏷️ Tag Categories

**Tags describe WHAT THE REFERENCE SHOWS, not what you're generating.**

| Category | Examples |
|----------|----------|
| **action** | motion_lines, speed_effects, impact, explosion |
| **art_technique** | halftone, ligne_claire, painterly, chromatic_aberration |
| **color_style** | high_contrast, vibrant_colors, noir, neon |
| **lighting** | dramatic, soft_diffused, rim_lighting |
| **composition** | rule_of_thirds, centered, symmetrical, diagonal |
| **subject_matter** | character_design, environment, mechanical_detail |
| **visual_density** | sparse, moderate, dense, cluttered |
| **texture** | smooth, rough, grainy, paper_texture |

---

## 🔧 CLI Commands

```bash
# Analyze images
python manage_art_references.py analyze <style> [directory]

# List references
python manage_art_references.py list <style>

# Show details
python manage_art_references.py show <style> <ref_id>

# Search
python manage_art_references.py search <style> --shot_type=wide

# List tags
python manage_art_references.py tags <style>
```

---

## 📂 Directory Structure

```
knowledge/art-styles/references/
├── akira/
│   ├── motion_lines.jpg
│   ├── impact_panel.jpg
│   └── akira_references.json  # Generated
├── spiderverse/
│   ├── halftone_texture.jpg
│   └── spiderverse_references.json
└── arcane/
    ├── painterly_portrait.jpg
    └── arcane_references.json
```

---

## 🎯 Workflow Example

```bash
# 1. Add images
cp ~/Downloads/akira_*.jpg knowledge/art-styles/references/akira/

# 2. Analyze
python manage_art_references.py analyze akira

# 3. Check results
python manage_art_references.py list akira

# 4. Use in generation
python your_generation_script.py --style=akira --use-references
```

---

## 📖 Full Documentation

- **HOW_TO_USE.md** - ⭐ START HERE - Step-by-step usage guide
- **TAG_PHILOSOPHY.md** - Understanding input vs output tags
- **ART_REFERENCE_SYSTEM_GUIDE.md** - Complete reference system guide
- **ART_STYLE_AND_TEXT_GUIDE.md** - Style + text strategies
- **GRID_LAYOUT_USAGE.md** - Grid layout guide
- **IMPLEMENTATION_SUMMARY.md** - What we built
