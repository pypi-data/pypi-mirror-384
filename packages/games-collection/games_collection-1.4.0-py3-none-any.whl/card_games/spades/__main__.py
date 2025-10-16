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
from common import SettingsManager
from common.themes import ThemeManager

PREFERENCES_NAMESPACE = "card_games.spades.gui"


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
    parser.add_argument(
        "--theme",
        choices=ThemeManager().list_themes(),
        help="Override the GUI theme and persist the selection for future sessions.",
    )
    parser.add_argument(
        "--sounds",
        dest="sounds",
        action="store_true",
        help="Enable GUI sound effects for this and future sessions.",
    )
    parser.add_argument(
        "--no-sounds",
        dest="sounds",
        action="store_false",
        help="Disable GUI sound effects for this and future sessions.",
    )
    parser.add_argument(
        "--animations",
        dest="animations",
        action="store_true",
        help="Enable GUI animations for this and future sessions.",
    )
    parser.add_argument(
        "--no-animations",
        dest="animations",
        action="store_false",
        help="Disable GUI animations for this and future sessions.",
    )
    parser.set_defaults(sounds=None, animations=None)
    parser.add_argument(
        "--reset-preferences",
        action="store_true",
        help="Reset stored Spades GUI preferences before launching.",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.cli:
        game_loop()
        return

    _apply_preference_overrides(args)

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


def _apply_preference_overrides(args: argparse.Namespace) -> None:
    """Persist CLI-specified preference overrides for the Spades GUI.

    Args:
        args: Parsed CLI namespace.
    """

    defaults = {"theme": "dark", "enable_sounds": True, "enable_animations": True}
    manager = SettingsManager()
    settings = manager.load_settings(PREFERENCES_NAMESPACE, defaults)

    if args.reset_preferences:
        settings.reset()

    if args.theme:
        settings.set("theme", args.theme)

    if args.sounds is not None:
        settings.set("enable_sounds", bool(args.sounds))

    if args.animations is not None:
        settings.set("enable_animations", bool(args.animations))

    manager.save_settings(PREFERENCES_NAMESPACE, settings)


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
