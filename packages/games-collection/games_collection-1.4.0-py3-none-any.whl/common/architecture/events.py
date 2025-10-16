"""Event-driven architecture for game state changes.

This module provides a flexible event system that allows games to emit
and respond to events without tight coupling between components.
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set


class GameEventType(str, Enum):
    """Canonical event types emitted by game engines and controllers."""

    GAME_INITIALIZED = "game.initialized"
    GAME_START = "game.start"
    TURN_COMPLETE = "game.turn_complete"
    SCORE_UPDATED = "game.score_updated"
    GAME_OVER = "game.over"
    ACTION_PROCESSED = "game.action_processed"


@dataclass
class Event:
    """Represents a game event with metadata.

    Attributes:
        type: The type/name of the event (e.g., "PLAYER_MOVE", "GAME_START")
        data: Additional data associated with the event
        timestamp: When the event was created
        source: Optional identifier of the event source
    """

    type: str
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    source: Optional[str] = None

    def __str__(self) -> str:
        """Return a string representation of the event."""
        return f"Event(type={self.type}, source={self.source}, data={self.data})"


class EventHandler(ABC):
    """Abstract base class for event handlers.

    Subclasses must implement the handle method to process events.
    """

    @abstractmethod
    def handle(self, event: Event) -> None:
        """Handle an event.

        Args:
            event: The event to handle
        """
        pass

    def can_handle(self, event_type: str) -> bool:
        """Check if this handler can handle a given event type.

        By default, returns True for all event types. Override to filter events.

        Args:
            event_type: The type of event to check

        Returns:
            True if the handler can handle this event type
        """
        return True


class EventBus:
    """Central event bus for publishing and subscribing to events.

    The EventBus implements the observer pattern for event-driven architecture.
    Components can subscribe to specific event types or all events, and the bus
    will route events to the appropriate handlers.
    """

    def __init__(self) -> None:
        """Initialize the event bus."""
        self._handlers: Dict[str, List[EventHandler]] = {}
        self._global_handlers: List[EventHandler] = []
        self._event_history: List[Event] = []
        self._enabled = True

    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        """Subscribe a handler to a specific event type.

        Args:
            event_type: The type of events to subscribe to
            handler: The handler that will process the events
        """
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        if handler not in self._handlers[event_type]:
            self._handlers[event_type].append(handler)

    def subscribe_all(self, handler: EventHandler) -> None:
        """Subscribe a handler to all events.

        Args:
            handler: The handler that will process all events
        """
        if handler not in self._global_handlers:
            self._global_handlers.append(handler)

    def unsubscribe(self, event_type: str, handler: EventHandler) -> None:
        """Unsubscribe a handler from a specific event type.

        Args:
            event_type: The type of events to unsubscribe from
            handler: The handler to remove
        """
        if event_type in self._handlers and handler in self._handlers[event_type]:
            self._handlers[event_type].remove(handler)

    def unsubscribe_all(self, handler: EventHandler) -> None:
        """Unsubscribe a handler from all events.

        Args:
            handler: The handler to remove from global handlers
        """
        if handler in self._global_handlers:
            self._global_handlers.remove(handler)

    def publish(self, event: Event) -> None:
        """Publish an event to all subscribed handlers.

        Args:
            event: The event to publish
        """
        if not self._enabled:
            return

        # Store event in history
        self._event_history.append(event)

        # Notify event-specific handlers
        if event.type in self._handlers:
            for handler in self._handlers[event.type]:
                handler.handle(event)

        # Notify global handlers
        for handler in self._global_handlers:
            if handler.can_handle(event.type):
                handler.handle(event)

    def emit(self, event_type: str, data: Optional[Dict[str, Any]] = None, source: Optional[str] = None) -> Event:
        """Create and publish an event.

        Convenience method that creates an Event and publishes it.

        Args:
            event_type: The type of event to emit
            data: Optional data to include with the event
            source: Optional source identifier

        Returns:
            The created event
        """
        event = Event(type=event_type, data=data or {}, source=source)
        self.publish(event)
        return event

    def clear_history(self) -> None:
        """Clear the stored event history."""

        self._event_history.clear()

    def get_history(self, event_type: Optional[str] = None) -> List[Event]:
        """Return a copy of the event history, optionally filtered by type."""

        if event_type is None:
            return self._event_history.copy()
        return [event for event in self._event_history if event.type == event_type]

    def enable(self) -> None:
        """Enable event processing for the bus."""

        self._enabled = True

    def disable(self) -> None:
        """Disable event processing for the bus."""

        self._enabled = False

    def is_enabled(self) -> bool:
        """Return ``True`` when the bus will dispatch events."""

        return self._enabled


_GLOBAL_EVENT_BUS: Optional[EventBus] = None


def get_global_event_bus() -> EventBus:
    """Return the shared global :class:`EventBus` instance.

    The first call creates a new bus; subsequent calls return the same instance.
    """

    global _GLOBAL_EVENT_BUS
    if _GLOBAL_EVENT_BUS is None:
        _GLOBAL_EVENT_BUS = EventBus()
    return _GLOBAL_EVENT_BUS


def set_global_event_bus(event_bus: EventBus) -> None:
    """Set the shared global :class:`EventBus` instance."""

    global _GLOBAL_EVENT_BUS
    _GLOBAL_EVENT_BUS = event_bus


class FunctionEventHandler(EventHandler):
    """Event handler that wraps a function.

    This is a convenience class for creating simple event handlers from functions.
    """

    def __init__(self, func: Callable[[Event], None], event_types: Optional[Set[str]] = None) -> None:
        """Initialize the function handler.

        Args:
            func: The function to call when handling events
            event_types: Optional set of event types this handler can process
        """
        self._func = func
        self._event_types = event_types

    def handle(self, event: Event) -> None:
        """Handle an event by calling the wrapped function."""
        self._func(event)

    def can_handle(self, event_type: str) -> bool:
        """Check if this handler can handle a given event type."""
        if self._event_types is None:
            return True
        return event_type in self._event_types
