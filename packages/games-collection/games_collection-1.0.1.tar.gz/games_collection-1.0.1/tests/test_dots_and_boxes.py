import pathlib
import random
import sys

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from paper_games.dots_and_boxes import DotsAndBoxes, Tournament


def test_computer_takes_bonus_turns_until_no_scoring_moves():
    game = DotsAndBoxes(size=1, rng=random.Random(0))
    # Human draws three sides of the single box.
    assert game.claim_edge("h", 0, 0, game.human_name) == 0
    assert game.claim_edge("v", 0, 0, game.human_name) == 0
    assert game.claim_edge("h", 1, 0, game.human_name) == 0

    moves = game.computer_turn()
    assert moves == [(("v", 0, 1), 1)]

    assert game.scores[game.computer_name] == 1
    assert game.is_finished()


def test_computer_opens_shortest_chain_when_forced():
    game = DotsAndBoxes(size=2, rng=random.Random(0))
    # Replicate the pre-computed state with varying chain penalties.
    preset_edges = [
        ("h", 1, 0),
        ("h", 1, 1),
        ("h", 2, 0),
        ("h", 2, 1),
        ("v", 0, 1),
    ]
    for orient, row, col in preset_edges:
        if orient == "h":
            game.horizontal_edges[(row, col)] = game.human_name
        else:
            game.vertical_edges[(row, col)] = game.human_name

    moves = game.computer_turn()
    assert moves, "Computer should make exactly one move in this forced state."
    first_move, completed = moves[0]
    assert first_move == ("h", 0, 0)
    assert completed == 0
    # Ensure no additional edges were drawn because the computer had to give up the turn.
    assert len(moves) == 1


def test_larger_board_sizes():
    """Test that larger board sizes work correctly."""
    for size in [2, 3, 4, 5, 6]:
        game = DotsAndBoxes(size=size)
        assert game.size == size
        assert len(game.boxes) == size * size
        expected_edges = 2 * size * (size + 1)
        assert len(game.available_edges()) == expected_edges


def test_chain_detection():
    """Test that chain detection works correctly."""
    game = DotsAndBoxes(size=2, rng=random.Random(0))
    # Set up a situation where a move would create a third edge
    game.claim_edge("h", 0, 0, game.human_name)
    game.claim_edge("v", 0, 0, game.human_name)

    # This move should create a third edge on box (0, 0)
    assert game._creates_third_edge(("h", 1, 0))


def test_scoring_move_detection():
    """Test that scoring move detection works."""
    game = DotsAndBoxes(size=1, rng=random.Random(0))
    game.claim_edge("h", 0, 0, game.human_name)
    game.claim_edge("v", 0, 0, game.human_name)
    game.claim_edge("h", 1, 0, game.human_name)

    # The last edge should be detected as a scoring move
    scoring_move = game._find_scoring_move()
    assert scoring_move == ("v", 0, 1)


def test_tournament_stats():
    """Test tournament statistics tracking."""
    tournament = Tournament(size=2, num_games=3, seed=42)
    stats = tournament.stats

    # Record some games
    stats.record_game(2, 1)  # Human wins
    stats.record_game(1, 2)  # Computer wins
    stats.record_game(2, 2)  # Tie

    assert stats.total_games == 3
    assert stats.human_wins == 1
    assert stats.computer_wins == 1
    assert stats.ties == 1
    assert abs(stats.win_percentage() - 33.33333333333333) < 0.001
    assert stats.total_human_score == 5
    assert stats.total_computer_score == 5
