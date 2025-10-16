"""Entry point for launching the Pinochle package."""

from __future__ import annotations

import argparse
import sys
from typing import Sequence

try:
    from tkinter import TclError
except Exception:  # pragma: no cover - Tk may be absent.
    _GUI_ERRORS: tuple[type[BaseException], ...] = (RuntimeError,)
else:
    _GUI_ERRORS = (RuntimeError, TclError)

from card_games.pinochle.cli import main as cli_main
from card_games.pinochle.gui import run_app as run_tk_app


def main(argv: Sequence[str] | None = None) -> None:
    """Parse arguments and launch the requested frontend."""

    parser = argparse.ArgumentParser(description="Play partnership double-deck Pinochle.")
    parser.add_argument("--cli", action="store_true", help="Run the text interface instead of a GUI.")
    parser.add_argument(
        "--gui-framework",
        choices=("auto", "tk", "pyqt"),
        default="auto",
        help="Select the GUI toolkit (auto tries PyQt then Tk).",
    )
    parser.add_argument(
        "--names",
        nargs="*",
        help="Optional list of player names in seating order (South, West, North, East).",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    names = args.names if args.names else None
    if args.cli:
        cli_main(names)
        return

    if args.gui_framework in ("auto", "pyqt"):
        if _launch_pyqt(names):
            return
        if args.gui_framework == "pyqt":
            print("PyQt5 GUI unavailable. Falling back to the command-line interface...", file=sys.stderr)
            cli_main(names)
            return

    if args.gui_framework in ("auto", "tk"):
        if _launch_tk(names):
            return
        if args.gui_framework == "tk":
            print("Tkinter GUI unavailable. Falling back to the command-line interface...", file=sys.stderr)
            cli_main(names)
            return

    print("No GUI backend available. Falling back to the command-line interface...", file=sys.stderr)
    cli_main(names)


def _launch_tk(names: Sequence[str] | None) -> bool:
    try:
        run_tk_app(list(names) if names else None)
    except _GUI_ERRORS as exc:
        print(exc, file=sys.stderr)
        return False
    return True


def _launch_pyqt(names: Sequence[str] | None) -> bool:
    try:
        from card_games.pinochle.gui_pyqt import run_app as run_pyqt_app
    except ImportError as exc:
        if "PyQt5" in str(exc):
            return False
        raise
    try:
        run_pyqt_app(list(names) if names else None)
    except Exception as exc:  # pragma: no cover - Qt failures are environment-specific.
        print(exc, file=sys.stderr)
        return False
    return True


if __name__ == "__main__":  # pragma: no cover - exercised in integration tests
    main()
