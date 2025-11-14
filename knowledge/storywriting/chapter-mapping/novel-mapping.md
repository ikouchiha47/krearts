# Novel Chapter Mapping

> **⚠️ DEPRECATED**: This file has been split into two separate files for better organization:
> - **Linear structures**: See `linear-novel-mapping.md`
> - **Non-linear structures**: See `non-linear-novel-mapping.md`
> 
> Please use those files instead. This file is kept for backward compatibility only.

## Overview

This document maps narrative structures to novel chapters with scalable formulas for different lengths.

**Base Assumptions**:
- Novella: 15,000 words → 15 chapters (1,000 words/chapter avg)
- Novel: 90,000 words → 90 chapters (1,000 words/chapter avg)
- Epic: 150,000 words → 150 chapters (1,000 words/chapter avg)

**Adjustable**: Words per chapter can range from 800-1,200 depending on pacing needs.

---

## Freytag's Pyramid Mapping

### Structure Overview
Six phases with clear dramatic arc:
1. Exposition
2. Inciting Incident
3. Rising Action
4. Climax (reversal/turning point)
5. Falling Action
6. Resolution/Denouement

### Chapter Distribution (15-chapter novella)

| Phase | Chapters | Percentage | Purpose |
|-------|----------|------------|---------|
| **Exposition** | 1-3 | 20% | Establish world, characters, baseline mystery state |
| **Inciting Incident** | 3-4 | Overlap | Disturbance that forces protagonist to act |
| **Rising Action** | 4-7 | 27% | Complications, clue gathering, stakes escalate |
| **Climax** | 8-10 | 20% | Pivotal reveal/proof that flips understanding |
| **Falling Action** | 11-12 | 13% | Consequences, confessions, alliances exposed |
| **Resolution** | 13-15 | 20% | New equilibrium, thematic closure |

### Scaling Formula

```
For N total chapters:
- Exposition: Chapters 1 to ceil(N × 0.20)
- Inciting: Chapter ceil(N × 0.20) to ceil(N × 0.27)
- Rising: Chapter ceil(N × 0.27) to ceil(N × 0.47)
- Climax: Chapter ceil(N × 0.47) to ceil(N × 0.67)
- Falling: Chapter ceil(N × 0.67) to ceil(N × 0.80)
- Resolution: Chapter ceil(N × 0.80) to N
```

**Examples**:
- 90-chapter novel: Exposition (1-18), Inciting (18-24), Rising (24-42), Climax (42-60), Falling (60-72), Resolution (72-90)
- 5-chapter short story: Exposition (1), Inciting (1-2), Rising (2-3), Climax (3-4), Falling (4), Resolution (5)

### Detective Genre Application

**Exposition (Ch 1-3)**:
- Establish detective POV and baseline
- Introduce victim context
- Plant initial suspicion/red herring seed
- **Clue requirement**: First clue by end of Ch 3

**Inciting Incident (Ch 3-4)**:
- Body found / call to scene / first incontrovertible anomaly
- Detective commits to investigation

**Rising Action (Ch 4-7)**:
- **Clue density**: ≥5 clues total by end of Ch 7
- Balance red herrings vs. true clues (≤40% red herrings)
- Evidence hierarchy: Introduce ≥3 types (forensic, financial, behavioral)
- Suspect interviews and contradictions surface

**Climax (Ch 8-10)**:
- **Proof chain locks**: Multilayered forensics + motive tie-in + temporal plausibility
- Decisive evidence revealed (tool mark, fiber, phone metadata)
- Confrontation with killer

**Falling Action (Ch 11-12)**:
- Formal confessions
- Exonerations (framed suspect cleared)
- Contracts/ledgers/alliances exposed

**Resolution (Ch 13-15)**:
- Public exoneration
- Status changes (inheritance, freedom, arrest)
- Detective's thematic beat (justice vs. convenience)

---

## Three-Act Structure Mapping

### Structure Overview
Classic screenplay structure adapted for novels:
1. Act I: Setup (25-33%)
2. Act II: Confrontation (50%)
3. Act III: Resolution (17-25%)

### Chapter Distribution (15-chapter novella)

| Act | Chapters | Percentage | Purpose |
|-----|----------|------------|---------|
| **Act I (Setup)** | 1-5 | 33% | Introduce world, establish stakes, inciting incident |
| **Act II (Confrontation)** | 6-11 | 40% | Complications, obstacles, midpoint reversal |
| **Act III (Resolution)** | 12-15 | 27% | Climax, falling action, denouement |

### Key Turning Points

- **End of Act I** (Ch 5): Point of no return, detective fully committed
- **Midpoint** (Ch 8): Major revelation that shifts investigation direction
- **End of Act II** (Ch 11): All seems lost / darkest moment
- **Climax** (Ch 12-13): Final confrontation and proof
- **Resolution** (Ch 14-15): Wrap-up and thematic closure

### Scaling Formula

```
For N total chapters:
- Act I: Chapters 1 to ceil(N × 0.33)
- Act II: Chapter ceil(N × 0.33) to ceil(N × 0.73)
- Act III: Chapter ceil(N × 0.73) to N
```

### Detective Genre Application

**Act I (Ch 1-5)**:
- Crime discovered
- Initial suspects introduced
- First clues planted
- Detective accepts case (point of no return)

**Act II (Ch 6-11)**:
- False leads and red herrings
- Midpoint revelation (Ch 8): Major clue shifts suspicion
- Evidence accumulation
- Darkest moment (Ch 11): Killer seems to have perfect alibi

**Act III (Ch 12-15)**:
- Breakthrough evidence (Ch 12)
- Confrontation and confession (Ch 13)
- Consequences and exoneration (Ch 14)
- Thematic resolution (Ch 15)

---

## Five-Act Structure Mapping

### Structure Overview
Shakespearean/dramatic structure:
1. Exposition
2. Rising Action
3. Climax
4. Falling Action
5. Denouement

### Chapter Distribution (15-chapter novella)

| Act | Chapters | Percentage | Purpose |
|-----|----------|------------|---------|
| **Act I (Exposition)** | 1-3 | 20% | Setup, inciting incident |
| **Act II (Rising Action)** | 4-6 | 20% | Complications begin |
| **Act III (Climax)** | 7-9 | 20% | Peak tension, major reversal |
| **Act IV (Falling Action)** | 10-12 | 20% | Consequences unfold |
| **Act V (Denouement)** | 13-15 | 20% | Resolution, new equilibrium |

### Scaling Formula

```
For N total chapters (equal distribution):
- Act I: Chapters 1 to ceil(N × 0.20)
- Act II: Chapter ceil(N × 0.20) to ceil(N × 0.40)
- Act III: Chapter ceil(N × 0.40) to ceil(N × 0.60)
- Act IV: Chapter ceil(N × 0.60) to ceil(N × 0.80)
- Act V: Chapter ceil(N × 0.80) to N
```

### Detective Genre Application

**Act I (Ch 1-3)**:
- Crime scene establishment
- Initial investigation begins

**Act II (Ch 4-6)**:
- Clue gathering intensifies
- First major suspect emerges

**Act III (Ch 7-9)**:
- Decisive evidence discovered
- Major confrontation or revelation

**Act IV (Ch 10-12)**:
- Confession obtained
- Alliances/betrayals exposed
- Framed suspect exonerated

**Act V (Ch 13-15)**:
- Legal/social consequences
- Thematic reflection
- New status quo established

---

## In Medias Res Mapping (Non-Linear)

### Structure Overview
Start with dramatic moment, then flashback to explain how we got here:
1. Hook (Present)
2. Flashback (Exposition)
3. Rising Action (Past → Present)
4. Climax
5. Resolution

### Chapter Distribution (15-chapter novella)

| Phase | Chapters | Percentage | Purpose |
|-------|----------|------------|---------|
| **Hook (Present)** | 1-2 | 13% | Start with dramatic moment (body found, confrontation) |
| **Flashback (Exposition)** | 3-5 | 20% | Rewind to establish context |
| **Rising Action** | 6-10 | 33% | Build from past to present |
| **Climax** | 11-13 | 20% | Return to present, resolve mystery |
| **Resolution** | 14-15 | 14% | Aftermath and closure |

### Scaling Formula

```
For N total chapters:
- Hook: Chapters 1 to ceil(N × 0.13)
- Flashback: Chapter ceil(N × 0.13) to ceil(N × 0.33)
- Rising: Chapter ceil(N × 0.33) to ceil(N × 0.66)
- Climax: Chapter ceil(N × 0.66) to ceil(N × 0.86)
- Resolution: Chapter ceil(N × 0.86) to N
```

### Detective Genre Application

**Hook (Ch 1-2)**:
- Open with detective confronting killer OR body discovery
- Create immediate tension and questions

**Flashback (Ch 3-5)**:
- "72 hours earlier..."
- Establish victim, suspects, initial clues
- Show what led to opening scene

**Rising Action (Ch 6-10)**:
- Progress chronologically toward opening scene
- Plant clues that will pay off in climax
- Build toward the moment we started with

**Climax (Ch 11-13)**:
- Return to present timeline
- Reveal how detective solved it
- Confrontation and confession

**Resolution (Ch 14-15)**:
- Consequences
- Thematic closure

---

## Hero's Journey Mapping

### Structure Overview
Joseph Campbell's 12-stage monomyth:
1. Ordinary World
2. Call to Adventure
3. Refusal of the Call
4. Meeting the Mentor
5. Crossing the Threshold
6. Tests, Allies, Enemies
7. Approach to Inmost Cave
8. Ordeal
9. Reward
10. The Road Back
11. Resurrection
12. Return with Elixir

### Chapter Distribution (15-chapter novella)

| Phase | Chapters | Percentage | Purpose |
|-------|----------|------------|---------|
| **Act I: Departure** | 1-5 | 33% | Ordinary World → Crossing Threshold |
| **Act II: Initiation** | 6-11 | 40% | Tests → Ordeal → Reward |
| **Act III: Return** | 12-15 | 27% | Road Back → Resurrection → Return |

### Detailed Breakdown

- **Ordinary World** (Ch 1): Establish protagonist's normal life
- **Call to Adventure** (Ch 2): Inciting incident
- **Refusal** (Ch 3): Protagonist resists
- **Meeting Mentor** (Ch 4): Guidance received
- **Crossing Threshold** (Ch 5): Point of no return
- **Tests, Allies, Enemies** (Ch 6-8): Learning the rules
- **Approach** (Ch 9): Preparation for major challenge
- **Ordeal** (Ch 10-11): Death/rebirth moment
- **Reward** (Ch 11): Seizing the prize
- **Road Back** (Ch 12): Pursuit begins
- **Resurrection** (Ch 13-14): Final test
- **Return** (Ch 15): New equilibrium with wisdom

### Scaling Formula

```
For N total chapters:
- Act I (Departure): Ch 1 to ceil(N × 0.33)
- Act II (Initiation): Ch ceil(N × 0.33) to ceil(N × 0.73)
- Act III (Return): Ch ceil(N × 0.73) to N
```

### Detective Genre Application

**Act I (Ch 1-5)**:
- Ordinary World: Detective's routine life
- Call: Crime discovered
- Refusal: "Not my jurisdiction" / initial resistance
- Mentor: Forensic expert / veteran detective
- Threshold: Accepts case officially

**Act II (Ch 6-11)**:
- Tests: Interview suspects, gather clues
- Allies: Forensic team, helpful witnesses
- Enemies: Obstructive chief, lying suspects
- Approach: Narrow down to prime suspect
- Ordeal: Confrontation where detective's theory is challenged
- Reward: Decisive evidence discovered

**Act III (Ch 12-15)**:
- Road Back: Killer attempts escape/cover-up
- Resurrection: Final proof locks the case
- Return: Justice served, detective changed by experience

---

## Pulp Fiction Structure Mapping (Non-Linear)

### Structure Overview
Multiple storylines told out of chronological order, interconnected through:
- Shared characters
- Thematic parallels
- Object/location connections

### Chapter Distribution (15-chapter novella)

Organize by **storyline**, not chronology:

| Storyline | Chapters | Timeline Position | Purpose |
|-----------|----------|-------------------|---------|
| **Story A** | 1-3, 8-9 | Day 1, Day 3 | Primary narrative |
| **Story B** | 4-6 | Day 2 | Parallel events |
| **Story C** | 7, 10-12 | Day 1 (earlier), Day 3 (later) | Backstory + resolution |
| **Convergence** | 13-15 | Day 3 (finale) | All threads unite |

### Key Principles

- **Non-chronological presentation**: Jump between timelines
- **Thematic unity**: Stories echo similar themes
- **Character crossover**: Characters appear in multiple storylines
- **Delayed reveals**: Information from Story B explains Story A

### Scaling Formula

```
For N total chapters with M storylines:
- Allocate chapters per storyline: N / M
- Interweave: Story A (Ch 1-3), Story B (Ch 4-6), Story A (Ch 7-9), etc.
- Reserve final 20% for convergence: ceil(N × 0.20)
```

### Detective Genre Application

**Story A: The Murder** (Ch 1-3, 8-9)
- Present timeline: Body found, initial investigation
- Jump to: Confrontation with killer

**Story B: The Accomplice** (Ch 4-6)
- Flashback: How accomplice got involved
- Reveals motive we didn't understand in Story A

**Story C: The Framed Suspect** (Ch 7, 10-12)
- Earlier timeline: Showing their innocence
- Later timeline: Their exoneration

**Convergence** (Ch 13-15)
- All timelines meet at climax
- Full picture revealed through non-linear assembly

---

## Memento Structure Mapping (Reverse Chronology)

### Structure Overview
Tell the story backwards, from end to beginning:
- Start with the resolution
- Each chapter reveals what came before
- Final chapter shows the inciting incident

### Chapter Distribution (15-chapter novella)

| Phase | Chapters | Chronological Order | Narrative Order |
|-------|----------|---------------------|-----------------|
| **Resolution** | 1 | Day 5 (end) | Ch 1 (start) |
| **Falling Action** | 2-4 | Day 4 | Ch 2-4 |
| **Climax** | 5-7 | Day 3 | Ch 5-7 |
| **Rising Action** | 8-11 | Day 2 | Ch 8-11 |
| **Exposition** | 12-14 | Day 1 | Ch 12-14 |
| **Inciting Incident** | 15 | Day 1 (beginning) | Ch 15 (end) |

### Key Principles

- **Mystery deepens**: Each chapter raises new questions about what came before
- **Dramatic irony**: Reader knows outcome, wants to know cause
- **Revelation structure**: Each step back reveals new context

### Scaling Formula

```
For N total chapters:
- Start at chronological end: Ch 1 = Timeline position N
- Work backwards: Ch 2 = Timeline position (N-1)
- End at chronological beginning: Ch N = Timeline position 1
```

### Detective Genre Application

**Ch 1 (Timeline: Day 5)**: Killer arrested, case closed
**Ch 2-4 (Day 4)**: How detective got final proof
**Ch 5-7 (Day 3)**: The confrontation that led to proof
**Ch 8-11 (Day 2)**: Clue gathering that led to confrontation
**Ch 12-14 (Day 1)**: Initial investigation
**Ch 15 (Day 1, morning)**: Body discovered

**Effect**: Reader knows WHO but discovers WHY and HOW backwards

---

## Bookend Structure Mapping (Circular)

### Structure Overview
Story begins and ends in the same place/moment:
- Present → Flashback → Return to Present
- Creates thematic closure through repetition with difference

### Chapter Distribution (15-chapter novella)

| Phase | Chapters | Timeline | Purpose |
|-------|----------|----------|---------|
| **Opening Frame** | 1-2 | Present | Establish current situation |
| **Flashback** | 3-13 | Past → Present | Main narrative |
| **Closing Frame** | 14-15 | Present (same as Ch 1-2) | Return with new understanding |

### Key Principles

- **Repetition with difference**: Same scene, different meaning
- **Thematic echo**: Opening question answered by closing
- **Circular imagery**: Visual/symbolic elements repeat

### Scaling Formula

```
For N total chapters:
- Opening frame: Ch 1 to ceil(N × 0.13)
- Flashback: Ch ceil(N × 0.13) to ceil(N × 0.87)
- Closing frame: Ch ceil(N × 0.87) to N
```

### Detective Genre Application

**Opening Frame (Ch 1-2)**: Detective at retirement ceremony, reflecting on one case
**Flashback (Ch 3-13)**: The case itself, told chronologically
**Closing Frame (Ch 14-15)**: Return to ceremony, now understanding why it mattered

**Effect**: Frame provides thematic context for the investigation

---

## Usage Guidelines

### Choosing a Mapping

1. **Match to narrative structure**: Use the mapping that corresponds to your chosen structure from `narrative-structures/`
2. **Consider genre**: Detective stories work well with Freytag (clear reveal) or 3-Act (midpoint twist)
3. **Adjust for length**: Use scaling formulas for novels longer/shorter than 15 chapters
4. **Enforce genre rules**: Apply detective principles regardless of structure chosen

### Implementation Steps

1. **Calculate total chapters**: `target_words / avg_words_per_chapter`
2. **Apply scaling formula**: Get chapter ranges for each phase
3. **Map plot points**: Assign story beats to specific chapters
4. **Validate against genre rules**: Ensure clue distribution, evidence hierarchy, etc.
5. **Generate chapters**: Expand each chapter using snowflake method

### Example Calculation

```
Target: 90,000-word detective novel
Words per chapter: 1,000 avg
Total chapters: 90

Structure: Freytag's Pyramid

Exposition: Ch 1-18 (90 × 0.20 = 18)
Inciting: Ch 18-24 (90 × 0.27 = 24)
Rising: Ch 24-42 (90 × 0.47 = 42)
Climax: Ch 42-60 (90 × 0.67 = 60)
Falling: Ch 60-72 (90 × 0.80 = 72)
Resolution: Ch 72-90

Detective constraints:
- First clue: By Ch 18 (end of exposition)
- ≥5 clues: By Ch 42 (end of rising action)
- Decisive evidence: Ch 42-60 (climax)
- Confession: Ch 60-72 (falling action)
```

---

## Related Documents

- Narrative structures: `knowledge/narrative-structures/index.md`
- Detective principles: `knowledge/storywriting/detective/principles.md`
- Storytelling techniques: `knowledge/storywriting/detective/storytelling-techniques.md`
