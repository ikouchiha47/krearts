"""
Integration Helpers

Helper functions to bridge between screenplay format and workflow classifier format.
Converts scene metadata and maps asset IDs to file paths.

This module provides integration between:
- Screenplay format (from movie_maker pipeline)
- WorkflowClassifier input format
- Asset path management
- Logging integration
"""

import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


def setup_workflow_logging(log_level: str = "INFO"):
    """
    Configure logging for workflow operations.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
    """
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    logger.info(f"Workflow logging configured at {log_level} level")


def convert_scene_to_classifier_input(
    scene: Dict[str, Any],
    screenplay: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Convert screenplay scene format to WorkflowClassifier input format.
    
    Screenplay scene format:
    {
        "scene_id": "S1_Tokyo_Crossing",
        "duration": 3.0,
        "keyframe_description": {
            "first_frame_prompt": "...",
            "last_frame_prompt": "..."
        },
        "characters": {
            "primary_character_id": 1
        },
        "action_prompt": "...",
        "video_prompt": "...",
        ...
    }
    
    Classifier input format:
    {
        "scene_id": "S1_Tokyo_Crossing",
        "duration": 3.0,
        "keyframe_description": {
            "first_frame": "...",
            "last_frame": "..."
        },
        "character_ids": [1],
        "action_sequences": [...],  # for timestamp prompting
        "cinematography": {...},
        "context": "..."
    }
    
    Args:
        scene: Scene dict from screenplay
        screenplay: Full screenplay dict (for character lookup)
        
    Returns:
        Scene dict formatted for WorkflowClassifier
    """
    logger.debug(f"Converting scene {scene.get('scene_id')} to classifier format")
    
    # Extract character IDs
    character_ids = []
    primary_char_id = scene.get("characters", {}).get("primary_character_id")
    if primary_char_id is not None:
        character_ids.append(primary_char_id)
    
    # Convert keyframe format
    keyframe_desc = scene.get("keyframe_description", {})
    classifier_keyframes = {}
    
    if keyframe_desc.get("first_frame_prompt"):
        classifier_keyframes["first_frame"] = keyframe_desc["first_frame_prompt"]
    
    if keyframe_desc.get("last_frame_prompt"):
        classifier_keyframes["last_frame"] = keyframe_desc["last_frame_prompt"]
    
    # Extract action sequences for timestamp prompting
    # (Currently not in screenplay format, but prepared for future)
    action_sequences = scene.get("action_sequences", [])
    
    # Build classifier input
    classifier_input = {
        "scene_id": scene.get("scene_id", "unknown"),
        "duration": scene.get("duration", 4.0),
        "keyframe_description": classifier_keyframes,
        "character_ids": character_ids,
        "action_sequences": action_sequences,
        "cinematography": scene.get("cinematography", {}),
        "context": scene.get("context", ""),
        "action_prompt": scene.get("action_prompt", ""),
        "video_prompt": scene.get("video_prompt", ""),
    }
    
    logger.debug(f"  Character IDs: {character_ids}")
    logger.debug(f"  Has first frame: {'first_frame' in classifier_keyframes}")
    logger.debug(f"  Has last frame: {'last_frame' in classifier_keyframes}")
    
    return classifier_input


def map_asset_ids_to_paths(
    scene: Dict[str, Any],
    character_refs: Dict[int, Dict[str, str]],
    keyframe_dir: str,
    output_dir: str
) -> Dict[str, str]:
    """
    Map asset IDs to file paths for workflow classifier.
    
    Creates a mapping of asset identifiers to their file system paths.
    
    Args:
        scene: Scene dict from screenplay
        character_refs: Dict mapping character_id -> {view: path}
            Example: {1: {"front": "output/CHAR_1_front.png", ...}}
        keyframe_dir: Directory where keyframes are stored
        output_dir: Base output directory
        
    Returns:
        Dict mapping asset_id -> file_path
        Example: {
            "CHAR_1_reference": "output/characters/CHAR_1_front.png",
            "S1_Tokyo_Crossing_first_frame": "output/keyframes/S1_first.png",
            "S1_Tokyo_Crossing_last_frame": "output/keyframes/S1_last.png"
        }
    """
    scene_id = scene.get("scene_id", "unknown")
    logger.debug(f"Mapping asset IDs to paths for scene {scene_id}")
    
    asset_map = {}
    
    # Map character references
    character_ids = []
    primary_char_id = scene.get("characters", {}).get("primary_character_id")
    if primary_char_id is not None:
        character_ids.append(primary_char_id)
    
    for char_id in character_ids:
        if char_id in character_refs:
            # Use front view as canonical reference
            front_path = character_refs[char_id].get("front")
            if front_path:
                asset_id = f"CHAR_{char_id}_reference"
                asset_map[asset_id] = front_path
                logger.debug(f"  Mapped {asset_id} -> {front_path}")
    
    # Map keyframes
    keyframe_desc = scene.get("keyframe_description", {})
    
    if keyframe_desc.get("first_frame_prompt"):
        first_frame_id = f"{scene_id}_first_frame"
        first_frame_path = str(Path(keyframe_dir) / f"{scene_id}_first.png")
        asset_map[first_frame_id] = first_frame_path
        logger.debug(f"  Mapped {first_frame_id} -> {first_frame_path}")
    
    if keyframe_desc.get("last_frame_prompt"):
        last_frame_id = f"{scene_id}_last_frame"
        last_frame_path = str(Path(keyframe_dir) / f"{scene_id}_last.png")
        asset_map[last_frame_id] = last_frame_path
        logger.debug(f"  Mapped {last_frame_id} -> {last_frame_path}")
    
    return asset_map


def get_character_reference_for_scene(
    scene: Dict[str, Any],
    character_refs: Dict[int, Dict[str, str]],
    view: str = "front"
) -> Optional[str]:
    """
    Get character reference path for a scene.
    
    Args:
        scene: Scene dict from screenplay
        character_refs: Dict mapping character_id -> {view: path}
        view: Which view to get (default: "front")
        
    Returns:
        Path to character reference image, or None if not found
    """
    primary_char_id = scene.get("characters", {}).get("primary_character_id")
    
    if primary_char_id is None:
        return None
    
    if primary_char_id not in character_refs:
        logger.warning(f"Character {primary_char_id} not found in character_refs")
        return None
    
    char_views = character_refs[primary_char_id]
    
    if view not in char_views:
        logger.warning(f"View '{view}' not found for character {primary_char_id}")
        # Fallback to front view
        return char_views.get("front")
    
    return char_views[view]


def get_keyframe_paths(
    scene: Dict[str, Any],
    keyframe_dir: str
) -> Dict[str, str]:
    """
    Get keyframe file paths for a scene.
    
    Args:
        scene: Scene dict from screenplay
        keyframe_dir: Directory where keyframes are stored
        
    Returns:
        Dict with keys "first_frame" and/or "last_frame" mapping to paths
    """
    scene_id = scene.get("scene_id", "unknown")
    keyframe_desc = scene.get("keyframe_description", {})
    
    paths = {}
    
    if keyframe_desc.get("first_frame_prompt"):
        paths["first_frame"] = str(Path(keyframe_dir) / f"{scene_id}_first.png")
    
    if keyframe_desc.get("last_frame_prompt"):
        paths["last_frame"] = str(Path(keyframe_dir) / f"{scene_id}_last.png")
    
    return paths


def extract_scenes_from_screenplay(
    screenplay: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Extract scenes list from screenplay.
    
    Args:
        screenplay: Full screenplay dict
        
    Returns:
        List of scene dicts
    """
    scenes = screenplay.get("scenes", [])
    logger.info(f"Extracted {len(scenes)} scenes from screenplay")
    return scenes


def extract_characters_from_screenplay(
    screenplay: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Extract characters list from screenplay.
    
    Args:
        screenplay: Full screenplay dict
        
    Returns:
        List of character dicts
    """
    characters = screenplay.get("character_description", [])
    logger.info(f"Extracted {len(characters)} characters from screenplay")
    return characters


def build_output_paths(
    base_output_dir: str,
    scene_id: str
) -> Dict[str, str]:
    """
    Build standard output paths for a scene.
    
    Args:
        base_output_dir: Base output directory
        scene_id: Scene identifier
        
    Returns:
        Dict with keys:
            - video: Path for generated video
            - first_frame: Path for first frame keyframe
            - last_frame: Path for last frame keyframe
    """
    base_path = Path(base_output_dir)
    
    return {
        "video": str(base_path / "videos" / f"{scene_id}.mp4"),
        "first_frame": str(base_path / "keyframes" / f"{scene_id}_first.png"),
        "last_frame": str(base_path / "keyframes" / f"{scene_id}_last.png"),
    }


def log_workflow_decision(
    scene_id: str,
    workflow_type: str,
    reason: str,
    confidence: float
):
    """
    Log workflow decision with consistent formatting.
    
    Args:
        scene_id: Scene identifier
        workflow_type: Selected workflow type
        reason: Reason for selection
        confidence: Confidence score (0.0 to 1.0)
    """
    logger.info(f"🎯 Workflow Decision for {scene_id}")
    logger.info(f"   Type: {workflow_type}")
    logger.info(f"   Reason: {reason}")
    logger.info(f"   Confidence: {confidence:.2f}")


def validate_scene_assets(
    scene: Dict[str, Any],
    asset_map: Dict[str, str]
) -> tuple[bool, List[str]]:
    """
    Validate that all required assets exist for a scene.
    
    Args:
        scene: Scene dict
        asset_map: Dict mapping asset_id -> file_path
        
    Returns:
        (is_valid, missing_assets)
    """
    missing = []
    
    for asset_id, asset_path in asset_map.items():
        if not Path(asset_path).exists():
            missing.append(f"{asset_id}: {asset_path}")
            logger.warning(f"  Missing asset: {asset_id} at {asset_path}")
    
    is_valid = len(missing) == 0
    
    if is_valid:
        logger.debug(f"  All assets validated for scene {scene.get('scene_id')}")
    else:
        logger.error(f"  {len(missing)} missing assets for scene {scene.get('scene_id')}")
    
    return is_valid, missing



def convert_pipeline_state_to_asset_map(state, scene_id: str) -> Dict[str, str]:
    """
    Convert PipelineState to asset map for a specific scene.

    This is a convenience function for movie_maker.py integration.

    Args:
        state: PipelineState object from pipeline
        scene_id: Scene identifier

    Returns:
        Dict mapping asset_id -> file_path
    """
    asset_map = {}

    # Add character references
    if hasattr(state, "screenplay_dict") and state.screenplay_dict:
        scenes = state.screenplay_dict.get("scenes", [])
        scene = next((s for s in scenes if s.get("scene_id") == scene_id), None)

        if scene:
            primary_char_id = scene.get("characters", {}).get("primary_character_id")
            if primary_char_id is not None:
                # Try to find character reference with char_101 format (from CharacterReferenceManager)
                for view in ["front", "side", "full_body"]:
                    char_path = state.get_character_image_path(
                        primary_char_id, view
                    )
                    if char_path.exists():
                        asset_map[f"CHAR_{primary_char_id}_reference"] = str(
                            char_path
                        )
                        logger.debug(
                            f"  Added character reference: CHAR_{primary_char_id}_reference -> {char_path}"
                        )
                        break  # Only need one view as reference

    # Add keyframes
    first_frame_path = state.get_scene_image_path(scene_id, "first_frame")
    if first_frame_path.exists():
        asset_map[f"{scene_id}_first_frame"] = str(first_frame_path)
        logger.debug(f"  Added first frame: {scene_id}_first_frame")

    last_frame_path = state.get_scene_image_path(scene_id, "last_frame")
    if last_frame_path.exists():
        asset_map[f"{scene_id}_last_frame"] = str(last_frame_path)
        logger.debug(f"  Added last frame: {scene_id}_last_frame")

    return asset_map


def get_scene_from_screenplay(
    screenplay: Dict[str, Any],
    scene_id: str
) -> Optional[Dict[str, Any]]:
    """
    Get a specific scene from screenplay by scene_id.
    
    Args:
        screenplay: Full screenplay dict
        scene_id: Scene identifier
        
    Returns:
        Scene dict or None if not found
    """
    scenes = screenplay.get("scenes", [])
    scene = next((s for s in scenes if s.get("scene_id") == scene_id), None)
    
    if scene:
        logger.debug(f"Found scene: {scene_id}")
    else:
        logger.warning(f"Scene not found: {scene_id}")
    
    return scene


def build_character_reference_map(
    state,
    character_ids: List[int]
) -> Dict[int, Dict[str, str]]:
    """
    Build character reference map from PipelineState.
    
    Args:
        state: PipelineState object
        character_ids: List of character IDs
        
    Returns:
        Dict mapping character_id -> {view: path}
        Example: {1: {"front": "path/to/front.png", "side": "path/to/side.png"}}
    """
    char_map = {}
    
    for char_id in character_ids:
        views = {}
        for view in ["front", "side", "full_body"]:
            path = state.get_character_image_path(char_id, view)
            if path.exists():
                views[view] = str(path)
        
        if views:
            char_map[char_id] = views
            logger.debug(f"  Character {char_id}: {len(views)} views available")
    
    return char_map


def log_asset_availability(
    scene_id: str,
    asset_map: Dict[str, str]
):
    """
    Log asset availability for debugging.
    
    Args:
        scene_id: Scene identifier
        asset_map: Dict mapping asset_id -> file_path
    """
    logger.info(f"📦 Assets for {scene_id}:")
    
    if not asset_map:
        logger.info("  No assets available")
        return
    
    for asset_id, asset_path in asset_map.items():
        exists = Path(asset_path).exists()
        status = "✓" if exists else "✗"
        logger.info(f"  {status} {asset_id}: {asset_path}")


def validate_workflow_prerequisites(
    scene: Dict[str, Any],
    asset_map: Dict[str, str],
    workflow_type: str
) -> tuple[bool, List[str]]:
    """
    Validate that all prerequisites are met for a specific workflow.
    
    Args:
        scene: Scene dict
        asset_map: Dict mapping asset_id -> file_path
        workflow_type: Workflow type (e.g., "FIRST_LAST_FRAME_INTERPOLATION")
        
    Returns:
        (is_valid, error_messages)
    """
    errors = []
    scene_id = scene.get("scene_id", "unknown")
    
    if workflow_type == "FIRST_LAST_FRAME_INTERPOLATION":
        # Check for first and last frame
        first_frame_id = f"{scene_id}_first_frame"
        last_frame_id = f"{scene_id}_last_frame"
        
        if first_frame_id not in asset_map:
            errors.append(f"Missing first frame for interpolation: {first_frame_id}")
        elif not Path(asset_map[first_frame_id]).exists():
            errors.append(f"First frame file not found: {asset_map[first_frame_id]}")
        
        if last_frame_id not in asset_map:
            errors.append(f"Missing last frame for interpolation: {last_frame_id}")
        elif not Path(asset_map[last_frame_id]).exists():
            errors.append(f"Last frame file not found: {asset_map[last_frame_id]}")
    
    elif workflow_type == "INGREDIENTS_TO_VIDEO":
        # Check for character references
        has_char_ref = any("reference" in asset_id for asset_id in asset_map.keys())
        if not has_char_ref:
            errors.append("Missing character references for ingredients workflow")
    
    elif workflow_type == "IMAGE_TO_VIDEO":
        # Check for first frame
        first_frame_id = f"{scene_id}_first_frame"
        if first_frame_id not in asset_map:
            errors.append(f"Missing first frame for image-to-video: {first_frame_id}")
        elif not Path(asset_map[first_frame_id]).exists():
            errors.append(f"First frame file not found: {asset_map[first_frame_id]}")
    
    is_valid = len(errors) == 0
    
    if not is_valid:
        logger.error(f"Workflow prerequisites not met for {scene_id}:")
        for error in errors:
            logger.error(f"  - {error}")
    
    return is_valid, errors
