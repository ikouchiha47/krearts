# Acceptance Criteria for Workflow Selection

## Overview

The acceptance criteria from the requirements document are used in **Task 2.4: LLM-based decision making** to intelligently choose between INTERPOLATION and INGREDIENTS workflows.

## Location in Code

**File**: `cinema/workflow/classifier.py`  
**Class**: `WorkflowClassifier`  
**Method**: `_llm_decide_workflow()`

## How It Works

When both interpolation and ingredients workflows are valid (scene has both keyframes AND character references), the system uses an LLM to decide which workflow will produce better results.

### Decision Flow

```
Scene has first_frame + last_frame + character_refs
                    ↓
         Conflict detected!
                    ↓
    ┌───────────────────────────┐
    │ Config Selection Mode?    │
    └───────────────────────────┘
                    ↓
    ┌───────────────────────────────────────┐
    │ LLM_INTELLIGENT mode                  │
    │ → Call _llm_decide_workflow()         │
    └───────────────────────────────────────┘
                    ↓
    ┌───────────────────────────────────────┐
    │ LLM analyzes scene against            │
    │ ACCEPTANCE CRITERIA                   │
    └───────────────────────────────────────┘
                    ↓
         DECISION: INTERPOLATION or INGREDIENTS
```

## Acceptance Criteria (from Requirements)

These criteria are embedded in the LLM prompt:

### Interpolation Quality Criteria (ALL must be true):

1. **Subject position stays relatively consistent** (not moving far)
2. **Framing changes are gradual** (NOT wide → extreme close-up)
3. **Clear spatial continuity** (same location)
4. **Camera movement explicitly described**
5. **Background not too complex/chaotic**

### LLM Prompt Template

```python
prompt = f"""You are a video generation workflow expert. Decide between:
1. FIRST_LAST_FRAME_INTERPOLATION - Interpolate between two keyframes
2. INGREDIENTS_TO_VIDEO - Generate video using character references

Scene: {scene.get('scene_id')}
Duration: {scene.get('duration')}s
Camera: {scene.get('cinematography', {}).get('camera_movement', {}).get('movement_type')}

First Frame: {scene.get('keyframe_description', {}).get('first_frame_prompt', '')[:200]}...
Last Frame: {scene.get('keyframe_description', {}).get('last_frame_prompt', '')[:200]}...

Interpolation Quality Criteria (ALL must be true):
1. Subject position stays relatively consistent (not moving far)
2. Framing changes are gradual (NOT wide → extreme close-up)
3. Clear spatial continuity (same location)
4. Camera movement explicitly described
5. Background not too complex/chaotic

Respond with:
DECISION: [INTERPOLATION or INGREDIENTS]
REASON: [one sentence]
"""
```

## Example: Your Screenplay Scene 1

**Scene**: S1_Tokyo_Crossing

**Input**:
- First Frame: "Wide shot of traveler starting to walk across Shibuya crossing"
- Last Frame: "Extreme close-up of foot mid-stride"
- Camera: "Tracking shot following traveler"
- Character: CHAR_001 available

**LLM Analysis**:
```
✅ Criterion 1: Subject position - ❌ FAIL (traveler moves across entire street)
✅ Criterion 2: Framing changes - ❌ FAIL (wide → extreme close-up)
✅ Criterion 3: Spatial continuity - ✅ PASS (same crossing)
✅ Criterion 4: Camera movement - ✅ PASS (tracking shot described)
✅ Criterion 5: Background complexity - ❌ FAIL (chaotic Shibuya crossing)

Result: 2/5 criteria met
```

**LLM Decision**:
```
DECISION: INGREDIENTS
REASON: Dramatic framing change (wide to extreme close-up) and subject movement across space make interpolation unreliable; ingredients workflow will produce better motion quality.
```

## Configuration Options

### Option 1: Always use LLM (Recommended)
```python
config = WorkflowConfig(
    selection_mode=WorkflowSelectionMode.LLM_INTELLIGENT,
    llm_model="gemini-2.0-flash-exp"
)
```

### Option 2: Use config default
```python
config = WorkflowConfig(
    selection_mode=WorkflowSelectionMode.CONFIG_DEFAULT,
    default_workflow=VeoWorkflowType.INGREDIENTS_TO_VIDEO
)
```

### Option 3: Force specific workflow
```python
config = WorkflowConfig(
    selection_mode=WorkflowSelectionMode.ALWAYS_INTERPOLATION
)
# or
config = WorkflowConfig(
    selection_mode=WorkflowSelectionMode.ALWAYS_INGREDIENTS
)
```

## Implementation Task

**Task 2.4**: Implement LLM-based decision making
- Build prompt with scene metadata and acceptance criteria
- Call LLM (Gemini 2.0 Flash)
- Parse response to extract decision and reason
- Log decision for transparency
- Fallback to default if LLM fails

## Benefits

1. **Intelligent**: Uses real-world quality criteria from testing
2. **Transparent**: Logs decision reason
3. **Flexible**: Can override with config
4. **Reliable**: Fallback to default if LLM fails
5. **Learning**: Can improve criteria based on results

## Related Requirements

- **Requirement 5.1-5.6**: Workflow Decision Logic
- **Requirement 8.1-8.4**: Workflow Documentation and Examples
- **Requirement 9.1-9.5**: Workflow Performance Tracking

## Testing

```python
def test_llm_decision_interpolation_fail():
    """Test LLM correctly rejects interpolation for dramatic framing change"""
    scene = {
        "scene_id": "S1",
        "keyframe_description": {
            "first_frame": "Wide shot of character",
            "last_frame": "Extreme close-up of foot"
        },
        "character_ids": ["CHAR_001"]
    }
    
    classifier = WorkflowClassifier(
        config=WorkflowConfig(selection_mode=WorkflowSelectionMode.LLM_INTELLIGENT)
    )
    
    classification = classifier.classify_scene(scene, assets)
    
    # Should choose INGREDIENTS due to dramatic framing change
    assert classification.workflow_type == VeoWorkflowType.INGREDIENTS_TO_VIDEO
    assert "framing" in classification.reason.lower()
```
