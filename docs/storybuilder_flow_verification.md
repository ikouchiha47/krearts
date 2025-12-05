# StoryBuilder Flow - Pause/Resume Verification

## Flow Stages

The StoryBuilder flow has the following stages:

```
start → plan → critique → eval → [screenplay/bookerama] → storyboard → success
```

## Current Pause Point

**Only ONE pause point is currently implemented:**

### 1. Storyboard Stage (IMPLEMENTED ✅)

**Location**: `handle_storyboarding()` method (line 418)

**Trigger**: `waits_at["storyboard"] = True`

**What happens**:
1. Flow reaches `handle_storyboarding()`
2. Checks `if self.state.waits_at.get("storyboard", False)`
3. If True:
   - Sets `halted_at = "storyboard"`
   - Calls `save_state()` to persist state
   - Returns `"halted"`
   - Exits flow execution

**What's completed before pause**:
- ✅ Storyline generation (plan)
- ✅ Critique validation
- ✅ Book/Screenplay generation (bookerama/screenplay)

**What's NOT done**:
- ❌ Comic chapter generation (storyboard)

**Resume behavior**:
- `resume_from_halt()` loads state
- Resets `waits_at["storyboard"] = False`
- Clears `halted_at = None`
- Continues from storyboard stage

## Potential Pause Points (NOT IMPLEMENTED)

These stages could have pause points but currently don't:

### 2. Plan Stage (NOT IMPLEMENTED ❌)

**Would pause after**: Storyline generation
**Before**: Critique

```python
# NOT IMPLEMENTED - Example of what it would look like:
@listen("plan")
async def handle_storybuilding(self):
    # ... generate storyline ...
    
    if self.state.waits_at.get("plan", False):
        self.state.halted_at = "plan"
        self.save_state()
        return "halted"
```

### 3. Critique Stage (NOT IMPLEMENTED ❌)

**Would pause after**: Critique validation
**Before**: Book/Screenplay generation

```python
# NOT IMPLEMENTED
@router(handle_critique)
def eval_plotline(self):
    # ... evaluate critique ...
    
    if self.state.waits_at.get("critique", False):
        self.state.halted_at = "critique"
        self.save_state()
        return "halted"
```

### 4. Screenplay/Bookerama Stage (NOT IMPLEMENTED ❌)

**Would pause after**: Book/Screenplay generation
**Before**: Storyboard

```python
# NOT IMPLEMENTED
@listen("bookerama")
async def handle_book_writing(self):
    # ... generate book ...
    
    if self.state.waits_at.get("bookerama", False):
        self.state.halted_at = "bookerama"
        self.save_state()
        return "halted"
```

## Flow Execution Path

### Path 1: No Pause (Default)

```
start → plan → critique → eval → bookerama → storyboard → success
```

All stages execute without interruption.

### Path 2: Pause at Storyboard (IMPLEMENTED)

```
start → plan → critique → eval → bookerama → storyboard [PAUSE]
                                                    ↓
                                            save_state()
                                                    ↓
                                                 halted
```

**Resume**:
```
load_state() → storyboard [CONTINUE] → success
```

## State Persistence

**Saved to**: `output/flow_states/storybuilder_{id}.json`

**State includes**:
```json
{
  "id": "abc123",
  "current_state": "storyboard",
  "halted_at": "storyboard",
  "waits_at": {
    "storyboard": true
  },
  "input": { ... },
  "output": {
    "storyline": "...",
    "screenplay": "...",
    "storystructure": null
  }
}
```

## Resume Process

1. **Load state**: `StoryBuilder.load_state(flow_id)`
2. **Reset halt flag**: `waits_at[halted_at] = False`
3. **Clear halt marker**: `halted_at = None`
4. **Build flow**: `StoryBuilder.build(..., initial_state=state_data)`
5. **Continue execution**: `flow.kickoff_async()`

## Usage Examples

### Example 1: Pause at Storyboard

```python
# Start with pause
flow = StoryBuilder.build(
    ctx=ctx,
    plotbuilder=plotbuilder,
    critique=critique,
    storyboard=storyboard,
    screenplay=screenplay,
    booker=booker,
    initial_state={
        "id": "abc123",
        "waits_at": {"storyboard": True}
    }
)

result = await flow.kickoff_async()
# Returns: "halted"
# State saved to: output/flow_states/storybuilder_abc123.json

# Resume later
flow = StoryBuilder.resume_from_halt(
    flow_id="abc123",
    ctx=ctx,
    plotbuilder=plotbuilder,
    critique=critique,
    storyboard=storyboard,
    screenplay=screenplay,
    booker=booker
)

result = await flow.kickoff_async()
# Returns: "success"
```

### Example 2: No Pause (Default)

```python
flow = StoryBuilder.build(
    ctx=ctx,
    plotbuilder=plotbuilder,
    critique=critique,
    storyboard=storyboard,
    screenplay=screenplay,
    booker=booker,
    initial_state={
        "id": "abc123",
        "waits_at": {}  # No pause points
    }
)

result = await flow.kickoff_async()
# Returns: "success"
# Executes all stages without pausing
```

## Verification Checklist

- ✅ Pause at storyboard is implemented
- ✅ State is saved when paused
- ✅ Resume resets halt flags
- ✅ Flow continues from correct stage
- ✅ ID syncs with output directory
- ❌ Pause at plan is NOT implemented
- ❌ Pause at critique is NOT implemented
- ❌ Pause at bookerama is NOT implemented

## Recommendations

### For Krearts Integration

The current implementation supports:

```bash
# Initialize (plan + critique)
krearts init book
# Pauses after critique if waits_at["critique"] = True (NOT IMPLEMENTED)

# Generate book (bookerama)
krearts book {id} --continue
# Pauses after bookerama if waits_at["bookerama"] = True (NOT IMPLEMENTED)

# Generate chapters (storyboard)
krearts book {id} chapters all
# Currently executes without pause
# Should pause if waits_at["storyboard"] = True (IMPLEMENTED)
```

### To Add More Pause Points

To support the Krearts workflow stages, add pause checks:

1. **After critique** (for `krearts init book`):
   ```python
   @router(handle_critique)
   def eval_plotline(self):
       # ... existing code ...
       
       if self.state.waits_at.get("critique", False):
           self.state.halted_at = "critique"
           self.save_state()
           return "halted"
   ```

2. **After bookerama** (for `krearts book {id} --continue`):
   ```python
   @listen("bookerama")
   async def handle_book_writing(self):
       # ... existing code ...
       
       if self.state.waits_at.get("bookerama", False):
           self.state.halted_at = "bookerama"
           self.save_state()
           return "halted"
   ```

## Summary

**Current Status**: Only storyboard pause is implemented.

**For Krearts**: Need to add pause points at critique and bookerama stages to support the incremental workflow.

**Working**: Pause/resume mechanism is functional, just needs more pause points added.
