# In Medias Res

## Definition

Latin for "in the middle of things." Story starts in the middle of the action, then goes back to show how we got there, then continues forward.

---

## Famous Examples

- **The Odyssey** - Homer (original example)
- **Breaking Bad** - TV series (cold opens)
- **Mission: Impossible** films - Action opening
- **The Usual Suspects** - Interrogation frame
- Most action movie trailers

---

## Purpose

- Hook audience immediately with exciting moment
- Create questions (how did we get here?)
- Build anticipation
- Skip boring setup
- Promise excitement to come

---

## Structure

```
Timeline: A → B → C → D → E (actual chronology)
Presentation: C → A → B → D → E

Scene 1: Exciting middle moment (C) - "The Hook"
Scene 2: Go back to beginning (A)
Scene 3: Build up (B)
Scene 4: Return to hook moment (C) - "We're back"
Scene 5: Continue to resolution (D → E)
```

---

## Visual Indicators

### Opening Hook
```yaml
style: high energy, dramatic
duration: 5-10 seconds
purpose: grab attention
content: action, conflict, or mystery
```

### Transition to Beginning
```yaml
text_overlay: "24 HOURS EARLIER" or "LET'S REWIND"
transition: smash cut, record scratch, or freeze frame
color_shift: optional (hook in one tone, flashback in another)
```

### Return to Hook
```yaml
text_overlay: "NOW" or "BACK TO..."
visual_match: recreate exact moment from opening
audience_recognition: "Oh, this is where we started"
```

---

## For Short-Form (15-30s)

### 15-Second Example
```yaml
structure:
  - hook (3s): Character in exciting situation with product
    time: "THE RESULT"
  
  - transition (0.5s): Record scratch + text "REWIND"
  
  - flashback (6s): Character discovers product, quick setup
    time: "THE BEGINNING"
  
  - return (3s): Back to exciting moment, now makes sense
    time: "NOW"
  
  - payoff (2.5s): Product name + tagline

total: 15s
effect: Hook audience, explain quickly, deliver payoff
```

### 30-Second Example
```yaml
structure:
  - hook (5s): Dramatic moment - character in crisis with product
    time: "5 MINUTES FROM NOW"
  
  - transition (1s): Freeze frame + text "LET'S GO BACK"
  
  - setup (8s): Character's normal day, problem emerges
    time: "THIS MORNING"
  
  - discovery (4s): Character finds product
    time: "10 MINUTES AGO"
  
  - transition (0.5s): Text "AND NOW..."
  
  - return (5s): Back to opening crisis, product saves the day
    time: "NOW"
  
  - resolution (4s): Happy ending
  
  - final_card (2.5s): Product name + tagline

total: 30s
effect: Full narrative arc with exciting opening
```

---

## Screenplay Schema

```json
{
  "narrative_structure": "in_medias_res",
  "hook_scene": "S3_CRISIS",
  "scenes": [
    {
      "scene_id": "S3_CRISIS",
      "chronological_order": 3,
      "presentation_order": 1,
      "time_marker": "5 MINUTES FROM NOW",
      "description": "Hook - exciting moment",
      "is_hook": true
    },
    {
      "scene_id": "S1_BEGINNING",
      "chronological_order": 1,
      "presentation_order": 2,
      "time_marker": "THIS MORNING",
      "description": "Flashback to beginning"
    },
    {
      "scene_id": "S2_DISCOVERY",
      "chronological_order": 2,
      "presentation_order": 3,
      "time_marker": "10 MINUTES AGO",
      "description": "Character finds product"
    },
    {
      "scene_id": "S3_CRISIS_RETURN",
      "chronological_order": 3,
      "presentation_order": 4,
      "time_marker": "NOW",
      "description": "Return to hook moment",
      "matches_scene": "S3_CRISIS"
    },
    {
      "scene_id": "S4_RESOLUTION",
      "chronological_order": 4,
      "presentation_order": 5,
      "time_marker": "NOW",
      "description": "Resolution"
    }
  ]
}
```

---

## Types of Hooks

### Action Hook
```yaml
content: Physical action, chase, fight
energy: high
purpose: excitement
example: "Character running from something"
```

### Mystery Hook
```yaml
content: Strange situation, unanswered question
energy: medium
purpose: curiosity
example: "Character in unexpected place"
```

### Conflict Hook
```yaml
content: Argument, confrontation, problem
energy: medium-high
purpose: drama
example: "Character facing crisis"
```

### Success Hook
```yaml
content: Character achieving goal
energy: positive
purpose: aspiration
example: "Character celebrating with product"
```

---

## Transition Techniques

### Record Scratch
```yaml
audio: music stops abruptly
visual: freeze frame
text: "WAIT, LET'S REWIND"
style: comedic, self-aware
```

### Smash Cut
```yaml
audio: sudden silence or change
visual: hard cut to black or different scene
text: "24 HOURS EARLIER"
style: dramatic
```

### Reverse Motion
```yaml
audio: reverse sound effects
visual: footage plays backwards briefly
text: "LET'S GO BACK"
style: literal, clear
```

### Dissolve
```yaml
audio: music transition
visual: slow dissolve
text: "EARLIER THAT DAY"
style: smooth, traditional
```

---

## When to Use

**Good for**:
- Action-oriented products
- Grabbing attention quickly
- Social media (hook in first 3 seconds)
- Products with dramatic results
- Storytelling ads
- Transformation narratives

**Avoid for**:
- Very short content (<10s) - not enough time
- Complex products needing explanation
- Calm, meditative brands
- When chronology is important to understand

---

## Tips

1. **Strong hook**: Opening must be genuinely exciting
2. **Quick flashback**: Don't spend too long in the past
3. **Clear return**: Audience must recognize when we're back
4. **Payoff**: Resolution should be worth the wait
5. **Not too complex**: Keep it simple for short-form

---

## Variations

### Cold Open (TV Style)
```yaml
structure: Hook → Title Card → Beginning → Continue
duration: Hook is 30-60s, then title/credits
purpose: Grab attention before credits
```

### Teaser Hook
```yaml
structure: Brief hook (3s) → Full story → Return to hook
duration: Very short hook, just a glimpse
purpose: Intrigue without revealing too much
```

### Multiple Hooks
```yaml
structure: Hook 1 → Flashback → Hook 2 → Continue
duration: Several exciting moments shown upfront
purpose: Promise multiple payoffs
```

---

## Comparison

| Structure | Opening | Complexity | Hook Strength |
|-----------|---------|------------|---------------|
| Linear | Beginning | Simple | None |
| In Medias Res | Middle | Medium | Strong |
| Flashback | Present | Medium | Medium |
| Reverse | End | High | Very Strong |

---

## Common Mistakes

❌ **Weak hook**: Opening isn't actually exciting
❌ **Too long in past**: Spending too much time in flashback
❌ **Confusing return**: Audience doesn't realize we're back
❌ **Anticlimactic**: Resolution doesn't pay off the hook
❌ **Overused**: Every video doesn't need this structure

✅ **Strong hook**: Genuinely exciting or intriguing opening
✅ **Quick flashback**: Just enough context
✅ **Clear return**: Visual or audio cue we're back
✅ **Satisfying payoff**: Resolution delivers on promise
✅ **Strategic use**: Use when it serves the story
