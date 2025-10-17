# Game Plugins

This directory serves as the repository for third-party game plugins, which can be dynamically discovered and loaded into the main application without modifying the core codebase. This document provides a comprehensive guide for developers looking to create, distribute, and manage plugins.

## What is a Plugin?

A plugin is a self-contained Python module or package that extends the application with a new game. To be recognized, a plugin must implement the `GamePlugin` interface, which involves providing:

1.  **Game Engine**: A class inheriting from `GameEngine` that encapsulates the game's logic, rules, and state management.
2.  **Metadata**: Information about the plugin, such as its name, version, author, and description, provided via a `PluginMetadata` object.
3.  **Lifecycle Hooks**: `initialize()` and `shutdown()` methods to manage the plugin's state.
4.  **Optional Components**:
    -   A UI class for integration with a graphical user interface.
    -   A configuration schema to allow users to customize game settings.

A plugin must expose an instance of its `GamePlugin` implementation through a module-level variable named `plugin`.

## Creating a Plugin

### Basic Structure (Single File)

For simple games, a single Python file is sufficient. Create a new file in this directory (e.g., `my_game.py`):

```python
from common.architecture.engine import GameEngine, GameState, GamePhase
from common.architecture.plugin import GamePlugin, PluginMetadata
from typing import Any, Type, List, Dict, Optional

class MyGameEngine(GameEngine):
    """Implements the core logic for MyGame."""
    def initialize(self, **kwargs: Any) -> None:
        self._state = GameState(phase=GamePhase.RUNNING)
        print("MyGameEngine initialized.")

    def reset(self) -> None:
        self.initialize()

    def is_finished(self) -> bool:
        return self._state.phase == GamePhase.FINISHED

    def get_current_player(self) -> Optional[str]:
        return "Player1"

    def get_valid_actions(self) -> List[Any]:
        return ["action1", "action2"]

    def execute_action(self, action: Any) -> bool:
        print(f"Executing action: {action}")
        return True

class MyGamePlugin(GamePlugin):
    """Plugin entry point for MyGame."""
    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="my_game",
            version="1.0.0",
            author="Your Name",
            description="An awesome game."
        )

    def initialize(self, **kwargs: Any) -> None:
        print(f"'{self.get_metadata().name}' plugin initialized.")

    def shutdown(self) -> None:
        print(f"'{self.get_metadata().name}' plugin shutting down.")

    def get_game_class(self) -> Type[GameEngine]:
        return MyGameEngine

# The plugin manager requires a module-level 'plugin' variable.
plugin: GamePlugin = MyGamePlugin()
```

### Package Structure (Directory)

For more complex plugins with multiple modules, assets, or UI components, a package structure is recommended:

```
plugins/
  my_game/
    ├── __init__.py      # Plugin definition and entry point
    ├── engine.py        # Core game engine logic
    ├── ui.py            # Optional UI components
    └── assets/          # Game assets (images, sounds, etc.)
```

The `__init__.py` file should define and export the `plugin` instance, similar to the single-file structure.

## Plugin Lifecycle

The `PluginManager` controls the lifecycle of a plugin, which consists of the following stages:

1.  **Discovery**: The manager scans the `plugins` directory for Python files and packages that appear to be plugins.
2.  **Loading**: When `manager.load_plugin("my_plugin")` is called, the manager imports the plugin's module or package.
3.  **Instantiation**: The manager looks for a module-level variable named `plugin` and verifies that it is an instance of `GamePlugin`.
4.  **Initialization**: The plugin's `initialize()` method is called, allowing it to perform setup tasks, such as loading resources or setting up event listeners. The plugin is now considered "active."
5.  **Execution**: The main application can now retrieve the plugin via `manager.get_plugin()` and access its `GameEngine` class to create and run game instances.
6.  **Shutdown**: When the plugin is no longer needed, `manager.unload_plugin()` calls the plugin's `shutdown()` method for cleanup before removing it from the list of active plugins.

## Loading and Using Plugins

Plugins are managed programmatically using the `PluginManager`:

```python
from common.architecture.plugin import PluginManager
from pathlib import Path

# Initialize the manager with the plugin directory
manager = PluginManager(plugin_dirs=[Path("./plugins")])

# Discover all available plugins
available_plugins = manager.discover_plugins()
print(f"Found plugins: {available_plugins}")

# Load a specific plugin
if manager.load_plugin("example_plugin"):
    print("Plugin 'example_plugin' loaded successfully.")

    # Get the plugin instance
    plugin = manager.get_plugin("example_plugin")
    if plugin:
        GameClass = plugin.get_game_class()

        # Create and use the game engine
        game = GameClass()
        game.initialize(target=42, max_guesses=7)
        print("Game instance created and initialized.")
```

## Example Plugin

See `example_plugin.py` in this directory for a complete, well-documented example of a number guessing game. It serves as an excellent starting point for new developers.

## Best Practices

To ensure your plugin is robust, maintainable, and integrates well with the ecosystem, follow these best practices:

1.  **Emit Events for State Changes**: Instead of tightly coupling your game logic to other components, emit events for significant occurrences (e.g., `PLAYER_TURN_CHANGED`, `SCORE_UPDATED`). This allows UI components, analytics, or other systems to react to changes without direct dependencies.

    ```python
    # In your GameEngine
    self.emit_event("GAME_OVER", data={"winner": "Player1"})
    ```

2.  **Design for Observable State**: Your `GameEngine` should be designed as an `Observable`. When the state changes in a way that the UI needs to reflect, call `self.notify()` to push updates to observers.

    ```python
    # In your GameEngine, after a move
    self.notify(board_updated=True, new_board_state=self.board)
    ```

3.  **Implement Save/Load**: Support persistence by implementing `save_state()` and `load_state()` in your `GameEngine`. This is crucial for a good user experience.

4.  **Provide a Configuration Schema**: If your game has tunable parameters (e.g., difficulty, board size), define them in a schema returned by `get_config_schema()`. This allows for automatic UI generation for settings.

5.  **Write Comprehensive Documentation**: Include detailed docstrings for all classes and methods. Add a `README.md` inside your plugin's package if it is complex.

6.  **Write Unit Tests**: Create tests for your game logic to ensure it is correct and to prevent regressions.

## Plugin Requirements

-   Must implement the `GamePlugin` abstract base class.
-   Must provide a game engine class that inherits from `GameEngine`.
-   The plugin module or package must define a module-level variable named `plugin` that holds an instance of your `GamePlugin` implementation.
-   Should handle initialization and cleanup gracefully within `initialize()` and `shutdown()`.

## Distribution

To distribute your plugin, simply package your plugin file or directory (e.g., in a ZIP archive). Users can install it by placing the contents into their `plugins` folder.

## Troubleshooting

### Plugin Not Loading

-   **Is the file/directory in the correct `plugins` folder?**
-   **Does your plugin file/package export a variable named `plugin`?** This is case-sensitive.
-   **Does your plugin class correctly implement the `GamePlugin` interface?**
-   **Are there any error messages in the console output?** Check for `ImportError` or other exceptions during loading.

### Import Errors

-   Ensure that your plugin correctly imports from `common.architecture`. The application's root directory should be in the Python path.
-   List any third-party dependencies in your plugin's metadata.

## Contributing

If you create a useful plugin, consider contributing it to the main repository or sharing it with the community! See the main `CONTRIBUTING.md` for guidelines on submitting pull requests.
