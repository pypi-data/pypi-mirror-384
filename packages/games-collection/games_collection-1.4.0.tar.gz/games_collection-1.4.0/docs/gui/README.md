# GUI Framework Implementation

## 🎮 Overview

This document provides a quick overview of the GUI framework implementation in the Games repository. For detailed information, see the documentation in the `docs/` directory.

## ✅ What's Been Done

The Games repository now supports **PyQt5** as its primary GUI framework, addressing issues with tkinter availability in CI/CD and headless environments.

### Implemented Components

1. **Base Infrastructure** (`common/gui_base_pyqt.py`)

   - Abstract base class for all PyQt5 GUIs
   - Configuration system with GUIConfig
   - Helper methods for common UI elements
   - Theme and sound manager integration

1. **Working Examples**

   - `paper_games/dots_and_boxes/gui_pyqt.py` – Custom board rendering with QPainter
   - `card_games/go_fish/gui_pyqt.py` – Scoreboard driven, card-request workflow
   - `card_games/bluff/gui_pyqt.py` – Turn-based multiplayer table with claim/challenge dialogs

1. **Go Fish GUI** (`card_games/go_fish/gui_pyqt.py`)

   - Full PyQt5 implementation of a multi-player card game
   - Scoreboard, request controls, and animated celebrations
   - Demonstrates integration without relying on `BaseGUI`

1. **Bridge GUI** (`card_games/bridge/gui_pyqt.py`)

   - Subclasses `BaseGUI` to reuse shared theming utilities
   - Custom `TrickDisplay` widget replaces the Tkinter canvas
   - QTimer-driven bidding and play sequencing mirrors the Tkinter flow

1. **Test Framework** (`tests/test_gui_pyqt.py`)

   - pytest-qt integration
   - Import and structure validation
   - All tests passing (now covering Dots and Boxes, Go Fish, Bluff)
   - Coverage for Dots and Boxes, Go Fish, and Bridge modules

1. **Documentation**

   - `MIGRATION_GUIDE.md` - Complete migration guide
   - `FRAMEWORKS.md` - Framework overview
   - `PYQT5_IMPLEMENTATION.md` - Implementation details

1. **Developer Tools**

   - `scripts/test_gui.py` - Check framework availability
   - `scripts/validate_pyqt5.py` - Validate implementation

## 🚀 Quick Start

### Check Framework Availability

```bash
python scripts/test_gui.py --check-framework all
```

Output:

```
GUI Framework Availability:
----------------------------------------
Tkinter: ✗ Not available
PyQt5:   ✓ Available
```

### List Games with GUI Support

```bash
python scripts/test_gui.py --list
```

This command now introspects the `card_games` and `paper_games` packages to detect both Tkinter (`gui.py`) and PyQt5 (`gui_pyqt.py`) implementations.
Whenever a new GUI module is added, it is automatically included in the output without requiring manual updates to `scripts/test_gui.py`.

### Validate PyQt5 Implementation

```bash
python scripts/validate_pyqt5.py
```

Output:

```
✅ All validations PASSED

PyQt5 implementation is working correctly!
```

### Run Tests

```bash
pytest tests/test_gui_pyqt.py -v
```

## 📊 Migration Status

🎉 **Migration Complete!** All 16 games with GUI support have been successfully migrated to PyQt5.

### Completed (16/16 - 100%)

**Paper Games (2/2):**

- ✅ Battleship
- ✅ Dots and Boxes

**Card Games (14/14):**

- ✅ Blackjack
- ✅ Bluff
- ✅ Bridge
- ✅ Canasta
- ✅ Crazy Eights
- ✅ Gin Rummy
- ✅ Go Fish
- ✅ Hearts
- ✅ Pinochle
- ✅ Poker
- ✅ Solitaire
- ✅ Spades
- ✅ Uno
- ✅ War

For detailed migration information, see [GUI_MIGRATION_STATUS.md](../status/GUI_MIGRATION_STATUS.md).

## 🛠️ For Developers

### Creating a New PyQt5 GUI

```python
from PyQt5.QtWidgets import QApplication, QWidget
from common.gui_base_pyqt import BaseGUI, GUIConfig

class MyGameGUI(BaseGUI):
    def __init__(self):
        config = GUIConfig(
            window_title="My Game",
            window_width=800,
            window_height=600,
        )
        super().__init__(config=config)
        self.build_layout()

    def build_layout(self):
        # Build your UI here
        pass

    def update_display(self):
        # Update UI based on game state
        pass
```

### Migrating from Tkinter

See `MIGRATION_GUIDE.md` for:

- Widget mapping (tkinter → PyQt5)
- Event handling patterns
- Layout management
- Common gotchas and solutions
- Step-by-step process

### Reference Implementation

Study `paper_games/dots_and_boxes/gui_pyqt.py` for:

- Custom widget creation (BoardCanvas)
- Mouse event handling
- QPainter for custom drawing
- Timer usage
- Layout management
- Game logic integration

### Development Workflow

Install the development dependencies and register the shared pre-commit hooks so your local environment matches CI formatting and
linting:

```bash
pip install -e ".[dev]"
pre-commit install

# Optional: run all hooks before pushing changes
pre-commit run --all-files
```

## 📚 Documentation

| Document                  | Purpose                                      |
| ------------------------- | -------------------------------------------- |
| `MIGRATION_GUIDE.md`      | Step-by-step migration from tkinter to PyQt5 |
| `FRAMEWORKS.md`           | Framework overview and guidelines            |
| `PYQT5_IMPLEMENTATION.md` | Complete implementation summary              |
| This file                 | Quick reference                              |

## 🧪 Testing

### Run GUI Tests

```bash
# All GUI tests
pytest tests/test_gui_pyqt.py -v

# With coverage
pytest tests/test_gui_pyqt.py --cov=common.gui_base_pyqt --cov=paper_games.dots_and_boxes.gui_pyqt \
    --cov=card_games.go_fish.gui_pyqt --cov=card_games.bridge.gui_pyqt
```

### Validate Implementation

```bash
# Validate all components
python scripts/validate_pyqt5.py

# Check specific game
python scripts/test_gui.py --check-game paper_games/dots_and_boxes --framework pyqt5
```

## 🎯 Key Benefits

### Why PyQt5 Over Tkinter?

1. **Headless Support**: Works in CI/CD without X11 display
1. **Cross-Platform**: Consistent behavior across OS platforms
1. **Professional UI**: Modern widgets and appearance
1. **Better Performance**: More efficient rendering
1. **Rich Features**: Extensive widget library

### Code Quality

All code meets repository standards:

- ✅ Black formatting (160 char lines)
- ✅ Ruff linting (no errors)
- ✅ Type hints throughout
- ✅ Google-style docstrings
- ✅ Complexity ≤ 10 per function

## 📦 Dependencies

Install with:

```bash
# GUI support (includes PyQt5)
pip install games-collection[gui]

# Or directly
pip install pyqt5>=5.15
```

## 🤝 Contributing

To develop new GUIs or enhance existing ones:

1. Use PyQt5 as the primary framework
1. Follow `MIGRATION_GUIDE.md` for best practices
1. Reference existing implementations (e.g., `card_games/solitaire/gui_pyqt.py` for complex GUIs)
1. Use `common/gui_base_pyqt.py` for consistency
1. Add tests in `tests/test_gui_pyqt.py`
1. Run validation: `python scripts/validate_pyqt5.py`

## 📝 Design Decisions

### Why Separate Files?

- `gui.py` - Original tkinter version (legacy)
- `gui_pyqt.py` - New PyQt5 version

**Benefits**:

- Backward compatibility during transition
- Easy comparison and testing
- Clear migration path
- Reduced risk of breaking changes

### Why BaseGUI?

- Consistent API across games
- Shared utilities (logging, themes, shortcuts)
- Reduced code duplication
- Easier maintenance

## 🔮 Future Work

Potential enhancements:

1. Add theme customization UI
1. Implement network multiplayer
1. Add game replay system
1. Create tournament mode interface
1. Add animation effects
1. Enhance accessibility features

## 📞 Support

For help with GUI development:

1. Read the documentation in `docs/`
1. Study the example: `paper_games/dots_and_boxes/gui_pyqt.py`
1. Use validation tools: `scripts/validate_pyqt5.py`
1. Check framework availability: `scripts/test_gui.py`
1. Open an issue on GitHub

## ✨ Summary

The PyQt5 implementation successfully:

- ✅ Resolved tkinter availability issues
- ✅ Created robust, reusable infrastructure
- ✅ Demonstrated working proof of concept
- ✅ Provided comprehensive documentation
- ✅ Established clear migration path
- ✅ All tests passing
- ✅ All code quality checks passing

The foundation is in place for completing the migration of all remaining GUIs! 🚀
