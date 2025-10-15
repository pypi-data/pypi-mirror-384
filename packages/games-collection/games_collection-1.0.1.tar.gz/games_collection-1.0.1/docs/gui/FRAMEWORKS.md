# GUI Framework Support

The Games repository supports multiple GUI frameworks to ensure compatibility across different environments and platforms.

## Available Frameworks

### PyQt5 (Recommended)

**Status**: Primary framework for new GUIs

PyQt5 is the recommended GUI framework for the Games repository because:

- ✅ Works in headless CI/CD environments
- ✅ Better cross-platform support (Linux, Windows, macOS)
- ✅ More robust and feature-rich
- ✅ Professional appearance with modern widgets
- ✅ Extensive documentation and community support

**Installation:**

```bash
pip install games-collection[gui]
# or
pip install pyqt5
```

**Available Games:**

- Dots and Boxes (paper_games/dots_and_boxes/gui_pyqt.py)
- Go Fish (card_games/go_fish/gui_pyqt.py)
- Gin Rummy (card_games/gin_rummy/gui_pyqt.py)
- Blackjack (card_games/blackjack/gui_pyqt.py)
- Solitaire (card_games/solitaire/gui_pyqt.py)
- Spades (card_games/spades/gui_pyqt.py)
- Dots and Boxes (`paper_games/dots_and_boxes/gui_pyqt.py`)
- Go Fish (`card_games/go_fish/gui_pyqt.py`)
- War (`card_games/war/gui_pyqt.py`)

### Tkinter (Legacy)

**Status**: Legacy framework, being phased out

Tkinter was the original GUI framework used in this repository. However, it has limitations:

- ❌ Not available in all Python installations
- ❌ Requires X11 display server (problematic in CI/CD)
- ❌ Less consistent cross-platform behavior
- ❌ Limited widget set

**Available Games:**

- Bridge (card_games/bridge/gui.py)
- Gin Rummy (card_games/gin_rummy/gui.py)
- Spades (card_games/spades/gui.py)

## Migration Status

**For up-to-date migration status, see [MIGRATION_STATUS.md](../MIGRATION_STATUS.md) in the repository root.**

For detailed migration instructions, see `MIGRATION_GUIDE.md`.

### Quick Summary

| Status | Count | Percentage |
| ------------ | ----- | ---------- |
| ✅ Completed | 3/14 | 21% |
| ⏳ Remaining | 11/14 | 79% |

**Completed**: Dots and Boxes, Go Fish, Gin Rummy

**Remaining**: Battleship (paper games), Blackjack, Bluff, Bridge, Crazy Eights, Hearts, Poker, Solitaire, Spades, Uno, War (card games)
**Completed**: Battleship, Dots and Boxes, Go Fish

**Remaining**: Blackjack, Bluff, Bridge, Crazy Eights, Gin Rummy, Hearts, Poker, Solitaire, Spades, Uno, War (card games)
**Completed**: Dots and Boxes, Go Fish, Blackjack

**Remaining**: Battleship (paper games), Bluff, Bridge, Crazy Eights, Gin Rummy, Hearts, Poker, Solitaire, Spades, Uno, War (card games)
**Completed**: Dots and Boxes, Go Fish, Bluff

**Remaining**: Battleship (paper games), Blackjack, Bridge, Crazy Eights, Gin Rummy, Hearts, Poker, Solitaire, Spades, Uno, War (card games)
**Completed**: Dots and Boxes, Go Fish, Crazy Eights

**Remaining**: Battleship (paper games), Blackjack, Bluff, Bridge, Gin Rummy, Hearts, Poker, Solitaire, Spades, Uno, War (card games)
**Completed**: Dots and Boxes, Go Fish, Hearts

**Remaining**: Battleship (paper games), Blackjack, Bluff, Bridge, Crazy Eights, Gin Rummy, Poker, Solitaire, Spades, Uno, War (card games)
**Completed**: Dots and Boxes, Go Fish, Solitaire

**Remaining**: Battleship (paper games), Blackjack, Bluff, Bridge, Crazy Eights, Gin Rummy, Hearts, Poker, Spades, Uno, War (card games)
**Completed**: Dots and Boxes, Go Fish, Spades

**Remaining**: Battleship (paper games), Blackjack, Bluff, Bridge, Crazy Eights, Gin Rummy, Hearts, Poker, Solitaire, Uno, War (card games)
**Completed**: Dots and Boxes, Go Fish, Uno

**Remaining**: Battleship (paper games), Blackjack, Bluff, Bridge, Crazy Eights, Gin Rummy, Hearts, Poker, Solitaire, Spades, War (card games)

## Using GUIs

### Running a Game with GUI

```bash
# Using module syntax (recommended)
python -m paper_games.dots_and_boxes --gui

# Using entry point (if installed via pip)
games-dots-and-boxes --gui
```

### Checking Framework Availability

Use the provided utility script:

```bash
# Check what frameworks are available
python scripts/test_gui.py --check-framework all

# List all games and their GUI support
python scripts/test_gui.py --list

# Check specific game
python scripts/test_gui.py --check-game paper_games/dots_and_boxes --framework pyqt5
```

## For Developers

### Creating a New GUI

When creating a new game GUI, use PyQt5:

```python
from PyQt5.QtWidgets import QApplication, QWidget
import sys

class MyGameGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("My Game")
        # Build your GUI here

def run_gui():
    app = QApplication.instance() or QApplication(sys.argv)
    window = MyGameGUI()
    window.show()
    app.exec()

if __name__ == "__main__":
    run_gui()
```

### Using BaseGUI

For consistency, use the BaseGUI class:

```python
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
        # Implement your layout
        pass

    def update_display(self):
        # Update UI based on game state
        pass
```

### Testing GUIs

```python
import pytest

@pytest.mark.gui
class TestMyGamePyQt:
    def test_import(self):
        from my_game.gui_pyqt import MyGameGUI
        assert MyGameGUI is not None

    @pytest.mark.skipif(not has_display(), reason="Requires display")
    def test_initialization(self, qtbot):
        from my_game.gui_pyqt import MyGameGUI

        window = MyGameGUI()
        qtbot.addWidget(window)
        assert window is not None
```

## FAQ

### Q: Why not use Pygame?

Pygame is better suited for games with real-time graphics and animations. Most games in this repository are turn-based and benefit more from traditional widget-based GUIs that PyQt5 provides. However, Pygame is still available as an optional dependency for games that need it (like Uno's sound effects).

### Q: Can I still use tkinter?

Yes, tkinter GUIs are still available for games that haven't been migrated yet. However, they may not work in all environments (especially CI/CD systems and headless servers).

### Q: How do I migrate my game from tkinter to PyQt5?

See `MIGRATION_GUIDE.md` for a comprehensive guide with examples.

### Q: What about web-based GUIs?

Web-based GUIs are out of scope for this project, which focuses on desktop applications. However, the game engines are designed to be UI-agnostic, so you could create web frontends using Flask or similar frameworks.

## Resources

- [PyQt5 Documentation](https://www.riverbankcomputing.com/static/Docs/PyQt5/)
- [Qt Documentation](https://doc.qt.io/qt-5/)
- [Migration Guide](GUI_MIGRATION_GUIDE.md)
- [Test Utility](../scripts/test_gui.py)
