# Cinema - AI Comic Book Generator

Cinema is an AI-powered comic book generation system that transforms story ideas into fully illustrated comic books with consistent characters, professional layouts, and classic comic book styling.

## What It Does

Cinema takes a story concept and generates:
- **Storyline** with plot structure, characters, and narrative arcs
- **Full novel** with detailed chapters and scenes
- **Comic book chapters** with panel-by-panel breakdowns
- **Character reference sheets** for visual consistency
- **Illustrated pages** with proper comic book layouts
- **Text overlays** with dialogue and narration in classic caption boxes

## The Process

```mermaid
graph LR
    A[Story Config] --> B[Storyline Generation]
    B --> C[Novel Writing]
    C --> D[Chapter Structuring]
    D --> E[Character References]
    E --> F[Page Generation]
    F --> G[Text Overlays]
    G --> H[Complete Comic Book]
```

**Flow:**
1. **Config** → Define characters, setting, theme, art style
2. **Storyline** → AI generates plot with critique loop
3. **Novel** → Expands storyline into full narrative
4. **Chapters** → Breaks novel into comic book structure (scenes/pages/panels)
5. **Characters** → Generates reference images for consistency
6. **Pages** → Creates illustrated panels and composites into pages
7. **Text** → Adds dialogue/narration in comic book caption boxes

## Sample Stories

Check out complete generated stories in the [releases/](releases/) folder:
- **[Sci-Fi Mystery](releases/scifi/)** - "RAINGLASS" - Cyberpunk noir on an orbital station
- **[Classic Noir](releases/noir/)** - "Blood Red Lotus" - 1947 LA detective story

## Getting Started

### Prerequisites

```bash
# Install dependencies
pip install -r requirements.txt

# Set up API keys in .env
GEMINI_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here
```

### Quick Start

```bash
# 1. Initialize a new story
python cinema/cmd/krearts.py init book --config examples/noir_detective_config.json
# Output: ID: abc123

# 2. Generate the novel
python cinema/cmd/krearts.py book abc123 --continue

# 3. Generate character references
python cinema/cmd/krearts.py characters abc123

# 4. Generate comic chapters
python cinema/cmd/krearts.py book abc123 --chapters 1,2,3

# 5. Generate illustrated pages (with automatic text overlays)
python cinema/cmd/krearts.py chapters abc123 --pages all
```

## Exploring the Codebase

### Entry Point
**Main CLI**: `cinema/cmd/krearts.py`
- Unified interface for all generation stages
- Handles workflow state management
- Coordinates between different crews and generators

### Key Components

**Workflows** (`cinema/workflow/`)
- `book_workflow.py` - Main orchestration logic
- `character_manager.py` - Character reference generation
- `interface.py` - Workflow state management

**AI Crews** (`cinema/agents/bookwriter/`)
- `plotbuilder/` - Story structure generation
- `critique/` - Plot validation
- `writer/` - Novel generation
- `storyboard/` - Comic chapter structuring

**Generators** (`cinema/pipeline/`)
- `parallel_comic_generator.py` - Parallel chapter processing
- `detective_maker.py` - Detective story specialization

**Providers** (`cinema/providers/`)
- `gemini.py` - Gemini API for image generation

**Utilities** (`cinema/utils/`)
- `text_overlay.py` - Comic book text rendering

## Commands

### Initialize
```bash
# Create new story
krearts init book --config <config.json>

# Generate config template
krearts template book --detective --output config.json
```

### Generate Content
```bash
# Generate novel
krearts book <id> --continue

# Generate chapters
krearts book <id> --chapters 1,2,3
krearts book <id> --chapters all
krearts book <id> --chapters --continue
```

### Generate Images
```bash
# Generate character references
krearts characters <id>

# Generate pages
krearts chapters <id> --pages 1,10
krearts chapters <id> --pages all
krearts chapters <id> --continue
```

### Utilities
```bash
# Check status
krearts status <id>

# Read content
krearts read <id> --storyline
krearts read <id> --novel
krearts read <id> --chapter 1
```

## Configuration

Example config (`examples/noir_detective_config.json`):

```json
{
  "characters": "Jack Malone (45, detective), Veronica Steele (32, femme fatale)",
  "killer": "Tommy 'The Knife' Russo",
  "victim": "Eddie Chen",
  "art_style": "Classic noir - high contrast, dramatic shadows, rain-slicked streets",
  "aspect_ratio": "4:5",
  "genre": "Noir Detective Mystery",
  "setting": "1947, Los Angeles",
  "theme": "Moral ambiguity, corruption, redemption",
  "tone": "Dark, cynical, atmospheric"
}
```

## Features

- ✅ **4:5 Portrait Aspect Ratio** - Optimized for modern comic book format
- ✅ **Character Consistency** - Reference-based generation with seeding chain
- ✅ **Parallel Processing** - Generate multiple chapters simultaneously
- ✅ **Incremental Workflow** - Resume from any stage
- ✅ **Text Overlays** - Automatic caption boxes in classic comic style
- ✅ **Art Style Control** - Configurable visual style per story
- ✅ **Quality Analysis** - Built-in image analysis tools

## Output

Each story generates:
- `novel.md` - Full narrative text
- `chapter_XX.json` - Comic structure with panel descriptions
- `characters/` - Character reference images (front, side, full_body, back)
- `pages/` - Illustrated comic book pages
- `pages/*_with_text.png` - Pages with dialogue/narration overlays

## Documentation

- [Image Generation Guide](docs/image_generation_guide.md)
- [Aspect Ratio Implementation](docs/aspect_ratio_implementation.md)
- [Text Overlay Styles](docs/comic_text_styles.md)
- [Flow Pause/Resume](docs/flow_pause_resume.md)

## Troubleshooting

**API Rate Limits**: Gemini has rate limits. If you hit them, the system will retry automatically or you can resume with `--continue`.

**Missing Text Overlays**: Text overlays are generated automatically during page generation. If missing, check that `cinema/utils/text_overlay.py` is accessible.

**Character Inconsistency**: Ensure character references are generated before pages. Use `krearts characters <id>` first.

**Memory Issues**: For large stories, generate chapters in batches rather than all at once.

## Sample Output

See complete generated stories with images in [releases/README.md](releases/README.md)
