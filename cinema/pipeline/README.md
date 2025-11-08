# Cinema Pipeline

A resumable, job-tracked pipeline for automated movie generation from scripts.

## Architecture

The pipeline follows a multi-stage approach with SQLite-backed job tracking for resumability:

```
Script Input
    ↓
[Stage 0] Screenplay Generation
    ↓
[Stage 1] Character Reference Images
    ↓
[Stage 2] Keyframe Image Generation
    ↓
[Stage 3] Video Generation
    ↓
[Stage 4] Post-Production & Assembly
    ↓
Final Movie Output
```

## Core Components

### 1. Pipeline (`pipeline.py`)

Generic pipeline abstraction for chaining async operations:

```python
pipeline = (
    Pipeline()
    .then(StageA())
    .then(StageB())
    .then(StageC())
)

result = await pipeline.execute(input)
```

### 2. State Management (`state.py`)

`PipelineState` carries all data between stages:
- Screenplay data
- File paths for all assets
- Job tracking
- Stage completion flags

### 3. Job Tracking (`job_tracker.py`)

SQLite-backed persistence for:
- Job status (pending, in_progress, completed, failed)
- Progress tracking
- Resumability from any point
- Error logging

### 4. Pipeline Stages (`movie_maker.py`)

#### ScreenplayBuilder
- Generates structured screenplay from script
- Extracts all generation stages
- Creates jobs for subsequent stages

#### VisualCharacterBuilder
- Generates character reference images (front, side, full_body)
- Saves to `{base_dir}/characters/`

#### KeyframeGenerator
- Generates keyframe images for scenes
- Creates first_frame, last_frame, transition_frame
- Saves to `{base_dir}/images/`

#### VideoGenerator
- Generates videos using different strategies:
  - Text-to-video
  - Image-to-video
  - First+last frame interpolation
- Saves to `{base_dir}/videos/`

#### VideoProcessingPipeline
- Applies post-production effects
- Handles transitions
- Stitches final video
- Saves to `{base_dir}/output/`

### 5. MovieMaker

Main orchestrator that:
- Manages the full pipeline
- Handles resumability
- Tracks progress
- Saves state to database

## Usage

### Basic Generation

```python
from cinema.pipeline import MovieMaker
from cinema.agents.scriptwriter.crew import ScriptWriter, Enhancer

# Initialize
writer = ScriptWriter()
enhancer = Enhancer()
maker = MovieMaker(writer, enhancer)

# Generate movie
state = await maker.generate(
    script="Your script here...",
    movie_id="my_movie_v1",  # Optional
    base_dir="./output"
)

print(f"Final video: {state.get_final_video_path()}")
```

### Resume Generation

If generation fails or is interrupted:

```python
# Resume from where it left off
state = await maker.resume(
    movie_id="my_movie_v1",
    base_dir="./output"
)
```

### Check Status

```python
status = maker.get_status("my_movie_v1")
print(f"Progress: {status['progress']:.1f}%")
print(f"Completed: {status['completed']}/{status['total']}")
```

## Directory Structure

```
output/
└── {movie_id}/
    ├── characters/
    │   ├── char_1_front.png
    │   ├── char_1_side.png
    │   └── char_1_full_body.png
    ├── images/
    │   ├── scene_1_first_frame.png
    │   ├── scene_1_last_frame.png
    │   └── scene_1_transition_frame.png
    ├── videos/
    │   ├── scene_1.mp4
    │   ├── scene_1_processed.mp4
    │   └── scene_2.mp4
    ├── audio/
    │   └── scene_1.mp3
    └── output/
        └── {movie_id}_final.mp4
```

## Job Tracking

Jobs are stored in SQLite with:
- Unique ID
- Type (screenplay, character, image, video, post_production)
- Status (pending, in_progress, completed, failed)
- Scene/character associations
- Error messages
- Output paths
- Timestamps

This allows:
- **Resumability**: Pick up exactly where you left off
- **Parallel execution**: Run multiple jobs concurrently (future)
- **Rate limiting**: Handle API throttling gracefully
- **Progress tracking**: Monitor generation in real-time
- **Error recovery**: Retry failed jobs without redoing successful ones

## Integration with Extractors

The pipeline uses `cinema.transformers.screenplay_extractors` to:
1. Extract character data → Create character jobs
2. Extract image specs → Create image jobs
3. Extract video specs → Create video jobs
4. Extract post-production specs → Create post-production jobs

Each extractor provides structured data for its stage:
- `CharacterGenerationStage`
- `ImageGenerationStage`
- `VideoGenerationStage`
- `PostProductionStage`

## Future Enhancements

- [ ] Parallel job execution with worker pools
- [ ] Rate limiting and throttling
- [ ] Retry logic with exponential backoff
- [ ] Real-time progress webhooks
- [ ] Cloud storage integration
- [ ] Distributed execution across machines
- [ ] Cost tracking per job
- [ ] Quality validation checkpoints

## Example

See `example.py` for complete usage examples.
