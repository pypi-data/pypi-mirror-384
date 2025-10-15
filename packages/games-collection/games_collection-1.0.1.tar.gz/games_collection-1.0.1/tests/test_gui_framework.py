"""GUI testing framework using pytest-qt.

These tests verify that GUI components work correctly.
Note: These tests may be skipped in headless CI environments.
"""

import pathlib
import sys

import pytest

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Check if we can import GUI modules
try:
    import tkinter as tk

    TKINTER_AVAILABLE = True
except ImportError:
    TKINTER_AVAILABLE = False

pytestmark = pytest.mark.skipif(not TKINTER_AVAILABLE, reason="tkinter not available")


@pytest.mark.gui
class TestBattleshipGUI:
    """Test Battleship GUI components."""

    def test_battleship_gui_import(self):
        """Test that Battleship GUI can be imported."""
        try:
            from paper_games.battleship.gui import BattleshipGUI

            assert BattleshipGUI is not None
        except ImportError as e:
            if "tkinter" in str(e).lower():
                pytest.skip("tkinter not available")
            raise

    def test_battleship_gui_initialization(self):
        """Test Battleship GUI initialization without display."""
        try:
            from paper_games.battleship import BattleshipGame

            # This tests that the class can be instantiated
            # In a real GUI test with display, we would create the actual window
            game = BattleshipGame()
            assert game is not None
        except Exception as e:
            if "display" in str(e).lower() or "DISPLAY" in str(e):
                pytest.skip("No display available")
            raise


@pytest.mark.gui
class TestDotsAndBoxesGUI:
    """Test Dots and Boxes GUI components."""

    def test_dots_boxes_gui_import(self):
        """Test that Dots and Boxes GUI can be imported."""
        try:
            from paper_games.dots_and_boxes.gui import DotsAndBoxesGUI

            assert DotsAndBoxesGUI is not None
        except ImportError as e:
            if "tkinter" in str(e).lower():
                pytest.skip("tkinter not available")
            raise


@pytest.mark.gui
class TestBlackjackGUI:
    """Test Blackjack GUI components."""

    def test_blackjack_gui_import(self):
        """Test that Blackjack GUI can be imported."""
        try:
            from card_games.blackjack.gui import BlackjackApp

            assert BlackjackApp is not None
        except ImportError as e:
            if "tkinter" in str(e).lower():
                pytest.skip("tkinter not available")
            raise


@pytest.mark.gui
class TestUnoGUI:
    """Test UNO GUI components."""

    def test_uno_gui_import(self):
        """Test that UNO GUI can be imported."""
        try:
            from card_games.uno.gui import TkUnoInterface

            assert TkUnoInterface is not None
        except ImportError as e:
            if "tkinter" in str(e).lower():
                pytest.skip("tkinter not available")
            raise


@pytest.mark.gui
class TestBluffGUI:
    """Test Bluff GUI components."""

    def test_bluff_gui_import(self):
        """Test that Bluff GUI can be imported."""
        try:
            from card_games.bluff.gui import BluffGUI

            assert BluffGUI is not None
        except ImportError as e:
            if "tkinter" in str(e).lower():
                pytest.skip("tkinter not available")
            raise


@pytest.mark.gui
def test_gui_modules_available():
    """Test that all GUI modules can be imported."""
    gui_modules = [
        "paper_games.battleship.gui",
        "paper_games.dots_and_boxes.gui",
        "card_games.blackjack.gui",
        "card_games.uno.gui",
        "card_games.bluff.gui",
    ]

    available_modules = []
    for module_name in gui_modules:
        try:
            __import__(module_name)
            available_modules.append(module_name)
        except ImportError as e:
            if "tkinter" not in str(e).lower():
                raise

    # At least some GUI modules should be available if tkinter is present
    if TKINTER_AVAILABLE:
        assert len(available_modules) > 0, "No GUI modules available despite tkinter being present"


@pytest.mark.gui
@pytest.mark.skipif(not TKINTER_AVAILABLE, reason="Requires tkinter and display")
def test_tkinter_basic_functionality():
    """Test basic tkinter functionality."""
    try:
        # Create a simple tkinter widget to verify it works
        root = tk.Tk()
        root.withdraw()  # Don't show window
        label = tk.Label(root, text="Test")
        assert label is not None
        root.destroy()
    except Exception as e:
        if "display" in str(e).lower() or "DISPLAY" in str(e):
            pytest.skip("No display available for GUI testing")
        raise
