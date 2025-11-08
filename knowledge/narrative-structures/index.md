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
- **Hero's Journey** - `linear/heros-journey.md` ✅
- **Problem-Solution** - `linear/problem-solution.md` ✅
- **Testimonial Structure** - `linear/testimonial-structure.md` ✅
- **Five-Act Structure** - `linear/five-act.md` (TODO)
- **Chronological** - `linear/chronological.md` (TODO)

### Non-Linear Structures
- **Pulp Fiction Structure** - `non-linear/pulp-fiction-structure.md` ✅
- **Memento Structure (Reverse)** - `non-linear/memento-structure.md` ✅
- **In Medias Res** - `non-linear/in-medias-res.md` ✅
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
| **Linear** | Chronological | Simple | Clear storytelling | Any |
| **Flashback** | Past → Present | Medium | Backstory reveal | 30s+ |
| **Flash-forward** | Present → Future | Medium | Build tension | 30s+ |
| **Reverse** | End → Beginning | High | Mystery, reveal | 60s+ |
| **Fractured** | Mixed order | High | Puzzle, mystery | 60s+ |
| **In Medias Res** | Middle → Beginning → End | Medium | Hook audience | 30s+ |
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
