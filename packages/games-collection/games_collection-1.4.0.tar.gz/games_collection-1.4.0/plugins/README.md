# Game Plugins

This directory contains third-party game plugins that can be dynamically loaded without modifying the core codebase.

## What is a Plugin?

A plugin is a Python module or package that implements the `GamePlugin` interface, providing:

1. Game engine implementation
1. Metadata (name, version, author, description)
1. Optional UI components
1. Configuration schema

## Creating a Plugin

### Basic Structure

Create a Python file in this directory (e.g., `my_game.py`):

```python
from common.architecture import GameEngine, GamePlugin, PluginMetadata

class MyGameEngine(GameEngine):
    def initialize(self, **kwargs):
        # Initialize game
        pass

    def reset(self):
        # Reset game state
        pass

    def is_finished(self):
        # Check if game is finished
        return False

    def get_current_player(self):
        # Return current player
        return None

    def get_valid_actions(self):
        # Return list of valid actions
        return []

    def execute_action(self, action):
        # Execute an action
        return True

class MyGamePlugin(GamePlugin):
    def get_metadata(self):
        return PluginMetadata(
            name="my_game",
            version="1.0.0",
            author="Your Name",
            description="My awesome game"
        )

    def initialize(self, **kwargs):
        print("Plugin initialized")

    def shutdown(self):
        print("Plugin shutting down")

    def get_game_class(self):
        return MyGameEngine

# Export plugin instance
plugin = MyGamePlugin()
```

### Package Structure

For more complex plugins, create a package:

```
plugins/
  my_game/
    __init__.py      # Plugin definition
    engine.py        # Game engine
    ui.py           # Optional UI components
    assets/         # Game assets
```

## Loading Plugins

Plugins can be loaded programmatically:

```python
from common.architecture import PluginManager
from pathlib import Path

manager = PluginManager(plugin_dirs=[Path("./plugins")])

# Discover available plugins
plugins = manager.discover_plugins()
print(f"Found plugins: {plugins}")

# Load a specific plugin
success = manager.load_plugin("my_game")

# Get the plugin
plugin = manager.get_plugin("my_game")
GameClass = plugin.get_game_class()

# Create and use the game
game = GameClass()
game.initialize()
```

## Example Plugin

See `example_plugin.py` in this directory for a complete working example of a number guessing game.

To test the example plugin:

```python
from common.architecture import PluginManager
from pathlib import Path

manager = PluginManager(plugin_dirs=[Path("./plugins")])
manager.load_plugin("example_plugin")

# Get the game class
plugin = manager.get_plugin("example_plugin")
GameClass = plugin.get_game_class()

# Play the game
game = GameClass()
game.initialize(target=42, max_guesses=7)

while not game.is_finished():
    guess = int(input("Enter your guess (1-100): "))
    game.execute_action(guess)

    state = game.get_public_state()
    if state.get("finished"):
        print("Game over!")
    else:
        print(f"Guesses remaining: {state['guesses_remaining']}")
```

## Best Practices

1. **Use Events**: Emit events for important game state changes
1. **Observable State**: Make your game engine observable for GUI integration
1. **Save/Load Support**: Implement save_state() and load_state() methods
1. **Settings Support**: Use the SettingsManager for configuration
1. **Comprehensive Metadata**: Provide detailed plugin metadata
1. **Documentation**: Include docstrings and usage examples
1. **Testing**: Write tests for your game logic

## Plugin Requirements

- Must implement the `GamePlugin` interface
- Must provide a game engine class that extends `GameEngine`
- Should handle initialization and cleanup properly
- Should not depend on other plugins unless specified in metadata

## Distribution

To distribute your plugin:

1. Package your plugin files
1. Include a README with installation instructions
1. List any dependencies in the plugin metadata
1. Provide example usage code

Users can install by simply placing your plugin file/directory in the `plugins` folder.

## Troubleshooting

### Plugin Not Loading

- Check that the plugin file is in the plugins directory
- Verify the plugin exports a `plugin` variable
- Ensure the plugin implements the `GamePlugin` interface
- Check console output for error messages

### Import Errors

- Make sure `common.architecture` is importable
- Check that all dependencies are installed
- Verify Python path includes the repository root

## Contributing

If you create a useful plugin, consider contributing it to the main repository or sharing it with the community!

See the main `CONTRIBUTING.md` for guidelines on submitting plugins.
