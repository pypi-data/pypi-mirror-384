"""Command-line entry point for the Bridge package."""

from __future__ import annotations

import argparse
from typing import Optional

from card_games.bridge.cli import game_loop
from card_games.bridge.gui import run_app
from common.gui_base import TKINTER_AVAILABLE
from common.gui_base_pyqt import PYQT5_AVAILABLE


def main(args: Optional[list[str]] = None) -> None:
    """Launch the Bridge game in CLI or GUI mode."""

    parser = argparse.ArgumentParser(description="Play a deal of Contract Bridge.")
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument("--cli", action="store_true", help="Launch the text-based interface.")
    mode_group.add_argument("--gui", action="store_true", help="Launch the graphical interface.")
    parser.add_argument(
        "--gui-backend",
        choices=["tkinter", "pyqt"],
        default="tkinter",
        help="Select the GUI backend to launch (default: tkinter).",
    )
    parsed = parser.parse_args(args)

    if parsed.cli:
        game_loop()
        return

    if parsed.gui_backend == "pyqt":
        if not PYQT5_AVAILABLE:
            print("PyQt5 is unavailable. Falling back to the CLI interface.")
            game_loop()
            return
        try:
            from card_games.bridge.gui_pyqt import run_gui as run_pyqt_gui
            from common.gui_base_pyqt import GUIConfig
        except ImportError as exc:  # pragma: no cover - PyQt missing at runtime
            print(f"Unable to import the PyQt Bridge GUI: {exc}")
            game_loop()
            return

        config = GUIConfig(
            window_title="Contract Bridge (PyQt)",
            window_width=1100,
            window_height=720,
            font_family="Segoe UI",
            font_size=11,
            theme_name="dark",
        )
        if run_pyqt_gui(config=config):
            return
        print("PyQt5 could not initialize a window. Falling back to the CLI interface.")
        game_loop()
        return

    if parsed.gui_backend == "tkinter" and not TKINTER_AVAILABLE:
        print("Tkinter is unavailable. Falling back to the CLI interface.")
        game_loop()
        return

    run_app()


if __name__ == "__main__":
    main()
