# Requirements Document

## Introduction

The current Veo video generation system needs to support all three Veo 3.1 workflow types so we can experiment and determine which works best for different scenarios. Veo 3.1 supports three distinct workflows: First and Last Frame interpolation, Ingredients to Video (composition with reference images), and Timestamp Prompting. The system must implement Python methods for each workflow type, allowing manual testing and experimentation before building automatic workflow selection logic.

## Glossary

- **Veo 3.1**: Google's video generation model with multiple workflow types
- **First and Last Frame Workflow**: Veo feature that interpolates video between two provided keyframe images
- **Ingredients to Video Workflow**: Veo feature that composes a scene using reference images for characters and settings
- **Timestamp Prompting Workflow**: Veo feature that creates videos with multiple sequential actions using timestamp notation [HH:MM:SS-HH:MM:SS]
- **Reference Image**: An image provided to guide character, object, or environment consistency (max 3 per generation)
- **Keyframe**: A still image representing a specific moment in the video timeline
- **Scene Classification**: The process of analyzing scene metadata to determine optimal workflow
- **GeminiMediaGen**: The Python class that interfaces with Google's GenAI API for video generation

## Requirements

### Requirement 1: Three Workflow Method Implementation

**User Story:** As a developer, I want three separate Python methods in GeminiMediaGen for each Veo workflow type, so that I can manually test and experiment with each workflow independently.

#### Acceptance Criteria

1. WHEN the GeminiMediaGen class is implemented, THE System SHALL provide a method for first_last_frame_interpolation workflow
2. WHEN the GeminiMediaGen class is implemented, THE System SHALL provide a method for ingredients_to_video workflow
3. WHEN the GeminiMediaGen class is implemented, THE System SHALL provide a method for timestamp_prompting workflow
4. WHEN each method is implemented, THE System SHALL include clear docstrings explaining parameters and usage
5. WHEN each method is implemented, THE System SHALL include example usage in the docstring

### Requirement 2: First and Last Frame Workflow Implementation

**User Story:** As a video producer, I want scenes with defined start and end states to use first/last frame interpolation, so that I get smooth transitions between two specific visual moments.

#### Acceptance Criteria

1. WHEN the System executes a first_last_frame_interpolation workflow, THE System SHALL call GeminiMediaGen.generate_video with both image and last_image parameters
2. WHEN the System provides keyframes for interpolation, THE System SHALL ensure both images are generated using Imagen before video generation
3. WHEN the System builds the Veo prompt for interpolation, THE System SHALL describe the motion and transformation between the two frames
4. WHEN the System uses interpolation workflow, THE System SHALL NOT include reference_images parameter (incompatible with last_frame)
5. WHEN the System generates interpolation videos, THE System SHALL validate that visual continuity elements (lighting, character position) are compatible between frames

### Requirement 3: Ingredients to Video Workflow Implementation

**User Story:** As a video producer, I want dialogue scenes with consistent characters to use the ingredients workflow, so that character appearance remains consistent across the video.

#### Acceptance Criteria

1. WHEN the System executes an ingredients_to_video workflow, THE System SHALL call GeminiMediaGen.generate_video with reference_images parameter containing character and setting references
2. WHEN the System provides reference images, THE System SHALL limit to maximum 3 reference images as per Veo specifications
3. WHEN the System builds the Veo prompt for ingredients workflow, THE System SHALL reference the provided images in the prompt text (e.g., "Using the provided images for the detective...")
4. WHEN the System uses ingredients workflow, THE System SHALL NOT include last_image parameter (incompatible with reference_images)
5. WHEN the System generates character reference images, THE System SHALL create neutral pose images suitable for composition

### Requirement 3.1: Character Reference Seeding Chain

**User Story:** As a video producer, I want character reference images to be generated using a seeding chain, so that all character views maintain consistent appearance.

#### Acceptance Criteria

1. WHEN the System generates character reference images, THE System SHALL generate the front view first without any reference image
2. WHEN the System generates additional character views (side, full_body), THE System SHALL use the front view as reference_image to ensure consistency
3. WHEN the System generates keyframe images with characters, THE System SHALL use the front view character reference as reference_image
4. WHEN the System generates moodboard or scene-specific images, THE System SHALL use the front view character reference to maintain character consistency
5. WHEN the System uses character references in video generation, THE System SHALL prioritize the front view as the canonical character reference

### Requirement 4: Timestamp Prompting Workflow Implementation

**User Story:** As a video producer, I want complex single-shot sequences to use timestamp prompting, so that I can create videos with multiple actions within one generation without cuts.

#### Acceptance Criteria

1. WHEN the System executes a timestamp_prompting workflow, THE System SHALL format the prompt using timestamp notation [HH:MM:SS-HH:MM:SS] for each action segment
2. WHEN the System builds timestamp prompts, THE System SHALL ensure timestamps are sequential and non-overlapping
3. WHEN the System uses timestamp prompting, THE System SHALL ensure the total duration matches the scene duration and does not exceed 8 seconds
4. WHEN the System builds timestamp segments, THE System SHALL include cinematography, subject, and action details for each segment
5. WHEN the System uses timestamp prompting, THE System SHALL ensure smooth narrative flow between timestamp segments

### Requirement 5: Manual Workflow Testing Support

**User Story:** As a developer, I want to easily test each workflow with sample inputs, so that I can evaluate quality and determine which workflow works best for different scenarios.

#### Acceptance Criteria

1. WHEN the System implements workflows, THE System SHALL allow manual specification of which workflow to use
2. WHEN testing workflows, THE System SHALL provide clear logging of which workflow is being executed
3. WHEN testing workflows, THE System SHALL log all API parameters being sent to Veo
4. WHEN a workflow execution completes, THE System SHALL log the generation time and output file path
5. WHEN a workflow execution fails, THE System SHALL log the error message and parameters that caused the failure

### Requirement 6: API Parameter Mapping

**User Story:** As a developer, I want clear mapping between workflow types and GeminiMediaGen API parameters, so that I can correctly implement each workflow in Python code.

#### Acceptance Criteria

1. WHEN the System uses first_last_frame_interpolation, THE System SHALL call generate_video with parameters: prompt, image, last_image, duration
2. WHEN the System uses ingredients_to_video, THE System SHALL call generate_video with parameters: prompt, reference_images, duration
3. WHEN the System uses timestamp_prompting, THE System SHALL call generate_video with parameters: prompt, duration (with timestamp-formatted prompt)
4. WHEN the System uses text_to_video, THE System SHALL call generate_video with parameters: prompt, duration
5. WHEN the System uses image_to_video, THE System SHALL call generate_video with parameters: prompt, image, duration

### Requirement 7: Workflow Validation

**User Story:** As a video producer, I want the system to validate workflow compatibility before generation, so that I avoid API errors and wasted generation attempts.

#### Acceptance Criteria

1. WHEN the System selects first_last_frame_interpolation, THE System SHALL validate that both first_frame and last_frame images exist
2. WHEN the System selects ingredients_to_video, THE System SHALL validate that reference_images count does not exceed 3
3. WHEN the System selects timestamp_prompting, THE System SHALL validate that total duration does not exceed 8 seconds
4. WHEN the System detects incompatible parameters (e.g., last_image + reference_images), THE System SHALL raise a validation error before API call
5. WHEN validation fails, THE System SHALL provide a clear error message indicating the incompatibility and suggested fix

### Requirement 8: Workflow Documentation and Examples

**User Story:** As a developer, I want clear code examples for each workflow type, so that I can understand how to implement and test each workflow.

#### Acceptance Criteria

1. WHEN the System implements workflow selection, THE System SHALL include code comments documenting each workflow type
2. WHEN the System provides examples, THE System SHALL include sample API calls for each workflow type
3. WHEN the System documents workflows, THE System SHALL include parameter requirements and constraints for each type
4. WHEN the System documents workflows, THE System SHALL include example scene metadata that triggers each workflow
5. WHEN the System provides examples, THE System SHALL include expected output and common error cases

### Requirement 9: Workflow Comparison and Evaluation

**User Story:** As a developer, I want to compare the results of different workflows on the same scene, so that I can determine which workflow produces the best quality for different scene types.

#### Acceptance Criteria

1. WHEN the System implements workflows, THE System SHALL support generating the same scene with different workflows for comparison
2. WHEN comparing workflows, THE System SHALL log the workflow type, generation parameters, and output path for each attempt
3. WHEN comparing workflows, THE System SHALL preserve all generated videos for side-by-side comparison
4. WHEN workflow testing is complete, THE System SHALL provide a summary of which workflows were tested and their outputs
5. WHEN evaluating workflows, THE System SHALL document observations about quality, consistency, and prompt adherence for each workflow type
