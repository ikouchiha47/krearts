# Image Generation Guide

## Overview

After generating a detective novel with chapter JSON files, you can generate comic book images in two ways:

1. **Multi-Panel Pages** (Recommended) - Generate complete comic book pages with multiple panels composited together
2. **Individual Panels** - Generate each panel as a separate image

---

## Option 1: Multi-Panel Comic Pages (Recommended)

Generate complete comic book pages with proper panel layouts (2-3 panels per page).

### Quick Start

```bash
# Generate first 2 pages of chapter 1 (default)
python -m cinema.cmd.examples.generate_comic_pages

# Generate pages for a specific detective ID
python -m cinema.cmd.examples.generate_comic_pages detective_abc123

# Generate pages for a specific chapter
python -m cinema.cmd.examples.generate_comic_pages detective_abc123 2

# Generate more pages (e.g., 5 pages)
python -m cinema.cmd.examples.generate_comic_pages detective_abc123 1 5
```

### Command Format

```bash
python -m cinema.cmd.examples.generate_comic_pages [DETECTIVE_ID] [CHAPTER_NUM] [MAX_PAGES]
```

**Arguments:**
- `DETECTIVE_ID` (optional): The detective output directory name (e.g., `detective_ce8f9a4a`)
  - Default: `detective_ce8f9a4a`
- `CHAPTER_NUM` (optional): Chapter number to process (1-10)
  - Default: `1`
- `MAX_PAGES` (optional): Maximum number of pages to generate
  - Default: `3`

### Output

Pages are saved to: `output/{DETECTIVE_ID}/pages/`

Filename format: `ch{chapter}_sc{scene}_page{page}.png`

Example: `ch1_sc1_page1.png`

Each page contains 2-3 panels arranged according to the layout:
- `vertical-3-panel`: 3 panels stacked vertically
- `horizontal-2-panel`: 2 panels side-by-side
- `horizontal-3-panel`: 3 panels side-by-side
- `zoom-progression`: Progressive zoom sequence
- etc.

---

## Option 2: Individual Panel Images

Generate each panel as a separate image (useful for testing or custom layouts).

### Quick Start

```bash
# Generate images for the first 10 panels of chapter 1 (default)
python -m cinema.cmd.examples.generate_panel_images_standalone

# Generate images for a specific detective ID
python -m cinema.cmd.examples.generate_panel_images_standalone detective_abc123

# Generate images for a specific chapter
python -m cinema.cmd.examples.generate_panel_images_standalone detective_abc123 2

# Generate more panels (e.g., 20 panels)
python -m cinema.cmd.examples.generate_panel_images_standalone detective_abc123 1 20
```

### Command Format

```bash
python -m cinema.cmd.examples.generate_panel_images_standalone [DETECTIVE_ID] [CHAPTER_NUM] [MAX_PANELS]
```

**Arguments:**
- `DETECTIVE_ID` (optional): The detective output directory name (e.g., `detective_ce8f9a4a`)
  - Default: `detective_ce8f9a4a`
- `CHAPTER_NUM` (optional): Chapter number to process (1-10)
  - Default: `1`
- `MAX_PANELS` (optional): Maximum number of panels to generate
  - Default: `10`

### Command Format

```bash
python -m cinema.cmd.examples.generate_panel_images_standalone [DETECTIVE_ID] [CHAPTER_NUM] [MAX_PANELS]
```

**Arguments:**
- `DETECTIVE_ID` (optional): The detective output directory name
  - Default: `detective_ce8f9a4a`
- `CHAPTER_NUM` (optional): Chapter number to process (1-10)
  - Default: `1`
- `MAX_PANELS` (optional): Maximum number of panels to generate
  - Default: `10`

### Output

Images are saved to: `output/{DETECTIVE_ID}/images/`

Filename format: `ch{chapter}_sc{scene}_pg{page}_panel{panel}.png`

Example: `ch1_sc1_pg1_panel1.png`

---

## Comparison

| Feature | Multi-Panel Pages | Individual Panels |
|---------|------------------|-------------------|
| **Output** | Complete comic pages | Separate panel images |
| **Layout** | Automatic composition | Manual composition needed |
| **File Size** | ~3MB per page | ~1.5-2MB per panel |
| **Use Case** | Final comic book | Testing, custom layouts |
| **Generation Time** | ~30-40s per page | ~8-10s per panel |
| **Recommended** | ✅ Yes | For advanced users |

---

## Examples

### Multi-Panel Pages

**Generate first 3 pages of chapter 1:**
```bash
python -m cinema.cmd.examples.generate_comic_pages detective_ce8f9a4a 1 3
```

**Generate all pages from chapter 2:**
```bash
python -m cinema.cmd.examples.generate_comic_pages detective_ce8f9a4a 2 10
```

### Individual Panels

**Generate first 10 panels from chapter 1:**
```bash
python -m cinema.cmd.examples.generate_panel_images_standalone detective_ce8f9a4a 1 10
```

**Generate all panels from chapter 2:**
```bash
python -m cinema.cmd.examples.generate_panel_images_standalone detective_ce8f9a4a 2 100
```

---

## Requirements

- Chapter JSON files must exist in `output/{DETECTIVE_ID}/chapter_{num:02d}.json`
- `GEMINI_API_KEY` must be set in your `.env` file
- Python packages: `google-genai`, `Pillow`, `python-dotenv`

## Generation Times

- **Multi-Panel Page**: ~30-40 seconds per page (generates 2-3 panels + composition)
- **Individual Panel**: ~8-10 seconds per panel

## Troubleshooting

**Error: "No such file or directory"**
- Check that the chapter JSON file exists
- Verify the detective ID is correct
- Ensure chapter number is formatted as `chapter_01.json`, `chapter_02.json`, etc.

**Error: "GEMINI_API_KEY not found"**
- Add `GEMINI_API_KEY=your_key_here` to your `.env` file
- Restart your terminal or run `source .env`

**Rate Limiting**
- The scripts include automatic rate limiting
- If you hit API limits, reduce `MAX_PAGES`/`MAX_PANELS` or wait a few minutes
- Gemini has a rate limit of ~60 requests per minute

**Image Quality Issues**
- Panel images are generated at high resolution (typically 1024x1024)
- Multi-panel pages are composited at 1200x1600 pixels
- Adjust `page_size` in `generate_comic_pages.py` for different dimensions

---

## Advanced Usage

### Custom Page Layouts

Edit `LAYOUT_CONFIGS` in `generate_comic_pages.py` to customize panel arrangements:

```python
LAYOUT_CONFIGS = {
    "horizontal-2-panel": {"rows": 1, "cols": 2, "ratios": [[1, 1]]},
    "vertical-3-panel": {"rows": 3, "cols": 1, "ratios": [[1], [1], [1]]},
    # Add custom layouts here
}
```

### Batch Processing

Generate all chapters at once:

```bash
for i in {1..10}; do
    python -m cinema.cmd.examples.generate_comic_pages detective_ce8f9a4a $i 10
done
```
