# Enhanced Screenplay Structure for Veo 3.1 Generation

## Video Context
- **Title**: (title of the video)
- **Target Audience**:
  - Demographic: (age, interests, lifestyle)
  - Cultural Context: (regional, cultural considerations)
  - Emotional Journey: (emotions invoked throughout)
- **Duration**: X seconds
- **Overall Energy**: (high_energy | moderate | calm | dramatic)
- **Visual Style**: (cinematic, documentary, artistic, commercial)
- **Lighting Consistency Guidelines**: 
  - Color Temperature: (warm/cool/neutral)
  - Lighting Progression: (how lighting evolves across scenes)
  - Mood Palette: (color grading approach)
- **Camera Equipment**: (35mm, 50mm, wide-angle, etc.)
- **Aspect Ratio**: 9:16 or 16:9

---

## Character Registry
(Define all characters upfront for reference image generation)

### Character: CHAR_001 - Alex
- **Physical Appearance**: 30-year-old man, mixed race, medium-brown skin tone, short black textured hair, athletic build
- **Style Evolution**: 
  - Scene 1-2: Dark gray smart casual shirt (office)
  - Scene 3-4: Charcoal gray performance tank top (gym)
  - Scene 5-6: Same tank + dark athletic shorts (run)
- **Voice Characteristics**: Confident, punchy, rhythmic, aspirational
- **Reference Images Required**: 
  - Front portrait (neutral expression)
  - Side profile
  - Full body (athletic stance)

---

## Scene Flow Map
(Visual overview of scene connections and transitions)

```
[S1: Office Focus] 
    ↓ (Graphical Match Cut - Headphone position)
[S2: Gym Power]
    ↓ (Graphical Match Cut - Headphone band to horizon)
[S3: Run Freedom]
    ↓ (Rhythm Cut - Energy shift)
[S4: Rapid Montage] → [S4A: Office] → [S4B: Run] → [S4C: Gym]
    ↓ (Smash Cut to Black)
[S5: Product Reveal]
```

---

## Scene 1: Office Focus

### Scene Metadata
- **Scene ID**: S1_OfficeFocus
- **Duration**: 2.0 seconds
- **Scene Type**: Hook
- **Composition**: Single continuous shot
- **Energy**: Dramatic, tense

### Scene Flow Context
- **Previous Scene**: N/A (opening shot)
- **Next Scene**: S2_GymPower
- **Transition Type**: Graphical Match Cut
- **Visual Bridge**: Headphone earcup position (bottom-right quadrant)
- **Narrative Purpose**: Establish problem - distraction and noise

### Characters Present
- **Primary**: CHAR_001 - Alex
- **Character State**: Tense, concentrating, fighting distraction
- **Character Action**: Furrowing brow, subtle head movements blocking out noise

### Environment Context
- **Location**: Modern minimalist office
- **Time of Day**: Mid-day (bright artificial lighting)
- **Ambient Sound**: Office chatter, keyboard clicks, phone rings
- **Mood**: Professional but stressful

### Camera Control

#### Camera Setup (First Frame)
- **Shot Type**: Close-up portrait
- **Camera Position**: Eye-level, slight right offset
- **Focal Length**: 35mm
- **Depth of Field**: Shallow (f/2.8)
- **Focus Point**: Alex's eyes and headphone earcup

#### Camera Movement
- **Movement Type**: Slow push-in (dolly forward)
- **Speed**: Gradual, 2-second duration
- **End Position**: Tighter close-up on face
- **Purpose**: Increase tension, draw viewer into Alex's struggle

#### Camera Consistency Guardrails
- **Headphone Earcup Position**: Bottom-right quadrant of frame (CRITICAL for match cut)
- **Eye-line**: Horizontal center
- **Lighting Direction**: Front-left key light

### Keyframe Image Descriptions

#### First Frame - Imagen Prompt
```
Cinematic close-up portrait photograph of a 30-year-old mixed-race man with medium-brown skin tone and short black textured hair. He is wearing high-end matte black over-ear headphones. Shot at eye-level with 35mm lens at f/2.8, creating shallow depth of field. He sits at a minimalist modern office desk wearing a dark gray smart casual shirt. The background shows blurred office environment with bright, cool-toned artificial lighting. His expression shows tense concentration - slightly furrowed brow, focused eyes. The black headphone earcup is prominently visible in the bottom-right quadrant of the frame. Professional studio lighting with soft key light from front-left. Photorealistic, high detail, 4K quality. Aspect ratio: 9:16.
```

#### Last Frame - Imagen Prompt
```
Same composition as first frame but tighter crop. Cinematic extreme close-up portrait of the same 30-year-old mixed-race man. Camera has pushed in closer - frame now shows from mid-forehead to chin. The black over-ear headphone earcup remains in bottom-right quadrant (CRITICAL). His brow is more furrowed, eyes more intense. Same lighting, same background blur. The headphone earcup position must geometrically match the first frame for seamless transition to next scene. 35mm lens, f/2.8, photorealistic. Aspect ratio: 9:16.
```

### Video Generation Caption (Veo 3.1 Prompt)

**Prompt Structure**: [Cinematography] + [Subject] + [Action] + [Context] + [Style & Ambiance]

```
Slow dolly-in close-up shot. A 30-year-old mixed-race man wearing matte black over-ear headphones sits at a minimalist office desk. He furrows his brow and shifts slightly, trying to concentrate despite audible office distractions. The modern office environment is bright with cool-toned artificial lighting, blurred in the background. The camera slowly pushes in from close-up to extreme close-up over 2 seconds, increasing tension. The black headphone earcup remains prominently visible in the bottom-right quadrant throughout. Cinematic, professional, shot on 35mm with shallow depth of field. 

Voiceover (male, confident, punchy): "Noise. Distraction. Always fighting for..."

Ambient noise: Office chatter, keyboard typing, phone ringing in distance.

Photorealistic, high-quality commercial aesthetic.
```

**Negative Prompt**:
```
cartoon, animated, low quality, blurry, distorted faces, multiple people, cluttered frame, harsh shadows, overexposed
```

### Visual Continuity Anchors
- **Consistent Element**: Black over-ear headphones (product hero)
- **Character**: CHAR_001 - Alex
- **Color Palette**: Cool grays, whites, muted blues
- **Key Lighting**: Soft front-left key, cool temperature
- **Critical Match Point**: Headphone earcup in bottom-right quadrant (for next scene match cut)

---

## Scene 2: Gym Power

### Scene Metadata
- **Scene ID**: S2_GymPower
- **Duration**: 3.0 seconds
- **Scene Type**: Problem escalation
- **Composition**: Single continuous shot
- **Energy**: High energy, intense

### Scene Flow Context
- **Previous Scene**: S1_OfficeFocus
- **Next Scene**: S3_RunFreedom
- **Transition Type**: Graphical Match Cut (from S1)
- **Visual Bridge FROM S1**: Headphone earcup position matches exactly
- **Visual Bridge TO S3**: Headphone band aligns with horizon line
- **Narrative Purpose**: Show versatility - same headphones, different intense environment

### Characters Present
- **Primary**: CHAR_001 - Alex
- **Character State**: Intensely focused, physically strained, powerful
- **Character Action**: Completing heavy dumbbell lift, muscles tensed

### Environment Context
- **Location**: Raw industrial gym
- **Time of Day**: Evening (high-contrast moody lighting)
- **Ambient Sound**: Weights crashing, rhythmic pulsing electronic music, heavy breathing
- **Mood**: Intense, powerful, gritty

### Camera Control

#### Camera Setup (First Frame)
- **Shot Type**: Close-up portrait
- **Camera Position**: Eye-level, MATCHING S1 headphone earcup position
- **Focal Length**: 35mm
- **Depth of Field**: Shallow (f/2.8)
- **Focus Point**: Alex's face and headphone earcup

#### Camera Movement
- **Movement Type**: Static with subtle handheld shake
- **Speed**: N/A (locked off with micro-movements)
- **Purpose**: Convey raw intensity and physical strain

#### Camera Consistency Guardrails
- **CRITICAL**: Headphone earcup MUST be in same bottom-right quadrant position as S1 final frame
- **Eye-line**: Horizontal center (matching S1)
- **Lighting Direction**: High-contrast side lighting (different mood but geometrically consistent framing)

### Keyframe Image Descriptions

#### First Frame - Imagen Prompt
```
GRAPHICAL MATCH CUT COMPOSITION. Cinematic close-up portrait photograph of a 30-year-old mixed-race man with medium-brown skin tone and short black textured hair wearing the identical matte black over-ear headphones. He is mid-lift, gripping a heavy dumbbell, wearing a charcoal gray performance tank top. Shot at eye-level with 35mm lens at f/2.8. The background is a raw industrial gym with high-contrast moody lighting - dramatic side lighting creating strong shadows. His expression shows intense focus and physical strain - clenched jaw, intense eyes, visible sweat. The black headphone earcup is positioned in the EXACT same bottom-right quadrant as the previous office scene (CRITICAL for match cut). Gritty, powerful aesthetic. Photorealistic, high detail. Aspect ratio: 9:16.
```

#### Last Frame - Imagen Prompt
```
Same composition. The 30-year-old mixed-race man has just completed the lift - slight release in facial tension but still intense. The dumbbell is at the top of the movement. Sweat is more visible. The headphone earcup remains in bottom-right quadrant. The horizontal headphone band across his head should be clearly visible and level (this will align with the horizon line in the next running scene). Same lighting, same gym background. 35mm, f/2.8, photorealistic. Aspect ratio: 9:16.
```

### Video Generation Caption (Veo 3.1 Prompt)

```
Static close-up shot with subtle handheld camera shake. A 30-year-old mixed-race man wearing matte black over-ear headphones completes the final repetition of a heavy dumbbell lift in a raw industrial gym. His muscles are visibly strained, jaw clenched, sweat glistening on his skin. He wears a charcoal gray performance tank top. The gym environment features high-contrast moody lighting with dramatic shadows. The camera remains steady, capturing the raw intensity. The black headphone earcup is prominently positioned in the bottom-right quadrant of the frame, geometrically matching the previous office scene.

Voiceover (male, confident, punchy): "...to switch gears. To push harder."

SFX: Heavy weights crashing, rhythmic pulsing electronic music.
Ambient noise: Gym atmosphere, heavy breathing.

Cinematic, gritty, powerful aesthetic. Shot on 35mm with shallow depth of field. Photorealistic.
```

**Negative Prompt**:
```
cartoon, animated, clean gym, bright lighting, multiple people, cluttered frame, soft focus
```

### Transition Frame to S3 (Optional Enhancement)

If the graphical match cut to S3 needs additional smoothness, generate a transition frame:

#### Transition Frame - Imagen Prompt
```
Medium close-up of the same man, now outdoors. The camera angle is transitioning from the gym close-up to an outdoor running shot. The headphone band is clearly visible and horizontal, positioned to align with the distant horizon line. Golden hour lighting begins to appear. This frame bridges the high-contrast gym lighting to warm outdoor lighting. Aspect ratio: 9:16.
```

### Visual Continuity Anchors
- **Consistent Element**: Black over-ear headphones (same product, different context)
- **Character**: CHAR_001 - Alex (same outfit: tank top)
- **Color Palette**: Dark grays, deep shadows, high contrast
- **Key Lighting**: Dramatic side lighting, warm-cool contrast
- **Critical Match Point FROM S1**: Headphone earcup bottom-right quadrant
- **Critical Match Point TO S3**: Headphone band horizontal alignment with horizon

---

## Scene 4: Rapid Benefits Montage

### Scene Metadata
- **Scene ID**: S4_RapidMontage
- **Duration**: 4.0 seconds TOTAL
- **Scene Type**: Benefit demonstration
- **Composition**: **MONTAGE - Multiple separate video generations**
- **Energy**: High energy, rhythmic

### Montage Strategy
- **Type**: Quick Cut Montage (requires post-production editing)
- **Total Cuts**: 3 separate video clips
- **Cut Rhythm**: 1.3s + 1.3s + 1.4s = 4.0s
- **Editing Note**: These are 3 SEPARATE Veo generations that will be edited together

### Scene Flow Context
- **Previous Scene**: S3_RunFreedom
- **Next Scene**: S5_ProductReveal (via smash cut to black)
- **Transition Type**: Rhythmic quick cuts (post-production)
- **Narrative Purpose**: Rapid demonstration of versatility across all three environments

---

#### Sub-Scene 4A: Office Typing

##### Sub-Scene Metadata
- **Scene ID**: S4A_OfficeTyping
- **Duration**: 1.3 seconds
- **Composition**: Single shot
- **Energy**: Focused, productive

##### Characters Present
- **Primary**: CHAR_001 - Alex
- **Character State**: Focused, productive, in flow state
- **Character Action**: Typing quickly on keyboard

##### Environment Context
- **Location**: Same modern office from S1
- **Time of Day**: Mid-day
- **Ambient Sound**: Keyboard clicking rapidly
- **Mood**: Productive flow

##### Camera Control
- **Shot Type**: Medium shot
- **Camera Position**: Slightly elevated angle looking down at desk
- **Focal Length**: 35mm
- **Movement**: Static

##### Keyframe Image Description

**First Frame - Imagen Prompt**:
```
Medium shot photograph from slightly elevated angle. A 30-year-old mixed-race man wearing matte black over-ear headphones sits at a modern minimalist desk, typing quickly on a sleek keyboard. He wears a dark gray smart casual shirt. His expression shows focused concentration - in the flow state. The office environment is clean, bright with cool-toned lighting. Shot on 35mm, photorealistic, high contrast, vibrant colors. Aspect ratio: 9:16.
```

##### Video Generation Caption (Veo 3.1 Prompt)

```
Static medium shot from slightly elevated angle. A 30-year-old mixed-race man wearing matte black over-ear headphones types quickly and confidently on a keyboard at a modern office desk. He wears a dark gray smart casual shirt. His movements are fluid and focused - in a productive flow state. The office is bright with cool-toned lighting, minimalist aesthetic. 

Voiceover (male, confident): "One pair."

SFX: Rapid keyboard clicking.
Ambient noise: Quiet office hum.

High-contrast, vibrant, commercial aesthetic. Shot on 35mm. Photorealistic.
```

---

#### Sub-Scene 4B: Running Feet

##### Sub-Scene Metadata
- **Scene ID**: S4B_RunningFeet
- **Duration**: 1.3 seconds
- **Composition**: Single shot
- **Energy**: Dynamic, freedom

##### Characters Present
- **Primary**: CHAR_001 - Alex (feet only visible)
- **Character State**: In motion, free, energized
- **Character Action**: Running on sunlit pavement

##### Environment Context
- **Location**: Outdoor city park path
- **Time of Day**: Golden hour
- **Ambient Sound**: Footsteps on pavement, air whooshing
- **Mood**: Freedom, movement

##### Camera Control
- **Shot Type**: Low angle close-up
- **Camera Position**: Ground level looking up at feet
- **Focal Length**: Wide angle (24mm)
- **Movement**: Tracking with runner

##### Keyframe Image Description

**First Frame - Imagen Prompt**:
```
Low angle close-up photograph of athletic legs and feet in dark athletic shorts and running shoes, mid-stride on sunlit pavement. Shot from ground level with 24mm wide-angle lens. Golden hour sunlight creates long shadows and warm tones. The background shows blurred park path. Dynamic, energetic composition. Photorealistic, high detail, vibrant warm colors. Aspect ratio: 9:16.
```

##### Video Generation Caption (Veo 3.1 Prompt)

```
Low angle tracking shot following running feet. Athletic legs in dark shorts and running shoes pound the sunlit pavement in a steady rhythm. Shot from ground level with wide-angle lens, creating dynamic perspective. Golden hour sunlight bathes the scene in warm tones, creating long shadows. The camera tracks smoothly with the runner's movement.

Voiceover (male, confident): "Every moment."

SFX: Rhythmic footsteps on pavement, air whooshing.

Dynamic, energetic, warm golden hour aesthetic. Shot on 24mm wide-angle. Photorealistic.
```

---

#### Sub-Scene 4C: Gym Sweat

##### Sub-Scene Metadata
- **Scene ID**: S4C_GymSweat
- **Duration**: 1.4 seconds
- **Composition**: Single shot
- **Energy**: Intense, powerful

##### Characters Present
- **Primary**: CHAR_001 - Alex
- **Character State**: Post-exertion, powerful, accomplished
- **Character Action**: Wiping sweat from brow

##### Environment Context
- **Location**: Industrial gym from S2
- **Time of Day**: Evening
- **Ambient Sound**: Gym ambience, heavy breathing
- **Mood**: Powerful, accomplished

##### Camera Control
- **Shot Type**: Close-up side angle
- **Camera Position**: Side profile, eye-level
- **Focal Length**: 50mm
- **Movement**: Static

##### Keyframe Image Description

**First Frame - Imagen Prompt**:
```
Close-up side angle photograph of a 30-year-old mixed-race man wearing matte black over-ear headphones in an industrial gym. He wipes sweat from his brow with his forearm, wearing a charcoal gray performance tank top. His expression shows satisfaction and power after intense workout. The headphone earcup is clearly visible. High-contrast moody lighting with dramatic shadows. Shot on 50mm lens. Photorealistic, gritty aesthetic. Aspect ratio: 9:16.
```

##### Video Generation Caption (Veo 3.1 Prompt)

```
Static close-up side angle shot. A 30-year-old mixed-race man wearing matte black over-ear headphones wipes sweat from his brow in an industrial gym. He wears a charcoal gray performance tank top. His expression shows satisfaction and accomplishment after intense exertion. The black headphone earcup is prominently visible. High-contrast moody lighting creates dramatic shadows in the raw gym environment.

SFX: Heavy breathing, distant weight clanking.
Ambient noise: Gym atmosphere.

Gritty, powerful, high-contrast aesthetic. Shot on 50mm. Photorealistic.
```

---

### Montage Assembly Notes (Post-Production)
- **Edit Pattern**: S4A (1.3s) → S4B (1.3s) → S4C (1.4s)
- **Cut Style**: Hard cuts on the beat
- **Audio**: Maintain voiceover continuity across cuts
- **Color Grading**: Maintain distinct color palettes (cool office, warm outdoor, high-contrast gym)
- **Transition to S5**: Smash cut to black after S4C

---

## Scene 5: Product Reveal

### Scene Metadata
- **Scene ID**: S5_ProductReveal
- **Duration**: 2.5 seconds
- **Scene Type**: Call to action
- **Composition**: Single shot (product focus)
- **Energy**: Bold, confident, aspirational

### Scene Flow Context
- **Previous Scene**: S4C_GymSweat (via smash cut to black)
- **Next Scene**: N/A (closing shot)
- **Transition Type**: Smash cut from black
- **Narrative Purpose**: Product hero moment, call to action

### Characters Present
- **None** (product-only shot)

### Environment Context
- **Location**: Studio environment
- **Background**: Minimalist dark gray gradient
- **Ambient Sound**: Silence → bold audio sting
- **Mood**: Premium, aspirational, bold

### Camera Control

#### Camera Setup
- **Shot Type**: Product beauty shot
- **Camera Position**: Eye-level, centered
- **Focal Length**: 85mm (product photography)
- **Movement**: Slow 360-degree rotation around product
- **Lighting**: Three-point studio lighting

#### Camera Movement
- **Movement Type**: Slow orbital rotation
- **Speed**: 2.5 seconds for partial rotation (120 degrees)
- **Purpose**: Showcase product design and premium quality

### Keyframe Image Descriptions

#### First Frame - Imagen Prompt
```
Hyper-realistic 3D product photograph of premium matte black over-ear headphones floating in center frame against a minimalist dark gray gradient background. Studio lighting with soft key light from front-left, fill light from right, and rim light from behind creating subtle edge glow. The headphones are positioned at a slight three-quarter angle showing the earcup detail and headband. Shot on 85mm macro lens with perfect focus. Premium, clean, aspirational aesthetic. Photorealistic, ultra-high detail, 8K quality. Aspect ratio: 9:16.
```

#### Last Frame - Imagen Prompt
```
Same hyper-realistic product shot but the headphones have rotated approximately 120 degrees, now showing a different angle - more of the side profile and opposite earcup. Same minimalist dark gray background, same studio lighting creating consistent premium aesthetic. The rotation is smooth and elegant. 85mm macro lens, perfect focus, photorealistic. Aspect ratio: 9:16.
```

### Video Generation Caption (Veo 3.1 Prompt)

```
Slow orbital camera rotation around premium matte black over-ear headphones. The headphones float elegantly in center frame against a minimalist dark gray gradient background. The camera rotates smoothly 120 degrees over 2.5 seconds, revealing the product's sleek design, premium materials, and functional details. Studio lighting creates soft highlights and subtle rim lighting. The rotation is smooth and cinematic, emphasizing the product's premium quality and design excellence.

Voiceover (male, confident, aspirational): "Performance meets versatility."

SFX: Subtle whoosh sound as camera rotates, ending with bold audio sting.

Premium, clean, aspirational aesthetic. Shot on 85mm macro lens. Hyper-realistic, ultra-high quality.
```

**Negative Prompt**:
```
cartoon, low quality, cluttered background, multiple products, text overlay, busy composition, harsh shadows
```

### On-Screen Text (Post-Production)
- **Text 1** (0.0s-1.0s): "HEADPHONES. REIMAGINED." (bold white sans-serif)
- **Text 2** (1.5s-2.5s): "GET YOUR FLOW. BUY NOW." (bold white sans-serif with CTA)

### Visual Continuity Anchors
- **Product**: Black over-ear headphones (hero product from all scenes)
- **Color Palette**: Dark grays, blacks, minimal
- **Lighting**: Premium studio lighting
- **Mood**: Aspirational, confident, premium

---

## Generation Manifest

### Phase 1: Character Reference Images
1. **CHAR_001_front.png** - Imagen generation
2. **CHAR_001_side.png** - Imagen generation
3. **CHAR_001_full.png** - Imagen generation

### Phase 2: Scene Keyframes
1. **S1_first_frame.png** - Imagen generation
2. **S1_last_frame.png** - Imagen generation
3. **S2_first_frame.png** - Imagen generation (match cut composition)
4. **S2_last_frame.png** - Imagen generation
5. **S3_first_frame.png** - Imagen generation (match cut composition)
6. **S3_last_frame.png** - Imagen generation
7. **S4A_first_frame.png** - Imagen generation
8. **S4B_first_frame.png** - Imagen generation
9. **S4C_first_frame.png** - Imagen generation
10. **S5_first_frame.png** - Imagen generation
11. **S5_last_frame.png** - Imagen generation

### Phase 3: Video Generation
1. **S1_OfficeFocus.mp4** - Veo 3.1 (first+last frame interpolation, 2s)
2. **S2_GymPower.mp4** - Veo 3.1 (first+last frame interpolation, 3s, with character references)
3. **S3_RunFreedom.mp4** - Veo 3.1 (first+last frame interpolation, 3s, with character references)
4. **S4A_OfficeTyping.mp4** - Veo 3.1 (image-to-video, 1.3s, with character references)
5. **S4B_RunningFeet.mp4** - Veo 3.1 (image-to-video, 1.3s)
6. **S4C_GymSweat.mp4** - Veo 3.1 (image-to-video, 1.4s, with character references)
7. **S5_ProductReveal.mp4** - Veo 3.1 (first+last frame interpolation, 2.5s)

### Phase 4: Post-Production Assembly
1. Edit S4A + S4B + S4C into montage sequence
2. Add smash cut to black transition
3. Add on-screen text to S5
4. Color grade for consistency
5. Mix audio (voiceover, SFX, music)

---

## Notes on Quick Cuts with Flow Consistency

### Strategy for Maintaining Flow with Quick Cuts:

1. **Graphical Match Cuts** (S1→S2, S2→S3):
   - Use geometric composition matching (headphone position)
   - Maintain eye-line consistency
   - Create visual "anchors" that persist across cuts

2. **Montage Decomposition** (S4):
   - Generate each cut as separate video
   - Maintain character consistency via reference images
   - Use distinct color palettes to differentiate environments
   - Edit together in post-production

3. **Transition Frames** (Optional):
   - Generate intermediate frames for smoother transitions
   - Use when lighting/context changes are too abrupt

4. **Camera Consistency Guardrails**:
   - Document exact positions of key elements (headphone earcup, eye-line)
   - Specify these in both first/last frame prompts
   - Use same focal lengths for matching shots

5. **Lighting Progression**:
   - Cool → High-contrast → Warm → Minimal
   - Each scene has distinct palette but logical progression

This structure allows for:
- ✅ Quick cuts (via separate generations + post-production)
- ✅ Visual flow (via match cuts and consistent elements)
- ✅ Narrative coherence (via scene flow context)
- ✅ Character consistency (via reference images)
- ✅ Proper Veo usage (single continuous shots per generation)
