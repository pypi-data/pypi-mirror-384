"""Entry point for launching the Gin Rummy experiences."""

from __future__ import annotations

import argparse
from typing import Sequence

from card_games.gin_rummy.cli import game_loop


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse command-line options for the Gin Rummy launcher."""

    parser = argparse.ArgumentParser(description="Gin Rummy launcher")
    parser.add_argument(
        "--mode",
        choices=["cli", "gui", "pyqt"],
        default="cli",
        help="Launch the CLI, the Tkinter GUI, or the PyQt GUI.",
    )
    parser.add_argument(
        "--player-name",
        default="You",
        help="Name to display for the human player when using the GUI.",
    )
    parser.add_argument(
        "--opponent-name",
        default="AI",
        help="Name to display for the computer opponent in the GUI.",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    """Main entry point for Gin Rummy game."""

    args = parse_args(argv)
    if args.mode == "gui":
        from card_games.gin_rummy.gui import run_app

        run_app(player_name=args.player_name, opponent_name=args.opponent_name)
        return

    if args.mode == "pyqt":
        try:
            from card_games.gin_rummy.gui_pyqt import run_pyqt_app
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise RuntimeError("PyQt5 is not available for the Gin Rummy GUI") from exc

        run_pyqt_app(player_name=args.player_name, opponent_name=args.opponent_name)
        return

    game_loop()


if __name__ == "__main__":
    main()
