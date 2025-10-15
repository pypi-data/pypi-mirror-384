"""Entry point for the Spades game package."""

from __future__ import annotations

import argparse
import sys
from typing import Sequence

try:
    from tkinter import TclError
except Exception:  # pragma: no cover - Tkinter may be unavailable in some environments.
    _GUI_ERRORS: tuple[type[BaseException], ...] = (RuntimeError,)
else:
    _GUI_ERRORS = (RuntimeError, TclError)

from card_games.spades.cli import game_loop
from card_games.spades.gui import run_app as run_tk_app


def main(argv: Sequence[str] | None = None) -> None:
    """Launch the GUI by default, falling back to the CLI when requested."""

    parser = argparse.ArgumentParser(description="Play Spades against AI opponents.")
    parser.add_argument("--cli", action="store_true", help="Run the text-based interface instead of the GUI.")
    parser.add_argument("--name", default="You", help="Display name for the GUI human player.")
    parser.add_argument(
        "--backend",
        choices=("auto", "pyqt", "tk"),
        default="auto",
        help="Select the GUI backend: auto detects PyQt5 then Tkinter.",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.cli:
        game_loop()
        return

    backend = args.backend

    if backend in ("auto", "pyqt"):
        if _launch_pyqt(args.name):
            return
        if backend == "pyqt":
            print("PyQt5 GUI unavailable. Falling back to the command-line interface...", file=sys.stderr)
            game_loop()
            return

    if backend in ("auto", "tk"):
        if _launch_tk(args.name):
            return
        if backend == "tk":
            print("Tkinter GUI unavailable. Falling back to the command-line interface...", file=sys.stderr)
            game_loop()
            return

    print("No GUI backend available. Falling back to the command-line interface...", file=sys.stderr)
    game_loop()


def _launch_tk(player_name: str) -> bool:
    """Attempt to launch the Tkinter GUI backend."""

    try:
        run_tk_app(player_name=player_name)
    except _GUI_ERRORS as exc:
        print(exc, file=sys.stderr)
        return False
    return True


def _launch_pyqt(player_name: str) -> bool:
    """Attempt to launch the PyQt5 GUI backend."""

    try:
        from card_games.spades.gui_pyqt import run_app as run_pyqt_app
    except ImportError as exc:
        if "PyQt5" in str(exc):
            return False
        raise

    try:
        run_pyqt_app(player_name=player_name)
    except Exception as exc:  # pragma: no cover - display issues are environment-specific.
        print(exc, file=sys.stderr)
        return False
    return True


if __name__ == "__main__":
    main()
