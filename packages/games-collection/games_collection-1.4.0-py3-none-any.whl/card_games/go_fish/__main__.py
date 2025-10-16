"""Entry point for Go Fish card game."""

from __future__ import annotations

import argparse
import random

from card_games.go_fish.cli import game_loop
from card_games.go_fish.game import GoFishGame
from common.gui_base import TKINTER_AVAILABLE


def main() -> None:
    """Main entry point for the Go Fish game."""
    parser = argparse.ArgumentParser(description="Play the card game Go Fish")
    parser.add_argument("--players", type=int, default=2, choices=range(2, 7), help="Number of players (2-6)")
    parser.add_argument("--seed", type=int, help="Random seed for reproducible games")
    parser.add_argument("--names", nargs="+", help="Player names")
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument("--cli", action="store_true", help="Launch the text-based interface")
    mode_group.add_argument("--gui", action="store_true", help="Launch the graphical interface (default)")
    args = parser.parse_args()

    rng = None
    if args.seed is not None:
        rng = random.Random(args.seed)

    player_names = args.names if args.names else None
    game = GoFishGame(num_players=args.players, player_names=player_names, rng=rng)

    use_gui = args.gui or not args.cli

    if use_gui and not TKINTER_AVAILABLE:
        print("Tkinter is not available on this system. Falling back to the CLI interface.")
        use_gui = False

    if use_gui:
        if launch_gui(game):
            return
        print("Falling back to the CLI interface.")

    game_loop(game)


def launch_gui(game: GoFishGame) -> bool:
    """Launch the Tkinter GUI for Go Fish if possible.

    Args:
        game: The Go Fish engine instance to visualize and control.

    Returns:
        ``True`` if the GUI was successfully launched, ``False`` when Tkinter
        failed to initialize (for example, in headless environments).
    """

    import tkinter as tk

    from card_games.go_fish.gui import GoFishGUI

    try:
        root = tk.Tk()
    except tk.TclError as error:
        print(f"Unable to initialize the Tkinter GUI: {error}")
        return False

    GoFishGUI(root, game)
    root.mainloop()
    return True


if __name__ == "__main__":
    main()
