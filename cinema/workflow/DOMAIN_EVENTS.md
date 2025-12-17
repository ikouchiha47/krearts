# Domain Event System

## Overview

The domain event system decouples side effects from core workflow logic. Instead of embedding character extraction, notifications, or other operations directly in the flow, we emit events at key state transitions and handle them separately.

## Architecture

```
┌─────────────────┐
│  StoryBuilder   │
│     Flow        │
└────────┬────────┘
         │ emits events
         ▼
┌─────────────────┐
│ Event Registry  │
│  (queue)        │
└────────┬────────┘
         │ after flow.kickoff_async()
         ▼
┌─────────────────┐
│ Event Handlers  │
│  - Characters   │
│  - Notifications│
│  - etc.         │
└─────────────────┘
```

## Key Components

### 1. DomainEvent
A data class representing a state transition:
- `name`: Event identifier (e.g., "storyline_approved")
- `workflow_id`: Which workflow emitted this
- `state`: Full flow state snapshot
- `metadata`: Additional context

### 2. DomainEventRegistry
Manages event handlers and queuing:
- `register(event_name, handler)`: Register a handler for an event
- `enqueue(event)`: Queue an event during flow execution
- `dispatch_queued()`: Execute all handlers after flow completes

### 3. Event Handlers
Injected with dependencies, handle specific side effects:
- `CharacterExtractionHandler`: Parses storyline and saves characters to DB

## Usage

### In Flow (cinema/agents/bookwriter/flow.py)

```python
def _emit_event(self, event_name: str, metadata: Optional[Dict] = None):
    """Emit a domain event for this workflow state."""
    if not self._event_registry:
        return
    
    event = DomainEvent(
        name=event_name,
        workflow_id=self.state.id,
        state=self.state.model_dump(),
        metadata=metadata or {}
    )
    self._event_registry.enqueue(event)

# In eval_plotline when critique passes:
self._emit_event("storyline_approved")
```

### In Workflow Orchestrator (cinema/workflow/book_workflow.py)

```python
from cinema.workflow.domain_events import get_event_registry
from cinema.workflow.handlers.character_extraction import CharacterExtractionHandler

# Set up registry and handlers
event_registry = get_event_registry()
character_handler = CharacterExtractionHandler()
event_registry.register("storyline_approved", character_handler.handle)

# Inject into flow
flow._event_registry = event_registry

# Run flow
await flow.kickoff_async()

# Dispatch all queued events
event_registry.dispatch_queued()
```

## Benefits

1. **Separation of Concerns**: Flow logic stays focused on state transitions
2. **Testability**: Handlers can be tested independently
3. **Flexibility**: Easy to add/remove handlers without touching flow code
4. **Dependency Injection**: Handlers get their dependencies (parsers, storage, etc.)
5. **Error Isolation**: Handler failures don't crash the flow

## Events

### storyline_approved
Emitted when critique passes (or max retries reached).

**State includes:**
- `output.storyline`: The approved storyline text

**Handlers:**
- `CharacterExtractionHandler`: Parses characters and saves to DB

**Metadata:**
- `max_retries_reached`: True if approved due to max retries

## Adding New Handlers

1. Create handler class in `cinema/workflow/handlers/`
2. Implement `handle(event: DomainEvent)` method
3. Register in workflow orchestrator before `kickoff_async()`

Example:

```python
class NotificationHandler:
    def __init__(self, email_service):
        self.email_service = email_service
    
    def handle(self, event: DomainEvent):
        workflow_id = event.workflow_id
        self.email_service.send(f"Storyline approved for {workflow_id}")

# Register
notification_handler = NotificationHandler(email_service)
event_registry.register("storyline_approved", notification_handler.handle)
```

## Testing

```python
from cinema.workflow.domain_events import DomainEventRegistry, DomainEvent

# Create test registry
registry = DomainEventRegistry()

# Track handler calls
calls = []
def test_handler(event):
    calls.append(event)

registry.register("test_event", test_handler)

# Emit and dispatch
event = DomainEvent(name="test_event", workflow_id="test", state={})
registry.enqueue(event)
registry.dispatch_queued()

assert len(calls) == 1
```
