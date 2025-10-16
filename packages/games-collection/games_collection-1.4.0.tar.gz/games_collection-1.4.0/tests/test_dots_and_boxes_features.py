"""Test all Dots and Boxes features requested in the issue."""

import pathlib
import random
import sys

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from paper_games.dots_and_boxes import DotsAndBoxes, Tournament
from paper_games.dots_and_boxes.network import NetworkClient, NetworkHost
from paper_games.dots_and_boxes.tournament import TournamentStats


def test_larger_board_sizes():
    """Test that 4x4, 5x5, and 6x6 boards work correctly."""
    # Test 4x4 board
    game_4x4 = DotsAndBoxes(size=4)
    assert game_4x4.size == 4
    assert len(game_4x4.boxes) == 16
    assert len(game_4x4.horizontal_edges) == 20  # 5 rows × 4 cols
    assert len(game_4x4.vertical_edges) == 20  # 4 rows × 5 cols
    assert len(game_4x4.available_edges()) == 40

    # Test 5x5 board
    game_5x5 = DotsAndBoxes(size=5)
    assert game_5x5.size == 5
    assert len(game_5x5.boxes) == 25
    assert len(game_5x5.horizontal_edges) == 30  # 6 rows × 5 cols
    assert len(game_5x5.vertical_edges) == 30  # 5 rows × 6 cols
    assert len(game_5x5.available_edges()) == 60

    # Test 6x6 board
    game_6x6 = DotsAndBoxes(size=6)
    assert game_6x6.size == 6
    assert len(game_6x6.boxes) == 36
    assert len(game_6x6.horizontal_edges) == 42  # 7 rows × 6 cols
    assert len(game_6x6.vertical_edges) == 42  # 6 rows × 7 cols
    assert len(game_6x6.available_edges()) == 84

    print("✓ Larger board sizes (4x4, 5x5, 6x6) working correctly")


def test_chain_identification():
    """Test chain identification and analysis functionality."""
    game = DotsAndBoxes(size=3, rng=random.Random(42))

    # Set up a scenario with a potential chain
    game.claim_edge("h", 0, 0, game.human_name)
    game.claim_edge("v", 0, 0, game.human_name)

    # Test chain detection
    edge_creates_chain = ("h", 1, 0)
    assert game._creates_third_edge(edge_creates_chain), "Should detect third edge creation"

    # Test chain length calculation
    chain_length = game._chain_length_if_opened(edge_creates_chain)
    assert chain_length > 0, "Should calculate chain length"

    # Test scoring move detection
    game2 = DotsAndBoxes(size=2, rng=random.Random(42))
    game2.claim_edge("h", 0, 0, game2.human_name)
    game2.claim_edge("v", 0, 0, game2.human_name)
    game2.claim_edge("h", 1, 0, game2.human_name)

    scoring_move = game2._find_scoring_move()
    assert scoring_move is not None, "Should find scoring move"
    assert game2._would_complete_box(scoring_move), "Scoring move should complete a box"

    print("✓ Chain identification and analysis working correctly")


def test_move_hints_logic():
    """Test move hints/suggestions logic."""
    game = DotsAndBoxes(size=2, rng=random.Random(42))

    # Test finding a scoring move
    game.claim_edge("h", 0, 0, game.human_name)
    game.claim_edge("v", 0, 0, game.human_name)
    game.claim_edge("h", 1, 0, game.human_name)

    hint = game._find_scoring_move()
    assert hint is not None, "Should suggest scoring move"
    assert game._would_complete_box(hint), "Hint should complete a box"

    # Test finding a safe move
    game2 = DotsAndBoxes(size=3, rng=random.Random(42))
    safe_moves = [move for move in game2.available_edges() if not game2._creates_third_edge(move)]
    assert len(safe_moves) > 0, "Should have safe moves available at game start"

    # Test chain starter selection when forced
    game3 = DotsAndBoxes(size=2, rng=random.Random(42))
    # Fill board to force chain decision
    for _ in range(8):  # Fill some edges
        available = [m for m in game3.available_edges() if not game3._creates_third_edge(m)]
        if available:
            orient, row, col = available[0]
            game3.claim_edge(orient, row, col, game3.human_name)

    print("✓ Move hints/suggestions logic working correctly")


def test_tournament_mode():
    """Test tournament mode with multiple games and statistics."""
    tournament = Tournament(size=2, num_games=3, seed=42)

    # Test tournament initialization
    assert tournament.size == 2
    assert tournament.num_games == 3
    assert tournament.stats.total_games == 0

    # Test tournament stats
    stats = TournamentStats()
    stats.record_game(5, 3)  # Human wins
    stats.record_game(2, 4)  # Computer wins
    stats.record_game(3, 3)  # Tie

    assert stats.total_games == 3
    assert stats.human_wins == 1
    assert stats.computer_wins == 1
    assert stats.ties == 1
    assert stats.total_human_score == 10
    assert stats.total_computer_score == 10
    assert abs(stats.win_percentage() - 33.33333333333333) < 0.01
    assert abs(stats.avg_score_diff() - 0.0) < 0.01

    # Test playing a single game in tournament
    human_score, computer_score = tournament.play_game(0, interactive=False)
    assert isinstance(human_score, int)
    assert isinstance(computer_score, int)
    assert human_score >= 0
    assert computer_score >= 0

    print("✓ Tournament mode with statistics working correctly")


def test_network_multiplayer_classes():
    """Test network multiplayer classes instantiation."""
    # Test NetworkHost
    host = NetworkHost(size=4, player_name="Alice", port=5555)
    assert host.size == 4
    assert host.player_name == "Alice"
    assert host.port == 5555
    assert host.opponent_name == "Opponent"

    # Test NetworkClient
    client = NetworkClient(size=4, player_name="Bob", host="localhost", port=5555)
    assert client.size == 4
    assert client.player_name == "Bob"
    assert client.host == "localhost"
    assert client.port == 5555
    assert client.opponent_name == "Opponent"

    print("✓ Network multiplayer classes working correctly")


def test_all_features_integration():
    """Test that all features work together on different board sizes."""
    for size in [4, 5, 6]:
        # Create game with larger board
        game = DotsAndBoxes(size=size, rng=random.Random(42))

        # Test chain detection works on larger boards
        available = game.available_edges()
        if available:
            edge = available[0]
            creates_chain = game._creates_third_edge(edge)
            # Should not create chain on empty board
            assert not creates_chain, f"Empty {size}x{size} board should have no chains"

        # Test tournament with larger board
        tournament = Tournament(size=size, num_games=1, seed=42)
        assert tournament.size == size

        # Test network classes with larger board
        host = NetworkHost(size=size, player_name="Player1", port=5555)
        assert host.size == size

    print("✓ All features integration test passed for board sizes 4x4, 5x5, 6x6")


if __name__ == "__main__":
    test_larger_board_sizes()
    test_chain_identification()
    test_move_hints_logic()
    test_tournament_mode()
    test_network_multiplayer_classes()
    test_all_features_integration()
    print("\n✅ All Dots and Boxes features tests passed!")
