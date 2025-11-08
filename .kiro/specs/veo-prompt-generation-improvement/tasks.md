# Implementation Tasks

## Task 1: Audio Generation Module

Implement the audio-first generation workflow with 11Labs integration and automatic scene boundary detection.

- [ ] 1.1 Implement AudioGenerator class
  - Create 11Labs client wrapper
  - Implement `generate_full_voiceover()` method
  - Map character voice characteristics to 11Labs settings
  - Add error handling and retry logic
  - _Requirements: 9.1_

- [ ] 1.2 Implement AudioTranscriber class
  - Integrate Whisper for transcription with word-level timestamps
  - Implement Gemini transcription as fallback
  - Parse transcription output into WordTimestamp objects
  - Handle transcription errors gracefully
  - _Requirements: 9.2_

- [ ] 1.3 Implement SceneBoundaryDetector class
  - Implement heuristic boundary detection using pause analysis
  - Implement LLM-based boundary detection using Gemini
  - Match detected boundaries to screenplay structure
  - Validate boundary detection accuracy
  - _Requirements: 9.3_

- [ ] 1.4 Implement AudioSegmenter class
  - Use pydub to segment audio files
  - Preserve audio quality without re-encoding
  - Generate scene-aligned audio clips
  - Handle edge cases (very short clips, overlapping boundaries)
  - _Requirements: 9.4_

- [ ] 1.5 Implement scene duration update logic
  - Update Scene.duration based on audio timing
  - Update Scene.timing with start-end timestamps
  - Recalculate total video duration
  - Validate duration constraints (Veo 4-8s limits)
  - _Requirements: 9.8_

- [ ] 1.6 Create audio generation pipeline orchestrator
  - Coordinate all audio generation steps
  - Handle failures and fallbacks
  - Log progress and timing information
  - Return AudioGenerationResult with all clips
  - _Requirements: 9.1, 9.2, 9.3, 9.4_

## Task 2: Scene Analysis and Classification Module

Implement scene analysis to detect cinematic techniques and classify generation methods.

- [ ] 2.1 Create cinematic techniques knowledge base
  - Load transitions vocabulary from knowledge/transitions/vocabulary.txt
  - Parse technique definitions (match_cut, smash_cut, etc.)
  - Map techniques to generation methods
  - Create TechniqueDefinition data models
  - _Requirements: 2.5_

- [ ] 2.2 Implement CinematicTechniqueDetector class
  - Detect technique from scene descriptions
  - Analyze scene flow and transition types
  - Match scene descriptions to technique patterns
  - Handle ambiguous cases with LLM assistance
  - _Requirements: 2.1, 2.2_

- [ ] 2.3 Implement GenerationMethodClassifier class
  - Classify scenes as text-to-video, image-to-video, or interpolation
  - Calculate motion complexity score
  - Determine if keyframes are needed
  - Document classification reasoning
  - _Requirements: 2.1, 2.2, 2.3_

- [ ] 2.4 Implement MontageDecomposer class
  - Detect montage scenes from descriptions
  - Split montage into individual shots
  - Distribute duration across shots
  - Preserve character and style consistency
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [ ] 2.5 Implement GenerationManifestBuilder class
  - Build complete asset generation manifest
  - Identify all required assets (refs, keyframes, videos)
  - Determine generation order based on dependencies
  - Include prompts and configuration for each asset
  - _Requirements: 7.1, 7.2, 7.3, 7.4_

## Task 3: Imagen Asset Generation Module

Implement Imagen integration for generating character references and keyframes.

- [ ] 3.1 Implement ImagenGenerator class
  - Create Gemini client wrapper for Imagen
  - Implement character reference generation
  - Implement keyframe generation (first/last frames)
  - Handle Imagen API errors and retries
  - _Requirements: 4.1, 4.2, 4.3_

- [ ] 3.2 Implement Imagen prompt builder
  - Follow Imagen prompting best practices (Subject + Context + Style)
  - Include photography modifiers (camera, lighting, lens)
  - Generate prompts for character references
  - Generate prompts for keyframes with composition matching
  - _Requirements: 4.1, 4.2, 4.4, 4.5_

- [ ] 3.3 Implement character reference image generation
  - Generate front view, side view, and full body references
  - Use neutral backgrounds and lighting
  - Ensure consistent character appearance
  - Store references with character IDs
  - _Requirements: 6.1, 6.2, 6.3, 6.4_

- [ ] 3.4 Implement keyframe generation for interpolation
  - Generate first frame keyframes
  - Generate last frame keyframes with composition matching
  - Ensure visual continuity for interpolation
  - Handle match cut composition requirements
  - _Requirements: 4.5_

- [ ] 3.5 Implement transition frame generation
  - Generate intermediate frames for lighting/environment transitions
  - Bridge abrupt changes between scenes
  - Maintain visual continuity
  - _Requirements: 4.5_

## Task 4: Veo Video Generation Module

Implement Veo 3.1 integration for video generation with proper prompt structure.

- [ ] 4.1 Implement VeoGenerator class
  - Create Gemini client wrapper for Veo
  - Implement text-to-video generation
  - Implement image-to-video generation
  - Implement first+last frame interpolation
  - _Requirements: 3.1_

- [ ] 4.2 Implement Veo prompt builder
  - Follow Veo formula: [Cinematography] + [Subject] + [Action] + [Context] + [Style & Ambiance]
  - Include camera movement terms (dolly shot, tracking shot, etc.)
  - Format audio cues (SFX:, Ambient noise:)
  - Exclude dialogue when audio strategy is post_production
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 9.5_

- [ ] 4.3 Implement negative prompt builder
  - Describe unwanted elements without "no"/"don't" language
  - Add "dialogue, voiceover, speech" when excluding audio
  - Handle scene-specific exclusions
  - _Requirements: 3.5, 9.5_

- [ ] 4.4 Implement reference image handling
  - Include character reference images in Veo API calls
  - Limit to maximum 3 references per generation
  - Handle reference image paths and uploads
  - _Requirements: 6.2, 6.5_

- [ ] 4.5 Implement video generation with proper configuration
  - Set duration (4s, 6s, or 8s)
  - Set aspect ratio (9:16 or 16:9)
  - Set resolution (720p or 1080p)
  - Handle Veo API polling and timeouts
  - _Requirements: 3.1_

- [ ] 4.6 Implement timestamp prompting support
  - Format prompts with [HH:MM:SS-HH:MM:SS] notation
  - Ensure total duration matches scene duration
  - Include details for each timestamp segment
  - Limit to 8 seconds maximum
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

## Task 5: Asset Generation Orchestration

Implement orchestration logic to generate all assets in correct order with dependency management.

- [ ] 5.1 Implement AssetOrchestrator class
  - Execute generation manifest in dependency order
  - Check dependencies before generating each asset
  - Track generation status (pending, generating, complete, failed)
  - Handle partial failures gracefully
  - _Requirements: 7.5_

- [ ] 5.2 Implement parallel generation for independent assets
  - Identify assets with no dependencies
  - Generate multiple assets in parallel (max 4 concurrent)
  - Use ThreadPoolExecutor for parallelization
  - Monitor and log parallel generation progress
  - _Requirements: 1.1, 1.2, 1.3, 1.4_

- [ ] 5.3 Implement asset caching
  - Cache character reference images
  - Cache keyframes for reuse
  - Use content-based cache keys
  - Implement cache invalidation logic
  - _Requirements: 6.4_

- [ ] 5.4 Implement generation result tracking
  - Track completed assets with output paths
  - Track failed assets with error messages
  - Calculate success rate
  - Determine if pipeline can continue despite failures
  - _Requirements: 7.5_

- [ ] 5.5 Implement retry logic for failed generations
  - Retry failed generations up to 3 times
  - Use exponential backoff (2^attempt seconds)
  - Log retry attempts
  - Mark as permanently failed after max retries
  - _Requirements: 1.1, 1.2, 1.3, 1.4_

## Task 6: Post-Production Assembly Module

Implement video assembly with audio mixing and transitions.

- [ ] 6.1 Implement VideoAssembler class
  - Mix audio clips to corresponding videos
  - Concatenate scenes in correct order
  - Apply transitions between scenes
  - Export final video
  - _Requirements: 9.6_

- [ ] 6.2 Implement audio-to-video mixing
  - Load video clips with moviepy
  - Load corresponding audio clips
  - Replace video audio with pre-generated audio
  - Preserve video quality during mixing
  - _Requirements: 9.6, 9.7_

- [ ] 6.3 Implement TransitionApplicator class
  - Apply hard cuts (simple concatenation)
  - Apply crossfades with configurable duration
  - Apply smash cuts with black frames
  - Handle transition timing and alignment
  - _Requirements: 2.5_

- [ ] 6.4 Implement video concatenation
  - Concatenate all scene clips
  - Maintain aspect ratio and resolution
  - Handle clips of varying durations
  - Ensure smooth playback
  - _Requirements: 9.6_

- [ ] 6.5 Implement final video export
  - Export with libx264 codec
  - Export with AAC audio codec
  - Set 24fps frame rate
  - Optimize for file size and quality
  - _Requirements: 9.6_

## Task 7: Pipeline Integration and Testing

Integrate all modules into complete pipeline and add comprehensive testing.

- [ ] 7.1 Implement complete audio-first pipeline
  - Integrate all modules (audio, analysis, generation, assembly)
  - Coordinate execution flow
  - Handle errors at each stage
  - Log progress and timing
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6_

- [ ] 7.2 Implement PipelineConfig class
  - Define configuration options
  - Load configuration from file or environment
  - Validate configuration values
  - Provide sensible defaults
  - _Requirements: All_

- [ ] 7.3 Create unit tests for audio module
  - Test audio generation
  - Test transcription
  - Test boundary detection
  - Test audio segmentation
  - _Requirements: 9.1, 9.2, 9.3, 9.4_

- [ ] 7.4 Create unit tests for scene analysis module
  - Test technique detection
  - Test generation method classification
  - Test montage decomposition
  - Test manifest building
  - _Requirements: 2.1, 2.2, 2.3, 5.1, 7.1_

- [ ] 7.5 Create unit tests for asset generation module
  - Test Imagen prompt building
  - Test Veo prompt building
  - Test reference image generation
  - Test keyframe generation
  - _Requirements: 3.1, 4.1, 6.1_

- [ ] 7.6 Create integration tests for complete pipeline
  - Test end-to-end audio-first workflow
  - Test asset generation with dependencies
  - Test video assembly
  - Test error handling and recovery
  - _Requirements: All_

- [ ] 7.7 Create performance benchmarks
  - Measure audio generation time
  - Measure video generation time
  - Measure total pipeline time
  - Identify bottlenecks
  - _Requirements: All_

## Task 8: Documentation and Examples

Create comprehensive documentation and usage examples.

- [ ] 8.1 Document audio-first workflow
  - Explain workflow steps
  - Provide code examples
  - Document configuration options
  - Include troubleshooting guide
  - _Requirements: 9.1, 9.2, 9.3, 9.4_

- [ ] 8.2 Document cinematic techniques knowledge base
  - List all supported techniques
  - Explain generation method for each
  - Provide prompt examples
  - Document when to use each technique
  - _Requirements: 2.5_

- [ ] 8.3 Document Imagen and Veo prompt best practices
  - Explain prompt structure
  - Provide examples for different scene types
  - Document common pitfalls
  - Include quality improvement tips
  - _Requirements: 3.1, 4.1_

- [ ] 8.4 Create usage examples
  - Simple 15-second ad example
  - Complex multi-scene narrative example
  - Montage sequence example
  - Match cut example
  - _Requirements: All_

- [ ] 8.5 Document API reference
  - Document all public classes and methods
  - Include parameter descriptions
  - Provide return value documentation
  - Add code examples for each method
  - _Requirements: All_

## Task 9: Output Schema Updates

Update output schemas to support new generation workflow.

- [ ] 9.1 Update CinematgrapherCrewOutput model
  - Add audio_strategy field (veo_native, post_production, hybrid)
  - Add generation_manifest field
  - Add target_demographic, cultural_context, emotions_invoked fields
  - Add visual_style field
  - _Requirements: 9.1, 9.2_

- [ ] 9.2 Update Scene model with new fields
  - Add timing field (start-end timestamps)
  - Add context field (narrative purpose)
  - Add scene_flow field (SceneFlow model)
  - Add cinematography field (Cinematography model)
  - Add generation_strategy field (GenerationStrategy model)
  - Add keyframe_description field (KeyframeDescription model)
  - Add audio_details field (AudioDetails model)
  - Add visual_continuity field (VisualContinuity model)
  - Add veo_prompt and negative_prompt fields
  - _Requirements: 2.1, 3.1, 4.1, 9.8_

- [ ] 9.3 Create new data models for audio workflow
  - Create WordTimestamp model
  - Create SceneBoundary model
  - Create AudioFile model
  - Create AudioClip model
  - _Requirements: 9.2, 9.3, 9.4_

- [ ] 9.4 Create new data models for scene analysis
  - Create CinematicTechnique model
  - Create GenerationMethod model
  - Create SceneClassification model
  - Create GenerationManifest model
  - Create AssetSpec model
  - _Requirements: 2.1, 2.2, 7.1_

- [ ] 9.5 Create new data models for cinematography
  - Create CameraSetup model
  - Create CameraMovement model
  - Create CameraConsistency model
  - Create Cinematography model
  - _Requirements: 3.1_

- [ ] 9.6 Update VideoConfig model
  - Add camera field (35mm, 50mm, etc.)
  - Add lighting_consistency field
  - _Requirements: 3.1_

- [ ] 9.7 Validate all model changes with getDiagnostics
  - Check cinema/models.py for errors
  - Ensure backward compatibility
  - Update any dependent code
  - _Requirements: All_

## Task 10: CLI and API Interface

Create command-line interface and API for the pipeline.

- [ ] 10.1 Create CLI for audio-first pipeline
  - Add command: `cinema generate-audio <screenplay.md>`
  - Add command: `cinema generate-video <screenplay.md>`
  - Add command: `cinema generate-full <screenplay.md>`
  - Add progress indicators and logging
  - _Requirements: All_

- [ ] 10.2 Create API endpoints for pipeline
  - POST /api/generate/audio - Generate audio only
  - POST /api/generate/video - Generate video with pre-generated audio
  - POST /api/generate/full - Complete pipeline
  - GET /api/status/<job_id> - Check generation status
  - _Requirements: All_

- [ ] 10.3 Add configuration file support
  - Support YAML configuration files
  - Support environment variable overrides
  - Validate configuration on load
  - Provide example configuration files
  - _Requirements: All_
