"""Command-line interface for playing Battleship.

This module provides a terminal-based interactive experience for playing
Battleship. It supports a variety of command-line arguments to configure
the game, including board size, fleet composition, AI difficulty, and special
game modes like two-player hot-seat and salvo mode.

The CLI handles user input for ship placement and firing shots, and it
displays the game state in a clear, readable format.

Functions:
    play(argv): Runs an interactive Battleship session with command-line
                configuration.
"""

from __future__ import annotations

import argparse
from typing import Optional, Sequence

from .battleship import DEFAULT_FLEET, EXTENDED_FLEET, SMALL_FLEET, BattleshipGame, Coordinate


def _prompt_orientation() -> str:
    """Prompts the user for a ship orientation ('h' or 'v').

    Returns:
        str: The validated orientation character.

    Raises:
        ValueError: If the input is not 'h' or 'v'.
    """
    orientation = input("Orientation (h for horizontal, v for vertical): ").strip().lower()
    if orientation not in {"h", "v"}:
        raise ValueError("Orientation must be 'h' or 'v'.")
    return orientation


def _prompt_coordinate(prompt: str) -> Coordinate:
    """Prompts the user for a board coordinate (row and column).

    Args:
        prompt (str): The message to display to the user.

    Returns:
        Coordinate: A tuple containing the (row, col) integers.

    Raises:
        ValueError: If the input is not two space-separated integers.
    """
    raw = input(prompt).split()
    if len(raw) != 2:
        raise ValueError("Enter row and column, separated by a space.")
    row, col = map(int, raw)
    return row, col


def play(argv: Optional[Sequence[str]] = None) -> None:
    """Runs an interactive Battleship session with command-line configuration.

    This function parses command-line arguments to set up the game, handles
    the ship placement phase for each player, and then enters the main game
    loop until a winner is determined.

    Args:
        argv (Optional[Sequence[str]]): A sequence of command-line arguments.
                                        If None, `sys.argv` is used.
    """
    parser = argparse.ArgumentParser(description="Play Battleship with configurable options")
    parser.add_argument(
        "--size",
        type=int,
        choices=[8, 10],
        default=10,
        help="The size of the game board (8 for 8x8, 10 for 10x10).",
    )
    parser.add_argument(
        "--fleet",
        choices=["small", "default", "extended"],
        default="default",
        help="The fleet configuration to use (small for 8x8, default, or extended).",
    )
    parser.add_argument(
        "--difficulty",
        choices=["easy", "medium", "hard"],
        default="medium",
        help="The AI difficulty level (easy: random, medium: 70%% smart, hard: always smart).",
    )
    parser.add_argument(
        "--two-player",
        action="store_true",
        help="Enable two-player hot-seat mode (no AI).",
    )
    parser.add_argument(
        "--salvo",
        action="store_true",
        help="Enable salvo mode, where the number of shots per turn equals the number of unsunk ships.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="A random seed for reproducible games.",
    )

    args = parser.parse_args(argv)

    # Select the appropriate fleet based on the command-line arguments.
    fleet_map = {
        "small": SMALL_FLEET,
        "default": DEFAULT_FLEET,
        "extended": EXTENDED_FLEET,
    }
    fleet = fleet_map[args.fleet]

    # Create a random number generator, optionally using the provided seed.
    import random

    rng = random.Random(args.seed) if args.seed is not None else None

    # Initialize the game with the specified options.
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

    # Set up the ships for Player 1.
    _setup_player(game, player_name="Player 1", is_player_board=True)

    # Set up the ships for Player 2 (in hot-seat mode) or the AI.
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

    # Start the main game loop.
    _game_loop(game)


def _setup_player(game: BattleshipGame, player_name: str, is_player_board: bool) -> None:
    """Handles the ship setup phase for a single player.

    This function allows the player to choose between placing their ships
    manually or having them placed randomly.

    Args:
        game (BattleshipGame): The game instance.
        player_name (str): The name of the player setting up their ships.
        is_player_board (bool): True if setting up the main player's board,
                                False for the opponent's board (in hot-seat mode).
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
    """The main game loop for Battleship.

    This function alternates turns between the player(s) and/or the AI,
    handling shots and checking for a win condition.

    Args:
        game (BattleshipGame): The game instance.
    """
    current_player = 1  # 1 for the main player, 2 for the AI or second player.

    while True:
        if game.two_player:
            print("\n" + "=" * 50)
            print(f"Player {current_player}'s Turn")
            print("=" * 50)
            input("Press Enter when ready...")

        print("\n" + game.render())

        # Determine the number of shots available for the current player's turn.
        if game.salvo_mode:
            shots_available = game.get_salvo_count("player" if current_player == 1 else "opponent")
            print(f"\nYou have {shots_available} shot(s) this turn!")
        else:
            shots_available = 1

        # Handle Player 1's turn.
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

        # Handle the AI's or Player 2's turn.
        if not game.two_player:
            # It's the AI's turn.
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
            # It's Player 2's turn in hot-seat mode.
            current_player = 2
            print("\n" + "=" * 50)
            print("Player 2's Turn")
            print("=" * 50)
            input("Press Enter when Player 1 has looked away...")

            # Show Player 2's view of the board.
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
                    # Player 2 shoots at Player 1's board.
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
    """Renders the board from the perspective of Player 2 in hot-seat mode.

    This function shows Player 2 their own fleet and their shots on Player 1's
    board, without revealing Player 1's ship positions.

    Args:
        game (BattleshipGame): The game instance.

    Returns:
        str: A string representation of the board from Player 2's view.
    """
    # Player 2's fleet (the opponent_board) with their ships shown.
    player2_fleet = game.opponent_board.render(show_ships=True)
    # Player 1's board (the player_board) with only shots shown.
    player1_waters = game.player_board.render(show_ships=False)
    divider = "\n" + "=" * (game.size * 3) + "\n"
    return f"Your Fleet:\n{player2_fleet}{divider}Enemy Waters:\n{player1_waters}"
