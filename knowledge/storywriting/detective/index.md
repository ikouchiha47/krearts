# Detective Story Writing Knowledge Base

## Overview

This directory contains principles, techniques, and guidelines for writing detective and mystery fiction.

---

## Files

### principles.md
**Core detective story principles and validation rules**

Contains:
- Core Principles (provenance, plausibility, concrete motives)
- Evidence Distribution Checklist (MUST PASS requirements)
- Clue Types (required evidence categories)
- Common Critique Points (anti-patterns to avoid)
- Forensic Evidence Hierarchy (strength ranking)
- Critique Workflow (validation process)

**Use for**: Validating storylines, ensuring logical consistency, checking evidence density.

---

### storytelling-techniques.md
**Detective-specific storytelling techniques**

Contains 16 detailed techniques organized by category:
- **Information Control**: Slow-Burn Pivot, False Confirmation, Emotional Trigger Reveal
- **Clue Revelation**: Breadcrumb Chain, Convergent Evidence, The Overlooked Detail
- **Interrogation**: Contradiction Trap, Sympathetic Ear, Silent Pressure
- **Misdirection**: Obvious Suspect, Unreliable Witness
- **Reveal**: The Gathering, Reverse Reveal, Partial Reveal
- **Pacing**: Ticking Clock, Cold Case Warm-Up

**Use for**: Choosing how to reveal information, pacing reveals, structuring interrogations.

---

## Key Distinctions

### Detective Principles vs Storytelling Techniques
- **Principles** (principles.md): WHAT must be present (evidence, motives, clues)
- **Techniques** (storytelling-techniques.md): HOW to reveal information (pacing, disclosure)

### Detective Storytelling Techniques vs Narrative Structures
- **Detective Storytelling Techniques**: Genre-specific storytelling methods (Slow-Burn Pivot, The Gathering)
- **Narrative Structures**: General timeline organization (Three-Act, In Medias Res)
- **Location**: Narrative structures are in `/knowledge/narrative-structures/`

---

## Workflow

### 1. Planning Phase
- Review `principles.md` for requirements
- Choose 2-3 techniques from `storytelling-techniques.md`
- Select narrative structure from `/knowledge/narrative-structures/`

### 2. Writing Phase
- Apply chosen techniques to scenes
- Ensure all principles are met (evidence density, concrete motives)
- Use forensic evidence hierarchy for multilayered clues

### 3. Validation Phase
- Run through critique workflow in `principles.md`
- Check Evidence Distribution Checklist (MUST PASS)
- Verify all anti-patterns are avoided

---

## Quick Reference

### Minimum Requirements (from principles.md)
- ✅ ≥5 clues total
- ✅ ≥2 clues implicating killer
- ✅ ≥1 clue exonerating framed suspect
- ✅ Red herrings ≤40% of clues
- ✅ Concrete proof for each alliance/betrayal
- ✅ ≥3 evidence types from forensic hierarchy
- ✅ Killer has documented opportunity

### Recommended Techniques (from storytelling-techniques.md)
**For Fair-Play Mysteries**: Breadcrumb Chain, Convergent Evidence, Overlooked Detail
**For Psychological Thrillers**: Emotional Trigger, Sympathetic Ear, Unreliable Witness
**For Action-Oriented**: Ticking Clock, Contradiction Trap, The Gathering

---

## Integration with Cinema Pipeline

### Knowledge Sources
Both files are loaded as knowledge sources in the detective plot builder:

```python
knowledge_sources = TextFileKnowledgeSource(
    file_paths=[
        "storywriting/detective/principles.md",
        "storywriting/detective/storytelling-techniques.md",  # NEW
        "narrative-structures/index.md"
    ]
)
```

### Critique Agent
The critique agent uses `principles.md` to validate storylines and can reference `storytelling-techniques.md` for technique-specific feedback.

---

## Examples

### Good: Multilayered Evidence
```
Physical: Glove fibers at scene
Financial: Ledger showing motive
Digital: Phone records placing killer at scene
Document: Handwriting analysis on planted letter
```
**Result**: 4 evidence types, strong case ✅

### Bad: Single-Layer Evidence
```
Physical: Stationery match only
```
**Result**: 1 evidence type, weak case ❌

### Good: Concrete Alliance Motive
```
Butler-Price Alliance:
- Butler has ledger showing Price's illegal prescriptions
- Price has photos of Butler stealing heirlooms
- Both have "insurance files" on each other
- Mutual assured destruction
```
**Result**: Explicit leverage, logical risk calculus ✅

### Bad: Thin Alliance Motive
```
Butler-Price Alliance:
- "They worked together"
- No explanation of why or how
```
**Result**: No concrete stakes, illogical risk ❌

---

## Related Knowledge Bases

- `/knowledge/narrative-structures/` - General story organization (three-act, non-linear, etc.)
- `/knowledge/moviemaking/storytelling.md` - Visual storytelling principles
- `/knowledge/moviemaking/storyboarding.md` - Scene-by-scene planning

---

## Contributing

When adding new content:
1. **Principles**: Add to `principles.md` if it's a validation rule or requirement
2. **Techniques**: Add to `storytelling-techniques.md` if it's a storytelling method
3. **Examples**: Keep examples generic and decoupled from specific storylines
4. **Cross-reference**: Update this README when adding new files

---

## Version History

- v1.0: Initial principles.md
- v1.1: Added Common Critique Points and Forensic Evidence Hierarchy
- v1.2: Created storytelling-techniques.md with 16 detailed techniques
- v1.3: Added this README for navigation
- v1.4: Renamed narrative-techniques.md to storytelling-techniques.md for clarity
