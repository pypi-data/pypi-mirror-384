"""Demo script to showcase Dots and Boxes features.

This script demonstrates various features of the enhanced Dots and Boxes game.
"""

from __future__ import annotations

from .dots_and_boxes import DotsAndBoxes


def demo_board_sizes() -> None:
    """Demonstrate different board sizes."""
    print("=" * 60)
    print("DEMO: Multiple Board Sizes")
    print("=" * 60)
    print("\nThe game now supports board sizes from 2x2 to 6x6.\n")

    for size in [2, 3, 4, 5, 6]:
        game = DotsAndBoxes(size=size)
        print(f"\n{size}x{size} Board ({len(game.boxes)} boxes, {len(game.available_edges())} edges):")
        print(game.render())
        print()


def demo_chain_detection() -> None:
    """Demonstrate chain detection capabilities."""
    print("\n" + "=" * 60)
    print("DEMO: Chain Detection")
    print("=" * 60)
    print("\nThe AI can detect when a move would create a chain.\n")

    game = DotsAndBoxes(size=2)

    # Create a scenario with chains
    print("Setting up a board with potential chains...\n")
    game.claim_edge("h", 0, 0, "Human")
    game.claim_edge("v", 0, 0, "Human")
    game.claim_edge("h", 1, 0, "Human")

    print(game.render())
    print()

    # Test chain detection
    test_move = ("v", 0, 1)
    if game._would_complete_box(test_move):
        print(f"✅ Move {test_move} would complete a box!")
    else:
        print(f"❌ Move {test_move} would not complete a box.")

    test_move2 = ("h", 1, 1)
    if game._creates_third_edge(test_move2):
        print(f"⚠️ Move {test_move2} would create a third edge (risky!).")
    else:
        print(f"✅ Move {test_move2} is safe (no third edge).")


def demo_scoring_detection() -> None:
    """Demonstrate scoring move detection."""
    print("\n" + "=" * 60)
    print("DEMO: Scoring Move Detection")
    print("=" * 60)
    print("\nThe AI can find moves that complete boxes.\n")

    game = DotsAndBoxes(size=1)

    # Set up a nearly complete box
    game.claim_edge("h", 0, 0, "Human")
    game.claim_edge("v", 0, 0, "Human")
    game.claim_edge("h", 1, 0, "Human")

    print(game.render())
    print()

    scoring_move = game._find_scoring_move()
    if scoring_move:
        print(f"🎯 The AI found a scoring move: {scoring_move}")
    else:
        print("No scoring moves available.")


def demo_game_play() -> None:
    """Demonstrate a quick automated game."""
    print("\n" + "=" * 60)
    print("DEMO: Automated Game Play")
    print("=" * 60)
    print("\nWatching a quick automated game on a 2x2 board...\n")

    import random

    game = DotsAndBoxes(size=2, rng=random.Random(42))
    move_count = 0

    print("Initial board:")
    print(game.render())
    print()

    while not game.is_finished() and move_count < 6:
        # Make a random move
        available = game.available_edges()
        if available:
            move = random.choice(available)
            orient, row, col = move
            player = "Human" if move_count % 2 == 0 else "Computer"
            completed = game.claim_edge(orient, row, col, player)
            move_count += 1

            print(f"Move {move_count}: {player} plays {orient} {row} {col}")
            if completed:
                print(f"  → Completed {completed} box{'es' if completed > 1 else ''}!")

    print(f"\nBoard after {move_count} moves:")
    print(game.render())
    print(f"\nScore - Human: {game.scores['Human']}, Computer: {game.scores['Computer']}")


def demo_tournament_stats() -> None:
    """Demonstrate tournament statistics."""
    print("\n" + "=" * 60)
    print("DEMO: Tournament Statistics")
    print("=" * 60)
    print("\nTournament mode tracks detailed statistics across multiple games.\n")

    from .tournament import TournamentStats

    stats = TournamentStats()

    # Simulate some game results
    stats.record_game(3, 1)  # Human wins
    stats.record_game(1, 3)  # Computer wins
    stats.record_game(2, 2)  # Tie
    stats.record_game(4, 0)  # Human dominates
    stats.record_game(0, 4)  # Computer dominates

    print(stats)


def run_all_demos() -> None:
    """Run all demonstrations."""
    print("\n")
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 10 + "Dots and Boxes - Feature Demonstrations" + " " * 9 + "║")
    print("╚" + "═" * 58 + "╝")

    demo_board_sizes()
    demo_chain_detection()
    demo_scoring_detection()
    demo_game_play()
    demo_tournament_stats()

    print("\n" + "=" * 60)
    print("DEMO COMPLETE")
    print("=" * 60)
    print("\nTo try these features yourself:")
    print("  CLI:        python -m paper_games.dots_and_boxes --size 4")
    print("  GUI:        python -m paper_games.dots_and_boxes --gui --hints")
    print("  Tournament: python -m paper_games.dots_and_boxes --tournament 3")
    print("  Multiplayer:")
    print("    Host:     python -m paper_games.dots_and_boxes --host")
    print("    Join:     python -m paper_games.dots_and_boxes --join localhost")
    print()


if __name__ == "__main__":
    run_all_demos()
