# Detective Pipeline Image Prompt Structure

## Overview

The detective pipeline generates comic panel images using structured prompts built from the `PanelPrompt` model.

## Prompt Construction Flow

```
DetectiveMaker.generate()
  ↓
  _create_panel_jobs()
    ↓
    For each character.actions_and_locations:
      ↓
      action.panel.to_image_prompt(art_style)
        ↓
        Returns structured prompt string
        ↓
        Stored in job.metadata["prompt"]
  ↓
PanelImageGenerator.run()
  ↓
  For each job:
    ↓
    prompt = job.metadata["prompt"]
    ↓
    gemini.generate_content(prompt=prompt)
```

## PanelPrompt Model

Located in `cinema/models/detective_output.py`:

```python
class PanelPrompt(BaseModel):
    """Structured prompt for generating a single comic panel"""
    
    shot_type: str  # e.g., "CLOSE_UP", "WIDE_SHOT", "MEDIUM_SHOT"
    visual_description: str  # Detailed scene description
    dialogue: Optional[str]  # Character dialogue or narrator caption
    sound_effects: Optional[str]  # e.g., "POW!", "BANG!"
    emotional_tone: str  # e.g., "tense", "mysterious", "dramatic"
    orientation: Literal["Landscape", "Portrait"]  # Image aspect ratio
```

## to_image_prompt() Method

```python
def to_image_prompt(self, art_style: str = "Noir Comic Book Style") -> str:
    """Convert to full image generation prompt"""
    prompt = f"A single comic book panel in {art_style}. "
    prompt += f"{self.shot_type.replace('_', ' ').title()} shot. "
    prompt += f"{self.visual_description}. "
    prompt += f"Emotional tone: {self.emotional_tone}. "

    if self.dialogue:
        prompt += f"Caption box: '{self.dialogue}'. "

    if self.sound_effects:
        prompt += f"Sound effect: '{self.sound_effects}'. "

    prompt += f"{self.orientation}."

    return prompt
```

## Example Prompt

### Input:
```python
panel = PanelPrompt(
    shot_type="CLOSE_UP",
    visual_description="Detective Morgan examining a bloody knife in dim lighting",
    dialogue="This changes everything...",
    sound_effects=None,
    emotional_tone="tense and foreboding",
    orientation="Landscape"
)

prompt = panel.to_image_prompt("Noir Comic Book Style")
```

### Output:
```
A single comic book panel in Noir Comic Book Style. Close Up shot. Detective Morgan examining a bloody knife in dim lighting. Emotional tone: tense and foreboding. Caption box: 'This changes everything...'. Landscape.
```

## Job Metadata Structure

When creating panel generation jobs in `_create_panel_jobs()`:

```python
job = Job(
    id=f"panel_{character_name}_{action_index:02d}",
    type=JobType.IMAGE,
    status=JobStatus.PENDING,
    metadata={
        "character_name": character.name,
        "action_index": idx,
        "timestamp": action.timestamp,
        "action": action.action,
        "location": action.location,
        "prompt": prompt,  # Full structured prompt from to_image_prompt()
        "art_style": self.art_style,
        "shot_type": action.panel.shot_type,
        "emotional_tone": action.panel.emotional_tone,
        "orientation": action.panel.orientation,
    },
)
```

## Image Generation with Rate Limiting

```python
class PanelImageGenerator:
    async def run(self, state: PipelineState) -> PipelineState:
        # Get pending jobs
        pending = [j for j in image_jobs if j.status == PENDING]
        
        # Create rate limiter
        rate_limiter = RateLimiterManager()
        gemini = GeminiMediaGen(rate_limiter=rate_limiter)
        
        # Use semaphore for concurrent requests
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def generate_panel(job: Job):
            async with semaphore:
                prompt = job.metadata["prompt"]
                response = await gemini.generate_content(prompt=prompt)
                gemini.render_image(output_path, response)
        
        # Generate all panels concurrently
        await asyncio.gather(*[generate_panel(job) for job in pending])
```

## Rate Limiting

The pipeline uses two levels of rate limiting:

1. **Semaphore** (Concurrency Control):
   - Limits number of simultaneous API calls
   - Default: 3 concurrent requests
   - Configurable via `--max-concurrent` flag

2. **RateLimiterManager** (API Quota Management):
   - Tracks API call rates per model
   - Implements exponential backoff
   - Prevents quota violations
   - Shared with movie_maker pipeline

## Customization

### Change Art Style:
```bash
python cinema/cmd/examples/example_detective.py --style "Cyberpunk Comic Style"
```

### Adjust Concurrency:
```bash
python cinema/cmd/examples/example_detective.py --max-concurrent 5
```

### Modify Prompt Template:

Edit `cinema/models/detective_output.py`:

```python
def to_image_prompt(self, art_style: str = "Noir Comic Book Style") -> str:
    # Add more details
    prompt = f"A highly detailed comic book panel in {art_style}. "
    prompt += f"Professional comic book illustration. "
    prompt += f"{self.shot_type.replace('_', ' ').title()} shot. "
    # ... rest of prompt
    return prompt
```

## Output Files

Generated images are saved to:
```
./output/{movie_id}/images/{character_name}_{action_index:02d}.png
```

Example:
```
./output/detective_abc123/images/
  ├── Detective_Morgan_00.png
  ├── Detective_Morgan_01.png
  ├── Victor_Ashford_00.png
  ├── James_Butler_00.png
  └── ...
```

## Flow State Output

The complete flow state (including all prompts) is saved to:
```
./output/flow_states/storybuilder_output_{timestamp}.json
```

This JSON file contains:
- All panel prompts
- Character profiles
- Narrative structure
- Plot structure
- Timestamps and metadata

## Related Files

- `cinema/models/detective_output.py` - PanelPrompt model and to_image_prompt()
- `cinema/pipeline/detective_maker.py` - _create_panel_jobs() and PanelImageGenerator
- `cinema/providers/gemini.py` - GeminiMediaGen with rate limiting
- `cinema/utils/rate_limiter.py` - RateLimiterManager
