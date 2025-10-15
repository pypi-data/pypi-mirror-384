"""Entry point for Crazy Eights card game."""

from __future__ import annotations

import argparse
import random

from card_games.crazy_eights.cli import game_loop
from card_games.crazy_eights.game import CrazyEightsGame
from common.gui_base import TKINTER_AVAILABLE
from common.gui_base_pyqt import PYQT5_AVAILABLE


def main() -> None:
    """Main entry point for the Crazy Eights game."""
    parser = argparse.ArgumentParser(description="Play the card game Crazy Eights")
    parser.add_argument("--players", type=int, default=2, choices=range(2, 7), help="Number of players (2-6)")
    parser.add_argument("--seed", type=int, help="Random seed for reproducible games")
    parser.add_argument("--names", nargs="+", help="Player names")
    parser.add_argument("--draw-limit", type=int, default=3, help="Max cards to draw when unable to play (0 = unlimited)")
    parser.add_argument("--cli", action="store_true", help="Run the command-line interface instead of the GUI")
    parser.add_argument(
        "--gui-framework",
        choices=["auto", "tkinter", "pyqt5"],
        default="auto",
        help="Preferred GUI framework (default: auto).",
    )
    args = parser.parse_args()

    rng = None
    if args.seed is not None:
        rng = random.Random(args.seed)

    player_names = args.names if args.names else None
    game = CrazyEightsGame(num_players=args.players, player_names=player_names, draw_limit=args.draw_limit, rng=rng)

    if args.cli:
        game_loop(game)
        return

    framework_preference = {
        "auto": ["pyqt5", "tkinter"],
        "pyqt5": ["pyqt5", "tkinter"],
        "tkinter": ["tkinter", "pyqt5"],
    }[args.gui_framework]

    for framework in framework_preference:
        if framework == "pyqt5":
            if not PYQT5_AVAILABLE:
                if args.gui_framework == "pyqt5":
                    print("PyQt5 is not available. Falling back to other options.")
                continue
            if launch_pyqt_gui(game):
                return
            print("Unable to start the PyQt5 GUI. Trying alternatives...")
        else:  # tkinter
            if not TKINTER_AVAILABLE:
                if args.gui_framework == "tkinter":
                    print("Tkinter is not available. Falling back to other options.")
                continue
            if launch_tk_gui(game):
                return
            print("Unable to start the Tkinter GUI. Trying alternatives...")

    print("Falling back to the CLI interface.")
    game_loop(game)


def launch_tk_gui(game: CrazyEightsGame) -> bool:
    """Launch the Tkinter GUI for Crazy Eights.

    Args:
        game: Game engine instance to visualise.

    Returns:
        ``True`` if the GUI was started successfully, ``False`` otherwise.
    """

    import tkinter as tk

    from card_games.crazy_eights.gui import CrazyEightsGUI

    try:
        root = tk.Tk()
    except tk.TclError as exc:
        print(f"Unable to start the Crazy Eights Tkinter GUI: {exc}")
        return False

    CrazyEightsGUI(root, game)
    root.mainloop()
    return True


def launch_pyqt_gui(game: CrazyEightsGame) -> bool:
    """Launch the PyQt5 GUI for Crazy Eights.

    Args:
        game: Game engine instance to visualise.

    Returns:
        ``True`` if the GUI was started successfully, ``False`` otherwise.
    """

    if not PYQT5_AVAILABLE:
        return False

    try:
        from PyQt5.QtWidgets import QApplication

        from card_games.crazy_eights.gui_pyqt import CrazyEightsGUI
    except Exception as error:  # pragma: no cover - import side effects depend on environment
        print(f"Unable to import the PyQt5 GUI: {error}")
        return False

    try:
        app = QApplication.instance() or QApplication([])
    except Exception as error:  # pragma: no cover - depends on runtime display support
        print(f"Unable to initialise the PyQt5 application: {error}")
        return False

    window = CrazyEightsGUI(game)
    window.show()
    app.exec()
    return True


if __name__ == "__main__":
    main()
