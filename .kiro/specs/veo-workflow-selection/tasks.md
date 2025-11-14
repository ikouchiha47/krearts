# Implementation Plan

## Overview
Implement intelligent workflow selection for Veo 3.1 video generation with config-based defaults, LLM-based decision making, and A/B testing capabilities.

## Tasks

- [x] 1. Create workflow selection data models and enums
  - Create `VeoWorkflowType` enum with all workflow types
  - Create `WorkflowSelectionMode` enum for selection strategies
  - Create `WorkflowClassification` dataclass for classification results
  - Create `WorkflowConfig` dataclass with all configuration options
  - _Requirements: 1.1, 6.1_

- [x] 2. Implement core WorkflowClassifier class
  - [x] 2.1 Create WorkflowClassifier with config-based initialization
    - Initialize with `WorkflowConfig` and optional Gemini client
    - Implement `classify_scene()` main entry point
    - Add logging for workflow decisions
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

  - [x] 2.2 Implement workflow detection methods
    - Implement `_has_first_and_last_frames()` checker
    - Implement `_has_character_references()` checker
    - Implement `_has_timestamp_actions()` checker
    - Implement `_has_single_keyframe()` checker
    - _Requirements: 1.1, 1.2, 1.3, 1.4_

  - [x] 2.3 Implement conflict resolution logic
    - Implement `_resolve_workflow_conflict()` for interpolation vs ingredients
    - Add support for CONFIG_DEFAULT mode
    - Add support for ALWAYS_INTERPOLATION mode
    - Add support for ALWAYS_INGREDIENTS mode
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6_

  - [x] 2.4 Implement LLM-based decision making
    - Implement `_llm_decide_workflow()` with acceptance criteria prompt
    - Build prompt with scene metadata and quality criteria
    - Parse LLM response to extract decision and reason
    - Add error handling and fallback to default
    - Log LLM decision and reasoning
    - _Requirements: 5.6, 8.1, 8.2, 8.3, 8.4_

- [x] 3. Implement WorkflowParameterBuilder class
  - [x] 3.1 Create parameter builder with workflow-specific methods
    - Implement `build_parameters()` main entry point
    - Route to workflow-specific builders based on type
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

  - [x] 3.2 Implement interpolation parameter builder
    - Implement `_build_interpolation_params()` with image and last_image
    - Build interpolation-specific prompt describing camera movement
    - Extract first_frame and last_frame asset paths
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 6.1_

  - [x] 3.3 Implement ingredients parameter builder
    - Implement `_build_ingredients_params()` with reference_images
    - Limit reference images to max 3
    - Build ingredients-specific prompt referencing provided images
    - Extract character reference asset paths
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 6.2_

  - [x] 3.4 Implement timestamp parameter builder
    - Implement `_build_timestamp_params()` with formatted prompt
    - Build timestamp-formatted prompt with [HH:MM:SS-HH:MM:SS] notation
    - Ensure timestamps are sequential and non-overlapping
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 6.3_

  - [x] 3.5 Implement text-to-video and image-to-video builders
    - Implement `_build_text_to_video_params()` with prompt only
    - Implement `_build_image_to_video_params()` with image parameter
    - _Requirements: 6.4, 6.5_

- [x] 4. Implement WorkflowValidator class
  - [x] 4.1 Create validator with workflow-specific validation
    - Implement `validate()` main entry point
    - Route to workflow-specific validators
    - Collect and return all validation errors
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

  - [x] 4.2 Implement interpolation validation
    - Validate both image and last_image parameters exist
    - Check that image files exist on disk
    - Validate no reference_images parameter (incompatible)
    - _Requirements: 7.1, 7.4_

  - [x] 4.3 Implement ingredients validation
    - Validate reference_images parameter exists
    - Check reference image count does not exceed 3
    - Check that reference image files exist on disk
    - Validate no last_image parameter (incompatible)
    - _Requirements: 7.2, 7.4_

  - [x] 4.4 Implement timestamp validation
    - Validate duration does not exceed 8 seconds
    - Validate prompt contains valid timestamp notation
    - Check timestamps are sequential
    - _Requirements: 7.3_

  - [x] 4.5 Implement common validations
    - Validate duration is between 4 and 8 seconds
    - Check for incompatible parameter combinations
    - _Requirements: 7.5_

- [x] 5. Implement VeoWorkflowOrchestrator class
  - [x] 5.1 Create orchestrator with workflow coordination
    - Initialize with GeminiMediaGen client and WorkflowConfig
    - Create instances of classifier, param builder, and validator
    - Initialize metrics tracker
    - _Requirements: 1.1, 5.1, 5.2, 5.3, 5.4, 5.5, 5.6_

  - [x] 5.2 Implement main generation workflow
    - Implement `generate_video_with_workflow()` main entry point
    - Step 1: Classify workflow using WorkflowClassifier
    - Step 2: Build parameters using WorkflowParameterBuilder
    - Step 3: Validate using WorkflowValidator
    - Step 4: Execute generation with GeminiMediaGen
    - Step 5: Track metrics
    - Add comprehensive logging at each step
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 5.6_

  - [x] 5.3 Add error handling and metrics tracking
    - Wrap generation in try-catch with metrics recording
    - Record success metrics with generation time
    - Record failure metrics with error message
    - Log all workflow decisions and outcomes
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_

- [x] 6. Implement WorkflowMetrics tracking
  - [x] 6.1 Create metrics data models
    - Create `WorkflowMetric` dataclass for single execution
    - Create `WorkflowMetrics` class for aggregation
    - _Requirements: 9.1, 9.2, 9.3_

  - [x] 6.2 Implement metrics collection
    - Implement `record_success()` method
    - Implement `record_failure()` method
    - Store workflow type, scene ID, timing, and errors
    - _Requirements: 9.1, 9.2, 9.3_

  - [x] 6.3 Implement metrics reporting
    - Implement `get_summary()` for aggregated statistics
    - Calculate success rates per workflow type
    - Calculate average generation times
    - Implement `export_to_json()` for persistence
    - _Requirements: 9.4, 9.5_

- [ ]* 7. Implement A/B testing support (OPTIONAL - Skip for now)
  - [ ] 7.1 Create ABTestOrchestrator class
    - Initialize with GeminiMediaGen and WorkflowConfig
    - Implement `generate_ab_test()` main entry point
    - _Requirements: 1.1, 5.1, 5.2, 5.3, 5.4, 5.5, 5.6_

  - [ ] 7.2 Implement dual workflow generation
    - Generate video with ALWAYS_INTERPOLATION config
    - Generate video with ALWAYS_INGREDIENTS config
    - Handle failures gracefully (continue if one fails)
    - Return dict mapping workflow_type to video_path
    - _Requirements: 1.1, 1.2, 1.3_

  - [ ] 7.3 Implement A/B test manifest generation
    - Create manifest with scene metadata
    - Include both video paths
    - Add review_notes section for manual annotation
    - Save manifest to ab_test_output_dir
    - _Requirements: 8.1, 8.2, 8.3, 8.4_

- [ ]* 8. Implement WorkflowKnowledgeBase for learning (OPTIONAL - Skip for now)
  - [ ] 8.1 Create knowledge base collector
    - Implement `collect_reviewed_tests()` to find annotated A/B tests
    - Filter for tests with winner annotation
    - _Requirements: 9.5_

  - [ ] 8.2 Implement training data generation
    - Implement `generate_training_data()` from reviewed tests
    - Extract scene metadata and winner
    - Format for future fine-tuning or rule generation
    - _Requirements: 9.5_

  - [ ] 8.3 Implement knowledge base export
    - Implement `export_knowledge_base()` to JSON
    - Include version and sample count
    - _Requirements: 9.5_

- [x] 9. Implement CharacterReferenceManager with seeding chain
  - [x] 9.1 Create CharacterReferenceManager class
    - Initialize with GeminiMediaGen client
    - Create character_cache dictionary for storing references
    - _Requirements: 3.1.1, 3.1.2, 3.1.3, 3.1.4, 3.1.5_

  - [x] 9.2 Implement character reference generation with seeding
    - Implement `generate_character_references()` main method
    - Step 1: Generate front view without reference (canonical)
    - Step 2: Generate side view using front as reference_image
    - Step 3: Generate full_body using front as reference_image
    - Cache all references for future use
    - _Requirements: 3.1.1, 3.1.2, 3.1.3_

  - [x] 9.3 Implement character-consistent keyframe generation
    - Implement `generate_keyframe_with_character()` method
    - Use cached front view as reference_image
    - Log which character reference is being used
    - _Requirements: 3.1.3, 3.1.4_

  - [x] 9.4 Implement moodboard generation with character
    - Implement `generate_moodboard_with_character()` method
    - Use cached front view as reference_image for character consistency
    - Support scene-specific environment descriptions
    - _Requirements: 3.1.4_

  - [x] 9.5 Implement character reference utilities
    - Implement `get_canonical_reference()` to retrieve front view
    - Implement `_build_character_prompt()` for each view type
    - Add validation for cached characters
    - _Requirements: 3.1.5_

  - [x] 9.6 Add back view support for POV/behind shots
    - Extend `generate_character_references_extended()` to include back view
    - Add `include_back_view` parameter (default: True)
    - Generate back view seeded from front view
    - Update `_build_character_prompt()` to support "back" view type
    - _Requirements: 3.1.2, 3.1.3_

  - [x] 9.7 Implement smart reference selection
    - Implement `get_reference_for_shot()` to auto-select view
    - Detect "from behind", "POV", "rear view" keywords → use back view
    - Detect "side", "profile" keywords → use side view
    - Detect "full body", "wide shot" keywords → use full_body view
    - Default to front view for all other shots
    - _Requirements: 3.1.4, 3.1.5_

  - [x] 9.8 Implement smart keyframe generation
    - Implement `generate_keyframe_smart()` method
    - Automatically select appropriate reference based on shot description
    - Log which reference view is being used
    - _Requirements: 3.1.3, 3.1.4_

- [-] 10. Implement ScreenplayEnhancer for view detection
  - [x] 10.1 Create ScreenplayEnhancer class
    - Implement `enhance_character_views()` main method
    - Analyze screenplay and add required_views to characters
    - _Requirements: 3.1.1, 3.1.2_

  - [x] 10.2 Implement view detection logic
    - Implement `_analyze_character_views()` method
    - Detect back view: "following", "tracking", "from behind", "POV"
    - Detect side view: "profile", "side angle", "side view"
    - Detect full_body: "wide shot", "establishing shot", "full body"
    - Always include front view (canonical)
    - _Requirements: 3.1.2, 3.1.3_

  - [x] 10.3 Implement detection metadata
    - Implement `_get_scenes_with_character()` to list scenes
    - Implement `_get_detection_reasons()` for transparency
    - Add view_analysis to character description
    - Log detection reasons for debugging
    - _Requirements: 3.1.2_

  - [ ] 10.4 Integrate with CharacterReferenceManager
    - Implement `generate_from_screenplay()` method
    - Read required_views from enhanced screenplay
    - Generate only required views using seeding chain
    - Skip unnecessary views for cost optimization
    - _Requirements: 3.1.1, 3.1.2, 3.1.3_

- [x] 11. Integration with existing GeminiMediaGen
  - [x] 11.1 Verify GeminiMediaGen API compatibility
    - Confirm generate_video() supports all required parameters
    - Test image, last_image, reference_images parameters
    - Verify parameter type compatibility (ImageInput)
    - Test generate_content() with reference_image parameter
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 3.1, 3.2, 3.3, 3.4_

  - [x] 11.2 Create integration helper functions
    - Create helper to convert scene metadata to classifier input
    - Create helper to map asset IDs to file paths
    - Add logging integration
    - _Requirements: 1.1, 1.5_

  - [x] 11.3 Update movie_maker.py to use CharacterReferenceManager
    - Replace independent character view generation with seeding chain
    - Update VisualCharacterBuilder to use CharacterReferenceManager
    - Ensure front view is generated first, then side and full_body
    - _Requirements: 3.1.1, 3.1.2, 3.1.3_

  - [x] 11.4 Update movie_maker.py to use workflow orchestrator
    - Replace direct generate_video calls with orchestrator
    - Pass WorkflowConfig from pipeline config
    - Log workflow decisions in pipeline
    - _Requirements: 1.1, 5.6_

- [ ] 12. Add configuration file support
  - [ ] 12.1 Create workflow config schema
    - Define JSON schema for WorkflowConfig
    - Add to config.json or separate workflow_config.json
    - Document all configuration options
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6_

  - [ ] 12.2 Implement config loading
    - Load workflow config from file
    - Merge with defaults
    - Validate config values
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6_

- [x] 13. Create example scripts and documentation
  - [x] 13.1 Create example script for config-based selection
    - Example using CONFIG_DEFAULT mode
    - Example using ALWAYS_INTERPOLATION mode
    - Example using ALWAYS_INGREDIENTS mode
    - _Requirements: 8.1, 8.2, 8.3, 8.4_

  - [x] 13.2 Create example script for LLM-based selection
    - Example using LLM_INTELLIGENT mode
    - Show LLM decision logging
    - _Requirements: 8.1, 8.2, 8.3, 8.4_

  - [x] 13.3 Create example script for A/B testing
    - Example generating both workflows
    - Example reviewing A/B test results
    - Example building knowledge base
    - _Requirements: 8.1, 8.2, 8.3, 8.4_

  - [x] 13.4 Create usage documentation
    - Document all workflow types and when to use them
    - Document configuration options
    - Document A/B testing workflow
    - Add troubleshooting guide
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

- [ ]* 14. Add comprehensive testing
  - [ ]* 14.1 Create unit tests for WorkflowClassifier
    - Test classification of each workflow type
    - Test conflict resolution logic
    - Test LLM decision making (mocked)
    - Test forced workflow modes
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

  - [ ]* 14.2 Create unit tests for WorkflowParameterBuilder
    - Test parameter building for each workflow
    - Test prompt generation
    - Test asset path extraction
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

  - [ ]* 14.3 Create unit tests for WorkflowValidator
    - Test validation for each workflow type
    - Test incompatible parameter detection
    - Test file existence checks
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

  - [ ]* 14.4 Create unit tests for CharacterReferenceManager
    - Test seeding chain (front → side → full_body)
    - Test character cache management
    - Test keyframe generation with character reference
    - Test moodboard generation with character reference
    - _Requirements: 3.1.1, 3.1.2, 3.1.3, 3.1.4, 3.1.5_

  - [ ]* 14.5 Create unit tests for ScreenplayEnhancer
    - Test view detection from scene descriptions
    - Test keyword matching for back/side/full_body views
    - Test detection reasons and metadata
    - _Requirements: 3.1.2_

  - [ ]* 14.6 Create integration tests with real API
    - Test full workflow with interpolation
    - Test full workflow with ingredients
    - Test A/B testing generation
    - Test metrics tracking
    - _Requirements: 1.1, 2.1, 3.1, 4.1, 9.1, 9.2, 9.3, 9.4, 9.5_
