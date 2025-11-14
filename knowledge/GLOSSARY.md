# Glossary

Quick reference guide for all knowledge base categories and their purposes.
---

# Knowledge Base Definitions

## A. Narrative Structures
**Purpose**: Defines the temporal organization of story events

**What it controls**: Timeline arrangement, story phases, dramatic arcs, turning points

**Categories**:
- Linear: Chronological storytelling (Freytag's Pyramid, Three-Act, Five-Act, Hero's Journey)
- Non-Linear: Time manipulation (In Medias Res, Pulp Fiction, Memento, Bookend)
- Circular: Story returns to starting point
- Parallel: Multiple storylines simultaneously
- Episodic: Self-contained segments

**Location**: `knowledge/narrative-structures/`

**When to use**: Planning overall story organization and temporal flow

---

## B. Story Writing
**Purpose**: Genre-specific writing principles, chapter mapping formulas, and story development workflows

**Location**: `knowledge/storywriting/`

**Sub-categories**:

### B1. Chapter Mapping
**Purpose**: Translates narrative structures into concrete chapter divisions

**What it controls**: Chapter counts, scaling formulas, phase distributions

**Files**:
- `storywriting/chapter-mapping/index.md`: Overview of chapter mapping concepts
- `storywriting/chapter-mapping/linear-novel-mapping.md`: Chronological structures (Freytag, Three-Act, Five-Act, Hero's Journey)
- `storywriting/chapter-mapping/non-linear-novel-mapping.md`: Non-chronological structures (In Medias Res, Pulp Fiction, Memento)
- `storywriting/chapter-mapping/novel-mapping.md`: General novel mapping guidelines

**Location**: `knowledge/storywriting/chapter-mapping/`

**When to use**: Converting abstract narrative structure into chapter plan

---

### B2. Detective (Genre-Specific)
**Purpose**: Defines genre-specific rules for fair-play mystery construction

**What it controls**: Evidence hierarchy, clue density, proof chains, fair-play rules, storytelling techniques

**Files**:
- `storywriting/detective/index.md`: Overview of detective genre requirements
- `storywriting/detective/principles.md`: Evidence hierarchy, clue density, proof chains, fair-play rules
- `storywriting/detective/storytelling-techniques.md`: Reveal patterns, interrogation strategies, tension management

**Key concepts**: Forensic evidence > financial > behavioral; ≥5 clues by midpoint; ≤40% red herrings

**Location**: `knowledge/storywriting/detective/`

**When to use**: 
- Validating detective plot logic and mystery fairness
- Crafting specific detective scenes and managing reader engagement

---

### B3. Story Writing Methods (Workflows)
**Purpose**: Planning/expansion workflows for developing a story from premise to chapters/scenes

**What it controls**: Outline granularity, expansion stages, per-step validation gates. Orthogonal to linear/non-linear narrative structures (workflows = how to build; structures = the blueprint the audience experiences).

**Files**:
- `storywriting/methods/index.md`: Overview of story development workflows
- `storywriting/methods/snowflake-method.md`: Iterative expansion from premise to full novel
- `storywriting/methods/three-act-structure-workflow.md`: Three-act development process
- `storywriting/methods/heros-journey-workflow.md`: Hero's Journey development workflow
- `storywriting/methods/save-the-cat-beat-sheet.md`: Blake Snyder's beat sheet method

**Location**: `knowledge/storywriting/methods/`

**When to use**: After choosing a narrative structure and target length, to expand a validated storyline using chapter-mapping formulas and genre rules
**Index**: storywriting/methods/index.md

---

## C. Cinematic Styles
**Purpose**: Visual and technical presentation techniques for filmmaking

**What it controls**: Camera movements, lighting styles, color palettes, shot composition

**Categories**:
- Camera movements: Dolly, tracking, crane, handheld, Steadicam
- Lighting: Three-point, high-key, low-key, chiaroscuro, natural
- Color: Warm, cool, monochrome, desaturated, saturated
- Shot types: Wide, medium, close-up, POV, Dutch angle

**Examples**:
- Film Noir: Low-key lighting + high contrast + shadows
- Documentary: Handheld + natural lighting
- Music Video: Dynamic camera + colored lighting

**Files**:
- `cinematic-styles/README.md`: Developer documentation, integration guide, contributing guidelines
- `cinematic-styles/index.md`: Quick reference for agents (decision tables, cheat sheets, prompt shortcuts)
- `cinematic-styles/camera-movements.md`: Dolly, tracking, crane, handheld techniques
- `cinematic-styles/lighting-styles.md`: Three-point, high-key, low-key, chiaroscuro
- `cinematic-styles/creative-techniques.md`: Advanced cinematography techniques
- `cinematic-styles/temporal-narratives.md`: Time-based storytelling techniques
- `cinematic-styles/director-styles.md`: Director-specific style combinations
- `cinematic-styles/QUICK-REFERENCE.md`: Additional quick lookup guide
- `cinematic-styles/INTEGRATION.md`: How to combine techniques
- `cinematic-styles/VALIDATION.md`: Style validation checklist

**Location**: `knowledge/cinematic-styles/`

**When to use**: Defining visual look and feel for scenes

---

## D. Director Styles
**Purpose**: Personal signatures combining narrative, visual, and editing elements

**What it controls**: Signature technique combinations, thematic preferences, editing rhythms, music choices

**Examples**:
- Tarantino: Non-linear + stylized violence + retro music + dialogue-heavy
- Edgar Wright: Rapid editing + visual comedy + match cuts + crash zooms
- Wes Anderson: Symmetry + pastels + whimsy + deadpan delivery

**Files**:
- `director-styles/README.md`: Overview of director style analysis
- `director-styles/tarantino.md`: Quentin Tarantino's signature techniques
- `director-styles/edgar-wright.md`: Edgar Wright's visual comedy style
- `director-styles/wes-anderson.md`: Wes Anderson's symmetrical aesthetic

**Location**: `knowledge/director-styles/`

**When to use**: Emulating a specific director's aesthetic

---

## E. Transitions
**Purpose**: Editing techniques to connect scenes

**What it controls**: Scene-to-scene connections, visual/audio bridges, pacing rhythm

**Examples**:
- Match cut: Visual similarity between shots
- Smash cut: Abrupt transition for shock
- Dissolve: Gradual fade between scenes
- Whip pan: Fast camera movement transition
- Jump cut: Temporal discontinuity

**Files**:
- `transitions/vocabulary.md`: Complete list of transition types and definitions

**Location**: `knowledge/transitions/`

**When to use**: Connecting scenes in screenplay or post-production

---

## F. Art Styles
**Purpose**: Visual art and illustration styles for image generation

**What it controls**: Artistic rendering approaches, visual aesthetics, medium types

**Examples**: Photorealistic, anime, watercolor, oil painting, sketch, pixel art, comic book

**Files**:
- `art-styles/styles.md`: Comprehensive catalog of visual art styles with descriptions

**Location**: `knowledge/art-styles/`

**When to use**: Specifying artistic style for image generation

---

## G. Layouts (Comic/Manga Panel Arrangements)
**Purpose**: Panel layout patterns and composition rules for comic book pages

**What it controls**: Panel arrangements, page layouts, visual flow, reading order

**Categories**:
- Multi-panel arrangements: horizontal, vertical, zoom-progression, fractured-overlapping
- Panel border styles: clean-sharp, ragged-dynamic, overlapping, no-borders
- Panel transitions: hard-cuts, blended-transitions, diagonal-cuts, frame-within-frame
- Layout selection rules based on narrative beats

**Files**:
- `layouts/panel_arrangements.md`: Complete catalog of panel layout patterns
- `layouts/panel_chosing_rules.md`: Guidelines for selecting appropriate layouts

**Location**: `knowledge/layouts/`

**When to use**: Designing comic book pages, storyboarding visual sequences

---

## H. Gemini API
**Purpose**: Technical documentation for Google Gemini (Imagen/Veo) API usage

**What it controls**: Prompt engineering, API parameters, workflow patterns, quality optimization

**Files**:
- `gemini/image-prompting.md`: Best practices for Gemini Image Generation prompts
- `gemini/video-prompting.md`: Best practices for Veo Video Genetaion propmts
- `gemini/video-gen-workflow.md`: Video Production workflows prompts

**When to use**: Writing prompts for image/video generation

**Location**: `knowledge/gemini/`

---

## I. Moviemaking
**Purpose**: Technical filmmaking knowledge and production techniques

**What it controls**: Production processes, technical specifications, industry standards

**Files**:
- `moviemaking/continuity.md`: Maintaining visual and narrative consistency across shots
- `moviemaking/depth_of_field.md`: Camera focus techniques and depth control
- `moviemaking/screen_direction.md`: 180-degree rule, eyeline matches, spatial continuity
- `moviemaking/screenplay-format.md`: Industry-standard screenplay formatting
- `moviemaking/shot_composition_rules.md`: Framing, rule of thirds, visual balance
- `moviemaking/storyboarding.md`: Visual planning and shot sequencing
- `moviemaking/walter_murch_rules.md`: Editing principles and cut priorities

**Location**: `knowledge/moviemaking/`

**When to use**: Understanding film production workflows, shot composition, editing principles

---

## Relationship Hierarchy

```
Story Planning:
1. Narrative Structure (abstract pattern) → "Use Freytag's Pyramid"
2. Chapter Mapping (concrete divisions) → "15 chapters: Exposition Ch 1-3, Rising Ch 4-7..."
3. Genre Principles (rules) → "≥5 clues by Ch 7, forensic evidence required"
4. Narrative Techniques (methods) → "Use slow-burn pivot in Ch 3-5"

Visual Planning:
1. Cinematic Style (visual approach) → "Film noir lighting"
2. Director Style (signature combo) → "Tarantino-style"
3. Art Style (rendering) → "Photorealistic"

Scene Execution:
1. Transitions (connections) → "Match cut between scenes"
2. Gemini API (generation) → "Prompt: dark alley, low-key lighting..."
```

---

## Quick Reference Table

| Category | Purpose | Controls | Example |
|----------|---------|----------|---------|
| **Narrative Structures** | Story timeline | Event order, phases | Freytag's Pyramid |
| **Chapter Mapping** | Medium implementation | Chapter counts, ranges | 15-ch novella formula |
| **Detective Principles** | Genre rules | Evidence, clues, fairness | ≥5 clues by midpoint |
| **Storytelling Techniques** | Storytelling methods | Reveals, tension | Slow-burn pivot |
| **Cinematic Styles** | Visual presentation | Camera, lighting, color | Film noir |
| **Director Styles** | Personal signatures | Combined techniques | Tarantino aesthetic |
| **Transitions** | Scene connections | Editing techniques | Match cut |
| **Art Styles** | Visual rendering | Artistic approach | Photorealistic |
| **Layouts** | Comic page design | Panel arrangements | Horizontal-2-panel |
| **Gemini API** | Generation tech | Prompts, parameters | Image prompting |
| **Moviemaking** | Production process | Technical workflows | Film production |

---

## Usage Guidelines

### For Detective Novel Generation:
1. Choose **Narrative Structure** (e.g., Freytag's Pyramid)
2. Apply **Chapter Mapping** (e.g., 15-chapter novella)
3. Enforce **Detective Principles** (clue density, evidence hierarchy)
4. Use **Storytelling Techniques** (slow-burn, false confirmation)

### For Comic Panel Generation:
1. Choose **Narrative Structure** (e.g., Three-Act)
2. Apply **Layouts** (panel arrangements, page composition)
3. Apply **Cinematic Styles** (lighting, camera angles)
4. Use **Art Styles** (comic book, photorealistic)
5. Apply **Gemini API** guides (image prompting)

### For Video Generation:
1. Choose **Narrative Structure** (e.g., In Medias Res)
2. Apply **Cinematic Styles** (camera movements, lighting)
3. Use **Transitions** (match cuts, dissolves)
4. Optional: **Director Style** (Edgar Wright)
5. Apply **Gemini API** guides (video prompting)

---

## Common Confusions

### ❌ Narrative Structure != Chapter Mapping
- **Narrative Structure**: Abstract pattern (Freytag's Pyramid)
- **Chapter Mapping**: Concrete implementation (Ch 1-3 = Exposition)

### ❌ Cinematic Style != Director Style
- **Cinematic Style**: Individual technique (low-key lighting)
- **Director Style**: Combination of techniques (Tarantino = non-linear + violence + music)

### ❌ Storytelling Technique != Narrative Structure
- **Narrative Structure**: Timeline organization (linear, non-linear)
- **Storytelling Technique**: Storytelling method (slow-burn pivot, false confirmation)

### ❌ Transition != Narrative Structure
- **Transition**: Editing technique (match cut, dissolve)
- **Narrative Structure**: Story organization (flashback, in medias res)

---

## File Paths Reference

```
knowledge/
├── DEFINITIONS.md (this file)
├── README.md (detailed overview)
│
├── narrative-structures/
│   ├── index.md
│   ├── linear/
│   ├── non-linear/
│   ├── circular/
│   ├── parallel/
│   └── episodic/
│
├── storywriting/
│   ├── chapter-mapping/
│   │   ├── index.md
│   │   ├── linear-novel-mapping.md
│   │   ├── non-linear-novel-mapping.md
│   │   └── novel-mapping.md
│   ├── detective/
│   │   ├── index.md
│   │   ├── principles.md
│   │   └── storytelling-techniques.md
│   ├── methods/
│   │   ├── index.md
│   │   ├── snowflake-method.md
│   │   ├── three-act-structure-workflow.md
│   │   ├── heros-journey-workflow.md
│   │   └── save-the-cat-beat-sheet.md
│   ├── fiction/
│   └── folklore/
│
├── cinematic-styles/
│   ├── camera-movements.md
│   ├── lighting-styles.md
│   ├── creative-techniques.md
│   ├── temporal-narratives.md
│   ├── director-styles.md
│   ├── index.md
│   ├── INTEGRATION.md
│   └── VALIDATION.md
│
├── director-styles/
│   ├── README.md
│   ├── tarantino.md
│   ├── edgar-wright.md
│   └── wes-anderson.md
│
├── transitions/
│   └── vocabulary.md
│
├── art-styles/
│   └── styles.md
│
├── layouts/
│   ├── panel_arrangements.md
│   └── panel_chosing_rules.md
│
├── gemini/
│   ├── image-prompting.md
│   ├── video-prompting.md
│   └── video-gen-workflow.md
│
└── moviemaking/
    ├── continuity.md
    ├── depth_of_field.md
    ├── screen_direction.md
    ├── screenplay-format.md
    ├── shot_composition_rules.md
    ├── storyboarding.md
    └── walter_murch_rules.md
```
