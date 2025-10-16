#!/usr/bin/env python
"""Demonstration of the architecture system.

This script shows how to use all the architecture components together:
- Plugin system
- Event system
- Observer pattern
- Save/load
- Settings
- Replay/undo
"""

import tempfile
from pathlib import Path

from common.architecture import Event, EventHandler, Observer, PluginManager, ReplayManager, SaveLoadManager, SettingsManager


class GameEventLogger(EventHandler):
    """Logs all game events."""

    def handle(self, event: Event):
        print(f"📢 Event: {event.type}")
        if event.data:
            print(f"   Data: {event.data}")


class GameStateObserver(Observer):
    """Observes game state changes."""

    def update(self, observable, **kwargs):
        print(f"👀 State changed: {kwargs}")


def main():
    """Run the architecture demonstration."""
    print("=" * 60)
    print("Architecture System Demonstration")
    print("=" * 60)

    # 1. Plugin System
    print("\n1️⃣  Plugin System")
    print("-" * 60)
    plugin_manager = PluginManager(plugin_dirs=[Path("./plugins")])

    print("Discovering plugins...")
    plugins = plugin_manager.discover_plugins()
    print(f"Found: {plugins}")

    print("\nLoading example_plugin...")
    plugin_manager.load_plugin("example_plugin")

    plugin = plugin_manager.get_plugin("example_plugin")
    metadata = plugin_manager.get_plugin_metadata("example_plugin")
    print(f"Loaded: {metadata.name} v{metadata.version}")

    # 2. Create game instance
    print("\n2️⃣  Game Engine")
    print("-" * 60)
    GameClass = plugin.get_game_class()
    game = GameClass()

    # 3. Event System
    print("\n3️⃣  Event System")
    print("-" * 60)
    event_logger = GameEventLogger()
    game.event_bus.subscribe_all(event_logger)
    print("Event logger attached")

    # 4. Observer Pattern
    print("\n4️⃣  Observer Pattern")
    print("-" * 60)
    state_observer = GameStateObserver()
    game.attach(state_observer)
    print("State observer attached")

    # 5. Settings System
    print("\n5️⃣  Settings System")
    print("-" * 60)
    with tempfile.TemporaryDirectory() as tmpdir:
        settings_manager = SettingsManager(config_dir=Path(tmpdir))
        settings = settings_manager.load_settings(
            "number_guessing",
            defaults={"difficulty": "medium", "max_guesses": 10},
        )
        print(f"Settings loaded: {settings.to_dict()}")

        # Initialize game with settings
        print("\nInitializing game...")
        game.initialize(target=42, max_guesses=settings.get("max_guesses"))

        # 6. Replay System
        print("\n6️⃣  Replay System")
        print("-" * 60)
        replay_manager = ReplayManager()
        print("Replay manager created")

        # Play the game
        print("\n🎮 Playing the game...")
        print("-" * 60)
        guesses = [30, 50, 40, 42]

        import time

        for guess in guesses:
            if game.is_finished():
                break

            print(f"\nGuessing: {guess}")

            # Record action for replay
            state_before = game.get_public_state()
            timestamp = time.time()

            game.execute_action(guess)

            replay_manager.record_action(
                timestamp=timestamp,
                actor="Player",
                action_type="GUESS",
                data={"guess": guess},
                state_before=state_before,
            )

        # 7. Save/Load System
        print("\n7️⃣  Save/Load System")
        print("-" * 60)
        save_manager = SaveLoadManager(save_dir=Path(tmpdir))

        final_state = game.get_public_state()
        save_path = save_manager.save("number_guessing", final_state, save_name="demo_save")
        print(f"Game saved to: {save_path.name}")

        # List saves
        saves = save_manager.list_saves("number_guessing")
        print(f"Total saves: {len(saves)}")

        # Load the save
        loaded = save_manager.load(save_path)
        print(f"Loaded save from: {loaded['timestamp']}")

        # 8. Replay Analysis
        print("\n8️⃣  Replay Analysis")
        print("-" * 60)
        history = replay_manager.get_history()
        print(f"Total actions recorded: {len(history)}")
        for i, action in enumerate(history, 1):
            print(f"  {i}. {action.action_type}: {action.data['guess']}")

        # Demonstrate undo
        print("\n9️⃣  Undo System")
        print("-" * 60)
        print(f"Can undo: {replay_manager.can_undo()}")
        if replay_manager.can_undo():
            undone = replay_manager.undo()
            print(f"Undid action: {undone.data}")
            print(f"Can redo: {replay_manager.can_redo()}")

        # 10. Event History
        print("\n🔟 Event History")
        print("-" * 60)
        event_history = game.event_bus.get_history()
        print(f"Total events: {len(event_history)}")
        event_types = {}
        for event in event_history:
            event_types[event.type] = event_types.get(event.type, 0) + 1
        print("Event summary:")
        for event_type, count in event_types.items():
            print(f"  {event_type}: {count}")

    print("\n" + "=" * 60)
    print("✅ Demonstration Complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
