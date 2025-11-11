# Detective Comic Strip Generator

## Overview

The detective comic strip generator creates comic panels from plot constraints using a multi-stage pipeline with validation checkpoints.

## Pipeline Stages

1. **Plot Structure Generation** - Creates logical plot structure from constraints
2. **Narrative Generation** - Generates character profiles, backstories, and storyline
3. **Storyline Validation** - Review checkpoint before image generation
4. **Panel Job Creation** - Creates image generation jobs
5. **Panel Image Generation** - Generates comic panel images

## Usage

### Step 1: Validate Storyline (Recommended)

Run with `--validate-only` to generate the storyline and review it before creating images:

```bash
python cinema/cmd/examples/example_detective.py --validate-only
```

This will:
- Generate plot structure
- Generate narrative with characters and panels
- Save storyline analysis to `output/detective_XXXXX/storyline_analysis.txt`
- **Stop before image generation**

### Step 2: Review the Output

Check the generated storyline analysis file:

```bash
cat output/detective_XXXXX/storyline_analysis.txt
```

The file contains:
- Complete storyline
- Narrative structure used
- Character profiles with backstories
- Action timeline for each character
- Panel descriptions
- Summary statistics

### Step 3: Generate Images

Once you're happy with the storyline, run without `--validate-only` to generate images:

```bash
python cinema/cmd/examples/example_detective.py
```

Or resume from the existing state:

```bash
python cinema/cmd/examples/example_detective.py --resume detective_XXXXX
```

## Command Line Options

- `--validate-only` - Only validate storyline, don't generate images
- `--resume MOVIE_ID` - Resume from existing movie_id
- `--style STYLE` - Art style for comic (default: "Noir Comic Book Style")

## Art Styles

Available styles:
- "Noir Comic Book Style" (default)
- "Cyberpunk Comic Style"
- "Anime & Manga Style"
- "Pop Art Comic Style"
- "Print Comics Art"
- "Print Comics + Noir"
- "Pixel Art Comic Panel (16-bit)"
- "Pencil Sketch Comic Style"

## Example Workflow

```bash
# 1. Generate and validate storyline
python cinema/cmd/examples/example_detective.py --validate-only

# Output:
# Detective Comic ID: detective_abc123
# ...
# VALIDATION COMPLETE - Review output before proceeding
# Storyline analysis: output/detective_abc123/storyline_analysis.txt

# 2. Review the storyline
cat output/detective_abc123/storyline_analysis.txt

# 3. If satisfied, generate images
python cinema/cmd/examples/example_detective.py --resume detective_abc123

# Or start fresh without validation
python cinema/cmd/examples/example_detective.py
```

## Output Structure

```
output/
└── detective_XXXXX/
    ├── storyline_analysis.txt    # Human-readable storyline review
    ├── images/                    # Generated panel images
    │   ├── Detective_Morgan_00.png
    │   ├── Detective_Morgan_01.png
    │   └── ...
    └── state.json                 # Pipeline state for resuming
```

## Customizing the Story

Edit `example_detective.py` to customize:

- **Characters**: Modify the `characters` list
- **Plot Constraints**: Change killer, victim, witnesses, etc.
- **Art Style**: Use `--style` flag or modify default

Example:

```python
characters = [
    Character("Detective Sarah Chen", "detective"),
    Character("Marcus Blackwood", "victim"),
    Character("Elena Frost", "killer", faction="corporate"),
    Character("Dr. James Wilson", "witness"),
]

constraints = PlotConstraints(
    killer="Elena Frost",
    victim="Marcus Blackwood",
    accomplices=[],
    witnesses=[("Dr. James Wilson", "saw the meeting")],
    # ... more constraints
)
```
