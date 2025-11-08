# Cinematic Styles Knowledge Base

## Overview

This knowledge base contains reference material for cinematic storytelling techniques, visual styles, and narrative structures. These documents should be referenced by AI agents when generating screenplays and planning video generation.

---

## Directory Structure

```
knowledge/
├── cinematic-styles/
│   ├── README.md (this file)
│   ├── temporal-narratives.md ✓
│   ├── camera-movements.md ✓
│   ├── lighting-styles.md ✓
│   ├── creative-techniques.md ✓
│   ├── color-palettes.md (TODO)
│   └── genre-conventions.md (TODO)
├── transitions/
│   └── vocabulary.md
└── gemini/
    ├── image-prompting.md
    ├── video-prompting.md
    └── video-gen-workflow.md
```

---

## Available Knowledge Bases

### 1. Temporal Narratives ✓
**File**: `temporal-narratives.md`

**Topics Covered**:
- Flashback (past)
- Flash-forward (future)
- Non-linear/fractured narrative
- Parallel timeline
- Bookend structure

**Use Cases**:
- Creating complex story structures
- Showing cause and effect across time
- Building mystery and tension
- Connecting themes temporally

**Integration**:
- Screenplay schema extensions
- Post-production effects
- Prompt engineering templates

---

### 2. Camera Movements ✓
**File**: `camera-movements.md`

**Topics Covered**:
- Static shots
- Pan (horizontal)
- Tilt (vertical)
- Dolly/Track (forward/backward)
- Tracking/Trucking (lateral)
- Crane/Boom (vertical + horizontal)
- Handheld
- Steadicam
- Drone/Aerial
- Zoom
- Dutch angle
- Push in

**Use Cases**:
- Planning camera movement
- Creating dynamic shots
- Matching movement to emotion
- Professional cinematography

**Integration**:
- Veo prompt templates
- Movement speed guidelines
- Emotional mapping

---

### 3. Lighting Styles ✓
**File**: `lighting-styles.md`

**Topics Covered**:
- Three-point lighting
- High-key lighting
- Low-key lighting
- Natural/Available light
- Rembrandt lighting
- Butterfly/Paramount lighting
- Backlighting/Silhouette
- Side/Split lighting
- Motivated lighting
- Colored/Gel lighting
- Practical lighting
- Hard vs Soft light

**Use Cases**:
- Setting mood and atmosphere
- Professional lighting setups
- Matching lighting to genre
- Creating visual hierarchy

**Integration**:
- Lighting for different scenarios
- Time of day lighting
- Color psychology
- Veo prompt templates

---

### 4. Creative Techniques ✓
**File**: `creative-techniques.md`

**Topics Covered**:
- Bullet time / Time slice
- Tilt-shift / Miniature effect
- Long exposure / Light trails
- Hyperlapse
- Cinemagraph / Living photo
- Vertigo effect / Dolly zoom
- Rack focus / Focus pull
- Whip pan transition
- Forced perspective
- Symmetrical framing (Wes Anderson)
- Glitch / Digital distortion
- Infrared / Thermal imaging
- Slow motion (High-speed)
- Monochrome / Black and white
- Split screen / Multi-frame

**Use Cases**:
- Creating unique visual signatures
- Memorable moments
- Artistic projects
- Modern/edgy aesthetics
- Attention-grabbing effects

**Integration**:
- Post-production workflows
- Veo generation strategies
- Creative combinations

---

### 5. Transitions Vocabulary
**File**: `../transitions/vocabulary.md`

**Topics Covered**:
- Match cuts (graphic, action)
- Jump cuts
- Flow cuts
- Smash cuts
- Action cuts
- Montage cuts

**Use Cases**:
- Planning scene transitions
- Determining generation methods
- Post-production editing

---

### 6. Gemini Video Generation
**Directory**: `../gemini/`

**Topics Covered**:
- Image prompting best practices
- Video prompting techniques
- Generation workflow

**Use Cases**:
- Prompt engineering
- API usage
- Quality optimization

---

## How to Use This Knowledge Base

### For Screenplay Writers (AI Agents)

1. **Reference during screenplay generation**:
   ```python
   # Load relevant knowledge
   temporal_kb = load_knowledge("cinematic-styles/temporal-narratives.md")
   transitions_kb = load_knowledge("transitions/vocabulary.md")
   
   # Use in prompt context
   screenplay = generate_screenplay(
       script=user_script,
       knowledge=[temporal_kb, transitions_kb]
   )
   ```

2. **Apply patterns from knowledge base**:
   - Use temporal narrative structures when appropriate
   - Reference transition vocabulary for scene connections
   - Follow prompt engineering templates

3. **Add metadata based on knowledge**:
   - Timeline information
   - Visual style specifications
   - Transition techniques

### For Pipeline Developers

1. **Implement knowledge-based features**:
   - Temporal effects processor
   - Transition generator
   - Style applicator

2. **Extend screenplay schema**:
   - Add temporal metadata
   - Add visual style fields
   - Add transition specifications

3. **Create post-production processors**:
   - Timeline-specific color grading
   - Transition effects
   - Text overlay generation

### For Human Directors

1. **Reference when writing scripts**:
   - Understand available techniques
   - Plan temporal structures
   - Specify visual styles

2. **Review generated screenplays**:
   - Verify temporal logic
   - Check transition choices
   - Validate visual styles

---

## Knowledge Base Expansion

### Planned Additions

#### Color Palettes (TODO)
- Complementary colors
- Analogous colors
- Monochromatic
- Warm vs cool
- Desaturation techniques
- Color psychology
- Brand color systems
- Emotional color mapping

#### Genre Conventions (TODO)
- Action
- Drama
- Comedy
- Horror
- Sci-fi
- Documentary
- Romance
- Thriller

#### Shot Types (TODO)
- Extreme wide shot
- Wide shot
- Medium shot
- Close-up
- Extreme close-up
- Over-the-shoulder
- Point of view
- Two-shot
- Insert shot

#### Composition Rules (TODO)
- Rule of thirds
- Leading lines
- Symmetry
- Depth
- Framing
- Negative space
- Golden ratio
- Visual weight

---

## Contributing to Knowledge Base

### Adding New Techniques

1. **Create markdown file** in appropriate directory
2. **Follow template structure**:
   ```markdown
   # Technique Name
   
   ## Definition
   [Clear explanation]
   
   ## Purpose
   [Why use this technique]
   
   ## Visual Indicators
   [How to recognize/implement]
   
   ## Screenplay Structure
   [JSON schema example]
   
   ## Generation Strategy
   [How to generate with Veo/Imagen]
   
   ## Prompt Template
   [Prompt engineering examples]
   
   ## Examples
   [Real-world examples]
   
   ## Integration with Pipeline
   [Code examples]
   ```

3. **Update this README** with new entry
4. **Add to agent context** if needed

### Updating Existing Techniques

1. **Edit markdown file** directly
2. **Maintain backward compatibility** in schemas
3. **Update examples** if needed
4. **Document changes** in commit message

---

## Integration with AI Agents

### Screenplay Writer Agent

**Should reference**:
- `temporal-narratives.md` - for story structure
- `transitions/vocabulary.md` - for scene transitions
- `gemini/video-prompting.md` - for prompt quality

**Should output**:
- Temporal metadata in screenplay
- Transition specifications
- Visual style guidelines

### Enhancer Agent

**Should reference**:
- All cinematic style documents
- Genre conventions (when available)
- Lighting and color guides (when available)

**Should output**:
- Enhanced prompts with style details
- Generation strategy recommendations
- Post-production specifications

### Pipeline Orchestrator

**Should reference**:
- Generation strategies from knowledge base
- Post-production requirements
- Transition techniques

**Should implement**:
- Knowledge-based generation decisions
- Style-specific post-processing
- Transition effects

---

## Best Practices

### 1. Keep Knowledge Atomic
- One technique per section
- Clear, focused explanations
- Avoid overlap between documents

### 2. Provide Examples
- Real-world use cases
- Code snippets
- Visual descriptions

### 3. Include Integration Details
- Schema extensions
- Code templates
- Pipeline modifications

### 4. Maintain Consistency
- Use same terminology across documents
- Follow template structure
- Cross-reference related techniques

### 5. Update Regularly
- Add new techniques as discovered
- Update based on generation results
- Incorporate user feedback

---

## Quick Reference

### When to Use Temporal Narratives

| Goal | Technique | Knowledge Base |
|------|-----------|----------------|
| Show backstory | Flashback | temporal-narratives.md |
| Create tension | Flash-forward | temporal-narratives.md |
| Build mystery | Non-linear | temporal-narratives.md |
| Show simultaneity | Parallel timeline | temporal-narratives.md |
| Frame story | Bookend | temporal-narratives.md |

### When to Use Transitions

| Goal | Technique | Knowledge Base |
|------|-----------|----------------|
| Visual continuity | Match cut | transitions/vocabulary.md |
| Time passage | Jump cut | transitions/vocabulary.md |
| Smooth progression | Flow cut | transitions/vocabulary.md |
| Dramatic impact | Smash cut | transitions/vocabulary.md |
| Multiple angles | Action cut | transitions/vocabulary.md |
| Rapid sequence | Montage cut | transitions/vocabulary.md |

---

## Future Enhancements

### Database Integration
- Store knowledge in vector database
- Enable semantic search
- Provide AI-powered recommendations

### Interactive Tools
- Visual style previewer
- Transition simulator
- Timeline planner

### Analytics
- Track technique usage
- Measure effectiveness
- Optimize recommendations

---

## Questions?

For questions about:
- **Using knowledge base**: See integration examples above
- **Adding techniques**: Follow contribution guidelines
- **Pipeline integration**: Check code examples in documents
- **Best practices**: Reference this README

---

## Version History

- **v1.3** (2025-11-08): Added creative techniques (15 techniques)
- **v1.2** (2025-11-08): Added lighting styles (12 styles)
- **v1.1** (2025-11-08): Added camera movements (12 movements)
- **v1.0** (2025-11-08): Initial knowledge base with temporal narratives
- **v0.9** (2025-11-07): Transitions vocabulary
- **v0.8** (2025-11-06): Gemini prompting guides
