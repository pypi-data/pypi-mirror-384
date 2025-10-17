"""Abstract base classes for game engines.

This module defines the common interface that all game engines should implement,
providing a consistent API for game state management, move validation, and
game flow control. By adhering to this interface, different games can be
integrated into a common framework with shared UI components, AI strategies,
and analytics tools.

The `GameEngine` class is the centerpiece of this module, defining the abstract
methods that every game must implement. This ensures that all games can be
controlled and monitored in a standardized way.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, Generic, List, Optional, TypeVar, Union

from .architecture.events import EventBus, GameEventType, get_global_event_bus

# Type variable for move representation. This allows different games to use
# different types for their moves, such as integers for board positions,
# strings for commands, or tuples for complex actions.
MoveType = TypeVar("MoveType")

# Type variable for player representation. This allows for flexibility in how
# players are identified, whether by simple strings (e.g., "Player 1"),
# integers, or more complex player objects.
PlayerType = TypeVar("PlayerType")


class GameState(Enum):
    """Enumeration of possible game states.

    This enum provides a standardized way to represent the current state of the
    game, making it easier for UI components and other systems to react
    accordingly.
    """

    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    FINISHED = "finished"
    PAUSED = "paused"


class GameEngine(ABC, Generic[MoveType, PlayerType]):
    """Abstract base class for game engines.

    This class defines the essential interface that all game engines must
    implement. It provides a structured framework for managing the game's
    lifecycle, including state transitions, move validation, and win/loss
    detection.

    By creating a subclass of `GameEngine` and implementing its abstract
    methods, developers can create a new game that is compatible with the
    broader ecosystem of tools and components.

    Type Parameters:
        MoveType: The type used to represent a move in the game.
        PlayerType: The type used to represent a player.
    """

    def __init__(self, event_bus: Optional[EventBus] = None) -> None:
        """Initialize the game engine.

        Args:
            event_bus: An optional event bus to use for emitting game events.
                       If not provided, a global event bus will be used.
        """
        self._event_bus: Optional[EventBus] = event_bus

    def set_event_bus(self, event_bus: EventBus) -> None:
        """Attach a specific :class:`EventBus` to the engine.

        This allows for decoupling the game engine from the rest of the
        application and facilitates testing by allowing a mock event bus to be
        injected.

        Args:
            event_bus: The event bus to use for emitting events.
        """
        self._event_bus = event_bus

    @property
    def event_bus(self) -> EventBus:
        """Return the active :class:`EventBus`.

        If no event bus has been explicitly set, this property will fall back
        to a global event bus, ensuring that events can always be emitted.

        Returns:
            The currently configured event bus.
        """
        bus = getattr(self, "_event_bus", None)
        if bus is None:
            # Fallback to the global event bus if none is set
            bus = get_global_event_bus()
            self._event_bus = bus
        return bus

    def emit_event(self, event_type: Union[GameEventType, str], data: Optional[Dict[str, Any]] = None) -> None:
        """Emit an event through the engine's event bus.

        This is a convenience method for emitting game-related events, such as
        `MOVE_MADE` or `GAME_OVER`.

        Args:
            event_type: The type of event to emit. Can be a `GameEventType` enum
                        member or a custom string.
            data: An optional dictionary of data to include with the event.
        """
        event_name = event_type.value if isinstance(event_type, GameEventType) else event_type
        self.event_bus.emit(event_name, data=data or {}, source=self.__class__.__name__)

    @abstractmethod
    def reset(self) -> None:
        """Reset the game to its initial state.

        This method should clear the game board, reset scores, and set the
        turn to the starting player. It is typically called at the beginning
        of a new game.
        """
        pass

    @abstractmethod
    def is_game_over(self) -> bool:
        """Check if the game has ended.

        The game is considered over if there is a winner, a draw, or some
        other terminal condition has been met.

        Returns:
            True if the game is over, False otherwise.
        """
        pass

    @abstractmethod
    def get_current_player(self) -> PlayerType:
        """Get the player whose turn it is.

        Returns:
            The player who is currently expected to make a move.
        """
        pass

    @abstractmethod
    def get_valid_moves(self) -> List[MoveType]:
        """Get all valid moves for the current game state.

        This method is crucial for AI players and for validating human input.
        It should return a list of all possible moves that the current player
        can make.

        Returns:
            A list of valid moves. If no moves are possible, an empty list
            should be returned.
        """
        pass

    @abstractmethod
    def make_move(self, move: MoveType) -> bool:
        """Apply a move to the game state.

        This method should validate the move, update the game state
        accordingly, and switch the turn to the next player.

        Args:
            move: The move to apply, as provided by a player or AI.

        Returns:
            True if the move was valid and successfully applied, False
            otherwise.
        """
        pass

    @abstractmethod
    def get_winner(self) -> Optional[PlayerType]:
        """Get the winner of the game, if any.

        This method should be called after `is_game_over()` returns True to
        determine the outcome.

        Returns:
            The winning player, or None if the game is a draw or still in
            progress.
        """
        pass

    @abstractmethod
    def get_game_state(self) -> GameState:
        """Get the current state of the game.

        This method provides a high-level view of the game's status, which is
        useful for UI components and game flow management.

        Returns:
            The current `GameState` of the game (e.g., `IN_PROGRESS`,
            `FINISHED`).
        """
        pass

    def is_valid_move(self, move: MoveType) -> bool:
        """Check if a move is valid in the current game state.

        This provides a simple way to check a move's validity without
        retrieving the entire list of valid moves.

        Args:
            move: The move to validate.

        Returns:
            True if the move is valid, False otherwise.
        """
        return move in self.get_valid_moves()

    def get_state_representation(self) -> Any:
        """Get a serializable representation of the current game state.

        This method can be overridden to provide a custom data structure
        (e.g., a dictionary or a JSON string) that represents the current
        state of the game. This is useful for saving/loading games,
        transmitting the state over a network, or for debugging purposes.

        Returns:
            A representation of the current game state. By default, it
            returns None.
        """
        return None
