"""
Workflow Parameter Builder

Builds API parameters for different Veo workflow types.
"""

import logging
from typing import Any, Dict, List, Optional

from cinema.workflow.models import VeoWorkflowType

logger = logging.getLogger(__name__)


class WorkflowParameterBuilder:
    """Builds GeminiMediaGen API parameters for each workflow type"""

    @staticmethod
    def normalize_duration(duration: float) -> float:
        """
        Normalize duration to valid Veo API range.
        
        - Rounds up to nearest integer (e.g., 3.5s -> 4s)
        - Clamps to minimum 4s
        - Clamps to maximum 8s
        
        Args:
            duration: Raw duration in seconds
            
        Returns:
            Normalized duration (4-8 seconds)
        """
        import math
        
        # Round up to nearest integer
        rounded = math.ceil(duration)
        
        # Clamp to valid range [4, 8]
        normalized = max(4, min(8, rounded))
        
        if normalized != duration:
            logger.debug(f"Duration normalized: {duration}s -> {normalized}s")
        
        return normalized

    def build_parameters(
        self,
        workflow_type: VeoWorkflowType,
        scene: Dict[str, Any],
        assets: Dict[str, str],
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
        logger.debug(f"Building parameters for {workflow_type.value}")

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
        self, scene: Dict[str, Any], assets: Dict[str, str]
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
        scene_id = scene.get("scene_id", "")
        first_frame_id = f"{scene_id}_first_frame"
        last_frame_id = f"{scene_id}_last_frame"

        if first_frame_id not in assets:
            raise ValueError(f"First frame asset not found: {first_frame_id}")
        if last_frame_id not in assets:
            raise ValueError(f"Last frame asset not found: {last_frame_id}")

        prompt = self._build_interpolation_prompt(scene)

        params = {
            "prompt": prompt,
            "image": assets[first_frame_id],
            "last_image": assets[last_frame_id],
            "duration": self.normalize_duration(scene.get("duration", 4.0)),
        }

        logger.debug(f"Interpolation params: image={first_frame_id}, last_image={last_frame_id}")
        return params

    def _build_interpolation_prompt(self, scene: Dict[str, Any]) -> str:
        """
        Build prompt for interpolation workflow.
        Format: Describe the motion/transformation between frames.
        """
        # Get camera movement description
        cinematography = scene.get("cinematography", {})
        camera_movement = cinematography.get("camera_movement", {})
        movement_type = camera_movement.get("movement_type", "")
        direction = camera_movement.get("direction", "")
        purpose = camera_movement.get("purpose", "")

        # Get video prompt if available
        video_prompt = scene.get("video_prompt", "")
        if video_prompt:
            return video_prompt

        # Build from components
        prompt_parts = []

        if movement_type:
            prompt_parts.append(f"{movement_type.capitalize()}")

        if direction:
            prompt_parts.append(f"{direction}")

        # Add action
        action = scene.get("action_prompt", scene.get("action", ""))
        if action:
            prompt_parts.append(action)

        # Add audio if specified
        audio_details = scene.get("audio_details", {})
        sfx = audio_details.get("sfx_description", "")
        if sfx:
            prompt_parts.append(f"SFX: {sfx}")

        prompt = ". ".join(prompt_parts) + "."
        logger.debug(f"Built interpolation prompt: {prompt[:100]}...")
        return prompt


    def _build_ingredients_params(
        self, scene: Dict[str, Any], assets: Dict[str, str]
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
        character_ids = scene.get("character_ids", [])
        if not character_ids:
            # Try to get from characters dict
            characters = scene.get("characters", {})
            primary_char = characters.get("primary_character_id")
            if primary_char:
                character_ids = [primary_char]

        reference_images = []
        for char_id in character_ids[:3]:  # Max 3 references
            ref_key = f"CHAR_{char_id}_reference"
            if ref_key in assets:
                reference_images.append(assets[ref_key])
            else:
                logger.warning(f"Character reference not found: {ref_key}")

        if not reference_images:
            raise ValueError(f"No character references found for scene {scene.get('scene_id')}")

        prompt = self._build_ingredients_prompt(scene, character_ids)

        params = {
            "prompt": prompt,
            "reference_images": reference_images,
            "duration": self.normalize_duration(scene.get("duration", 4.0)),
        }

        logger.debug(f"Ingredients params: {len(reference_images)} reference images")
        return params

    def _build_ingredients_prompt(
        self, scene: Dict[str, Any], character_ids: List[int]
    ) -> str:
        """
        Build prompt for ingredients workflow.
        Format: Reference the provided images explicitly.
        """
        # Get character names
        characters = scene.get("characters", {})
        char_names = []
        for cid in character_ids:
            # Try to get character name from scene or use ID
            char_names.append(f"character {cid}")

        # Get video prompt if available
        video_prompt = scene.get("video_prompt", "")
        if video_prompt:
            # Check if it already references images
            if "using the provided" in video_prompt.lower():
                return video_prompt
            # Prepend reference
            return f"Using the provided images for {', '.join(char_names)}, {video_prompt}"

        # Build from components
        prompt = f"Using the provided images for {', '.join(char_names)}, "

        # Add description
        description = scene.get("description", scene.get("action_prompt", ""))
        if description:
            prompt += description

        # Add dialogue if present
        dialogue = scene.get("dialogue", "")
        audio_details = scene.get("audio_details", {})
        dialogue_text = audio_details.get("dialogue_text", dialogue)
        if dialogue_text:
            prompt += f' {dialogue_text}'

        logger.debug(f"Built ingredients prompt: {prompt[:100]}...")
        return prompt


    def _build_timestamp_params(self, scene: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build parameters for timestamp prompting.

        API Call:
            generate_video(
                prompt=timestamp_formatted_prompt,
                duration=duration
            )
        """
        prompt = self._build_timestamp_prompt(scene)

        params = {
            "prompt": prompt,
            "duration": self.normalize_duration(scene.get("duration", 4.0)),
        }

        logger.debug(f"Timestamp params: duration={params['duration']}s")
        return params

    def _build_timestamp_prompt(self, scene: Dict[str, Any]) -> str:
        """
        Build prompt with timestamp notation.
        Format: [00:00:00-00:00:02] action 1. [00:00:02-00:00:04] action 2.
        """
        action_sequences = scene.get("action_sequences", [])

        if not action_sequences:
            # Fallback: use regular prompt
            logger.warning("No action_sequences found for timestamp prompting")
            return scene.get("video_prompt", scene.get("description", ""))

        prompt_parts = []
        for action in action_sequences:
            start = action.get("start_time", action.get("timestamp", "00:00:00"))
            end = action.get("end_time", "00:00:00")
            description = action.get("description", action.get("action", ""))

            # Format timestamp
            timestamp_str = f"[{start}-{end}]"
            prompt_parts.append(f"{timestamp_str} {description}")

        prompt = ". ".join(prompt_parts) + "."
        logger.debug(f"Built timestamp prompt: {prompt[:100]}...")
        return prompt

    def _build_text_to_video_params(self, scene: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build parameters for text-to-video.

        API Call:
            generate_video(
                prompt=prompt,
                duration=duration
            )
        """
        prompt = scene.get("video_prompt", scene.get("description", ""))

        params = {
            "prompt": prompt,
            "duration": self.normalize_duration(scene.get("duration", 4.0)),
        }

        logger.debug(f"Text-to-video params: prompt length={len(prompt)}")
        return params

    def _build_image_to_video_params(
        self, scene: Dict[str, Any], assets: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Build parameters for image-to-video.

        API Call:
            generate_video(
                prompt=prompt,
                image=image_path,
                duration=duration
            )
        """
        scene_id = scene.get("scene_id", "")
        first_frame_id = f"{scene_id}_first_frame"

        if first_frame_id not in assets:
            raise ValueError(f"First frame asset not found: {first_frame_id}")

        prompt = scene.get("video_prompt", scene.get("description", ""))

        params = {
            "prompt": prompt,
            "image": assets[first_frame_id],
            "duration": self.normalize_duration(scene.get("duration", 4.0)),
        }

        logger.debug(f"Image-to-video params: image={first_frame_id}")
        return params
