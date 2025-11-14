# Flow Pause and Resume

## Overview

The StoryBuilder flow supports pausing execution at specific stages and resuming later. This is useful for:

- **Manual review** of generated content before proceeding
- **Resource management** (pause expensive operations)
- **Iterative development** (generate novel, review, then generate comic)
- **Debugging** (inspect intermediate states)

## How It Works

### 1. Pause Mechanism

The flow uses `waits_at` flags to control execution:

```python
initial_state = {
    "id": "abc123",
    "waits_at": {
        "storyboard": True  # Pause before storyboard generation
    }
}
```

When the flow reaches a stage with `waits_at[stage] = True`:
1. Sets `halted_at = stage`
2. Saves flow state to `output/flow_states/storybuilder_{id}.json`
3. Returns `"halted"` status
4. Exits execution

### 2. State Persistence

Flow state is saved as JSON:

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

### 3. Resume Mechanism

To resume:

```python
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
```

The resume process:
1. Loads state from `output/flow_states/storybuilder_{id}.json`
2. Resets `waits_at[halted_at] = False`
3. Clears `halted_at = None`
4. Continues execution from saved state

## Usage Examples

### Example 1: Pause After Novel Generation

```python
# Start flow with pause at storyboard
flow = StoryBuilder.build(
    ctx=ctx,
    plotbuilder=plotbuilder,
    critique=critique,
    storyboard=storyboard,
    screenplay=screenplay,
    booker=booker,
    initial_state={
        "id": "detective_abc123",
        "waits_at": {"storyboard": True}
    },
    output_base_dir="output/detective_abc123",
    flow_id="detective_abc123"
)

# Run until pause
result = await flow.kickoff_async()
# Returns: "halted"

# Review the generated novel at output/detective_abc123/novel.md

# Resume to generate comic
flow = StoryBuilder.resume_from_halt(
    flow_id="detective_abc123",
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

### Example 2: CLI Usage

```bash
# Start with pause
python -m cinema.cmd.examples.flow_resume_example --pause-at storyboard

# Output:
# 💾 Flow state saved to: output/flow_states/storybuilder_abc123.json
#    Flow ID: abc123
#    Halted at: storyboard
#    To resume: --continue abc123

# Resume later
python -m cinema.cmd.examples.flow_resume_example --continue abc123
```

### Example 3: Integration with Detective Maker

```python
# In detective_maker.py
from cinema.agents.bookwriter.flow import StoryBuilder

# Generate detective ID
detective_id = generate_detective_id()  # e.g., "detective_abc123"

# Start flow with pause
flow = StoryBuilder.build(
    ctx=ctx,
    plotbuilder=plotbuilder,
    critique=critique,
    storyboard=storyboard,
    screenplay=screenplay,
    booker=booker,
    initial_state={
        "id": detective_id,
        "waits_at": {"storyboard": True}  # Pause after novel
    },
    output_base_dir=f"output/{detective_id}",
    flow_id=detective_id
)

# Run until pause
result = await flow.kickoff_async()

# User reviews novel, then resumes
flow = StoryBuilder.resume_from_halt(
    flow_id=detective_id,
    ctx=ctx,
    plotbuilder=plotbuilder,
    critique=critique,
    storyboard=storyboard,
    screenplay=screenplay,
    booker=booker
)

result = await flow.kickoff_async()
```

## Pause Points

You can pause at any stage:

| Stage | Description | Use Case |
|-------|-------------|----------|
| `plan` | After plot generation | Review plot before critique |
| `critique` | After critique | Review feedback before retry |
| `screenplay` | After screenplay | Review screenplay before novel |
| `bookerama` | After novel | Review novel before comic |
| `storyboard` | Before comic generation | Review novel, then generate comic |

## ID Synchronization

The flow ID syncs with output directories:

```
flow_id = "detective_abc123"

output/
├── detective_abc123/           # Output directory
│   ├── chapter_01.json
│   ├── chapter_02.json
│   └── ...
└── flow_states/
    └── storybuilder_detective_abc123.json  # Flow state
```

## Benefits

1. **Manual Review**: Inspect generated content before expensive operations
2. **Cost Control**: Pause before generating 68 comic pages
3. **Iterative Workflow**: Generate → Review → Continue
4. **Debugging**: Inspect intermediate states
5. **Resource Management**: Pause during high-load periods

## Implementation Details

### StoryBuilderState

```python
class StoryBuilderState(BaseModel):
    id: str = ""
    current_state: Literal[...] = "start"
    halted_at: Optional[str] = None
    waits_at: Dict[str, bool] = {"storyboard": False}
    input: Optional[StoryBuilderInput] = None
    output: Optional[StoryBuilderOutput] = None
```

### Key Methods

- `save_state()`: Saves flow state to JSON
- `load_state(flow_id)`: Loads flow state from JSON
- `resume_from_halt(flow_id, **kwargs)`: Resumes from saved state
- `build(..., flow_id=...)`: Sets flow ID for syncing

### Halt Check

```python
@listen(or_("storyboard", handle_screenplay, handle_book_writing))
async def handle_storyboarding(self):
    self.update_state("storyboard")
    
    # Check if we should halt
    if self.state.waits_at.get("storyboard", False):
        logger.info("⏸️  Flow halted at storyboard")
        self.state.halted_at = "storyboard"
        self.save_state()
        return "halted"
    
    # Continue with storyboard generation
    ...
```

## Future Enhancements

1. **Web UI**: Visual interface for pause/resume
2. **Multiple Pause Points**: Pause at multiple stages
3. **Conditional Pauses**: Pause based on output quality
4. **Auto-Resume**: Schedule resume at specific time
5. **State Diff**: Show what changed between pause and resume
