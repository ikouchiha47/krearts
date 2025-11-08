# Simplified Screenplay Extraction Guide

## What You Actually Need

The current output is too complex. Here's what you need for each generation step:

---

## Step 0: Character Generation

**Extract from screenplay**:
```python
{
  "characters": [
    {
      "id": 1,
      "name": "Liam",
      "description": "32-year-old man, Black, short black hair, athletic build",
      "style_variations": {
        "office": "Crisp white shirt, tailored trousers",
        "gym": "Dark gray fitted athletic wear",
        "casual": "Dark athletic wear"
      }
    }
  ]
}
```

**Use for**: Generating character reference images (front, side, full body)

---

## Step 1: Image Generation (Nano Banana / Imagen)

**Extract from each scene**:
```python
{
  "scene_id": "S1_Office_Focus",
  "images_needed": {
    "first_frame": {
      "prompt": "Cinematic close-up shot, 50mm lens, shallow depth of field (f/2.0). Liam (32, Black, white shirt), looking stressed, taps a pen impatiently. He is surrounded by chaotic, noisy, cool-toned modern office environment, slightly blurred. Photorealistic, 4K. Aspect ratio: 16:9.",
      "aspect_ratio": "16:9",
      "character_refs": [1]  // Use character ID 1 references
    },
    "last_frame": {
      "prompt": "Extreme close-up, 50mm lens. Liam (32, Black, focused expression) wears matte black VibeFlow over-ear headphones. The bright white rectangular screen of his laptop fills the central-right quadrant. High-contrast, cool lighting. Photorealistic, 4K. Aspect ratio: 16:9.",
      "aspect_ratio": "16:9",
      "character_refs": [1]
    }
  }
}
```

**Use for**: Generating keyframe images with Imagen/Nano Banana

---

## Step 2: Video Generation (Veo)

**Extract from each scene**:
```python
{
  "scene_id": "S1_Office_Focus",
  "video_generation": {
    "method": "first_last_frame_interpolation",  // or "text_to_video", "image_to_video"
    "prompt": "Gradual dolly-in close-up shot, 50mm lens with shallow depth of field (f/2.0). Liam (32, Black, white shirt) initially appears stressed, tapping a pen impatiently, surrounded by a distracting, noisy modern office. At 2.5 seconds, he smoothly places matte black VibeFlow over-ear headphones over his ears. The camera becomes static, focusing on his now calm, determined expression. The bright white laptop screen fills the central-right quadrant, dominating the final frame for a graphical match cut. Office environment is cool-toned and chaotic, contrasting with Liam's sharp focus. Cinematic, high-contrast commercial aesthetic.",
    "negative_prompt": "cartoon, low quality, distortion, blurry screen, visible wires, unrealistic reflections",
    "duration": 5.0,
    "aspect_ratio": "16:9",
    "first_frame_image": "S1_first_frame.png",  // Generated in step 1
    "last_frame_image": "S1_last_frame.png",    // Generated in step 1
    "character_refs": [1],  // Use character reference images
    "audio_handling": "ambient_only"  // or "silent", "veo_native"
  }
}
```

**Use for**: Generating videos with Veo

---

## Step 3: Post-Production

**Extract from each scene**:
```python
{
  "scene_id": "S1_Office_Focus",
  "post_production": {
    "trim_to": null,  // or 3.0 if needs trimming
    "transition_to_next": "match_cut_graphic",  // or "smash_cut", "flow_cut", etc.
    "effects": [
      {"type": "text_overlay", "text": "NOISE IS THE ENEMY.", "timing": "0-1s"},
      {"type": "text_overlay", "text": "Silence is power.", "timing": "3-5s"}
    ],
    "audio_clip": "S1_audio.mp3"  // Pre-generated audio segment
  }
}
```

**Use for**: Final editing and assembly

---

## Simplified Extraction Function

```python
def extract_for_generation(screenplay_output):
    """
    Extract only what's needed for generation from complex screenplay output.
    """
    
    # Step 0: Extract characters
    characters = []
    for char in screenplay_output.get("character_description", []):
        characters.append({
            "id": char["id"],
            "name": extract_name(char["physical_appearance"]),
            "description": char["physical_appearance"],
            "style_variations": parse_style_variations(char["style"])
        })
    
    # Step 1 & 2: Extract scene generation data
    scenes = []
    for scene in screenplay_output.get("scenes", []):
        scene_data = {
            "scene_id": scene["scene_id"],
            "duration": scene["duration"],
            
            # Image generation
            "images_needed": extract_keyframes(scene),
            
            # Video generation
            "video_generation": {
                "method": scene.get("generation_strategy", {}).get("generation_method", "text_to_video"),
                "prompt": scene.get("video_prompt", ""),
                "negative_prompt": scene.get("negative_prompt", ""),
                "duration": scene["duration"],
                "aspect_ratio": screenplay_output["video_config"]["aspect_ratio"],
                "character_refs": extract_character_ids(scene),
                "audio_handling": scene.get("generation_strategy", {}).get("audio_handling", "ambient_only")
            },
            
            # Post-production
            "post_production": {
                "trim_to": scene.get("generation_strategy", {}).get("duration_trim"),
                "transition_to_next": scene.get("scene_flow", {}).get("transition_technique"),
                "effects": extract_effects(scene),
                "audio_clip": f"{scene['scene_id']}_audio.mp3"
            }
        }
        scenes.append(scene_data)
    
    return {
        "characters": characters,
        "scenes": scenes,
        "video_config": {
            "aspect_ratio": screenplay_output["video_config"]["aspect_ratio"],
            "total_duration": screenplay_output["video_config"]["total_duration"]
        }
    }

def extract_keyframes(scene):
    """Extract keyframe prompts from scene."""
    keyframes = scene.get("keyframe_description", {})
    
    images = {}
    
    if keyframes.get("first_frame_prompt"):
        images["first_frame"] = {
            "prompt": keyframes["first_frame_prompt"],
            "aspect_ratio": extract_aspect_ratio(scene),
            "character_refs": extract_character_ids(scene)
        }
    
    if keyframes.get("last_frame_prompt"):
        images["last_frame"] = {
            "prompt": keyframes["last_frame_prompt"],
            "aspect_ratio": extract_aspect_ratio(scene),
            "character_refs": extract_character_ids(scene)
        }
    
    if keyframes.get("transition_frame_prompt"):
        images["transition_frame"] = {
            "prompt": keyframes["transition_frame_prompt"],
            "aspect_ratio": extract_aspect_ratio(scene)
        }
    
    return images

def extract_character_ids(scene):
    """Extract character IDs from scene."""
    chars = scene.get("characters", {})
    if isinstance(chars, dict) and "primary_character_id" in chars:
        return [chars["primary_character_id"]]
    return []

def extract_effects(scene):
    """Extract post-production effects from scene."""
    effects = []
    
    # Extract text overlays from generation strategy notes
    notes = scene.get("generation_strategy", {}).get("post_production_notes", "")
    # Parse "Super: 'TEXT' (timing)" patterns
    import re
    super_pattern = r"Super: '([^']+)' \(([^)]+)\)"
    for match in re.finditer(super_pattern, notes):
        effects.append({
            "type": "text_overlay",
            "text": match.group(1),
            "timing": match.group(2)
        })
    
    return effects
```

---

## What to Remove from Output

**Remove these fields** (they're redundant or unused):
- `image_prompt` (always empty, use `keyframe_description` instead)
- `action_prompt` (redundant with `video_prompt`)
- `cinematography.camera_setup` (details are in the prompts already)
- `cinematography.camera_movement` (details are in the prompts already)
- `cinematography.camera_consistency` (only needed for match cuts, can be in prompt)
- `visual_continuity` (nice to have but not essential for generation)
- `audio_details` (too granular, audio is pre-generated)

**Keep these fields**:
- `scene_id`, `duration`, `timing`
- `keyframe_description.first_frame_prompt`
- `keyframe_description.last_frame_prompt`
- `video_prompt`
- `negative_prompt`
- `generation_strategy.generation_method`
- `generation_strategy.duration_trim`
- `generation_strategy.audio_handling`
- `scene_flow.transition_technique`
- `characters.primary_character_id`

---

## Simplified Output Schema

```json
{
  "characters": [
    {
      "id": 1,
      "name": "Liam",
      "description": "32-year-old man, Black, short black hair, athletic build",
      "style": "Office: white shirt. Gym: athletic wear."
    }
  ],
  "scenes": [
    {
      "scene_id": "S1_Office_Focus",
      "duration": 5.0,
      "images": {
        "first_frame": "Cinematic close-up shot...",
        "last_frame": "Extreme close-up..."
      },
      "video": {
        "method": "first_last_frame_interpolation",
        "prompt": "Gradual dolly-in close-up shot...",
        "negative_prompt": "cartoon, low quality...",
        "character_refs": [1],
        "audio": "ambient_only"
      },
      "post": {
        "trim_to": null,
        "transition": "match_cut_graphic",
        "effects": [
          {"type": "text", "text": "NOISE IS THE ENEMY.", "timing": "0-1s"}
        ]
      }
    }
  ]
}
```

This is **80% smaller** and contains only what you need for generation.
