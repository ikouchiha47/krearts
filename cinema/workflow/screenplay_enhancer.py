"""
Screenplay Enhancer for Auto-Detecting Required Character Views

Analyzes screenplay scenes to determine which character reference views
are needed (front, side, back, full_body) based on shot descriptions
and camera movements.
"""

import logging
from typing import Dict, List, Any, Set

logger = logging.getLogger(__name__)


class ScreenplayEnhancer:
    """
    Enhances screenplay with derived metadata including required character views.
    
    Analyzes all scenes to detect which character views are needed based on:
    - Shot descriptions
    - Camera movements
    - Cinematography details
    """
    
    def __init__(self):
        """Initialize ScreenplayEnhancer."""
        logger.info("ScreenplayEnhancer initialized")
    
    def enhance_character_views(self, screenplay: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze screenplay and add required_views to each character.
        
        Args:
            screenplay: Screenplay dictionary with keys:
                - character_description: List of character dicts
                - scenes: List of scene dicts
                
        Returns:
            Enhanced screenplay with required_views populated for each character
        """
        logger.info("🔍 Analyzing screenplay for required character views")
        
        characters = screenplay.get("character_description", [])
        scenes = screenplay.get("scenes", [])
        
        if not characters:
            logger.warning("No characters found in screenplay")
            return screenplay
        
        if not scenes:
            logger.warning("No scenes found in screenplay")
            return screenplay
        
        for character in characters:
            char_id = character.get("id")
            if char_id is None:
                logger.warning("Character missing 'id' field, skipping")
                continue
            
            # Analyze which views are needed for this character
            required_views = self._analyze_character_views(char_id, scenes)
            
            # Add to character description
            character["required_views"] = required_views
            character["view_analysis"] = {
                "detected_from_scenes": self._get_scenes_with_character(char_id, scenes),
                "detection_reasons": self._get_detection_reasons(char_id, scenes, required_views)
            }
            
            logger.info(f"📊 Character {char_id} requires views: {required_views}")
            for reason_view, reason_list in character["view_analysis"]["detection_reasons"].items():
                for reason in reason_list:
                    logger.debug(f"   {reason_view}: {reason}")
        
        logger.info("✅ Screenplay enhancement complete")
        return screenplay
    
    def _analyze_character_views(
        self,
        char_id: int,
        scenes: List[Dict[str, Any]]
    ) -> List[str]:
        """
        Analyze scenes to determine which character views are needed.
        
        Detection rules:
        - front: Always required (canonical reference)
        - back: Needed if "following", "tracking from behind", "walks away", POV shots
        - side: Needed if "profile", "side angle", "side view" mentioned
        - full_body: Needed if "wide shot", "establishing shot", "full body" mentioned
        
        Args:
            char_id: Character ID to analyze
            scenes: List of scene dictionaries
            
        Returns:
            Sorted list of required view names
        """
        required_views: Set[str] = {"front"}  # Always need canonical front view
        
        for scene in scenes:
            # Check if character is in this scene
            primary_char = scene.get("characters", {}).get("primary_character_id")
            if primary_char != char_id:
                continue
            
            scene_id = scene.get("scene_id", "")
            
            # Gather all text for analysis
            cinematography = scene.get("cinematography", {})
            camera_movement = cinematography.get("camera_movement", {})
            camera_setup = cinematography.get("camera_setup", {})
            
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
                "pov", "over shoulder", "walks away", "walking away"
            ]
            if any(keyword in all_text for keyword in back_keywords):
                required_views.add("back")
                logger.debug(f"   {scene_id}: Detected back view need - '{all_text[:80]}...'")
            
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
        scenes: List[Dict[str, Any]]
    ) -> List[str]:
        """
        Get list of scene IDs featuring this character.
        
        Args:
            char_id: Character ID
            scenes: List of scene dictionaries
            
        Returns:
            List of scene IDs
        """
        return [
            scene["scene_id"]
            for scene in scenes
            if scene.get("characters", {}).get("primary_character_id") == char_id
        ]
    
    def _get_detection_reasons(
        self,
        char_id: int,
        scenes: List[Dict[str, Any]],
        required_views: List[str]
    ) -> Dict[str, List[str]]:
        """
        Get detailed reasons for each detected view.
        
        Args:
            char_id: Character ID
            scenes: List of scene dictionaries
            required_views: List of detected required views
            
        Returns:
            Dict mapping view name to list of detection reasons
        """
        reasons: Dict[str, List[str]] = {
            "front": ["Always required as canonical reference"]
        }
        
        # Only add reason keys for views that were detected
        if "back" in required_views:
            reasons["back"] = []
        if "side" in required_views:
            reasons["side"] = []
        if "full_body" in required_views:
            reasons["full_body"] = []
        
        for scene in scenes:
            primary_char = scene.get("characters", {}).get("primary_character_id")
            if primary_char != char_id:
                continue
            
            scene_id = scene.get("scene_id", "")
            camera_movement = scene.get("cinematography", {}).get("camera_movement", {})
            camera_setup = scene.get("cinematography", {}).get("camera_setup", {})
            direction = camera_movement.get("direction", "").lower()
            movement_type = camera_movement.get("movement_type", "").lower()
            shot_type = camera_setup.get("shot_type", "").lower()
            
            # Check for back view triggers
            if "back" in required_views:
                if "following" in direction or "behind" in direction:
                    reasons["back"].append(f"{scene_id}: Camera following/tracking from behind")
                elif "following" in movement_type:
                    reasons["back"].append(f"{scene_id}: {movement_type.capitalize()} camera movement")
            
            # Check for side view triggers
            if "side" in required_views:
                if "profile" in shot_type or "side" in shot_type:
                    reasons["side"].append(f"{scene_id}: {shot_type.capitalize()} shot type")
            
            # Check for full body triggers
            if "full_body" in required_views:
                if shot_type in ["wide shot", "establishing shot", "full shot"]:
                    reasons["full_body"].append(f"{scene_id}: {shot_type.capitalize()}")
        
        # Remove empty lists
        return {k: v for k, v in reasons.items() if v}
