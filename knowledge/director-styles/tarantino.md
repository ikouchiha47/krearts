# Quentin Tarantino Style

## Overview

Tarantino's signature style combines non-linear storytelling, pop culture references, stylized violence, and distinctive visual/audio techniques.

---

## Key Characteristics

### 1. Non-Linear Narrative Structure

**Signature**: Chapter-based storytelling with scenes out of chronological order

**Examples**:
- *Pulp Fiction*: 3 interwoven stories told non-chronologically
- *Reservoir Dogs*: Present action intercut with flashbacks
- *Kill Bill*: Revenge story told in volumes and chapters

**Implementation**:
```json
{
  "narrative_structure": "tarantino_chapters",
  "chapters": [
    {
      "title": "Chapter 1: The Setup",
      "timeline": "present",
      "scenes": ["S1", "S2"]
    },
    {
      "title": "Chapter 2: The Backstory", 
      "timeline": "past",
      "timeline_offset": "-3 years",
      "scenes": ["S3", "S4"]
    },
    {
      "title": "Chapter 3: The Payoff",
      "timeline": "present",
      "scenes": ["S5", "S6"]
    }
  ]
}
```

---

### 2. Long Dialogue Scenes

**Signature**: Extended conversations building tension before violence

**Characteristics**:
- Static or slow-moving camera
- Medium shots and close-ups
- Mundane topics building to explosive moments
- Duration: 3-5 minutes (long for action films)

**Visual Style**:
```yaml
shot_type: medium_shot or close_up
camera_movement: minimal (locked off or slow push-in)
lighting: naturalistic
focus: dialogue and performance
tension: builds through conversation, not action
```

**For Short-Form**:
```yaml
duration: 8-12 seconds (condensed)
technique: rapid_dialogue_cuts
pacing: quick back-and-forth
payoff: sudden action or reveal
```

---

### 3. Trunk Shot (Low Angle POV)

**Signature**: Camera looking up from inside car trunk

**Visual**:
```yaml
camera_position: low angle, looking up
framing: characters looking down into frame
lighting: rim light around characters, dark foreground
aspect_ratio: 2.35:1 (ultra-wide)
```

**Prompt Template**:
```
Extreme low angle shot from inside car trunk looking up. 
[Characters] standing above, looking down into trunk. 
Strong rim lighting around their silhouettes against bright sky. 
Dark trunk interior in foreground. Cinematic 2.35:1 aspect ratio.
Shot on 35mm film, high contrast.
```

**Use Cases**:
- Victim POV
- Reveal moment
- Stylistic signature shot

---

### 4. Crash Zoom

**Signature**: Rapid zoom in on character's face during realization/shock

**Characteristics**:
```yaml
speed: very fast (0.3-0.5 seconds)
start: medium shot
end: extreme close-up on eyes
trigger: moment of realization or shock
audio: often paired with dramatic music sting
```

**Generation Strategy**:
```yaml
method: first_last_frame_interpolation
first_frame: medium shot of character
last_frame: extreme close-up of character's eyes
duration: 0.5s
post_production: speed up if needed
```

---

### 5. Stylized Violence

**Signature**: Over-the-top, choreographed violence with artistic flair

**Visual Style**:
```yaml
blood: exaggerated, bright red
slow_motion: used for impact moments
sound_design: amplified, stylized
music: often upbeat or ironic contrast
color_grading: saturated, vibrant
```

**For Commercial Use** (toned down):
```yaml
implication_over_graphic: suggest violence, don't show
quick_cuts: fast editing to imply action
sound_design: impactful but not graphic
aftermath: show result, not act
```

---

### 6. Pop Culture References

**Signature**: Characters discuss movies, music, TV shows

**Implementation**:
- Dialogue references to brands/products
- Retro music choices
- Vintage aesthetics
- Cultural touchstones

---

### 7. Title Cards

**Signature**: Bold, colorful chapter titles and character introductions

**Visual Style**:
```yaml
typography: bold, sans-serif or retro fonts
colors: bright yellow, red, white
animation: quick fade or wipe
placement: center or lower third
duration: 2-3 seconds
```

**Examples**:
- "CHAPTER 1: THE SETUP"
- "VINCENT VEGA - Hitman"
- "3 YEARS EARLIER"

---

### 8. Mexican Standoff

**Signature**: Multiple characters pointing guns at each other

**Composition**:
```yaml
shot_sequence:
  - wide_shot: establish all participants
  - individual_close_ups: each character's face
  - gun_close_ups: weapons pointed
  - rapid_cutting: between faces as tension builds
timing: slow build, sudden resolution
```

---

### 9. Retro Soundtrack

**Signature**: 60s/70s soul, surf rock, or eclectic music choices

**Characteristics**:
- Unexpected song choices
- Music contrasts with action
- Diegetic music (characters hear it)
- Iconic needle drops

---

### 10. Red Apple Cigarettes

**Signature**: Fictional brand appearing across films

**Implementation**: Consistent fictional brands create universe

---

## Color Palette

```yaml
primary: saturated, vibrant colors
blood: bright, arterial red
lighting: high contrast, dramatic shadows
film_stock: 35mm film aesthetic
grain: visible film grain
```

---

## Editing Rhythm

### Dialogue Scenes
```yaml
pacing: slow, deliberate
cuts: minimal during monologues
shot_duration: 5-10 seconds average
technique: let scenes breathe
```

### Action Scenes
```yaml
pacing: fast, kinetic
cuts: rapid during violence
shot_duration: 0.5-2 seconds
technique: quick cuts, slow motion accents
```

---

## For Short-Form Ads (15-30s)

### Tarantino-Inspired Structure

```yaml
structure:
  - title_card: "CHAPTER 1: THE PROBLEM" (1s)
  - dialogue_scene: Two characters discussing product (8s)
  - crash_zoom: Realization moment (0.5s)
  - title_card: "CHAPTER 2: THE SOLUTION" (1s)
  - action_sequence: Product in use, stylized (4s)
  - trunk_shot: Product reveal from low angle (2s)
  - title_card: Product name + tagline (2.5s)

total_duration: 19s
style: condensed Tarantino aesthetic
```

### Visual Approach
```yaml
aspect_ratio: 2.35:1 (cinematic)
color_grading: saturated, high contrast
music: retro/unexpected choice
dialogue: witty, pop culture reference
violence: implied, not graphic (for commercial)
```

---

## Screenplay Schema Extension

```python
class TarantinoStyle(BaseModel):
    """Tarantino-specific style metadata"""
    
    chapter_title: Optional[str]  # "CHAPTER 1: THE SETUP"
    timeline_label: Optional[str]  # "3 YEARS EARLIER"
    character_intro: Optional[str]  # "VINCENT VEGA - Hitman"
    
    dialogue_heavy: bool = False
    trunk_shot: bool = False
    crash_zoom: bool = False
    title_card: bool = False
    
    music_choice: Optional[str]  # Specific song or style
    
class Scene(BaseModel):
    scene_id: str
    tarantino_style: Optional[TarantinoStyle]
    # ... existing fields
```

---

## Prompt Engineering

### Trunk Shot
```
Extreme low angle POV from inside car trunk looking up. 
[Character] standing above trunk, looking down into camera. 
Strong rim lighting creating silhouette against bright sky. 
Dark trunk interior edges in foreground frame. 
Cinematic 2.35:1 ultra-wide aspect ratio. 
Shot on 35mm film, high contrast, Tarantino style.
```

### Crash Zoom
```
FIRST FRAME:
Medium shot of [character], neutral expression. 
Natural lighting, 2.35:1 aspect ratio.

LAST FRAME:
Extreme close-up of [character]'s eyes, wide with realization. 
Same lighting, same aspect ratio.

INTERPOLATION: Rapid zoom from medium to extreme close-up.
Duration: 0.5 seconds.
```

### Dialogue Scene
```
Medium shot, two characters sitting across table in diner booth. 
Natural lighting from window, slight film grain. 
[Character 1] on left, [Character 2] on right. 
Casual conversation, relaxed body language. 
Shot on 35mm film, 2.35:1 aspect ratio. 
Tarantino-style naturalistic dialogue scene.
```

### Title Card
```
Bold yellow text on black background: "CHAPTER 1: THE SETUP"
Sans-serif font, centered. 
Clean, high contrast. 
Tarantino-style chapter card.
```

---

## Post-Production

### Color Grading
```yaml
saturation: +15-20%
contrast: high (blacks crushed slightly)
highlights: slightly blown for film look
shadows: deep, rich blacks
film_grain: 35mm grain overlay
```

### Audio
```yaml
dialogue: crisp, clear, prominent
music: loud, prominent in mix
sound_effects: exaggerated, stylized
silence: used for tension
```

---

## Examples for Different Video Lengths

### 15-Second Ad
```
S1 (1s): Title card - "CHAPTER 1"
S2 (6s): Trunk shot - Product reveal from low angle
S3 (0.5s): Crash zoom - Customer's excited reaction
S4 (5s): Quick montage - Product in use
S5 (2.5s): Title card - Product name + tagline

Style: Condensed Tarantino aesthetic
Music: Retro surf rock
```

### 30-Second Ad
```
S1 (1s): Title card - "CHAPTER 1: THE PROBLEM"
S2 (8s): Dialogue scene - Two characters discussing issue
S3 (1s): Title card - "CHAPTER 2: THE SOLUTION"
S4 (0.5s): Crash zoom - Realization
S5 (2s): Trunk shot - Product reveal
S6 (1s): Title card - "CHAPTER 3: THE RESULT"
S7 (6s): Action montage - Product solving problem
S8 (2.5s): Title card - Product name + tagline
S9 (8s): End credits with retro music

Style: Full Tarantino chapter structure
Music: 70s soul track
```

---

## Key Takeaways

1. **Non-linear structure**: Use chapters and time jumps
2. **Dialogue-driven**: Let conversations build tension
3. **Signature shots**: Trunk shot, crash zoom
4. **Bold graphics**: Title cards with personality
5. **Stylized violence**: Artistic, not gratuitous (tone down for ads)
6. **Retro music**: Unexpected, ironic choices
7. **High contrast**: Saturated colors, deep blacks
8. **Film aesthetic**: 35mm grain, 2.35:1 aspect ratio
9. **Pop culture**: References and fictional brands
10. **Tension and release**: Slow build, explosive payoff

---

## When to Use Tarantino Style

**Good for**:
- Products with attitude/edge
- Storytelling-focused ads
- Retro/vintage brands
- Dialogue-heavy concepts
- Chapter-based narratives
- Cool, stylish brands

**Avoid for**:
- Corporate/conservative brands
- Family-friendly products
- Minimalist aesthetics
- Fast-paced action without story
- Serious/somber topics
