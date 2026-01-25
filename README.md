# Krearts – AI Story & Comic Generator

Cinema AI workflow for generating novels, comic chapters, and page art with incremental control. Ships with FastAPI backend, worker, and Vite+React frontend; runs via Docker Compose or locally with Poetry + Node.

## Table of Contents
- [Features](#features)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Quickstart (Docker Compose)](#quickstart-docker-compose)
- [Environment](#environment)
- [Project Layout](#project-layout)
- [CLI Highlights](#cli-highlights)
- [Common Tasks](#common-tasks)
- [Troubleshooting](#troubleshooting)

## Features
- Incremental workflows: storyline → novel → chapters → pages.
- Resume-anywhere with `--continue`.
- FastAPI API with health endpoint and asset serving.
- Runit-supervised services in container (`api`, `worker`, `frontend`).
- React/Vite UI (port 5173).
- Job persistence and workflow state stored under `output/` + sqlite.

## Architecture
- **Backend:** FastAPI (`cinema/server/app.py`) exposes book workflow, jobs, workflows list, `/health`.
- **Worker:** Processes queued workflow jobs.
- **Frontend:** Vite app served on 5173 (proxied via the container).
- **CLI:** `cinema/cmd/krearts.py` provides the same workflows from terminal.
- **Storage:** SQLite databases + output directory for artifacts and state.

## Prerequisites
- Docker Desktop (includes Compose).
- (Optional for local dev) Python 3.12 with Poetry, Node (via nvm) if running outside Docker.

## Quickstart (Docker Compose)
```bash
docker compose up --build
```
- API: http://localhost:8000
- Frontend: http://localhost:5173
- Health: http://localhost:8000/health
- Volumes: `./output` and `./datastore` mount into the container.
- Env file: compose loads `.env` (copy from `.env.example` if needed).

Stop:
```bash
docker compose down
```

Clean (remove volumes and local images):
```bash
docker compose down -v --rmi local
```

## Environment
- Copy defaults:
```bash
cp .env.example .env
```
- Key vars (see `.env.example` for the full list):
  - `ENVIRONMENT=production`
  - `CINEMA_ROOT=/app`
  - API keys / model config for LLM/image providers, storage paths, feature toggles.

## Project Layout
- `docker-compose.yml` – single `cinema` service running api+worker+frontend.
- `Dockerfile` – multi-stage; installs Poetry + nvm + node modules; uses runit entrypoint.
- `docker-entrypoint.sh` – boots `api`, `worker`, `frontend`, or `all` (default).
- `infra/` – runit service scripts.
- `cinema/` – backend, workflows, agents, storage, server.
- `ui/` – Vite/React frontend.
- `output/` – generated books, chapters, pages (mounted).
- `datastore/` – sqlite databases (mounted).
- `docs/` – deep dives and specs; `docs/krearts_cli.md` for full CLI usage.
- `examples/` – sample configs.

## CLI Highlights
Make executable or run as module:
```bash
python -m cinema.cmd.krearts --help
```
Main flows (see `docs/krearts_cli.md` for full commands):
- Initialize storyline:
  ```bash
  krearts init book --config examples/book_config.json
  ```
- Generate book content:
  ```bash
  krearts book <workflow_id> --continue
  ```
- Generate chapters or pages:
  ```bash
  krearts book <workflow_id> chapters all
  krearts chapters <workflow_id> --pages 1,20
  ```

## Common Tasks
- Build image: `docker compose build`
- Tail logs: `docker compose logs -f`
- Shell into service: `docker compose exec cinema bash`
- Check health: `curl -f http://localhost:8000/health`
- Make targets (shortcuts): `make up`, `make down`, `make logs`, `make shell`, `make clean`

## Troubleshooting
- **Container not healthy:** `docker compose ps` then `docker compose logs cinema` to inspect.
- **Ports busy (8000/5173):** stop conflicting services or change published ports in `docker-compose.yml`.
- **Missing env:** ensure `.env` exists (copy from `.env.example`); rebuild if build args depend on it.
- **Assets not served:** ensure `output/` exists; `SERVE_ASSETS_LOCALLY` controls static mounting at `/assets`.

Happy creating 📚🎨

=======

# Self-Evolving Story Graph System

A modular, self-evolving narrative graph system that generates believable character relationships and plot developments through worldview tracking, value conflicts, and causal chains.

## 🎯 Problem Solved

**Before**: Detective-specific plot structure with fixed roles (killer, victim, etc.)
**After**: Generic self-evolving graph where relationships emerge naturally from character arcs

### Key Example: "Friends Turning Enemies"

For two friends to believably turn against each other, the system ensures:

1. ✅ **Worldview Divergence**: Characters' core beliefs gradually diverge
2. ✅ **Value Conflicts**: Their most important values come into direct opposition
3. ✅ **Forcing Event**: A high-stakes situation forces them to choose sides
4. ✅ **Narrative Justification**: Multiple shared experiences show organic drift
5. ✅ **Character Development**: Both characters have gone through enough growth to justify this

**The system won't allow**: Sudden, unmotivated betrayals without proper setup.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    EXISTING PIPELINE (Unchanged)                 │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐        │
│  │ StoryBuilder │ → │ BookWriter   │ → │ Comic Gen    │        │
│  └──────────────┘   └──────────────┘   └──────────────┘        │
└─────────────────────────────────────────────────────────────────┘
                              ▲
                              │ plot_structure
                              │
┌─────────────────────────────┴───────────────────────────────────┐
│              NEW: Self-Evolving Plot Generation                  │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  EvolvedPlotStructureBuilder                              │  │
│  │  (Replaces PlotStructureBuilder/PlotGraphFlow)           │  │
│  └───────────────────┬──────────────────────────────────────┘  │
│                      │                                           │
│                      ▼                                           │
│  ┌───────────────────────────────────────────────────────┐     │
│  │           StoryGraph (Core Engine)                     │     │
│  │  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐ │     │
│  │  │ Character   │  │ Relationship │  │ Consequence  │ │     │
│  │  │ Arcs        │  │ Evolution    │  │ Engine       │ │     │
│  │  └─────────────┘  └──────────────┘  └──────────────┘ │     │
│  │                                                         │     │
│  │  • Worldview tracking                                  │     │
│  │  • Value conflict detection                            │     │
│  │  • Causal chain validation                             │     │
│  │  • Truth table (who knows what)                        │     │
│  └───────────────────────────────────────────────────────┘     │
│                                                                   │
│  Optional: LLMStoryValidator                                     │
│  • Validates consequences with LLM reasoning                     │
│  • Generates character interpretations                           │
│  • Ensures narrative believability                               │
└───────────────────────────────────────────────────────────────────┘
```

---

## 📦 Components

### 1. `narrative_graph.py` - Core Data Structures

**Key Classes**:

```python
# Character System
- Worldview: Beliefs, values hierarchy, cognitive biases
- CharacterArc: Evolution tracking, worldview shifts
- Value: Core values that drive decisions (justice, loyalty, etc.)
- Belief: Individual beliefs with confidence levels

# Event System
- Event: Story events with participants, stakes, witnesses
- Consequence: Natural results of events
- CausalChain: Cause-effect validation

# Relationship System
- RelationshipState: Dynamic trust levels, shared experiences
- RelationshipEvolutionEngine: Evaluates breaking points
- WorldviewShift: Tracks belief changes

# World State
- WorldState: Snapshot at each beat (facts, beliefs, relationships)
- ConsequenceEngine: Validates logical/emotional/narrative coherence
```

**Example: Breaking Point Evaluation**

```python
breaking_point = relationship_engine.evaluate_breaking_point(
    char1_arc=alex_arc,
    char2_arc=jordan_arc,
    event=confrontation_event,
    relationship=current_relationship
)

# Returns None if not ready to break
# Returns breakdown details if all conditions met:
# - Worldview divergence > 0.5
# - Value conflict > 0.5  
# - Forcing event (high stakes)
# - Sufficient arc progression (multiple shifts)
```

### 2. `evolved_plot_builder.py` - Pipeline Integration

**Main Class**: `EvolvedPlotStructureBuilder`

Replaces `PlotStructureBuilder` from `detective_maker.py` with drop-in compatibility:

```python
builder = EvolvedPlotStructureBuilder(
    use_llm_validation=True,  # Enable LLM validation
    ctx=directors_context,     # Your existing context
    min_events=10,             # Minimum story events
    min_consequences=5         # Minimum consequences
)

result = await builder.run({
    "seed": "Story premise",
    "characters": character_list,
    "genre": "detective"
})

# Output format matches PlotStructureBuilder:
plot_structure = result["plot_structure"]
# - graph: characters, relationships, events
# - truth_table: who knows what at each beat
# - timeline: chronological events
# - constraints: extracted plot constraints
```

**LLM Integration Points**:

```python
# Optional: Validate consequences with LLM
validator = LLMStoryValidator(ctx=directors_context)

is_valid = await validator.validate_consequence(
    event=event,
    consequence=proposed_consequence,
    char1_arc=character_arc_1,
    char2_arc=character_arc_2,
    relationship=their_relationship
)

# Optional: Generate character interpretations
interpretations = await validator.generate_event_interpretations(
    event=ambiguous_event,
    char1_arc=character_arc_1,
    char2_arc=character_arc_2
)
# Returns: { "char1": "interpretation1", "char2": "interpretation2" }
```

### 3. `integration_guide.py` - Examples and Tests

Contains:
- Integration examples
- "Friends to Enemies" demo
- Test suite
- Migration checklist

---

## 🔄 Integration Options

### Option 1: Drop-in Replacement (Recommended)

Replace `PlotStructureBuilder` in `detective_maker.py`:

```python
# OLD:
from cinema.agents.bookwriter.detective import (
    ConstraintTableBuilder,
    ConsistencyValidator,
    TruthTable,
)

class PlotStructureBuilder(Runner[Dict[str, Any], Dict[str, Any]]):
    def __init__(self):
        self.builder = ConstraintTableBuilder()
        # ...

# NEW:
from evolved_plot_builder import EvolvedPlotStructureBuilder

class PlotStructureBuilder(Runner[Dict[str, Any], Dict[str, Any]]):
    def __init__(self, ctx=None):
        self.builder = EvolvedPlotStructureBuilder(
            ctx=ctx,
            use_llm_validation=True
        )
```

### Option 2: Conditional Branch

Add to `BookWorkflow.init()`:

```python
genre = kwargs.get('genre', 'detective').lower()

if genre == 'detective' and not kwargs.get('use_evolved_graph'):
    # Legacy detective path
    plot_builder = DetectivePlotBuilder(ctx=self.ctx)
else:
    # New self-evolving path
    from evolved_plot_builder import EvolvedPlotStructureBuilder
    
    plot_builder = EvolvedPlotStructureBuilder(
        ctx=self.ctx,
        use_llm_validation=True
    )
```

---

## 🚀 Quick Start

### Basic Usage

```python
from evolved_plot_builder import EvolvedPlotStructureBuilder

# Create builder
builder = EvolvedPlotStructureBuilder(
    use_llm_validation=False,  # Start without LLM
    min_events=10
)

# Define story
inputs = {
    "seed": "Two detectives with different ideas about justice",
    "characters": [
        {"id": "alex", "name": "Alex", "values": ["justice", "truth"]},
        {"id": "jordan", "name": "Jordan", "values": ["loyalty", "compassion"]},
    ],
    "genre": "detective"
}

# Generate plot
result = await builder.run(inputs)

# Access results
plot_structure = result["plot_structure"]
graph = result["graph"]

# Use with existing pipeline
narrative_builder = NarrativeBuilderWithStoryBuilder(...)
story_output = await narrative_builder.run(result)
```

### Run Examples

```bash
# Run "Friends to Enemies" demo
python evolved_plot_builder.py

# Run integration guide examples
python integration_guide.py
```

---

## 🎓 Key Concepts

### 1. Worldview System

Characters interpret events through their worldview:

```python
worldview = Worldview(
    core_beliefs={
        "belief_1": Belief(
            statement="Justice must be served",
            confidence=0.9
        )
    },
    values_hierarchy=[
        Value(type=ValueType.JUSTICE, importance=1.0),
        Value(type=ValueType.TRUTH, importance=0.8),
    ],
    biases=["confirmation_bias"]
)
```

### 2. Value Conflicts

Values can oppose each other in specific contexts:

```python
# Justice vs. Loyalty conflict
justice_value.conflicts_with(loyalty_value, context="protecting a friend")
# Returns: 0.8 (strong conflict)

# When forced to choose, characters act based on their importance hierarchy
```

### 3. Worldview Divergence

Measures how different two characters' worldviews are:

```python
divergence = char1.worldview.calculate_divergence(char2.worldview)
# 0.0 = identical worldviews
# 1.0 = opposite worldviews

# Relationship changes require divergence > 0.5
```

### 4. Consequence Validation

Every consequence is validated across multiple dimensions:

```python
is_valid, reasoning, confidence = engine.evaluate_consequence_validity(
    event=trigger_event,
    consequence=proposed_consequence,
    char1_arc=character_arc,
    char2_arc=other_char_arc,
    relationship=their_relationship
)

# Checks:
# ✓ Logical consistency (cause → effect makes sense)
# ✓ Character development (enough growth to justify action)
# ✓ Relationship dynamics (worldview divergence, value conflicts)
# ✓ Stakes alignment (severity matches event importance)
```

### 5. Breaking Points

Relationships break when ALL conditions are met:

1. Worldview divergence > 0.5
2. Value conflict strength > 0.5
3. Forcing event (stakes > 0.7, right type)
4. Sufficient arc progression (multiple shifts)

```python
breaking_point = relationship_engine.evaluate_breaking_point(
    char1_arc, char2_arc, event, relationship
)

if breaking_point:
    # Returns:
    {
        "worldview_divergence": 0.73,
        "value_conflict": 0.85,
        "char1_reasoning": "...",
        "char2_reasoning": "...",
        "trust_delta": -0.8,
        "reversible": False
    }
```

---

## 📊 Output Format

### Compatible with Existing Pipeline

```python
{
    "plot_structure": {
        "graph": {
            "characters": [...],      # Character arcs
            "relationships": [...],   # Relationship states
            "action_sequences": [...] # Events
        },
        "truth_table": {              # Who knows what
            "beat_1": {
                "facts": {...},
                "beliefs": {...}
            }
        },
        "timeline": [                 # Chronological events
            {
                "beat": 1,
                "event_id": "...",
                "type": "revelation",
                "description": "...",
                "consequences": [...]
            }
        ],
        "constraints": {...},         # Extracted constraints
        "causal_chains": [...]        # Cause-effect chains
    },
    "graph": <StoryGraph object>      # Full graph for debugging
}
```

---

## 🧪 Testing

### Run Test Suite

```python
from integration_guide import test_integration

await test_integration()

# Tests:
# ✓ Output format compatibility
# ✓ Character arc tracking
# ✓ Relationship dynamics
# ✓ Event-consequence chains
# ✓ Plot coherence validation
```

### Manual Validation

```python
# Check plot coherence
is_valid, violations = graph.validate_plot_coherence()

if violations:
    for v in violations:
        print(f"Issue: {v}")

# Analyze character arcs
for char_id, arc in graph.character_arcs.items():
    print(f"{char_id}:")
    print(f"  Shifts: {len(arc.worldview_shifts)}")
    print(f"  Experiences: {len(arc.experiences)}")

# Check relationship evolution
for (c1, c2), rel in graph.relationships.items():
    if c1 < c2:
        print(f"{c1} <-> {c2}: trust={rel.trust_level:.2f}")
```

---

## 🎯 Use Cases

### 1. Detective Mystery
Two detectives with different ideas about justice gradually clash:
- One prioritizes TRUTH (by-the-book)
- Other prioritizes COMPASSION (considers context)
- Forcing event: Must decide whether to prosecute sympathetic criminal

### 2. Political Drama
Allies become enemies over policy decisions:
- Shared initial values (JUSTICE, EQUALITY)
- Diverge on FREEDOM vs. DUTY
- Forcing event: Vote on controversial law

### 3. Family Drama
Siblings drift apart:
- Different life experiences shape worldviews
- Same event (parent's illness) interpreted differently
- Values conflict: LOYALTY vs. TRUTH

### 4. War Story
Comrades question the cause:
- Start with shared DUTY value
- One shifts to COMPASSION after witnessing civilians
- Other maintains DUTY despite doubts
- Forcing event: Order to attack civilian area

---

## 🔧 Configuration

### Genre-Specific Settings

```python
genre_configs = {
    "detective": {
        "min_events": 12,
        "min_consequences": 8,
        "default_values": [ValueType.TRUTH, ValueType.JUSTICE, ValueType.DUTY]
    },
    "thriller": {
        "min_events": 8,
        "min_consequences": 5,
        "default_values": [ValueType.SURVIVAL, ValueType.POWER]
    },
    "drama": {
        "min_events": 10,
        "min_consequences": 6,
        "default_values": [ValueType.LOYALTY, ValueType.COMPASSION, ValueType.TRUTH]
    }
}
```

### LLM Integration

```python
# Enable LLM validation for better coherence
builder = EvolvedPlotStructureBuilder(
    ctx=directors_context,
    use_llm_validation=True
)

# LLM validates:
# - Consequence believability
# - Character interpretations
# - Worldview consistency
# - Narrative flow
```

---

## 📚 Migration Checklist

- [ ] Add `narrative_graph.py` to project
- [ ] Add `evolved_plot_builder.py` to project  
- [ ] Update imports in `detective_maker.py` or `book_workflow.py`
- [ ] Test with simple story
- [ ] Integrate LLM validation (optional)
- [ ] Test with complex multi-character story
- [ ] Verify comic generation works
- [ ] Add genre-specific configs
- [ ] Update documentation
- [ ] Deploy

---

## 🐛 Troubleshooting

### "No consequences generated"
→ Increase `min_consequences` parameter
→ Check that events have sufficient `stakes` (> 0.5)

### "Worldviews too similar"
→ Adjust initial worldview generation
→ Add more diverse `ValueType` options
→ Increase value importance differentiation

### "Relationships don't evolve"
→ Ensure events involve multiple characters
→ Increase stakes on relationship-testing events
→ Add `requires_interpretation=True` for ambiguous events

### "Plot seems random"
→ Enable LLM validation
→ Adjust event templates for your genre
→ Increase `min_events` for better arc development

---

## 🤝 Contributing

This is a modular system designed to be extended:

1. **Add new ValueTypes**: Expand `ValueType` enum in `narrative_graph.py`
2. **Add event templates**: Extend `_get_event_templates_for_genre()`
3. **Custom validation rules**: Subclass `ConsequenceEngine`
4. **Genre-specific logic**: Subclass `EvolvedPlotStructureBuilder`


## 🎉 Summary

This system now provides:

✅ **Self-evolving plots** where relationships emerge naturally
✅ **Believable character arcs** with worldview tracking
✅ **Value-based conflicts** that justify relationship changes
✅ **Causal validation** ensuring logical coherence
✅ **Drop-in compatibility** with existing pipeline
✅ **LLM integration points** for enhanced validation
✅ **Genre flexibility** - works for any story type

**The key insight**: By tracking how characters see the world differently and evolving those worldviews through experiences, we get organically motivated plot developments instead of arbitrary events.