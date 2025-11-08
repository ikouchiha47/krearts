# Cinematic Technique to Generation Method Mapping

## The Real Problem

This isn't a cost-benefit optimization - it's a **creative technique recognition problem**.

When a screenplay describes:
- "Graphical match cut"
- "Smash cut"
- "Jump cut"
- "Crossfade"
- "Whip pan transition"

**How do we know which generation method achieves that technique?**

## Cinematic Editing Techniques Taxonomy

### 1. Match Cut
**Definition**: Cut between two shots that are compositionally similar

**Types**:
- **Graphical Match Cut**: Visual elements align (your headphone example)
- **Match on Action**: Cut during movement
- **Eyeline Match**: Character looks, cut to what they see

**Generation Method**:
```
Method: First + Last Frame (Veo interpolation)
Why: Need precise control over composition in both frames
Process:
  1. Generate first frame with specific element position
  2. Generate last frame with same element in same position
  3. Veo interpolates the transition
  4. OR: Generate two separate videos, cut in post
```

**Example from your screenplay**:
```
S1 (Office) → S2 (Gym)
Technique: Graphical match cut on headphone earcup position
Method: 
  - Option A: Generate S1 video + S2 video, ensure earcup position matches, cut in post
  - Option B: Generate S1 last frame + S2 first frame as identical compositions, 
              then generate each video separately
```

### 2. Jump Cut
**Definition**: Abrupt cut within same scene/subject, showing time passage

**Generation Method**:
```
Method: Multiple image generations OR single video trimmed
Why: Jump cuts are about discontinuity, not smooth motion
Process:
  1. Generate image of subject in position A
  2. Generate image of subject in position B (same framing)
  3. Hard cut between them (no transition)
```

**When to use**:
- Showing time passage
- Rapid montage sequences
- Energetic pacing

### 3. Smash Cut
**Definition**: Jarring cut between contrasting scenes (often to black/white)

**Generation Method**:
```
Method: Two separate video generations + hard cut in post
Why: The contrast IS the technique - no interpolation needed
Process:
  1. Generate scene A video
  2. Generate scene B video (or black frame)
  3. Hard cut with no transition
```

**Example from your screenplay**:
```
S4C (Gym) → Black → S5 (Product)
Technique: Smash cut to black
Method: 
  - Generate S4C video
  - Insert 0.5s black frame (no generation needed)
  - Generate S5 video
  - Hard cut in post
```

### 4. Crossfade/Dissolve
**Definition**: Gradual transition where one shot fades into another

**Generation Method**:
```
Method: Two separate generations + ffmpeg crossfade
Why: Crossfade is a post-production effect, not camera movement
Process:
  1. Generate video/image A
  2. Generate video/image B
  3. Apply crossfade in post:
     ffmpeg -i A.mp4 -i B.mp4 \
       -filter_complex "xfade=transition=fade:duration=0.5:offset=1.5" \
       output.mp4
```

**When to use**:
- Dreamy/nostalgic transitions
- Time passage
- Soft scene changes

### 5. Whip Pan Transition
**Definition**: Fast camera pan that blurs, used to transition between scenes

**Generation Method**:
```
Method: 
  - Option A: Single Veo generation with whip pan in prompt
  - Option B: Two videos + motion blur transition in post
Why: Veo can generate camera movement, but may need post-production enhancement
Process:
  1. Generate scene A with "camera whip pans right at end"
  2. Generate scene B with "camera whip pans in from left at start"
  3. Cut at peak blur point
```

### 6. L-Cut / J-Cut
**Definition**: Audio from next/previous scene bleeds over the cut

**Generation Method**:
```
Method: Separate video generations + audio editing in post
Why: This is purely an audio editing technique
Process:
  1. Generate both videos with audio
  2. In post, extend audio from scene B to overlap scene A's end (L-cut)
  3. Or extend audio from scene A into scene B's start (J-cut)
```

### 7. Montage (Rapid Cuts)
**Definition**: Series of short shots edited together

**Generation Method**:
```
Method: Depends on shot duration and motion

Decision Tree:
  Each shot < 2s AND static/minimal motion?
    → Generate images, stitch with ffmpeg
  
  Each shot < 2s BUT has motion?
    → Generate 4s videos, trim each to needed duration
  
  Each shot >= 4s?
    → Generate videos at exact duration
```

**Example from your screenplay**:
```
S4: Rapid Benefits Montage
  - S4A (1.3s, static typing): Image generation + stitch
  - S4B (1.3s, running feet): 4s video generation + trim (motion required)
  - S4C (1.4s, static sweat wipe): Image generation + stitch
```

## The Knowledge Base Approach

You're right - this should be a **knowledge base lookup**, not an algorithm.

### Structure:

```yaml
cinematic_techniques:
  
  match_cut:
    description: "Cut between compositionally similar shots"
    subtypes:
      - graphical_match_cut
      - match_on_action
      - eyeline_match
    
    generation_strategy:
      method: "separate_videos_with_composition_control"
      steps:
        - "Generate Scene A with specific element position documented"
        - "Generate Scene B with same element in same position"
        - "Cut in post-production at matching frame"
      
      alternative_method: "first_last_frame_interpolation"
      alternative_steps:
        - "Generate last frame of Scene A"
        - "Generate first frame of Scene B (matching composition)"
        - "Use frames as keyframes for video generation"
    
    veo_capabilities:
      - "Veo can maintain composition if using first+last frame"
      - "Reference images help maintain subject consistency"
    
    post_production_required: true
    
    examples:
      - scene_transition: "S1_Office → S2_Gym"
        matching_element: "Headphone earcup position"
        technique_note: "Earcup stays in bottom-right quadrant across cut"

  smash_cut:
    description: "Abrupt cut between contrasting scenes"
    
    generation_strategy:
      method: "separate_videos_hard_cut"
      steps:
        - "Generate Scene A"
        - "Generate Scene B (or use black/white frame)"
        - "Hard cut with no transition in post"
      
    veo_capabilities:
      - "No special Veo features needed"
      - "The contrast is created in editing, not generation"
    
    post_production_required: true
    
    examples:
      - scene_transition: "S4C_Gym → Black → S5_Product"
        technique_note: "Jarring energy shift, no transition"

  jump_cut:
    description: "Abrupt cut within same scene showing time passage"
    
    generation_strategy:
      method: "multiple_images_or_trimmed_video"
      steps:
        - "Generate image/video of subject in position A"
        - "Generate image/video of subject in position B (same framing)"
        - "Hard cut between them"
      
      decision_criteria:
        - "If minimal motion: use images"
        - "If subject movement: use trimmed video"
    
    veo_capabilities:
      - "Jump cuts are about discontinuity"
      - "Don't use Veo interpolation - defeats the purpose"
    
    post_production_required: true

  crossfade:
    description: "Gradual transition where shots blend"
    
    generation_strategy:
      method: "separate_generations_plus_ffmpeg"
      steps:
        - "Generate Scene A"
        - "Generate Scene B"
        - "Apply crossfade in post with ffmpeg"
      
      ffmpeg_command: |
        ffmpeg -i A.mp4 -i B.mp4 \
          -filter_complex "xfade=transition=fade:duration=0.5:offset=1.5" \
          output.mp4
    
    veo_capabilities:
      - "Crossfade is post-production effect"
      - "Veo doesn't need to know about the transition"
    
    post_production_required: true

  whip_pan:
    description: "Fast camera pan creating motion blur transition"
    
    generation_strategy:
      method: "veo_with_camera_movement_or_post"
      steps:
        - "Option A: Generate with 'camera whip pans right' in prompt"
        - "Option B: Generate two videos, add motion blur in post"
      
    veo_capabilities:
      - "Veo can generate camera pans"
      - "May need post-production enhancement for blur"
    
    veo_prompt_keywords:
      - "whip pan"
      - "fast pan"
      - "camera swish"
    
    post_production_required: "optional"

  montage:
    description: "Series of short shots edited together"
    
    generation_strategy:
      method: "hybrid_based_on_shot_characteristics"
      decision_tree:
        - condition: "shot_duration < 2s AND motion_minimal"
          method: "image_generation_stitch"
        - condition: "shot_duration < 2s AND motion_significant"
          method: "video_generation_trim"
        - condition: "shot_duration >= 4s"
          method: "video_generation_exact"
    
    veo_capabilities:
      - "Each shot is separate generation"
      - "Montage is created in editing"
    
    post_production_required: true
```

## The Real Answer to Your Question

**"How do we know?"**

**Answer**: We need a **cinematic technique knowledge base** that maps:

1. **Technique name** (match cut, smash cut, etc.)
2. **What it achieves creatively** (visual continuity, jarring contrast, etc.)
3. **How to generate it** (separate videos, first+last frame, images, etc.)
4. **What Veo can/can't do** (interpolation, camera movement, etc.)
5. **What requires post-production** (crossfades, hard cuts, etc.)

This isn't something you calculate - it's something you **look up** based on the editing technique being used.

## Implementation Approach

### Option 1: Rule-Based Lookup
```python
TECHNIQUE_REGISTRY = {
    "graphical_match_cut": {
        "generation_method": "separate_videos_with_composition_control",
        "requires_keyframes": True,
        "requires_post": True,
        "veo_features": ["first_last_frame", "reference_images"]
    },
    "smash_cut": {
        "generation_method": "separate_videos_hard_cut",
        "requires_keyframes": False,
        "requires_post": True,
        "veo_features": []
    },
    # ... etc
}

def determine_generation_method(transition_type):
    return TECHNIQUE_REGISTRY.get(transition_type)
```

### Option 2: LLM with Knowledge Base (RAG)
```python
# Use an LLM to analyze the screenplay and identify techniques
prompt = f"""
Given this scene transition description:
"{scene.transition_description}"

Identify the cinematic technique being used and recommend the generation method.

Available techniques: {list(TECHNIQUE_REGISTRY.keys())}
"""

# LLM returns: "graphical_match_cut"
# Then lookup in knowledge base
```

### Option 3: Train a Classifier (Overkill?)
- Probably not worth it for this
- Rule-based + LLM is sufficient

## What You Actually Need

A **cinematic editing techniques knowledge base** that documents:

1. **Common editing techniques** (50-100 techniques)
2. **How each technique is achieved** in post-production
3. **What Veo can generate** vs what needs editing
4. **Prompt patterns** for each technique
5. **Examples** from real films/ads

This becomes your **source of truth** for mapping creative intent to technical execution.

---

**TL;DR**: You're right - this is a creative problem, not an optimization problem. You need a knowledge base of cinematic techniques mapped to generation methods, not an algorithm calculating motion scores. The technique name (match cut, smash cut, etc.) tells you exactly what to do.
