# Requirements Document

## Introduction

This spec covers the integration of Google Gemini APIs (Imagen 3, Veo 2) and 11labs API into the cinema pipeline for actual image, video, and audio generation. Currently, the pipeline uses mock implementations that create placeholder files. This spec will replace those with real API calls while maintaining the existing pipeline architecture.

## Glossary

- **Pipeline**: The cinema movie generation system with stages for character, image, video, and post-production
- **Imagen 3**: Google's image generation API for creating character references and keyframes
- **Veo 2**: Google's video generation API supporting text-to-video, image-to-video, and first+last frame interpolation
- **11labs**: Text-to-speech API for voiceover generation
- **Job**: A discrete unit of work tracked in SQLite (e.g., generate character image, generate scene video)
- **State**: PipelineState object containing screenplay data, file paths, and job tracking
- **Rate Limiting**: Throttling API requests to stay within provider limits
- **Resumability**: Ability to restart pipeline from any point after failure

## Requirements

### Requirement 0: Support Pre-Generated Screenplay JSON

**User Story:** As a pipeline user, I want to provide a pre-generated screenplay JSON directly to MovieMaker, so that I can skip the screenplay generation stage and test the pipeline faster.

#### Acceptance Criteria

1. WHEN MovieMaker.generate() is called with a screenplay_json parameter, THE System SHALL use the provided JSON instead of generating a new screenplay
2. WHEN screenplay_json is provided, THE System SHALL skip the ScreenplayBuilder stage entirely
3. WHEN screenplay_json is provided, THE System SHALL NOT require writer or enhancer parameters
4. THE System SHALL extract generation stages from the provided screenplay_json and create jobs
5. THE System SHALL mark the SCREENPLAY stage as complete immediately when using pre-generated JSON

### Requirement 1: Imagen 3 Integration for Character References

**User Story:** As a pipeline user, I want character reference images generated using Imagen 3, so that characters maintain consistent appearance across all scenes.

#### Acceptance Criteria

1. WHEN the VisualCharacterBuilder stage processes a character job, THE System SHALL call Imagen 3 API with the character reference prompt
2. WHEN Imagen 3 returns an image, THE System SHALL save the image to the designated character directory path
3. WHEN the API call fails, THE System SHALL mark the job as failed and log the error without crashing the pipeline
4. WHERE a character has multiple views (front, side, full_body), THE System SHALL generate each view as a separate API call
5. WHILE generating character images, THE System SHALL respect Imagen 3 rate limits by implementing exponential backoff

### Requirement 2: Imagen 3 Integration for Keyframe Images

**User Story:** As a pipeline user, I want keyframe images (first_frame, last_frame, transition_frame) generated using Imagen 3, so that Veo can use them for video interpolation.

#### Acceptance Criteria

1. WHEN the KeyframeGenerator stage processes an image job, THE System SHALL call Imagen 3 API with the keyframe prompt and aspect ratio
2. WHERE character references exist for the scene, THE System SHALL include character reference images in the Imagen 3 API call
3. WHEN Imagen 3 returns an image, THE System SHALL save the image to the designated scene image directory path
4. IF the API call fails after 3 retry attempts, THEN THE System SHALL mark the job as failed and continue with other jobs
5. WHILE generating keyframe images, THE System SHALL implement rate limiting to avoid exceeding API quotas

### Requirement 3: Veo 2 Integration for Text-to-Video Generation

**User Story:** As a pipeline user, I want videos generated from text prompts using Veo 2, so that scenes without keyframes can be created directly from descriptions.

#### Acceptance Criteria

1. WHEN the VideoGenerator stage processes a video job with method "text_to_video", THE System SHALL call Veo 2 text-to-video API with the video prompt
2. WHEN the video prompt includes character references, THE System SHALL include up to 3 character reference images in the API call
3. WHEN Veo 2 returns a video, THE System SHALL save the video to the designated scene video directory path
4. WHERE the scene specifies a duration, THE System SHALL request that duration from Veo 2 (minimum 4 seconds)
5. IF Veo 2 generation fails, THEN THE System SHALL retry up to 2 times with exponential backoff before marking the job as failed

### Requirement 4: Veo 2 Integration for Image-to-Video Generation

**User Story:** As a pipeline user, I want videos generated from first frame images using Veo 2, so that scenes can start with precise compositions.

#### Acceptance Criteria

1. WHEN the VideoGenerator stage processes a video job with method "image_to_video", THE System SHALL call Veo 2 image-to-video API with the first frame image and video prompt
2. WHEN the first frame image does not exist, THE System SHALL mark the job as failed with a clear error message
3. WHEN Veo 2 returns a video, THE System SHALL save the video to the designated scene video directory path
4. WHERE character references exist, THE System SHALL include them in the API call along with the first frame image
5. WHILE generating the video, THE System SHALL respect Veo 2's maximum of 3 reference images total

### Requirement 5: Veo 2 Integration for First+Last Frame Interpolation

**User Story:** As a pipeline user, I want videos generated by interpolating between first and last frame images using Veo 2, so that match cuts and precise transitions can be achieved.

#### Acceptance Criteria

1. WHEN the VideoGenerator stage processes a video job with method "first_last_frame_interpolation", THE System SHALL call Veo 2 API with both first and last frame images
2. WHEN either frame image is missing, THE System SHALL mark the job as failed with a clear error message
3. WHEN Veo 2 returns a video, THE System SHALL save the video to the designated scene video directory path
4. WHERE the scene requires character consistency, THE System SHALL include character reference images in the API call
5. IF the total reference images (first frame + last frame + character refs) exceeds 3, THEN THE System SHALL prioritize first and last frames and omit character references

### Requirement 6: 11labs Integration for Audio Generation

**User Story:** As a pipeline user, I want voiceover audio generated using 11labs, so that scenes have professional narration.

#### Acceptance Criteria

1. WHEN the AudioGenerator stage processes the screenplay, THE System SHALL extract voiceover text and timing from the audio_track
2. WHEN voiceover text exists, THE System SHALL call 11labs API with the text and voice characteristics
3. WHEN 11labs returns audio, THE System SHALL save the audio file to the designated audio directory path
4. WHERE multiple voiceover segments exist, THE System SHALL generate each segment separately and track timing metadata
5. IF 11labs API fails, THEN THE System SHALL mark audio generation as failed but allow the pipeline to continue

### Requirement 7: Rate Limiting and Throttling

**User Story:** As a pipeline user, I want API calls to be rate-limited, so that I don't exceed provider quotas and incur additional costs.

#### Acceptance Criteria

1. THE System SHALL implement exponential backoff for all API retry attempts
2. THE System SHALL track API call counts per provider (Imagen, Veo, 11labs) in the job metadata
3. WHERE rate limit errors are returned by the API, THE System SHALL wait the specified retry-after duration before retrying
4. WHEN multiple jobs are pending, THE System SHALL process them sequentially to avoid parallel rate limit violations
5. THE System SHALL log all rate limit events with timestamps for debugging

### Requirement 8: Error Handling and Resumability

**User Story:** As a pipeline user, I want the pipeline to handle API failures gracefully, so that I can resume generation without losing progress.

#### Acceptance Criteria

1. WHEN an API call fails, THE System SHALL log the error details including job ID, API endpoint, and error message
2. WHEN a job fails, THE System SHALL mark it as FAILED in the database without stopping other jobs
3. WHERE a job fails due to transient errors (network, timeout), THE System SHALL retry up to 3 times with exponential backoff
4. WHEN a job fails due to permanent errors (invalid prompt, quota exceeded), THE System SHALL mark it as FAILED immediately without retrying
5. THE System SHALL save pipeline state to database after each stage completion, enabling resumability

### Requirement 9: Cost Tracking and Monitoring

**User Story:** As a pipeline user, I want to track API costs per job, so that I can monitor spending and optimize generation strategies.

#### Acceptance Criteria

1. THE System SHALL calculate estimated cost for each API call based on provider pricing
2. THE System SHALL store cost estimates in job metadata (cost_usd field)
3. WHEN a movie generation completes, THE System SHALL calculate and log total estimated cost
4. THE System SHALL provide a method to query total costs by movie_id
5. WHERE cost tracking is unavailable, THE System SHALL log a warning but continue execution

### Requirement 10: API Configuration and Credentials

**User Story:** As a pipeline user, I want API credentials managed securely, so that keys are not exposed in code or logs.

#### Acceptance Criteria

1. THE System SHALL load API credentials from environment variables (GOOGLE_API_KEY, ELEVENLABS_API_KEY)
2. WHEN credentials are missing, THE System SHALL raise a clear error message before attempting API calls
3. THE System SHALL never log API keys or credentials in any log output
4. WHERE multiple API keys are available (e.g., for load balancing), THE System SHALL support key rotation
5. THE System SHALL validate API credentials on initialization before processing jobs

### Requirement 11: FFmpeg Integration for Post-Production

**User Story:** As a pipeline user, I want videos stitched together with proper transitions using FFmpeg, so that the final movie has professional editing.

#### Acceptance Criteria

1. WHEN the VideoProcessingPipeline stage processes post-production jobs, THE System SHALL use FFmpeg to stitch videos
2. WHERE a scene requires trimming, THE System SHALL use FFmpeg to trim the video to the specified duration
3. WHEN a transition is specified (jump_cut, flow_cut, smash_cut), THE System SHALL apply the appropriate FFmpeg filter
4. WHERE text overlays are specified, THE System SHALL use FFmpeg drawtext filter to add text at specified timings
5. WHEN all scenes are processed, THE System SHALL concatenate all videos into a single final output file

### Requirement 12: Parallel Job Execution

**User Story:** As a pipeline user, I want independent jobs to execute in parallel, so that generation completes faster.

#### Acceptance Criteria

1. WHERE multiple character jobs exist, THE System SHALL execute them in parallel up to a configurable limit (default: 3)
2. WHERE multiple image jobs for different scenes exist, THE System SHALL execute them in parallel
3. THE System SHALL respect rate limits even when executing jobs in parallel
4. WHEN parallel execution is enabled, THE System SHALL use asyncio.gather for concurrent API calls
5. THE System SHALL provide a configuration option to disable parallel execution for debugging

### Requirement 13: Output Caching and Skip Logic

**User Story:** As a pipeline user, I want the system to skip regeneration if output files already exist and the screenplay hasn't changed, so that I don't waste API calls and costs on duplicate work.

#### Acceptance Criteria

1. WHEN a screenplay is loaded or generated, THE System SHALL compute a SHA256 hash of the screenplay JSON
2. WHEN the screenplay hash differs from the stored hash in the database, THE System SHALL invalidate all existing jobs and mark them as PENDING
3. WHEN a job is about to execute, THE System SHALL check if the output file already exists at the expected path
4. WHERE the output file exists and is valid (non-zero size) and the screenplay hash matches, THE System SHALL mark the job as COMPLETED and skip API call
5. WHEN the output file exists but is invalid (zero size or corrupted), THE System SHALL delete it and proceed with generation
6. THE System SHALL log cache hits with job ID and file path for monitoring
7. WHERE a force_regenerate flag is set, THE System SHALL ignore existing files and regenerate all jobs

### Requirement 14: API Call Monitoring and Logging

**User Story:** As a pipeline user, I want detailed logging of all API calls, so that I can debug issues and monitor usage patterns.

#### Acceptance Criteria

1. THE System SHALL log every API call with timestamp, provider, endpoint, and job ID
2. WHEN an API call succeeds, THE System SHALL log response time and output file size
3. WHEN an API call fails, THE System SHALL log the error code, error message, and retry attempt number
4. THE System SHALL maintain a running count of API calls per provider per movie generation
5. WHEN a movie generation completes, THE System SHALL log a summary of total API calls by provider

### Requirement 15: Cost Limits and Budget Tracking

**User Story:** As a pipeline user, I want to set cost limits, so that generation stops if estimated costs exceed my budget.

#### Acceptance Criteria

1. THE System SHALL accept an optional max_cost_usd parameter when starting movie generation
2. WHEN max_cost_usd is set, THE System SHALL calculate running cost total after each job completion
3. IF the running cost total exceeds max_cost_usd, THEN THE System SHALL log a warning but continue execution (non-blocking)
4. THE System SHALL provide a method to query current estimated cost at any point during generation
5. WHERE cost limit is exceeded, THE System SHALL mark the movie generation with a cost_limit_exceeded flag in metadata

### Requirement 16: ScreenplayBuilder Dual Mode Support

**User Story:** As a pipeline user, I want ScreenplayBuilder to accept either a script or pre-generated screenplay JSON, so that I can test and iterate faster without regenerating screenplays.

#### Acceptance Criteria

1. THE ScreenplayBuilder SHALL accept a new input type that can contain either script text OR screenplay JSON
2. WHEN screenplay JSON is provided, THE ScreenplayBuilder SHALL validate and return it directly without calling ScriptWriter/Enhancer crews
3. WHEN script text is provided, THE ScreenplayBuilder SHALL generate screenplay using ScriptWriter and Enhancer crews as normal
4. WHERE screenplay JSON is provided, THE System SHALL validate it contains required fields (scenes, video_config, character_description)
5. IF screenplay JSON validation fails, THEN THE ScreenplayBuilder SHALL raise a clear error message with details of missing fields

## Constraints

- All API integrations MUST maintain the existing pipeline architecture without breaking changes
- The System MUST NOT require changes to the screenplay extraction or job creation logic
- API calls MUST be implemented as async functions to support parallel execution
- The System MUST work with the existing SQLite job tracking database schema
- All API providers MUST be optional - the pipeline should run in mock mode if credentials are not provided
- Parallel execution MUST respect rate limits and not cause quota violations
- Cost limit warnings MUST be non-blocking - generation continues even if budget is exceeded
- Cache checking MUST be fast (< 100ms per file check) to avoid slowing down the pipeline

## Success Criteria

1. Character reference images are generated using Imagen 3 and saved to disk
2. Keyframe images are generated using Imagen 3 with character references
3. Videos are generated using all three Veo 2 methods (text-to-video, image-to-video, interpolation)
4. Voiceover audio is generated using 11labs
5. Videos are stitched together using FFmpeg with proper transitions
6. The pipeline handles API failures gracefully and can resume from any point
7. API costs are tracked and logged for each movie generation
8. Rate limiting prevents quota violations
9. The existing dry-run mode continues to work for testing
10. Parallel execution reduces total generation time by at least 40% for movies with 4+ scenes
11. Output caching prevents duplicate API calls when resuming failed generations
12. API call monitoring provides clear visibility into usage patterns and costs
13. Cost limit warnings alert users when budget is exceeded without blocking generation
14. MovieMaker supports both script-based and screenplay-JSON-based generation modes
