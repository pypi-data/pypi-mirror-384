"""Entry point for War card game."""

from __future__ import annotations

import argparse
import random
import time
from typing import Optional

from card_games.war.cli import STATS_AVAILABLE, game_loop
from card_games.war.game import WarGame

if STATS_AVAILABLE:  # pragma: no branch - optional import for statistics
    from card_games.common.stats import CardGameStats

try:  # pragma: no cover - import may fail when Tkinter is unavailable
    from card_games.war.gui import run_app as run_gui_app

    GUI_AVAILABLE = True
except ImportError:  # pragma: no cover - runtime environment without GUI support
    GUI_AVAILABLE = False
    run_gui_app = None  # type: ignore[assignment]


def _build_game(seed: Optional[int]) -> WarGame:
    """Create a WarGame instance using an optional seed."""

    rng = random.Random(seed) if seed is not None else None
    return WarGame(rng=rng)


def main() -> None:
    """Main entry point for the War game."""

    parser = argparse.ArgumentParser(description="Play the card game War")
    parser.add_argument("--seed", type=int, help="Random seed for reproducible games")
    parser.add_argument("--auto", action="store_true", help="Automatically play all rounds in CLI mode")
    parser.add_argument("--delay", type=float, default=0.5, help="Delay between rounds in CLI auto mode (seconds)")
    parser.add_argument("--no-stats", action="store_true", help="Disable statistics tracking in CLI mode")
    parser.add_argument("--show-stats", action="store_true", help="Show player statistics and exit")
    parser.add_argument("--leaderboard", action="store_true", help="Show leaderboard and exit")
    parser.add_argument("--player", type=str, help="Player name to show stats for (use with --show-stats)")
    parser.add_argument("--gui", action="store_true", help="Launch the Tkinter GUI instead of the CLI")
    parser.add_argument("--pyqt", action="store_true", help="Launch the PyQt GUI instead of the CLI")
    parser.add_argument("--enable-sounds", action="store_true", help="Enable sound effects in GUI mode (if supported)")
    args = parser.parse_args()

    if STATS_AVAILABLE:
        if args.leaderboard:
            stats = CardGameStats("war")
            stats.display_leaderboard()
            return
        if args.show_stats:
            stats = CardGameStats("war")
            player_name = args.player or "Player 1"
            stats.display_player_stats(player_name)
            return

    if args.gui and args.pyqt:
        parser.error("Choose either --gui or --pyqt, not both.")

    if args.pyqt:
        try:
            from card_games.war.gui_pyqt import run_gui as run_pyqt_gui
        except ImportError as exc:  # pragma: no cover - optional GUI dependency
            parser.error(f"PyQt5 GUI mode is unavailable: {exc}")

        game = _build_game(args.seed)
        run_pyqt_gui(game=game)
        return

    if args.gui:
        if not GUI_AVAILABLE:
            parser.error("GUI mode is unavailable because Tkinter could not be imported.")
        assert run_gui_app is not None
        game = _build_game(args.seed)
        run_gui_app(game=game, enable_sounds=args.enable_sounds)
        return

    game = _build_game(args.seed)
    start_time = time.time()
    game_loop(game, auto_play=args.auto, delay=args.delay, track_stats=not args.no_stats, start_time=start_time)


if __name__ == "__main__":
    main()
