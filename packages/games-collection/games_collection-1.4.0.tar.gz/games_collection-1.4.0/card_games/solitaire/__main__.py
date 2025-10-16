"""Entry point for Solitaire (Klondike) game."""

from __future__ import annotations

import argparse
import random

from card_games.solitaire.cli import game_loop
from card_games.solitaire.game import SolitaireGame
from card_games.solitaire.gui import run_app as run_app_tk

try:  # pragma: no cover - Optional dependency import
    from card_games.solitaire import gui_pyqt as gui_pyqt_module

    PYQT_AVAILABLE = gui_pyqt_module.PYQT5_AVAILABLE
except Exception:  # pragma: no cover - PyQt5 missing
    gui_pyqt_module = None  # type: ignore[assignment]
    PYQT_AVAILABLE = False


def main() -> None:
    """Main entry point for the Solitaire game."""
    parser = argparse.ArgumentParser(description="Play Klondike Solitaire")
    parser.add_argument("--seed", type=int, help="Random seed for reproducible games")
    parser.add_argument(
        "--draw-count",
        type=int,
        choices=[1, 3],
        default=3,
        help="Number of cards to draw from the stock at a time (1 or 3).",
    )
    parser.add_argument(
        "--max-recycles",
        type=int,
        help="Limit how many times the waste can be recycled back to the stock (default: unlimited for draw-one, 3 for draw-three).",
    )
    parser.add_argument(
        "--scoring",
        choices=["standard", "vegas"],
        default="standard",
        help="Choose between standard (Windows-style) or Vegas scoring.",
    )
    parser.add_argument(
        "--cli",
        action="store_true",
        help="Run the text-based interface instead of the GUI.",
    )
    args = parser.parse_args()

    def make_game() -> SolitaireGame:
        rng = random.Random(args.seed) if args.seed is not None else None
        return SolitaireGame(
            draw_count=args.draw_count,
            max_recycles=args.max_recycles,
            scoring_mode=args.scoring,
            rng=rng,
        )

    if args.cli:
        game_loop(make_game())
        return

    if PYQT_AVAILABLE and gui_pyqt_module is not None:
        try:
            gui_pyqt_module.run_app(
                draw_count=args.draw_count,
                max_recycles=args.max_recycles,
                scoring_mode=args.scoring,
                seed=args.seed,
            )
            return
        except RuntimeError as exc:
            print(f"PyQt5 GUI unavailable ({exc}). Trying Tkinter fallback...")
    elif not PYQT_AVAILABLE:
        print("PyQt5 GUI unavailable (PyQt5 not installed). Trying Tkinter fallback...")

    try:
        run_app_tk(
            draw_count=args.draw_count,
            max_recycles=args.max_recycles,
            scoring_mode=args.scoring,
            seed=args.seed,
        )
        return
    except RuntimeError as exc:
        print(f"Tkinter GUI unavailable ({exc}). Falling back to CLI mode.")

    game_loop(make_game())


if __name__ == "__main__":
    main()
