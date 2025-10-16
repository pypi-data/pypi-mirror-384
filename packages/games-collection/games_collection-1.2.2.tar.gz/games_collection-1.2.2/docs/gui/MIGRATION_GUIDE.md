# GUI Migration Guide: From Tkinter to PyQt5

This guide explains how to migrate GUI applications from Tkinter to PyQt5 in the Games repository.

## Why Migrate to PyQt5?

1. **Better Cross-Platform Support**: PyQt5 works consistently across Linux, Windows, and macOS
1. **More Reliable**: PyQt5 is less prone to display issues in various environments
1. **Richer Widgets**: PyQt5 provides more sophisticated UI components
1. **Better Documentation**: Extensive Qt documentation and examples
1. **Professional Look**: More modern and polished appearance

## Migration Status

**For detailed game-by-game migration status, see [MIGRATION_STATUS.md](../MIGRATION_STATUS.md) in the repository root.**

### Infrastructure (Complete)

- ✅ PyQt5 base infrastructure (`common/gui_base_pyqt.py`)
- ✅ Dots and Boxes game (`paper_games/dots_and_boxes/gui_pyqt.py`)
- ✅ Test framework for PyQt5 GUIs

### Games (3/14 completed)

- ✅ **Completed**: Dots and Boxes, Go Fish, Gin Rummy

- ⏳ **Remaining**: 11 games

  - Paper games: Battleship
  - Card games: Blackjack, Bluff, Bridge, Crazy Eights, Hearts, Poker, Solitaire, Spades, Uno, War

- ✅ **Completed**: Battleship, Dots and Boxes, Go Fish

- ⏳ **Remaining**: 11 games (card games: Blackjack, Bluff, Bridge, Crazy Eights, Gin Rummy, Hearts, Poker, Solitaire, Spades, Uno, War)

- ✅ **Completed**: Dots and Boxes, Go Fish, Bluff

- ⏳ **Remaining**: 11 games

  - Paper games: Battleship
  - Card games: Blackjack, Bridge, Crazy Eights, Gin Rummy, Hearts, Poker, Solitaire, Spades, Uno, War

- ✅ **Completed**: Dots and Boxes, Go Fish, Crazy Eights

- ⏳ **Remaining**: 11 games

  - Paper games: Battleship
  - Card games: Blackjack, Bluff, Bridge, Gin Rummy, Hearts, Poker, Solitaire, Spades, Uno, War

- ✅ **Completed**: Dots and Boxes, Go Fish, Hearts

- ⏳ **Remaining**: 11 games

  - Paper games: Battleship
  - Card games: Blackjack, Bluff, Bridge, Crazy Eights, Gin Rummy, Poker, Solitaire, Spades, Uno, War

## Running PyQt5 GUIs Headlessly

Some contributors work in headless Linux environments where a display server is unavailable. Configure Qt to use the offscreen platform plugin before launching GUIs or running the PyQt5 test suite:

```bash
export QT_QPA_PLATFORM=offscreen
export XDG_RUNTIME_DIR=/tmp/qt-runtime
mkdir -p "$XDG_RUNTIME_DIR"
```

The pytest configuration in this repository sets these variables automatically, but local shells and ad-hoc scripts still need them to ensure Qt can initialize without access to a windowing system.

### Games (1/14 completed)

- ✅ **Completed**: Dots and Boxes, Go Fish, Poker
- ⏳ **Remaining**: 11 games
  - Paper games: Battleship
  - Card games: Blackjack, Bluff, Bridge, Crazy Eights, Gin Rummy, Hearts, Solitaire, Spades, Uno, War

## Quick Start for Migration

### 1. Basic Widget Mapping

| Tkinter | PyQt5 | Notes |
| --------------------------- | ---------------------------------------- | ---------------------------------------------- |
| `tk.Tk()` | `QApplication` + `QWidget`/`QMainWindow` | PyQt5 uses QApplication globally |
| `tk.Frame` | `QWidget` or `QFrame` | QFrame has borders, QWidget doesn't |
| `tk.Label` | `QLabel` | Similar API |
| `tk.Button` | `QPushButton` | Use `.clicked.connect()` instead of `command=` |
| `tk.Canvas` | Custom `QWidget` with `paintEvent()` | More powerful but requires custom painting |
| `tk.Entry` | `QLineEdit` | Similar functionality |
| `scrolledtext.ScrolledText` | `QTextEdit` | Set readonly with `.setReadOnly(True)` |
| `ttk.Style` | `QStyleSheet` or `QStyle` | Use CSS-like syntax |

### 2. Event Handling

**Tkinter:**

```python
button = tk.Button(parent, text="Click", command=self.on_click)
canvas.bind("<Button-1>", self.on_mouse_click)
canvas.bind("<Motion>", self.on_mouse_move)
```

**PyQt5:**

```python
button = QPushButton("Click", parent)
button.clicked.connect(self.on_click)

# For canvas/custom widgets, override methods:
def mousePressEvent(self, event):
    if event.button() == Qt.MouseButton.LeftButton:
        self.on_mouse_click(event)

def mouseMoveEvent(self, event):
    self.on_mouse_move(event)
```

### 3. Layout Management

**Tkinter (pack):**

```python
label.pack(side=tk.LEFT, padx=10, pady=5)
```

**PyQt5 (layout managers):**

```python
layout = QHBoxLayout()
layout.addWidget(label)
layout.setContentsMargins(10, 5, 10, 5)
parent.setLayout(layout)
```

### 4. Timers

**Tkinter:**

```python
self.root.after(500, self.callback)
```

**PyQt5:**

```python
QTimer.singleShot(500, self.callback)
```

### 5. Message Boxes

**Tkinter:**

```python
messagebox.showinfo("Title", "Message")
messagebox.showerror("Error", "Error message")
```

**PyQt5:**

```python
QMessageBox.information(self, "Title", "Message")
QMessageBox.critical(self, "Error", "Error message")
```

## Example Migration: Dots and Boxes

### Before (Tkinter)

```python
import tkinter as tk
from tkinter import messagebox

class DotsAndBoxesGUI:
    def __init__(self, root: tk.Tk, size: int = 2):
        self.root = root
        self.root.title(f"Dots and Boxes ({size}x{size})")

        self.canvas = tk.Canvas(self.root, width=300, height=300, bg="white")
        self.canvas.pack()
        self.canvas.bind("<Button-1>", self._on_click)

        button = tk.Button(self.root, text="New Game", command=self._new_game)
        button.pack()

def run_gui(size: int = 2):
    root = tk.Tk()
    DotsAndBoxesGUI(root, size=size)
    root.mainloop()
```

### After (PyQt5)

```python
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPainter, QColor, QPen

class BoardCanvas(QWidget):
    def __init__(self, gui, size: int):
        super().__init__()
        self.gui = gui
        self.setFixedSize(300, 300)

    def paintEvent(self, event):
        painter = QPainter(self)
        # Custom drawing code here

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.gui._on_click(event)

class DotsAndBoxesGUI(QWidget):
    def __init__(self, size: int = 2):
        super().__init__()
        self.setWindowTitle(f"Dots and Boxes ({size}x{size})")

        layout = QVBoxLayout()
        self.canvas = BoardCanvas(self, size)
        layout.addWidget(self.canvas)

        button = QPushButton("New Game")
        button.clicked.connect(self._new_game)
        layout.addWidget(button)

        self.setLayout(layout)

def run_gui(size: int = 2):
    app = QApplication.instance() or QApplication(sys.argv)
    window = DotsAndBoxesGUI(size=size)
    window.show()
    app.exec()
```

## Step-by-Step Migration Process

### 1. Create PyQt5 Version

Create a new file `gui_pyqt.py` alongside the existing `gui.py`:

```bash
# For card games
card_games/<game_name>/gui_pyqt.py

# For paper games
paper_games/<game_name>/gui_pyqt.py
```

### 2. Update Imports

```python
# Old
import tkinter as tk
from tkinter import messagebox, ttk

# New
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout, QMessageBox
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QPainter, QColor
```

### 3. Convert Class Structure

```python
# Old
class GameGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self._build_layout()

# New
class GameGUI(QWidget):
    def __init__(self):
        super().__init__()
        self._build_layout()
```

### 4. Convert Layouts

Use QVBoxLayout, QHBoxLayout, or QGridLayout instead of pack/grid.

### 5. Convert Event Handlers

Replace `.bind()` calls with signal/slot connections or override event methods.

### 6. Test

Create tests in `tests/test_gui_pyqt.py`:

```python
@pytest.mark.gui
class TestGamePyQt:
    def test_game_gui_import(self):
        from card_games.game_name.gui_pyqt import GameGUI
        assert GameGUI is not None
```

### 7. Update Entry Points

Update the game's `__main__.py` or CLI to use PyQt5 version:

```python
from common.gui_frameworks import launch_preferred_gui
from .gui import run_app as run_tk_gui
from .gui_pyqt import run_gui as run_pyqt_gui


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--gui-framework", choices=["tkinter", "pyqt5"], default="pyqt5")
    args = parser.parse_args()

    launch_preferred_gui(
        preferred=args.gui_framework,
        tkinter_launcher=lambda: run_tk_gui(),
        pyqt_launcher=lambda: run_pyqt_gui(),
    )
```

## Common Gotchas

### 1. QApplication Must Be Created First

```python
# Always check if QApplication exists
app = QApplication.instance()
if app is None:
    app = QApplication(sys.argv)
```

### 2. Canvas Drawing

PyQt5 doesn't have a simple Canvas widget. You need to:

- Subclass QWidget
- Override `paintEvent()`
- Use QPainter for drawing

### 3. Variable Observers

Tkinter has `StringVar`, `IntVar`, etc. with `trace()`. PyQt5 uses:

- Signals/slots
- Property change events
- Manual updates

### 4. Grid/Pack vs Layouts

PyQt5 doesn't use pack() or grid() directly. All widgets must be added to layouts:

```python
# Wrong
button.show()  # Won't display properly

# Right
layout = QVBoxLayout()
layout.addWidget(button)
parent.setLayout(layout)
```

### 5. Modal Dialogs

```python
# Tkinter
result = messagebox.askyesno("Question", "Continue?")

# PyQt5
reply = QMessageBox.question(self, "Question", "Continue?",
                             QMessageBox.StandardButton.Yes |
                             QMessageBox.StandardButton.No)
result = reply == QMessageBox.StandardButton.Yes
```

## Using BaseGUI

The repository provides `common/gui_base_pyqt.py` with common utilities:

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

## Testing PyQt5 GUIs

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

## Resources

- [PyQt5 Documentation](https://www.riverbankcomputing.com/static/Docs/PyQt5/)
- [Qt Documentation](https://doc.qt.io/qt-5/)
- [PyQt5 Tutorial](https://realpython.com/python-pyqt-gui-calculator/)

## Getting Help

If you encounter issues during migration:

1. Check this guide for common patterns
1. Review completed migrations such as `paper_games/dots_and_boxes/gui_pyqt.py`, `card_games/go_fish/gui_pyqt.py`, and `card_games/spades/gui_pyqt.py`
1. Look at completed migrations: `paper_games/dots_and_boxes/gui_pyqt.py`, `card_games/go_fish/gui_pyqt.py`, `card_games/bridge/gui_pyqt.py`
1. Consult PyQt5 documentation
1. Ask in the repository issues

## Maintenance Notes

- Keep both tkinter and PyQt5 versions during transition
- Mark tkinter versions as deprecated in docstrings
- Eventually remove tkinter versions after all migrations complete
- Update documentation to reference PyQt5 as the primary GUI framework
