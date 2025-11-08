# Keyframe Generation Logic

## The Problem

We don't need to generate keyframes for every scene. Keyframes are only needed for specific techniques.

## When to Generate Keyframes

### Case 1: Simple Text-to-Video (NO keyframes)
```
Scene: "A man typing at a desk"
Method: text_to_video
Keyframes needed: NONE
```

Just generate the video directly from the prompt. No images needed.

### Case 2: Match Cut Transition (YES keyframes)
```
Scene i: "Office scene with headphones in bottom-right"
Scene i+1: "Gym scene with headphones in bottom-right"
Transition: match_cut_graphic
Keyframes needed: 
  - scene[i].last_frame (headphone position)
  - scene[i+1].first_frame (matching headphone position)
```

Generate:
1. Scene i video (text-to-video or with last_frame)
2. Scene i last frame image (Imagen)
3. Scene i+1 first frame image (Imagen) - matches scene i composition
4. Scene i+1 video (using first_frame as starting point)

### Case 3: First/Last Frame Interpolation (YES keyframes)
```
Scene: "Camera rotates around product"
Method: first_last_frame_interpolation
Keyframes needed:
  - first_frame (product front view)
  - last_frame (product rotated 180°)
```

Generate:
1. First frame image (Imagen)
2. Last frame image (Imagen)
3. Video interpolating between frames (Veo with first+last frame)

### Case 4: Transition Frame (MAYBE keyframes)
```
Scene i: "Bright office (day)"
Scene i+1: "Dark gym (night)"
Problem: Abrupt lighting change
Keyframes needed:
  - scene[i].last_frame (bright office)
  - transition_frame (intermediate lighting)
  - scene[i+1].first_frame (dark gym)
```

Generate:
1. Scene i video
2. Scene i last frame (Imagen)
3. Transition frame (Imagen) - bridges lighting
4. Scene i+1 first frame (Imagen)
5. Scene i+1 video

## The Keyframe Chain

For transitions, keyframes form a chain:

```
Scene 1 (text-to-video)
  ↓
Scene 1 last_frame (Imagen) ← Only if transition to Scene 2
  ↓
[Optional: transition_frame (Imagen)]
  ↓
Scene 2 first_frame (Imagen) ← Matches Scene 1 last_frame composition
  ↓
Scene 2 (first_frame → video)
  ↓
Scene 2 last_frame (Imagen) ← Only if transition to Scene 3
  ↓
...
```

## Decision Tree

```python
def needs_keyframes(scene, next_scene):
    """Determine if scene needs keyframe generation"""
    
    # Check if scene uses interpolation
    if scene.generation_strategy.generation_method == "first_last_frame_interpolation":
        return {
            "needs_keyframes": True,
            "first_frame": True,
            "last_frame": True,
            "reason": "Interpolation requires both frames"
        }
    
    # Check if there's a transition to next scene
    if next_scene and scene.scene_flow:
        transition = scene.scene_flow.transition_technique
        
        if transition in ["match_cut_graphic", "match_cut_action"]:
            return {
                "needs_keyframes": True,
                "first_frame": False,  # Not needed for this scene
                "last_frame": True,    # Needed to match next scene
                "reason": f"Match cut to next scene requires last frame"
            }
        
        # Check if lighting/environment changes abruptly
        if needs_transition_frame(scene, next_scene):
            return {
                "needs_keyframes": True,
                "first_frame": False,
                "last_frame": True,
                "transition_frame": True,
                "reason": "Abrupt lighting change requires transition frame"
            }
    
    # Default: no keyframes needed
    return {
        "needs_keyframes": False,
        "first_frame": False,
        "last_frame": False,
        "reason": "Simple text-to-video generation"
    }

def needs_transition_frame(scene_i, scene_i_plus_1):
    """Check if transition frame is needed between scenes"""
    
    # Compare lighting
    lighting_i = scene_i.visual_continuity.lighting
    lighting_i_plus_1 = scene_i_plus_1.visual_continuity.lighting
    
    if lighting_i and lighting_i_plus_1:
        # Check for abrupt changes
        if ("day" in lighting_i and "night" in lighting_i_plus_1) or \
           ("bright" in lighting_i and "dark" in lighting_i_plus_1):
            return True
    
    # Compare color palettes
    palette_i = scene_i.visual_continuity.color_palette
    palette_i_plus_1 = scene_i_plus_1.visual_continuity.color_palette
    
    if palette_i and palette_i_plus_1:
        # Check for dramatic color shifts
        if ("warm" in palette_i and "cool" in palette_i_plus_1) or \
           ("bright" in palette_i and "muted" in palette_i_plus_1):
            return True
    
    return False
```

## Example Screenplay with Keyframe Decisions

```python
scenes = [
    {
        "scene_id": "S1_Office",
        "duration": 2.0,
        "generation_method": "text_to_video",
        "needs_keyframes": False,  # Simple scene
        "transition_to_next": "match_cut_graphic"
    },
    {
        "scene_id": "S2_Gym",
        "duration": 3.0,
        "generation_method": "first_last_frame_interpolation",
        "needs_keyframes": True,  # Interpolation + match cut from S1
        "first_frame": True,  # Matches S1 last frame
        "last_frame": True,   # For interpolation + match cut to S3
        "transition_to_next": "match_cut_graphic"
    },
    {
        "scene_id": "S3_Run",
        "duration": 3.0,
        "generation_method": "text_to_video",
        "needs_keyframes": True,  # Match cut from S2
        "first_frame": True,  # Matches S2 last frame
        "last_frame": False,  # No transition to next
        "transition_to_next": None
    }
]
```

## Generation Order

1. **Analyze all scenes** to determine keyframe needs
2. **Generate keyframes first** (all Imagen generations)
3. **Generate videos** using keyframes where needed
4. **Edit together** in post-production

```python
# Step 1: Determine keyframe needs
keyframe_manifest = []
for i, scene in enumerate(scenes):
    next_scene = scenes[i+1] if i < len(scenes)-1 else None
    keyframe_info = needs_keyframes(scene, next_scene)
    keyframe_manifest.append(keyframe_info)

# Step 2: Generate all keyframes
for i, scene in enumerate(scenes):
    info = keyframe_manifest[i]
    
    if info["first_frame"]:
        generate_imagen(scene.keyframe_description.first_frame_prompt)
    
    if info["last_frame"]:
        generate_imagen(scene.keyframe_description.last_frame_prompt)
    
    if info.get("transition_frame"):
        generate_imagen(scene.keyframe_description.transition_frame_prompt)

# Step 3: Generate videos
for i, scene in enumerate(scenes):
    info = keyframe_manifest[i]
    
    if scene.generation_method == "first_last_frame_interpolation":
        generate_veo_with_frames(
            prompt=scene.video_prompt,
            first_frame=scene.first_frame_image,
            last_frame=scene.last_frame_image
        )
    elif info["first_frame"]:
        generate_veo_with_first_frame(
            prompt=scene.video_prompt,
            first_frame=scene.first_frame_image
        )
    else:
        generate_veo_text_to_video(
            prompt=scene.video_prompt
        )
```

## Summary

- **Most scenes**: Just `text_to_video`, no keyframes
- **Match cuts**: Generate last_frame of scene i, first_frame of scene i+1
- **Interpolation**: Generate both first_frame and last_frame for same scene
- **Transition frames**: Only when lighting/environment changes abruptly
- **Keyframes form a chain** across scenes for smooth transitions
