# Reverse Chronology

## Definition

Story told backwards, starting with the ending and moving towards the beginning. Each scene shows what happened before the previous scene.

---

## Famous Examples

- **Memento** (2000) - Christopher Nolan
- **Irreversible** (2002) - Gaspar Noé  
- **5x2** (2004) - François Ozon
- **Betrayal** (1983) - Harold Pinter play

---

## Purpose

- Create mystery (why did this happen?)
- Show consequences before causes
- Force audience to piece together story
- Subvert expectations
- Emotional impact (knowing the end changes how we see beginning)

---

## Structure

```
Timeline: A → B → C → D → E (actual chronology)
Presentation: E → D → C → B → A (reverse order)

Scene 1: The ending (E)
Scene 2: What led to ending (D)
Scene 3: What led to that (C)
Scene 4: Earlier events (B)
Scene 5: The beginning (A)
```

---

## Visual Indicators

### Text Overlays
```yaml
style: countdown or time markers
examples:
  - "10 MINUTES EARLIER"
  - "2 HOURS BEFORE"
  - "THE DAY BEFORE"
  - "ONE WEEK AGO"
placement: beginning of each scene
```

### Color Grading
```yaml
progression: scenes get warmer/brighter as we go back
present (ending): cool, desaturated
past (beginning): warm, saturated
reason: emotional journey from dark to light
```

### Transitions
```yaml
between_scenes:
  - fade_to_black: clear separation
  - reverse_motion: brief reverse footage
  - time_card: explicit time marker
```

---

## For Short-Form (30-60s)

### 30-Second Example
```yaml
structure:
  - scene_1 (5s): Ending - Character happy with product
    time: "NOW"
  
  - transition (0.5s): Fade to black + text "10 MINUTES EARLIER"
  
  - scene_2 (6s): Character using product
    time: "10 MINUTES EARLIER"
  
  - transition (0.5s): Fade to black + text "1 HOUR EARLIER"
  
  - scene_3 (6s): Character discovering product
    time: "1 HOUR EARLIER"
  
  - transition (0.5s): Fade to black + text "THIS MORNING"
  
  - scene_4 (8s): Character struggling with problem
    time: "THIS MORNING"
  
  - final_card (3s): Product name + tagline

total: 30s
effect: Audience sees solution first, then understands problem
```

---

## Screenplay Schema

```json
{
  "narrative_structure": "reverse_chronology",
  "scenes": [
    {
      "scene_id": "S1_ENDING",
      "chronological_order": 5,
      "presentation_order": 1,
      "time_marker": "NOW",
      "description": "Character happy with product"
    },
    {
      "scene_id": "S2_BEFORE_END",
      "chronological_order": 4,
      "presentation_order": 2,
      "time_marker": "10 MINUTES EARLIER",
      "description": "Character using product"
    },
    {
      "scene_id": "S3_DISCOVERY",
      "chronological_order": 3,
      "presentation_order": 3,
      "time_marker": "1 HOUR EARLIER",
      "description": "Character discovers product"
    },
    {
      "scene_id": "S4_PROBLEM",
      "chronological_order": 2,
      "presentation_order": 4,
      "time_marker": "THIS MORNING",
      "description": "Character has problem"
    }
  ]
}
```

---

## When to Use

**Good for**:
- Mystery/intrigue
- Showing transformation
- Subverting expectations
- Creating "aha" moments
- Products that solve problems

**Avoid for**:
- Simple, straightforward stories
- Very short content (<20s)
- Audiences needing clarity
- Complex products requiring explanation

---

## Tips

1. **Clear time markers**: Audience must know they're going backwards
2. **Strong ending/opening**: Start with compelling result
3. **Logical progression**: Each scene should raise questions about previous
4. **Not too many jumps**: 3-5 scenes maximum for short-form
5. **Satisfying beginning**: The "ending" (chronological beginning) should pay off

---

## Comparison

| Structure | Order | Complexity | Audience Effort |
|-----------|-------|------------|-----------------|
| Linear | A→B→C→D→E | Simple | Low |
| Flashback | C→A→B→D→E | Medium | Medium |
| Reverse | E→D→C→B→A | High | High |
| Fractured | C→E→A→D→B | Very High | Very High |
