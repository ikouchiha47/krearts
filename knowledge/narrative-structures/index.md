# Narrative Structures Index

## Overview

Narrative structures define how a story is told - the order, pacing, and organization of events. This is separate from visual style, editing techniques, or director signatures.

---

## Categories

### 1. Linear Narrative Structures
Stories told in chronological order from beginning to end.

### 2. Non-Linear Narrative Structures  
Stories told out of chronological order or with time manipulation.

### 3. Circular Narrative Structures
Stories that end where they began.

### 4. Parallel Narrative Structures
Multiple storylines told simultaneously.

### 5. Episodic Narrative Structures
Stories told in distinct, self-contained segments.

---

## Available Documentation

### Linear Structures
- **Three-Act Structure** - `linear/three-act-structure.md` ✅
  - *When to use*: Fast-paced action, thrillers, modern blockbusters, clear hero's journey
- **Five-Act Structure** - `linear/five-act.md` ✅
  - *When to use*: Tragedies, character-driven dramas, complex mysteries, moral dilemmas, Shakespearean adaptations
- **Freytag’s Pyramid** - `linear/freytag-pyramid.md` ✅
  - *When to use*: Classical dramatic arc with clear rise–climax–fall; detective reveals with one decisive reversal
- **Hero's Journey** - `linear/heros-journey.md` ✅
  - *When to use*: Transformation stories, adventure narratives, coming-of-age, hero origin stories
- **Story Circle (Dan Harmon)** - `linear/story-circle.md` ✅
  - *When to use*: Character-driven arcs emphasizing transformation and consequence
- **Fichtean Curve** - `linear/fichtean-curve.md` ✅
  - *When to use*: High-tension narratives with continuous escalation and minimal setup
- **Problem-Solution** - `linear/problem-solution.md` ✅
  - *When to use*: Educational content, product demos, B2B videos, how-to guides, direct response
- **Testimonial Structure** - `linear/testimonial-structure.md` ✅
  - *When to use*: Customer stories, case studies, social proof, before/after transformations
- **Chronological** - `linear/chronological.md` ✅

### Non-Linear Structures
- **In Medias Res** - `non-linear/in-medias-res.md` ✅
  - *When to use*: Hook audience quickly, social media content, dramatic reveals, transformation stories
- **Pulp Fiction Structure** - `non-linear/pulp-fiction-structure.md` ✅
  - *When to use*: Multiple interconnected stories, ensemble casts, thematic connections, artistic narratives
- **Memento Structure (Reverse)** - `non-linear/memento-structure.md` ✅
  - *When to use*: Mystery reveals, detective stories, psychological thrillers, "how did we get here" narratives
- **Flashback/Flash-forward** - `non-linear/flashback-flashforward.md` (TODO)
- **Fractured/Puzzle** - `non-linear/fractured.md` (TODO)
- **Frame Story** - `non-linear/frame-story.md` (TODO)

### Circular Structures
- **Bookend** - `circular/bookend.md`
- **Loop** - `circular/loop.md`

### Parallel Structures
- **Parallel Timelines** - `parallel/parallel-timelines.md`
- **Interwoven Stories** - `parallel/interwoven.md`
- **Hyperlink Cinema** - `parallel/hyperlink.md`

### Episodic Structures
- **Anthology** - `episodic/anthology.md`
- **Vignette** - `episodic/vignette.md`
- **Chapter-Based** - `episodic/chapter-based.md`

---

## Quick Reference

| Structure | Time Order | Complexity | Best For | Duration |
|-----------|-----------|------------|----------|----------|
| **Three-Act** | Chronological | Simple | Action, thrillers, clear storytelling | Any |
| **Five-Act** | Chronological | Medium | Drama, tragedy, character studies | 60min+ |
| **Freytag’s Pyramid** | Chronological | Medium | Classical drama, single decisive reveal | Any |
| **Hero's Journey** | Chronological | Medium | Transformation, adventure | 60min+ |
| **Problem-Solution** | Chronological | Simple | Educational, product demos | 15s-5min |
| **In Medias Res** | Middle → Beginning → End | Medium | Hook audience, social media | 30s+ |
| **Flashback** | Past → Present | Medium | Backstory reveal | 30s+ |
| **Flash-forward** | Present → Future | Medium | Build tension | 30s+ |
| **Reverse** | End → Beginning | High | Mystery, reveal | 60s+ |
| **Fractured** | Mixed order | High | Puzzle, mystery | 60s+ |
| **Bookend** | Present → Past → Present | Medium | Frame story | 30s+ |
| **Parallel** | Simultaneous | Medium-High | Compare/contrast | 30s+ |
| **Episodic** | Segments | Low-Medium | Multiple stories | 30s+ |

---

## Relationship to Other Knowledge Bases

### vs. Transitions (editing techniques)
- **Narrative Structure**: WHAT order to tell the story
- **Transitions**: HOW to move between scenes
- Example: Flashback (structure) uses dissolve transition (editing)

### vs. Cinematic Styles (visual techniques)
- **Narrative Structure**: Story organization
- **Cinematic Style**: Visual presentation
- Example: Non-linear story (structure) with film noir lighting (style)

### vs. Director Styles (personal signatures)
- **Narrative Structure**: One element of storytelling
- **Director Style**: Combination of many elements
- Example: Tarantino uses non-linear structure + stylized violence + dialogue

---

## For Short-Form Content (15-60s)

### Recommended Structures

**15-30 seconds**:
- Linear (simple, clear)
- In Medias Res (hook quickly)
- Bookend (simple frame)

**30-45 seconds**:
- Flashback (single time jump)
- Parallel (two timelines)
- Chapter-based (2-3 chapters)

**45-60 seconds**:
- Fractured (puzzle narrative)
- Multiple flashbacks
- Complex parallel

### Avoid for Short-Form:
- Reverse chronology (too confusing)
- Complex fractured narratives
- Multiple parallel timelines (>2)

---

## Integration with Cinema Pipeline

### Screenplay Schema
```python
class NarrativeStructure(BaseModel):
    """Narrative structure metadata"""
    
    type: Literal[
        "linear",
        "flashback",
        "flashforward", 
        "reverse",
        "fractured",
        "in_medias_res",
        "bookend",
        "parallel",
        "episodic"
    ]
    
    timelines: Optional[List[Timeline]]
    chapters: Optional[List[Chapter]]
    
class Timeline(BaseModel):
    id: str
    offset: str  # "-5 years", "+2 days", "present"
    scenes: List[str]
    
class Chapter(BaseModel):
    number: int
    title: Optional[str]
    scenes: List[str]
```

---

## Usage Guidelines

### Choosing a Structure

1. **Consider duration**: Shorter = simpler structure
2. **Consider audience**: Complex structures need attention
3. **Consider message**: Structure should serve story
4. **Consider platform**: Social media = simpler

### Implementation Steps

1. Choose narrative structure
2. Map scenes to timeline/chapters
3. Define transitions between time periods
4. Add visual indicators (text, color grading)
5. Test audience comprehension

---

## Next Steps

- Read specific structure documentation
- Choose structure for your story
- Map scenes to structure
- Define transitions
- Implement in screenplay
