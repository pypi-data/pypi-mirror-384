"""Demonstration script showcasing all Nim features and variants.

Run this script to see examples of:
- Graphical heap representation
- Educational strategy hints
- Computer moves with explanations
- Multiplayer mode
- Custom rule variations
- Northcott's Game
- Wythoff's Game
"""

from paper_games.nim import NimGame, NorthcottGame, WythoffGame


def demo_graphical_rendering():
    """Demonstrate graphical heap visualization."""
    print("=" * 70)
    print("FEATURE 1: Graphical Heap Representation")
    print("=" * 70)
    print("\nStandard text representation:")
    game = NimGame([4, 6, 8])
    print(game.render(graphical=False))

    print("\nGraphical block representation:")
    print(game.render(graphical=True))
    print()


def demo_educational_mode():
    """Demonstrate educational strategy hints."""
    print("=" * 70)
    print("FEATURE 2: Educational Mode with Strategy Hints")
    print("=" * 70)
    game = NimGame([3, 4, 5])
    print(game.get_strategy_hint())
    print()


def demo_computer_explanation():
    """Demonstrate computer moves with explanations."""
    print("=" * 70)
    print("FEATURE 3: Computer Moves with Explanations")
    print("=" * 70)
    game = NimGame([5, 7, 9])
    print(f"Current state: {game.heaps}")
    print(f"Nim-sum: {game.nim_sum()}")

    heap_idx, count, explanation = game.computer_move(explain=True)
    print(f"\nComputer's move: Remove {count} from heap {heap_idx + 1}")
    print(f"Explanation: {explanation}")
    print(f"New state: {game.heaps}")
    print(f"New Nim-sum: {game.nim_sum()}")
    print()


def demo_multiplayer():
    """Demonstrate multiplayer mode."""
    print("=" * 70)
    print("FEATURE 4: Multiplayer Mode (3+ Players)")
    print("=" * 70)
    game = NimGame([10, 12, 15], num_players=4)
    print(f"Game with {game.num_players} players")
    print(f"Initial heaps: {game.heaps}")
    print(f"Current player: Player {game.current_player + 1}")

    # Simulate a few moves
    for i in range(3):
        heap_idx = i % len(game.heaps)
        game.player_move(heap_idx, 2)
        print(f"Player {i + 1} removes 2 from heap {heap_idx + 1}")
        print(f"  Current player is now: Player {game.current_player + 1}")
        print(f"  Heaps: {game.heaps}")
    print()


def demo_custom_rules():
    """Demonstrate custom rule variations."""
    print("=" * 70)
    print("FEATURE 5: Custom Rule Variations")
    print("=" * 70)

    # Max-take rule
    game = NimGame([10, 15, 20], max_take=5)
    print(f"Game with max_take={game.max_take}")
    print(f"Initial heaps: {game.heaps}")

    print("\nValid move (taking 3):")
    game.player_move(0, 3)
    print(f"  Heaps after move: {game.heaps}")

    print("\nAttempting invalid move (taking 6):")
    try:
        game.player_move(1, 6)
    except ValueError as e:
        print(f"  Error: {e}")

    # Misère rule
    print("\nMisère mode (last player loses):")
    game2 = NimGame([2, 2, 2], misere=True)
    print(f"  Heaps: {game2.heaps}")
    print(f"  Misère: {game2.misere}")
    print()


def demo_northcott():
    """Demonstrate Northcott's Game."""
    print("=" * 70)
    print("VARIANT 1: Northcott's Game")
    print("=" * 70)
    print("Players slide pieces on parallel rows toward each other.")
    print("The gaps between pieces form Nim heaps.\n")

    game = NorthcottGame(board_size=8, num_rows=3, rows=[(1, 6), (0, 5), (2, 7)])
    print(game.render())

    print("\nMaking a move: White piece in row 1 from position 1 to 3")
    game.make_move(0, "white", 3)
    print(game.render())

    print("\nComputer's turn:")
    row, piece, pos = game.computer_move()
    print(f"Computer moved {piece} piece in row {row + 1} to position {pos}")
    print(game.render())
    print()


def demo_wythoff():
    """Demonstrate Wythoff's Game."""
    print("=" * 70)
    print("VARIANT 2: Wythoff's Game")
    print("=" * 70)
    print("Two heaps with three move types:")
    print("  1. Remove from heap 1 only")
    print("  2. Remove from heap 2 only")
    print("  3. Remove same amount from both (diagonal move)\n")

    game = WythoffGame(heap1=5, heap2=8)
    print(game.render())

    print("\nPlayer move: Remove 2 from heap 1")
    game.make_move(2, 0)
    print(game.render())

    print("\nPlayer move: Diagonal - remove 1 from both")
    game.make_move(1, 1)
    print(game.render())

    print("\nComputer's turn:")
    h1, h2 = game.computer_move()
    if h1 > 0 and h2 > 0:
        print(f"Computer made diagonal move: removed {h1} from both heaps")
    elif h1 > 0:
        print(f"Computer removed {h1} from heap 1")
    else:
        print(f"Computer removed {h2} from heap 2")
    print(game.render())
    print()


def main():
    """Run all demonstrations."""
    print("\n" + "=" * 70)
    print("NIM GAME ENHANCEMENTS DEMONSTRATION")
    print("=" * 70)
    print("\nThis demo showcases all new features added to the Nim game.\n")

    demo_graphical_rendering()
    input("Press Enter to continue...")

    demo_educational_mode()
    input("Press Enter to continue...")

    demo_computer_explanation()
    input("Press Enter to continue...")

    demo_multiplayer()
    input("Press Enter to continue...")

    demo_custom_rules()
    input("Press Enter to continue...")

    demo_northcott()
    input("Press Enter to continue...")

    demo_wythoff()

    print("=" * 70)
    print("END OF DEMONSTRATION")
    print("=" * 70)
    print("\nTo play interactively, run: python -m paper_games.nim")
    print("For more information, see: paper_games/nim/README.md")
    print()


if __name__ == "__main__":
    main()
