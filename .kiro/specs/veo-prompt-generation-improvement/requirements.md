# Requirements Document

## Introduction

The current screenplay-to-video generation system produces prompts that don't align with Veo 3.1's capabilities and best practices. This feature will redesign the prompt generation pipeline to leverage Veo 3.1's advanced workflows including first/last frame interpolation, reference images for character consistency, and proper prompt structure.

## Glossary

- **Veo 3.1**: Google's video generation model that creates 4-8 second video clips
- **Imagen**: Google's image generation model used to create keyframes and reference images
- **First and Last Frame**: Veo feature that interpolates video between two provided images
- **Reference Images**: Up to 3 images that guide character/object consistency in generated videos
- **Screenplay JSON**: The structured JSON output containing scene descriptions and prompts
- **Shot**: A single continuous video clip without cuts
- **Montage**: Multiple shots edited together (requires separate video generations)
- **Keyframe**: A still image representing a specific moment in the video timeline

## Requirements

### Requirement 1: Multi-Phase Generation Pipeline

**User Story:** As a video producer, I want the system to generate videos in multiple phases (assets first, then videos), so that I have proper reference materials and keyframes before video generation begins.

#### Acceptance Criteria

1. WHEN the System receives a screenplay JSON, THE System SHALL analyze all scenes and identify required asset generation tasks before any video generation
2. WHEN the System identifies character-based scenes, THE System SHALL generate character reference images using Imagen before video generation
3. WHEN the System identifies transition scenes, THE System SHALL generate both first and last frame keyframes using Imagen before video generation
4. WHEN all required assets are generated, THE System SHALL proceed to video generation phase with proper references

### Requirement 2: Scene Classification and Method Selection

**User Story:** As a video producer, I want each scene to be classified by the appropriate Veo generation method, so that the system uses the optimal technique for each shot type.

#### Acceptance Criteria

1. WHEN the System analyzes a scene with a single static composition, THE System SHALL classify it as "image-to-video" generation
2. WHEN the System analyzes a scene describing a camera movement or transformation between two states, THE System SHALL classify it as "first-and-last-frame" generation
3. WHEN the System analyzes a scene requiring character consistency with previous scenes, THE System SHALL classify it as "reference-image-based" generation
4. WHEN the System analyzes a scene describing rapid cuts or montage, THE System SHALL split it into multiple separate shot generations
5. WHEN the System classifies a scene, THE System SHALL document the classification reason and required assets

### Requirement 3: Veo-Compliant Prompt Structure

**User Story:** As a video producer, I want all video prompts to follow Veo's recommended structure, so that generated videos have better quality and prompt adherence.

#### Acceptance Criteria

1. WHEN the System generates a video prompt, THE System SHALL structure it as "[Cinematography] + [Subject] + [Action] + [Context] + [Style & Ambiance]"
2. WHEN the System includes cinematography terms, THE System SHALL use Veo-recognized terms like "dolly shot", "tracking shot", "crane shot", "close-up", "wide shot"
3. WHEN the System includes audio cues, THE System SHALL format dialogue with quotation marks and prefix sound effects with "SFX:"
4. WHEN the System includes ambient audio, THE System SHALL prefix with "Ambient noise:"
5. WHEN the System generates negative prompts, THE System SHALL describe unwanted elements without using "no" or "don't" language

### Requirement 4: Imagen Keyframe Generation

**User Story:** As a video producer, I want the system to generate high-quality keyframe images using Imagen, so that image-to-video and interpolation workflows have proper source material.

#### Acceptance Criteria

1. WHEN the System generates a keyframe image, THE System SHALL use Imagen with proper photography modifiers (camera position, lighting, lens type)
2. WHEN the System generates a character image, THE System SHALL include detailed physical descriptions and use portrait photography techniques
3. WHEN the System generates an environment image, THE System SHALL specify aspect ratio matching the target video (9:16 or 16:9)
4. WHEN the System generates reference images for character consistency, THE System SHALL create neutral pose images suitable for reference across multiple scenes
5. WHEN the System generates first and last frames, THE System SHALL ensure visual continuity elements (lighting, character position, environment) are compatible for interpolation

### Requirement 5: Montage Scene Decomposition

**User Story:** As a video producer, I want scenes describing multiple cuts or rapid sequences to be automatically split into separate video generations, so that each generation produces a single continuous shot as Veo requires.

#### Acceptance Criteria

1. WHEN the System encounters a scene with "rapid-fire sequence", "multiple cuts", or "montage" in the description, THE System SHALL decompose it into individual shots
2. WHEN the System decomposes a montage scene, THE System SHALL create separate scene entries for each described shot
3. WHEN the System creates decomposed shots, THE System SHALL assign appropriate durations that sum to the original scene duration
4. WHEN the System creates decomposed shots, THE System SHALL preserve character and style consistency across all shots
5. WHEN the System creates decomposed shots, THE System SHALL indicate they require post-production editing to achieve the montage effect

### Requirement 6: Character Reference Image Management

**User Story:** As a video producer, I want consistent character appearance across all scenes, so that the generated video maintains visual continuity.

#### Acceptance Criteria

1. WHEN the System identifies a character in the screenplay, THE System SHALL generate a reference image set (front view, side view, and full body) using Imagen
2. WHEN the System generates videos featuring a character, THE System SHALL include the character's reference images in the Veo API call
3. WHEN the System generates character reference images, THE System SHALL use neutral backgrounds and lighting suitable for reference purposes
4. WHEN the System stores character references, THE System SHALL associate them with character IDs for reuse across scenes
5. WHEN the System uses reference images, THE System SHALL limit to maximum 3 references per video generation as per Veo specifications

### Requirement 7: Asset and Generation Manifest

**User Story:** As a video producer, I want a clear manifest of all assets to be generated and their dependencies, so that I can understand the generation pipeline and troubleshoot issues.

#### Acceptance Criteria

1. WHEN the System completes scene analysis, THE System SHALL output a generation manifest listing all required assets
2. WHEN the System creates the manifest, THE System SHALL include asset type (character reference, keyframe, video), dependencies, and generation order
3. WHEN the System creates the manifest, THE System SHALL include estimated generation parameters (duration, aspect ratio, resolution)
4. WHEN the System creates the manifest, THE System SHALL include the full Imagen or Veo prompt for each asset
5. WHEN the System executes generation, THE System SHALL update the manifest with generation status and output file paths

### Requirement 8: Timestamp Prompting Support

**User Story:** As a video producer, I want to use timestamp prompting for complex single-shot sequences, so that I can create videos with multiple actions within one generation.

#### Acceptance Criteria

1. WHEN the System identifies a scene with multiple sequential actions within a single shot, THE System SHALL format the prompt using timestamp notation [HH:MM:SS-HH:MM:SS]
2. WHEN the System uses timestamp prompting, THE System SHALL ensure the total duration matches the scene duration
3. WHEN the System uses timestamp prompting, THE System SHALL include cinematography, subject, and action details for each timestamp segment
4. WHEN the System uses timestamp prompting, THE System SHALL ensure smooth narrative flow between timestamp segments
5. WHEN the System uses timestamp prompting, THE System SHALL limit to maximum 8 seconds total duration as per Veo specifications

### Requirement 9: Audio-First Generation Workflow

**User Story:** As a video producer, I want to generate voiceover audio first and automatically align video generation to audio timing, so that I have consistent voice quality and automatic scene timing without manual sync work.

#### Acceptance Criteria

1. WHEN the System begins video generation, THE System SHALL generate complete voiceover audio using 11Labs before any video generation
2. WHEN the System generates voiceover audio, THE System SHALL transcribe the audio with word-level timestamps using speech recognition
3. WHEN the System analyzes transcription, THE System SHALL automatically detect scene boundaries based on pauses, dialogue breaks, and script structure
4. WHEN the System detects scene boundaries, THE System SHALL segment the audio track into scene-aligned clips with precise start/end timestamps
5. WHEN the System generates videos with Veo, THE System SHALL use prompts without dialogue (SFX and ambient only) to avoid audio conflicts
6. WHEN the System completes video generation, THE System SHALL automatically mix the pre-segmented audio clips back to their corresponding video scenes
7. WHEN the System segments audio, THE System SHALL preserve audio quality without re-encoding where possible
8. WHEN the System detects scene boundaries, THE System SHALL update scene duration metadata to match actual audio timing

### Requirement 9: Audio Consistency Strategy

**User Story:** As a video producer, I want consistent voice and audio across all scenes, so that the final video has professional audio quality without jarring transitions.

#### Acceptance Criteria

1. WHEN the System generates a multi-scene video with voiceover, THE System SHALL support three audio generation strategies: "veo_native", "post_production", and "hybrid"
2. WHEN the audio strategy is "post_production", THE System SHALL generate a complete audio track specification with full voiceover script and timing markers
3. WHEN the audio strategy is "post_production", THE System SHALL configure video generation to use "ambient_only" or "silent" audio handling
4. WHEN the audio strategy is "veo_native", THE System SHALL include dialogue in Veo prompts but SHALL warn about potential voice inconsistency across scenes
5. WHEN the System generates the audio track specification, THE System SHALL include audio segments with precise timing (start, end, text, type) for post-production assembly
6. WHEN the audio strategy is "hybrid", THE System SHALL identify which scenes can use Veo native audio (single long scenes) and which require post-production audio overlay
7. WHEN generating video prompts with "ambient_only" audio, THE System SHALL include only environmental sound descriptions (e.g., "SFX: office chatter, keyboard clicks") and SHALL NOT include dialogue
8. WHEN the System creates the complete audio track, THE System SHALL ensure voice characteristics, pacing, and emotional tone are consistent across all segments
