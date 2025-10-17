"""Command-line interface for playing Battleship.

This module provides the terminal-based interactive experience for playing
Battleship against an AI opponent that uses a hunting strategy.
"""

from __future__ import annotations

import argparse
from typing import Optional, Sequence

from .battleship import DEFAULT_FLEET, EXTENDED_FLEET, SMALL_FLEET, BattleshipGame, Coordinate


def _prompt_orientation() -> str:
    """Prompts the user for a ship orientation."""
    orientation = input("Orientation (h for horizontal, v for vertical): ").strip().lower()
    if orientation not in {"h", "v"}:
        raise ValueError("Orientation must be 'h' or 'v'.")
    return orientation


def _prompt_coordinate(prompt: str) -> Coordinate:
    """Prompts the user for a coordinate."""
    raw = input(prompt).split()
    if len(raw) != 2:
        raise ValueError("Enter row and column, separated by a space.")
    row, col = map(int, raw)
    return row, col


def play(argv: Optional[Sequence[str]] = None) -> None:
    """Interactive Battleship session with command-line configuration.

    Args:
        argv: Command-line arguments (uses sys.argv if None)
    """
    parser = argparse.ArgumentParser(description="Play Battleship with configurable options")
    parser.add_argument(
        "--size",
        type=int,
        choices=[8, 10],
        default=10,
        help="Board size (8x8 or 10x10)",
    )
    parser.add_argument(
        "--fleet",
        choices=["small", "default", "extended"],
        default="default",
        help="Fleet configuration (small for 8x8, default, or extended)",
    )
    parser.add_argument(
        "--difficulty",
        choices=["easy", "medium", "hard"],
        default="medium",
        help="AI difficulty level (easy: random, medium: 70%% smart, hard: always smart)",
    )
    parser.add_argument(
        "--two-player",
        action="store_true",
        help="Enable 2-player hot-seat mode (no AI)",
    )
    parser.add_argument(
        "--salvo",
        action="store_true",
        help="Enable salvo mode (shots per turn = unsunk ships)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed for reproducible games",
    )

    args = parser.parse_args(argv)

    # Select fleet based on arguments
    fleet_map = {
        "small": SMALL_FLEET,
        "default": DEFAULT_FLEET,
        "extended": EXTENDED_FLEET,
    }
    fleet = fleet_map[args.fleet]

    # Create random number generator with optional seed
    import random

    rng = random.Random(args.seed) if args.seed is not None else None

    # Create game with specified options
    game = BattleshipGame(
        size=args.size,
        fleet=fleet,
        rng=rng,
        difficulty=args.difficulty,
        two_player=args.two_player,
        salvo_mode=args.salvo,
    )

    print("=" * 50)
    print("Welcome to Battleship!")
    print("=" * 50)
    print(f"Board size: {args.size}x{args.size}")
    print(f"Fleet: {args.fleet} ({len(fleet)} ships)")
    if not args.two_player:
        print(f"AI difficulty: {args.difficulty}")
    else:
        print("Mode: 2-player hot-seat")
    if args.salvo:
        print("Salvo mode: ENABLED")
    print("=" * 50)

    # Setup ships for Player 1
    _setup_player(game, player_name="Player 1", is_player_board=True)

    # Setup ships for Player 2 or AI
    if game.two_player:
        print("\n" + "=" * 50)
        print("Now Player 2 will set up their fleet")
        print("=" * 50)
        input("Press Enter when Player 1 has looked away...")
        _setup_player(game, player_name="Player 2", is_player_board=False)
        print("\nBoth players ready! Game starting...")
        input("Press Enter to begin...")
    else:
        game.opponent_board.randomly_place_ships(game.fleet, game.rng)
        print("\nAI opponent fleet is ready!")

    # Main game loop
    _game_loop(game)


def _setup_player(game: BattleshipGame, player_name: str, is_player_board: bool) -> None:
    """Setup ships for a player.

    Args:
        game: The game instance
        player_name: Name of the player setting up
        is_player_board: True for player board, False for opponent board
    """
    board = game.player_board if is_player_board else game.opponent_board

    manual = input(f"\n{player_name}, place ships manually? (y/n): ").strip().lower()
    if manual.startswith("y"):
        print("Enter the starting coordinate for each ship.")
        for name, length in game.fleet:
            placed = False
            while not placed:
                print(f"\nPlacing {name} (length {length})")
                print(board.render(show_ships=True))
                try:
                    start = _prompt_coordinate("Starting coordinate (row col): ")
                    orientation = _prompt_orientation()
                    board.place_ship(name, length, start, orientation)
                    placed = True
                except ValueError as exc:
                    print(f"Cannot place ship: {exc}")
    else:
        board.randomly_place_ships(game.fleet, game.rng)
        print(f"{player_name}'s fleet placed randomly!")


def _game_loop(game: BattleshipGame) -> None:
    """Main game loop for Battleship.

    Args:
        game: The game instance
    """
    current_player = 1  # 1 for player/Player 1, 2 for AI/Player 2

    while True:
        if game.two_player:
            print("\n" + "=" * 50)
            print(f"Player {current_player}'s Turn")
            print("=" * 50)
            input("Press Enter when ready...")

        print("\n" + game.render())

        # Determine number of shots for this turn
        if game.salvo_mode:
            shots_available = game.get_salvo_count("player" if current_player == 1 else "opponent")
            print(f"\nYou have {shots_available} shot(s) this turn!")
        else:
            shots_available = 1

        # Player/Player 1 turn
        if current_player == 1:
            for shot_num in range(shots_available):
                if shots_available > 1:
                    print(f"\nShot {shot_num + 1} of {shots_available}")

                try:
                    target = _prompt_coordinate("Fire at (row col): ")
                    result, ship_name = game.player_shoot(target)
                except ValueError as exc:
                    print(f"Invalid shot: {exc}")
                    continue

                if result == "miss":
                    print("Splash! You missed.")
                elif result == "hit":
                    print("Direct hit!")
                else:
                    print(f"You sank the enemy {ship_name}!")

                if game.opponent_has_lost():
                    print("\n" + "=" * 50)
                    print("ALL ENEMY SHIPS DESTROYED!")
                    if game.two_player:
                        print(f"Player {current_player} WINS!")
                    else:
                        print("YOU WIN!")
                    print("=" * 50)
                    return

        # AI/Player 2 turn
        if not game.two_player:
            # AI turn
            ai_shots = game.get_salvo_count("opponent") if game.salvo_mode else 1
            if game.salvo_mode and ai_shots > 1:
                print(f"\nAI takes {ai_shots} shots...")

            for _ in range(ai_shots):
                coord, ai_result, ship_name = game.ai_shoot()
                row, col = coord
                if ai_result == "miss":
                    print(f"AI fires at ({row}, {col}) and misses.")
                elif ai_result == "hit":
                    print(f"AI hits your ship at ({row}, {col})!")
                else:
                    print(f"AI sinks your {ship_name} at ({row}, {col})!")

                if game.player_has_lost():
                    print("\n" + "=" * 50)
                    print("YOUR FLEET HAS BEEN DESTROYED!")
                    print("AI WINS!")
                    print("=" * 50)
                    return
        else:
            # Player 2 turn in hot-seat mode
            current_player = 2
            print("\n" + "=" * 50)
            print("Player 2's Turn")
            print("=" * 50)
            input("Press Enter when Player 1 has looked away...")

            # Show Player 2's view (their fleet and where they've shot at Player 1)
            print("\n" + _render_player2_view(game))

            if game.salvo_mode:
                shots_available = game.get_salvo_count("opponent")
                print(f"\nYou have {shots_available} shot(s) this turn!")
            else:
                shots_available = 1

            for shot_num in range(shots_available):
                if shots_available > 1:
                    print(f"\nShot {shot_num + 1} of {shots_available}")

                try:
                    target = _prompt_coordinate("Fire at (row col): ")
                    # Player 2 shoots at Player 1's board
                    result, ship_name = game.player_board.receive_shot(target)
                except ValueError as exc:
                    print(f"Invalid shot: {exc}")
                    continue

                if result == "miss":
                    print("Splash! You missed.")
                elif result == "hit":
                    print("Direct hit!")
                else:
                    print(f"You sank Player 1's {ship_name}!")

                if game.player_has_lost():
                    print("\n" + "=" * 50)
                    print("PLAYER 1'S FLEET DESTROYED!")
                    print("PLAYER 2 WINS!")
                    print("=" * 50)
                    return

            current_player = 1
            print("\n" + "=" * 50)
            input("Press Enter to switch back to Player 1...")


def _render_player2_view(game: BattleshipGame) -> str:
    """Render the board from Player 2's perspective.

    Args:
        game: The game instance

    Returns:
        String representation of both boards from Player 2's view
    """
    # Player 2's fleet (opponent_board) with ships shown
    # Player 1's board (player_board) without ships shown
    player2_fleet = game.opponent_board.render(show_ships=True)
    player1_waters = game.player_board.render(show_ships=False)
    divider = "\n" + "=" * (game.size * 3) + "\n"
    return f"Your Fleet:\n{player2_fleet}{divider}Enemy Waters:\n{player1_waters}"
