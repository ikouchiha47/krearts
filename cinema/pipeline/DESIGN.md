# Pipeline Design Document

## Overview

The cinema pipeline is a **resumable, job-tracked system** for automated movie generation. It transforms a text script into a final video through multiple stages, with SQLite-backed persistence allowing recovery from failures and rate limiting.

## Design Principles

1. **Resumability**: Every stage can be resumed from any point
2. **Job Tracking**: All work is tracked as discrete jobs in SQLite
3. **State Management**: Pipeline state flows through stages immutably
4. **Composability**: Stages are independent `Runner` implementations
5. **Minimal Implementation**: Only essential functionality, no over-engineering

## Architecture

### Core Abstractions

#### 1. Runner[IT, OT]
Generic interface for any async transformation:
```python
class Runner(Generic[IT, OT]):
    async def run(self, inputs: IT) -> OT: ...
```

#### 2. Pipeline[IT, OT]
Chains runners together:
```python
pipeline = (
    Pipeline()
    .then(StageA())
    .then(StageB())
    .then(StageC())
)
```

#### 3. PipelineState
Immutable state object passed between stages containing:
- Movie ID and directory paths
- Screenplay data (structured JSON)
- Job list with status tracking
- Stage completion flags

#### 4. JobTracker
SQLite persistence layer for:
- Job status and metadata
- Pipeline state snapshots
- Progress tracking
- Error logging

## Pipeline Stages

### Stage 0: Screenplay Generation
**Input**: Script text + PipelineState  
**Output**: PipelineState with screenplay + jobs created  
**Jobs Created**: Character, Image, Video, Post-production jobs

**Process**:
1. Generate screenplay using ScriptWriter crew
2. Enhance with Enhancer crew
3. Extract all generation stages using `extract_all_stages()`
4. Create jobs for all subsequent stages
5. Save screenplay to state

### Stage 1: Character Reference Generation
**Input**: PipelineState  
**Output**: PipelineState with character images generated  
**Jobs Processed**: CHARACTER type jobs

**Process**:
1. Get pending character jobs
2. For each character, generate 3 views: front, side, full_body
3. Use `CharacterGenerationStage.get_reference_prompts()` for prompts
4. Save images to `{base_dir}/characters/`
5. Update job status

### Stage 2: Audio Generation (Optional)
**Input**: PipelineState  
**Output**: PipelineState with audio metadata  
**Jobs Processed**: None (metadata only)

**Process**:
1. Generate voiceover/narration using 11labs
2. Extract timing and duration info
3. Store metadata in state
4. Currently returns mock data

### Stage 3: Keyframe Image Generation
**Input**: PipelineState  
**Output**: PipelineState with keyframe images  
**Jobs Processed**: IMAGE type jobs

**Process**:
1. Get pending image jobs
2. For each scene, generate required frames:
   - first_frame (starting composition)
   - last_frame (ending composition)
   - transition_frame (bridge to next scene)
3. Use `ImageGenerationStage` for specs
4. Optionally include character references
5. Save to `{base_dir}/images/`

### Stage 4: Video Generation
**Input**: PipelineState  
**Output**: PipelineState with scene videos  
**Jobs Processed**: VIDEO type jobs

**Process**:
1. Get pending video jobs
2. For each scene, use appropriate method:
   - **text_to_video**: Pure prompt-based generation
   - **image_to_video**: Animate from first_frame
   - **first_last_frame_interpolation**: Interpolate between frames
3. Use `VideoGenerationStage` for specs
4. Save to `{base_dir}/videos/`

### Stage 5: Post-Production & Assembly
**Input**: PipelineState  
**Output**: PipelineState with final video  
**Jobs Processed**: POST_PRODUCTION type jobs

**Process**:
1. Get pending post-production jobs
2. For each scene:
   - Trim to target duration
   - Apply text overlays
   - Apply color grading
   - Mix audio
3. Stitch all scenes with transitions
4. Save final video to `{base_dir}/output/`

## Data Flow

```
Script Text
    ↓
ScreenplayBuilderInput(script, state)
    ↓
[ScreenplayBuilder]
    ↓
PipelineState(screenplay_dict, jobs=[...])
    ↓
[VisualCharacterBuilder]
    ↓
PipelineState(character images generated)
    ↓
[AudioGenerator]
    ↓
PipelineState(audio metadata)
    ↓
[KeyframeGenerator]
    ↓
PipelineState(keyframe images generated)
    ↓
[VideoGenerator]
    ↓
PipelineState(scene videos generated)
    ↓
[VideoProcessingPipeline]
    ↓
PipelineState(final video complete)
```

## Job Lifecycle

```
PENDING → IN_PROGRESS → COMPLETED
                ↓
              FAILED
                ↓
            (retry or skip)
```

Jobs can also be marked as SKIPPED if they're not needed.

## Resumability Strategy

1. **Save state after each stage**: `tracker.save_state(state)`
2. **Check completion flags**: `state.is_stage_complete(JobType.X)`
3. **Load existing state**: `tracker.load_state(movie_id)`
4. **Continue from last checkpoint**: Pipeline skips completed stages

## File Organization

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

## Database Schema

### jobs table
```sql
CREATE TABLE jobs (
    id TEXT PRIMARY KEY,
    movie_id TEXT NOT NULL,
    type TEXT NOT NULL,
    status TEXT NOT NULL,
    scene_id TEXT,
    character_id INTEGER,
    metadata TEXT,
    error TEXT,
    output_path TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
)
```

### pipeline_states table
```sql
CREATE TABLE pipeline_states (
    movie_id TEXT PRIMARY KEY,
    screenplay_complete INTEGER DEFAULT 0,
    characters_complete INTEGER DEFAULT 0,
    images_complete INTEGER DEFAULT 0,
    videos_complete INTEGER DEFAULT 0,
    post_production_complete INTEGER DEFAULT 0,
    screenplay_data TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
)
```

## Integration Points

### With Screenplay Extractors
The pipeline uses `cinema.transformers.screenplay_extractors` to convert the screenplay JSON into stage-specific data structures:

```python
extracted = extract_all_stages(screenplay_dict)

# Returns:
{
    "characters": CharacterGenerationStage,
    "images": ImageGenerationStage,
    "videos": VideoGenerationStage,
    "post_production": PostProductionStage,
    "video_config": {...}
}
```

### With Generation APIs
Each stage will integrate with:
- **Imagen/Nano Banana**: Character and keyframe image generation
- **Veo**: Video generation with multiple strategies
- **11labs**: Audio/voiceover generation
- **FFmpeg**: Video processing and stitching

## Error Handling

1. **Job-level errors**: Caught and stored in job.error field
2. **Stage-level errors**: Propagate up but state is saved
3. **Retry strategy**: Manual retry by resuming with same movie_id
4. **Partial completion**: Completed jobs are never re-run

## Future Enhancements

1. **Parallel execution**: Process independent jobs concurrently
2. **Rate limiting**: Built-in throttling for API calls
3. **Cost tracking**: Track API costs per job
4. **Quality validation**: Automated checks before proceeding
5. **Webhooks**: Real-time progress notifications
6. **Distributed execution**: Run stages on different machines
7. **Caching**: Reuse similar generations across movies

## Usage Patterns

### New Movie
```python
maker = MovieMaker(writer, enhancer)
state = await maker.generate(script="...", movie_id="my_movie")
```

### Resume Failed Generation
```python
maker = MovieMaker(writer, enhancer)
state = await maker.resume(movie_id="my_movie")
```

### Check Progress
```python
maker = MovieMaker(writer, enhancer)
status = maker.get_status("my_movie")
# Returns: {total, completed, failed, pending, progress}
```

### Custom Pipeline
```python
# Build custom pipeline with only needed stages
pipeline = (
    Pipeline()
    .then(KeyframeGenerator())
    .then(VideoGenerator())
)

state = await pipeline.execute(existing_state)
```

## Design Decisions

### Why SQLite?
- Simple, no external dependencies
- ACID transactions for reliability
- Easy to inspect and debug
- Sufficient for single-machine workloads
- Can migrate to PostgreSQL later if needed

### Why Immutable State?
- Easier to reason about data flow
- Enables parallel execution in future
- Simplifies debugging and testing
- Natural fit for functional pipeline pattern

### Why Job-Based Tracking?
- Fine-grained progress monitoring
- Easy to implement retry logic
- Supports rate limiting naturally
- Enables parallel execution
- Clear audit trail

### Why Separate Stages?
- Single responsibility principle
- Easy to test independently
- Can swap implementations
- Clear boundaries for optimization
- Supports partial pipeline execution
