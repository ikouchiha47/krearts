# Pipeline Logging Configuration

## Overview

The cinema pipeline now supports configurable logging levels via the `LOG_LEVEL` environment variable in `.env`.

## Configuration

Set the logging level in your `.env` file:

```bash
LOG_LEVEL=DEBUG  # or INFO, WARNING, ERROR
```

## Log Levels

### INFO (Default)
- Pipeline stage progress
- Job completion status
- Cache hits
- Summary statistics

### DEBUG
- All INFO level logs
- **Full prompts for all generation stages:**
  - Character reference prompts (front, side, full_body)
  - Keyframe image prompts (first_frame, last_frame, transition_frame)
  - Video generation prompts (with negative prompts and duration)
- Screenplay hash changes
- Job invalidation details

## Example Output

### INFO Level
```
2025-11-08 16:47:01,820 - cinema.pipeline.movie_maker - INFO - === Stage 1: Character Reference Generation ===
2025-11-08 16:47:01,820 - cinema.pipeline.movie_maker - INFO - Generating 3 character images...
2025-11-08 16:47:01,820 - cinema.pipeline.movie_maker - INFO -   ✓ Generated 30-year-old woman - front
```

### DEBUG Level
```
2025-11-08 16:47:01,820 - cinema.pipeline.movie_maker - DEBUG - Character prompt for 30-year-old woman (front):
Close-up studio portrait photograph of 30-year-old woman, mixed ethnicity, fair skin, athletic build, dark brown hair.. 
50mm lens, shallow depth of field f/2.8. Neutral expression, looking directly at camera. Clean white background, professional studio lighting. Front view, centered, photorealistic, high detail. Aspect ratio: 1:1.

2025-11-08 16:47:01,820 - cinema.pipeline.movie_maker - DEBUG - Video prompt for S1_CHAOS (text_to_video):
Prompt: A fast, shaky, handheld cinematic shot begins as a close-up on the hands of ANNA...
Negative: cartoon, low quality, blurred background, soft lighting, calm, organized, smiling, green screen
Duration: 4.0s
```

## Usage

### Running with DEBUG logging
```bash
# Set in .env
LOG_LEVEL=DEBUG

# Run pipeline
PYTHONPATH=cinema uv run --active python cinema/pipeline/example_with_screenplay.py
```

### Running with INFO logging (less verbose)
```bash
# Set in .env
LOG_LEVEL=INFO

# Run pipeline
PYTHONPATH=cinema uv run --active python cinema/pipeline/example_with_screenplay.py
```

## Implementation Details

All example scripts now:
1. Load `.env` using `python-dotenv`
2. Read `LOG_LEVEL` environment variable
3. Configure `logging.basicConfig()` with the appropriate level
4. Log prompts at DEBUG level before generation

Files updated:
- `cinema/pipeline/example_with_screenplay.py`
- `cinema/pipeline/example_cricket.py`
- `cinema/pipeline/movie_maker.py`
