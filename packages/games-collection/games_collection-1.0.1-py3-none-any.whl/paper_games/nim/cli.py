"""Command-line interface for playing Nim and its variants.

This module provides the terminal-based interactive experience for playing
Nim against the computer. It handles user input, game setup, and announcing
the winner.

Supports:
- Classic Nim with optional misère rules
- Graphical heap representation
- Educational mode with strategy hints
- Multiplayer mode (3+ players)
- Custom rule variations (max_take limit)
- Variant games: Northcott and Wythoff
"""

from __future__ import annotations

from .nim import NimGame, NorthcottGame, WythoffGame


def play() -> None:
    """Run a terminal-based Nim match against the computer."""

    print("=" * 60)
    print("Welcome to Nim and Variants!")
    print("=" * 60)
    print("\nAvailable games:")
    print("  1. Classic Nim")
    print("  2. Northcott's Game")
    print("  3. Wythoff's Game")

    game_choice = input("\nSelect game (1-3) [1]: ").strip()

    if game_choice == "2":
        play_northcott()
    elif game_choice == "3":
        play_wythoff()
    else:
        play_classic_nim()


def play_classic_nim() -> None:
    """Play classic Nim with all enhancements."""

    print("\n" + "=" * 60)
    print("Classic Nim")
    print("=" * 60)
    print("Remove sticks; whoever takes the last wins by default.")
    print("You may optionally switch to misère rules where taking the last stick loses.")

    # Get the heap sizes from the user.
    while True:
        heap_input = input("\nEnter heap sizes separated by spaces (press Enter for the classic 3 4 5): ").strip()
        if heap_input:
            try:
                heaps = [int(value) for value in heap_input.split() if value]
                if not heaps or any(value <= 0 for value in heaps):
                    raise ValueError
            except ValueError:
                print("Please provide positive integers like '1 3 5'.")
                continue
        else:
            heaps = [3, 4, 5]
        break

    # Get the game rules from the user.
    misere_choice = input("Play misère Nim (last move loses)? [y/N]: ").strip().lower()
    misere = misere_choice == "y"

    # Ask about graphical mode
    graphical_choice = input("Use graphical heap display? [Y/n]: ").strip().lower()
    graphical = graphical_choice != "n"

    # Ask about educational mode
    educational_choice = input("Enable educational mode (strategy hints)? [y/N]: ").strip().lower()
    educational = educational_choice == "y"

    # Ask about custom rules
    max_take_input = input("Limit max objects per turn? (press Enter for no limit, or enter a number): ").strip()
    max_take = int(max_take_input) if max_take_input else None

    # Ask about multiplayer
    num_players = 2
    multiplayer_choice = input("Play with more than 2 players? [y/N]: ").strip().lower()
    if multiplayer_choice == "y":
        while True:
            try:
                num_players = int(input("Enter number of players (2-6): ").strip())
                if 2 <= num_players <= 6:
                    break
                print("Please enter a number between 2 and 6.")
            except ValueError:
                print("Please enter a valid number.")

    # Determine first player
    if num_players == 2:
        first_choice = input("Do you want to move first? [Y/n]: ").strip().lower()
        human_starts = first_choice != "n"
        current_player_is_human = human_starts
    else:
        # In multiplayer, computer is the last player
        print(f"\nPlayers 1-{num_players - 1} are humans, Player {num_players} is the computer.")
        current_player_is_human = True

    game = NimGame(heaps=heaps, misere=misere, num_players=num_players, max_take=max_take)

    rules_summary = f"\nStarting heaps: {', '.join(str(heap) for heap in game.heaps)}"
    rules_summary += f" ({'misère' if misere else 'normal'} rules"
    if max_take:
        rules_summary += f", max {max_take} per turn"
    rules_summary += ")"
    print(rules_summary)

    # Main game loop.
    while not game.is_over():
        print("\n" + ("=" * 60))
        print(game.render(graphical=graphical))

        # Show educational hints if enabled
        if educational and current_player_is_human:
            show_hint = input("\nShow strategy hint? [y/N]: ").strip().lower()
            if show_hint == "y":
                print("\n" + game.get_strategy_hint())

        if num_players == 2:
            player_name = "You" if current_player_is_human else "Computer"
        else:
            if game.current_player == num_players - 1:
                player_name = f"Player {game.current_player + 1} (Computer)"
            else:
                player_name = f"Player {game.current_player + 1}"

        print(f"\n{player_name}'s turn:")

        if current_player_is_human or (num_players > 2 and game.current_player < num_players - 1):
            # Human player move
            move = input("Choose heap and amount (e.g., 2 3 to take 3 from heap 2): ").split()
            if len(move) != 2:
                print("Enter two numbers: heap index and count to remove.")
                continue
            try:
                heap_index = int(move[0]) - 1
                count = int(move[1])
                game.player_move(heap_index, count)
            except ValueError as exc:
                print(exc)
                continue
        else:
            # Computer move
            if educational:
                heap_index, count, explanation = game.computer_move(explain=True)
                print(f"Computer removes {count} from heap {heap_index + 1}.")
                print(f"Strategy: {explanation}")
            else:
                heap_index, count = game.computer_move()
                print(f"Computer removes {count} from heap {heap_index + 1}.")

        if not game.is_over():
            if num_players == 2:
                current_player_is_human = not current_player_is_human
            # In multiplayer, current_player is automatically updated by player_move

    # Determine the winner based on the game rules.
    print("\n" + "=" * 60)
    print("Game Over!")
    print("=" * 60)

    last_player = (game.current_player - 1) % game.num_players

    if misere:
        # In misère, the last player to move loses
        winner = (last_player + 1) % game.num_players
        print("Misère scoring: whoever takes the last object loses!")
    else:
        winner = last_player
        print("Normal scoring: taking the last object wins.")

    if num_players == 2:
        if (winner == 0 and human_starts) or (winner == 1 and not human_starts):
            print("You win! Congratulations.")
        else:
            print("Computer wins. Better luck next time!")
    else:
        if winner == num_players - 1:
            print(f"Player {winner + 1} (Computer) wins!")
        else:
            print(f"Player {winner + 1} wins! Congratulations.")


def play_northcott() -> None:
    """Play Northcott's Game."""

    print("\n" + "=" * 60)
    print("Northcott's Game")
    print("=" * 60)
    print("Players slide pieces towards each other on rows.")
    print("The gaps between pieces form Nim heaps.")
    print("The last player to move wins.")

    # Setup game
    board_size = 8
    num_rows = 3

    game = NorthcottGame(board_size=board_size, num_rows=num_rows)

    first_choice = input("\nDo you want to move first? [Y/n]: ").strip().lower()
    human_turn = first_choice != "n"

    print("\nStarting position:")
    print(game.render())

    # Main game loop
    while not game.is_over():
        print("\n" + "=" * 60)
        print(game.render())

        if human_turn:
            print("\nYour turn:")
            move_str = input("Enter: row piece position (e.g., '1 white 3' to move white in row 1 to position 3): ").split()
            if len(move_str) != 3:
                print("Please enter: row piece position")
                continue
            try:
                row_idx = int(move_str[0]) - 1
                piece = move_str[1].lower()
                new_pos = int(move_str[2])
                game.make_move(row_idx, piece, new_pos)
            except (ValueError, IndexError) as exc:
                print(f"Invalid move: {exc}")
                continue
        else:
            row_idx, piece, new_pos = game.computer_move()
            print(f"\nComputer moves {piece} piece in row {row_idx + 1} to position {new_pos}")

        human_turn = not human_turn

    # Determine winner
    print("\n" + "=" * 60)
    print("Game Over!")
    print("=" * 60)

    if human_turn:
        # Computer made last move
        print("Computer wins. Better luck next time!")
    else:
        print("You win! Congratulations.")


def play_wythoff() -> None:
    """Play Wythoff's Game."""

    print("\n" + "=" * 60)
    print("Wythoff's Game")
    print("=" * 60)
    print("Two heaps: Remove from one heap, or the same amount from both.")
    print("The last player to move wins.")

    # Setup game
    heap1_input = input("\nEnter size of heap 1 (press Enter for 5): ").strip()
    heap1 = int(heap1_input) if heap1_input else 5

    heap2_input = input("Enter size of heap 2 (press Enter for 8): ").strip()
    heap2 = int(heap2_input) if heap2_input else 8

    game = WythoffGame(heap1=heap1, heap2=heap2)

    first_choice = input("\nDo you want to move first? [Y/n]: ").strip().lower()
    human_turn = first_choice != "n"

    print("\nStarting position:")
    print(game.render())

    # Main game loop
    while not game.is_over():
        print("\n" + "=" * 60)
        print(game.render())

        if human_turn:
            print("\nYour turn:")
            print("Enter amounts to remove from each heap.")
            print("Examples: '3 0' (remove 3 from heap1), '0 2' (remove 2 from heap2), '2 2' (remove 2 from both)")
            move_str = input("Your move: ").split()
            if len(move_str) != 2:
                print("Please enter two numbers")
                continue
            try:
                h1_remove = int(move_str[0])
                h2_remove = int(move_str[1])
                game.make_move(h1_remove, h2_remove)
            except ValueError as exc:
                print(f"Invalid move: {exc}")
                continue
        else:
            h1_remove, h2_remove = game.computer_move()
            if h1_remove > 0 and h2_remove > 0:
                print(f"\nComputer removes {h1_remove} from both heaps")
            elif h1_remove > 0:
                print(f"\nComputer removes {h1_remove} from heap 1")
            else:
                print(f"\nComputer removes {h2_remove} from heap 2")

        human_turn = not human_turn

    # Determine winner
    print("\n" + "=" * 60)
    print("Game Over!")
    print("=" * 60)

    if human_turn:
        # Computer made last move
        print("Computer wins. Better luck next time!")
    else:
        print("You win! Congratulations.")
