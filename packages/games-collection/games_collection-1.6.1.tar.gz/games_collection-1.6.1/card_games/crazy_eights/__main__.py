"""Main entry point for the Crazy Eights card game application.

This script allows the Crazy Eights game to be run directly from the command
line, supporting both a command-line interface (CLI) and graphical user
interfaces (GUIs).

Usage:
    $ python -m card_games.crazy_eights
    $ python -m card_games.crazy_eights --cli
    $ python -m card_games.crazy_eights --players 4 --seed 123
"""

from __future__ import annotations

import argparse
import random

from card_games.crazy_eights.cli import game_loop
from card_games.crazy_eights.game import CrazyEightsGame
from common.gui_base import TKINTER_AVAILABLE
from common.gui_base_pyqt import PYQT5_AVAILABLE


def main() -> None:
    """Main entry point for the Crazy Eights game application."""
    parser = argparse.ArgumentParser(description="Play the card game Crazy Eights.")
    parser.add_argument("--players", type=int, default=2, choices=range(2, 7), help="The number of players (2-6).")
    parser.add_argument("--seed", type=int, help="A random seed for reproducible games.")
    parser.add_argument("--names", nargs="+", help="A list of player names.")
    parser.add_argument("--draw-limit", type=int, default=3, help="The maximum number of cards to draw when unable to play (0 for unlimited).")
    parser.add_argument("--cli", action="store_true", help="Run in command-line mode instead of launching a GUI.")
    parser.add_argument("--gui-framework", choices=["auto", "tkinter", "pyqt5"], default="auto", help="The preferred GUI framework to use.")
    args = parser.parse_args()

    rng = random.Random(args.seed) if args.seed is not None else None
    game = CrazyEightsGame(
        num_players=args.players,
        player_names=args.names,
        draw_limit=args.draw_limit,
        rng=rng,
    )

    if args.cli:
        game_loop(game)
        return

    # Attempt to launch the preferred GUI, with fallbacks.
    frameworks = {
        "auto": ["pyqt5", "tkinter"],
        "pyqt5": ["pyqt5"],
        "tkinter": ["tkinter"],
    }[args.gui_framework]

    for framework in frameworks:
        if framework == "pyqt5" and launch_pyqt_gui(game):
            return
        if framework == "tkinter" and launch_tk_gui(game):
            return

    print("No suitable GUI framework found. Falling back to CLI.")
    game_loop(game)


def launch_tk_gui(game: CrazyEightsGame) -> bool:
    """Launch the Tkinter GUI for Crazy Eights.

    Args:
        game: The game engine instance to visualize.

    Returns:
        True if the GUI was launched successfully, False otherwise.
    """
    if not TKINTER_AVAILABLE:
        return False
    try:
        import tkinter as tk

        from card_games.crazy_eights.gui import CrazyEightsGUI

        root = tk.Tk()
        app = CrazyEightsGUI(root, game)
        app.master.mainloop()
        return True
    except (ImportError, tk.TclError) as e:
        print(f"Failed to launch Tkinter GUI: {e}")
        return False


def launch_pyqt_gui(game: CrazyEightsGame) -> bool:
    """Launch the PyQt5 GUI for Crazy Eights.

    Args:
        game: The game engine instance to visualize.

    Returns:
        True if the GUI was launched successfully, False otherwise.
    """
    if not PYQT5_AVAILABLE:
        return False
    try:
        from PyQt5.QtWidgets import QApplication

        from card_games.crazy_eights.gui_pyqt import CrazyEightsGUI

        app = QApplication.instance() or QApplication([])
        window = CrazyEightsGUI(game)
        window.show()
        app.exec_()
        return True
    except (ImportError, Exception) as e:
        print(f"Failed to launch PyQt5 GUI: {e}")
        return False


if __name__ == "__main__":
    main()
