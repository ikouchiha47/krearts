# Design Document: Veo Workflow Selection System

## Overview

This design document outlines the technical architecture for implementing intelligent workflow selection for Veo 3.1 video generation. The system will analyze scene metadata and automatically choose between First and Last Frame interpolation, Ingredients to Video composition, Timestamp Prompting, or standard text-to-video generation.

## Architecture

### High-Level Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    Input: Scene Metadata                         │
│  - Scene description                                             │
│  - Keyframe descriptions (first_frame, last_frame)              │
│  - Character references                                          │
│  - Action sequences with timing                                  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              Workflow Classification Engine                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ 1. Check for first + last frame keyframes               │  │
│  │ 2. Check for character reference images                 │  │
│  │ 3. Check for timestamp-based action sequences           │  │
│  │ 4. Apply decision rules                                  │  │
│  │ 5. Select optimal workflow                               │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              Workflow-Specific Parameter Builder                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Build API parameters based on workflow type:             │  │
│  │ - first_last_frame_interpolation                         │  │
│  │ - ingredients_to_video                                   │  │
│  │ - timestamp_prompting                                    │  │
│  │ - text_to_video                                          │  │
│  │ - image_to_video                                         │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              Validation & Compatibility Check                    │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ - Validate required assets exist                         │  │
│  │ - Check parameter compatibility                          │  │
│  │ - Verify duration constraints                            │  │
│  │ - Validate reference image count (max 3)                 │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              GeminiMediaGen.generate_video()                     │
│  Execute with workflow-specific parameters                       │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
                    ┌────────────────┐
                    │  Generated Video│
                    └────────────────┘
```

## Workflow Decision Logic

### How the LLM Decides Between Workflows

The system supports two classification modes:

#### 1. Rule-Based Classification (Fast, Deterministic)
Uses explicit metadata to make decisions:
- **Has first_frame AND last_frame?** → Interpolation
- **Has character_ids?** → Ingredients
- **Has multiple action_sequences with timestamps?** → Timestamp Prompting
- **Has only first_frame?** → Image-to-Video
- **None of above?** → Text-to-Video

#### 2. LLM-Based Classification (Intelligent, Context-Aware)
Uses Gemini to analyze scene description and make intelligent decisions:

**Key Decision Factors:**

1. **Transformation vs Composition**
   - **Interpolation**: Scene describes movement/transformation between two states
     - "Dolly shot pushing in from wide to close-up"
     - "Character walks from background to foreground"
   - **Ingredients**: Scene describes a composition with specific characters
     - "Detective behind desk talking to woman"
     - "Two characters having conversation"

2. **Character Consistency**
   - **Ingredients**: Dialogue scenes, multi-character interactions
   - **Interpolation**: Single character movement, no dialogue focus

3. **Motion Type**
   - **Interpolation**: Defined start and end points, smooth transition
   - **Timestamp**: Multiple distinct actions in sequence
   - **Text-to-Video**: General motion, no specific constraints

4. **Available Assets**
   - LLM checks what assets exist vs what's needed
   - Recommends workflow based on available resources

**Decision Matrix:**

| Scene Characteristic | Interpolation | Ingredients | Timestamp | Text-to-Video |
|---------------------|---------------|-------------|-----------|---------------|
| **Camera movement with start/end** | ✅ Best | ❌ | ❌ | ⚠️ Possible |
| **Dialogue scene** | ❌ | ✅ Best | ❌ | ⚠️ Possible |
| **Multiple characters** | ❌ | ✅ Best | ❌ | ⚠️ Possible |
| **Character consistency needed** | ❌ | ✅ Best | ⚠️ Possible | ❌ |
| **Transformation described** | ✅ Best | ❌ | ❌ | ⚠️ Possible |
| **Multiple sequential actions** | ❌ | ❌ | ✅ Best | ⚠️ Possible |
| **Duration > 8s** | ✅ | ✅ | ❌ | ✅ |
| **No specific constraints** | ❌ | ❌ | ❌ | ✅ Best |

**Example LLM Decision Process:**

```
Scene: "Close-up dolly shot of Alex's face, pushing in from medium to extreme close-up as he realizes the truth"

LLM Analysis:
- Describes transformation: medium → extreme close-up ✓
- Camera movement: dolly shot with clear start/end ✓
- No dialogue mentioned
- No multiple characters
- Duration: 2s (within limits)

Decision: FIRST_LAST_FRAME_INTERPOLATION
Reasoning: "Scene describes clear camera transformation with defined start and end states. Interpolation will create smooth dolly motion between two keyframes."
Required Assets: [first_frame, last_frame]
```

```
Scene: "Medium shot of detective behind desk. He looks up at woman and says 'Of all the offices in this town, you had to walk into mine.'"

LLM Analysis:
- Has dialogue ✓
- Multiple characters: detective, woman ✓
- Composition-focused (behind desk, looking up)
- No transformation described
- Character consistency important

Decision: INGREDIENTS_TO_VIDEO
Reasoning: "Dialogue scene with multiple characters requiring consistent appearance. Ingredients workflow ensures character references are used for visual consistency."
Required Assets: [detective_reference, woman_reference]
```

## Components

### 1. Workflow Classification Engine

**Purpose**: Analyze scene metadata and determine the optimal Veo workflow type.


**Key Classes**:

```python
from enum import Enum
from dataclasses import dataclass
from typing import Optional, List, Dict, Any

class VeoWorkflowType(Enum):
    """Enumeration of supported Veo workflow types"""
    TEXT_TO_VIDEO = "text_to_video"
    IMAGE_TO_VIDEO = "image_to_video"
    FIRST_LAST_FRAME_INTERPOLATION = "first_last_frame_interpolation"
    INGREDIENTS_TO_VIDEO = "ingredients_to_video"
    TIMESTAMP_PROMPTING = "timestamp_prompting"


@dataclass
class WorkflowClassification:
    """Result of workflow classification"""
    workflow_type: VeoWorkflowType
    reason: str
    required_assets: List[str]
    confidence: float  # 0.0 to 1.0
    warnings: List[str]


class WorkflowClassifier:
    """Classifies scenes into appropriate Veo workflow types"""
    
    def __init__(self, use_llm_classification: bool = True):
        """
        Initialize classifier.
        
        Args:
            use_llm_classification: If True, use LLM for intelligent workflow selection.
                                   If False, use rule-based heuristics only.
        """
        self.use_llm = use_llm_classification
        self.llm_client = None
        if use_llm_classification:
            from google import genai
            self.llm_client = genai.Client()
    
    def classify_scene(
        self,
        scene: Dict[str, Any],
        available_assets: Dict[str, str]
    ) -> WorkflowClassification:
        """
        Analyze scene metadata and determine optimal workflow.
        
        Two modes:
        1. Rule-based: Fast, deterministic, based on explicit metadata
        2. LLM-based: Intelligent, analyzes scene description and context
        
        Args:
            scene: Scene metadata including keyframes, references, actions
            available_assets: Dict of asset_id -> file_path for available assets
            
        Returns:
            WorkflowClassification with workflow type and reasoning
        """
        if self.use_llm:
            return self._classify_with_llm(scene, available_assets)
        else:
            return self._classify_with_rules(scene, available_assets)
    
    def _classify_with_rules(
        self,
        scene: Dict[str, Any],
        available_assets: Dict[str, str]
    ) -> WorkflowClassification:
        """
        Rule-based classification using explicit metadata.
        Fast and deterministic.
        """
        # Priority 1: Check for first + last frame interpolation
        if self._has_first_and_last_frames(scene):
            return self._classify_interpolation(scene, available_assets)
        
        # Priority 2: Check for ingredients to video (character references)
        if self._has_character_references(scene):
            return self._classify_ingredients(scene, available_assets)
        
        # Priority 3: Check for timestamp prompting
        if self._has_timestamp_actions(scene):
            return self._classify_timestamp(scene)
        
        # Priority 4: Check for image-to-video
        if self._has_single_keyframe(scene):
            return self._classify_image_to_video(scene, available_assets)
        
        # Default: text-to-video
        return self._classify_text_to_video(scene)
    
    def _classify_with_llm(
        self,
        scene: Dict[str, Any],
        available_assets: Dict[str, str]
    ) -> WorkflowClassification:
        """
        LLM-based classification using scene analysis.
        Intelligent but slower.
        """
        # Build analysis prompt for LLM
        analysis_prompt = self._build_llm_analysis_prompt(scene, available_assets)
        
        # Get LLM decision
        response = self.llm_client.models.generate_content(
            model="gemini-2.0-flash-exp",
            contents=analysis_prompt
        )
        
        # Parse LLM response
        return self._parse_llm_response(response, scene, available_assets)
    
    def _build_llm_analysis_prompt(
        self,
        scene: Dict[str, Any],
        available_assets: Dict[str, str]
    ) -> str:
        """
        Build prompt for LLM to analyze scene and recommend workflow.
        """
        prompt = f"""You are a video generation workflow expert. Analyze this scene and recommend the optimal Veo 3.1 workflow.

## Scene Information
Scene ID: {scene.get('scene_id')}
Duration: {scene.get('duration')}s
Description: {scene.get('description', '')}
Cinematography: {scene.get('cinematography', '')}
Action: {scene.get('action', '')}
Dialogue: {scene.get('dialogue', 'None')}

## Available Assets
"""
        
        # List available assets
        if available_assets:
            for asset_id, path in available_assets.items():
                prompt += f"- {asset_id}: {path}\n"
        else:
            prompt += "- No pre-generated assets available\n"
        
        prompt += """
## Workflow Options

### 1. FIRST_LAST_FRAME_INTERPOLATION
**When to use:**
- Scene describes a clear transformation or movement between two states
- You want smooth motion between a defined start and end point
- Camera movement (dolly, pan, zoom) with clear beginning and end
- Character/object moving from position A to position B

**Requirements:**
- Need both first_frame and last_frame keyframe images
- Images should have visual continuity (same lighting, character, environment)

**API Call:**
```python
generate_video(
    prompt="Describe the motion/transformation",
    image=first_frame_path,
    last_image=last_frame_path,
    duration=duration
)
```

**Example scenes:**
- "Dolly shot pushing in from wide shot to close-up of character's face"
- "Pan from left to right across a cityscape"
- "Character walks from background to foreground"

### 2. INGREDIENTS_TO_VIDEO
**When to use:**
- Scene has dialogue with characters
- Need consistent character appearance across multiple scenes
- Composing a scene with specific characters and settings
- Multi-character interactions

**Requirements:**
- Character reference images (max 3)
- Prompt should reference "Using the provided images for [character names]..."

**API Call:**
```python
generate_video(
    prompt="Using the provided images for detective and woman, create...",
    reference_images=[detective_ref, woman_ref, setting_ref],
    duration=duration
)
```

**Example scenes:**
- "Detective behind desk talking to woman visitor"
- "Two characters having a conversation in a cafe"
- "Character interacting with a specific product/object"

### 3. TIMESTAMP_PROMPTING
**When to use:**
- Single continuous shot with multiple sequential actions
- Complex choreography within one take
- Multiple actions that need precise timing

**Requirements:**
- Total duration ≤ 8 seconds
- Actions must be sequential, not simultaneous

**API Call:**
```python
generate_video(
    prompt="[00:00:00-00:00:02] action 1. [00:00:02-00:00:04] action 2.",
    duration=duration
)
```

**Example scenes:**
- "Character picks up phone [0-2s], answers it [2-4s], reacts with surprise [4-6s]"
- "Camera starts wide [0-2s], pushes in [2-5s], ends on close-up [5-8s]"

### 4. TEXT_TO_VIDEO
**When to use:**
- Simple scene without specific visual constraints
- No character consistency requirements
- No complex transformations

**API Call:**
```python
generate_video(
    prompt="Full scene description",
    duration=duration
)
```

### 5. IMAGE_TO_VIDEO
**When to use:**
- Starting from a specific visual composition
- Animating a still image
- Only first frame is defined, natural motion from there

**API Call:**
```python
generate_video(
    prompt="Describe motion from this starting point",
    image=first_frame_path,
    duration=duration
)
```

## Your Task

Analyze the scene and respond with ONLY a JSON object (no markdown, no explanation):

{{
  "workflow": "FIRST_LAST_FRAME_INTERPOLATION" | "INGREDIENTS_TO_VIDEO" | "TIMESTAMP_PROMPTING" | "TEXT_TO_VIDEO" | "IMAGE_TO_VIDEO",
  "confidence": 0.0-1.0,
  "reasoning": "Brief explanation of why this workflow is optimal",
  "required_assets": ["list", "of", "asset_ids", "needed"],
  "warnings": ["any potential issues or considerations"]
}}

Consider:
1. What assets are available vs what's needed?
2. Does the scene describe a transformation (interpolation) or a composition (ingredients)?
3. Are there characters that need consistency?
4. Is there dialogue?
5. Are there multiple sequential actions?
6. What's the duration constraint?

Respond with JSON only:"""
        
        return prompt
    
    def _parse_llm_response(
        self,
        response,
        scene: Dict[str, Any],
        available_assets: Dict[str, str]
    ) -> WorkflowClassification:
        """Parse LLM response and create WorkflowClassification"""
        import json
        
        # Extract JSON from response
        response_text = response.text.strip()
        
        # Remove markdown code blocks if present
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
        
        # Parse JSON
        try:
            decision = json.loads(response_text)
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse LLM response, falling back to rules: {e}")
            return self._classify_with_rules(scene, available_assets)
        
        # Convert to WorkflowClassification
        workflow_type = VeoWorkflowType(decision["workflow"])
        
        return WorkflowClassification(
            workflow_type=workflow_type,
            reason=decision["reasoning"],
            required_assets=decision.get("required_assets", []),
            confidence=decision.get("confidence", 0.8),
            warnings=decision.get("warnings", [])
        )
    
    def _has_first_and_last_frames(self, scene: Dict[str, Any]) -> bool:
        """Check if scene has both first and last frame keyframe descriptions"""
        keyframes = scene.get("keyframes", {})
        return "first_frame" in keyframes and "last_frame" in keyframes
    
    def _has_character_references(self, scene: Dict[str, Any]) -> bool:
        """Check if scene references characters with available reference images"""
        return bool(scene.get("character_ids", []))
    
    def _has_timestamp_actions(self, scene: Dict[str, Any]) -> bool:
        """Check if scene has multiple timed action sequences"""
        actions = scene.get("action_sequences", [])
        return len(actions) > 1 and all("timestamp" in a for a in actions)
    
    def _has_single_keyframe(self, scene: Dict[str, Any]) -> bool:
        """Check if scene has a single keyframe for image-to-video"""
        keyframes = scene.get("keyframes", {})
        return "first_frame" in keyframes and "last_frame" not in keyframes
    
    def _classify_interpolation(
        self,
        scene: Dict[str, Any],
        available_assets: Dict[str, str]
    ) -> WorkflowClassification:
        """Classify as interpolation workflow"""
        first_frame_id = f"{scene['scene_id']}_first_frame"
        last_frame_id = f"{scene['scene_id']}_last_frame"
        
        warnings = []
        if first_frame_id not in available_assets:
            warnings.append(f"First frame asset not found: {first_frame_id}")
        if last_frame_id not in available_assets:
            warnings.append(f"Last frame asset not found: {last_frame_id}")
        
        return WorkflowClassification(
            workflow_type=VeoWorkflowType.FIRST_LAST_FRAME_INTERPOLATION,
            reason="Scene has both first and last frame keyframes defined",
            required_assets=[first_frame_id, last_frame_id],
            confidence=1.0,
            warnings=warnings
        )
    
    def _classify_ingredients(
        self,
        scene: Dict[str, Any],
        available_assets: Dict[str, str]
    ) -> WorkflowClassification:
        """Classify as ingredients workflow"""
        character_ids = scene.get("character_ids", [])
        required_assets = [f"{cid}_reference" for cid in character_ids]
        
        warnings = []
        if len(character_ids) > 3:
            warnings.append(f"Scene has {len(character_ids)} characters, but max is 3 reference images")
        
        for asset_id in required_assets[:3]:
            if asset_id not in available_assets:
                warnings.append(f"Character reference not found: {asset_id}")
        
        return WorkflowClassification(
            workflow_type=VeoWorkflowType.INGREDIENTS_TO_VIDEO,
            reason="Scene has character references for consistency",
            required_assets=required_assets[:3],
            confidence=0.9,
            warnings=warnings
        )
    
    def _classify_timestamp(self, scene: Dict[str, Any]) -> WorkflowClassification:
        """Classify as timestamp prompting workflow"""
        action_sequences = scene.get("action_sequences", [])
        
        warnings = []
        if scene.get("duration", 0) > 8:
            warnings.append(f"Duration {scene['duration']}s exceeds 8s limit for timestamp prompting")
        
        return WorkflowClassification(
            workflow_type=VeoWorkflowType.TIMESTAMP_PROMPTING,
            reason=f"Scene has {len(action_sequences)} sequential actions with timing",
            required_assets=[],
            confidence=0.85,
            warnings=warnings
        )
    
    def _classify_image_to_video(
        self,
        scene: Dict[str, Any],
        available_assets: Dict[str, str]
    ) -> WorkflowClassification:
        """Classify as image-to-video workflow"""
        first_frame_id = f"{scene['scene_id']}_first_frame"
        
        warnings = []
        if first_frame_id not in available_assets:
            warnings.append(f"First frame asset not found: {first_frame_id}")
        
        return WorkflowClassification(
            workflow_type=VeoWorkflowType.IMAGE_TO_VIDEO,
            reason="Scene has first frame keyframe for image-to-video",
            required_assets=[first_frame_id],
            confidence=0.8,
            warnings=warnings
        )
    
    def _classify_text_to_video(self, scene: Dict[str, Any]) -> WorkflowClassification:
        """Classify as text-to-video workflow"""
        return WorkflowClassification(
            workflow_type=VeoWorkflowType.TEXT_TO_VIDEO,
            reason="No specific assets or constraints, using text-to-video",
            required_assets=[],
            confidence=0.7,
            warnings=[]
        )
```

### 2. Workflow Parameter Builder

**Purpose**: Build API parameters specific to each workflow type.

```python
class WorkflowParameterBuilder:
    """Builds GeminiMediaGen API parameters for each workflow type"""
    
    def build_parameters(
        self,
        workflow_type: VeoWorkflowType,
        scene: Dict[str, Any],
        assets: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Build API parameters based on workflow type.
        
        Args:
            workflow_type: The selected workflow type
            scene: Scene metadata
            assets: Available asset paths
            
        Returns:
            Dict of parameters for GeminiMediaGen.generate_video()
        """
        if workflow_type == VeoWorkflowType.FIRST_LAST_FRAME_INTERPOLATION:
            return self._build_interpolation_params(scene, assets)
        
        elif workflow_type == VeoWorkflowType.INGREDIENTS_TO_VIDEO:
            return self._build_ingredients_params(scene, assets)
        
        elif workflow_type == VeoWorkflowType.TIMESTAMP_PROMPTING:
            return self._build_timestamp_params(scene)
        
        elif workflow_type == VeoWorkflowType.IMAGE_TO_VIDEO:
            return self._build_image_to_video_params(scene, assets)
        
        else:  # TEXT_TO_VIDEO
            return self._build_text_to_video_params(scene)
    
    def _build_interpolation_params(
        self,
        scene: Dict[str, Any],
        assets: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Build parameters for first and last frame interpolation.
        
        API Call:
            generate_video(
                prompt=prompt,
                image=first_frame_path,
                last_image=last_frame_path,
                duration=duration
            )
        """
        first_frame_id = f"{scene['scene_id']}_first_frame"
        last_frame_id = f"{scene['scene_id']}_last_frame"
        
        return {
            "prompt": self._build_interpolation_prompt(scene),
            "image": assets[first_frame_id],
            "last_image": assets[last_frame_id],
            "duration": scene.get("duration", 4.0)
        }
    
    def _build_ingredients_params(
        self,
        scene: Dict[str, Any],
        assets: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Build parameters for ingredients to video.
        
        API Call:
            generate_video(
                prompt=prompt,
                reference_images=[ref1, ref2, ref3],
                duration=duration
            )
        """
        # Get character reference images (max 3)
        character_ids = scene.get("character_ids", [])[:3]
        reference_images = [
            assets[f"{char_id}_reference"]
            for char_id in character_ids
            if f"{char_id}_reference" in assets
        ]
        
        return {
            "prompt": self._build_ingredients_prompt(scene, character_ids),
            "reference_images": reference_images,
            "duration": scene.get("duration", 4.0)
        }
    
    def _build_timestamp_params(self, scene: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build parameters for timestamp prompting.
        
        API Call:
            generate_video(
                prompt=timestamp_formatted_prompt,
                duration=duration
            )
        """
        return {
            "prompt": self._build_timestamp_prompt(scene),
            "duration": scene.get("duration", 4.0)
        }
    
    def _build_interpolation_prompt(self, scene: Dict[str, Any]) -> str:
        """
        Build prompt for interpolation workflow.
        Format: Describe the motion/transformation between frames.
        """
        cinematography = scene.get("cinematography", "")
        action = scene.get("action", "")
        audio = scene.get("audio", "")
        
        prompt = f"{cinematography}. {action}."
        if audio:
            prompt += f" {audio}."
        
        return prompt
    
    def _build_ingredients_prompt(
        self,
        scene: Dict[str, Any],
        character_ids: List[str]
    ) -> str:
        """
        Build prompt for ingredients workflow.
        Format: Reference the provided images explicitly.
        """
        char_names = [scene.get("characters", {}).get(cid, {}).get("name", cid) 
                      for cid in character_ids]
        
        prompt = f"Using the provided images for {', '.join(char_names)}, "
        prompt += scene.get("description", "")
        
        if scene.get("dialogue"):
            prompt += f' {scene["dialogue"]}'
        
        return prompt
    
    def _build_timestamp_prompt(self, scene: Dict[str, Any]) -> str:
        """
        Build prompt with timestamp notation.
        Format: [00:00:00-00:00:02] action 1. [00:00:02-00:00:04] action 2.
        """
        action_sequences = scene.get("action_sequences", [])
        
        prompt_parts = []
        for action in action_sequences:
            start = action["start_time"]
            end = action["end_time"]
            description = action["description"]
            prompt_parts.append(f"[{start}-{end}] {description}")
        
        return ". ".join(prompt_parts) + "."
```

### 3. Workflow Validator

**Purpose**: Validate workflow compatibility and parameter constraints.

```python
class WorkflowValidator:
    """Validates workflow parameters before API calls"""
    
    def validate(
        self,
        workflow_type: VeoWorkflowType,
        parameters: Dict[str, Any],
        assets: Dict[str, str]
    ) -> tuple[bool, List[str]]:
        """
        Validate workflow parameters.
        
        Returns:
            (is_valid, error_messages)
        """
        errors = []
        
        if workflow_type == VeoWorkflowType.FIRST_LAST_FRAME_INTERPOLATION:
            errors.extend(self._validate_interpolation(parameters, assets))
        
        elif workflow_type == VeoWorkflowType.INGREDIENTS_TO_VIDEO:
            errors.extend(self._validate_ingredients(parameters, assets))
        
        elif workflow_type == VeoWorkflowType.TIMESTAMP_PROMPTING:
            errors.extend(self._validate_timestamp(parameters))
        
        # Common validations
        errors.extend(self._validate_duration(parameters))
        errors.extend(self._validate_incompatible_params(parameters))
        
        return (len(errors) == 0, errors)
    
    def _validate_interpolation(
        self,
        params: Dict[str, Any],
        assets: Dict[str, str]
    ) -> List[str]:
        """Validate first and last frame interpolation parameters"""
        errors = []
        
        # Check required parameters
        if "image" not in params:
            errors.append("Missing 'image' parameter for interpolation")
        if "last_image" not in params:
            errors.append("Missing 'last_image' parameter for interpolation")
        
        # Check files exist
        if "image" in params and not self._file_exists(params["image"]):
            errors.append(f"First frame image not found: {params['image']}")
        if "last_image" in params and not self._file_exists(params["last_image"]):
            errors.append(f"Last frame image not found: {params['last_image']}")
        
        # Check incompatibility with reference_images
        if "reference_images" in params:
            errors.append(
                "Cannot use 'reference_images' with 'last_image' in interpolation workflow"
            )
        
        return errors
    
    def _validate_ingredients(
        self,
        params: Dict[str, Any],
        assets: Dict[str, str]
    ) -> List[str]:
        """Validate ingredients to video parameters"""
        errors = []
        
        # Check reference_images parameter
        if "reference_images" not in params:
            errors.append("Missing 'reference_images' parameter for ingredients workflow")
        else:
            ref_images = params["reference_images"]
            
            # Check count (max 3)
            if len(ref_images) > 3:
                errors.append(
                    f"Too many reference images: {len(ref_images)}. Maximum is 3."
                )
            
            # Check files exist
            for ref_img in ref_images:
                if not self._file_exists(ref_img):
                    errors.append(f"Reference image not found: {ref_img}")
        
        # Check incompatibility with last_image
        if "last_image" in params:
            errors.append(
                "Cannot use 'last_image' with 'reference_images' in ingredients workflow"
            )
        
        return errors
    
    def _validate_timestamp(self, params: Dict[str, Any]) -> List[str]:
        """Validate timestamp prompting parameters"""
        errors = []
        
        # Check duration constraint (max 8 seconds)
        duration = params.get("duration", 0)
        if duration > 8:
            errors.append(
                f"Timestamp prompting duration {duration}s exceeds maximum of 8s"
            )
        
        # Validate timestamp format in prompt
        prompt = params.get("prompt", "")
        if not self._has_valid_timestamps(prompt):
            errors.append("Prompt does not contain valid timestamp notation [HH:MM:SS-HH:MM:SS]")
        
        return errors
    
    def _validate_duration(self, params: Dict[str, Any]) -> List[str]:
        """Validate duration constraints"""
        errors = []
        duration = params.get("duration", 0)
        
        if duration < 4:
            errors.append(f"Duration {duration}s is below minimum of 4s")
        if duration > 8:
            errors.append(f"Duration {duration}s exceeds maximum of 8s")
        
        return errors
    
    def _validate_incompatible_params(self, params: Dict[str, Any]) -> List[str]:
        """Check for incompatible parameter combinations"""
        errors = []
        
        # last_image and reference_images are mutually exclusive
        if "last_image" in params and "reference_images" in params:
            errors.append(
                "Parameters 'last_image' and 'reference_images' are mutually exclusive"
            )
        
        return errors
    
    @staticmethod
    def _file_exists(path: str) -> bool:
        """Check if file exists"""
        from pathlib import Path
        return Path(path).exists()
    
    @staticmethod
    def _has_valid_timestamps(prompt: str) -> bool:
        """Check if prompt contains valid timestamp notation"""
        import re
        pattern = r'\[\d{2}:\d{2}:\d{2}-\d{2}:\d{2}:\d{2}\]'
        return bool(re.search(pattern, prompt))
```

### 4. Workflow Orchestrator

**Purpose**: Coordinate workflow selection, validation, and execution.

```python
class VeoWorkflowOrchestrator:
    """Orchestrates the complete workflow selection and execution process"""
    
    def __init__(self, gemini_client: GeminiMediaGen):
        self.gemini = gemini_client
        self.classifier = WorkflowClassifier()
        self.param_builder = WorkflowParameterBuilder()
        self.validator = WorkflowValidator()
        self.metrics = WorkflowMetrics()
    
    async def generate_video_with_workflow(
        self,
        scene: Dict[str, Any],
        assets: Dict[str, str]
    ) -> tuple[str, WorkflowClassification]:
        """
        Complete workflow: classify, validate, and generate video.
        
        Args:
            scene: Scene metadata
            assets: Available asset paths
            
        Returns:
            (video_path, workflow_classification)
        """
        # Step 1: Classify workflow
        classification = self.classifier.classify_scene(scene, assets)
        logger.info(f"🎯 Selected workflow: {classification.workflow_type.value}")
        logger.info(f"   Reason: {classification.reason}")
        
        # Step 2: Build parameters
        params = self.param_builder.build_parameters(
            classification.workflow_type,
            scene,
            assets
        )
        logger.debug(f"📋 Parameters: {params.keys()}")
        
        # Step 3: Validate
        is_valid, errors = self.validator.validate(
            classification.workflow_type,
            params,
            assets
        )
        
        if not is_valid:
            error_msg = "\n".join(errors)
            logger.error(f"❌ Validation failed:\n{error_msg}")
            raise ValueError(f"Workflow validation failed: {error_msg}")
        
        # Step 4: Execute generation
        logger.info(f"🎬 Generating video with {classification.workflow_type.value}")
        start_time = time.time()
        
        try:
            response = await self.gemini.generate_video(**params)
            video_path = await self.gemini.render_video(
                f"output/{scene['scene_id']}.mp4",
                response
            )
            
            generation_time = time.time() - start_time
            
            # Track metrics
            self.metrics.record_success(
                classification.workflow_type,
                scene['scene_id'],
                generation_time
            )
            
            logger.info(f"✅ Video generated in {generation_time:.1f}s")
            return video_path, classification
            
        except Exception as e:
            generation_time = time.time() - start_time
            
            # Track failure
            self.metrics.record_failure(
                classification.workflow_type,
                scene['scene_id'],
                str(e)
            )
            
            logger.error(f"❌ Generation failed after {generation_time:.1f}s: {e}")
            raise
```

### 5. Workflow Metrics Tracker

**Purpose**: Track workflow usage and performance.

```python
@dataclass
class WorkflowMetric:
    """Single workflow execution metric"""
    workflow_type: VeoWorkflowType
    scene_id: str
    success: bool
    generation_time: float
    error_message: Optional[str] = None
    timestamp: float = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()


class WorkflowMetrics:
    """Tracks workflow performance metrics"""
    
    def __init__(self):
        self.metrics: List[WorkflowMetric] = []
    
    def record_success(
        self,
        workflow_type: VeoWorkflowType,
        scene_id: str,
        generation_time: float
    ):
        """Record successful generation"""
        metric = WorkflowMetric(
            workflow_type=workflow_type,
            scene_id=scene_id,
            success=True,
            generation_time=generation_time
        )
        self.metrics.append(metric)
    
    def record_failure(
        self,
        workflow_type: VeoWorkflowType,
        scene_id: str,
        error_message: str
    ):
        """Record failed generation"""
        metric = WorkflowMetric(
            workflow_type=workflow_type,
            scene_id=scene_id,
            success=False,
            generation_time=0.0,
            error_message=error_message
        )
        self.metrics.append(metric)
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary statistics"""
        if not self.metrics:
            return {}
        
        summary = {}
        for workflow_type in VeoWorkflowType:
            workflow_metrics = [m for m in self.metrics if m.workflow_type == workflow_type]
            
            if not workflow_metrics:
                continue
            
            successes = [m for m in workflow_metrics if m.success]
            failures = [m for m in workflow_metrics if not m.success]
            
            summary[workflow_type.value] = {
                "total": len(workflow_metrics),
                "successes": len(successes),
                "failures": len(failures),
                "success_rate": len(successes) / len(workflow_metrics) if workflow_metrics else 0,
                "avg_generation_time": sum(m.generation_time for m in successes) / len(successes) if successes else 0
            }
        
        return summary
    
    def export_to_json(self, output_path: str):
        """Export metrics to JSON file"""
        import json
        
        data = {
            "metrics": [
                {
                    "workflow_type": m.workflow_type.value,
                    "scene_id": m.scene_id,
                    "success": m.success,
                    "generation_time": m.generation_time,
                    "error_message": m.error_message,
                    "timestamp": m.timestamp
                }
                for m in self.metrics
            ],
            "summary": self.get_summary()
        }
        
        with open(output_path, "w") as f:
            json.dump(data, f, indent=2)
```

## Data Models

### Scene Metadata Structure

```python
@dataclass
class SceneMetadata:
    """Complete scene metadata for workflow selection"""
    scene_id: str
    duration: float
    description: str
    cinematography: str
    action: str
    audio: Optional[str] = None
    dialogue: Optional[str] = None
    
    # Keyframe descriptions
    keyframes: Dict[str, str] = None  # {"first_frame": "...", "last_frame": "..."}
    
    # Character references
    character_ids: List[str] = None
    characters: Dict[str, Dict[str, Any]] = None
    
    # Timestamp-based actions
    action_sequences: List[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.keyframes is None:
            self.keyframes = {}
        if self.character_ids is None:
            self.character_ids = []
        if self.characters is None:
            self.characters = {}
        if self.action_sequences is None:
            self.action_sequences = []
```

## Integration with Existing Code

### Modifications to GeminiMediaGen

The existing `GeminiMediaGen.generate_video()` method already supports all required parameters:

```python
# Current signature (no changes needed)
async def generate_video(
    self,
    prompt: str,
    image: Optional[ImageInput] = None,
    last_image: Optional[ImageInput] = None,
    reference_images: Optional[list[ImageInput]] = None,
    duration: Optional[float] = None,
):
```

### Usage Example

```python
# Initialize orchestrator
gemini = GeminiMediaGen()
orchestrator = VeoWorkflowOrchestrator(gemini)

# Scene with first and last frames (interpolation)
scene_interpolation = {
    "scene_id": "S1_Tokyo_Crossing",
    "duration": 4.0,
    "description": "Walking on rainy Tokyo crosswalk",
    "cinematography": "Low-angle shot",
    "action": "Feet walking forward",
    "keyframes": {
        "first_frame": "Feet at start of crosswalk",
        "last_frame": "Feet at end of crosswalk"
    }
}

assets = {
    "S1_Tokyo_Crossing_first_frame": "output/images/S1_first.png",
    "S1_Tokyo_Crossing_last_frame": "output/images/S1_last.png"
}

# Generate with automatic workflow selection
video_path, classification = await orchestrator.generate_video_with_workflow(
    scene_interpolation,
    assets
)
# Output: Uses FIRST_LAST_FRAME_INTERPOLATION workflow

# Scene with character references (ingredients)
scene_dialogue = {
    "scene_id": "S2_Detective_Office",
    "duration": 6.0,
    "description": "Detective behind desk talking to woman",
    "cinematography": "Medium shot",
    "dialogue": '"Of all the offices in this town, you had to walk into mine."',
    "character_ids": ["CHAR_001_detective", "CHAR_002_woman"]
}

assets = {
    "CHAR_001_detective_reference": "output/refs/detective.png",
    "CHAR_002_woman_reference": "output/refs/woman.png"
}

video_path, classification = await orchestrator.generate_video_with_workflow(
    scene_dialogue,
    assets
)
# Output: Uses INGREDIENTS_TO_VIDEO workflow
```

## Error Handling

```python
class WorkflowValidationError(Exception):
    """Raised when workflow validation fails"""
    pass

class IncompatibleParametersError(WorkflowValidationError):
    """Raised when incompatible parameters are detected"""
    pass

class MissingAssetError(WorkflowValidationError):
    """Raised when required assets are missing"""
    pass

# Usage in orchestrator
try:
    video_path, classification = await orchestrator.generate_video_with_workflow(
        scene, assets
    )
except WorkflowValidationError as e:
    logger.error(f"Validation error: {e}")
    # Handle validation failure
except Exception as e:
    logger.error(f"Generation error: {e}")
    # Handle generation failure
```

## Testing Strategy

### Unit Tests

```python
def test_workflow_classification_interpolation():
    """Test classification of interpolation workflow"""
    classifier = WorkflowClassifier()
    
    scene = {
        "scene_id": "S1",
        "keyframes": {
            "first_frame": "Start frame",
            "last_frame": "End frame"
        }
    }
    
    classification = classifier.classify_scene(scene, {})
    assert classification.workflow_type == VeoWorkflowType.FIRST_LAST_FRAME_INTERPOLATION


def test_workflow_classification_ingredients():
    """Test classification of ingredients workflow"""
    classifier = WorkflowClassifier()
    
    scene = {
        "scene_id": "S2",
        "character_ids": ["CHAR_001", "CHAR_002"],
        "keyframes": {}
    }
    
    classification = classifier.classify_scene(scene, {})
    assert classification.workflow_type == VeoWorkflowType.INGREDIENTS_TO_VIDEO


def test_validation_incompatible_params():
    """Test validation catches incompatible parameters"""
    validator = WorkflowValidator()
    
    params = {
        "prompt": "Test",
        "last_image": "frame.png",
        "reference_images": ["ref1.png"],
        "duration": 4.0
    }
    
    is_valid, errors = validator.validate(
        VeoWorkflowType.FIRST_LAST_FRAME_INTERPOLATION,
        params,
        {}
    )
    
    assert not is_valid
    assert any("mutually exclusive" in e for e in errors)
```

### Integration Tests

```python
async def test_full_workflow_interpolation():
    """Test complete workflow with interpolation"""
    gemini = GeminiMediaGen()
    orchestrator = VeoWorkflowOrchestrator(gemini)
    
    scene = create_test_scene_interpolation()
    assets = create_test_assets()
    
    video_path, classification = await orchestrator.generate_video_with_workflow(
        scene, assets
    )
    
    assert os.path.exists(video_path)
    assert classification.workflow_type == VeoWorkflowType.FIRST_LAST_FRAME_INTERPOLATION
```

## Performance Considerations

### Workflow Selection Performance

- Classification is O(1) - simple rule-based checks
- No expensive operations during classification
- Validation is O(n) where n is number of assets to check

### Caching Opportunities

```python
class WorkflowClassifier:
    def __init__(self):
        self._classification_cache = {}
    
    def classify_scene(self, scene, assets):
        # Cache based on scene_id and asset fingerprint
        cache_key = self._get_cache_key(scene, assets)
        
        if cache_key in self._classification_cache:
            return self._classification_cache[cache_key]
        
        classification = self._do_classification(scene, assets)
        self._classification_cache[cache_key] = classification
        return classification
```

## Configuration

```python
from enum import Enum

class WorkflowSelectionMode(Enum):
    """How to select workflow when multiple options are valid"""
    CONFIG_DEFAULT = "config_default"  # Use configured default
    LLM_INTELLIGENT = "llm_intelligent"  # Use LLM to decide
    ALWAYS_INTERPOLATION = "always_interpolation"  # Force interpolation
    ALWAYS_INGREDIENTS = "always_ingredients"  # Force ingredients
    AB_TEST = "ab_test"  # Generate with both workflows


@dataclass
class WorkflowConfig:
    """Configuration for workflow selection"""
    
    # Workflow selection mode
    selection_mode: WorkflowSelectionMode = WorkflowSelectionMode.LLM_INTELLIGENT
    
    # Default workflow when both interpolation and ingredients are valid
    default_workflow: VeoWorkflowType = VeoWorkflowType.INGREDIENTS_TO_VIDEO
    
    # Enable/disable specific workflows
    enable_interpolation: bool = True
    enable_ingredients: bool = True
    enable_timestamp: bool = True
    
    # LLM-based decision settings
    use_llm_for_workflow_decision: bool = True
    llm_model: str = "gemini-2.0-flash-exp"
    
    # A/B testing settings
    ab_test_enabled: bool = False
    ab_test_output_dir: str = "output/ab_test"
    
    # Interpolation quality thresholds
    interpolation_quality_threshold: float = 0.6  # 0.0 to 1.0
    
    # Validation settings
    strict_validation: bool = True
    allow_missing_assets: bool = False
    
    # Performance settings
    enable_classification_cache: bool = True
    max_reference_images: int = 3
    
    # Logging
    log_workflow_decisions: bool = True
    export_metrics: bool = True
    metrics_output_path: str = "output/workflow_metrics.json"
```

## Next Steps

1. Implement WorkflowClassifier class
2. Implement WorkflowParameterBuilder class
3. Implement WorkflowValidator class
4. Implement VeoWorkflowOrchestrator class
5. Implement WorkflowMetrics tracking
6. Add unit tests for each component
7. Add integration tests with real API calls
8. Document usage examples and best practices


## Enhanced Workflow Classification with Config and LLM

### Updated WorkflowClassifier with Conflict Resolution

```python
class WorkflowClassifier:
    """Classifies scenes with config-based and LLM-based decision support"""
    
    def __init__(self, config: WorkflowConfig, gemini_client: Optional[genai.Client] = None):
        self.config = config
        self.gemini_client = gemini_client or genai.Client()
    
    def classify_scene(
        self,
        scene: Dict[str, Any],
        available_assets: Dict[str, str]
    ) -> WorkflowClassification:
        """
        Analyze scene and determine optimal workflow using config or LLM.
        """
        # Check selection mode
        if self.config.selection_mode == WorkflowSelectionMode.ALWAYS_INTERPOLATION:
            return self._force_interpolation(scene, available_assets)
        
        if self.config.selection_mode == WorkflowSelectionMode.ALWAYS_INGREDIENTS:
            return self._force_ingredients(scene, available_assets)
        
        # Check for workflow conflicts
        has_interpolation = self._has_first_and_last_frames(scene)
        has_ingredients = self._has_character_references(scene)
        
        if has_interpolation and has_ingredients:
            # Conflict: use config or LLM to decide
            return self._resolve_workflow_conflict(scene, available_assets)
        
        # Single workflow is valid
        if has_interpolation:
            return self._classify_interpolation(scene, available_assets)
        if has_ingredients:
            return self._classify_ingredients(scene, available_assets)
        
        # Fallback workflows
        if self._has_timestamp_actions(scene):
            return self._classify_timestamp(scene)
        if self._has_single_keyframe(scene):
            return self._classify_image_to_video(scene, available_assets)
        
        return self._classify_text_to_video(scene)
    
    def _resolve_workflow_conflict(
        self,
        scene: Dict[str, Any],
        available_assets: Dict[str, str]
    ) -> WorkflowClassification:
        """Resolve conflict when both interpolation and ingredients are valid"""
        
        if self.config.selection_mode == WorkflowSelectionMode.CONFIG_DEFAULT:
            # Use configured default
            logger.info(f"⚙️ Using config default: {self.config.default_workflow.value}")
            if self.config.default_workflow == VeoWorkflowType.FIRST_LAST_FRAME_INTERPOLATION:
                return self._classify_interpolation(scene, available_assets)
            else:
                return self._classify_ingredients(scene, available_assets)
        
        elif self.config.selection_mode == WorkflowSelectionMode.LLM_INTELLIGENT:
            # Use LLM to decide based on acceptance criteria
            logger.info("🤖 Using LLM to decide workflow...")
            return self._llm_decide_workflow(scene, available_assets)
        
        else:
            # Default to ingredients (more reliable)
            return self._classify_ingredients(scene, available_assets)
    
    def _llm_decide_workflow(
        self,
        scene: Dict[str, Any],
        available_assets: Dict[str, str]
    ) -> WorkflowClassification:
        """Use LLM to decide between interpolation and ingredients"""
        
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
        
        try:
            response = self.gemini_client.models.generate_content(
                model=self.config.llm_model,
                contents=prompt
            )
            
            response_text = response.text.strip()
            
            # Parse decision
            if "INTERPOLATION" in response_text.split("\n")[0]:
                workflow_type = VeoWorkflowType.FIRST_LAST_FRAME_INTERPOLATION
            else:
                workflow_type = VeoWorkflowType.INGREDIENTS_TO_VIDEO
            
            # Extract reason
            reason_lines = [l for l in response_text.split("\n") if "REASON:" in l]
            reason = reason_lines[0].replace("REASON:", "").strip() if reason_lines else "LLM decision"
            
            logger.info(f"🤖 LLM decided: {workflow_type.value} - {reason}")
            
            if workflow_type == VeoWorkflowType.FIRST_LAST_FRAME_INTERPOLATION:
                return self._classify_interpolation(scene, available_assets)
            else:
                return self._classify_ingredients(scene, available_assets)
        
        except Exception as e:
            logger.warning(f"LLM decision failed: {e}. Using default.")
            if self.config.default_workflow == VeoWorkflowType.FIRST_LAST_FRAME_INTERPOLATION:
                return self._classify_interpolation(scene, available_assets)
            else:
                return self._classify_ingredients(scene, available_assets)
```

### A/B Testing Support

```python
class ABTestOrchestrator:
    """Generates videos with multiple workflows for comparison"""
    
    def __init__(self, gemini_client: GeminiMediaGen, config: WorkflowConfig):
        self.gemini = gemini_client
        self.config = config
    
    async def generate_ab_test(
        self,
        scene: Dict[str, Any],
        assets: Dict[str, str]
    ) -> Dict[str, str]:
        """
        Generate video with both interpolation and ingredients workflows.
        
        Returns:
            Dict mapping workflow_type -> video_path
        """
        results = {}
        
        # Test 1: Interpolation
        try:
            logger.info("🧪 A/B Test - Generating with INTERPOLATION...")
            orchestrator_interp = VeoWorkflowOrchestrator(
                self.gemini,
                WorkflowConfig(
                    selection_mode=WorkflowSelectionMode.ALWAYS_INTERPOLATION
                )
            )
            video_path, _ = await orchestrator_interp.generate_video_with_workflow(
                scene, assets
            )
            results["interpolation"] = video_path
            logger.info(f"✅ Interpolation video: {video_path}")
        except Exception as e:
            logger.error(f"❌ Interpolation failed: {e}")
            results["interpolation"] = None
        
        # Test 2: Ingredients
        try:
            logger.info("🧪 A/B Test - Generating with INGREDIENTS...")
            orchestrator_ingred = VeoWorkflowOrchestrator(
                self.gemini,
                WorkflowConfig(
                    selection_mode=WorkflowSelectionMode.ALWAYS_INGREDIENTS
                )
            )
            video_path, _ = await orchestrator_ingred.generate_video_with_workflow(
                scene, assets
            )
            results["ingredients"] = video_path
            logger.info(f"✅ Ingredients video: {video_path}")
        except Exception as e:
            logger.error(f"❌ Ingredients failed: {e}")
            results["ingredients"] = None
        
        # Save comparison manifest
        self._save_ab_test_manifest(scene, results)
        
        return results
    
    def _save_ab_test_manifest(
        self,
        scene: Dict[str, Any],
        results: Dict[str, str]
    ):
        """Save A/B test results for manual review"""
        import json
        from pathlib import Path
        
        output_dir = Path(self.config.ab_test_output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        manifest = {
            "scene_id": scene.get("scene_id"),
            "timestamp": time.time(),
            "results": results,
            "scene_metadata": {
                "duration": scene.get("duration"),
                "camera_movement": scene.get("cinematography", {}).get("camera_movement"),
                "first_frame": scene.get("keyframe_description", {}).get("first_frame_prompt", "")[:100],
                "last_frame": scene.get("keyframe_description", {}).get("last_frame_prompt", "")[:100]
            },
            "review_notes": {
                "interpolation_quality": "",
                "ingredients_quality": "",
                "winner": "",
                "notes": ""
            }
        }
        
        manifest_path = output_dir / f"{scene.get('scene_id')}_ab_test.json"
        with open(manifest_path, "w") as f:
            json.dump(manifest, f, indent=2)
        
        logger.info(f"📊 A/B test manifest saved: {manifest_path}")
```

### Usage Examples

```python
# Example 1: Use config default (ingredients)
config = WorkflowConfig(
    selection_mode=WorkflowSelectionMode.CONFIG_DEFAULT,
    default_workflow=VeoWorkflowType.INGREDIENTS_TO_VIDEO
)
orchestrator = VeoWorkflowOrchestrator(gemini, config)
video_path, classification = await orchestrator.generate_video_with_workflow(scene, assets)
# Always uses ingredients when conflict exists

# Example 2: Use LLM to decide intelligently
config = WorkflowConfig(
    selection_mode=WorkflowSelectionMode.LLM_INTELLIGENT,
    llm_model="gemini-2.0-flash-exp"
)
orchestrator = VeoWorkflowOrchestrator(gemini, config)
video_path, classification = await orchestrator.generate_video_with_workflow(scene, assets)
# LLM analyzes scene and decides based on acceptance criteria

# Example 3: Force interpolation for all scenes
config = WorkflowConfig(
    selection_mode=WorkflowSelectionMode.ALWAYS_INTERPOLATION
)
orchestrator = VeoWorkflowOrchestrator(gemini, config)
video_path, classification = await orchestrator.generate_video_with_workflow(scene, assets)
# Always uses interpolation

# Example 4: A/B test both workflows
config = WorkflowConfig(
    ab_test_enabled=True,
    ab_test_output_dir="output/ab_test"
)
ab_tester = ABTestOrchestrator(gemini, config)
results = await ab_tester.generate_ab_test(scene, assets)
# Generates: results["interpolation"] and results["ingredients"]
# Saves manifest for manual review
```

### Knowledge Base Building

For building a knowledge base from A/B tests:

```python
class WorkflowKnowledgeBase:
    """Builds knowledge base from A/B test results"""
    
    def __init__(self, ab_test_dir: str):
        self.ab_test_dir = Path(ab_test_dir)
    
    def collect_reviewed_tests(self) -> List[Dict[str, Any]]:
        """Collect all A/B tests that have been manually reviewed"""
        reviewed = []
        
        for manifest_file in self.ab_test_dir.glob("*_ab_test.json"):
            with open(manifest_file) as f:
                data = json.load(f)
            
            # Check if manually reviewed
            if data["review_notes"]["winner"]:
                reviewed.append(data)
        
        return reviewed
    
    def generate_training_data(self) -> List[Dict[str, Any]]:
        """Generate training data for fine-tuning LLM decision model"""
        reviewed = self.collect_reviewed_tests()
        
        training_data = []
        for test in reviewed:
            training_data.append({
                "scene_metadata": test["scene_metadata"],
                "winner": test["review_notes"]["winner"],
                "quality_notes": test["review_notes"]["notes"]
            })
        
        return training_data
    
    def export_knowledge_base(self, output_path: str):
        """Export knowledge base for future use"""
        training_data = self.generate_training_data()
        
        with open(output_path, "w") as f:
            json.dump({
                "version": "1.0",
                "total_samples": len(training_data),
                "training_data": training_data
            }, f, indent=2)
        
        logger.info(f"📚 Knowledge base exported: {output_path}")
```


## Character Reference Seeding Chain Pattern

### Overview

To ensure consistent character appearance across all generated images and videos, we use a **seeding chain** where the front view character reference acts as the canonical representation.

### Seeding Chain Flow

```
┌─────────────────────────────────────────────────────────────────┐
│  Step 1: Generate Front View (Canonical Reference)              │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Input: Text prompt only (no reference)                   │  │
│  │ Output: front_view.png                                   │  │
│  │ Purpose: Establish canonical character appearance        │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  Step 2: Generate Side View (Seeded from Front)                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Input: Text prompt + front_view.png as reference         │  │
│  │ Output: side_view.png                                    │  │
│  │ Purpose: Consistent side profile                         │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  Step 3: Generate Full Body (Seeded from Front)                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Input: Text prompt + front_view.png as reference         │  │
│  │ Output: full_body.png                                    │  │
│  │ Purpose: Consistent full body appearance                 │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  Step 4: Generate Back View (Seeded from Front) - Optional      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Input: Text prompt + front_view.png as reference         │  │
│  │ Output: back_view.png                                    │  │
│  │ Purpose: Consistent rear view for POV/behind shots       │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  Step 5: Generate Keyframes (Seeded from Front)                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Input: Scene prompt + front_view.png as reference        │  │
│  │ Output: scene_keyframe.png                               │  │
│  │ Purpose: Character consistency in scene-specific images  │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  Step 5: Generate Moodboards (Seeded from Front)                │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Input: Scene/environment prompt + front_view.png         │  │
│  │ Output: moodboard_tokyo.png, moodboard_paris.png        │  │
│  │ Purpose: Scene-specific images with character            │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  Step 6: Generate Video with Ingredients                        │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Input: Video prompt + [front_view.png, moodboard.png]   │  │
│  │ Output: scene_video.mp4                                  │  │
│  │ Purpose: Video with consistent character and scene       │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### Implementation

```python
class CharacterReferenceManager:
    """Manages character reference generation with seeding chain"""
    
    def __init__(self, gemini_client: GeminiMediaGen):
        self.gemini = gemini_client
        self.character_cache: Dict[str, Dict[str, str]] = {}
        # Structure: {char_id: {"front": path, "side": path, "full_body": path}}
    
    async def generate_character_references(
        self,
        character_id: str,
        character_description: Dict[str, Any],
        output_dir: str
    ) -> Dict[str, str]:
        """
        Generate all character reference views using seeding chain.
        
        Args:
            character_id: Unique character identifier
            character_description: Character metadata (appearance, style)
            output_dir: Directory to save reference images
            
        Returns:
            Dict mapping view -> image_path
        """
        results = {}
        
        # Step 1: Generate front view (no reference)
        logger.info(f"📸 Generating canonical front view for {character_id}")
        front_prompt = self._build_character_prompt(
            character_description, 
            view="front"
        )
        
        front_response = await self.gemini.generate_content(
            prompt=front_prompt,
            reference_image=None  # No reference for canonical view
        )
        
        front_path = f"{output_dir}/{character_id}_front.png"
        self.gemini.render_image(front_path, front_response)
        results["front"] = front_path
        
        logger.info(f"✅ Front view saved: {front_path}")
        
        # Step 2: Generate side view (seeded from front)
        logger.info(f"📸 Generating side view for {character_id} (seeded from front)")
        side_prompt = self._build_character_prompt(
            character_description,
            view="side"
        )
        
        side_response = await self.gemini.generate_content(
            prompt=side_prompt,
            reference_image=front_path  # ← Seeded from front
        )
        
        side_path = f"{output_dir}/{character_id}_side.png"
        self.gemini.render_image(side_path, side_response)
        results["side"] = side_path
        
        logger.info(f"✅ Side view saved: {side_path}")
        
        # Step 3: Generate full body (seeded from front)
        logger.info(f"📸 Generating full body for {character_id} (seeded from front)")
        full_body_prompt = self._build_character_prompt(
            character_description,
            view="full_body"
        )
        
        full_body_response = await self.gemini.generate_content(
            prompt=full_body_prompt,
            reference_image=front_path  # ← Seeded from front
        )
        
        full_body_path = f"{output_dir}/{character_id}_full_body.png"
        self.gemini.render_image(full_body_path, full_body_response)
        results["full_body"] = full_body_path
        
        logger.info(f"✅ Full body saved: {full_body_path}")
        
        # Cache for future use
        self.character_cache[character_id] = results
        
        return results
    
    async def generate_keyframe_with_character(
        self,
        scene_prompt: str,
        character_id: str,
        output_path: str
    ) -> str:
        """
        Generate scene keyframe with character consistency.
        Uses front view as reference.
        """
        if character_id not in self.character_cache:
            raise ValueError(f"Character {character_id} not in cache. Generate references first.")
        
        front_ref = self.character_cache[character_id]["front"]
        
        logger.info(f"📸 Generating keyframe with character reference: {front_ref}")
        
        response = await self.gemini.generate_content(
            prompt=scene_prompt,
            reference_image=front_ref  # ← Use canonical front view
        )
        
        self.gemini.render_image(output_path, response)
        logger.info(f"✅ Keyframe saved: {output_path}")
        
        return output_path
    
    async def generate_moodboard_with_character(
        self,
        scene_description: str,
        character_id: str,
        output_path: str
    ) -> str:
        """
        Generate scene-specific moodboard with character.
        Uses front view as reference for character consistency.
        """
        if character_id not in self.character_cache:
            raise ValueError(f"Character {character_id} not in cache. Generate references first.")
        
        front_ref = self.character_cache[character_id]["front"]
        
        logger.info(f"🎨 Generating moodboard with character reference: {front_ref}")
        
        response = await self.gemini.generate_content(
            prompt=scene_description,
            reference_image=front_ref  # ← Character-consistent moodboard
        )
        
        self.gemini.render_image(output_path, response)
        logger.info(f"✅ Moodboard saved: {output_path}")
        
        return output_path
    
    def get_canonical_reference(self, character_id: str) -> str:
        """Get the canonical (front view) reference for a character"""
        if character_id not in self.character_cache:
            raise ValueError(f"Character {character_id} not in cache")
        
        return self.character_cache[character_id]["front"]
    
    def _build_character_prompt(
        self,
        character_description: Dict[str, Any],
        view: str
    ) -> str:
        """Build character reference prompt for specific view"""
        appearance = character_description.get("physical_appearance", "")
        style = character_description.get("style", "")
        
        base = f"{appearance}, {style}"
        
        if view == "front":
            return f"""Neutral portrait photograph of {base}. 
Front view, centered, neutral expression, plain white background. 
Professional reference photo, studio lighting, high quality, 4K."""
        
        elif view == "side":
            return f"""Side profile photograph of {base}. 
90-degree side view, neutral expression, plain white background. 
Professional reference photo, studio lighting, high quality, 4K.
IMPORTANT: Maintain exact same appearance as front view."""
        
        elif view == "full_body":
            return f"""Full body photograph of {base}. 
Standing pose, front view, neutral expression, plain white background. 
Professional reference photo, studio lighting, high quality, 4K.
IMPORTANT: Maintain exact same appearance as front view."""
        
        elif view == "back":
            return f"""Back view photograph of {base}. 
Rear view showing back of head and shoulders, neutral pose, plain white background. 
Professional reference photo, studio lighting, high quality, 4K.
IMPORTANT: Maintain exact same appearance as front view (hair, clothing, build)."""
        
        return base
```

### Usage Example: Complete Workflow

```python
# Initialize managers
char_manager = CharacterReferenceManager(gemini)
orchestrator = VeoWorkflowOrchestrator(gemini, config)

# Character description
character = {
    "id": "CHAR_001",
    "physical_appearance": "28-year-old gender-neutral, olive skin, short dark hair",
    "style": "Dark structured travel jacket, slim-fit pants, black backpack"
}

# Step 1: Generate character references with seeding chain
char_refs = await char_manager.generate_character_references(
    character_id="CHAR_001",
    character_description=character,
    output_dir="output/characters"
)
# Output: {"front": "..._front.png", "side": "..._side.png", "full_body": "..._full_body.png"}

# Step 2: Generate scene-specific moodboard (optional)
moodboard_tokyo = await char_manager.generate_moodboard_with_character(
    scene_description="Tokyo Shibuya crossing at night, neon lights, rainy pavement",
    character_id="CHAR_001",
    output_path="output/moodboards/tokyo.png"
)

# Step 3: Generate keyframe with character consistency
keyframe = await char_manager.generate_keyframe_with_character(
    scene_prompt="Alex walking across Shibuya crossing, medium shot, neon lights",
    character_id="CHAR_001",
    output_path="output/keyframes/S1_first.png"
)

# Step 4: Generate video using ingredients workflow
scene = {
    "scene_id": "S1_Tokyo_Crossing",
    "duration": 4.0,
    "character_ids": ["CHAR_001"],
    # ... other scene metadata
}

assets = {
    "CHAR_001_reference": char_refs["front"],  # Use canonical front view
    "tokyo_moodboard": moodboard_tokyo  # Optional moodboard
}

video_path, classification = await orchestrator.generate_video_with_workflow(
    scene, assets
)
# Uses ingredients workflow with character reference + moodboard
```

### Benefits of Seeding Chain

1. **Consistency**: All character views reference the same canonical appearance
2. **Quality**: Front view establishes high-quality baseline
3. **Flexibility**: Can generate unlimited scene-specific images with character
4. **Efficiency**: Only one "seed" generation needed, rest are seeded
5. **Moodboard Support**: Can create scene-specific moodboards with character

### Integration with Workflow Selection

The seeding chain works seamlessly with both workflows:

**Interpolation Workflow:**
```python
# Generate keyframes with character consistency
first_frame = await char_manager.generate_keyframe_with_character(
    scene_prompt="Alex at start of crossing...",
    character_id="CHAR_001",
    output_path="S1_first.png"
)

last_frame = await char_manager.generate_keyframe_with_character(
    scene_prompt="Alex's foot mid-stride...",
    character_id="CHAR_001",
    output_path="S1_last.png"
)

# Both keyframes have consistent character appearance
video = await gemini.generate_video(
    prompt="...",
    image=first_frame,
    last_image=last_frame,
    duration=4.0
)
```

**Ingredients Workflow:**
```python
# Use canonical reference directly
canonical_ref = char_manager.get_canonical_reference("CHAR_001")

video = await gemini.generate_video(
    prompt="Using the provided image of Alex, create...",
    reference_images=[canonical_ref, moodboard_tokyo],
    duration=4.0
)
```


## Extended Character Views: Back View Support

### Why Back View Matters

Many cinematic shots require filming characters from behind:
- **POV shots**: Following character as they walk
- **Over-the-shoulder**: Dialogue scenes
- **Reveal shots**: Character facing away, then turns
- **Transition shots**: Character walking away from camera

### Extended Seeding Chain with Back View

```python
async def generate_character_references_extended(
    self,
    character_id: str,
    character_description: Dict[str, Any],
    output_dir: str,
    include_back_view: bool = True
) -> Dict[str, str]:
    """
    Generate all character reference views including optional back view.
    
    Views generated:
    - front (canonical)
    - side (seeded from front)
    - full_body (seeded from front)
    - back (seeded from front) - optional
    """
    results = {}
    
    # Step 1: Generate front view (canonical)
    front_prompt = self._build_character_prompt(character_description, "front")
    front_response = await self.gemini.generate_content(
        prompt=front_prompt,
        reference_image=None
    )
    front_path = f"{output_dir}/{character_id}_front.png"
    self.gemini.render_image(front_path, front_response)
    results["front"] = front_path
    logger.info(f"✅ Front view: {front_path}")
    
    # Step 2: Generate side view (seeded from front)
    side_prompt = self._build_character_prompt(character_description, "side")
    side_response = await self.gemini.generate_content(
        prompt=side_prompt,
        reference_image=front_path
    )
    side_path = f"{output_dir}/{character_id}_side.png"
    self.gemini.render_image(side_path, side_response)
    results["side"] = side_path
    logger.info(f"✅ Side view: {side_path}")
    
    # Step 3: Generate full body (seeded from front)
    full_body_prompt = self._build_character_prompt(character_description, "full_body")
    full_body_response = await self.gemini.generate_content(
        prompt=full_body_prompt,
        reference_image=front_path
    )
    full_body_path = f"{output_dir}/{character_id}_full_body.png"
    self.gemini.render_image(full_body_path, full_body_response)
    results["full_body"] = full_body_path
    logger.info(f"✅ Full body: {full_body_path}")
    
    # Step 4: Generate back view (seeded from front) - OPTIONAL
    if include_back_view:
        back_prompt = self._build_character_prompt(character_description, "back")
        back_response = await self.gemini.generate_content(
            prompt=back_prompt,
            reference_image=front_path  # Still seeded from front for consistency
        )
        back_path = f"{output_dir}/{character_id}_back.png"
        self.gemini.render_image(back_path, back_response)
        results["back"] = back_path
        logger.info(f"✅ Back view: {back_path}")
    
    # Cache all references
    self.character_cache[character_id] = results
    
    return results
```

### Selecting the Right View for Keyframes

```python
def get_reference_for_shot(
    self,
    character_id: str,
    shot_description: str
) -> str:
    """
    Select the appropriate character reference based on shot description.
    
    Returns the best reference view for the shot type.
    """
    if character_id not in self.character_cache:
        raise ValueError(f"Character {character_id} not in cache")
    
    refs = self.character_cache[character_id]
    shot_lower = shot_description.lower()
    
    # Check for back/behind shots
    if any(keyword in shot_lower for keyword in [
        "from behind", "back view", "rear view", "pov", 
        "following", "walks away", "over shoulder"
    ]):
        if "back" in refs:
            logger.info(f"🎯 Using back view for: {shot_description[:50]}...")
            return refs["back"]
    
    # Check for side shots
    if any(keyword in shot_lower for keyword in [
        "side view", "profile", "side angle", "90 degree"
    ]):
        logger.info(f"🎯 Using side view for: {shot_description[:50]}...")
        return refs["side"]
    
    # Check for full body shots
    if any(keyword in shot_lower for keyword in [
        "full body", "wide shot", "establishing", "full figure"
    ]):
        logger.info(f"🎯 Using full body for: {shot_description[:50]}...")
        return refs["full_body"]
    
    # Default to front view (canonical)
    logger.info(f"🎯 Using front view (default) for: {shot_description[:50]}...")
    return refs["front"]


async def generate_keyframe_smart(
    self,
    scene_prompt: str,
    character_id: str,
    output_path: str,
    shot_description: Optional[str] = None
) -> str:
    """
    Generate keyframe with automatically selected character reference.
    
    Intelligently selects front/side/back/full_body based on shot description.
    """
    # Select appropriate reference
    reference_path = self.get_reference_for_shot(
        character_id,
        shot_description or scene_prompt
    )
    
    logger.info(f"📸 Generating keyframe with reference: {reference_path}")
    
    response = await self.gemini.generate_content(
        prompt=scene_prompt,
        reference_image=reference_path
    )
    
    self.gemini.render_image(output_path, response)
    logger.info(f"✅ Keyframe saved: {output_path}")
    
    return output_path
```

### Usage Examples

**Example 1: Front-facing shot (default)**
```python
keyframe = await char_manager.generate_keyframe_smart(
    scene_prompt="Alex standing in Tokyo crossing, facing camera, neon lights",
    character_id="CHAR_001",
    output_path="S1_first.png",
    shot_description="medium shot, front view"
)
# Uses: front_view.png as reference
```

**Example 2: POV shot from behind**
```python
keyframe = await char_manager.generate_keyframe_smart(
    scene_prompt="Alex walking through Shibuya crossing, seen from behind, backpack visible",
    character_id="CHAR_001",
    output_path="S1_pov.png",
    shot_description="POV shot from behind, following character"
)
# Uses: back_view.png as reference
```

**Example 3: Side profile**
```python
keyframe = await char_manager.generate_keyframe_smart(
    scene_prompt="Alex in profile, looking at Eiffel Tower, golden hour",
    character_id="CHAR_001",
    output_path="S2_profile.png",
    shot_description="side angle, profile shot"
)
# Uses: side_view.png as reference
```

**Example 4: Full body establishing shot**
```python
keyframe = await char_manager.generate_keyframe_smart(
    scene_prompt="Alex standing on Santorini cliff, arms spread, full figure",
    character_id="CHAR_001",
    output_path="S4_wide.png",
    shot_description="wide shot, full body"
)
# Uses: full_body.png as reference
```

### Character Reference Views Summary

| View | When to Use | Seeded From | Use Cases |
|------|-------------|-------------|-----------|
| **front** | Default, face visible | None (canonical) | Dialogue, close-ups, medium shots |
| **side** | Profile shots | front | Side angles, walking past camera |
| **full_body** | Wide shots | front | Establishing shots, full figure |
| **back** | Rear view | front | POV, following shots, walking away |

### Benefits of Back View

1. **Cinematic Variety**: Support common "from behind" shots
2. **POV Sequences**: Following character through environments
3. **Transition Shots**: Character walking away into next scene
4. **Character Consistency**: Back of head, hair, clothing match front view
5. **Flexibility**: Can generate any angle while maintaining consistency

### Configuration

```python
# Generate all 4 views (recommended for cinematic projects)
char_refs = await char_manager.generate_character_references_extended(
    character_id="CHAR_001",
    character_description=character,
    output_dir="output/characters",
    include_back_view=True  # ← Include back view
)

# Generate only basic 3 views (faster, less cost)
char_refs = await char_manager.generate_character_references_extended(
    character_id="CHAR_001",
    character_description=character,
    output_dir="output/characters",
    include_back_view=False  # ← Skip back view
)
```


## Enhancer: Auto-Detecting Required Character Views

### Overview

The screenplay enhancer analyzes all scenes to determine which character views are needed, then adds this information to the character description. This ensures only necessary views are generated, optimizing cost and generation time.

### Enhancer Analysis Logic

```python
class ScreenplayEnhancer:
    """Enhances screenplay with derived metadata including required character views"""
    
    def enhance_character_views(self, screenplay: dict) -> dict:
        """
        Analyze screenplay and add required_views to each character.
        
        Returns enhanced screenplay with required_views populated.
        """
        characters = screenplay.get("character_description", [])
        scenes = screenplay.get("scenes", [])
        
        for character in characters:
            char_id = character["id"]
            
            # Analyze which views are needed for this character
            required_views = self._analyze_character_views(char_id, scenes)
            
            # Add to character description
            character["required_views"] = required_views
            character["view_analysis"] = {
                "detected_from_scenes": self._get_scenes_with_character(char_id, scenes),
                "detection_reason": self._get_detection_reasons(char_id, scenes)
            }
            
            logger.info(f"📊 Character {char_id} requires views: {required_views}")
        
        return screenplay
    
    def _analyze_character_views(
        self,
        char_id: int,
        scenes: List[dict]
    ) -> List[str]:
        """
        Analyze scenes to determine which character views are needed.
        
        Detection rules:
        - front: Always required (canonical reference)
        - back: Needed if "following", "tracking from behind", "walks away", POV shots
        - side: Needed if "profile", "side angle", "side view" mentioned
        - full_body: Needed if "wide shot", "establishing shot", "full body" mentioned
        """
        required_views = {"front"}  # Always need canonical front view
        
        for scene in scenes:
            # Check if character is in this scene
            primary_char = scene.get("characters", {}).get("primary_character_id")
            if primary_char != char_id:
                continue
            
            scene_id = scene.get("scene_id", "")
            
            # Analyze cinematography
            cinematography = scene.get("cinematography", {})
            camera_movement = cinematography.get("camera_movement", {})
            camera_setup = cinematography.get("camera_setup", {})
            
            # Check descriptions
            action_prompt = scene.get("action_prompt", "").lower()
            video_prompt = scene.get("video_prompt", "").lower()
            description = scene.get("context", "").lower()
            shot_type = camera_setup.get("shot_type", "").lower()
            movement_type = camera_movement.get("movement_type", "").lower()
            direction = camera_movement.get("direction", "").lower()
            
            # Combine all text for analysis
            all_text = f"{action_prompt} {video_prompt} {description} {shot_type} {movement_type} {direction}"
            
            # Detect back view needs
            back_keywords = [
                "following", "from behind", "behind", "rear view", "back view",
                "pov", "over shoulder", "walks away", "walking away",
                "tracking.*behind", "follows.*from"
            ]
            if any(keyword in all_text for keyword in back_keywords):
                required_views.add("back")
                logger.debug(f"   {scene_id}: Detected back view need - '{all_text[:50]}...'")
            
            # Detect side view needs
            side_keywords = [
                "profile", "side view", "side angle", "side shot",
                "90 degree", "lateral", "side-on"
            ]
            if any(keyword in all_text for keyword in side_keywords):
                required_views.add("side")
                logger.debug(f"   {scene_id}: Detected side view need")
            
            # Detect full body needs
            full_body_keywords = [
                "wide shot", "establishing shot", "full body", "full figure",
                "full shot", "wide angle", "full-length"
            ]
            if any(keyword in all_text for keyword in full_body_keywords) or \
               shot_type in ["wide shot", "establishing shot", "full shot"]:
                required_views.add("full_body")
                logger.debug(f"   {scene_id}: Detected full_body view need")
        
        return sorted(list(required_views))  # Sort for consistency
    
    def _get_scenes_with_character(
        self,
        char_id: int,
        scenes: List[dict]
    ) -> List[str]:
        """Get list of scene IDs featuring this character"""
        return [
            scene["scene_id"]
            for scene in scenes
            if scene.get("characters", {}).get("primary_character_id") == char_id
        ]
    
    def _get_detection_reasons(
        self,
        char_id: int,
        scenes: List[dict]
    ) -> Dict[str, List[str]]:
        """Get detailed reasons for each detected view"""
        reasons = {
            "front": ["Always required as canonical reference"],
            "back": [],
            "side": [],
            "full_body": []
        }
        
        for scene in scenes:
            primary_char = scene.get("characters", {}).get("primary_character_id")
            if primary_char != char_id:
                continue
            
            scene_id = scene.get("scene_id", "")
            camera_movement = scene.get("cinematography", {}).get("camera_movement", {})
            direction = camera_movement.get("direction", "").lower()
            
            # Check for back view triggers
            if "following" in direction or "behind" in direction:
                reasons["back"].append(f"{scene_id}: Camera following/tracking")
            
            # Add more specific detection reasons as needed
        
        # Remove empty lists
        return {k: v for k, v in reasons.items() if v}
```

### Enhanced Screenplay Output

After enhancement, the character description will include:

```json
{
  "character_description": [
    {
      "id": 1,
      "physical_appearance": "28, gender-neutral, medium build, olive skin, short dark hair.",
      "style": "Dark structured travel jacket, slim-fit pants, functional black backpack.",
      "target_alignment": "Universal appeal, consistent silhouette for match cuts.",
      "voice_characterstics": null,
      "required_views": ["back", "front", "full_body"],  // ← Added by enhancer
      "view_analysis": {  // ← Added by enhancer
        "detected_from_scenes": [
          "S1_Tokyo_Crossing",
          "S2_Paris_Street",
          "S3_Marrakech_Archway",
          "S4_Santorini_Sunset"
        ],
        "detection_reason": {
          "front": ["Always required as canonical reference"],
          "back": [
            "S1_Tokyo_Crossing: Camera following traveler",
            "S2_Paris_Street: Tracking shot following forward"
          ],
          "full_body": [
            "S4_Santorini_Sunset: Wide shot revealing vista"
          ]
        }
      }
    }
  ]
}
```

### Integration with CharacterReferenceManager

```python
class CharacterReferenceManager:
    
    async def generate_from_screenplay(
        self,
        screenplay: dict,
        output_dir: str
    ) -> Dict[int, Dict[str, str]]:
        """
        Generate character references based on enhanced screenplay.
        
        Reads required_views from character description.
        """
        all_results = {}
        
        for character in screenplay.get("character_description", []):
            char_id = character["id"]
            
            # Get required views from enhanced screenplay
            required_views = character.get("required_views", ["front"])
            
            if not required_views:
                logger.warning(f"⚠️  No required_views for character {char_id}, using default")
                required_views = ["front"]
            
            logger.info(f"📸 Generating {len(required_views)} views for character {char_id}: {required_views}")
            
            # Generate only required views
            results = await self._generate_views(
                character_id=f"CHAR_{char_id}",
                character_description=character,
                required_views=required_views,
                output_dir=output_dir
            )
            
            all_results[char_id] = results
        
        return all_results
    
    async def _generate_views(
        self,
        character_id: str,
        character_description: dict,
        required_views: List[str],
        output_dir: str
    ) -> Dict[str, str]:
        """
        Generate only the required character views using seeding chain.
        
        Always generates front first (canonical), then seeds other views from it.
        """
        results = {}
        
        # Ensure front is first (canonical)
        if "front" not in required_views:
            required_views.insert(0, "front")
        
        # Step 1: Generate front view (canonical)
        logger.info(f"📸 Generating canonical front view for {character_id}")
        front_prompt = self._build_character_prompt(character_description, "front")
        front_response = await self.gemini.generate_content(
            prompt=front_prompt,
            reference_image=None
        )
        front_path = f"{output_dir}/{character_id}_front.png"
        self.gemini.render_image(front_path, front_response)
        results["front"] = front_path
        logger.info(f"✅ Front view: {front_path}")
        
        # Step 2+: Generate other required views (seeded from front)
        for view in required_views:
            if view == "front":
                continue  # Already generated
            
            logger.info(f"📸 Generating {view} view for {character_id} (seeded from front)")
            view_prompt = self._build_character_prompt(character_description, view)
            view_response = await self.gemini.generate_content(
                prompt=view_prompt,
                reference_image=front_path  # ← Seeded from canonical front
            )
            view_path = f"{output_dir}/{character_id}_{view}.png"
            self.gemini.render_image(view_path, view_response)
            results[view] = view_path
            logger.info(f"✅ {view.capitalize()} view: {view_path}")
        
        # Cache all generated views
        self.character_cache[character_id] = results
        
        return results
```

### Example: Analyzing Your Screenplay

For the travel vlog screenplay with "following the traveler" shots:

```python
enhancer = ScreenplayEnhancer()
enhanced_screenplay = enhancer.enhance_character_views(screenplay)

# Output:
# 📊 Character 1 requires views: ['back', 'front', 'full_body']
#    S1_Tokyo_Crossing: Detected back view need - 'following the traveler forward'
#    S2_Paris_Street: Detected back view need - 'following the traveler forward'
#    S4_Santorini_Sunset: Detected full_body view need - 'wide shot'

# Then generate only required views
char_manager = CharacterReferenceManager(gemini)
char_refs = await char_manager.generate_from_screenplay(
    enhanced_screenplay,
    output_dir="output/characters"
)

# Generates:
# - CHAR_1_front.png (canonical)
# - CHAR_1_back.png (seeded from front) ← Detected from "following" shots
# - CHAR_1_full_body.png (seeded from front) ← Detected from wide shot
# Skips: side view (not needed)
```

### Benefits

1. **Automatic**: No manual specification needed
2. **Optimized**: Only generates views that are actually used
3. **Cost-efficient**: Saves on unnecessary image generations
4. **Transparent**: Logs detection reasons for debugging
5. **Flexible**: Can override by manually adding required_views to script

### Workflow Integration

```
┌─────────────────────────────────────────────────────────────────┐
│  Step 1: Parse Original Screenplay                              │
│  - Read gemini_screenplay.md                                    │
│  - Character has no required_views field                        │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  Step 2: Enhance with View Analysis                             │
│  - ScreenplayEnhancer.enhance_character_views()                 │
│  - Analyze all scenes for view requirements                     │
│  - Add required_views: ["front", "back", "full_body"]           │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  Step 3: Generate Character References                          │
│  - CharacterReferenceManager.generate_from_screenplay()         │
│  - Generate only required views with seeding chain              │
│  - front → back, full_body (skip side)                          │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  Step 4: Use in Video Generation                                │
│  - Smart reference selection based on shot type                 │
│  - "following" shots use back view                              │
│  - "wide" shots use full_body view                              │
└─────────────────────────────────────────────────────────────────┘
```
