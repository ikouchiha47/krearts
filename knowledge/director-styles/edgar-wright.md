# Edgar Wright Style

## Overview

Edgar Wright's signature style features rapid-fire editing, visual comedy, match cuts, whip pans, and meticulous attention to comedic timing and visual storytelling.

---

## Key Characteristics

### 1. Quick Cuts / Rapid Montage

**Signature**: Mundane actions shown through rapid succession of close-ups

**Characteristics**:
```yaml
shot_duration: 0.1-0.3 seconds per cut
shot_types: extreme close-ups of details
action: everyday tasks (making coffee, getting dressed)
pacing: rhythmic, musical
sound_design: exaggerated foley, synchronized to cuts
```

**Example Sequence** (Getting Ready):
```
Cut 1 (0.2s): Alarm clock - hand hitting snooze
Cut 2 (0.2s): Eyes opening - extreme close-up
Cut 3 (0.2s): Feet hitting floor
Cut 4 (0.2s): Toothbrush in mouth
Cut 5 (0.2s): Water running
Cut 6 (0.2s): Door closing
Cut 7 (0.2s): Keys grabbed
Cut 8 (0.2s): Door locked

Total: 1.6s for entire morning routine
```

**Generation Strategy**:
```yaml
method: multiple_image_generations
approach: generate 8-12 extreme close-up images
post_production: stitch with 0.1-0.3s per frame
audio: sync sound effects to each cut
```

**Prompt Template**:
```
Extreme close-up, [specific detail]. 
Sharp focus, high contrast. 
Bright, saturated colors. 
Clean, graphic composition.
Shot on digital cinema camera, crisp detail.
```

---

### 2. Whip Pan Transitions

**Signature**: Extremely fast camera pan creating motion blur transition

**Characteristics**:
```yaml
speed: very fast (0.1-0.2 seconds)
blur: heavy motion blur
direction: horizontal or vertical
purpose: transition between scenes or reveal
```

**Generation Strategy**:
```yaml
method: post_production_effect
approach:
  - Generate Scene A (static)
  - Generate Scene B (static)
  - Add whip pan transition in post
  
alternative_method: first_last_frame
  - First frame: Scene A
  - Last frame: Scene B
  - Veo interpolates with motion blur
```

**Use Cases**:
- Scene transitions
- Time passage
- Comedic reveals
- Matching action across locations

---

### 3. Match Cuts on Action

**Signature**: Cutting between different actions that share similar motion/composition

**Example**:
```
Cut 1: Character closing car door
Cut 2: Character closing refrigerator door (same motion)
Cut 3: Character closing office door (same motion)

Effect: Visual rhythm, comedic repetition
```

**Implementation**:
```yaml
method: separate_videos_with_matched_composition
requirements:
  - Same screen position for action
  - Same direction of movement
  - Similar timing
  - Hard cut on action beat
```

---

### 4. Crash Zooms (Comedy Version)

**Signature**: Sudden, fast zoom for comedic emphasis

**Characteristics**:
```yaml
speed: very fast (0.2-0.4 seconds)
trigger: punchline, realization, or absurd moment
style: slightly shaky, handheld feel
purpose: comedic emphasis
```

**Different from Tarantino**:
- More frequent
- Comedic rather than dramatic
- Often paired with sound effect
- Can be in/out/in-out

---

### 5. Symmetrical Framing

**Signature**: Perfectly centered, balanced compositions

**Characteristics**:
```yaml
composition: centered subject
symmetry: bilateral symmetry
depth: often deep focus
style: Wes Anderson influence
purpose: visual comedy, formality
```

**Prompt Template**:
```
Perfectly symmetrical composition, [subject] centered in frame. 
Bilateral symmetry, balanced left and right. 
Deep focus, everything sharp. 
Bright, saturated colors. 
Formal, geometric framing.
Shot on digital cinema camera, 16:9 aspect ratio.
```

---

### 6. Visual Foreshadowing

**Signature**: Background details that hint at future events

**Implementation**:
- Props in background become important later
- Visual jokes hidden in frame
- Repeated visual motifs
- Blink-and-miss-it details

**For Ads**:
```yaml
technique: plant_and_payoff
setup: Product visible in background early
payoff: Product becomes focus later
duration: 2-3 second gap between plant and payoff
```

---

### 7. Text on Screen

**Signature**: On-screen text for comedic effect or information

**Characteristics**:
```yaml
style: clean, sans-serif fonts
animation: quick fade or wipe
purpose: 
  - Character names
  - Location/time
  - Comedic commentary
  - Sound effect visualization
placement: varies (not always lower third)
```

**Examples**:
- "MONDAY 8:47 AM"
- "DAVE - Accountant"
- "*THUD*" (sound effect text)
- "3 COFFEES LATER"

---

### 8. Fence Gag / Repetition

**Signature**: Same action repeated with slight variations

**Example**:
```
Character jumps over fence
Cut to: Different angle, jumps over another fence
Cut to: Different angle, jumps over another fence
Cut to: Different angle, crashes into fence

Effect: Builds rhythm, then breaks it for comedy
```

**Implementation**:
```yaml
method: multiple_separate_generations
pattern: A-A-A-B (repeat, repeat, repeat, break)
timing: 0.5-1.0s per repetition
payoff: unexpected variation on final repeat
```

---

### 9. Sound Design as Comedy

**Signature**: Exaggerated, synchronized sound effects

**Characteristics**:
```yaml
foley: amplified, crisp
synchronization: perfectly timed to cuts
style: cartoonish but realistic
purpose: comedic emphasis
```

**Examples**:
- Every footstep has distinct sound
- Objects make exaggerated sounds
- Silence used for comedic timing
- Music stings for punchlines

---

### 10. Cornetto Trilogy Color Palette

**Signature**: Specific color schemes for different moods

**Shaun of the Dead** (Red):
```yaml
primary_color: red (blood, danger)
secondary: browns, grays (mundane)
mood: horror-comedy
```

**Hot Fuzz** (Blue):
```yaml
primary_color: blue (police, authority)
secondary: greens (village)
mood: action-comedy
```

**The World's End** (Green):
```yaml
primary_color: green (aliens, pubs)
secondary: warm tones
mood: sci-fi-comedy
```

---

## Editing Rhythm

### Mundane Actions
```yaml
pacing: extremely fast
cuts: 8-15 per second
shot_duration: 0.1-0.3 seconds
technique: rapid montage
```

### Dialogue Scenes
```yaml
pacing: moderate
cuts: on punchlines or reactions
shot_duration: 2-4 seconds
technique: shot-reverse-shot with energy
```

### Action Scenes
```yaml
pacing: fast but clear
cuts: rhythmic, musical
shot_duration: 0.5-2 seconds
technique: geography maintained, creative angles
```

---

## For Short-Form Ads (15-30s)

### Edgar Wright-Inspired Structure

**15-Second Ad**:
```yaml
structure:
  - rapid_montage: Morning routine (3s, 12 cuts)
  - whip_pan: Transition to problem (0.2s)
  - symmetrical_shot: Product introduction (2s)
  - rapid_montage: Product solving problem (4s, 15 cuts)
  - crash_zoom: Happy customer (0.3s)
  - text_card: Product name + tagline (2.5s)
  - whip_pan: To logo (0.2s)
  - logo: Final frame (2.8s)

total_duration: 15s
cuts: ~30 total
style: high-energy, comedic
```

**30-Second Ad**:
```yaml
structure:
  - text_card: "MONDAY 8:47 AM" (1s)
  - rapid_montage: Character's chaotic morning (5s, 20 cuts)
  - whip_pan: Transition (0.2s)
  - symmetrical_shot: Character discovers product (3s)
  - match_cut_sequence: Product used in 3 locations (6s)
  - fence_gag: Repetition with variation (4s)
  - crash_zoom: Realization (0.3s)
  - rapid_montage: Life improved (5s, 20 cuts)
  - text_card: Product name (2s)
  - whip_pan: To logo (0.2s)
  - logo: Final frame (3.3s)

total_duration: 30s
cuts: ~50 total
style: comedic, energetic, visual storytelling
```

---

## Screenplay Schema Extension

```python
class EdgarWrightStyle(BaseModel):
    """Edgar Wright-specific style metadata"""
    
    rapid_montage: bool = False
    montage_cuts: Optional[int]  # Number of cuts in montage
    
    whip_pan: bool = False
    whip_pan_direction: Optional[Literal["left", "right", "up", "down"]]
    
    crash_zoom: bool = False
    crash_zoom_speed: Optional[float]  # Duration in seconds
    
    symmetrical_framing: bool = False
    
    match_cut_action: bool = False
    match_cut_count: Optional[int]  # Number of matched cuts
    
    text_overlay: Optional[str]  # On-screen text
    text_style: Optional[Literal["time", "name", "sound", "commentary"]]
    
    fence_gag: bool = False  # Repetition with variation
    
class Scene(BaseModel):
    scene_id: str
    edgar_wright_style: Optional[EdgarWrightStyle]
    # ... existing fields
```

---

## Prompt Engineering

### Rapid Montage (Individual Shots)
```
Extreme close-up of [specific detail]. 
Sharp focus, high contrast, bright saturated colors. 
Clean graphic composition, centered subject. 
Shot on digital cinema camera, crisp detail. 
Edgar Wright style quick cut.
```

### Symmetrical Shot
```
Perfectly symmetrical composition, [subject] centered in frame. 
Bilateral symmetry, balanced composition. 
Deep focus, everything sharp from foreground to background. 
Bright, saturated colors, clean aesthetic. 
Formal, geometric framing. 
Shot on digital cinema camera, 16:9 aspect ratio.
Edgar Wright style symmetrical framing.
```

### Whip Pan (Post-Production)
```
Scene A: [description]
Scene B: [description]

Post-production: Add 0.2s whip pan transition with heavy motion blur
Direction: [left/right/up/down]
```

### Match Cut Action
```
Shot 1: [Character] closing car door, right side of frame
Shot 2: [Character] closing refrigerator door, SAME position in frame
Shot 3: [Character] closing office door, SAME position in frame

CRITICAL: Maintain exact screen position and motion direction
Cut on action beat (door halfway closed)
```

---

## Post-Production

### Color Grading
```yaml
saturation: high (+20-30%)
contrast: moderate to high
brightness: slightly elevated (comedy is bright)
colors: vibrant, punchy
blacks: not crushed (maintain detail)
```

### Audio
```yaml
foley: exaggerated, crisp
music: rhythmic, synchronized to cuts
sound_effects: cartoonish but realistic
silence: used for comedic timing
dialogue: clear, prominent
```

### Editing
```yaml
cuts: on beat (musical rhythm)
timing: precise to frame
pacing: fast but clear
geography: always maintained
continuity: meticulous
```

---

## Examples for Different Video Lengths

### 15-Second Product Demo
```
S1 (3s): Rapid montage - 12 cuts showing problem
  - Cut 1-4: Messy desk (0.25s each)
  - Cut 5-8: Frustrated user (0.25s each)
  - Cut 9-12: Chaos (0.25s each)

S2 (0.2s): Whip pan transition

S3 (2s): Symmetrical shot - Product reveal

S4 (4s): Rapid montage - 16 cuts showing solution
  - Cut 1-8: Product in use (0.25s each)
  - Cut 9-16: Happy results (0.25s each)

S5 (0.3s): Crash zoom - Customer smile

S6 (2.5s): Text card - Product name

S7 (3s): Logo

Total cuts: 30
Style: High-energy, visual comedy
```

### 30-Second Story
```
S1 (1s): Text - "MONDAY 8:47 AM"

S2 (5s): Rapid montage - Morning chaos (20 cuts)

S3 (0.2s): Whip pan

S4 (3s): Symmetrical - Product discovery

S5 (6s): Match cut sequence - Product used 3 ways
  - Location 1 (2s)
  - Location 2 (2s)
  - Location 3 (2s)

S6 (4s): Fence gag - Repetition with variation
  - Attempt 1 (1s)
  - Attempt 2 (1s)
  - Attempt 3 (1s)
  - Success (1s)

S7 (0.3s): Crash zoom - Realization

S8 (5s): Rapid montage - Life improved (20 cuts)

S9 (2s): Text - Product name

S10 (0.2s): Whip pan

S11 (3.3s): Logo

Total cuts: 50+
Style: Comedic narrative, visual storytelling
```

---

## Key Takeaways

1. **Rapid editing**: 8-15 cuts per second for mundane actions
2. **Extreme close-ups**: Show details, not just wide shots
3. **Whip pans**: Fast transitions between scenes
4. **Match cuts**: Same action, different contexts
5. **Symmetrical framing**: Centered, balanced compositions
6. **Visual foreshadowing**: Details matter
7. **Text on screen**: Comedic or informative
8. **Repetition with variation**: Build rhythm, break for comedy
9. **Exaggerated sound**: Every action has crisp foley
10. **Musical editing**: Cuts on beat, rhythmic pacing

---

## When to Use Edgar Wright Style

**Good for**:
- Product demos (make mundane exciting)
- Comedic ads
- High-energy brands
- Tech products
- Lifestyle products
- Before/after transformations
- Visual storytelling without dialogue

**Avoid for**:
- Luxury/premium brands (too frenetic)
- Serious/emotional topics
- Slow, contemplative products
- Brands requiring gravitas
- Medical/pharmaceutical (too comedic)

---

## Technical Requirements

### For Rapid Montage
```yaml
images_needed: 8-15 per second of montage
image_type: extreme close-ups
generation_method: multiple image generations
post_production: ffmpeg stitch at 0.1-0.3s per frame
audio: sync foley to each cut
```

### For Whip Pans
```yaml
method: post_production_effect
software: After Effects, Premiere, or similar
duration: 0.1-0.2 seconds
blur: heavy motion blur
```

### For Match Cuts
```yaml
method: separate_video_generations
requirement: precise composition matching
timing: cut on action beat
continuity: maintain screen position
```

---

## Comparison with Other Styles

| Element | Edgar Wright | Tarantino | Wes Anderson |
|---------|-------------|-----------|--------------|
| Pacing | Very fast | Slow then fast | Deliberate |
| Cuts | 8-15/sec | 2-4/sec | 3-5/sec |
| Symmetry | Frequent | Rare | Constant |
| Comedy | Visual | Dialogue | Deadpan |
| Violence | Comedic | Stylized | Minimal |
| Music | Rhythmic | Retro | Whimsical |
| Color | Saturated | Saturated | Pastel |

---

## Summary

Edgar Wright's style is perfect for making ordinary actions extraordinary through rapid editing, visual comedy, and meticulous attention to detail. It's ideal for product demos and comedic ads that need high energy and visual storytelling.
