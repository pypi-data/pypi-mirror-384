#!/usr/bin/env python
"""This script provides a live demonstration of the core architectural components.

It showcases the interplay between the following systems:
- PluginManager: For discovering and loading game modules dynamically.
- Event System: For decoupled communication between game components.
- Observer Pattern: For state change notifications.
- SettingsManager: For managing persistent game settings.
- ReplayManager: For recording and replaying game sessions, including undo/redo.
- SaveLoadManager: For saving and loading game states.

The demonstration simulates a simple number guessing game to illustrate these concepts
in a practical context.
"""

import tempfile
import time
from pathlib import Path

from common.architecture import Event, EventHandler, Observer, PluginManager, ReplayManager, SaveLoadManager, SettingsManager


class GameEventLogger(EventHandler):
    """A simple event handler that logs all captured game events to the console.

    This class demonstrates how to create a component that listens to the event bus
    and reacts to specific events, or in this case, all events.
    """

    def handle(self, event: Event):
        """Processes and prints a single game event."""
        print(f"📢 Event Captured: {event.type}")
        if event.data:
            print(f"   - Data: {event.data}")


class GameStateObserver(Observer):
    """An observer that monitors and reports changes in the game's state.

    This class demonstrates the Observer pattern, where it's notified by the
    game object (the "observable") whenever its state changes.
    """

    def update(self, observable, **kwargs):
        """Receives and prints a notification about a state change."""
        # The 'observable' parameter is the object that sent the notification (the game).
        # '**kwargs' contains the data related to the state change.
        print(f"👀 Game State Observer: State has changed with data -> {kwargs}")


def main():
    """Runs the full demonstration of the architectural systems."""
    print("=" * 60)
    print("Architectural Systems Demonstration")
    print("=" * 60)

    # --- 1. Plugin System ---
    # The PluginManager is responsible for finding and loading game plugins from specified directories.
    print("\n1️⃣  Initializing Plugin System")
    print("-" * 60)
    # This points the manager to a directory where plugins are stored.
    plugin_manager = PluginManager(plugin_dirs=[Path("./plugins")])

    print("Discovering available plugins...")
    plugins = plugin_manager.discover_plugins()
    print(f"Plugins found: {plugins}")

    print("\nLoading the 'example_plugin'...")
    # This loads the plugin's code and makes it available.
    plugin_manager.load_plugin("example_plugin")

    # Retrieve the loaded plugin module and its metadata.
    plugin = plugin_manager.get_plugin("example_plugin")
    metadata = plugin_manager.get_plugin_metadata("example_plugin")
    print(f"Successfully loaded: {metadata.name} v{metadata.version}")

    # --- 2. Game Engine Instantiation ---
    # The plugin provides the main game class, which we can now instantiate.
    print("\n2️⃣  Instantiating Game Engine from Plugin")
    print("-" * 60)
    GameClass = plugin.get_game_class()
    game = GameClass()
    print(f"Game '{GameClass.__name__}' instance created.")

    # --- 3. Event System ---
    # The Event Bus allows for decoupled communication. We subscribe a logger to it.
    print("\n3️⃣  Setting up the Event System")
    print("-" * 60)
    event_logger = GameEventLogger()
    # `subscribe_all` means the logger will receive every event published on the bus.
    game.event_bus.subscribe_all(event_logger)
    print("GameEventLogger is now subscribed to all game events.")

    # --- 4. Observer Pattern ---
    # The Observer pattern allows objects to be notified of state changes.
    print("\n4️⃣  Attaching a State Observer")
    print("-" * 60)
    state_observer = GameStateObserver()
    # We attach the observer to the game instance.
    game.attach(state_observer)
    print("GameStateObserver is now attached to the game.")

    # Use a temporary directory for settings and saves to keep the project clean.
    with tempfile.TemporaryDirectory() as tmpdir:
        temp_path = Path(tmpdir)

        # --- 5. Settings System ---
        # The SettingsManager handles loading and saving game configurations.
        print("\n5️⃣  Managing Game Settings")
        print("-" * 60)
        settings_manager = SettingsManager(config_dir=temp_path)
        # Load settings for our game, providing default values if no file exists.
        settings = settings_manager.load_settings(
            "number_guessing",
            defaults={"difficulty": "medium", "max_guesses": 10},
        )
        print(f"Settings loaded: {settings.to_dict()}")

        # Initialize the game with the loaded settings.
        print("\nInitializing game with settings...")
        game.initialize(target=42, max_guesses=settings.get("max_guesses"))

        # --- 6. Replay System ---
        # The ReplayManager records actions for later analysis, undo, and redo.
        print("\n6️⃣  Initializing the Replay System")
        print("-" * 60)
        replay_manager = ReplayManager()
        print("ReplayManager created to record game actions.")

        # --- Simulate Gameplay ---
        print("\n🎮 Simulating a game of Number Guessing...")
        print("-" * 60)
        guesses = [30, 50, 40, 42]  # A sequence of guesses, one of which is correct.

        for guess in guesses:
            if game.is_finished():
                break

            print(f"\nPlayer guesses: {guess}")

            # Record the game state *before* the action for accurate replays and undos.
            state_before = game.get_public_state()
            timestamp = time.time()

            # Execute the action in the game engine.
            game.execute_action(guess)

            # Record the action in the ReplayManager.
            replay_manager.record_action(
                timestamp=timestamp,
                actor="Player",
                action_type="GUESS",
                data={"guess": guess},
                state_before=state_before,
            )

        # --- 7. Save/Load System ---
        # The SaveLoadManager handles serializing and deserializing the game state.
        print("\n7️⃣  Saving and Loading Game State")
        print("-" * 60)
        save_manager = SaveLoadManager(save_dir=temp_path)

        final_state = game.get_public_state()
        save_path = save_manager.save("number_guessing", final_state, save_name="demo_save")
        print(f"Game state saved to: {save_path.name}")

        # Verify the save by listing available save files.
        saves = save_manager.list_saves("number_guessing")
        print(f"Total saves for this game: {len(saves)}")

        # Load the game state back from the file.
        loaded_state = save_manager.load(save_path)
        print(f"Successfully loaded save created at: {loaded_state['timestamp']}")

        # --- 8. Replay Analysis ---
        # Review the history of actions recorded by the ReplayManager.
        print("\n8️⃣  Analyzing the Recorded Replay")
        print("-" * 60)
        history = replay_manager.get_history()
        print(f"Total actions recorded: {len(history)}")
        for i, action in enumerate(history, 1):
            print(f"  Action {i}: {action.action_type} -> {action.data['guess']}")

        # --- 9. Undo/Redo System ---
        # Demonstrate the undo functionality of the ReplayManager.
        print("\n9️⃣  Demonstrating Undo/Redo")
        print("-" * 60)
        print(f"Is undo possible? {replay_manager.can_undo()}")
        if replay_manager.can_undo():
            undone_action = replay_manager.undo()
            print(f"Action undone: {undone_action.data}")
            print(f"Is redo possible? {replay_manager.can_redo()}")

        # --- 10. Event History ---
        # The Event Bus also keeps a history of all events that were published.
        print("\n🔟 Reviewing Event History")
        print("-" * 60)
        event_history = game.event_bus.get_history()
        print(f"Total events recorded by the bus: {len(event_history)}")
        event_types = {}
        for event in event_history:
            event_types[event.type] = event_types.get(event.type, 0) + 1
        print("Summary of event types:")
        for event_type, count in event_types.items():
            print(f"  - {event_type}: {count} occurrence(s)")

    print("\n" + "=" * 60)
    print("✅ Architectural Demonstration Complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
