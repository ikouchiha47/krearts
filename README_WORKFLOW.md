# Krearts Workflow Guide

Complete guide for generating detective/mystery novels with comic book chapters using the incremental workflow system.

## Prerequisites

### 1. Environment Setup

Create a `.env` file in the project root:

```bash
# Required API Keys
GEMINI_API_KEY=your_gemini_api_key_here
OPENAI_API_KEY=your_openai_api_key_here

# Optional: Model Configuration
OPENAI_MODEL=gpt-4o
GEMINI_MODEL=gemini-2.5-flash-image
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

## Workflow Overview

The workflow has 4 incremental stages:

1. **init** - Generate storyline with plot + critique loop
2. **content** - Generate full novel/screenplay from storyline
3. **chapters** - Generate comic chapter JSONs with panel descriptions
4. **pages** - Generate actual panel images and composite into pages

Each stage can be run independently and resumed if interrupted.

---

## Complete Workflow Example

### Stage 1: Initialize (Generate Storyline)

Generate a config template:

```bash
python cinema/cmd/krearts.py template book --detective --output my_config.json
```

Or use the sci-fi example:

```bash
cp examples/scifi_config.json my_config.json
```

Edit `my_config.json` to customize your story, then initialize:

```bash
python cinema/cmd/krearts.py init book --config my_config.json
```

**What happens:**
- Generates unique workflow ID (e.g., `a1b2c3d4`)
- Runs DetectivePlotBuilder crew to create storyline
- Runs PlotCritique crew to validate (loops until PASS or max retries)
- Saves storyline and state to `output/book_{id}/`
- Saves input config to `output/book_{id}/input_config.json`

**Output:**
```
✅ Initialization complete
   ID: a1b2c3d4
   Output: output/book_a1b2c3d4
   Storyline: 5000 chars
   Critique: PASS

Next: krearts book a1b2c3d4 --continue
```

**Time:** ~5-10 minutes (depends on LLM speed and critique iterations)

---

### Stage 2: Generate Content (Novel/Screenplay)

```bash
python cinema/cmd/krearts.py book a1b2c3d4 --continue
```

**What happens:**
- Loads storyline from Stage 1
- Runs BookWriter crew to generate full novel (10 chapters)
- Saves novel to `output/book_{id}/novel.md`
- Updates workflow state

**Output:**
```
✅ Book generation complete
   Output: output/book_a1b2c3d4/novel.md

Next: krearts book a1b2c3d4 chapters all
```

**Time:** ~10-20 minutes (generates ~10,000 words)

---

### Stage 3: Generate Chapters (Comic Structure)

Generate all chapters:

```bash
python cinema/cmd/krearts.py book a1b2c3d4 chapters all
```

Or generate specific chapters:

```bash
python cinema/cmd/krearts.py book a1b2c3d4 chapters 1,3,5
```

Or continue from last chapter:

```bash
python cinema/cmd/krearts.py book a1b2c3d4 chapters --continue
```

**What happens:**
- Parses novel into chapters
- Runs ChapterBuilder crew for each chapter (parallel, max 3 concurrent)
- Generates comic structure: scenes → pages → panels
- Saves chapter JSONs to `output/book_{id}/chapter_XX.json`
- Each JSON contains panel descriptions, layouts, visual prompts

**Output:**
```
✅ Chapters generated: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
   Output: output/book_a1b2c3d4/
   Total generated: 10

Next: krearts chapters a1b2c3d4 --pages 1,10
```

**Time:** ~30-60 minutes for 10 chapters (parallel processing)

---

### Stage 4: Generate Pages (Images) [OPTIONAL]

Generate specific pages:

```bash
python cinema/cmd/krearts.py chapters a1b2c3d4 --pages 1,10
```

Or continue from last page:

```bash
python cinema/cmd/krearts.py chapters a1b2c3d4 --continue
```

**What happens:**
- Loads chapter JSONs
- For each page:
  - Generates individual panel images using Gemini
  - Composites panels into multi-panel page layout
  - Saves to `output/book_{id}/pages/chX_scY_pageZ.png`
- Updates workflow state with generated pages

**Output:**
```
✅ Pages generated: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
   Output: output/book_a1b2c3d4/pages/
   Total generated: 10
```

**Time:** ~2-3 minutes per page (depends on panel count)

---

## Check Workflow Status

At any time, check progress:

```bash
python cinema/cmd/krearts.py status a1b2c3d4
```

**Output:**
```
================================================================================
Workflow Status: a1b2c3d4
================================================================================
ID: a1b2c3d4
Type: book
Current Stage: chapters
Output Directory: output/book_a1b2c3d4

Progress:
  ✓ Storyline: Done
  ✓ Content: Done
  ✓ Chapters: 10 generated
     Chapters: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
       Chapter 1: 7 pages
       Chapter 2: 8 pages
       Chapter 3: 7 pages
       ...
  ✓ Pages: 25 generated
     Pages: [1, 2, 3, 4, 5, ...]

Next: krearts chapters a1b2c3d4 --continue
================================================================================
```

---

## Configuration Options

### Skipper Settings

Control which stages use mock/cached data vs actual generation:

```json
{
  "skipper": {
    "p": false,  // plotbuilder - false = generate, true = use mock
    "c": false,  // critique - false = generate, true = use mock
    "w": false,  // writer (book/screenplay) - false = generate, true = use mock
    "s": true    // storyboard - true = skip (handled separately in chapters stage)
  }
}
```

**Use cases:**
- **Full generation**: All false (except `s`)
- **Testing**: All true (uses cached mock data)
- **Resume from storyline**: `p: true, c: true, w: false` (skip plot/critique, generate book)

### Art Styles

Examples:
- `"Print Comic Noir Style with Halftones"`
- `"Cyberpunk Noir - neon lighting, high contrast"`
- `"Manga Style - clean lines, speed lines"`
- `"Watercolor Illustration - soft edges, muted colors"`

---

## Output Structure

```
output/book_{id}/
├── workflow_state.json          # Workflow progress tracking
├── input_config.json            # Original input configuration
├── novel.md                     # Generated novel (Stage 2)
├── chapter_01.json              # Comic structure for chapter 1 (Stage 3)
├── chapter_02.json
├── ...
├── chapter_10.json
└── pages/                       # Generated page images (Stage 4)
    ├── ch1_sc1_page1.png
    ├── ch1_sc1_page2.png
    └── ...
```

---

## Migrating Existing Detective Outputs

If you have existing `detective_{id}` outputs, migrate them:

```bash
python cinema/cmd/migrate_detective_to_workflow.py {detective_id}
```

This creates `workflow_state.json` and detects existing chapters/pages.

---

## Example: Complete Run

```bash
# 1. Generate config
python cinema/cmd/krearts.py template book --detective --output scifi.json

# 2. Edit scifi.json with your story details

# 3. Initialize (generate storyline)
python cinema/cmd/krearts.py init book --config scifi.json
# Output: ID: a1b2c3d4

# 4. Check status
python cinema/cmd/krearts.py status a1b2c3d4

# 5. Generate novel
python cinema/cmd/krearts.py book a1b2c3d4 --continue

# 6. Generate all chapters
python cinema/cmd/krearts.py book a1b2c3d4 chapters all

# 7. Check status again
python cinema/cmd/krearts.py status a1b2c3d4

# 8. (Optional) Generate first 10 pages
python cinema/cmd/krearts.py chapters a1b2c3d4 --pages 1,10
```

---

## Troubleshooting

### API Key Errors

```
ValueError: GEMINI_API_KEY not found in environment
```

**Solution:** Create `.env` file with API keys (see Prerequisites)

### Workflow Not Found

```
❌ Workflow not found: a1b2c3d4
```

**Solution:** Check the ID is correct, or run `ls output/` to see available workflows

### Out of Memory

If generating many chapters in parallel:

**Solution:** Reduce concurrency in `ParallelComicGenerator` (default: 3)

### Rate Limiting

If hitting API rate limits:

**Solution:** 
- Reduce concurrent requests
- Add delays between requests
- Use rate limiter (already integrated for Gemini)

---

## Advanced Usage

### Resume from Halt

If a stage is interrupted, resume from saved state:

```bash
# Resume book generation
python cinema/cmd/krearts.py book a1b2c3d4 --continue

# Resume chapter generation
python cinema/cmd/krearts.py book a1b2c3d4 chapters --continue

# Resume page generation
python cinema/cmd/krearts.py chapters a1b2c3d4 --continue
```

### Generate Specific Chapters

```bash
# Generate chapters 3, 5, 7
python cinema/cmd/krearts.py book a1b2c3d4 chapters 3,5,7
```

### Regenerate Failed Chapters

Chapters are idempotent - regenerating overwrites existing files:

```bash
# Regenerate chapter 5
python cinema/cmd/krearts.py book a1b2c3d4 chapters 5
```

---

## Performance Tips

1. **Parallel Processing**: Chapters generate in parallel (max 3 concurrent by default)
2. **Caching**: Already generated chapters/pages are skipped
3. **Incremental**: Each stage can be run independently
4. **Mock Mode**: Use skipper config to test without API calls

---

## File Formats

### Chapter JSON Structure

```json
{
  "title": "Chapter Title",
  "chapters": [{
    "chapter_number": 1,
    "chapter_title": "Title",
    "scenes": [{
      "scene_number": 1,
      "pages": [{
        "page_number": 1,
        "panel_arrangement": "vertical-3-panel",
        "panels": [{
          "panel_number": 1,
          "visual_description": "Detective Morgan stands in rain...",
          "dialogue": ["Morgan: 'The game begins.'"],
          "camera_angle": "low-angle",
          "lighting": "dramatic shadows"
        }]
      }]
    }]
  }]
}
```

---

## Next Steps

After generating chapters:
1. Review chapter JSONs for quality
2. Edit panel descriptions if needed
3. Generate page images (Stage 4)
4. Use `generate_comic_pages.py` for custom page generation
5. Composite pages into PDF or digital comic format

---

## Support

For issues or questions:
- Check workflow status: `krearts status {id}`
- Review logs in terminal output
- Check `output/book_{id}/workflow_state.json` for state
- Review `output/book_{id}/input_config.json` for configuration
