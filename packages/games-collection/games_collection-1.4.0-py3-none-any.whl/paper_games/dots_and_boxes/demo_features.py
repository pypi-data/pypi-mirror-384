#!/usr/bin/env python3
"""Demonstration script showcasing all Dots and Boxes features.

This script demonstrates:
1. Larger board sizes (4x4, 5x5, 6x6)
2. Chain identification highlighting
3. Network multiplayer mode
4. Move hints/suggestions
5. Tournament mode
"""

from paper_games.dots_and_boxes import DotsAndBoxes, Tournament
from paper_games.dots_and_boxes.network import NetworkClient, NetworkHost


def demo_larger_board_sizes():
    """Demonstrate larger board sizes."""
    print("\n" + "=" * 60)
    print("FEATURE 1: LARGER BOARD SIZES (4x4, 5x5, 6x6)")
    print("=" * 60)

    for size in [4, 5, 6]:
        game = DotsAndBoxes(size=size)
        print(f"\n{size}x{size} Board:")
        print(f"  - Total boxes: {len(game.boxes)}")
        print(f"  - Total edges: {len(game.available_edges())}")
        print(f"  - Horizontal edges: {len(game.horizontal_edges)}")
        print(f"  - Vertical edges: {len(game.vertical_edges)}")

        # Show a small portion of the board
        if size == 4:
            print("\nBoard visualization (4x4):")
            print(game.render())


def demo_chain_identification():
    """Demonstrate chain identification and highlighting."""
    print("\n" + "=" * 60)
    print("FEATURE 2: CHAIN IDENTIFICATION HIGHLIGHTING")
    print("=" * 60)

    game = DotsAndBoxes(size=3)

    # Create a scenario with chain potential
    print("\nSetting up board with chain potential...")
    game.claim_edge("h", 0, 0, game.human_name)
    game.claim_edge("v", 0, 0, game.human_name)

    print(game.render())

    # Test chain detection
    test_edge = ("h", 1, 0)
    creates_chain = game._creates_third_edge(test_edge)

    print(f"\nTesting edge {test_edge}:")
    if creates_chain:
        chain_length = game._chain_length_if_opened(test_edge)
        print("⚠️  WARNING: This creates a chain!")
        print(f"   Opponent could capture {chain_length} box{'es' if chain_length != 1 else ''}")
    else:
        print("✅ Safe move - no chain created")

    # Test a scoring move
    game2 = DotsAndBoxes(size=2)
    game2.claim_edge("h", 0, 0, game2.human_name)
    game2.claim_edge("v", 0, 0, game2.human_name)
    game2.claim_edge("h", 1, 0, game2.human_name)

    scoring_edge = ("v", 0, 1)
    if game2._would_complete_box(scoring_edge):
        print(f"\nEdge {scoring_edge}:")
        print("⭐ This move completes a box!")


def demo_move_hints():
    """Demonstrate move hints/suggestions."""
    print("\n" + "=" * 60)
    print("FEATURE 3: MOVE HINTS/SUGGESTIONS FOR LEARNING")
    print("=" * 60)

    game = DotsAndBoxes(size=2)

    # Scenario 1: Scoring move available
    game.claim_edge("h", 0, 0, game.human_name)
    game.claim_edge("v", 0, 0, game.human_name)
    game.claim_edge("h", 1, 0, game.human_name)

    print("\nCurrent board:")
    print(game.render())

    scoring_move = game._find_scoring_move()
    if scoring_move:
        print(f"\n💡 HINT: Complete a box with: {scoring_move}")

    # Scenario 2: Safe move available
    game2 = DotsAndBoxes(size=3)
    safe_moves = [move for move in game2.available_edges() if not game2._creates_third_edge(move)]
    if safe_moves:
        print(f"\n💡 HINT: Safe moves available: {len(safe_moves)} options")
        print(f"   Example safe move: {safe_moves[0]}")

    # Scenario 3: Forced to open chain
    game3 = DotsAndBoxes(size=2)
    # Fill board to demonstrate chain selection
    edges_to_fill = [("h", 0, 0), ("h", 0, 1), ("v", 0, 1), ("h", 2, 0), ("h", 2, 1), ("v", 0, 2)]
    for orient, row, col in edges_to_fill:
        try:
            game3.claim_edge(orient, row, col, game3.human_name)
        except (ValueError, KeyError):
            pass

    chain_starter = game3._choose_chain_starter()
    chain_length = game3._chain_length_if_opened(chain_starter)
    print(f"\n💡 HINT: Best of bad options: {chain_starter}")
    print(f"   (Opens chain of {chain_length} box{'es' if chain_length != 1 else ''})")


def demo_tournament_mode():
    """Demonstrate tournament mode."""
    print("\n" + "=" * 60)
    print("FEATURE 4: TOURNAMENT MODE WITH MULTIPLE GAMES")
    print("=" * 60)

    print("\nTournament setup:")
    tournament = Tournament(size=3, num_games=3, seed=42)
    print(f"  - Board size: {tournament.size}x{tournament.size}")
    print(f"  - Number of games: {tournament.num_games}")

    # Simulate a few games
    print("\nSimulating 3 games...")
    from paper_games.dots_and_boxes.tournament import TournamentStats

    stats = TournamentStats()

    # Game 1
    stats.record_game(6, 3)  # Human wins
    print("  Game 1: You: 6, Computer: 3 - You win! 🎉")

    # Game 2
    stats.record_game(2, 7)  # Computer wins
    print("  Game 2: You: 2, Computer: 7 - Computer wins! 🤖")

    # Game 3
    stats.record_game(4, 5)  # Computer wins
    print("  Game 3: You: 4, Computer: 5 - Computer wins! 🤖")

    print("\n" + "-" * 60)
    print("TOURNAMENT RESULTS")
    print("-" * 60)
    print(f"Total Games: {stats.total_games}")
    print(f"Human Wins: {stats.human_wins}")
    print(f"Computer Wins: {stats.computer_wins}")
    print(f"Ties: {stats.ties}")
    print(f"Win Percentage: {stats.win_percentage():.1f}%")
    print(f"Total Score - You: {stats.total_human_score}, Computer: {stats.total_computer_score}")
    print(f"Average Score Difference: {stats.avg_score_diff():.2f}")
    print("-" * 60)


def demo_network_multiplayer():
    """Demonstrate network multiplayer mode."""
    print("\n" + "=" * 60)
    print("FEATURE 5: NETWORK MULTIPLAYER MODE")
    print("=" * 60)

    print("\nNetwork multiplayer uses TCP sockets with JSON protocol.")
    print("Two modes available:")

    print("\n1. HOST MODE:")
    print("   python -m paper_games.dots_and_boxes --host --size 4 --name 'Alice'")
    host = NetworkHost(size=4, player_name="Alice", port=5555)
    print(f"   - Creates host: {host.player_name}")
    print(f"   - Board size: {host.size}x{host.size}")
    print(f"   - Listening on port: {host.port}")
    print("   - Waits for opponent to connect...")

    print("\n2. CLIENT MODE:")
    print("   python -m paper_games.dots_and_boxes --join localhost --name 'Bob'")
    client = NetworkClient(size=4, player_name="Bob", host="localhost", port=5555)
    print(f"   - Creates client: {client.player_name}")
    print(f"   - Connects to: {client.host}:{client.port}")
    print("   - Joins the game...")

    print("\nNetwork features:")
    print("  ✓ Real-time move synchronization")
    print("  ✓ Turn-based gameplay")
    print("  ✓ Score tracking for both players")
    print("  ✓ Connection error handling")
    print("  ✓ Works over local network or internet")


def main():
    """Run all feature demonstrations."""
    print("\n" + "=" * 60)
    print("DOTS AND BOXES - FEATURE DEMONSTRATION")
    print("=" * 60)
    print("\nThis demo showcases all implemented features:")
    print("1. Larger board sizes (4x4, 5x5, 6x6)")
    print("2. Chain identification highlighting")
    print("3. Move hints/suggestions for learning")
    print("4. Tournament mode with multiple games")
    print("5. Network multiplayer mode")

    demo_larger_board_sizes()
    demo_chain_identification()
    demo_move_hints()
    demo_tournament_mode()
    demo_network_multiplayer()

    print("\n" + "=" * 60)
    print("DEMONSTRATION COMPLETE")
    print("=" * 60)
    print("\nTo try these features yourself:")
    print("  • GUI mode:        python -m paper_games.dots_and_boxes --gui --size 5 --hints")
    print("  • Tournament:      python -m paper_games.dots_and_boxes --tournament 5 --size 4")
    print("  • Host multiplayer: python -m paper_games.dots_and_boxes --host --size 3 --name You")
    print("  • Join multiplayer: python -m paper_games.dots_and_boxes --join localhost --name Friend")
    print("\n" + "=" * 60 + "\n")


if __name__ == "__main__":
    main()
