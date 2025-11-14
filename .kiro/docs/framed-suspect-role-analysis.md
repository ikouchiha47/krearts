# Framed Suspect Role Analysis

## Problem Statement

The LLM generated a character with role `"framed suspect"` (line 77 in `detective_storyline.md`), but the Pydantic model `CharacterProfile` only allows these literal values:

```python
role: Literal["killer", "victim", "accomplice", "witness", "betrayal", "detective"]
```

This caused a validation error:
```
Input should be 'killer', 'victim', 'accomplice', 'witness', 'betrayal' or 'detective'
[type=literal_error, input_value='framed suspect', input_type=str]
```

## Root Cause Analysis

### Why Did "Framed Suspect" Appear?

1. **It's in the constraint model**: `PlotConstraints` has a `framed_suspect` field
2. **It's in the task prompt**: The detective task template references `{framed_suspect}` 
3. **It's a logical role**: Margaret Ashford IS being framed - this is a real plot function
4. **LLM made reasonable inference**: The model saw framing as a distinct role

### Where It Came From

Looking at the plot structure:
```python
# From example_detective.py
constraints = PlotConstraints(
    killer="James Butler",
    victim="Victor Ashford",
    framed_suspect="Margaret Ashford",  # ← This constraint exists
    # ...
)
```

The LLM correctly identified Margaret's narrative function: she's not just a bystander, she's **actively being framed**. This is a distinct role in the plot graph.

## Graph Analysis: Where Does "Framed Suspect" Fit?

### Current Graph Structure

```
ActionType.FRAMED relationship:
  source: killer (James Butler)
  target: framed_suspect (Margaret Ashford)
  action: FRAMED
  time: murder_time + 1
  location: crime_scene
  motive: "deflect suspicion"
```

### Role vs Action Distinction

**The confusion**: We're mixing **actions** (what happens) with **roles** (character functions).

| Action | Role |
|--------|------|
| KILLED | killer, victim |
| FRAMED | killer (framer), framed_suspect (framee) |
| WITNESSED | witness |
| BETRAYED | betrayer, betrayed |
| ALLIED_WITH | ally |
| DISCOVERED | detective |

**Margaret Ashford**:
- **Action performed ON her**: FRAMED (she's the target)
- **Role in narrative**: Framed suspect / Red herring
- **Function in plot**: Misdirection device

### Is "Framed Suspect" a Valid Role?

**YES**, for these reasons:

1. **Narrative Function**: Distinct from other roles
   - Not a witness (didn't see anything)
   - Not an accomplice (not helping killer)
   - Not a betrayer (not betraying anyone)
   - Not just a bystander (actively implicated)

2. **Plot Mechanics**: Has specific graph relationships
   - Target of FRAMED action
   - Has false evidence planted
   - Creates misdirection for detective
   - Eventually exonerated

3. **Character Arc**: Unique trajectory
   - Starts as prime suspect
   - Has apparent motive
   - Lacks actual guilt
   - Requires exoneration

4. **Detective Story Trope**: Classic element
   - Red herring is essential to mystery
   - Creates false leads
   - Tests detective's reasoning
   - Adds complexity to investigation

## Solutions

### Option 1: Add "framed_suspect" to Literal (Recommended)

**Pros**:
- Recognizes legitimate narrative role
- Matches constraint model
- Allows LLM to be accurate
- Reflects actual plot function

**Cons**:
- None significant

**Implementation**:
```python
role: Literal[
    "killer", 
    "victim", 
    "accomplice", 
    "witness", 
    "betrayal", 
    "detective",
    "framed_suspect"  # ← Add this
]
```

### Option 2: Map to Existing Role

Force "framed suspect" to map to an existing role.

**Possible mappings**:
- `"witness"` - NO: They didn't witness anything
- `"accomplice"` - NO: They're not helping the killer
- `"betrayal"` - NO: They're not betraying anyone
- Create generic `"suspect"` - MAYBE: But loses specificity

**Pros**:
- No model change needed

**Cons**:
- Loses semantic meaning
- Inaccurate representation
- Confusing for LLM
- Doesn't match constraint model

### Option 3: Use Role Composition

Allow multiple roles per character.

```python
roles: List[Literal["killer", "victim", "accomplice", "witness", "betrayal", "detective", "suspect"]]
```

**Example**:
```python
# James Butler
roles=["killer", "accomplice"]  # Kills victim, allies with doctor

# Margaret Ashford  
roles=["suspect"]  # Framed but innocent

# Dr. Helen Price
roles=["witness", "accomplice"]  # Witnesses murder, allied with killer
```

**Pros**:
- More flexible
- Handles complex characters
- Matches real plot complexity

**Cons**:
- Breaking change to model
- More complex validation
- Harder to query "who is THE killer"

### Option 4: Separate Primary/Secondary Roles

```python
primary_role: Literal["killer", "victim", "detective", "suspect"]
secondary_roles: List[Literal["accomplice", "witness", "betrayer", "betrayed", "framed"]]
```

**Pros**:
- Clear hierarchy
- Maintains single "main" role
- Allows complexity

**Cons**:
- More complex model
- Requires careful role assignment

## Recommendation

### Short Term: Add "framed_suspect" to Literal

This is the **minimal fix** that solves the immediate problem:

```python
role: Literal[
    "killer", 
    "victim", 
    "accomplice", 
    "witness", 
    "betrayal", 
    "detective",
    "framed_suspect",  # Red herring / falsely implicated
    "suspect"  # Generic suspect (optional)
]
```

**Rationale**:
1. Matches existing `PlotConstraints.framed_suspect` field
2. Reflects actual narrative function
3. Allows LLM to be accurate
4. Minimal code change
5. Semantically correct

### Medium Term: Consider Role Composition

For future complexity (multiple deaths, double-crosses, etc.), consider:

```python
class CharacterProfile(BaseModel):
    name: str
    primary_role: Literal["killer", "victim", "detective", "suspect", "bystander"]
    secondary_roles: List[Literal["accomplice", "witness", "betrayer", "betrayed", "framed"]]
    
    # Derived helpers
    @property
    def is_guilty(self) -> bool:
        return self.primary_role in ["killer", "accomplice"]
    
    @property
    def is_implicated(self) -> bool:
        return "framed" in self.secondary_roles or self.primary_role == "suspect"
```

## Additional Considerations

### Task Prompt Clarity

The task prompt should explicitly guide role assignment:

```yaml
description: |
  ## Character Roles
  
  Assign ONE primary role to each character:
  - **killer**: The person who committed the murder
  - **victim**: The person who was killed
  - **accomplice**: Helped the killer before/during/after
  - **witness**: Saw something suspicious (may be eliminated later)
  - **betrayal**: Betrayed an ally (may overlap with accomplice)
  - **detective**: Investigates the crime
  - **framed_suspect**: Falsely implicated by planted evidence
  - **suspect**: Generic suspect with motive but not framed
  
  Use the EXACT role names above. Do not invent new roles.
```

### Graph Consistency

Ensure the graph builder creates appropriate relationships:

```python
# When framed_suspect is specified
if constraints.framed_suspect:
    self.graph.add_relationship(Relationship(
        source=constraints.killer,
        target=constraints.framed_suspect,
        action=ActionType.FRAMED,
        time=murder_time + 1,
        location=crime_location,
        motive="deflect suspicion"
    ))
    
    # The framed suspect should have:
    # 1. Apparent motive (from backstory)
    # 2. Weak alibi (from timeline)
    # 3. Planted evidence (from framing action)
    # 4. Eventually exonerated (by detective)
```

### Validation Rules

Add validation to ensure framed suspects make sense:

```python
class ConsistencyValidator:
    def validate_framed_suspect(self, graph: RelationshipGraph, constraints: PlotConstraints):
        """Validate framed suspect logic"""
        errors = []
        
        if constraints.framed_suspect:
            # Must have FRAMED relationship
            framing_rels = [r for r in graph.action_sequences 
                           if r.action == ActionType.FRAMED 
                           and r.target == constraints.framed_suspect]
            
            if not framing_rels:
                errors.append(f"Framed suspect {constraints.framed_suspect} has no FRAMED relationship")
            
            # Framed suspect should NOT be the actual killer
            if constraints.framed_suspect == constraints.killer:
                errors.append("Framed suspect cannot be the actual killer")
            
            # Framed suspect should NOT be the victim
            if constraints.framed_suspect == constraints.victim:
                errors.append("Framed suspect cannot be the victim")
        
        return errors
```

## Summary

**The Issue**: LLM correctly identified "framed suspect" as a distinct narrative role, but the Pydantic model doesn't allow it.

**The Fix**: Add `"framed_suspect"` to the `role` Literal type.

**Why It Matters**: 
- Framed suspects are a core detective story element
- They serve a distinct plot function (red herring)
- The constraint model already supports them
- The LLM's inference was correct

**Action Items**:
1. ✅ Add `"framed_suspect"` to `CharacterProfile.role` Literal
2. ✅ Update task prompt to explicitly list valid roles
3. ✅ Add validation for framed suspect logic
4. 📋 Consider role composition for future complexity

This is not a bug - it's the LLM correctly identifying a missing role type in our model.
