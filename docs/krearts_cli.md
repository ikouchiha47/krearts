# Krearts CLI - Incremental Workflow Interface

## Overview

Krearts provides a unified CLI for incremental content generation with `--continue` support at each stage.

## Architecture

```
WorkflowInterface (Abstract)
├── BookWorkflow
└── ScreenplayWorkflow (future)

Stages:
1. init      → Generate storyline (up to critique)
2. content   → Generate book/screenplay
3. chapters  → Generate comic chapters
4. pages     → Generate page images
```

## Installation

```bash
# Make krearts executable
chmod +x cinema/cmd/krearts.py

# Or use as module
python -m cinema.cmd.krearts
```

## Usage

### Stage 0: Generate Template (Optional)

```bash
# Generate detective mystery template
krearts template book --detective

# Or generic book template
krearts template book

# Specify output file
krearts template book --detective --output my_config.json

# Output:
# ✅ Template generated: book_config.json
#    Type: Detective Mystery
# Edit the template and use it:
#   krearts init book --config book_config.json
```

### Stage 1: Initialize (Generate Storyline)

```bash
# Initialize with defaults (simplest)
krearts init book

# Or use JSON config file
krearts init book --config examples/book_config.json

# Or customize via CLI
krearts init book \
    --characters "Detective Morgan, James Butler" \
    --killer "James Butler" \
    --victim "Victor Ashford"

# CLI options override config file
krearts init book --config config.json --killer "Different Killer"

# Output:
# ✅ Initialization complete
#    ID: abc12345
#    Output: output/book_abc12345
#    Characters: Detective Morgan, James Butler...
#    Killer: James Butler
#    Victim: Victor Ashford
#    Storyline: 5000 chars
#    Critique: PASS
# Next: krearts book abc12345 --continue
```

**Config File Format** (`book_config.json`):
```json
{
  "characters": "Detective Morgan, James Butler, Victor Ashford...",
  "relationships": "Butler served Ashford for 30 years...",
  "killer": "James Butler",
  "victim": "Victor Ashford",
  "accomplices": "Dr. Helen Price",
  "witnesses": "Margaret Ashford",
  "betrayals": "",
  "art_style": "Print Comic Noir Style",
  "genre": "Detective Mystery",
  "setting": "1940s England",
  "theme": "Revenge and class struggle"
}
```

### Stage 2: Generate Book Content

```bash
# Generate novel from storyline
krearts book detective_abc123 --continue

# Output:
# ✅ Book generation complete
#    Output: output/book_detective_abc123/novel.md
# Next: krearts book detective_abc123 chapters 1,5
#   or: krearts book detective_abc123 chapters --continue
```

### Stage 3: Generate Chapters

```bash
# Generate ALL chapters
krearts book abc12345 chapters all

# Generate specific chapters
krearts book abc12345 chapters 1,5

# Or continue from last chapter
krearts book abc12345 chapters --continue

# Output:
# ✅ Chapter generation complete
#    Chapters: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
#    Total generated: 10
# Next: krearts chapters abc12345 --pages 1,20
#   or: krearts chapters abc12345 --continue
```

### Stage 4: Generate Pages

```bash
# Generate specific pages
krearts chapters detective_abc123 --pages 1,20

# Or continue from last page
krearts chapters detective_abc123 --continue

# Output:
# ✅ Page generation complete
#    Pages: [1, 2, 3, ..., 20]
#    Total generated: 20
#    Output: output/book_detective_abc123/pages
```

## Workflow State

State is automatically saved at each stage:

```json
{
  "id": "detective_abc123",
  "type": "book",
  "current_stage": "pages",
  "storyline_done": true,
  "content_done": true,
  "chapters_generated": [1, 2, 3, 4, 5],
  "pages_generated": [1, 2, 3, ..., 20],
  "output_dir": "output/book_detective_abc123"
}
```

## Command Reference

### template

Generate config templates with examples.

```bash
krearts template book [OPTIONS]

Options:
  --detective        Generate detective mystery template
  --output PATH      Output file path (default: book_config.json)

Examples:
  krearts template book --detective
  krearts template book --output my_story.json
```

### init

Initialize workflow (generate storyline up to critique). Returns new workflow ID.

```bash
krearts init book [OPTIONS]

Options:
  --config PATH      JSON config file with all parameters
  --characters TEXT  Character descriptions (overrides config)
  --killer TEXT      Killer name (overrides config)
  --victim TEXT      Victim name (overrides config)

Returns:
  Workflow ID (e.g., abc12345)

Priority:
  CLI options > Config file > Defaults
```

### status

Show workflow status and progress.

```bash
krearts status <workflow_id>

Output:
  - Current stage
  - Chapters generated (with page counts)
  - Pages generated
  - Next steps
```

### book

Generate book content or chapters.

```bash
krearts book <workflow_id> [OPTIONS]

Options:
  --continue         Continue from saved state
  --chapters TEXT    Generate specific chapters (e.g., 1,5 or "all")
```

### chapters

Generate page images from chapters.

```bash
krearts chapters <workflow_id> [OPTIONS]

Options:
  --pages TEXT       Generate specific pages (e.g., 1,20)
  --continue         Continue from last page
```

## Examples

### Full Workflow

```bash
# 0. Generate template (optional)
krearts template book --detective

# 1. Edit book_config.json with your story details

# 2. Initialize with config (returns ID: abc12345)
krearts init book --config book_config.json

# 3. Check status
krearts status abc12345

# 4. Generate book
krearts book abc12345 --continue

# 5. Generate ALL chapters
krearts book abc12345 chapters all

# 6. Check status (shows chapters and pages per chapter)
krearts status abc12345

# 7. Generate pages incrementally
krearts chapters abc12345 --pages 1,10
krearts chapters abc12345 --continue  # generates page 11
krearts chapters abc12345 --continue  # generates page 12

# 8. Final status
krearts status abc12345
```

### Batch Generation

```bash
# Generate multiple chapters at once
krearts book detective_abc123 chapters 1,2,3,4,5

# Generate multiple pages at once
krearts chapters detective_abc123 --pages 1,2,3,4,5,6,7,8,9,10
```

### Resume After Interruption

```bash
# If generation was interrupted, just continue
krearts book detective_abc123 chapters --continue
krearts chapters detective_abc123 --continue
```

## API Translation

The CLI is designed to easily translate to REST API:

```python
# POST /api/v1/workflows/init
{
  "type": "book",
  "id": "detective_abc123",
  "characters": "...",
  "killer": "...",
  "victim": "..."
}

# POST /api/v1/workflows/{id}/content
{
  "continue_from": true
}

# POST /api/v1/workflows/{id}/chapters
{
  "chapters": [1, 5],
  "continue_from": false
}

# POST /api/v1/workflows/{id}/pages
{
  "pages": [1, 20],
  "continue_from": false
}
```

## Benefits

1. **Incremental**: Generate content step-by-step
2. **Resumable**: Continue from any stage with `--continue`
3. **Flexible**: Generate specific chapters/pages or continue sequentially
4. **Stateful**: Automatic state tracking and persistence
5. **API-ready**: Easy to translate to REST/GraphQL endpoints
6. **Unified**: Single interface for all content types (book, screenplay)

## Future Enhancements

1. **Screenplay workflow**: `krearts init screenplay --id action_xyz789`
2. **Parallel generation**: `krearts book {id} chapters 1-10 --parallel 3`
3. **Quality checks**: `krearts book {id} validate`
4. **Export formats**: `krearts book {id} export --format pdf`
5. **Web UI**: Visual interface for workflow management
