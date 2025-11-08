# Final Video Generation Pipeline

## Overview

This is the practical, step-by-step pipeline for generating videos from screenplay to final output.

## Pipeline Steps

```
1. Generate Screenplay
   ↓
2. Extract Audio Segments
   ↓
3. Generate Character Reference Images
   ↓
4. Generate Moodboard/Collage
   ↓
5. Generate Scene Images (with transition frames)
   ↓
6. Generate Videos from Images
   ↓
7. Apply Effects (with video analysis if needed)
   ↓
8. Final Assembly
```

---

## Step 1: Generate Screenplay

**Input**: User request, product images, character descriptions

**Output**: Structured screenplay with:
- Scene descriptions
- Transition techniques
- Approximate durations
- Character assignments
- Audio requirements

**Tools**: ScriptWriter + Enhancer agents

**Example Output**:
```json
{
  "scenes": [
    {
      "scene_id": "S1_Hook",
      "technique": "match_cut_graphic",
      "duration": 2.0,
      "has_audio": true,
      "voiceover": "Noise. Distraction...",
      "characters": ["CHAR_001"]
    }
  ]
}
```

---

## Step 2: Extract Audio Segments

**Purpose**: Generate audio first, determine actual timing

**Process**:
```python
# 2.1: Generate full voiceover
full_audio = elevenlabs.generate(
    text=combine_all_voiceover(screenplay),
    voice="confident_male"
)

# 2.2: Transcribe with timestamps
transcript = whisper.transcribe(full_audio, word_timestamps=True)

# 2.3: Detect audio segments
segments = detect_audio_segments(transcript, screenplay)
# Returns: [
#   {"scene_id": "S1", "start": 0.0, "end": 2.1, "has_audio": True},
#   {"scene_id": "S2", "start": 2.1, "end": 5.3, "has_audio": True},
#   {"scene_id": "S3", "start": 5.3, "end": 8.1, "has_audio": False}  # No dialogue
# ]

# 2.4: Segment audio file
audio_clips = {}
for segment in segments:
    if segment["has_audio"]:
        audio_clips[segment["scene_id"]] = extract_audio_clip(
            full_audio, 
            segment["start"], 
            segment["end"]
        )

# 2.5: Update scene durations
for scene in screenplay.scenes:
    segment = find_segment(segments, scene.scene_id)
    scene.duration = segment["end"] - segment["start"]
    scene.timing = f"{segment['start']:.1f}s-{segment['end']:.1f}s"
```

**Output**: 
- Audio clips per scene
- Updated scene durations (actual, not approximate)

---

## Step 3: Generate Character Reference Images

**Purpose**: Create consistent character appearances across all scenes

**Process**:
```python
character_references = {}

for character in screenplay.character_description:
    # Generate 3 reference angles
    references = []
    
    # Front view
    front = imagen.generate(
        prompt=f"""
        Studio portrait photograph of {character.physical_appearance}.
        {character.style}. Neutral expression, looking at camera.
        Clean white background, professional studio lighting.
        Front view, centered, photorealistic, high detail.
        Aspect ratio: 1:1.
        """,
        aspect_ratio="1:1"
    )
    references.append(("front", front))
    
    # Side profile
    side = imagen.generate(
        prompt=f"""
        Studio portrait photograph of {character.physical_appearance}.
        {character.style}. Neutral expression, side profile.
        Clean white background, professional studio lighting.
        Side view, centered, photorealistic, high detail.
        Aspect ratio: 1:1.
        """,
        aspect_ratio="1:1"
    )
    references.append(("side", side))
    
    # Full body
    full = imagen.generate(
        prompt=f"""
        Full body studio photograph of {character.physical_appearance}.
        {character.style}. Standing naturally, neutral pose.
        Clean white background, professional studio lighting.
        Full body view, centered, photorealistic, high detail.
        Aspect ratio: 3:4.
        """,
        aspect_ratio="3:4"
    )
    references.append(("full", full))
    
    character_references[character.id] = references
```

**Output**: Character reference images (front, side, full body) for each character

---

## Step 4: Generate Moodboard/Collage

**Purpose**: Visual reference showing character in different scenarios

**Process**:
```python
# Generate scenario variations for each character
moodboard_images = {}

for character in screenplay.character_description:
    scenarios = []
    
    # Extract unique environments from scenes
    environments = extract_environments(screenplay, character.id)
    # e.g., ["modern office", "industrial gym", "city park"]
    
    for env in environments:
        scenario_image = imagen.generate(
            prompt=f"""
            {character.physical_appearance} in {env}.
            {character.style}. Natural pose and expression.
            {env} environment with appropriate lighting.
            Medium shot, photorealistic, cinematic.
            Aspect ratio: {screenplay.video_config.aspect_ratio}.
            """,
            aspect_ratio=screenplay.video_config.aspect_ratio
        )
        scenarios.append((env, scenario_image))
    
    # Create collage (optional)
    collage = create_image_collage(scenarios, layout="grid")
    moodboard_images[character.id] = {
        "scenarios": scenarios,
        "collage": collage
    }
```

**Output**: Moodboard showing character in different environments

---

## Step 5: Generate Scene Images (with Transition Frames)

**Purpose**: Generate keyframe images for each scene, including transition frames for scenic consistency

**Process**:
```python
scene_images = {}

for i, scene in enumerate(screenplay.scenes):
    images = {}
    
    # 5.1: Generate first frame
    first_frame = imagen.generate(
        prompt=scene.keyframe_description.first_frame_prompt,
        aspect_ratio=screenplay.video_config.aspect_ratio
    )
    images["first_frame"] = first_frame
    
    # 5.2: Generate last frame (if needed for interpolation)
    if scene.generation_strategy.generation_method == "first_last_frame_interpolation":
        last_frame = imagen.generate(
            prompt=scene.keyframe_description.last_frame_prompt,
            aspect_ratio=screenplay.video_config.aspect_ratio
        )
        images["last_frame"] = last_frame
    
    # 5.3: Generate transition frame (if needed)
    if i < len(screenplay.scenes) - 1:
        next_scene = screenplay.scenes[i + 1]
        
        # Check if transition frame is needed
        if needs_transition_frame(scene, next_scene):
            transition_frame = imagen.generate(
                prompt=generate_transition_prompt(scene, next_scene),
                aspect_ratio=screenplay.video_config.aspect_ratio
            )
            images["transition_frame"] = transition_frame
    
    scene_images[scene.scene_id] = images

def needs_transition_frame(scene1, scene2):
    """
    Determine if a transition frame is needed between scenes.
    
    Needed when:
    - Abrupt lighting change (day → night)
    - Environment change (indoor → outdoor)
    - Color palette shift (warm → cool)
    """
    # Check lighting consistency
    if scene1.visual_continuity.lighting != scene2.visual_continuity.lighting:
        return True
    
    # Check environment change
    if scene1.context != scene2.context:
        return True
    
    return False

def generate_transition_prompt(scene1, scene2):
    """
    Generate prompt for transition frame that bridges two scenes.
    """
    return f"""
    Transition frame bridging {scene1.scene_id} to {scene2.scene_id}.
    
    Visual elements from Scene 1:
    - {scene1.visual_continuity.consistent_element}
    - {scene1.visual_continuity.color_palette}
    
    Transitioning to Scene 2:
    - {scene2.visual_continuity.color_palette}
    - {scene2.context}
    
    Blend lighting from {scene1.visual_continuity.lighting} to {scene2.visual_continuity.lighting}.
    Maintain visual continuity while shifting environment.
    Aspect ratio: {screenplay.video_config.aspect_ratio}.
    """
```

**Output**: First frame, last frame (if needed), transition frame (if needed) for each scene

---

## Step 6: Generate Videos from Images

**Purpose**: Convert images to videos using appropriate method

**Process**:
```python
scene_videos = {}

for scene in screenplay.scenes:
    method = scene.generation_strategy.generation_method
    
    if method == "image_stitch_ffmpeg":
        # 6.1: Image stitching (for montages, static shots)
        video = stitch_images_to_video(
            images=scene_images[scene.scene_id],
            duration=scene.duration,
            transition="crossfade"
        )
    
    elif method == "image_to_video":
        # 6.2: Animate single image with Veo
        video = veo.generate_video(
            model="veo-3.1-generate-preview",
            image=scene_images[scene.scene_id]["first_frame"],
            prompt=scene.video_prompt,
            config={
                "duration_seconds": round(scene.duration),
                "aspect_ratio": screenplay.video_config.aspect_ratio,
                "negative_prompt": scene.negative_prompt
            }
        )
    
    elif method == "first_last_frame_interpolation":
        # 6.3: Interpolate between first and last frame
        video = veo.generate_video(
            model="veo-3.1-generate-preview",
            image=scene_images[scene.scene_id]["first_frame"],
            config={
                "duration_seconds": round(scene.duration),
                "aspect_ratio": screenplay.video_config.aspect_ratio,
                "last_frame": scene_images[scene.scene_id]["last_frame"],
                "negative_prompt": scene.negative_prompt
            }
        )
    
    elif method == "text_to_video":
        # 6.4: Pure text-to-video (for action scenes)
        video = veo.generate_video(
            model="veo-3.1-generate-preview",
            prompt=scene.video_prompt,
            config={
                "duration_seconds": round(scene.duration),
                "aspect_ratio": screenplay.video_config.aspect_ratio,
                "negative_prompt": scene.negative_prompt,
                "reference_images": get_character_references(scene)
            }
        )
    
    # Trim if needed
    if scene.generation_strategy.duration_trim:
        video = trim_video(
            video, 
            duration=scene.generation_strategy.duration_trim
        )
    
    scene_videos[scene.scene_id] = video
```

**Output**: Video clip for each scene

---

## Step 7: Apply Effects (with Video Analysis if Needed)

**Purpose**: Apply post-production effects, analyze videos for optimal cut points

**Process**:
```python
processed_videos = {}

for scene in screenplay.scenes:
    video = scene_videos[scene.scene_id]
    
    # 7.1: Analyze video (if needed)
    if scene.scene_type == "action" or scene.technique == "match_cut_action":
        analysis = analyze_video(video)
        # Returns: {
        #   "action_peaks": [0.5, 1.2, 1.8],  # Timestamps of action peaks
        #   "scene_changes": [1.5],
        #   "motion_intensity": [0.2, 0.8, 0.9, 0.3]
        # }
        
        # Find optimal cut point
        if scene.technique == "match_cut_action":
            cut_point = find_action_peak(analysis, target_time=scene.duration)
            video = trim_to_action_peak(video, cut_point)
    
    # 7.2: Apply color grading
    if scene.visual_continuity.color_palette:
        video = apply_color_grade(video, scene.visual_continuity.color_palette)
    
    # 7.3: Add audio
    if scene.scene_id in audio_clips:
        video = add_audio_track(video, audio_clips[scene.scene_id])
    
    processed_videos[scene.scene_id] = video
```

**Output**: Processed video clips with effects and audio

---

## Step 8: Final Assembly

**Purpose**: Combine all scenes into final video

**Process**:
```python
def assemble_final_video(screenplay, processed_videos):
    clips = []
    
    for scene in screenplay.scenes:
        clip = processed_videos[scene.scene_id]
        
        # Apply transition to next scene
        if scene.scene_flow and scene.scene_flow.transition_technique:
            transition = scene.scene_flow.transition_technique
            
            if transition == "match_cut_graphic" or transition == "match_cut_action":
                # Hard cut (no transition effect)
                clips.append(clip)
            
            elif transition == "flow_cut":
                # Crossfade
                clips.append((clip, "crossfade", 0.3))
            
            elif transition == "smash_cut":
                # Hard cut with black frame
                clips.append(clip)
                clips.append(create_black_frame(0.1))
            
            elif transition == "jump_cut":
                # Hard cut, no transition
                clips.append(clip)
            
            else:
                # Default: hard cut
                clips.append(clip)
        else:
            clips.append(clip)
    
    # Concatenate all clips
    final_video = concatenate_clips(clips)
    
    # Add background music (if needed)
    if screenplay.video_config.needs_background_music:
        final_video = add_background_music(
            final_video,
            music_description=screenplay.video_config.music_description
        )
    
    # Export
    final_video.write_videofile(
        "output/final_video.mp4",
        codec="libx264",
        audio_codec="aac",
        fps=24
    )
    
    return final_video
```

**Output**: Final assembled video

---

## Decision Matrix: When to Use Each Method

### Image Stitching (ffmpeg)
- **When**: Duration < 2s, minimal motion, montages
- **Examples**: Jump cut montage, product showcase, rapid identity swap
- **Pros**: Fast, deterministic, cheap
- **Cons**: Limited motion, feels static

### Image-to-Video (Veo)
- **When**: Single image needs animation, 2-4s duration
- **Examples**: Establishing shots, slow pans, product reveals
- **Pros**: Natural motion, good quality
- **Cons**: Limited control over motion

### First+Last Frame Interpolation (Veo)
- **When**: Need precise control over start/end state, match cuts
- **Examples**: Match cuts, controlled transitions, camera movements
- **Pros**: Precise control, smooth interpolation
- **Cons**: Requires careful keyframe generation

### Text-to-Video (Veo)
- **When**: Complex action, dialogue, character interaction
- **Examples**: Action scenes, dialogue scenes, dynamic movement
- **Pros**: Most flexible, natural motion
- **Cons**: Less control, longer generation time

---

## Summary

This pipeline is **pragmatic and iterative**:

1. ✅ **Audio-first** for timing accuracy
2. ✅ **Character references** for consistency
3. ✅ **Moodboard** for visual planning
4. ✅ **Transition frames** for scenic consistency
5. ✅ **Hybrid generation** (images + videos)
6. ✅ **Video analysis** for optimal cuts (when needed)
7. ✅ **Flexible assembly** based on transition techniques

It's **crude but effective** - start here, refine based on results.
