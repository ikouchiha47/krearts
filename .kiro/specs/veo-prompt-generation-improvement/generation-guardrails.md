# Post-Generation Guardrails

## Overview

After generating images/videos, we need to validate that the output matches the creative intent. Some fields from the screenplay can serve as **validation criteria** rather than generation inputs.

---

## Guardrail Categories

### 1. Visual Consistency Guardrails

**Purpose**: Ensure visual elements remain consistent across scenes

**Fields to Keep**:
```python
{
  "visual_continuity": {
    "consistent_element": "VibeFlow headphones",  # Must appear in all scenes
    "character_id": "CHAR_1",  # Character must be recognizable
    "color_palette": "Cool blues, whites",  # Dominant colors should match
    "lighting": "High-key, harsh fluorescent",  # Lighting style should match
    "critical_match_points": "Headphone earcup in bottom-right quadrant"  # For match cuts
  }
}
```

**Validation**:
- Run image analysis on generated frames
- Check if consistent element (product/character) is present
- Verify color palette matches (histogram analysis)
- For match cuts: verify element position matches between scenes

**Example Check**:
```python
def validate_visual_consistency(scene, generated_image):
    """Validate generated image matches visual continuity requirements."""
    
    # Check 1: Consistent element present
    if scene.visual_continuity.consistent_element:
        detected_objects = detect_objects(generated_image)
        if scene.visual_continuity.consistent_element not in detected_objects:
            return False, f"Missing: {scene.visual_continuity.consistent_element}"
    
    # Check 2: Color palette match
    if scene.visual_continuity.color_palette:
        dominant_colors = extract_dominant_colors(generated_image)
        expected_colors = parse_color_palette(scene.visual_continuity.color_palette)
        if not colors_match(dominant_colors, expected_colors, threshold=0.7):
            return False, f"Color mismatch: expected {expected_colors}, got {dominant_colors}"
    
    # Check 3: Character present (if specified)
    if scene.visual_continuity.character_id:
        faces = detect_faces(generated_image)
        if len(faces) == 0:
            return False, f"Character {scene.visual_continuity.character_id} not detected"
    
    return True, "Visual consistency validated"
```

---

### 2. Camera Consistency Guardrails (for Match Cuts)

**Purpose**: Ensure match cuts have proper geometric alignment

**Fields to Keep**:
```python
{
  "camera_consistency": {
    "critical_visual_anchors": "Headphone earcup position",
    "eye_line": "horizontal center",
    "compositional_notes": "White screen in central-right quadrant"
  }
}
```

**Validation**:
- For match cuts: compare last frame of Scene A with first frame of Scene B
- Check if critical visual anchor is in same position
- Verify eye-line alignment
- Validate compositional elements match

**Example Check**:
```python
def validate_match_cut(scene_a, scene_b, image_a_last, image_b_first):
    """Validate match cut alignment between two scenes."""
    
    # Extract critical anchor from both images
    anchor_element = scene_a.camera_consistency.critical_visual_anchors
    
    # Detect anchor position in both frames
    position_a = detect_element_position(image_a_last, anchor_element)
    position_b = detect_element_position(image_b_first, anchor_element)
    
    # Check if positions match (within tolerance)
    if not positions_match(position_a, position_b, tolerance=0.05):
        return False, f"Match cut misalignment: {anchor_element} at {position_a} vs {position_b}"
    
    # Check eye-line alignment
    if scene_a.camera_consistency.eye_line == scene_b.camera_consistency.eye_line:
        eyeline_a = detect_eyeline(image_a_last)
        eyeline_b = detect_eyeline(image_b_first)
        if abs(eyeline_a - eyeline_b) > 0.1:
            return False, f"Eye-line mismatch: {eyeline_a} vs {eyeline_b}"
    
    return True, "Match cut validated"
```

---

### 3. Character Consistency Guardrails

**Purpose**: Ensure character appearance remains consistent across scenes

**Fields to Keep**:
```python
{
  "characters": {
    "primary_character_id": 1
  },
  "character_description": {
    "id": 1,
    "physical_appearance": "32-year-old man, Black, short black hair, athletic build"
  }
}
```

**Validation**:
- Run face detection/recognition on generated images
- Compare detected face with character reference images
- Verify physical attributes match (age, race, build)

**Example Check**:
```python
def validate_character_consistency(scene, generated_image, character_refs):
    """Validate character appearance matches reference."""
    
    if not scene.characters or not scene.characters.primary_character_id:
        return True, "No character validation needed"
    
    char_id = scene.characters.primary_character_id
    reference_images = character_refs[char_id]
    
    # Detect faces in generated image
    detected_faces = detect_faces(generated_image)
    if len(detected_faces) == 0:
        return False, f"Character {char_id} not detected in scene"
    
    # Compare with reference images
    similarity_scores = []
    for ref_img in reference_images:
        score = compare_faces(detected_faces[0], ref_img)
        similarity_scores.append(score)
    
    max_similarity = max(similarity_scores)
    if max_similarity < 0.7:  # Threshold
        return False, f"Character {char_id} similarity too low: {max_similarity}"
    
    return True, f"Character validated (similarity: {max_similarity})"
```

---

### 4. Scene Flow Guardrails

**Purpose**: Ensure transitions between scenes are appropriate

**Fields to Keep**:
```python
{
  "scene_flow": {
    "previous_scene": "S1_Office_Focus",
    "next_scene": "S2_Gym_Power",
    "transition_technique": "match_cut_graphic",
    "visual_bridge_element": "White rectangular screen",
    "narrative_purpose": "Show seamless transition from focus to power"
  }
}
```

**Validation**:
- Check if transition technique is properly executed
- Verify visual bridge element is present in both scenes
- Validate narrative flow makes sense

**Example Check**:
```python
def validate_scene_transition(scene_a, scene_b, video_a, video_b):
    """Validate transition between scenes."""
    
    transition = scene_a.scene_flow.transition_technique
    
    if transition == "match_cut_graphic":
        # Extract last frame of A and first frame of B
        last_frame_a = extract_frame(video_a, -1)
        first_frame_b = extract_frame(video_b, 0)
        
        # Check visual bridge element
        bridge_element = scene_a.scene_flow.visual_bridge_element
        if bridge_element:
            present_in_a = detect_element(last_frame_a, bridge_element)
            present_in_b = detect_element(first_frame_b, bridge_element)
            
            if not (present_in_a and present_in_b):
                return False, f"Visual bridge '{bridge_element}' missing"
    
    elif transition == "smash_cut":
        # Verify abrupt contrast
        last_frame_a = extract_frame(video_a, -1)
        first_frame_b = extract_frame(video_b, 0)
        
        contrast = calculate_visual_contrast(last_frame_a, first_frame_b)
        if contrast < 0.5:  # Should be high contrast
            return False, f"Smash cut lacks contrast: {contrast}"
    
    return True, "Transition validated"
```

---

### 5. Duration Guardrails

**Purpose**: Ensure generated videos match expected duration

**Fields to Keep**:
```python
{
  "duration": 5.0,
  "generation_strategy": {
    "duration_generate": 5.0,
    "duration_trim": null
  }
}
```

**Validation**:
- Check actual video duration matches expected
- Verify trim operations were applied correctly

**Example Check**:
```python
def validate_duration(scene, generated_video):
    """Validate video duration matches expected."""
    
    actual_duration = get_video_duration(generated_video)
    expected_duration = scene.duration
    
    # Allow 0.1s tolerance
    if abs(actual_duration - expected_duration) > 0.1:
        return False, f"Duration mismatch: expected {expected_duration}s, got {actual_duration}s"
    
    return True, "Duration validated"
```

---

### 6. Audio Sync Guardrails

**Purpose**: Ensure audio aligns with video timing

**Fields to Keep**:
```python
{
  "audio_details": {
    "dialogue_timing": "00:00:00-00:02:00",
    "sfx_timing": "00:02:50",
    "ambient_mood": "Tense and frustrating"
  }
}
```

**Validation**:
- Check if audio clip duration matches video duration
- Verify dialogue timing aligns with video content
- Validate SFX timing matches visual events

**Example Check**:
```python
def validate_audio_sync(scene, video, audio_clip):
    """Validate audio synchronization with video."""
    
    video_duration = get_video_duration(video)
    audio_duration = get_audio_duration(audio_clip)
    
    # Check duration match
    if abs(video_duration - audio_duration) > 0.1:
        return False, f"Audio/video duration mismatch: {audio_duration}s vs {video_duration}s"
    
    # Check dialogue timing (if specified)
    if scene.audio_details and scene.audio_details.dialogue_timing:
        dialogue_segments = parse_timing(scene.audio_details.dialogue_timing)
        
        # Verify dialogue is present in audio at specified times
        for start, end in dialogue_segments:
            has_speech = detect_speech_in_range(audio_clip, start, end)
            if not has_speech:
                return False, f"No speech detected at {start}-{end}s"
    
    return True, "Audio sync validated"
```

---

## Recommended Guardrail Fields to Keep

### Essential (for validation):
1. ✅ `visual_continuity.consistent_element` - Check product/character presence
2. ✅ `visual_continuity.character_id` - Verify character consistency
3. ✅ `visual_continuity.critical_match_points` - Validate match cuts
4. ✅ `camera_consistency.critical_visual_anchors` - Match cut alignment
5. ✅ `scene_flow.transition_technique` - Validate transition execution
6. ✅ `scene_flow.visual_bridge_element` - Check bridge element presence
7. ✅ `duration` - Verify video length
8. ✅ `characters.primary_character_id` - Character validation

### Optional (nice to have):
1. ⚠️ `visual_continuity.color_palette` - Color consistency check
2. ⚠️ `visual_continuity.lighting` - Lighting style validation
3. ⚠️ `camera_consistency.eye_line` - Eye-line alignment
4. ⚠️ `audio_details.dialogue_timing` - Audio sync validation
5. ⚠️ `scene_flow.narrative_purpose` - Narrative coherence check

### Remove (not useful for validation):
1. ❌ `cinematography.camera_setup` - Already in prompts, can't validate
2. ❌ `cinematography.camera_movement` - Already in prompts, can't validate
3. ❌ `audio_details.voice_characteristics` - Subjective, hard to validate
4. ❌ `audio_details.ambient_mood` - Subjective, hard to validate

---

## Validation Pipeline

```python
def validate_generated_scene(scene, generated_assets, character_refs):
    """
    Run all guardrail checks on generated scene.
    
    Returns:
        (is_valid, issues)
    """
    issues = []
    
    # 1. Visual consistency
    if "image" in generated_assets or "video" in generated_assets:
        frame = extract_frame(generated_assets.get("video") or generated_assets.get("image"))
        valid, msg = validate_visual_consistency(scene, frame)
        if not valid:
            issues.append(f"Visual: {msg}")
    
    # 2. Character consistency
    if scene.characters:
        valid, msg = validate_character_consistency(scene, frame, character_refs)
        if not valid:
            issues.append(f"Character: {msg}")
    
    # 3. Duration
    if "video" in generated_assets:
        valid, msg = validate_duration(scene, generated_assets["video"])
        if not valid:
            issues.append(f"Duration: {msg}")
    
    # 4. Audio sync
    if "audio" in generated_assets:
        valid, msg = validate_audio_sync(scene, generated_assets["video"], generated_assets["audio"])
        if not valid:
            issues.append(f"Audio: {msg}")
    
    return len(issues) == 0, issues

def validate_scene_transitions(scenes, generated_videos):
    """
    Validate transitions between consecutive scenes.
    """
    issues = []
    
    for i in range(len(scenes) - 1):
        scene_a = scenes[i]
        scene_b = scenes[i + 1]
        video_a = generated_videos[scene_a.scene_id]
        video_b = generated_videos[scene_b.scene_id]
        
        # Validate transition
        valid, msg = validate_scene_transition(scene_a, scene_b, video_a, video_b)
        if not valid:
            issues.append(f"Transition {scene_a.scene_id}→{scene_b.scene_id}: {msg}")
    
    return len(issues) == 0, issues
```

---

## Summary

**Keep for Guardrails**:
- `visual_continuity` (essential for consistency checks)
- `camera_consistency` (essential for match cuts)
- `scene_flow` (essential for transition validation)
- `characters.primary_character_id` (essential for character validation)
- `duration` (essential for timing validation)

**Remove**:
- `cinematography` details (already in prompts, can't validate camera settings)
- Subjective `audio_details` (voice characteristics, mood - hard to validate)

This gives you **automated quality control** after generation without bloating the generation inputs.
