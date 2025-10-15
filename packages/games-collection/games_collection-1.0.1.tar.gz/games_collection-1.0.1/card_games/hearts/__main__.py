"""Entry point for the Hearts card game package.

This module exposes a command-line interface for selecting between the classic
text mode and the new Tkinter GUI. Accessibility options such as high contrast
and enhanced keyboard navigation are surfaced here so that ``python -m
card_games.hearts`` mirrors the behaviour of the standalone GUI launcher.
"""

from __future__ import annotations

import argparse
from typing import Optional, Sequence

from card_games.hearts.cli import game_loop


def _build_parser() -> argparse.ArgumentParser:
    """Create an argument parser for launching Hearts.

    Returns:
        argparse.ArgumentParser: Configured parser with CLI and GUI options.
    """
    parser = argparse.ArgumentParser(description="Play Hearts with a GUI or the classic CLI.")
    parser.add_argument("--cli", action="store_true", help="Launch the text-based interface instead of the GUI.")
    parser.add_argument("--player-name", default="Player", help="Name used for the human player.")
    parser.add_argument(
        "--high-contrast",
        action="store_true",
        help="Enable a high-contrast theme for improved visibility in the GUI.",
    )
    parser.add_argument(
        "--accessibility-mode",
        action="store_true",
        help="Enable additional accessibility aids such as larger fonts and screen-reader labels.",
    )
    parser.add_argument(
        "--backend",
        choices=["pyqt", "tk"],
        default="pyqt",
        help="GUI backend to use when launching the graphical interface.",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> None:
    """Parse CLI arguments and launch the selected Hearts interface.

    Args:
        argv: Optional sequence of command-line arguments for testing.
    """
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.cli:
        game_loop()
        return

    backend = args.backend

    if backend == "pyqt":
        try:
            from card_games.hearts.gui_pyqt import run_app as run_app_pyqt

            run_app_pyqt(
                player_name=args.player_name,
                high_contrast=args.high_contrast,
                accessibility_mode=args.accessibility_mode,
            )
            return
        except (ImportError, RuntimeError):
            print("PyQt5 backend unavailable, attempting Tkinter fallback…")

    try:
        from card_games.hearts.gui import run_app as run_app_tk
    except (ImportError, RuntimeError) as exc:  # pragma: no cover - environment specific
        raise SystemExit("No supported GUI backend is available. Install PyQt5 or Tkinter, or pass --cli.") from exc

    run_app_tk(
        player_name=args.player_name,
        high_contrast=args.high_contrast,
        accessibility_mode=args.accessibility_mode,
    )


if __name__ == "__main__":  # pragma: no cover - manual invocation entry point
    main()
