# Veo Workflow Selection Guide

Complete guide to using the intelligent workflow selection system for Veo 3.1 video generation.

## Table of Contents

1. [Overview](#overview)
2. [Workflow Types](#workflow-types)
3. [Selection Modes](#selection-modes)
4. [Configuration](#configuration)
5. [Usage Examples](#usage-examples)
6. [A/B Testing](#ab-testing)
7. [Troubleshooting](#troubleshooting)
8. [Best Practices](#best-practices)

## Overview

The Veo Workflow Selection system automatically chooses the optimal video generation workflow based on scene metadata. It supports:

- **5 workflow types**: Interpolation, Ingredients, Timestamp, Image-to-Video, Text-to-Video
- **4 selection modes**: Config Default, LLM Intelligent, Always Interpolation, Always Ingredients
- **Automatic validation**: Ensures parameters are compatible before generation
- **Metrics tracking**: Records success rates and generation times
- **A/B testing**: Compare workflows side-by-side

### Architecture

```
Scene Metadata → Classifier → Parameter Builder → Validator → GeminiMediaGen
                     ↓
              WorkflowConfig
```

## Workflow Types

### 1. First and Last Frame Interpolation

**When to use:**
- Scene describes clear camera movement (dolly, pan, zoom)
- Transformation between two defined states
- Gradual framing changes
- Subject stays relatively consistent

**Requirements:**
- Both `first_frame` and `last_frame` keyframe images
- Visual continuity between frames
- Cannot use with `reference_images`

**API Parameters:**
```python
{
    "prompt": "Describe the motion/transformation",
    "image": "path/to/first_frame.png",
    "last_image": "path/to/last_frame.png",
    "duration": 4.0
}
```

**Example scenes:**
- "Dolly shot pushing in from medium to close-up"
- "Pan from left to right across cityscape"
- "Character walks from background to foreground"

**Quality criteria:**
- ✅ Subject position stays relatively consistent
- ✅ Framing changes are gradual (NOT wide → extreme close-up)
- ✅ Clear spatial continuity (same location)
- ✅ Camera movement explicitly described
- ✅ Background not too complex/chaotic

### 2. Ingredients to Video

**When to use:**
- Dialogue scenes with characters
- Multi-character interactions
- Need consistent character appearance
- Composition-focused (not transformation)

**Requirements:**
- Character reference images (max 3)
- Prompt must reference provided images
- Cannot use with `last_image`

**API Parameters:**
```python
{
    "prompt": "Using the provided images for [characters], create...",
    "reference_images": ["char1.png", "char2.png"],
    "duration": 4.0
}
```

**Example scenes:**
- "Detective behind desk talking to woman"
- "Two characters having conversation in cafe"
- "Character interacting with specific product"

### 3. Timestamp Prompting

**When to use:**
- Single continuous shot with multiple sequential actions
- Complex choreography within one take
- Precise timing needed for actions

**Requirements:**
- Total duration ≤ 8 seconds
- Actions must be sequential, not simultaneous
- Timestamp notation in prompt

**API Parameters:**
```python
{
    "prompt": "[00:00:00-00:00:02] action 1. [00:00:02-00:00:04] action 2.",
    "duration": 6.0
}
```

**Example scenes:**
- "Character picks up phone [0-2s], answers [2-4s], reacts [4-6s]"
- "Camera starts wide [0-2s], pushes in [2-5s], ends close-up [5-8s]"

### 4. Image-to-Video

**When to use:**
- Starting from specific visual composition
- Animating a still image
- Only first frame defined, natural motion from there

**API Parameters:**
```python
{
    "prompt": "Describe motion from this starting point",
    "image": "path/to/first_frame.png",
    "duration": 4.0
}
```

### 5. Text-to-Video

**When to use:**
- Simple scene without specific visual constraints
- No character consistency requirements
- No complex transformations
- Default fallback

**API Parameters:**
```python
{
    "prompt": "Full scene description",
    "duration": 4.0
}
```

## Selection Modes

### CONFIG_DEFAULT

Use configured default workflow when conflicts exist.

**When to use:**
- You want consistent, predictable behavior
- Testing specific workflow types
- You know which workflow works best for your content

**Configuration:**
```python
config = WorkflowConfig(
    selection_mode=WorkflowSelectionMode.CONFIG_DEFAULT,
    default_workflow=VeoWorkflowType.INGREDIENTS_TO_VIDEO
)
```

**Behavior:**
- If scene supports both interpolation and ingredients → use default
- If scene supports only one workflow → use that workflow
- Fast and deterministic

### LLM_INTELLIGENT

Use LLM to analyze scenes and make intelligent decisions.

**When to use:**
- Production workflows with varied scenes
- Quality is more important than speed
- You want adaptive decision-making

**Configuration:**
```python
config = WorkflowConfig(
    selection_mode=WorkflowSelectionMode.LLM_INTELLIGENT,
    llm_model="gemini-2.0-flash-exp"
)
```

**Behavior:**
- LLM analyzes scene characteristics
- Considers quality criteria (framing, continuity, etc.)
- Provides reasoning for transparency
- Falls back to default if LLM fails

**Decision factors:**
- Transformation vs composition
- Character consistency needs
- Motion type and complexity
- Available assets

### ALWAYS_INTERPOLATION

Force interpolation workflow for ALL scenes.

**When to use:**
- Testing interpolation quality across scenes
- You know interpolation works best for your content
- Experimentation and comparison

**Configuration:**
```python
config = WorkflowConfig(
    selection_mode=WorkflowSelectionMode.ALWAYS_INTERPOLATION
)
```

**Behavior:**
- Forces interpolation regardless of scene characteristics
- Adds warning to classification
- May result in poor quality if scene unsuitable

### ALWAYS_INGREDIENTS

Force ingredients workflow for ALL scenes.

**When to use:**
- Testing character consistency
- You prioritize character appearance over motion
- Experimentation and comparison

**Configuration:**
```python
config = WorkflowConfig(
    selection_mode=WorkflowSelectionMode.ALWAYS_INGREDIENTS
)
```

**Behavior:**
- Forces ingredients regardless of scene characteristics
- Adds warning to classification
- Requires character references

## Configuration

### WorkflowConfig Options

```python
from cinema.workflow.models import WorkflowConfig, WorkflowSelectionMode, VeoWorkflowType

config = WorkflowConfig(
    # Selection mode
    selection_mode=WorkflowSelectionMode.LLM_INTELLIGENT,
    
    # Default workflow (used as fallback)
    default_workflow=VeoWorkflowType.INGREDIENTS_TO_VIDEO,
    
    # Enable/disable specific workflows
    enable_interpolation=True,
    enable_ingredients=True,
    enable_timestamp=True,
    
    # LLM settings
    use_llm_for_workflow_decision=True,
    llm_model="gemini-2.0-flash-exp",
    
    # A/B testing
    ab_test_enabled=False,
    ab_test_output_dir="output/ab_test",
    
    # Quality thresholds
    interpolation_quality_threshold=0.6,
    
    # Validation
    strict_validation=True,
    allow_missing_assets=False,
    
    # Performance
    enable_classification_cache=True,
    max_reference_images=3,
    
    # Logging
    log_workflow_decisions=True,
    export_metrics=True,
    metrics_output_path="output/workflow_metrics.json"
)
```

### Scene Metadata Format

```python
scene = {
    "scene_id": "S1_detective_office",
    "duration": 4.0,
    "description": "Detective behind desk, camera pushes in",
    
    # Cinematography
    "cinematography": {
        "camera_movement": {
            "movement_type": "dolly",  # dolly, pan, zoom, static
            "description": "Push in from medium to close-up"
        }
    },
    
    # Keyframes (for interpolation)
    "keyframe_description": {
        "first_frame_prompt": "Medium shot of detective behind desk",
        "last_frame_prompt": "Close-up of detective's face"
    },
    
    # Characters (for ingredients)
    "character_ids": ["detective_001"],
    
    # Dialogue (indicates ingredients may be better)
    "dialogue": "Of all the offices in this town...",
    
    # Timestamp actions (for timestamp prompting)
    "action_sequences": [
        {
            "start_time": "00:00:00",
            "end_time": "00:00:02",
            "description": "Character picks up phone",
            "timestamp": 0.0
        }
    ]
}
```

### Asset Paths Format

```python
assets = {
    # Keyframe images (for interpolation)
    "S1_detective_office_first_frame": "output/images/S1_first.png",
    "S1_detective_office_last_frame": "output/images/S1_last.png",
    
    # Character references (for ingredients)
    "detective_001_reference": "output/refs/detective.png",
    "woman_001_reference": "output/refs/woman.png"
}
```

## Usage Examples

### Basic Usage

```python
import asyncio
from cinema.providers.gemini import GeminiMediaGen
from cinema.workflow.models import WorkflowConfig
from cinema.workflow.orchestrator import VeoWorkflowOrchestrator

async def generate_video():
    # Initialize
    gemini = GeminiMediaGen()
    config = WorkflowConfig()  # Uses defaults
    orchestrator = VeoWorkflowOrchestrator(gemini, config)
    
    # Define scene
    scene = {
        "scene_id": "S1",
        "duration": 4.0,
        "keyframe_description": {
            "first_frame_prompt": "Start frame",
            "last_frame_prompt": "End frame"
        }
    }
    
    assets = {
        "S1_first_frame": "output/S1_first.png",
        "S1_last_frame": "output/S1_last.png"
    }
    
    # Generate
    video_path, classification = await orchestrator.generate_video_with_workflow(
        scene, assets
    )
    
    print(f"Video: {video_path}")
    print(f"Workflow: {classification.workflow_type.value}")
    print(f"Reason: {classification.reason}")

asyncio.run(generate_video())
```

### Config-Based Selection

```python
# Use ingredients as default
config = WorkflowConfig(
    selection_mode=WorkflowSelectionMode.CONFIG_DEFAULT,
    default_workflow=VeoWorkflowType.INGREDIENTS_TO_VIDEO
)

orchestrator = VeoWorkflowOrchestrator(gemini, config)
video_path, classification = await orchestrator.generate_video_with_workflow(
    scene, assets
)
```

### LLM-Based Selection

```python
# Let LLM decide
config = WorkflowConfig(
    selection_mode=WorkflowSelectionMode.LLM_INTELLIGENT
)

orchestrator = VeoWorkflowOrchestrator(gemini, config)
video_path, classification = await orchestrator.generate_video_with_workflow(
    scene, assets
)

# LLM provides reasoning
print(f"LLM decided: {classification.workflow_type.value}")
print(f"Reason: {classification.reason}")
```

### Force Specific Workflow

```python
# Force interpolation
config = WorkflowConfig(
    selection_mode=WorkflowSelectionMode.ALWAYS_INTERPOLATION
)

orchestrator = VeoWorkflowOrchestrator(gemini, config)
video_path, classification = await orchestrator.generate_video_with_workflow(
    scene, assets
)
```

### Get Metrics

```python
# After generating multiple videos
summary = orchestrator.get_metrics_summary()

print(f"Interpolation success rate: {summary['first_last_frame_interpolation']['success_rate']}")
print(f"Average generation time: {summary['first_last_frame_interpolation']['avg_generation_time']}s")

# Export metrics
orchestrator.export_metrics("output/metrics.json")
```

## A/B Testing

### Generate A/B Tests

```python
from examples.workflow_ab_testing import ABTestOrchestrator

config = WorkflowConfig(
    ab_test_enabled=True,
    ab_test_output_dir="output/ab_test"
)

ab_tester = ABTestOrchestrator(gemini, config)

# Generate with both workflows
results = await ab_tester.generate_ab_test(scene, assets)

print(f"Interpolation: {results['interpolation']}")
print(f"Ingredients: {results['ingredients']}")
```

### Review A/B Tests

1. Find manifest files in `output/ab_test/`
2. Watch both videos
3. Edit manifest JSON:

```json
{
  "review_notes": {
    "interpolation_quality": "4",
    "interpolation_notes": "Smooth motion, slight blur",
    "ingredients_quality": "3",
    "ingredients_notes": "Character consistent but stiff",
    "winner": "interpolation",
    "overall_notes": "Interpolation works better for this dolly shot"
  }
}
```

### Build Knowledge Base

```python
from examples.workflow_ab_testing import WorkflowKnowledgeBase

kb = WorkflowKnowledgeBase("output/ab_test")

# Collect reviewed tests
reviewed = kb.collect_reviewed_tests()
print(f"Found {len(reviewed)} reviewed tests")

# Generate training data
training_data = kb.generate_training_data()

# Export
kb.export_knowledge_base("output/knowledge_base.json")
```

## Troubleshooting

### Validation Errors

**Error: "Missing 'image' parameter for interpolation"**

Solution: Ensure keyframe images are generated and asset paths are correct.

```python
# Check assets
print(assets)  # Should include first_frame and last_frame

# Verify files exist
from pathlib import Path
assert Path(assets["S1_first_frame"]).exists()
```

**Error: "Cannot use 'reference_images' with 'last_image'"**

Solution: Interpolation and ingredients are mutually exclusive. Choose one workflow.

```python
# Force one workflow
config = WorkflowConfig(
    selection_mode=WorkflowSelectionMode.ALWAYS_INTERPOLATION
)
```

**Error: "Too many reference images: 4. Maximum is 3"**

Solution: Limit character references to 3.

```python
# Limit characters
scene["character_ids"] = scene["character_ids"][:3]
```

### Classification Issues

**Problem: LLM always chooses ingredients**

Solution: Check scene metadata. LLM may be detecting dialogue or multiple characters.

```python
# Remove dialogue to test
scene_copy = scene.copy()
scene_copy.pop("dialogue", None)

# Or force interpolation
config = WorkflowConfig(
    selection_mode=WorkflowSelectionMode.ALWAYS_INTERPOLATION
)
```

**Problem: LLM decision fails**

Solution: System automatically falls back to default workflow. Check logs for error.

```python
# Enable debug logging
import logging
logging.getLogger("cinema.workflow.classifier").setLevel(logging.DEBUG)

# Set reliable fallback
config = WorkflowConfig(
    selection_mode=WorkflowSelectionMode.LLM_INTELLIGENT,
    default_workflow=VeoWorkflowType.INGREDIENTS_TO_VIDEO
)
```

### Generation Failures

**Problem: Interpolation produces poor quality**

Possible causes:
- Extreme framing change (wide → extreme close-up)
- Subject moves too far between frames
- Complex/chaotic background
- Lighting changes dramatically

Solutions:
1. Use ingredients workflow instead
2. Generate intermediate keyframes
3. Adjust scene to have more gradual changes

**Problem: Ingredients doesn't maintain character consistency**

Possible causes:
- Reference images not high quality
- Too many characters (>3)
- Reference images don't match scene context

Solutions:
1. Improve reference image quality
2. Reduce number of characters
3. Generate scene-specific references

### Performance Issues

**Problem: Classification is slow**

Solution: Use CONFIG_DEFAULT mode instead of LLM_INTELLIGENT.

```python
config = WorkflowConfig(
    selection_mode=WorkflowSelectionMode.CONFIG_DEFAULT
)
```

**Problem: Too many API calls**

Solution: Enable classification caching.

```python
config = WorkflowConfig(
    enable_classification_cache=True
)
```

## Best Practices

### 1. Start with LLM_INTELLIGENT

Let the LLM analyze your scenes and make decisions. Review the results and adjust if needed.

```python
config = WorkflowConfig(
    selection_mode=WorkflowSelectionMode.LLM_INTELLIGENT,
    log_workflow_decisions=True
)
```

### 2. Use A/B Testing for Evaluation

Generate both workflows for key scenes and compare quality.

```python
# Test important scenes
important_scenes = [scene1, scene2, scene3]

for scene in important_scenes:
    results = await ab_tester.generate_ab_test(scene, assets)
    # Review and annotate
```

### 3. Build Knowledge Base

Collect reviewed A/B tests to understand patterns.

```python
kb = WorkflowKnowledgeBase("output/ab_test")
training_data = kb.generate_training_data()

# Analyze patterns
interpolation_wins = [t for t in training_data if t['winner'] == 'interpolation']
# What do they have in common?
```

### 4. Monitor Metrics

Track success rates and generation times.

```python
summary = orchestrator.get_metrics_summary()

# Check success rates
for workflow, stats in summary.items():
    print(f"{workflow}: {stats['success_rate']:.1%} success")
```

### 5. Validate Scene Metadata

Ensure scene metadata is complete and accurate.

```python
def validate_scene(scene):
    assert "scene_id" in scene
    assert "duration" in scene
    
    # Check for workflow requirements
    has_keyframes = "keyframe_description" in scene
    has_characters = bool(scene.get("character_ids"))
    
    if not has_keyframes and not has_characters:
        print("Warning: Scene may default to text-to-video")
```

### 6. Handle Failures Gracefully

Implement fallback strategies.

```python
try:
    video_path, classification = await orchestrator.generate_video_with_workflow(
        scene, assets
    )
except ValueError as e:
    # Validation error - fix scene metadata
    logger.error(f"Validation failed: {e}")
    # Try with different workflow
    config.selection_mode = WorkflowSelectionMode.ALWAYS_INGREDIENTS
    video_path, classification = await orchestrator.generate_video_with_workflow(
        scene, assets
    )
except Exception as e:
    # Generation error - log and continue
    logger.error(f"Generation failed: {e}")
```

### 7. Optimize for Your Content

Different content types may benefit from different defaults.

```python
# For dialogue-heavy content
dialogue_config = WorkflowConfig(
    selection_mode=WorkflowSelectionMode.CONFIG_DEFAULT,
    default_workflow=VeoWorkflowType.INGREDIENTS_TO_VIDEO
)

# For camera movement content
movement_config = WorkflowConfig(
    selection_mode=WorkflowSelectionMode.CONFIG_DEFAULT,
    default_workflow=VeoWorkflowType.FIRST_LAST_FRAME_INTERPOLATION
)
```

### 8. Use Appropriate Selection Mode

Choose based on your needs:

| Need | Selection Mode |
|------|----------------|
| Consistent behavior | CONFIG_DEFAULT |
| Adaptive decisions | LLM_INTELLIGENT |
| Testing interpolation | ALWAYS_INTERPOLATION |
| Testing ingredients | ALWAYS_INGREDIENTS |
| Quality comparison | A/B Testing |

## Additional Resources

- **Example Scripts**: See `examples/` directory
  - `workflow_config_based_selection.py`
  - `workflow_llm_based_selection.py`
  - `workflow_ab_testing.py`

- **API Documentation**: See docstrings in:
  - `cinema/workflow/classifier.py`
  - `cinema/workflow/orchestrator.py`
  - `cinema/workflow/models.py`

- **Design Document**: `.kiro/specs/veo-workflow-selection/design.md`

- **Requirements**: `.kiro/specs/veo-workflow-selection/requirements.md`

## Support

For issues or questions:
1. Check troubleshooting section above
2. Review example scripts
3. Enable debug logging
4. Check validation errors

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```
