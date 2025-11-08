# Hybrid Generation Strategy Examples

## Example 1: Headphone Versatility Morph Sequence

### Concept
Camera locked. Headphones stay in exact position. Character/environment morphs around them to show versatility.

### Execution Strategy: Image Sequence + Crossfade

#### Why Not Pure Veo?
- Veo generates continuous motion, not discrete morphs
- Morphing effect requires precise control over transformation
- Better achieved through image sequence with crossfade transitions

#### Generation Plan

**Total Duration**: 6 seconds  
**Method**: 6 Imagen generations + post-production crossfades  
**Frame Rate**: 1 image per second with 0.5s crossfade overlaps

---

### Frame 1: Office Professional (0-1s)

#### Imagen Prompt
```
Cinematic portrait photograph, camera locked at eye-level, centered composition. A 30-year-old Asian woman with shoulder-length black hair wearing matte black over-ear headphones. She wears a crisp white business shirt and navy blazer. Modern office environment with soft natural window light. The headphones are positioned EXACTLY centered in frame - earcups at precise horizontal alignment, headband vertical. Professional, focused expression. Shot on 50mm lens, f/2.8, photorealistic, 4K. Aspect ratio: 9:16.

CRITICAL: Document exact pixel coordinates of headphone earcup centers and headband position for subsequent frames.
```

**Metadata for Consistency**:
- Headphone earcup left: X=320px, Y=450px
- Headphone earcup right: X=720px, Y=450px
- Headband center: X=520px, Y=200px
- Camera: 50mm, f/2.8, eye-level, centered

---

### Frame 2: Gym Athlete (1-2s)

#### Imagen Prompt
```
Cinematic portrait photograph, IDENTICAL camera position and framing to previous frame. A 25-year-old Black man with short fade haircut wearing the SAME matte black over-ear headphones in EXACT same position. He wears a gray athletic tank top. Industrial gym environment with high-contrast moody lighting. Intense, focused expression with slight sweat. The headphones MUST be positioned at identical coordinates: earcups horizontally aligned, headband vertical center. Shot on 50mm lens, f/2.8, photorealistic, 4K. Aspect ratio: 9:16.

CRITICAL: Headphone position must match Frame 1 exactly - earcup centers at X=320/720px, Y=450px, headband at X=520px, Y=200px.
```

**Transition**: 0.5s crossfade from Frame 1 to Frame 2

---

### Frame 3: Runner in Nature (2-3s)

#### Imagen Prompt
```
Cinematic portrait photograph, IDENTICAL camera position and framing. A 28-year-old Hispanic woman with ponytail wearing the SAME matte black over-ear headphones in EXACT same position. She wears a bright athletic running jacket. Outdoor park environment with golden hour sunlight and blurred greenery. Joyful, energized expression. The headphones MUST be positioned at identical coordinates: earcups horizontally aligned, headband vertical center. Shot on 50mm lens, f/2.8, photorealistic, 4K. Aspect ratio: 9:16.

CRITICAL: Headphone position must match previous frames exactly.
```

**Transition**: 0.5s crossfade from Frame 2 to Frame 3

---

### Frame 4: Commuter on Train (3-4s)

#### Imagen Prompt
```
Cinematic portrait photograph, IDENTICAL camera position and framing. A 35-year-old Middle Eastern man with beard wearing the SAME matte black over-ear headphones in EXACT same position. He wears a casual denim jacket over hoodie. Subway train interior with motion-blurred windows showing city lights. Relaxed, contemplative expression. The headphones MUST be positioned at identical coordinates. Shot on 50mm lens, f/2.8, photorealistic, 4K. Aspect ratio: 9:16.

CRITICAL: Headphone position must match previous frames exactly.
```

**Transition**: 0.5s crossfade from Frame 3 to Frame 4

---

### Frame 5: Student Studying (4-5s)

#### Imagen Prompt
```
Cinematic portrait photograph, IDENTICAL camera position and framing. A 22-year-old South Asian woman with glasses and long dark hair wearing the SAME matte black over-ear headphones in EXACT same position. She wears a cozy oversized sweater. Cozy library environment with warm lamp lighting and blurred bookshelves. Concentrated, peaceful expression. The headphones MUST be positioned at identical coordinates. Shot on 50mm lens, f/2.8, photorealistic, 4K. Aspect ratio: 9:16.

CRITICAL: Headphone position must match previous frames exactly.
```

**Transition**: 0.5s crossfade from Frame 4 to Frame 5

---

### Frame 6: Creative at Home Studio (5-6s)

#### Imagen Prompt
```
Cinematic portrait photograph, IDENTICAL camera position and framing. A 30-year-old White man with messy artistic hair wearing the SAME matte black over-ear headphones in EXACT same position. He wears a vintage band t-shirt. Home music studio environment with colorful LED lights and audio equipment. Inspired, creative expression. The headphones MUST be positioned at identical coordinates. Shot on 50mm lens, f/2.8, photorealistic, 4K. Aspect ratio: 9:16.

CRITICAL: Headphone position must match previous frames exactly.
```

**Transition**: 0.5s crossfade from Frame 5 to Frame 6

---

### Post-Production Assembly

**Software**: After Effects, Premiere Pro, or DaVinci Resolve

**Steps**:
1. Import all 6 images as 1-second clips
2. Apply 0.5s crossfade transitions between each
3. Add subtle zoom-in (101% to 105% over 6 seconds) for dynamism
4. Color grade for consistency while maintaining environment distinctiveness
5. Add audio:
   - Voiceover: "One pair. Every lifestyle. Every moment."
   - Ambient sound morphing (office → gym → nature → train → library → studio)
   - Subtle whoosh on each transition

**Technical Notes**:
- Use motion tracking to ensure headphone position stays locked if images aren't perfectly aligned
- Apply subtle vignette to draw focus to center
- Add film grain for cohesion

---

## Example 2: Match Cut with Motion (Office → Gym)

### Concept
Headphone earcup stays in exact position. Character and environment change. Camera has slight movement.

### Execution Strategy: Veo First+Last Frame Interpolation

#### Why Veo Here?
- Need actual motion (zoom, slight camera movement)
- Transition between two distinct moments
- Duration: 2-3 seconds (Veo sweet spot)

#### Generation Plan

**Scene A: Office Focus (2s)**

##### First Frame - Imagen
```
Close-up portrait of 30-year-old mixed-race man wearing black over-ear headphones at office desk. Dark gray shirt. Tense expression. Modern office background. The headphone earcup is in bottom-right quadrant at coordinates X=850px, Y=1200px. Shot on 35mm, f/2.8. Aspect ratio: 9:16.
```

##### Last Frame - Imagen
```
Tighter close-up of same composition. Camera has pushed in 20%. The headphone earcup REMAINS at bottom-right quadrant, same coordinates X=850px, Y=1200px (appears larger due to zoom). Same man, same expression intensified. Aspect ratio: 9:16.
```

##### Veo Prompt
```
Slow dolly-in close-up shot. A 30-year-old mixed-race man wearing black over-ear headphones sits at office desk, furrowing brow in concentration. Camera slowly pushes in over 2 seconds. The headphone earcup remains in bottom-right quadrant throughout. Office environment, cool lighting. Shot on 35mm, shallow depth of field.

Voiceover: "Noise. Distraction."
Ambient noise: Office chatter.
```

---

**Scene B: Gym Power (3s) - MATCH CUT**

##### First Frame - Imagen
```
Close-up portrait of SAME 30-year-old mixed-race man wearing SAME black over-ear headphones, now in gym. Charcoal tank top. Intense expression, gripping dumbbell. Industrial gym background. The headphone earcup is in EXACT same bottom-right quadrant position at coordinates X=850px, Y=1200px. CRITICAL: This must geometrically match Scene A's last frame. Shot on 35mm, f/2.8. Aspect ratio: 9:16.
```

##### Last Frame - Imagen
```
Same composition. Man completes lift, muscles strained. Headphone earcup remains at same position. More sweat visible. Aspect ratio: 9:16.
```

##### Veo Prompt
```
Static close-up with subtle handheld shake. A 30-year-old mixed-race man wearing black over-ear headphones completes heavy dumbbell lift in industrial gym. Muscles strained, intense focus. The headphone earcup is positioned in bottom-right quadrant, matching previous office scene. High-contrast gym lighting. Shot on 35mm.

Voiceover: "To push harder."
SFX: Weights crashing, heavy breathing.
```

**Match Cut Execution**:
- Scene A last frame → Scene B first frame must have headphone earcup at IDENTICAL screen position
- Post-production: Hard cut on the beat
- Audio: Instant shift from office ambience to gym sounds

---

## Example 3: Quick Product Showcase (< 2s each)

### Concept
Rapid product shots showing different angles/features. Each shot < 2s.

### Execution Strategy: Imagen Sequence (No Veo)

#### Why Imagen Only?
- Each shot is < 2 seconds
- Static or minimal motion
- More cost-effective
- Easier to control exact composition

#### Generation Plan

**Total Duration**: 6 seconds (3 shots × 2s each)

##### Shot 1: Hero Angle (0-2s)
**Imagen Prompt**:
```
Hyper-realistic product photograph of matte black over-ear headphones at three-quarter angle. Minimalist dark gray background. Studio lighting with soft key light and rim light. Premium aesthetic. Shot on 85mm macro, f/4. Aspect ratio: 9:16.
```

**Post-Production**: 
- 2-second hold
- Subtle slow zoom (100% to 105%)
- Add product name text overlay

---

##### Shot 2: Detail Close-Up (2-4s)
**Imagen Prompt**:
```
Extreme close-up product photograph of headphone earcup showing premium leather padding and metal hinge detail. Same dark gray background. Dramatic side lighting highlighting texture. Shot on 100mm macro, f/2.8. Aspect ratio: 9:16.
```

**Post-Production**:
- 2-second hold
- Subtle pan right (5% movement)
- Add feature callout text

---

##### Shot 3: Lifestyle Context (4-6s)
**Imagen Prompt**:
```
Product photograph of black over-ear headphones resting on minimalist desk next to laptop and coffee cup. Soft natural window light. Premium lifestyle aesthetic. Shot on 50mm, f/2.8. Aspect ratio: 9:16.
```

**Post-Production**:
- 2-second hold
- Subtle zoom out (105% to 100%)
- Add CTA text

---

## Decision Matrix: When to Use What

| Scenario | Duration | Method | Reason |
|----------|----------|--------|--------|
| Static product shot | < 2s | Imagen only | No motion needed, cost-effective |
| Portrait with minimal motion | < 2s | Imagen + post zoom | Fake motion cheaper than Veo |
| Character morph sequence | Any | Imagen sequence + crossfade | Precise control over transformation |
| Match cut transition | 2-4s | Veo (first+last frame) | Need real camera motion |
| Continuous action | 4-8s | Veo (text-to-video or first+last) | Natural motion required |
| Complex camera move | 4-8s | Veo (first+last frame) | Controlled start/end points |
| Dialogue scene | 4-8s | Veo (text-to-video) | Audio sync required |
| Montage (multiple cuts) | Any | Multiple Imagen/Veo → edit | Each cut is separate generation |

---

## Technical Implementation: Sub-Scene Classification

### Algorithm for Scene Decomposition

```python
def classify_scene_generation_method(scene):
    """
    Determines optimal generation method based on scene characteristics.
    """
    
    # Extract scene metadata
    duration = scene.duration
    has_camera_movement = scene.camera_control.movement_type != "static"
    has_dialogue = scene.voiceover_text and scene.lip_sync
    is_transition = scene.transition_type in ["match_cut", "graphical_match"]
    is_montage = "montage" in scene.scene_composition or "rapid" in scene.action_prompt
    has_character = scene.characters is not None
    
    # Decision tree
    if is_montage:
        return {
            "method": "decompose_montage",
            "sub_scenes": decompose_into_shots(scene),
            "post_production": "edit_together"
        }
    
    if duration < 2.0 and not has_camera_movement and not has_dialogue:
        return {
            "method": "imagen_static",
            "frames": 1,
            "post_production": "add_fake_motion"  # zoom, pan in post
        }
    
    if is_transition and has_camera_movement:
        return {
            "method": "veo_first_last_frame",
            "frames": 2,  # Generate first and last keyframes
            "veo_duration": duration,
            "requires_match_coordinates": True
        }
    
    if duration >= 2.0 and duration <= 4.0:
        if has_camera_movement or has_dialogue:
            return {
                "method": "veo_first_last_frame",
                "frames": 2,
                "veo_duration": duration
            }
        else:
            return {
                "method": "imagen_sequence",
                "frames": int(duration),  # 1 frame per second
                "post_production": "crossfade_transitions"
            }
    
    if duration > 4.0 and duration <= 8.0:
        return {
            "method": "veo_full_generation",
            "input_type": "first_last_frame" if is_transition else "text_to_video",
            "veo_duration": duration,
            "use_reference_images": has_character
        }
    
    if duration > 8.0:
        return {
            "method": "split_into_multiple_scenes",
            "reason": "Veo max duration is 8s",
            "suggested_splits": math.ceil(duration / 6.0)  # Split into 6s chunks
        }


def decompose_into_shots(montage_scene):
    """
    Breaks a montage scene into individual shots.
    """
    # Parse action_prompt for shot descriptions
    # Example: "rapid-fire sequence: 1) office typing 2) running feet 3) gym sweat"
    
    shots = []
    total_duration = montage_scene.duration
    
    # Extract shot descriptions (this would use NLP in practice)
    shot_descriptions = extract_shot_descriptions(montage_scene.action_prompt)
    num_shots = len(shot_descriptions)
    shot_duration = total_duration / num_shots
    
    for i, description in enumerate(shot_descriptions):
        sub_scene = {
            "scene_id": f"{montage_scene.scene_id}_{chr(65+i)}",  # S4_A, S4_B, etc.
            "duration": shot_duration,
            "description": description,
            "method": classify_single_shot(description, shot_duration),
            "order": i
        }
        shots.append(sub_scene)
    
    return shots


def classify_single_shot(description, duration):
    """
    Classifies a single shot within a montage.
    """
    if duration < 2.0:
        return "imagen_static"
    elif duration < 4.0:
        return "veo_short_clip"
    else:
        return "veo_full_clip"
```

---

## Your Headphone Versatility Flow - Complete Execution

### Final Recommendation

**Method**: Imagen Sequence (6 frames) + Post-Production Crossfades

**Why**:
- Camera is locked (no motion needed)
- Morphing effect requires precise control
- Each "character swap" is essentially a still frame
- More cost-effective than 6 Veo generations
- Easier to ensure exact headphone positioning

**Execution Steps**:

1. **Generate Character Reference Images** (if needed for other scenes)
   - But for this morph sequence, each frame is standalone

2. **Generate 6 Keyframe Images with Imagen**
   - Use template prompt with variables: {character_description}, {environment}, {lighting}
   - CRITICAL: Include exact pixel coordinates for headphone position in each prompt
   - Use same camera settings (50mm, f/2.8, eye-level, centered)

3. **Post-Production Assembly**
   - Import as 1-second clips each
   - Apply 0.5s crossfade transitions
   - Add subtle zoom-in for dynamism (optional)
   - Color grade for consistency
   - Add audio: voiceover + morphing ambient sounds

4. **Quality Control**
   - Use motion tracking to lock headphone position if images aren't perfectly aligned
   - Apply subtle vignette to draw focus
   - Add film grain for cohesion

**Result**: Smooth morphing sequence showing headphone versatility across 6 different personas/environments in 6 seconds, with camera locked and headphones in exact position throughout.

---

## Summary: Hybrid Strategy Benefits

✅ **Cost-effective**: Use Imagen for static/minimal motion (cheaper)  
✅ **Quality control**: First+last frame gives precise transition control  
✅ **Flexibility**: Mix methods based on scene requirements  
✅ **Veo optimization**: Only use Veo when motion/audio truly needed  
✅ **Post-production power**: Leverage editing for effects Veo can't do natively  

The key insight: **Not everything needs to be generated as video. Strategic use of images + post-production can achieve effects that pure video generation cannot.**
