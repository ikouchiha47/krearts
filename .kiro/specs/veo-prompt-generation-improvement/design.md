# Design Document: Veo 3.1 Prompt Generation Improvement

## Overview

This design document outlines the technical architecture for improving the screenplay-to-video generation pipeline to properly leverage Veo 3.1's capabilities, including audio-first generation, cinematic technique mapping, and multi-phase asset generation.

## Architecture

### High-Level Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    Input: Screenplay Markdown                    │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              Phase 1: Audio Generation & Analysis                │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ 1. Generate 11Labs voiceover (full script)              │  │
│  │ 2. Transcribe with timestamps (Whisper/Gemini)          │  │
│  │ 3. Detect scene boundaries (pause analysis + LLM)       │  │
│  │ 4. Segment audio into scene clips                       │  │
│  │ 5. Update scene durations to match audio                │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│           Phase 2: Scene Analysis & Classification               │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ 1. Parse screenplay structure                            │  │
│  │ 2. Identify cinematic techniques (match cuts, etc.)      │  │
│  │ 3. Classify generation method per scene                  │  │
│  │ 4. Detect montage sequences → decompose                  │  │
│  │ 5. Build generation manifest                             │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              Phase 3: Asset Generation (Imagen)                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ 1. Generate character reference images                   │  │
│  │ 2. Generate first frame keyframes                        │  │
│  │ 3. Generate last frame keyframes (for interpolation)     │  │
│  │ 4. Generate transition frames (if needed)                │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│            Phase 4: Video Generation (Veo 3.1)                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ 1. Generate videos (silent/SFX only, no dialogue)        │  │
│  │ 2. Use first+last frame interpolation where needed       │  │
│  │ 3. Include character reference images                    │  │
│  │ 4. Apply negative prompts (no dialogue)                  │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              Phase 5: Post-Production Assembly                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ 1. Mix audio clips to videos                            │  │
│  │ 2. Concatenate scenes                                    │  │
│  │ 3. Apply transitions (hard cuts, crossfades)            │  │
│  │ 4. Export final video                                    │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
                    ┌────────────────┐
                    │  Final Video   │
                    └────────────────┘
```

## Components

### 1. Audio Generation Module

**Purpose**: Generate voiceover audio first and use it to drive scene timing.

**Key Classes**:

```python
class AudioGenerator:
    """Handles 11Labs audio generation"""
    
    def generate_full_voiceover(
        self,
        screenplay: CinematgrapherCrewOutput,
        voice_id: str
    ) -> AudioFile:
        """Generate complete voiceover for entire screenplay"""
        pass
    
    def get_voice_settings(
        self,
        character: CharacterDescription
    ) -> VoiceSettings:
        """Map character voice characteristics to 11Labs settings"""
        pass


class AudioTranscriber:
    """Handles audio transcription with timestamps"""
    
    def transcribe_with_whisper(
        self,
        audio_path: str
    ) -> List[WordTimestamp]:
        """Transcribe using Whisper with word-level timestamps"""
        pass
    
    def transcribe_with_gemini(
        self,
        audio_path: str
    ) -> List[WordTimestamp]:
        """Transcribe using Gemini API"""
        pass


class SceneBoundaryDetector:
    """Detects scene boundaries from transcription"""
    
    def detect_boundaries_heuristic(
        self,
        words: List[WordTimestamp],
        screenplay: CinematgrapherCrewOutput,
        pause_threshold: float = 0.5
    ) -> List[SceneBoundary]:
        """Detect boundaries using pause analysis"""
        pass
    
    def detect_boundaries_llm(
        self,
        words: List[WordTimestamp],
        screenplay: CinematgrapherCrewOutput
    ) -> List[SceneBoundary]:
        """Use LLM for intelligent boundary detection"""
        pass


class AudioSegmenter:
    """Segments audio into scene-aligned clips"""
    
    def segment_audio(
        self,
        audio_path: str,
        boundaries: List[SceneBoundary],
        output_dir: str
    ) -> Dict[str, str]:
        """Segment audio file into clips"""
        pass
```

**Data Models**:

```python
@dataclass
class WordTimestamp:
    word: str
    start: float  # seconds
    end: float
    confidence: float


@dataclass
class SceneBoundary:
    scene_id: str
    start: float
    end: float
    duration: float


@dataclass
class AudioFile:
    path: str
    duration: float
    format: str
```

### 2. Scene Analysis Module

**Purpose**: Analyze screenplay structure and classify generation methods.

**Key Classes**:

```python
class CinematicTechniqueDetector:
    """Detects cinematic techniques from scene descriptions"""
    
    def __init__(self):
        self.technique_registry = self._load_technique_registry()
    
    def detect_technique(
        self,
        scene: Scene,
        previous_scene: Optional[Scene] = None
    ) -> CinematicTechnique:
        """Identify the cinematic technique being used"""
        pass
    
    def _load_technique_registry(self) -> Dict[str, TechniqueDefinition]:
        """Load cinematic techniques knowledge base"""
        pass


class GenerationMethodClassifier:
    """Classifies optimal generation method for each scene"""
    
    def classify_scene(
        self,
        scene: Scene,
        technique: CinematicTechnique
    ) -> GenerationMethod:
        """
        Determine generation method:
        - text_to_video
        - image_to_video
        - first_last_frame_interpolation
        - image_stitch_ffmpeg
        """
        pass
    
    def calculate_motion_score(self, scene: Scene) -> int:
        """Calculate motion complexity score"""
        pass


class MontageDecomposer:
    """Decomposes montage scenes into individual shots"""
    
    def decompose_montage(
        self,
        montage_scene: Scene
    ) -> List[Scene]:
        """Split montage into separate shot scenes"""
        pass
    
    def distribute_duration(
        self,
        total_duration: float,
        num_shots: int
    ) -> List[float]:
        """Distribute duration across shots"""
        pass


class GenerationManifestBuilder:
    """Builds manifest of all assets to generate"""
    
    def build_manifest(
        self,
        screenplay: CinematgrapherCrewOutput,
        scene_classifications: List[SceneClassification]
    ) -> GenerationManifest:
        """Create complete generation manifest"""
        pass
```

**Data Models**:

```python
@dataclass
class CinematicTechnique:
    name: str  # match_cut_graphic, smash_cut, etc.
    description: str
    generation_method: str
    requires_keyframes: bool
    requires_post: bool
    veo_features: List[str]


@dataclass
class GenerationMethod:
    method: str  # text_to_video, image_to_video, etc.
    reason: str
    veo_features: List[str]
    post_production_required: bool
    post_production_notes: str


@dataclass
class SceneClassification:
    scene: Scene
    technique: CinematicTechnique
    generation_method: GenerationMethod
    required_assets: List[str]


@dataclass
class GenerationManifest:
    character_references: List[AssetSpec]
    keyframes: List[AssetSpec]
    videos: List[VideoSpec]
    audio_clips: Dict[str, str]
    generation_order: List[str]


@dataclass
class AssetSpec:
    asset_id: str
    asset_type: str  # character_ref, keyframe, video
    prompt: str
    dependencies: List[str]
    status: str  # pending, generating, complete, failed
    output_path: Optional[str] = None
```

### 3. Asset Generation Module

**Purpose**: Generate images and videos using Imagen and Veo.

**Key Classes**:

```python
class ImagenGenerator:
    """Handles Imagen image generation"""
    
    def __init__(self, client: genai.Client):
        self.client = client
    
    def generate_character_reference(
        self,
        character: CharacterDescription,
        view: str  # front, side, full_body
    ) -> str:
        """Generate character reference image"""
        pass
    
    def generate_keyframe(
        self,
        prompt: str,
        aspect_ratio: str,
        config: ImagenConfig
    ) -> str:
        """Generate keyframe image"""
        pass
    
    def build_imagen_prompt(
        self,
        scene: Scene,
        frame_type: str  # first, last, transition
    ) -> str:
        """Build Imagen prompt following best practices"""
        pass


class VeoGenerator:
    """Handles Veo 3.1 video generation"""
    
    def __init__(self, client: genai.Client):
        self.client = client
    
    def generate_video_text_to_video(
        self,
        prompt: str,
        config: VeoConfig
    ) -> str:
        """Generate video from text prompt"""
        pass
    
    def generate_video_image_to_video(
        self,
        prompt: str,
        image_path: str,
        config: VeoConfig
    ) -> str:
        """Generate video from image"""
        pass
    
    def generate_video_interpolation(
        self,
        prompt: str,
        first_frame: str,
        last_frame: str,
        config: VeoConfig
    ) -> str:
        """Generate video with first+last frame interpolation"""
        pass
    
    def build_veo_prompt(
        self,
        scene: Scene,
        include_dialogue: bool = False
    ) -> str:
        """
        Build Veo prompt following formula:
        [Cinematography] + [Subject] + [Action] + [Context] + [Style & Ambiance]
        """
        pass
    
    def build_negative_prompt(
        self,
        scene: Scene,
        exclude_dialogue: bool = True
    ) -> str:
        """Build negative prompt"""
        pass


class AssetOrchestrator:
    """Orchestrates asset generation with dependencies"""
    
    def __init__(
        self,
        imagen_gen: ImagenGenerator,
        veo_gen: VeoGenerator
    ):
        self.imagen_gen = imagen_gen
        self.veo_gen = veo_gen
    
    def execute_manifest(
        self,
        manifest: GenerationManifest
    ) -> GenerationResults:
        """Execute generation manifest in correct order"""
        pass
    
    def check_dependencies(
        self,
        asset: AssetSpec,
        completed: Set[str]
    ) -> bool:
        """Check if asset dependencies are satisfied"""
        pass
```

**Data Models**:

```python
@dataclass
class ImagenConfig:
    aspect_ratio: str
    number_of_images: int = 1
    image_size: str = "1K"


@dataclass
class VeoConfig:
    duration_seconds: int
    aspect_ratio: str
    resolution: str = "720p"
    negative_prompt: Optional[str] = None
    reference_images: Optional[List[str]] = None


@dataclass
class GenerationResults:
    character_references: Dict[str, str]  # char_id -> path
    keyframes: Dict[str, str]  # asset_id -> path
    videos: Dict[str, str]  # scene_id -> path
    audio_clips: Dict[str, str]  # scene_id -> path
    errors: List[GenerationError]
```

### 4. Post-Production Module

**Purpose**: Assemble final video from generated assets.

**Key Classes**:

```python
class VideoAssembler:
    """Assembles final video from scenes"""
    
    def mix_audio_to_videos(
        self,
        videos: Dict[str, str],
        audio_clips: Dict[str, str],
        screenplay: CinematgrapherCrewOutput
    ) -> List[VideoClip]:
        """Mix audio clips to corresponding videos"""
        pass
    
    def concatenate_scenes(
        self,
        clips: List[VideoClip],
        transitions: List[TransitionSpec]
    ) -> VideoClip:
        """Concatenate scenes with transitions"""
        pass
    
    def apply_transition(
        self,
        clip1: VideoClip,
        clip2: VideoClip,
        transition_type: str
    ) -> VideoClip:
        """Apply transition between clips"""
        pass
    
    def export_final_video(
        self,
        final_clip: VideoClip,
        output_path: str,
        codec: str = "libx264"
    ) -> str:
        """Export final video"""
        pass


class TransitionApplicator:
    """Applies cinematic transitions"""
    
    def apply_hard_cut(
        self,
        clip1: VideoClip,
        clip2: VideoClip
    ) -> VideoClip:
        """Simple hard cut"""
        pass
    
    def apply_crossfade(
        self,
        clip1: VideoClip,
        clip2: VideoClip,
        duration: float = 0.5
    ) -> VideoClip:
        """Crossfade transition"""
        pass
    
    def apply_smash_cut(
        self,
        clip1: VideoClip,
        clip2: VideoClip,
        black_duration: float = 0.5
    ) -> VideoClip:
        """Smash cut with black frame"""
        pass
```

**Data Models**:

```python
@dataclass
class TransitionSpec:
    from_scene: str
    to_scene: str
    transition_type: str  # hard_cut, crossfade, smash_cut
    duration: float


@dataclass
class VideoClip:
    path: str
    duration: float
    audio_path: Optional[str] = None
```

## Data Flow

### Input: Enhanced Screenplay Structure

The system expects a markdown screenplay with this structure:

```markdown
## Video Context
- Title: ...
- Duration: 15 seconds
- Aspect Ratio: 9:16
- Camera: 35mm
- Lighting Consistency: ...

## Character Registry
### Character: CHAR_001 - Alex
- Physical Appearance: ...
- Style: ...

## Scene 1: Office Focus

### Scene Metadata
- Scene ID: S1_OfficeFocus
- Duration: 2.0s
- Scene Type: hook

### Scene Flow
- Previous Scene: N/A
- Next Scene: S2_GymPower
- Transition Technique: match_cut_graphic
- Visual Bridge: Headphone earcup position

### Cinematography
#### Camera Setup
- Shot Type: close-up
- Focal Length: 35mm
...

### Keyframe Image Descriptions
#### First Frame - Imagen Prompt
```
Cinematic close-up portrait of...
```

#### Last Frame - Imagen Prompt
```
Same composition but tighter...
```

### Video Generation Caption (Veo Prompt)
```
Slow dolly-in close-up shot...
```
```

### Output: Generation Manifest

```json
{
  "audio": {
    "full_audio_path": "output/full_voiceover.mp3",
    "duration": 15.3,
    "clips": {
      "S1_OfficeFocus": {
        "path": "output/audio_clips/S1_audio.mp3",
        "start": 0.0,
        "end": 2.1,
        "duration": 2.1
      },
      "S2_GymPower": {
        "path": "output/audio_clips/S2_audio.mp3",
        "start": 2.1,
        "end": 5.2,
        "duration": 3.1
      }
    }
  },
  "character_references": [
    {
      "asset_id": "CHAR_001_front",
      "character_id": "CHAR_001",
      "view": "front",
      "prompt": "Portrait of 30-year-old mixed-race man...",
      "status": "complete",
      "output_path": "output/refs/CHAR_001_front.png"
    }
  ],
  "keyframes": [
    {
      "asset_id": "S1_first_frame",
      "scene_id": "S1_OfficeFocus",
      "frame_type": "first",
      "prompt": "Cinematic close-up portrait...",
      "status": "complete",
      "output_path": "output/keyframes/S1_first.png"
    }
  ],
  "videos": [
    {
      "asset_id": "S1_video",
      "scene_id": "S1_OfficeFocus",
      "generation_method": "first_last_frame_interpolation",
      "prompt": "Slow dolly-in close-up shot...",
      "negative_prompt": "dialogue, voiceover, speech",
      "config": {
        "duration_seconds": 2,
        "aspect_ratio": "9:16",
        "resolution": "720p",
        "reference_images": ["output/refs/CHAR_001_front.png"]
      },
      "dependencies": ["S1_first_frame", "S1_last_frame", "CHAR_001_front"],
      "status": "complete",
      "output_path": "output/videos/S1_video.mp4"
    }
  ],
  "generation_order": [
    "CHAR_001_front",
    "S1_first_frame",
    "S1_last_frame",
    "S1_video",
    "S2_first_frame",
    "S2_last_frame",
    "S2_video"
  ]
}
```

## Error Handling

### Audio Generation Failures

```python
class AudioGenerationError(Exception):
    """Raised when audio generation fails"""
    pass

# Retry logic
def generate_with_retry(
    func: Callable,
    max_retries: int = 3,
    backoff: float = 2.0
) -> Any:
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            time.sleep(backoff ** attempt)
```

### Transcription Failures

```python
# Fallback to alternative transcription service
def transcribe_with_fallback(audio_path: str) -> List[WordTimestamp]:
    try:
        return transcribe_with_whisper(audio_path)
    except Exception as e:
        logger.warning(f"Whisper failed: {e}, falling back to Gemini")
        return transcribe_with_gemini(audio_path)
```

### Video Generation Failures

```python
# Track failed generations and continue
class GenerationTracker:
    def __init__(self):
        self.failed: List[str] = []
        self.completed: List[str] = []
    
    def mark_failed(self, asset_id: str, error: Exception):
        self.failed.append(asset_id)
        logger.error(f"Asset {asset_id} failed: {error}")
    
    def can_continue(self) -> bool:
        """Check if we can continue despite failures"""
        # Can continue if at least 70% of scenes succeeded
        total = len(self.failed) + len(self.completed)
        success_rate = len(self.completed) / total if total > 0 else 0
        return success_rate >= 0.7
```

## Testing Strategy

### Unit Tests

```python
# Test audio segmentation
def test_audio_segmentation():
    boundaries = [
        SceneBoundary("S1", 0.0, 2.1, 2.1),
        SceneBoundary("S2", 2.1, 5.2, 3.1)
    ]
    clips = segment_audio("test_audio.mp3", boundaries)
    assert len(clips) == 2
    assert clips["S1"] == "output/audio_clips/S1_audio.mp3"


# Test boundary detection
def test_boundary_detection():
    words = [
        WordTimestamp("noise", 0.0, 0.3, 0.95),
        WordTimestamp("distraction", 0.4, 0.9, 0.92),
        # ... pause ...
        WordTimestamp("to", 2.2, 2.3, 0.98),
        WordTimestamp("switch", 2.4, 2.7, 0.96)
    ]
    boundaries = detect_boundaries_heuristic(words, screenplay, pause_threshold=0.5)
    assert len(boundaries) == 2
    assert boundaries[0].end < boundaries[1].start


# Test prompt building
def test_veo_prompt_building():
    scene = Scene(
        scene_id="S1",
        cinematography=Cinematography(
            camera_movement=CameraMovement(movement_type="dolly shot")
        ),
        # ...
    )
    prompt = build_veo_prompt(scene, include_dialogue=False)
    assert "dolly shot" in prompt.lower()
    assert '"' not in prompt  # No dialogue quotes
```

### Integration Tests

```python
# Test full audio-first pipeline
def test_audio_first_pipeline():
    screenplay = load_test_screenplay()
    final_video = audio_first_pipeline(screenplay)
    assert os.path.exists(final_video)
    assert get_video_duration(final_video) == pytest.approx(15.0, abs=0.5)


# Test asset generation with dependencies
def test_asset_generation_with_dependencies():
    manifest = build_test_manifest()
    results = execute_manifest(manifest)
    assert len(results.errors) == 0
    assert all(os.path.exists(path) for path in results.videos.values())
```

## Performance Considerations

### Parallel Generation

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

async def generate_assets_parallel(
    assets: List[AssetSpec],
    max_workers: int = 4
) -> List[str]:
    """Generate multiple assets in parallel"""
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        loop = asyncio.get_event_loop()
        tasks = [
            loop.run_in_executor(executor, generate_asset, asset)
            for asset in assets
            if not asset.dependencies  # Only independent assets
        ]
        return await asyncio.gather(*tasks)
```

### Caching

```python
from functools import lru_cache
import hashlib

@lru_cache(maxsize=100)
def get_cached_character_reference(
    character_id: str,
    view: str
) -> Optional[str]:
    """Cache character reference images"""
    cache_key = f"{character_id}_{view}"
    cache_path = f"cache/refs/{cache_key}.png"
    if os.path.exists(cache_path):
        return cache_path
    return None


def cache_asset(asset_id: str, content: bytes):
    """Cache generated asset"""
    cache_dir = "cache/assets"
    os.makedirs(cache_dir, exist_ok=True)
    cache_path = os.path.join(cache_dir, f"{asset_id}.bin")
    with open(cache_path, "wb") as f:
        f.write(content)
```

## Configuration

```python
@dataclass
class PipelineConfig:
    # Audio settings
    audio_provider: str = "elevenlabs"  # elevenlabs, google_tts
    transcription_provider: str = "whisper"  # whisper, gemini
    pause_threshold: float = 0.5  # seconds
    
    # Generation settings
    max_parallel_generations: int = 4
    retry_attempts: int = 3
    retry_backoff: float = 2.0
    
    # Quality settings
    video_resolution: str = "720p"  # 720p, 1080p
    audio_bitrate: str = "192k"
    video_codec: str = "libx264"
    
    # Paths
    output_dir: str = "output"
    cache_dir: str = "cache"
    temp_dir: str = "temp"
    
    # Feature flags
    enable_caching: bool = True
    enable_parallel_generation: bool = True
    use_llm_boundary_detection: bool = False  # Use heuristic by default
```

## Next Steps

1. Implement audio generation module
2. Implement scene analysis module
3. Implement asset generation orchestration
4. Implement post-production assembly
5. Add comprehensive error handling
6. Add performance optimizations (caching, parallelization)
7. Create integration tests
8. Document API and usage examples
