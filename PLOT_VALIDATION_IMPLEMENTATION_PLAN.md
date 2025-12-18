# Plot Validation Implementation Plan

## Executive Summary

We're replacing the current brittle, genre-specific validation system with a robust, structure-based approach using:

1. **Plot Invariant Specification (PIS)** - 7 minimal invariants that define what makes a story exist
2. **Adjacency Graph Analysis** - Character and event graphs for structural insights
3. **Score-Based Validation** - Gradient feedback instead of binary pass/fail
4. **Intent Hints** - LLM-provided semantic hints (fallible, never required)

**Core Rule**: Structure decides validity. Intent hints shape interpretation. Prose is never trusted directly.

This creates a **narrative static analyzer** that judges plot structure without reading prose.

---

## Current Problems (What We're Fixing)

### Problem 1: Label-Based Validation
```python
# CURRENT (brittle)
def validate_detective_story(graph):
    has_detective = any(c.role == "detective" for c in graph.characters)  # String matching
    return has_detective

# ISSUES:
# - LLM uses "protagonist" instead of "detective" → false negative
# - Passes if labels correct but structure broken
# - Fails if labels wrong but structure valid
```

### Problem 2: Genre Coupling
```python
# CURRENT (rigid)
- Detective stories need: detective, killer, victim roles
- Shonen stories need: protagonist, rival, mentor roles
- Adding new genre = update 3+ files

# ISSUES:
# - Role explosion for multi-genre stories
# - Maintenance burden
# - Aliases don't make sense (anime ≠ shonen)
```

### Problem 3: Binary Pass/Fail
```python
# CURRENT (blunt)
if violations:
    return FAIL  # No guidance on what's wrong or how close

# ISSUES:
# - No gradient feedback
# - Can't guide improvement
# - Retry loop is blind
```

---

## Solution Architecture

### Phase 1: Plot Invariant Specification (PIS) ✅ IMPLEMENTED

**7 Minimal Invariants** (genre-agnostic):

```python
PIS-01: Agency        - At least one entity causes events intentionally
PIS-02: Intent        - An agent wants or seeks something  
PIS-03: Opposition    - Something resists that intent
PIS-04: Causality     - Events are not independent
PIS-05: Change        - State before ≠ state after
PIS-06: Escalation    - Pressure or stakes increase
PIS-07: Irreversibility - Some change cannot be undone
```

**Score-Based Output**:
```python
{
  "score": 0.78,
  "breakdown": {
    "agency": {"raw": 1.0, "weight": 1.0, "weighted": 1.0},
    "opposition": {"raw": 1.0, "weight": 1.2, "weighted": 1.2},
    "causality": {"raw": 0.5, "weight": 1.5, "weighted": 0.75},
    "irreversibility": {"raw": 0.0, "weight": 1.1, "weighted": 0.0}
  },
  "interpretation": "Structurally valid. Missing irreversible consequences."
}
```

**Benefits**:
- ✅ Works for any genre (detective, shonen, cyberpunk, horror)
- ✅ Checks actual story structure, not labels
- ✅ Provides actionable feedback
- ✅ Deterministic (no LLM variance)

### Phase 1.5: Normalization Pass ⏳ PLACEHOLDER
**Purpose**: Future home for relationship intent processing
**Current**: Identity pass (no-op)
**Future**: 
- Embedding-based intent classification
- Heuristic overrides  
- Manual rubric edits

### Phase 2: Adjacency Graph Analysis ⏳ NEXT

**Why Graphs Matter**:
Current PIS checks are shallow ("Does something exist?"). Graphs answer:
- Who influences whom?
- Is the protagonist actually central?
- Is conflict connected or fragmented?
- Are events causally linked?

**Two Graph Types**:

1. **Character Relationship Graph** (directed, with intent hints)
```python
class CharacterGraph:
    edges = {
        "Detective Smith": [("John Doe", intent_hint="investigation", time=1)],
        "Jane Suspect": [("Detective Smith", intent_hint="opposition", time=2)]
    }
    # Note: Raw relationship text stays in PlotGraphOutput, not in graph
```

2. **Event Participation Graph** (bipartite)
```python
class EventGraph:
    char_to_events = {
        "Detective Smith": ["Murder Discovery", "Investigation", "Arrest"]
    }
    event_to_chars = {
        "Murder Discovery": ["Detective Smith", "Witness"]
    }
```

**Relationship Schema with Intent Hints**:
```python
{
  "source": "Vikram Malhotra",
  "target": "Detective Rao",
  "description": "plants fabricated evidence to redirect suspicion",  # Free text
  "reason": "to escape prosecution",
  "time": 2,
  "intent_hint": "opposition"  # Optional, one of 8 fixed labels
}
```

**Intent Hint Labels** (8 fixed):
- `opposition` - Direct conflict
- `alliance` - Cooperation
- `mentorship` - Teaching/guidance
- `rivalry` - Competition
- `manipulation` - Deception/control
- `betrayal` - Trust violation
- `romance` - Romantic connection
- `neutral` - No strong dynamic
- `possession` - horror / supernatural / superpower
- `symbiosis` sci-fi / biotech 
- `ideological` -  political / shonen

**Critical Rules**:
- Intent hints are **optional** but recommended
- Intent hints are **fallible** (LLM may be wrong)
- Intent hints **never gate pass/fail**
- Intent hints **contribute to scoring but are never required for structural validity**
- Validator never assumes correctness

**Structural Insights Unlocked**:

```python
# Protagonist Centrality (better agency scoring)
# STRUCTURAL SIGNAL - no intent hints needed
def protagonist_centrality(cg, protagonist):
    out_degree = len(cg.edges.get(protagonist, []))
    in_degree = count_incoming_edges(cg, protagonist)
    return out_degree + in_degree
    # Low centrality = passive protagonist = weak story

# Conflict Topology  
# STRUCTURAL + INTENT HINTS (layered)
def conflict_sources(cg):
    # Structural: incoming edges to protagonist
    structural_conflict = count_incoming_edges(cg, protagonist)
    
    # Intent hint: opposition edges (weak signal)
    hint_conflict = count_edges_with_hint(cg, "opposition")
    
    # Structure dominates
    return structural_conflict > 0 or hint_conflict >= 2

# Orphan Detection
def orphan_characters(graph, cg, eg):
    return [c for c in characters if no_relationships(c) and no_events(c)]
    # Orphans = hallucinated filler

# Event Connectivity
def build_event_dependency_graph(events):
    return event_causality_chains(events)
    # Disconnected components = episodic junk
```

### Phase 3: Enhanced Scoring ⏳ FUTURE

**Graph-Aware PIS Scoring** (Layered Evidence):
```python
# BEFORE (shallow)
def score_agency(graph):
    return 1.0 if has_protagonist_in_events(graph) else 0.0

# AFTER (structural + hints)
def score_opposition(graph, cg, eg):
    score = 0.0
    
    # Structural signal: protagonist has incoming edges (dominant)
    if protagonist_has_incoming_edges(cg):
        score += 0.4
    
    # Event signal: setbacks or losses (dominant)  
    if has_setback_events(graph):
        score += 0.4
    
    # Intent hint signal (weak, never required)
    opposition_hints = count_edges_with_intent(cg, {"opposition", "rivalry", "manipulation"})
    score += 0.2 * min(opposition_hints / 2, 1.0)  # Cap at 0.2
    
    return min(score, 1.0)

# Key: Wrong intent_hint ≠ broken validation
#      Missing intent_hint ≠ failure  
#      Structure still dominates
```

**Genre-Specific Scorers** (optional enhancement):
```python
def score_shonen_growth(graph, cg, eg):
    # Check for training arcs, power progression, mentor relationships
    pass

def score_detective_investigation(graph, cg, eg):
    # Check for clue discovery chains, suspect interrogations
    pass
```

---

## Implementation Status

### ✅ Phase 1: PIS Validator (DONE)

**Files Created/Modified**:
- ✅ `cinema/agents/bookwriter/plot_invariant_validator.py` - PIS implementation
- ✅ `cinema/agents/bookwriter/plotgraph_flow.py` - Integrated PIS validation
- ✅ `cinema/agents/bookwriter/crew.py` - Fixed ArcMetadata BaseModel

**What Works Now**:
- Score-based validation (0.0 - 1.0)
- Genre-agnostic structure checking
- Actionable feedback with suggestions
- Integrated into PlotGraphFlow

**Test Results**:
```python
# Detective story that previously failed on "detective" role label
# Now passes with score 0.78 (structurally valid)
# Issues identified: weak irreversibility, needs permanent consequences
```

### ⏳ Phase 2: Graph Analysis (NEXT)

**Files to Create**:
- `cinema/agents/bookwriter/plot_graph_ir.py` - Graph IR classes
- `cinema/agents/bookwriter/graph_analyzers.py` - Structural analysis functions

**Implementation Plan**:

1. **Update PlotGraphOutput Schema**:
```python
# Add intent_hint to relationships
class Relationship(BaseModel):
    source: str
    target: str
    description: str  # Free natural language
    reason: str
    time: int
    intent_hint: Optional[str] = None  # One of 8 fixed labels, fallible
```

2. **Create Graph IR Classes**:
```python
class PlotGraphIR:
    def __init__(self, plot_graph_output):
        self.character_graph = build_character_graph(plot_graph_output)  # Stores intent_hints
        self.event_graph = build_event_graph(plot_graph_output)
        self.event_dependency_graph = build_event_dependencies(plot_graph_output)
    
    def analyze_structure(self):
        return {
            "protagonist_centrality": self.protagonist_centrality(),
            "conflict_topology": self.conflict_topology(),
            "orphan_characters": self.orphan_characters(),
            "event_connectivity": self.event_connectivity(),
            "relationship_evolution": self.relationship_evolution()
        }
```

2. **Enhance PIS Scoring**:
```python
class EnhancedPlotInvariantValidator(PlotInvariantValidator):
    def validate_plot(self, graph):
        # Build graph IR
        graph_ir = PlotGraphIR(graph)
        
        # Run enhanced scoring
        return self._score_with_graphs(graph, graph_ir)
```

3. **Add Visualization** (optional):
```python
def visualize_plot_structure(graph_ir):
    # Generate networkx graph for debugging
    # Export to graphviz for visual inspection
    pass
```

### ⏳ Phase 3: Genre-Specific Enhancements (FUTURE)

**Shonen Scorer**:
```python
class ShonenPlotScorer:
    def score_growth_arc(self, graph_ir):
        # Check for power progression over time
        # Verify mentor → student relationships
        # Detect training → battle → growth cycles
        pass
```

**Detective Scorer**:
```python
class DetectivePlotScorer:
    def score_investigation_flow(self, graph_ir):
        # Check for clue discovery chains
        # Verify suspect interrogation patterns
        # Detect red herring vs real evidence
        pass
```

---

## Migration Strategy

### Step 1: Parallel Validation ✅ DONE
- PIS validator runs alongside old validator
- Compare results, tune weights
- Gradually increase confidence

### Step 2: Graph Integration ⏳ NEXT
- Add graph analysis to PIS validator
- Enhance scoring with structural insights
- Test with existing plot graphs

### Step 3: Remove Old Validator ⏳ FUTURE
- Replace genre-specific validation completely
- Remove role label requirements from PlotGraph task
- Simplify maintenance burden

### Step 4: Genre Enhancements ⏳ FUTURE
- Add optional genre-specific scorers
- Maintain genre-agnostic core
- Support multi-genre stories naturally

---

## Key Architectural Decisions

### 1. Genre-Agnostic Core
**Decision**: PIS invariants work for all genres
**Rationale**: Structure matters more than labels
**Impact**: Single validator for all story types

### 2. Score-Based Feedback
**Decision**: 0.0-1.0 scores instead of pass/fail
**Rationale**: Enables gradient feedback and guided improvement
**Impact**: Better retry loops, actionable suggestions

### 3. Graph-Based Analysis
**Decision**: Build adjacency graphs for structural analysis
**Rationale**: Shallow list checks miss important patterns
**Impact**: Deeper insights, better validation

### 4. Layered Enhancement
**Decision**: Genre-specific scorers are optional additions
**Rationale**: Keep core simple, add complexity only where needed
**Impact**: Maintainable, extensible system

### 5. Intent Hints as Weak Signals
**Decision**: LLM-provided intent hints boost scores but never gate validity
**Rationale**: LLMs are fallible, structure is more reliable
**Impact**: Robust to LLM variance, structural signals dominate

---

## Success Metrics

### Validation Quality
- ✅ Reduce false negatives (valid plots rejected due to label mismatch)
- ✅ Reduce false positives (invalid plots accepted due to correct labels)
- ⏳ Increase actionable feedback (specific suggestions for improvement)

### System Robustness
- ✅ Handle LLM output variance (different role names)
- ⏳ Support multi-genre stories (detective + cyberpunk)
- ⏳ Scale to new genres without code changes

### Developer Experience
- ✅ Explainable validation results
- ⏳ Visualizable plot structure
- ⏳ Debuggable validation failures

---

## Next Actions

### Immediate (This Week)
1. **Test PIS validator** with existing plot graphs
2. **Remove genre-specific role requirements** from PlotGraph task
3. **Fix shonen aliases** (growth-story, not anime)

### Short Term (Next Sprint)
1. **Implement graph IR classes**
2. **Add structural analysis functions**
3. **Enhance PIS scoring with graph insights**

### Medium Term (Next Month)
1. **Add visualization tools**
2. **Create genre-specific scorers**
3. **Remove old validation system**

---

## Technical Debt Addressed

### Before (Brittle)
- String matching on role names
- Binary pass/fail validation
- Genre-specific validation logic
- Maintenance burden for new genres

### After (Robust)
- Structure-based validation
- Score-based feedback with suggestions
- Genre-agnostic core with optional enhancements
- Single validator for all story types

This creates a **narrative static analyzer** that treats plot graphs like code and validates their structural integrity.