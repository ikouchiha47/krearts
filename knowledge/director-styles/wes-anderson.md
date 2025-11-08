# Wes Anderson Style

## Overview

Wes Anderson's signature style features symmetrical compositions, pastel color palettes, whimsical production design, deadpan humor, and meticulous attention to visual detail.

---

## Key Characteristics

### 1. Perfect Symmetry

**Signature**: Centered, perfectly balanced compositions

**Characteristics**:
```yaml
composition: bilateral symmetry
subject_placement: dead center
horizon: perfectly level
depth: often flat, frontal
style: formal, geometric
```

**Prompt Template**:
```
Perfectly symmetrical composition, [subject] centered exactly in frame.
Bilateral symmetry, balanced left and right sides.
Frontal view, flat perspective.
Pastel [color] color palette.
Whimsical, storybook aesthetic.
Shot on film, shallow depth of field.
Wes Anderson style symmetrical framing.
```

---

### 2. Pastel Color Palette

**Signature**: Soft, muted, carefully coordinated colors

**Color Schemes**:
```yaml
primary_colors:
  - pale_pink: #FFB6C1
  - mint_green: #98D8C8
  - butter_yellow: #F7DC6F
  - powder_blue: #B0E0E6
  - coral: #FF7F50
  - lavender: #E6E6FA

characteristics:
  saturation: low to medium
  brightness: high
  contrast: low
  harmony: carefully coordinated
  mood: whimsical, nostalgic
```

**Post-Production**:
```yaml
color_grading:
  - Reduce saturation by 20-30%
  - Lift shadows (no crushed blacks)
  - Soft highlights
  - Add slight warm or cool cast
  - Match colors across scenes
```

---

### 3. Flat Lay / Knolling

**Signature**: Objects arranged symmetrically from overhead view

**Characteristics**:
```yaml
camera_angle: directly overhead (90° down)
arrangement: geometric, organized
spacing: equal, precise
background: solid color or texture
purpose: inventory, organization, visual pleasure
```

**Prompt Template**:
```
Flat lay overhead shot, perfectly organized [objects].
Symmetrical arrangement, equal spacing.
[Pastel color] background.
Soft, even lighting, no harsh shadows.
Whimsical, storybook aesthetic.
Wes Anderson style knolling composition.
```

**Use Cases**:
- Product showcases
- Character belongings
- Tool kits
- Collections

---

### 4. Planimetric Composition

**Signature**: Frontal, flat perspective with minimal depth

**Characteristics**:
```yaml
perspective: frontal, parallel to camera
depth: minimal, flat
layers: stacked horizontally or vertically
style: like a stage set or diorama
```

**Example**:
```
Wide shot of room, camera perpendicular to back wall.
All furniture and objects face camera.
Symmetrical arrangement.
Flat, stage-like perspective.
```

---

### 5. Slow Motion

**Signature**: Slow-motion for emotional or comedic moments

**Characteristics**:
```yaml
speed: 50-75% normal speed
purpose: emphasize emotion or absurdity
music: often melancholic or whimsical
duration: 2-5 seconds
```

**Use Cases**:
- Character walking
- Emotional moments
- Group shots
- Comedic reveals

---

### 6. Whip Pans (Horizontal)

**Signature**: Fast horizontal pans between characters or objects

**Characteristics**:
```yaml
direction: horizontal (left/right)
speed: very fast
purpose: show multiple subjects quickly
style: energetic but controlled
```

---

### 7. Tracking Shots

**Signature**: Smooth lateral tracking following character

**Characteristics**:
```yaml
movement: horizontal, parallel to subject
speed: matches character's walking pace
framing: profile view, centered
background: often symmetrical or repeating
```

**Prompt Template**:
```
Tracking shot, profile view of [character] walking [left/right].
Character centered in frame, moving at steady pace.
[Pastel color] symmetrical background.
Smooth, steady camera movement.
Wes Anderson style tracking shot.
```

---

### 8. Chapter Titles / Intertitles

**Signature**: Centered text cards with custom typography

**Characteristics**:
```yaml
typography: custom, often serif or typewriter
placement: centered
background: solid color or scene
animation: fade or cut
duration: 2-3 seconds
```

**Examples**:
- "CHAPTER 1"
- "3 WEEKS LATER"
- "THE GRAND BUDAPEST HOTEL"

---

### 9. Miniatures / Dioramas

**Signature**: Miniature sets that look like toys or models

**Characteristics**:
```yaml
scale: obviously miniature
style: handcrafted, whimsical
purpose: establishing shots, transitions
aesthetic: storybook, fantastical
```

**For Ads**:
```yaml
technique: miniature_product_world
approach: Show product in miniature diorama
style: whimsical, handcrafted
lighting: soft, even
```

---

### 10. Ensemble Cast Shots

**Signature**: Group shots with all characters facing camera

**Characteristics**:
```yaml
arrangement: symmetrical, organized
framing: all characters visible
expression: deadpan or slight smile
purpose: family portrait aesthetic
```

---

## Typography

```yaml
fonts:
  - Futura (most common)
  - Archer
  - Helvetica
  - Custom typewriter fonts

style:
  - Clean, geometric
  - Often all caps
  - Centered alignment
  - Generous spacing
```

---

## Camera Movement

```yaml
movements:
  - tracking_shot: smooth, horizontal
  - whip_pan: fast, horizontal
  - slow_zoom: gradual push-in
  - static: locked off, symmetrical

characteristics:
  - Deliberate, controlled
  - Never handheld shakiness
  - Smooth, mechanical
  - Purposeful
```

---

## Aspect Ratios

```yaml
common_ratios:
  - 1.85:1 (standard)
  - 2.35:1 (anamorphic)
  - 4:3 (academy ratio)
  - Custom ratios for specific films

characteristics:
  - Often changes within film
  - Ratio serves story
  - Symmetry maintained regardless
```

---

## For Short-Form Ads (15-30s)

### Wes Anderson-Inspired Structure

**15-Second Ad**:
```yaml
structure:
  - title_card: "CHAPTER 1" (1.5s)
  - symmetrical_shot: Product in perfect composition (3s)
  - flat_lay: Product components overhead (2.5s)
  - tracking_shot: Product in use, profile view (4s)
  - slow_motion: Happy customer (2s)
  - title_card: Product name (2s)

total_duration: 15s
style: whimsical, symmetrical, pastel
music: quirky, instrumental
```

**30-Second Ad**:
```yaml
structure:
  - title_card: "THE [PRODUCT NAME] STORY" (2s)
  - symmetrical_shot: Character with problem (4s)
  - whip_pan: To product (0.3s)
  - flat_lay: Product components (3s)
  - tracking_shot: Character using product (5s)
  - slow_motion: Transformation moment (3s)
  - ensemble_shot: Multiple happy customers (4s)
  - miniature_shot: Product in whimsical world (3s)
  - title_card: "CHAPTER 2: HAPPINESS" (1.5s)
  - symmetrical_shot: Final product shot (4s)
  - title_card: Product name + tagline (2.2s)

total_duration: 32s
style: storybook narrative, whimsical
music: melancholic but uplifting
```

---

## Screenplay Schema Extension

```python
class WesAndersonStyle(BaseModel):
    """Wes Anderson-specific style metadata"""
    
    symmetrical: bool = True  # Almost always true
    
    color_palette: List[str]  # Specific pastel colors
    
    flat_lay: bool = False
    planimetric: bool = False
    
    slow_motion: bool = False
    slow_motion_speed: Optional[float]  # 0.5 = 50% speed
    
    tracking_shot: bool = False
    tracking_direction: Optional[Literal["left", "right"]]
    
    whip_pan: bool = False
    
    title_card: bool = False
    title_text: Optional[str]
    title_font: Optional[str]  # "Futura", "Archer", etc.
    
    miniature: bool = False
    
class Scene(BaseModel):
    scene_id: str
    wes_anderson_style: Optional[WesAndersonStyle]
    # ... existing fields
```

---

## Prompt Engineering

### Symmetrical Shot
```
Perfectly symmetrical composition, [subject] centered exactly in frame.
Bilateral symmetry, balanced left and right.
Frontal view, flat perspective.
Pastel [pink/blue/yellow/green] color palette, soft muted tones.
Whimsical, storybook aesthetic.
Soft, even lighting.
Shot on 35mm film, shallow depth of field.
Wes Anderson style symmetrical framing.
```

### Flat Lay
```
Flat lay overhead shot, [objects] arranged symmetrically.
Perfectly organized, equal spacing between items.
[Pastel color] background.
Soft, even lighting, no harsh shadows.
Geometric arrangement, bilateral symmetry.
Whimsical, handcrafted aesthetic.
Wes Anderson style knolling composition.
```

### Tracking Shot
```
Smooth tracking shot, profile view of [character] walking [left/right].
Character centered in frame, steady walking pace.
[Pastel color] symmetrical background with repeating elements.
Soft, even lighting.
Whimsical, storybook aesthetic.
Shot on 35mm film.
Wes Anderson style lateral tracking shot.
```

### Slow Motion
```
Slow motion shot (50% speed), [character/action].
[Pastel color] palette, soft lighting.
Emotional or whimsical moment.
Symmetrical composition.
Shot on 35mm film.
Wes Anderson style slow motion.
```

---

## Post-Production

### Color Grading
```yaml
saturation: reduced by 20-30%
highlights: soft, not blown
shadows: lifted, no crushed blacks
midtones: slightly warm or cool cast
colors: coordinated, harmonious
film_look: 35mm film emulation
grain: subtle, fine grain
```

### Audio
```yaml
music: 
  - Quirky instrumental
  - Melancholic but uplifting
  - Often vintage or classical
  - Prominent in mix

dialogue:
  - Deadpan delivery
  - Clear, centered
  - Often narration

sound_effects:
  - Subtle, realistic
  - Not exaggerated
  - Clean, precise
```

---

## Examples for Different Video Lengths

### 15-Second Product Showcase
```
S1 (1.5s): Title card - "THE [PRODUCT]"
S2 (3s): Symmetrical shot - Product centered, pastel background
S3 (2.5s): Flat lay - Product components overhead
S4 (4s): Tracking shot - Product in use, profile view
S5 (2s): Slow motion - Happy customer
S6 (2s): Title card - Product name

Style: Whimsical, symmetrical, pastel
Music: Quirky instrumental
```

### 30-Second Story
```
S1 (2s): Title - "CHAPTER 1: THE PROBLEM"
S2 (4s): Symmetrical - Character with problem
S3 (0.3s): Whip pan - To product
S4 (3s): Flat lay - Product components
S5 (5s): Tracking - Character using product
S6 (3s): Slow motion - Transformation
S7 (4s): Ensemble - Multiple customers
S8 (3s): Miniature - Product in whimsical world
S9 (1.5s): Title - "CHAPTER 2: HAPPINESS"
S10 (4s): Symmetrical - Final product shot
S11 (2.2s): Title - Product name

Style: Storybook narrative
Music: Melancholic but uplifting
```

---

## Key Takeaways

1. **Perfect symmetry**: Everything centered and balanced
2. **Pastel colors**: Soft, muted, coordinated palette
3. **Flat perspective**: Frontal, stage-like compositions
4. **Whimsical details**: Handcrafted, storybook aesthetic
5. **Slow motion**: For emotional or comedic emphasis
6. **Tracking shots**: Smooth, lateral movement
7. **Typography**: Clean, centered, custom fonts
8. **Miniatures**: Toy-like, fantastical worlds
9. **Deadpan humor**: Subtle, understated comedy
10. **Meticulous detail**: Every element carefully placed

---

## When to Use Wes Anderson Style

**Good for**:
- Lifestyle products
- Artisanal/handcrafted brands
- Quirky, unique products
- Nostalgic brands
- Stationery, design products
- Fashion (vintage/retro)
- Food (bakery, cafe)
- Hotels, hospitality

**Avoid for**:
- Tech products (too whimsical)
- Serious/corporate brands
- Action/sports products
- Aggressive/edgy brands
- Medical/pharmaceutical
- Heavy machinery

---

## Technical Requirements

### For Symmetrical Shots
```yaml
composition: centered, balanced
camera: locked off, level
framing: precise, measured
lighting: soft, even
```

### For Flat Lays
```yaml
camera_angle: 90° overhead
arrangement: geometric, organized
lighting: soft, shadowless
background: solid color or texture
```

### For Tracking Shots
```yaml
movement: smooth, horizontal
speed: matches subject
framing: profile, centered
stabilization: perfect (gimbal or dolly)
```

---

## Comparison with Other Styles

| Element | Wes Anderson | Tarantino | Edgar Wright |
|---------|-------------|-----------|--------------|
| Symmetry | Constant | Rare | Frequent |
| Colors | Pastel | Saturated | Saturated |
| Pacing | Deliberate | Varied | Very fast |
| Comedy | Deadpan | Dialogue | Visual |
| Camera | Smooth | Varied | Energetic |
| Detail | Meticulous | Stylized | Rapid |

---

## Summary

Wes Anderson's style is perfect for brands that want a whimsical, handcrafted, storybook aesthetic. It's ideal for products that benefit from careful presentation and nostalgic charm.
