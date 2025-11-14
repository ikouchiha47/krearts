# Detective Plot Complexity - Implementation Summary

## Overview
Enhanced the detective story generator to support complex narratives including multiple deaths, witness eliminations, and plot twists while maintaining logical consistency through the constraint-based graph system.

## Changes Made

### 1. Fixed Import Issues
**File**: `cinema/models/__init__.py`
- **Issue**: `CinematgrapherCrewOutput` was not exported from the models package
- **Fix**: Added export to make it available for import
- **Impact**: Resolves import error in `cinema/agents/scriptwriter/crew.py`

### 2. Added DirectorsContext to Detective Example
**File**: `cinema/cmd/examples/example_detective.py`
- **Issue**: Detective crews require `DirectorsContext` but example wasn't providing it
- **Fix**: Added context initialization with `GeminiHerd` LLM store
- **Impact**: Example now properly initializes crews

### 3. Fixed CrewAI Tuple Incompatibility
**File**: `cinema/agents/bookwriter/models.py`
- **Issue**: CrewAI doesn't accept tuples in inputs (only str, int, float, bool, dict, list)
- **Fix**: Added `to_crew()` method to `PlotConstraints` that converts tuples to markdown lists
- **Impact**: Witnesses, betrayals, and alliances now properly formatted for CrewAI

**Example**:
```python
# Before (tuples - not compatible)
witnesses=[("Dr. Helen Price", "saw Elena leaving")]

# After to_crew() conversion (markdown list - compatible)
witnesses="- Dr. Helen Price: saw Elena leaving"
```

### 4. Added Examples Loading
**File**: `cinema/pipeline/detective_maker.py`
- **Issue**: Storyboard task expected `{examples}` template variable but it wasn't provided
- **Fix**: Added `ComicStripStoryBoarding.load_examples()` to storyboard inputs
- **Impact**: Task templates now have all required variables

### 5. Enhanced Betrayal System for Witness Elimination
**File**: `cinema/agents/bookwriter/detective.py`
- **Issue**: Betrayals were generic actions, couldn't represent witness elimination (second murder)
- **Fix**: Enhanced betrayal processing to detect when betrayed person is a witness and convert to KILLED action
- **Impact**: Supports complex plots with multiple murders

**Logic**:
```python
if is_witness:
    # This is witness elimination - a second murder
    action = ActionType.KILLED
    motive = "eliminate witness"
else:
    # Regular betrayal (non-lethal)
    action = ActionType.BETRAYED
    motive = "self-interest"
```

### 6. Created Complex Example
**File**: `cinema/cmd/examples/example_detective_complex.py`
- **Purpose**: Demonstrates advanced plot features
- **Features**:
  - Multiple murders (primary + witness elimination)
  - Double-cross within alliance
  - Framed suspect
  - Complex character relationships

**Plot Summary**:
- Elena Volkov kills Marcus Blackwood (primary murder)
- Thomas Reed (Elena's accomplice) kills Dr. Morrison (witness elimination)
- Catherine Blackwood is framed
- Detective Sarah Chen investigates

### 7. Created ADR Document
**File**: `.kiro/adr/006-detective-plot-complexity.md`
- **Purpose**: Architecture decision record for plot complexity features
- **Contents**:
  - Proposed extensions to constraint model
  - New action types for plot twists
  - Validation rules for complex narratives
  - Implementation plan
  - Examples and consequences

## How It Works Now

### Timeline Example
```
time: 0 - Alliance formed (Elena + Thomas)
time: 1 - Primary murder (Elena kills Marcus)
time: 2 - Framing (Elena frames Catherine)
time: 3 - Witness elimination (Thomas kills Dr. Morrison) ← NEW!
time: 4 - Discovery (Detective finds bodies)
```

### Constraint Flow
```
PlotConstraints
    ↓
to_crew() converts tuples to markdown
    ↓
ConstraintTableBuilder builds graph
    ↓
Detects witness in betrayals list
    ↓
Creates KILLED action (not BETRAYED)
    ↓
Timeline has multiple murders
    ↓
LLM generates narrative descriptions
```

## Usage

### Simple Plot (Original)
```python
constraints = PlotConstraints(
    killer="James Butler",
    victim="Victor Ashford",
    framed_suspect="Margaret Ashford",
)
```

### Complex Plot (New)
```python
constraints = PlotConstraints(
    killer="Elena Volkov",
    victim="Marcus Blackwood",
    accomplices=["Thomas Reed"],
    witnesses=[("Dr. James Morrison", "saw Elena leaving")],
    betrayals=[("Thomas Reed", "Dr. James Morrison")],  # Witness elimination!
    framed_suspect="Catherine Blackwood",
)
```

## Testing

Run the simple example:
```bash
PYTHONPATH=cinema uv run python cinema/cmd/examples/example_detective.py --validate-only
```

Run the complex example:
```bash
PYTHONPATH=cinema uv run python cinema/cmd/examples/example_detective_complex.py --validate-only
```

## Future Enhancements (from ADR)

### Phase 1: Extended Data Model
- `additional_victims`: List of secondary murders
- `red_herrings`: Planted evidence
- `false_confessions`: Characters taking blame
- `plot_twists`: Identity reveals, motive revelations

### Phase 2: New Action Types
- `PLANTED_EVIDENCE`
- `CONFESSED_FALSELY`
- `REVEALED_SECRET`
- `DISCOVERED_TWIST`

### Phase 3: Advanced Validation
- Red herrings must be discovered
- False confessions must be disproven
- Twists must be foreshadowed
- Multiple deaths can't create paradoxes

## Benefits

1. **Logical Consistency**: Graph-based validation ensures plot makes sense
2. **Flexibility**: Supports both simple and complex narratives
3. **Backward Compatible**: Existing simple plots still work
4. **LLM Focus**: Structure is deterministic, LLM adds descriptions
5. **Replayability**: Different constraints create varied stories

## Files Modified

- `cinema/models/__init__.py` - Export CinematgrapherCrewOutput
- `cinema/models/move_output.py` - (no changes, just referenced)
- `cinema/agents/bookwriter/models.py` - Added to_crew() method
- `cinema/agents/bookwriter/detective.py` - Enhanced betrayal processing
- `cinema/pipeline/detective_maker.py` - Added examples loading
- `cinema/cmd/examples/example_detective.py` - Added DirectorsContext

## Files Created

- `cinema/cmd/examples/example_detective_complex.py` - Complex plot example
- `.kiro/adr/006-detective-plot-complexity.md` - Architecture decision record
- `.kiro/docs/detective-plot-complexity-summary.md` - This document
