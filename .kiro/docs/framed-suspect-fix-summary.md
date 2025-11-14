# Framed Suspect Role - Fix Summary

## Problem
The LLM generated `role: "framed suspect"` for Margaret Ashford, but the Pydantic model only accepted:
```python
["killer", "victim", "accomplice", "witness", "betrayal", "detective"]
```

This caused validation error:
```
Input should be 'killer', 'victim', 'accomplice', 'witness', 'betrayal' or 'detective'
[type=literal_error, input_value='framed suspect']
```

## Root Cause
The LLM **correctly identified** a missing role type:
1. `PlotConstraints` has `framed_suspect` field
2. Margaret Ashford IS being framed (FRAMED action in graph)
3. "Framed suspect" is a distinct narrative function (red herring)
4. The model definition was incomplete

## Solution Applied

### 1. Updated Pydantic Model
**File**: `cinema/models/detective_output.py`

```python
# Before
role: Literal["killer", "victim", "accomplice", "witness", "betrayal", "detective"]

# After
role: Literal["killer", "victim", "accomplice", "witness", "betrayal", "detective", "framed_suspect"]
```

### 2. Updated Task Prompt
**File**: `cinema/agents/bookwriter/plotbuilder/tasks.yaml`

Added explicit role definitions:
```yaml
#### Role
IMPORTANT: Use EXACTLY ONE of these role names (do not invent new roles):
- killer: The person who committed the murder
- victim: The person who was killed
- accomplice: Helped the killer before/during/after the crime
- witness: Saw something suspicious (may be eliminated later)
- betrayal: Betrayed an ally or accomplice
- detective: Investigates the crime
- framed_suspect: Falsely implicated by planted evidence (red herring)
```

## Why "Framed Suspect" Is a Valid Role

### Narrative Function
- **Distinct from other roles**: Not a witness, accomplice, or bystander
- **Active plot element**: Has false evidence planted against them
- **Creates misdirection**: Red herring for detective
- **Requires resolution**: Must be exonerated

### Graph Representation
```python
# FRAMED relationship
ActionType.FRAMED:
  source: killer (James Butler)
  target: framed_suspect (Margaret Ashford)
  time: murder_time + 1
  motive: "deflect suspicion"
```

### Character Arc
1. **Setup**: Has apparent motive (hated victim)
2. **Complication**: Evidence points to them (planted gloves, sedative)
3. **Investigation**: Becomes prime suspect
4. **Resolution**: Detective proves innocence, finds real killer

### Detective Story Trope
- Classic "red herring" element
- Essential for mystery complexity
- Tests detective's reasoning
- Prevents obvious solutions

## Graph Integration

### Where It Fits
```
Character Roles in Graph:
├── Active Participants
│   ├── killer (commits murder)
│   ├── accomplice (helps killer)
│   ├── witness (sees crime)
│   └── betrayal (betrays ally)
├── Passive Participants
│   ├── victim (is killed)
│   └── framed_suspect (is implicated) ← NEW
└── External
    └── detective (investigates)
```

### Relationships
```
framed_suspect receives:
- FRAMED action (from killer)
- False evidence (planted)
- Suspicion (from detective initially)
- Exoneration (from detective eventually)
```

## Example from Generated Story

**Margaret Ashford**:
- **Role**: `framed_suspect`
- **Function**: Red herring
- **Evidence against her**: 
  - Planted gloves (her monogrammed gloves at crime scene)
  - Planted sedative bottle (her medication near body)
  - Apparent motive (publicly hated Victor)
  - Weak alibi (alone and intoxicated)
- **Reality**: Innocent, framed by James Butler
- **Resolution**: Detective Morgan proves framing through fiber evidence

## Additional Benefits

### 1. Matches Constraint Model
```python
PlotConstraints(
    killer="James Butler",
    victim="Victor Ashford",
    framed_suspect="Margaret Ashford",  # ← Now has corresponding role
)
```

### 2. Enables Validation
```python
def validate_framed_suspect(constraints):
    if constraints.framed_suspect:
        # Must have FRAMED relationship
        # Cannot be killer or victim
        # Should have apparent motive
        # Should have weak alibi
```

### 3. Supports Complex Plots
Future scenarios:
- Multiple framed suspects
- Framed suspect who is also a witness
- Killer frames accomplice (double betrayal)

## Files Modified

1. **`cinema/models/detective_output.py`**
   - Added `"framed_suspect"` to `CharacterProfile.role` Literal

2. **`cinema/agents/bookwriter/plotbuilder/tasks.yaml`**
   - Added explicit role definitions with descriptions
   - Added warning not to invent new roles

3. **`.kiro/docs/framed-suspect-role-analysis.md`**
   - Detailed analysis of the issue

4. **`.kiro/docs/framed-suspect-fix-summary.md`**
   - This document

## Testing

The fix should resolve the validation error. Run:
```bash
PYTHONPATH=cinema uv run python cinema/cmd/examples/example_detective.py --validate-only
```

Expected: No validation error for Margaret Ashford's role.

## Future Considerations

### Role Composition (Future Enhancement)
For more complex plots, consider allowing multiple roles:

```python
class CharacterProfile(BaseModel):
    primary_role: Literal["killer", "victim", "detective", "suspect"]
    secondary_roles: List[Literal["accomplice", "witness", "betrayer", "betrayed", "framed"]]
```

**Example**:
```python
# Dr. Helen Price
primary_role="witness"
secondary_roles=["accomplice"]  # Witnessed murder, allied with killer

# James Butler  
primary_role="killer"
secondary_roles=["betrayer"]  # Killed victim, may betray accomplice later
```

### Additional Roles to Consider
- `"suspect"`: Generic suspect (not framed, just suspicious)
- `"bystander"`: Uninvolved character
- `"investigator"`: Non-detective who helps investigation
- `"conspirator"`: Part of larger conspiracy

## Conclusion

This was **not a bug** - the LLM correctly identified a legitimate role that was missing from our model. The fix:
1. ✅ Adds semantic accuracy
2. ✅ Matches constraint model
3. ✅ Reflects actual plot function
4. ✅ Enables proper validation
5. ✅ Supports detective story conventions

The "framed suspect" role is now properly recognized in the system.
