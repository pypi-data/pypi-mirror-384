"""Example plugin demonstrating the plugin system.

This module provides a complete, working example of a simple number guessing game
plugin. It is intended to serve as a reference for third-party developers
wishing to create their own game plugins.

The example covers:
- Implementation of the `GameEngine` for game logic.
- Implementation of the `GamePlugin` to integrate with the core system.
- Usage of game state, events, and configuration.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Type

from common.architecture.engine import GameEngine, GamePhase, GameState
from common.architecture.plugin import GamePlugin, PluginMetadata


class SimpleNumberGuessingGame(GameEngine):
    """A simple number guessing game engine.

    This engine implements the logic for a number guessing game where the player
    tries to guess a secret number within a limited number of attempts.

    This class demonstrates how to:
    - Manage game state (`GameState`).
    - Implement game lifecycle methods (`initialize`, `reset`).
    - Define game rules and logic (`execute_action`, `is_finished`).
    - Emit events for game state changes (`emit_event`).
    - Expose a public view of the game state (`get_public_state`).
    """

    def __init__(self) -> None:
        """Initialize the game engine."""
        super().__init__()
        self.target_number: int = 50
        self.guesses: List[int] = []
        self.max_guesses: int = 10

    def initialize(self, **kwargs: Any) -> None:
        """Initialize or restart the game.

        This method sets up the game with a new random target number and
        resets the guess count.

        Args:
            **kwargs: Configuration parameters for the game.
                - target (int): The secret number. If not provided, a random
                  number between 1 and 100 is chosen.
                - max_guesses (int): The maximum number of allowed guesses.
                  Defaults to 10.
        """
        import random

        # Set game parameters from kwargs or use defaults
        self.target_number = kwargs.get("target", random.randint(1, 100))
        self.max_guesses = kwargs.get("max_guesses", 10)
        self.guesses = []

        # Set the initial game state
        self._state = GameState(phase=GamePhase.RUNNING)

        # Emit an event to signal the start of the game
        self.emit_event("GAME_START", data={"max_guesses": self.max_guesses})

    def reset(self) -> None:
        """Reset the game to its initial state."""
        self.initialize()

    def is_finished(self) -> bool:
        """Check if the game has concluded.

        The game is finished if the player has won, run out of guesses, or
        if the game state is marked as FINISHED.

        Returns:
            True if the game is finished, False otherwise.
        """
        if self._state is None:
            return True  # Not initialized, so considered finished

        # Check for win/loss conditions
        has_won = self.guesses and self.guesses[-1] == self.target_number
        has_lost = len(self.guesses) >= self.max_guesses

        return self._state.phase == GamePhase.FINISHED or has_won or has_lost

    def get_current_player(self) -> str:
        """Get the current player.

        In this single-player game, it always returns a generic "Player".

        Returns:
            The identifier for the current player.
        """
        return "Player"

    def get_valid_actions(self) -> List[int]:
        """Get the list of valid actions.

        For this game, any integer between 1 and 100 is considered a
        valid action (a guess).

        Returns:
            A list of valid integer guesses.
        """
        return list(range(1, 101))

    def execute_action(self, action: Any) -> bool:
        """Execute a player's guess.

        This method processes a player's guess, updates the game state,
        and emits events based on the outcome.

        Args:
            action: The player's guess, expected to be an integer.

        Returns:
            True if the action was successfully executed, False otherwise.
        """
        if self.is_finished():
            self.emit_event("ACTION_REJECTED", data={"reason": "Game is already finished"})
            return False

        try:
            guess = int(action)
        except (ValueError, TypeError):
            self.emit_event("ACTION_REJECTED", data={"reason": "Invalid action format"})
            return False

        self.guesses.append(guess)

        # Check for win condition
        if guess == self.target_number:
            self._state.phase = GamePhase.FINISHED
            self.emit_event("GAME_WIN", data={"guesses": len(self.guesses)})
            self.notify(game_won=True, guesses=len(self.guesses))

        # Check for loss condition
        elif len(self.guesses) >= self.max_guesses:
            self._state.phase = GamePhase.FINISHED
            self.emit_event("GAME_LOSE", data={"target": self.target_number})
            self.notify(game_lost=True)

        # Otherwise, provide a hint
        else:
            hint = "higher" if guess < self.target_number else "lower"
            remaining = self.max_guesses - len(self.guesses)
            self.emit_event("GUESS_MADE", data={"guess": guess, "hint": hint, "remaining": remaining})
            self.notify(guess_made=guess, hint=hint)

        return True

    def get_public_state(self) -> Dict[str, Any]:
        """Get a serializable, public representation of the game state.

        This method provides a snapshot of the current game state that is
        safe to expose to UI components or other systems.

        Returns:
            A dictionary containing the public game state.
        """
        state = super().get_public_state()
        state.update(
            {
                "guesses": self.guesses.copy(),
                "guesses_remaining": self.max_guesses - len(self.guesses),
                "finished": self.is_finished(),
                "max_guesses": self.max_guesses,
            }
        )
        return state


class ExampleGamePlugin(GamePlugin):
    """Example implementation of a `GamePlugin`.

    This class serves as the entry point for the number guessing game plugin.
    It provides metadata, the game engine class, and manages the plugin's
    lifecycle.
    """

    def get_metadata(self) -> PluginMetadata:
        """Get metadata about this plugin.

        This information is used by the plugin manager to identify and
        display information about the plugin.

        Returns:
            A `PluginMetadata` object.
        """
        return PluginMetadata(
            name="number_guessing_game",
            version="1.1.0",
            author="Games Collection Team",
            description="A simple number guessing game to demonstrate the plugin system.",
            dependencies=[],
        )

    def initialize(self, **kwargs: Any) -> None:
        """Initialize the plugin.

        This method is called by the plugin manager when the plugin is loaded.
        """
        print(f"'{self.get_metadata().name}' plugin initialized.")

    def shutdown(self) -> None:
        """Shutdown the plugin.

        This method is called by the plugin manager when the plugin is unloaded.
        """
        print(f"'{self.get_metadata().name}' plugin shutting down.")

    def get_game_class(self) -> Type[SimpleNumberGuessingGame]:
        """Get the game engine class provided by this plugin.

        Returns:
            The `SimpleNumberGuessingGame` class.
        """
        return SimpleNumberGuessingGame

    def get_config_schema(self) -> Optional[Dict[str, Any]]:
        """Get the configuration schema for the game.

        This schema defines the configurable parameters for the game, which can
        be used by a settings UI.

        Returns:
            A dictionary defining the configuration schema.
        """
        return {
            "target": {
                "type": "int",
                "description": "The secret number to guess.",
                "min": 1,
                "max": 100,
                "default": 50,
            },
            "max_guesses": {
                "type": "int",
                "description": "The maximum number of guesses allowed.",
                "min": 1,
                "max": 20,
                "default": 10,
            },
        }


# The plugin manager looks for a module-level variable named 'plugin'
# to identify the plugin instance.
plugin: GamePlugin = ExampleGamePlugin()
