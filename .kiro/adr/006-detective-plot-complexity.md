# ADR 006: Detective Plot Complexity - Twists, Indirections, and Multiple Deaths

## Status
Proposed

## Context
The current detective story generator (`cinema/agents/bookwriter/detective.py`) supports basic plot structures with:
- Single murder event
- Simple framing mechanism
- Linear discovery process
- Basic alliances and betrayals

However, compelling detective stories often include:
- **Plot twists**: Unexpected revelations that recontextualize earlier events
- **Red herrings**: Misleading clues that point to wrong suspects
- **Multiple deaths**: Additional murders that complicate the investigation
- **Hidden motivations**: Secondary motives revealed later
- **Double-crosses**: Betrayals within alliances
- **False confessions**: Characters taking blame for crimes they didn't commit

## Decision
We will extend the constraint-based plot system to support complex narrative patterns while maintaining logical consistency.

### 1. Extended Constraint Model

Add new fields to `PlotConstraints`:

```python
@dataclass
class PlotConstraints:
    # Existing fields...
    killer: str
    victim: str
    accomplices: List[str]
    
    # NEW: Multiple deaths
    additional_victims: List[Tuple[str, str, int]] = field(default_factory=list)
    # Format: (victim_name, killer_name, time_offset)
    
    # NEW: Plot twists
    red_herrings: List[Tuple[str, str]] = field(default_factory=list)
    # Format: (planted_evidence, points_to_character)
    
    false_confessions: List[Tuple[str, int]] = field(default_factory=list)
    # Format: (character_name, confession_time)
    
    # NEW: Hidden relationships
    secret_alliances: List[Tuple[str, str, int]] = field(default_factory=list)
    # Format: (ally1, ally2, reveal_time)
    
    double_crosses: List[Tuple[str, str, int]] = field(default_factory=list)
    # Format: (betrayer, betrayed, betrayal_time)
    
    # NEW: Revelations
    plot_twists: List[Dict[str, Any]] = field(default_factory=list)
    # Format: {
    #   "type": "identity_reveal" | "motive_reveal" | "evidence_recontextualization",
    #   "character": str,
    #   "reveal_time": int,
    #   "details": str
    # }
```

### 2. New Action Types

Extend `ActionType` enum:

```python
class ActionType(Enum):
    # Existing
    KILLED = "killed"
    FRAMED = "framed"
    WITNESSED = "witnessed"
    DISCOVERED = "discovered"
    BETRAYED = "betrayed"
    ALLIED_WITH = "allied_with"
    
    # NEW
    PLANTED_EVIDENCE = "planted_evidence"
    CONFESSED_FALSELY = "confessed_falsely"
    REVEALED_SECRET = "revealed_secret"
    DISCOVERED_TWIST = "discovered_twist"
    DOUBLE_CROSSED = "double_crossed"
```

### 3. Constraint Builder Extensions

Add methods to `ConstraintTableBuilder`:

```python
def add_red_herring(self, planter: str, evidence: str, points_to: str, time: int):
    """Plant misleading evidence"""
    
def add_additional_murder(self, killer: str, victim: str, time: int, motive: str):
    """Add secondary murder event"""
    
def add_plot_twist(self, twist_type: str, character: str, reveal_time: int, details: Dict):
    """Add narrative twist that recontextualizes earlier events"""
    
def add_false_confession(self, character: str, time: int, reason: str):
    """Character falsely confesses to protect someone or mislead investigation"""
```

### 4. Validation Rules

Extend `ConsistencyValidator` to check:

1. **Red herrings must be discovered**: Planted evidence should be found by detective
2. **False confessions must be disproven**: Timeline must show confession is false
3. **Twists must be foreshadowed**: Earlier events should make sense in retrospect
4. **Multiple deaths don't create paradoxes**: Dead characters can't kill others after their death
5. **Double-crosses require prior alliance**: Can't betray someone you weren't allied with

### 5. Timeline Complexity

The timeline will support:
- **Parallel events**: Multiple actions at same time (different locations)
- **Flashback reveals**: Information revealed out of chronological order
- **Nested deceptions**: Layers of misdirection

## Example: Complex Plot

```python
constraints = PlotConstraints(
    # Primary murder
    killer="James Butler",
    victim="Victor Ashford",
    
    # Additional death (witness elimination)
    additional_victims=[
        ("Dr. Helen Price", "James Butler", 2)  # Killed 2 time units after main murder
    ],
    
    # Red herrings
    red_herrings=[
        ("bloody_glove", "Margaret Ashford"),  # Butler plants evidence
        ("forged_letter", "Margaret Ashford"),
    ],
    
    # Plot twist
    plot_twists=[
        {
            "type": "identity_reveal",
            "character": "James Butler",
            "reveal_time": 5,
            "details": "Butler is actually Victor's illegitimate son"
        }
    ],
    
    # False confession
    false_confessions=[
        ("Margaret Ashford", 4)  # Confesses to protect someone
    ],
    
    # Double-cross
    double_crosses=[
        ("James Butler", "Dr. Helen Price", 2)  # Kills his accomplice
    ],
    
    # Original fields
    accomplices=["Dr. Helen Price"],
    framed_suspect="Margaret Ashford",
    witnesses=[],
    alliances=[("James Butler", "Dr. Helen Price")],
    winners=["James Butler"],
    losers=["Margaret Ashford", "Dr. Helen Price"],
    betrayals=[],
)
```

## Consequences

### Positive
- **Richer narratives**: More engaging and complex detective stories
- **Replayability**: Different constraint combinations create varied plots
- **Logical consistency maintained**: All complexity still validated by graph
- **LLM focuses on description**: Structure remains deterministic

### Negative
- **Increased complexity**: More validation rules to implement
- **Harder to debug**: Complex plots may have subtle logical errors
- **Performance**: More relationships to validate
- **User learning curve**: More parameters to understand

### Neutral
- **Backward compatible**: Existing simple plots still work
- **Optional complexity**: Users can choose simple or complex plots
- **Gradual adoption**: Can implement features incrementally

## Implementation Plan

### Phase 1: Data Model Extensions
1. Add new fields to `PlotConstraints`
2. Extend `ActionType` enum
3. Update `to_crew()` method to handle new fields

### Phase 2: Builder Methods
1. Implement `add_red_herring()`
2. Implement `add_additional_murder()`
3. Implement `add_plot_twist()`
4. Implement `add_false_confession()`

### Phase 3: Validation
1. Add validation rules for new action types
2. Extend `ConsistencyValidator`
3. Add timeline coherence checks

### Phase 4: Examples
1. Create `example_detective_complex.py` with multi-death plot
2. Create `example_detective_twist.py` with major revelation
3. Create `example_detective_red_herring.py` with misleading evidence

### Phase 5: LLM Integration
1. Update task prompts to handle complex narratives
2. Add guidance for describing twists effectively
3. Ensure comic panels can represent revelations visually

## Alternatives Considered

### Alternative 1: Free-form LLM Generation
Let LLM create entire plot without constraints.
- **Rejected**: Loses logical consistency guarantees

### Alternative 2: Template-based Complexity
Pre-defined plot templates (e.g., "Agatha Christie style").
- **Rejected**: Less flexible than constraint-based approach

### Alternative 3: Probabilistic Plot Generation
Random generation with validation.
- **Rejected**: User has less control over specific story elements

## References
- Current implementation: `cinema/agents/bookwriter/detective.py`
- Constraint model: `cinema/agents/bookwriter/models.py`
- Example usage: `cinema/cmd/examples/example_detective.py`
- Related: ADR-001 (Graph-based plot generation)

## Notes
- This extends the existing constraint-based system rather than replacing it
- All new features are optional - simple plots remain simple
- The graph validation ensures even complex plots remain logically consistent
