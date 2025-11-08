# Temporal Narrative Techniques

## Overview

Temporal narratives are cinematic storytelling techniques that manipulate the chronological order of events to create specific emotional, dramatic, or thematic effects.

---

## 1. Flashback (Past)

### Definition
A scene that interrupts the present timeline to show events from the past.

### Purpose
- Reveal backstory
- Explain character motivation
- Create dramatic irony
- Build mystery

### Visual Indicators

#### Color Grading
```yaml
present:
  saturation: 100%
  temperature: neutral
  contrast: normal

past:
  saturation: 70-85%
  temperature: warm (sepia) or cool (blue)
  contrast: slightly reduced
  grain: optional film grain
```

#### Aspect Ratio
```yaml
present: 16:9 (full frame)
past: 4:3 (letterboxed) or 2.35:1 (cinematic)
```

#### Transition Techniques
- **Dissolve**: Slow fade (0.5-1.0s) - gentle, nostalgic
- **Ripple/Blur**: Dream-like, memory quality
- **Match Cut**: Object/action triggers memory
- **Audio Bridge**: Sound from past bleeds into present

### Screenplay Structure
```json
{
  "scene_id": "S2_FLASHBACK_CHILDHOOD",
  "timeline": "past",
  "timeline_offset": "-20 years",
  "visual_style": {
    "color_grade": "warm_sepia",
    "saturation": 75,
    "grain": "16mm_film",
    "aspect_ratio": "4:3"
  },
  "transition_from_present": {
    "type": "dissolve",
    "duration": 0.8,
    "trigger": "character_looks_at_photo"
  }
}
```

### Generation Strategy
```yaml
method: separate_video_with_post_processing
steps:
  1. Generate present scene normally
  2. Generate past scene with modified prompt:
     - Add "vintage photograph aesthetic"
     - Add "warm sepia tones"
     - Add "soft focus, nostalgic"
  3. Apply color grading in post:
     - Reduce saturation to 75%
     - Add warm temperature shift
     - Add subtle film grain
  4. Apply dissolve transition
```

### Prompt Template
```
PRESENT SCENE:
[Standard prompt with current lighting and color]

PAST SCENE (FLASHBACK):
Vintage photograph aesthetic, warm sepia tones, soft focus. 
[Scene description]. Nostalgic lighting, slightly desaturated. 
Film grain texture. Shot on 35mm film stock.
```

### Examples

#### Example 1: Triggered by Object
```
Present: Character finds old watch in drawer
Transition: Dissolve (0.8s) triggered by close-up of watch
Past: Young character receiving watch as gift (sepia tone)
```

#### Example 2: Triggered by Dialogue
```
Present: Character says "I remember when..."
Transition: Ripple effect (0.5s)
Past: Memory of event being described (desaturated, soft)
```

---

## 2. Flash-forward (Future)

### Definition
A scene that jumps ahead in time to show future events or potential outcomes.

### Purpose
- Create tension/anticipation
- Show consequences
- Establish stakes
- Create mystery

### Visual Indicators

#### Color Grading
```yaml
present:
  saturation: 100%
  temperature: neutral
  contrast: normal

future:
  saturation: 110-120% (hyper-real)
  temperature: cool (blue/cyan)
  contrast: high
  sharpness: increased
```

#### Aspect Ratio
```yaml
present: 16:9
future: 2.35:1 (ultra-wide, cinematic)
```

#### Transition Techniques
- **Smash Cut**: Sudden, jarring (0.2s) - shocking
- **White Flash**: Bright flash (0.3s) - prophetic
- **Quick Zoom**: Fast zoom in/out - disorienting
- **Glitch Effect**: Digital distortion - uncertain future

### Screenplay Structure
```json
{
  "scene_id": "S3_FLASHFORWARD_CONSEQUENCE",
  "timeline": "future",
  "timeline_offset": "+2 days",
  "visual_style": {
    "color_grade": "cool_cyan",
    "saturation": 115,
    "contrast": "high",
    "sharpness": "enhanced",
    "aspect_ratio": "2.35:1"
  },
  "transition_from_present": {
    "type": "white_flash",
    "duration": 0.3,
    "trigger": "character_makes_decision"
  }
}
```

### Generation Strategy
```yaml
method: separate_video_with_post_processing
steps:
  1. Generate present scene normally
  2. Generate future scene with modified prompt:
     - Add "hyper-realistic, sharp detail"
     - Add "cool cyan color palette"
     - Add "high contrast, dramatic"
  3. Apply color grading in post:
     - Increase saturation to 115%
     - Add cool temperature shift
     - Increase contrast and sharpness
  4. Apply flash transition
```

### Prompt Template
```
PRESENT SCENE:
[Standard prompt with current lighting and color]

FUTURE SCENE (FLASH-FORWARD):
Hyper-realistic, sharp detail, cool cyan color palette. 
[Scene description]. High contrast, dramatic lighting. 
Crisp, ultra-modern aesthetic. Shot on high-end digital cinema camera.
```

### Examples

#### Example 1: Consequence Preview
```
Present: Character about to make risky decision
Transition: White flash (0.3s)
Future: Consequence of that decision (high contrast, cool tones)
Transition: Smash cut back to present
```

#### Example 2: Multiple Futures
```
Present: Character at crossroads
Transition: Quick zoom (0.2s)
Future A: Outcome if choice A (cyan tones)
Transition: Glitch effect (0.3s)
Future B: Outcome if choice B (magenta tones)
Transition: Smash cut back to present
```

---

## 3. Non-linear / Fractured Narrative

### Definition
Story told out of chronological order, jumping between multiple time periods.

### Purpose
- Create mystery/puzzle
- Reveal information strategically
- Show cause and effect non-linearly
- Create thematic connections

### Visual Indicators

#### Timeline Color Coding
```yaml
timeline_1_past:
  color_grade: warm_amber
  saturation: 80%
  
timeline_2_present:
  color_grade: neutral
  saturation: 100%
  
timeline_3_future:
  color_grade: cool_blue
  saturation: 110%
```

#### Text Overlays
```yaml
style: minimal, elegant
examples:
  - "3 DAYS EARLIER"
  - "2 HOURS LATER"
  - "THE BEGINNING"
  - "NOW"
position: bottom-left or top-right
duration: 2-3 seconds
fade: in 0.3s, out 0.5s
```

### Screenplay Structure
```json
{
  "narrative_structure": "non_linear",
  "timelines": [
    {
      "id": "past",
      "offset": "-5 years",
      "visual_style": "warm_amber",
      "scenes": ["S1", "S4", "S7"]
    },
    {
      "id": "present",
      "offset": "0",
      "visual_style": "neutral",
      "scenes": ["S2", "S5", "S8"]
    },
    {
      "id": "future",
      "offset": "+1 year",
      "visual_style": "cool_blue",
      "scenes": ["S3", "S6", "S9"]
    }
  ],
  "scene_order": ["S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8", "S9"],
  "chronological_order": ["S1", "S4", "S7", "S2", "S5", "S8", "S3", "S6", "S9"]
}
```

### Generation Strategy
```yaml
method: separate_videos_with_consistent_styling
steps:
  1. Define visual style for each timeline
  2. Generate all scenes with timeline-specific prompts
  3. Apply consistent color grading per timeline
  4. Add text overlays for time indicators
  5. Edit in non-chronological order
```

### Transition Techniques
```yaml
between_timelines:
  - match_cut (thematic connection)
  - smash_cut (dramatic contrast)
  - dissolve (gentle shift)
  - text_overlay_transition (clear indicator)
```

### Examples

#### Example 1: Three-Timeline Product Story
```
Structure: 15s ad showing product evolution

Timeline 1 (Past - 5 years ago):
- S1 (3s): Founder sketching initial design (warm, sepia)
- Text: "5 YEARS AGO"

Timeline 2 (Present):
- S2 (3s): Product in use today (neutral, vibrant)
- Text: "TODAY"

Timeline 3 (Future - 1 year):
- S3 (3s): Next-gen product concept (cool, futuristic)
- Text: "COMING SOON"

Timeline 1 (Past):
- S4 (2s): First prototype (warm, sepia)

Timeline 2 (Present):
- S5 (2s): Customer testimonial (neutral)

Timeline 3 (Future):
- S6 (2s): Vision of future (cool, sleek)

Effect: Shows journey from concept to future vision
```

---

## 4. Parallel Timeline

### Definition
Multiple timelines shown simultaneously or intercut rapidly.

### Purpose
- Show simultaneous events
- Create tension through cross-cutting
- Compare/contrast different time periods
- Build to convergence point

### Visual Indicators

#### Split Screen
```yaml
layout: side_by_side or quad
border: thin white line (2px)
timelines:
  left: past
  right: present
```

#### Rapid Intercutting
```yaml
pattern: A-B-A-B-A-B
cut_duration: 1-2 seconds each
acceleration: cuts get faster toward climax
```

#### Color Coding
```yaml
timeline_a: warm tones
timeline_b: cool tones
convergence: neutral (when timelines meet)
```

### Screenplay Structure
```json
{
  "narrative_structure": "parallel_timeline",
  "timelines": [
    {
      "id": "timeline_a",
      "description": "Character's morning routine",
      "visual_style": "warm_natural"
    },
    {
      "id": "timeline_b", 
      "description": "Product being manufactured",
      "visual_style": "cool_industrial"
    }
  ],
  "intercut_pattern": [
    {"timeline": "a", "scene": "S1A", "duration": 2.0},
    {"timeline": "b", "scene": "S1B", "duration": 2.0},
    {"timeline": "a", "scene": "S2A", "duration": 1.5},
    {"timeline": "b", "scene": "S2B", "duration": 1.5},
    {"timeline": "a", "scene": "S3A", "duration": 1.0},
    {"timeline": "b", "scene": "S3B", "duration": 1.0}
  ],
  "convergence": {
    "scene": "S4_CONVERGENCE",
    "description": "Character receives product"
  }
}
```

### Generation Strategy
```yaml
method: separate_videos_for_each_timeline
steps:
  1. Generate all Timeline A scenes with consistent style
  2. Generate all Timeline B scenes with consistent style
  3. Edit in intercut pattern
  4. Optional: Create split-screen composite
  5. Build to convergence scene
```

### Examples

#### Example 1: Product Journey
```
Timeline A: Customer's day (warm, natural)
- S1A (2s): Waking up, checking phone
- S2A (1.5s): Commuting to work
- S3A (1s): Arriving at office

Timeline B: Product creation (cool, industrial)
- S1B (2s): Raw materials being processed
- S2B (1.5s): Assembly line
- S3B (1s): Quality control

Convergence:
- S4 (3s): Product delivered to customer (neutral)

Effect: Shows parallel journey of customer and product
```

#### Example 2: Before/After Split Screen
```
Split Screen Layout:
Left: Life before product (desaturated, chaotic)
Right: Life after product (vibrant, organized)

Both timelines play simultaneously showing contrast
Duration: 8s total
```

---

## 5. Bookend Structure

### Definition
Story begins and ends in same time/place, with main narrative as flashback.

### Purpose
- Frame the story
- Create circular narrative
- Provide context for flashback
- Emotional payoff

### Visual Indicators
```yaml
opening_frame:
  style: neutral or slightly desaturated
  text: "PRESENT DAY" or location/time

main_narrative:
  style: varies (often more vibrant)
  text: "X DAYS/YEARS EARLIER"

closing_frame:
  style: matches opening
  text: none (audience recognizes return)
```

### Screenplay Structure
```json
{
  "narrative_structure": "bookend",
  "scenes": [
    {
      "id": "S1_OPENING_FRAME",
      "timeline": "present",
      "description": "Character in current situation"
    },
    {
      "id": "S2_FLASHBACK_START",
      "timeline": "past",
      "transition": "dissolve",
      "text_overlay": "3 MONTHS EARLIER"
    },
    {
      "id": "S3_S8_MAIN_STORY",
      "timeline": "past",
      "description": "Main narrative events"
    },
    {
      "id": "S9_CLOSING_FRAME",
      "timeline": "present",
      "description": "Return to opening, now with context",
      "transition": "dissolve"
    }
  ]
}
```

---

## Integration with Cinema Pipeline

### Screenplay Schema Extension

Add temporal metadata to scenes:

```python
class TemporalMetadata(BaseModel):
    timeline: Literal["past", "present", "future"]
    timeline_offset: str  # e.g., "-5 years", "+2 days"
    visual_style: str  # e.g., "warm_sepia", "cool_cyan"
    text_overlay: Optional[str]  # e.g., "3 DAYS EARLIER"
    
class Scene(BaseModel):
    scene_id: str
    temporal: Optional[TemporalMetadata]
    # ... existing fields
```

### Post-Production Pipeline

Add temporal effects processor:

```python
class TemporalEffectsProcessor:
    """Apply timeline-specific visual effects"""
    
    def apply_timeline_style(self, video_path, timeline: str):
        if timeline == "past":
            return self.apply_flashback_style(video_path)
        elif timeline == "future":
            return self.apply_flashforward_style(video_path)
        return video_path
    
    def apply_flashback_style(self, video_path):
        # Reduce saturation to 75%
        # Add warm temperature shift
        # Add film grain
        # Optional: Add vignette
        pass
    
    def apply_flashforward_style(self, video_path):
        # Increase saturation to 115%
        # Add cool temperature shift
        # Increase contrast and sharpness
        pass
```

### Knowledge Base Integration

The screenplay writer agent should:

1. **Reference this knowledge base** when creating temporal narratives
2. **Add temporal metadata** to scenes
3. **Specify visual styles** per timeline
4. **Plan transitions** between timelines
5. **Add text overlays** for clarity

---

## Prompt Engineering for Temporal Styles

### Flashback Prompts
```
Base prompt: [scene description]

Add modifiers:
- "Vintage photograph aesthetic"
- "Warm sepia tones, slightly desaturated"
- "Soft focus, nostalgic lighting"
- "Film grain texture, 35mm film stock"
- "Gentle vignette, dreamy quality"
```

### Flash-forward Prompts
```
Base prompt: [scene description]

Add modifiers:
- "Hyper-realistic, ultra-sharp detail"
- "Cool cyan color palette, futuristic"
- "High contrast, dramatic lighting"
- "Crisp, modern aesthetic"
- "Shot on high-end digital cinema camera"
```

### Parallel Timeline Prompts
```
Timeline A (warm):
- "Natural warm lighting, golden hour"
- "Organic, lived-in environment"
- "Soft shadows, comfortable atmosphere"

Timeline B (cool):
- "Cool industrial lighting, blue tones"
- "Clean, modern environment"
- "Hard shadows, precise atmosphere"
```

---

## Best Practices

### 1. Consistency Within Timelines
- Use same visual style for all scenes in a timeline
- Maintain color grading consistency
- Use reference images for character consistency

### 2. Clear Transitions
- Make timeline shifts obvious (unless intentionally ambiguous)
- Use text overlays for first occurrence of each timeline
- Use consistent transition types per timeline

### 3. Visual Hierarchy
- Present should be most "normal" looking
- Past should feel nostalgic/softer
- Future should feel heightened/sharper

### 4. Don't Overuse
- Temporal shifts should serve the story
- Too many timelines can confuse
- Keep it simple for short-form content (< 30s)

### 5. Test Audience Comprehension
- Ensure timeline shifts are clear
- Text overlays help but shouldn't be crutch
- Visual style should communicate timeline

---

## Examples for Different Video Lengths

### 15-Second Ad
```
Structure: Simple bookend
- S1 (2s): Present - Character with problem
- S2 (8s): Flashback - Discovery of solution
- S3 (3s): Present - Character happy with solution
- S4 (2s): Product reveal

Timelines: 2 (present + past)
Transitions: 2 dissolves
```

### 30-Second Ad
```
Structure: Three-timeline narrative
- S1 (3s): Past - Origin story
- S2 (4s): Present - Current use
- S3 (3s): Future - Vision
- S4-S6 (12s): Intercut all three timelines
- S7 (5s): Convergence - Product reveal
- S8 (3s): Call to action

Timelines: 3 (past + present + future)
Transitions: Multiple, color-coded
```

### 60-Second Ad
```
Structure: Non-linear narrative
- Complex story told out of order
- 4-5 timelines
- Multiple convergence points
- Puzzle-like structure

Timelines: 4-5
Transitions: Varied, strategic
```

---

## Summary

Temporal narratives are powerful tools for:
- Creating emotional depth
- Building mystery and tension
- Showing cause and effect
- Connecting themes across time

Key implementation points:
1. Define clear visual styles per timeline
2. Use consistent color grading
3. Add text overlays for clarity
4. Plan transitions carefully
5. Integrate with post-production pipeline
6. Reference this knowledge base in screenplay generation
