"""Example plugin demonstrating the plugin system.

This is a simple example showing how to create a game plugin
using the architecture framework.
"""

from common.architecture import GameEngine, GamePhase, GamePlugin, GameState, PluginMetadata


class SimpleNumberGuessingGame(GameEngine):
    """A simple number guessing game engine.

    This demonstrates how to implement a game engine using
    the architecture framework.
    """

    def __init__(self):
        super().__init__()
        self.target_number = 50
        self.guesses = []
        self.max_guesses = 10

    def initialize(self, **kwargs):
        """Initialize the game."""
        import random

        self.target_number = kwargs.get("target", random.randint(1, 100))
        self.max_guesses = kwargs.get("max_guesses", 10)
        self.guesses = []
        self._state = GameState(phase=GamePhase.RUNNING)
        self.emit_event("GAME_START", data={"max_guesses": self.max_guesses})

    def reset(self):
        """Reset the game."""
        self.initialize()

    def is_finished(self):
        """Check if the game is finished."""
        if self._state is None:
            return False
        return self._state.phase == GamePhase.FINISHED or len(self.guesses) >= self.max_guesses or (self.guesses and self.guesses[-1] == self.target_number)

    def get_current_player(self):
        """Get current player (single player game)."""
        return "Player"

    def get_valid_actions(self):
        """Get valid actions (numbers 1-100)."""
        return list(range(1, 101))

    def execute_action(self, action):
        """Execute a guess action."""
        if self.is_finished():
            return False

        guess = int(action)
        self.guesses.append(guess)

        if guess == self.target_number:
            self._state.phase = GamePhase.FINISHED
            self.emit_event("GAME_WIN", data={"guesses": len(self.guesses)})
            self.notify(game_won=True, guesses=len(self.guesses))
        elif len(self.guesses) >= self.max_guesses:
            self._state.phase = GamePhase.FINISHED
            self.emit_event("GAME_LOSE", data={"target": self.target_number})
            self.notify(game_lost=True)
        else:
            hint = "higher" if guess < self.target_number else "lower"
            self.emit_event(
                "GUESS_MADE",
                data={"guess": guess, "hint": hint, "remaining": self.max_guesses - len(self.guesses)},
            )
            self.notify(guess_made=guess, hint=hint)

        return True

    def get_public_state(self):
        """Get public game state."""
        state = super().get_public_state()
        state.update(
            {
                "guesses": self.guesses.copy(),
                "guesses_remaining": self.max_guesses - len(self.guesses),
                "finished": self.is_finished(),
            }
        )
        return state


class ExampleGamePlugin(GamePlugin):
    """Example game plugin."""

    def get_metadata(self):
        """Return plugin metadata."""
        return PluginMetadata(
            name="number_guessing_game",
            version="1.0.0",
            author="Games Repository",
            description="A simple number guessing game demonstrating the plugin system",
            dependencies=[],
        )

    def initialize(self, **kwargs):
        """Initialize the plugin."""
        print("Number Guessing Game plugin initialized")

    def shutdown(self):
        """Shutdown the plugin."""
        print("Number Guessing Game plugin shutting down")

    def get_game_class(self):
        """Return the game engine class."""
        return SimpleNumberGuessingGame

    def get_config_schema(self):
        """Return configuration schema."""
        return {
            "target": {"type": "int", "min": 1, "max": 100, "default": 50},
            "max_guesses": {"type": "int", "min": 1, "max": 20, "default": 10},
        }


# Export the plugin instance
plugin = ExampleGamePlugin()
