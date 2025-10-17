"""Abstract base classes for game engines.

This module defines the common interface that all game engines should implement,
providing a consistent API for game state management, move validation, and
game flow control.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, Generic, List, Optional, TypeVar, Union

from .architecture.events import EventBus, GameEventType, get_global_event_bus

# Type variable for move representation (can be int, tuple, string, etc.)
MoveType = TypeVar("MoveType")
# Type variable for player representation
PlayerType = TypeVar("PlayerType")


class GameState(Enum):
    """Enumeration of possible game states."""

    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    FINISHED = "finished"
    PAUSED = "paused"


class GameEngine(ABC, Generic[MoveType, PlayerType]):
    """Abstract base class for game engines.

    This class defines the interface that all game engines must implement,
    providing methods for game state management, move validation, and
    determining winners.

    Type Parameters:
        MoveType: The type used to represent a move in the game
        PlayerType: The type used to represent a player
    """

    def __init__(self, event_bus: Optional[EventBus] = None) -> None:
        """Initialize the game engine with an optional event bus."""

        self._event_bus: Optional[EventBus] = event_bus

    def set_event_bus(self, event_bus: EventBus) -> None:
        """Attach a specific :class:`EventBus` to the engine."""

        self._event_bus = event_bus

    @property
    def event_bus(self) -> EventBus:
        """Return the active :class:`EventBus`, creating one if needed."""

        bus = getattr(self, "_event_bus", None)
        if bus is None:
            bus = get_global_event_bus()
            self._event_bus = bus
        return bus

    def emit_event(self, event_type: Union[GameEventType, str], data: Optional[Dict[str, Any]] = None) -> None:
        """Emit an event through the engine's event bus."""

        event_name = event_type.value if isinstance(event_type, GameEventType) else event_type
        self.event_bus.emit(event_name, data=data or {}, source=self.__class__.__name__)

    @abstractmethod
    def reset(self) -> None:
        """Reset the game to its initial state."""
        pass

    @abstractmethod
    def is_game_over(self) -> bool:
        """Check if the game has ended.

        Returns:
            True if the game is over, False otherwise.
        """
        pass

    @abstractmethod
    def get_current_player(self) -> PlayerType:
        """Get the player whose turn it is.

        Returns:
            The current player.
        """
        pass

    @abstractmethod
    def get_valid_moves(self) -> List[MoveType]:
        """Get all valid moves for the current game state.

        Returns:
            A list of valid moves that can be made.
        """
        pass

    @abstractmethod
    def make_move(self, move: MoveType) -> bool:
        """Apply a move to the game state.

        Args:
            move: The move to apply.

        Returns:
            True if the move was valid and applied, False otherwise.
        """
        pass

    @abstractmethod
    def get_winner(self) -> Optional[PlayerType]:
        """Get the winner of the game, if any.

        Returns:
            The winning player if the game is over and has a winner,
            None if the game is a draw or still in progress.
        """
        pass

    @abstractmethod
    def get_game_state(self) -> GameState:
        """Get the current state of the game.

        Returns:
            The current game state.
        """
        pass

    def is_valid_move(self, move: MoveType) -> bool:
        """Check if a move is valid in the current game state.

        Args:
            move: The move to validate.

        Returns:
            True if the move is valid, False otherwise.
        """
        return move in self.get_valid_moves()

    def get_state_representation(self) -> Any:
        """Get a representation of the current game state.

        This method can be overridden to provide a custom state representation
        for rendering, serialization, or analysis purposes.

        Returns:
            A representation of the current game state.
        """
        return None
