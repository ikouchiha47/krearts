# Three-Act Structure

## Overview

The most common narrative structure in Western storytelling. Divides story into Setup, Confrontation, and Resolution.

---

## Impactful Guidance

### When to use
- Clear storytelling, product demos, transformation arcs, detective reveals

### Core promise
- A: Hook and problem are established
- B: Stakes rise and commitment happens
- C: Conflict peaks and resolves with payoff

### Minimum beats
- A Opening Image → B Inciting Incident → C Plot Point 1 (end Act I)
- D Rising Action → E Midpoint → F Plot Point 2 (all-is-lost)
- G Climax → H Resolution/Closing Image

### Labeled Mermaid graph (A–H)
```mermaid
flowchart LR
  A[Opening Image] --> B[Inciting Incident]
  B --> C[Plot Point 1 (End of Act I)]
  C --> D[Rising Action] --> E[Midpoint]
  E --> F[Plot Point 2 (All Is Lost)]
  F --> G[Climax] --> H[Resolution / Closing Image]
```

### Minimal template (LLM-ready)
```yaml
structure: three_act
beats:
  - id: A_opening_image
  - id: B_inciting_incident
  - id: C_plot_point_1
  - id: D_rising_action
  - id: E_midpoint
  - id: F_plot_point_2
  - id: G_climax
  - id: H_resolution
constraints:
  - "Midpoint (E) changes stakes or understanding"
  - "Climax (G) resolves the core conflict"
  - "Closing image (H) mirrors or contrasts opening (A)"
```

### Quick checklist
- A clear hook and problem (A/B)
- A strong commitment at C
- A true reversal or elevation at E
- A decisive action at G
- A mirrored closing at H

## Structure

### Act 1: Setup (25% of runtime)
**Purpose**: Introduce world, characters, and conflict

**Key Elements**:
- **Opening Image**: Establishes tone and world
- **Exposition**: Who, what, where, when
- **Inciting Incident**: Event that disrupts normal life
- **Plot Point 1**: Decision/event that launches main story

**For 30s Ad**:
```yaml
duration: 7-8 seconds
content:
  - Show character's problem/need (3-4s)
  - Introduce product as solution (3-4s)
```

---

### Act 2: Confrontation (50% of runtime)
**Purpose**: Character pursues goal, faces obstacles

**Key Elements**:
- **Rising Action**: Complications increase
- **Midpoint**: Major revelation or setback
- **Obstacles**: Character struggles
- **Plot Point 2**: Lowest point, all seems lost

**For 30s Videos for Social Media**:
```yaml
duration: 15 seconds
content:
  - Show product in action (8-10s)
  - Demonstrate benefits (5-7s)
```

---

### Act 3: Resolution (25% of runtime)
**Purpose**: Climax and resolution

**Key Elements**:
- **Climax**: Final confrontation/decision
- **Resolution**: Loose ends tied up
- **Closing Image**: Mirrors or contrasts opening

**For 30s Ad**:
```yaml
duration: 7-8 seconds
content:
  - Show transformation/result (4-5s)
  - Call to action/logo (3s)
```

---

## Example: 30-Second Video

```yaml
Act 1 (8s):
  - S1 (4s): Character struggling with problem
  - S2 (4s): Discovers product

Act 2 (15s):
  - S3 (8s): Uses product, shows features
  - S4 (7s): Demonstrates benefits

Act 3 (7s):
  - S5 (4s): Happy result, transformation
  - S6 (3s): Product logo + tagline
```

---

## When to Use

**Best for**:
- Clear problem-solution narratives
- Product demonstrations
- Transformation stories
- Straightforward messaging

**Characteristics**:
- Linear, chronological
- Easy to follow
- Satisfying resolution
- Universal understanding
