"""
Domain event system for workflow state transitions.

Allows decoupling of side effects (like character extraction, notifications, etc.)
from core flow logic. Events are queued during flow execution and dispatched
after the flow completes.
"""
from __future__ import annotations

import logging
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class DomainEvent:
    """A domain event representing a state transition or significant occurrence."""
    name: str
    workflow_id: str
    state: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)


EventHandler = Callable[[DomainEvent], None]


class DomainEventRegistry:
    """
    Registry for domain event handlers.
    
    Handlers are registered for specific event names and executed when
    those events are dispatched.
    """
    
    def __init__(self):
        self._handlers: Dict[str, List[EventHandler]] = {}
        self._event_queue: List[DomainEvent] = []
    
    def register(self, event_name: str, handler: EventHandler) -> None:
        """Register a handler for a specific event."""
        if event_name not in self._handlers:
            self._handlers[event_name] = []
        self._handlers[event_name].append(handler)
        logger.debug(f"Registered handler for event: {event_name}")
    
    def enqueue(self, event: DomainEvent) -> None:
        """Queue an event for later dispatch."""
        self._event_queue.append(event)
        logger.debug(f"Enqueued event: {event.name} for workflow {event.workflow_id}")
    
    def dispatch_queued(self) -> None:
        """Dispatch all queued events and clear the queue."""
        logger.info(f"Dispatching {len(self._event_queue)} queued events")
        
        while self._event_queue:
            event = self._event_queue.pop(0)
            self._dispatch_event(event)
    
    def _dispatch_event(self, event: DomainEvent) -> None:
        """Dispatch a single event to all registered handlers."""
        handlers = self._handlers.get(event.name, [])
        
        if not handlers:
            logger.debug(f"No handlers registered for event: {event.name}")
            return
        
        logger.info(f"Dispatching event '{event.name}' to {len(handlers)} handler(s)")
        
        for handler in handlers:
            try:
                handler(event)
            except Exception as e:
                logger.error(f"Handler failed for event '{event.name}': {e}", exc_info=True)
    
    def clear_queue(self) -> None:
        """Clear all queued events without dispatching."""
        count = len(self._event_queue)
        self._event_queue.clear()
        logger.debug(f"Cleared {count} queued events")


# Global registry instance
_global_registry: Optional[DomainEventRegistry] = None


def get_event_registry() -> DomainEventRegistry:
    """Get the global event registry instance."""
    global _global_registry
    if _global_registry is None:
        _global_registry = DomainEventRegistry()
    return _global_registry


def reset_event_registry() -> None:
    """Reset the global registry (useful for testing)."""
    global _global_registry
    _global_registry = None
