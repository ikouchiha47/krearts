# Cinema Knowledge Base

## Overview

This knowledge base contains reference material for video generation, organized by category. Each category addresses a different aspect of filmmaking and storytelling.

---

## Directory Structure

```
knowledge/
├── README.md (this file)
│
├── narrative-structures/          # HOW the story is organized
│   ├── index.md
│   ├── linear/
│   ├── non-linear/
│   ├── circular/
│   ├── parallel/
│   └── episodic/
│
├── transitions/                    # HOW to move between scenes (editing)
│   └── vocabulary.md
│
├── cinematic-styles/              # VISUAL presentation techniques
│   ├── README.md
│   ├── temporal-narratives.md
│   ├── camera-movements.md
│   ├── lighting-styles.md
│   └── ...
│
├── director-styles/               # PERSONAL signatures (combinations)
│   ├── index.md
│   ├── tarantino.md
│   ├── edgar-wright.md
│   └── ...
│
└── gemini/                        # API-specific prompting guides
    ├── image-prompting.md
    ├── video-prompting.md
    └── video-gen-workflow.md
```

---

## Categories Explained

### 1. Narrative Structures
**What it is**: The order and organization of story events

**Examples**:
- Linear (A→B→C→D)
- Flashback (C→A→B→D)
- Reverse (D→C→B→A)
- In Medias Res (C→A→B→D→E)

**Use when**: Planning the story structure

**File**: `narrative-structures/index.md`

---

### 2. Transitions
**What it is**: Editing techniques to move between scenes

**Examples**:
- Match cut
- Jump cut
- Dissolve
- Whip pan
- Smash cut

**Use when**: Connecting scenes in post-production

**File**: `transitions/vocabulary.md`

---

### 3. Cinematic Styles
**What it is**: Visual and technical presentation techniques

**Examples**:
- Camera movements (dolly, tracking, crane)
- Lighting styles (three-point, high-key, low-key)
- Color palettes (warm, cool, monochrome)
- Shot types (wide, close-up, POV)

**Use when**: Defining visual look and feel

**File**: `cinematic-styles/README.md`

---

### 4. Director Styles
**What it is**: Personal signatures combining multiple elements

**Examples**:
- Tarantino: Non-linear + dialogue + stylized violence + retro music
- Edgar Wright: Rapid editing + visual comedy + match cuts
- Wes Anderson: Symmetry + pastels + whimsy + deadpan

**Use when**: Wanting a specific director's aesthetic

**File**: `director-styles/index.md`

---

### 5. Gemini API Guides
**What it is**: Technical documentation for Imagen/Veo APIs

**Examples**:
- Image prompting best practices
- Video generation workflow
- Prompt engineering tips

**Use when**: Writing prompts for generation

**File**: `gemini/`

---

## How They Work Together

### Example: Creating a 30-second ad

1. **Choose Narrative Structure** (narrative-structures/)
   - Decision: In Medias Res (hook audience quickly)
   - Result: Start with exciting moment, flashback, return

2. **Choose Transitions** (transitions/)
   - Decision: Record scratch to flashback, match cut to return
   - Result: Clear, comedic transitions

3. **Choose Cinematic Style** (cinematic-styles/)
   - Decision: High-key lighting, handheld camera, saturated colors
   - Result: Energetic, modern look

4. **Optional: Director Style** (director-styles/)
   - Decision: Edgar Wright-inspired rapid editing
   - Result: Quick cuts, visual comedy

5. **Generate with Gemini** (gemini/)
   - Use: Prompting guides to write effective prompts
   - Result: High-quality generated content

---

## Quick Decision Tree

```
START: What do I need?

├─ Story organization?
│  └─ Go to: narrative-structures/
│
├─ Scene connections?
│  └─ Go to: transitions/
│
├─ Visual look?
│  └─ Go to: cinematic-styles/
│
├─ Specific director aesthetic?
│  └─ Go to: director-styles/
│
└─ API/prompting help?
   └─ Go to: gemini/
```

---

## For AI Agents

### ScriptWriter Agent
**Should reference**:
- `narrative-structures/` - for story organization
- `transitions/vocabulary.md` - for scene connections
- `director-styles/` - if user requests specific style

**Should NOT reference**:
- `gemini/` - that's for Enhancer

### Enhancer Agent
**Should reference**:
- `cinematic-styles/` - for visual details
- `gemini/` - for prompt engineering
- `transitions/vocabulary.md` - for generation methods

**Should NOT reference**:
- `narrative-structures/` - that's already decided

---

## Common Confusions

### ❌ "Non-linear editing" = "Non-linear narrative"
**Wrong**: These are different things
- Non-linear editing: How you cut footage (software, techniques)
- Non-linear narrative: Story told out of order

### ❌ "Tarantino style" = "Non-linear narrative"
**Wrong**: Tarantino style includes many elements
- Non-linear narrative is ONE element
- Also includes: dialogue, violence, music, etc.

### ❌ "Flashback" is a transition
**Wrong**: Flashback is a narrative structure
- Transition: HOW you move between scenes (dissolve, cut)
- Flashback: WHAT you're showing (past event)

### ❌ "Match cut" is a narrative structure
**Wrong**: Match cut is an editing technique
- Narrative structure: Story organization
- Match cut: Specific type of transition

---

## Correct Usage

### ✅ Flashback (narrative) + Dissolve (transition)
```yaml
narrative_structure: flashback
transition_technique: dissolve
visual_style: desaturated
```

### ✅ In Medias Res (narrative) + Smash Cut (transition) + Edgar Wright (director style)
```yaml
narrative_structure: in_medias_res
transition_technique: smash_cut
director_style: edgar_wright
visual_elements: rapid_editing, crash_zoom
```

### ✅ Linear (narrative) + Match Cut (transition) + Film Noir (cinematic style)
```yaml
narrative_structure: linear
transition_technique: match_cut
cinematic_style: film_noir
lighting: low_key
color: black_and_white
```

---

## Integration with Pipeline

### Screenplay Schema
```python
class Screenplay(BaseModel):
    # Narrative structure
    narrative_structure: NarrativeStructure
    
    # Scenes with transitions
    scenes: List[Scene]
    
    # Optional director style
    director_style: Optional[DirectorStyle]
    
class Scene(BaseModel):
    scene_id: str
    
    # Cinematic style for this scene
    visual_style: VisualStyle
    
    # Transition to next scene
    transition: Transition
```

---

## Contributing

### Adding New Content

1. **Identify category**: Which folder does it belong in?
2. **Check for overlap**: Does it already exist?
3. **Create file**: Follow template for that category
4. **Update index**: Add to relevant index.md
5. **Update this README**: If adding new category

### Maintaining Separation

- Keep categories distinct
- Cross-reference when needed
- Don't duplicate content
- Use clear examples

---

## Summary

| Category | What | When | Example |
|----------|------|------|---------|
| **Narrative Structures** | Story order | Planning story | Flashback |
| **Transitions** | Scene connections | Editing | Match cut |
| **Cinematic Styles** | Visual look | Defining aesthetic | Film noir |
| **Director Styles** | Personal signature | Specific aesthetic | Tarantino |
| **Gemini Guides** | API usage | Writing prompts | Prompt tips |

---

## Questions?

- **"What's the difference between X and Y?"** - See "Common Confusions" above
- **"Which category for my need?"** - See "Quick Decision Tree" above
- **"How do they work together?"** - See "How They Work Together" above
