"""
Workflow Classifier

Classifies scenes into appropriate Veo workflow types based on scene metadata,
with support for config-based defaults and LLM-based intelligent decision making.
"""

import logging
from typing import Dict, Any, Optional

from google import genai

from cinema.workflow.models import (
    VeoWorkflowType,
    WorkflowSelectionMode,
    WorkflowClassification,
    WorkflowConfig
)

logger = logging.getLogger(__name__)


class WorkflowClassifier:
    """
    Classifies scenes with config-based and LLM-based decision support.
    
    Determines the optimal Veo workflow type for each scene based on:
    - Scene metadata (keyframes, characters, actions)
    - Configuration settings
    - LLM analysis (when enabled)
    """
    
    def __init__(
        self,
        config: WorkflowConfig,
        gemini_client: Optional[genai.Client] = None
    ):
        """
        Initialize WorkflowClassifier.
        
        Args:
            config: Workflow configuration
            gemini_client: Optional Gemini client for LLM decisions
        """
        self.config = config
        self.gemini_client = gemini_client or genai.Client()
        
        logger.info(f"WorkflowClassifier initialized")
        logger.info(f"  Selection mode: {config.selection_mode.value}")
        logger.info(f"  Default workflow: {config.default_workflow.value}")

    
    def classify_scene(
        self,
        scene: Dict[str, Any],
        available_assets: Dict[str, str]
    ) -> WorkflowClassification:
        """
        Analyze scene and determine optimal workflow using config or LLM.
        
        Args:
            scene: Scene metadata including:
                - scene_id: str
                - duration: float
                - keyframe_description: dict with first_frame, last_frame
                - character_ids: list
                - action_sequences: list (for timestamp prompting)
            available_assets: Dict of asset_id -> file_path
            
        Returns:
            WorkflowClassification with workflow type and reasoning
        """
        scene_id = scene.get("scene_id", "unknown")
        logger.info(f"🎯 Classifying workflow for scene: {scene_id}")
        
        # Check selection mode
        if self.config.selection_mode == WorkflowSelectionMode.ALWAYS_INTERPOLATION:
            return self._force_interpolation(scene, available_assets)
        
        if self.config.selection_mode == WorkflowSelectionMode.ALWAYS_INGREDIENTS:
            return self._force_ingredients(scene, available_assets)
        
        # Check for workflow conflicts
        has_interpolation = self._has_first_and_last_frames(scene)
        has_ingredients = self._has_character_references(scene)
        
        logger.debug(f"  Has first+last frames: {has_interpolation}")
        logger.debug(f"  Has character references: {has_ingredients}")
        
        if has_interpolation and has_ingredients:
            # Conflict: use config or LLM to decide
            logger.info("  ⚠️  Conflict: Both interpolation and ingredients are valid")
            return self._resolve_workflow_conflict(scene, available_assets)
        
        # Single workflow is valid
        # NOTE: Interpolation temporarily disabled - Gemini Veo doesn't support it yet
        # if has_interpolation:
        #     logger.info("  → Selected: Interpolation (has first+last frames)")
        #     return self._classify_interpolation(scene, available_assets)
        
        if has_ingredients:
            logger.info("  → Selected: Ingredients (has character references)")
            return self._classify_ingredients(scene, available_assets)
        
        # Fallback to image-to-video if we have keyframes (interpolation not supported)
        if has_interpolation:
            logger.info("  → Selected: Image-to-video (interpolation not yet supported by Gemini)")
            return self._classify_image_to_video(scene, available_assets)
        
        # Fallback workflows
        if self._has_timestamp_actions(scene):
            logger.info("  → Selected: Timestamp prompting (has action sequences)")
            return self._classify_timestamp(scene)
        
        if self._has_single_keyframe(scene):
            logger.info("  → Selected: Image-to-video (has single keyframe)")
            return self._classify_image_to_video(scene, available_assets)
        
        logger.info("  → Selected: Text-to-video (default)")
        return self._classify_text_to_video(scene)

    
    def _has_first_and_last_frames(self, scene: Dict[str, Any]) -> bool:
        """Check if scene has both first and last frame keyframe descriptions"""
        keyframes = scene.get("keyframe_description", {})
        # Check for both old format (first_frame_prompt) and new format (first_frame)
        has_first = "first_frame_prompt" in keyframes or "first_frame" in keyframes
        has_last = "last_frame_prompt" in keyframes or "last_frame" in keyframes
        return has_first and has_last
    
    def _has_character_references(self, scene: Dict[str, Any]) -> bool:
        """
        Check if scene references characters with available reference images.
        
        NOTE: Ingredients workflow is unreliable and not supported by Veo 3.1 API.
        This method now returns False to disable ingredients workflow entirely.
        Character consistency is achieved through keyframe images instead.
        """
        # Ingredients workflow disabled - keyframes already contain character images
        return False
    
    def _has_timestamp_actions(self, scene: Dict[str, Any]) -> bool:
        """Check if scene has multiple timed action sequences"""
        actions = scene.get("action_sequences", [])
        return len(actions) > 1 and all("timestamp" in a for a in actions)
    
    def _has_single_keyframe(self, scene: Dict[str, Any]) -> bool:
        """Check if scene has a single keyframe for image-to-video"""
        keyframes = scene.get("keyframe_description", {})
        # Check for both old format (first_frame_prompt) and new format (first_frame)
        has_first = "first_frame_prompt" in keyframes or "first_frame" in keyframes
        has_last = "last_frame_prompt" in keyframes or "last_frame" in keyframes
        return has_first and not has_last

    
    def _resolve_workflow_conflict(
        self,
        scene: Dict[str, Any],
        available_assets: Dict[str, str]
    ) -> WorkflowClassification:
        """Resolve conflict when both interpolation and ingredients are valid"""
        
        if self.config.selection_mode == WorkflowSelectionMode.CONFIG_DEFAULT:
            # Use configured default
            logger.info(f"⚙️  Using config default: {self.config.default_workflow.value}")
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
            logger.info("  → Defaulting to ingredients (more reliable)")
            return self._classify_ingredients(scene, available_assets)
    
    def _force_interpolation(
        self,
        scene: Dict[str, Any],
        available_assets: Dict[str, str]
    ) -> WorkflowClassification:
        """Force interpolation workflow"""
        logger.info("  → Forced: Interpolation (ALWAYS_INTERPOLATION mode)")
        return WorkflowClassification(
            workflow_type=VeoWorkflowType.FIRST_LAST_FRAME_INTERPOLATION,
            reason="Forced by configuration (ALWAYS_INTERPOLATION mode)",
            required_assets=self._get_keyframe_assets(scene),
            confidence=1.0,
            warnings=["Workflow forced by config, quality not validated"]
        )
    
    def _force_ingredients(
        self,
        scene: Dict[str, Any],
        available_assets: Dict[str, str]
    ) -> WorkflowClassification:
        """Force ingredients workflow"""
        logger.info("  → Forced: Ingredients (ALWAYS_INGREDIENTS mode)")
        return WorkflowClassification(
            workflow_type=VeoWorkflowType.INGREDIENTS_TO_VIDEO,
            reason="Forced by configuration (ALWAYS_INGREDIENTS mode)",
            required_assets=self._get_character_assets(scene),
            confidence=1.0,
            warnings=["Workflow forced by config"]
        )

    
    def _llm_decide_workflow(
        self,
        scene: Dict[str, Any],
        available_assets: Dict[str, str]
    ) -> WorkflowClassification:
        """Use LLM to decide between interpolation and ingredients"""
        
        # Build prompt with acceptance criteria
        keyframes = scene.get("keyframe_description", {})
        camera_movement = scene.get("cinematography", {}).get("camera_movement", {})
        
        prompt = f"""You are a video generation workflow expert. Decide between:
1. FIRST_LAST_FRAME_INTERPOLATION - Interpolate between two keyframes
2. INGREDIENTS_TO_VIDEO - Generate video using character references

Scene: {scene.get('scene_id')}
Duration: {scene.get('duration')}s
Camera: {camera_movement.get('movement_type', 'unknown')}

First Frame: {keyframes.get('first_frame_prompt', '')[:200]}...
Last Frame: {keyframes.get('last_frame_prompt', '')[:200]}...

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
            
            response_text = (response.text or "").strip()
            
            # Parse decision
            if "INTERPOLATION" in response_text.split("\n")[0]:
                workflow_type = VeoWorkflowType.FIRST_LAST_FRAME_INTERPOLATION
            else:
                workflow_type = VeoWorkflowType.INGREDIENTS_TO_VIDEO
            
            # Extract reason
            reason_lines = [l for l in response_text.split("\n") if "REASON:" in l]
            reason = reason_lines[0].replace("REASON:", "").strip() if reason_lines else "LLM decision"
            
            logger.info(f"🤖 LLM decided: {workflow_type.value}")
            logger.info(f"   Reason: {reason}")
            
            if workflow_type == VeoWorkflowType.FIRST_LAST_FRAME_INTERPOLATION:
                return self._classify_interpolation(scene, available_assets)
            else:
                return self._classify_ingredients(scene, available_assets)
        
        except Exception as e:
            logger.warning(f"LLM decision failed: {e}. Using default.")
            # Fallback to default
            if self.config.default_workflow == VeoWorkflowType.FIRST_LAST_FRAME_INTERPOLATION:
                return self._classify_interpolation(scene, available_assets)
            else:
                return self._classify_ingredients(scene, available_assets)

    
    def _classify_interpolation(
        self,
        scene: Dict[str, Any],
        available_assets: Dict[str, str]
    ) -> WorkflowClassification:
        """Classify as interpolation workflow"""
        scene_id = scene.get("scene_id", "unknown")
        required_assets = [
            f"{scene_id}_first_frame",
            f"{scene_id}_last_frame"
        ]
        
        return WorkflowClassification(
            workflow_type=VeoWorkflowType.FIRST_LAST_FRAME_INTERPOLATION,
            reason="Scene has first and last frame keyframes for interpolation",
            required_assets=required_assets,
            confidence=0.9
        )
    
    def _classify_ingredients(
        self,
        scene: Dict[str, Any],
        available_assets: Dict[str, str]
    ) -> WorkflowClassification:
        """Classify as ingredients workflow"""
        character_ids = scene.get("character_ids", [])
        required_assets = [f"{char_id}_reference" for char_id in character_ids]
        
        return WorkflowClassification(
            workflow_type=VeoWorkflowType.INGREDIENTS_TO_VIDEO,
            reason="Scene has character references for consistency",
            required_assets=required_assets,
            confidence=0.9
        )
    
    def _classify_timestamp(self, scene: Dict[str, Any]) -> WorkflowClassification:
        """Classify as timestamp prompting workflow"""
        return WorkflowClassification(
            workflow_type=VeoWorkflowType.TIMESTAMP_PROMPTING,
            reason="Scene has multiple timed action sequences",
            required_assets=[],
            confidence=0.9
        )
    
    def _classify_image_to_video(
        self,
        scene: Dict[str, Any],
        available_assets: Dict[str, str]
    ) -> WorkflowClassification:
        """Classify as image-to-video workflow"""
        scene_id = scene.get("scene_id", "unknown")
        required_assets = [f"{scene_id}_first_frame"]
        
        return WorkflowClassification(
            workflow_type=VeoWorkflowType.IMAGE_TO_VIDEO,
            reason="Scene has single keyframe for image-to-video",
            required_assets=required_assets,
            confidence=0.8
        )
    
    def _classify_text_to_video(self, scene: Dict[str, Any]) -> WorkflowClassification:
        """Classify as text-to-video workflow"""
        return WorkflowClassification(
            workflow_type=VeoWorkflowType.TEXT_TO_VIDEO,
            reason="Default text-to-video generation",
            required_assets=[],
            confidence=0.7
        )
    
    def _get_keyframe_assets(self, scene: Dict[str, Any]) -> list[str]:
        """Get required keyframe asset IDs"""
        scene_id = scene.get("scene_id", "unknown")
        return [f"{scene_id}_first_frame", f"{scene_id}_last_frame"]
    
    def _get_character_assets(self, scene: Dict[str, Any]) -> list[str]:
        """Get required character asset IDs"""
        character_ids = scene.get("character_ids", [])
        return [f"{char_id}_reference" for char_id in character_ids]
