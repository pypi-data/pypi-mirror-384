"""Game engine abstraction layer.

This module provides abstract base classes for game engines, enabling
consistent interfaces across different games and facilitating plugin development.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, Dict, List, Optional

from .events import EventBus
from .observer import Observable


class GamePhase(Enum):
    """Standard game phases."""

    SETUP = auto()
    RUNNING = auto()
    PAUSED = auto()
    FINISHED = auto()


@dataclass
class GameState:
    """Abstract representation of game state.

    This base class provides a common interface for game state that can be
    serialized, cloned, and restored for features like save/load and replay.

    Attributes:
        phase: Current phase of the game
        metadata: Additional metadata about the game state
    """

    phase: GamePhase = GamePhase.SETUP
    metadata: Dict[str, Any] = None

    def __post_init__(self) -> None:
        """Initialize metadata if not provided."""
        if self.metadata is None:
            self.metadata = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert game state to a dictionary for serialization.

        Returns:
            Dictionary representation of the game state
        """
        return {
            "phase": self.phase.name,
            "metadata": self.metadata.copy(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> GameState:
        """Create a game state from a dictionary.

        Args:
            data: Dictionary containing game state data

        Returns:
            A new GameState instance
        """
        return cls(
            phase=GamePhase[data.get("phase", "SETUP")],
            metadata=data.get("metadata", {}),
        )

    def clone(self) -> GameState:
        """Create a deep copy of this game state.

        Returns:
            A new GameState instance with copied data
        """
        return self.from_dict(self.to_dict())


class GameEngine(Observable, ABC):
    """Abstract base class for game engines.

    This class provides a common interface for all game engines, including
    state management, event dispatching, and lifecycle methods.
    """

    def __init__(self, event_bus: Optional[EventBus] = None) -> None:
        """Initialize the game engine.

        Args:
            event_bus: Optional event bus for event-driven architecture
        """
        super().__init__()
        self._event_bus = event_bus or EventBus()
        self._state: Optional[GameState] = None

    @property
    def event_bus(self) -> EventBus:
        """Get the event bus for this engine."""
        return self._event_bus

    @property
    def state(self) -> Optional[GameState]:
        """Get the current game state."""
        return self._state

    @abstractmethod
    def initialize(self, **kwargs: Any) -> None:
        """Initialize the game with given parameters.

        Args:
            **kwargs: Game-specific initialization parameters
        """
        pass

    @abstractmethod
    def reset(self) -> None:
        """Reset the game to initial state."""
        pass

    @abstractmethod
    def is_finished(self) -> bool:
        """Check if the game is finished.

        Returns:
            True if the game has ended
        """
        pass

    @abstractmethod
    def get_current_player(self) -> Optional[Any]:
        """Get the current player.

        Returns:
            The player whose turn it is, or None if not applicable
        """
        pass

    @abstractmethod
    def get_valid_actions(self) -> List[Any]:
        """Get list of valid actions in the current state.

        Returns:
            List of valid actions that can be taken
        """
        pass

    @abstractmethod
    def execute_action(self, action: Any) -> bool:
        """Execute a game action.

        Args:
            action: The action to execute

        Returns:
            True if the action was executed successfully
        """
        pass

    def get_public_state(self) -> Dict[str, Any]:
        """Get a public representation of the game state.

        This method should return a dictionary suitable for display or
        serialization that doesn't expose private information.

        Returns:
            Dictionary containing public game state
        """
        if self._state is None:
            return {}
        return self._state.to_dict()

    def emit_event(self, event_type: str, data: Optional[Dict[str, Any]] = None) -> None:
        """Emit a game event.

        Args:
            event_type: The type of event to emit
            data: Optional event data
        """
        self._event_bus.emit(event_type, data=data, source=self.__class__.__name__)

    def save_state(self) -> Dict[str, Any]:
        """Save the current game state.

        Returns:
            Dictionary representation of the game state
        """
        return self.get_public_state()

    def load_state(self, state_data: Dict[str, Any]) -> None:
        """Load a saved game state.

        Args:
            state_data: Dictionary containing saved state data
        """
        if self._state is not None:
            self._state = GameState.from_dict(state_data)
        self.notify(state_loaded=True)
