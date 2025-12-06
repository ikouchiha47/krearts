# Krearts Quick Start

Generate a complete detective novel with comic chapters in 4 commands.

## Setup (One Time)

```bash
# 1. Copy environment template
cp .env.example .env

# 2. Edit .env and add your API keys
# OPENAI_API_KEY=sk-proj-...
# GEMINI_API_KEY=...

# 3. Install dependencies
pip install -r requirements.txt
```

## Generate Your First Book

```bash
# 1. Create config from template
python cinema/cmd/krearts.py template book --detective --output my_story.json

# 2. Edit my_story.json (change characters, setting, etc.)

# 3. Initialize (generates storyline) - ~5-10 min
python cinema/cmd/krearts.py init book --config my_story.json
# Output: ID: abc123

# 4. Generate novel - ~10-20 min
python cinema/cmd/krearts.py book abc123 --continue

# 5. Generate comic chapters - ~30-60 min
python cinema/cmd/krearts.py book abc123 chapters all

# 6. Check results
python cinema/cmd/krearts.py status abc123
```

## Output

Your generated content is in `output/book_abc123/`:
- `novel.md` - Full novel text
- `chapter_01.json` through `chapter_10.json` - Comic panel descriptions
- `input_config.json` - Your configuration (for reproducibility)

## Optional: Generate Images

```bash
# Generate first 10 pages (2-3 min per page)
python cinema/cmd/krearts.py chapters abc123 --pages 1,10
```

Images saved to `output/book_abc123/pages/`

## Use Existing Example

```bash
# Use the sci-fi example
python cinema/cmd/krearts.py init book --config examples/scifi_config.json
```

## Next Steps

- See `README_WORKFLOW.md` for complete documentation
- Edit chapter JSONs to refine panel descriptions
- Generate more pages incrementally
- Customize art style in config

## Common Commands

```bash
# Check status
python cinema/cmd/krearts.py status {id}

# Generate specific chapters
python cinema/cmd/krearts.py book {id} chapters 1,3,5

# Continue from last chapter
python cinema/cmd/krearts.py book {id} chapters --continue

# Generate specific pages
python cinema/cmd/krearts.py chapters {id} --pages 1,20

# Continue from last page
python cinema/cmd/krearts.py chapters {id} --continue
```

## Troubleshooting

**API Key Error?**
- Check `.env` file exists and has valid keys

**Workflow Not Found?**
- Use correct ID from init output
- Check `ls output/` for available workflows

**Too Slow?**
- Skip image generation (chapters only)
- Use mock mode in config: `"skipper": {"p": true, "c": true}`

## Time Estimates

- **Storyline (init)**: 5-10 minutes
- **Novel (content)**: 10-20 minutes
- **Chapters (all 10)**: 30-60 minutes
- **Pages (per page)**: 2-3 minutes

**Total for complete book (no images)**: ~45-90 minutes
**Total with 68 pages of images**: ~3-5 hours
