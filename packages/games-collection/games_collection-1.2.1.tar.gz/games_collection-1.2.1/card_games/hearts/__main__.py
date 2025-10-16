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
from common import SettingsManager
from common.themes import ThemeManager

PREFERENCES_NAMESPACE = "card_games.hearts.gui"


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
        help="Reset stored Hearts GUI preferences before launching.",
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

    _apply_preference_overrides(args)

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


def _apply_preference_overrides(args: argparse.Namespace) -> None:
    """Persist CLI-specified preference overrides for the Hearts GUI.

    Args:
        args: Parsed CLI namespace.
    """

    defaults = {"theme": "midnight", "enable_sounds": True, "enable_animations": True}
    manager = SettingsManager()
    settings = manager.load_settings(PREFERENCES_NAMESPACE, defaults)

    if args.reset_preferences:
        settings.reset()

    if args.high_contrast:
        settings.set("theme", "high_contrast")

    if args.theme:
        settings.set("theme", args.theme)

    if args.sounds is not None:
        settings.set("enable_sounds", bool(args.sounds))

    if args.animations is not None:
        settings.set("enable_animations", bool(args.animations))

    manager.save_settings(PREFERENCES_NAMESPACE, settings)


if __name__ == "__main__":  # pragma: no cover - manual invocation entry point
    main()
