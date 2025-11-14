# Workflow Selection Examples

This directory contains example scripts demonstrating the Veo Workflow Selection system.

## Available Examples

### 1. Config-Based Selection (`workflow_config_based_selection.py`)

Demonstrates how to control workflow selection through configuration:

- **CONFIG_DEFAULT**: Use configured default when conflicts exist
- **ALWAYS_INTERPOLATION**: Force interpolation for all scenes
- **ALWAYS_INGREDIENTS**: Force ingredients for all scenes

**Run:**
```bash
python examples/workflow_config_based_selection.py
```

**Use cases:**
- Testing specific workflow types
- Consistent, predictable behavior
- Quick experimentation with different defaults

### 2. LLM-Based Selection (`workflow_llm_based_selection.py`)

Demonstrates intelligent workflow selection using LLM analysis:

- **LLM_INTELLIGENT**: Let LLM analyze scenes and decide
- Shows LLM decision logging and reasoning
- Compares LLM decisions with config-based approaches

**Run:**
```bash
python examples/workflow_llm_based_selection.py
```

**Use cases:**
- Production workflows with varied scenes
- Adaptive decision-making
- Understanding LLM reasoning

### 3. A/B Testing (`workflow_ab_testing.py`)

Demonstrates how to compare workflows side-by-side:

- Generate videos with both interpolation and ingredients
- Review and annotate test results
- Build knowledge base from reviewed tests

**Run:**
```bash
python examples/workflow_ab_testing.py
```

**Use cases:**
- Determining best workflow for scene types
- Quality comparison and evaluation
- Building training data for improvements

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

3. **Run an example:**
   ```bash
   python examples/workflow_config_based_selection.py
   ```

## Example Output

Each example provides detailed logging showing:

- Selected workflow type
- Decision reasoning
- Required assets
- Generation results
- Metrics and timing

Example output:
```
🎯 Classifying workflow for scene: S1_detective_office
  Has first+last frames: True
  Has character references: True
  ⚠️  Conflict: Both interpolation and ingredients are valid
🤖 Using LLM to decide workflow...
🤖 LLM decided: first_last_frame_interpolation
   Reason: Scene describes clear camera transformation with defined start and end states
✅ Video generated in 45.2s: output/S1_detective_office.mp4
```

## Scene Metadata Format

All examples use this scene metadata format:

```python
scene = {
    "scene_id": "S1_detective_office",
    "duration": 4.0,
    "description": "Detective behind desk, camera pushes in",
    "cinematography": {
        "camera_movement": {
            "movement_type": "dolly",
            "description": "Push in from medium to close-up"
        }
    },
    "keyframe_description": {
        "first_frame_prompt": "Medium shot of detective behind desk",
        "last_frame_prompt": "Close-up of detective's face"
    },
    "character_ids": ["detective_001"],
    "dialogue": "Of all the offices in this town..."
}
```

## Asset Paths Format

```python
assets = {
    "S1_detective_office_first_frame": "output/images/S1_first.png",
    "S1_detective_office_last_frame": "output/images/S1_last.png",
    "detective_001_reference": "output/refs/detective.png"
}
```

## Customization

Each example can be customized by:

1. **Modifying scene metadata**: Change camera movements, add dialogue, etc.
2. **Adjusting configuration**: Try different selection modes and defaults
3. **Adding new scenes**: Create your own test scenes

Example customization:

```python
# Create your own scene
my_scene = {
    "scene_id": "my_custom_scene",
    "duration": 5.0,
    "keyframe_description": {
        "first_frame_prompt": "Your first frame description",
        "last_frame_prompt": "Your last frame description"
    }
}

# Use custom config
my_config = WorkflowConfig(
    selection_mode=WorkflowSelectionMode.LLM_INTELLIGENT,
    default_workflow=VeoWorkflowType.INGREDIENTS_TO_VIDEO
)

# Generate
orchestrator = VeoWorkflowOrchestrator(gemini, my_config)
video_path, classification = await orchestrator.generate_video_with_workflow(
    my_scene, assets
)
```

## Documentation

For complete documentation, see:

- **Usage Guide**: `docs/workflow-selection-guide.md`
- **Design Document**: `.kiro/specs/veo-workflow-selection/design.md`
- **Requirements**: `.kiro/specs/veo-workflow-selection/requirements.md`

## Troubleshooting

### Common Issues

**Import errors:**
```bash
# Ensure you're in the project root
cd /path/to/project
python examples/workflow_config_based_selection.py
```

**Missing assets:**
```python
# Examples use placeholder paths
# Replace with your actual asset paths
assets = {
    "S1_first_frame": "path/to/your/first_frame.png",
    "S1_last_frame": "path/to/your/last_frame.png"
}
```

**API errors:**
```bash
# Check your .env file has valid API keys
cat .env | grep GOOGLE_API_KEY
```

### Debug Mode

Enable detailed logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Next Steps

1. **Run examples**: Try each example to understand different modes
2. **Review output**: Check generated videos and decision logs
3. **Customize**: Modify scenes and configs for your use case
4. **A/B test**: Compare workflows for your specific content
5. **Build knowledge**: Use A/B testing to improve decisions

## Support

For questions or issues:
1. Check the troubleshooting guide
2. Review the usage documentation
3. Enable debug logging
4. Check example output for errors
