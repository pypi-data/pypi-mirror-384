# Architecture Examples

This directory contains example scripts demonstrating the architecture components.

## Running Examples

All examples should be run from the repository root with the correct PYTHONPATH:

```bash
cd /home/runner/work/Games/Games
PYTHONPATH=/home/runner/work/Games/Games python examples/architecture_demo.py
```

Or use the Python module approach:

```bash
cd /home/runner/work/Games/Games
python -m examples.architecture_demo
```

## Available Examples

### cli_utils_demo.py

Comprehensive demonstration of CLI enhancement features:

- **ASCII Art** - Banners, boxes, victory/defeat art
- **Rich Text** - Headers, status messages, highlighting
- **Progress Indicators** - Progress bars and spinners
- **Interactive Menus** - Arrow key navigation with fallback
- **Command History** - History navigation and autocomplete
- **Themes** - Predefined and custom color schemes

Run with:

```bash
python examples/cli_utils_demo.py
```

### cli_enhanced_game.py

Complete working game using all CLI utilities - a number guessing game with:

- Interactive menu system
- Difficulty selection
- Progress bars and spinners
- Command history and autocomplete
- Themed UI elements
- Status messages and ASCII art

Run with:

```bash
python examples/cli_enhanced_game.py
```

### architecture_demo.py

A comprehensive demonstration of all architecture components:

1. **Plugin System** - Loading and managing plugins
1. **Game Engine** - Creating game instances
1. **Event System** - Event-driven architecture
1. **Observer Pattern** - State change notifications
1. **Settings System** - Configuration management
1. **Replay System** - Action recording
1. **Save/Load System** - Game state persistence
1. **Replay Analysis** - Reviewing recorded actions
1. **Undo System** - Undoing/redoing actions
1. **Event History** - Analyzing event patterns

The demo uses the example number guessing game plugin to demonstrate all features in action.

### gui_enhancements_demo.py

An interactive demonstration of all GUI enhancement features:

1. **Theme System** - Switch between light, dark, and high contrast themes
1. **Animation Framework** - Visual effects and transitions
1. **Accessibility Features** - High contrast mode, focus indicators
1. **Internationalization** - Multi-language support
1. **Keyboard Shortcuts** - Complete shortcut system with F1 help

To run:

```bash
python examples/gui_enhancements_demo.py
```

Features demonstrated:

- Real-time theme switching with color updates
- Animated button highlights
- Accessibility toggles (high contrast, focus indicators)
- Language selection (shows available translations)
- Keyboard shortcuts (F1 for help, Ctrl+T/L for themes, Esc to quit)

### Expected Output

When you run the demo, you'll see:

- Plugin discovery and loading
- Event notifications as game progresses
- State change observations
- Settings loading and usage
- Game being played with 4 guesses
- Save/load operations
- Replay analysis showing all actions
- Undo/redo functionality
- Event statistics

## Creating Your Own Examples

To create a new example:

1. Create a Python file in this directory
1. Import the architecture components you need
1. Use the example_plugin or create your own test plugin
1. Make the file executable: `chmod +x your_example.py`
1. Add documentation to this README

Example template:

```python
#!/usr/bin/env python
"""Your example description."""

from pathlib import Path
from common.architecture import PluginManager

def main():
    # Your example code here
    pass

if __name__ == "__main__":
    main()
```

## Tips

- Always run examples from the repository root
- Use `PYTHONPATH` to ensure imports work correctly
- Check the plugin system is working with `discover_plugins()`
- Use temporary directories for save/settings to avoid cluttering the repo
- Add descriptive output so others can follow what's happening

## Further Reading

- See `ARCHITECTURE.md` for detailed component documentation
- Check `plugins/README.md` for plugin development guide
- Review `tests/test_architecture.py` for usage patterns
