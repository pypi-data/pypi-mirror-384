import pathlib
import sys

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from paper_games.nim import NimGame, NorthcottGame, WythoffGame


def test_graphical_rendering():
    """Test that graphical rendering doesn't crash."""
    game = NimGame([3, 5, 7])
    output = game.render(graphical=True)
    assert "▓▓▓" in output
    assert "[  3]" in output
    assert "Heap1" in output


def test_strategy_hint():
    """Test that strategy hints are generated."""
    game = NimGame([3, 4, 5])
    hint = game.get_strategy_hint()
    assert "Strategy Analysis" in hint
    assert "Nim-sum" in hint
    assert "binary" in hint


def test_educational_mode():
    """Test computer move with explanation."""
    game = NimGame([3, 4, 5])
    result = game.computer_move(explain=True)
    assert len(result) == 3
    heap_idx, count, explanation = result
    assert isinstance(heap_idx, int)
    assert isinstance(count, int)
    assert isinstance(explanation, str)
    assert len(explanation) > 0


def test_multiplayer():
    """Test multiplayer mode with 3+ players."""
    game = NimGame([5, 6, 7], num_players=3)
    assert game.num_players == 3
    assert game.current_player == 0

    game.player_move(0, 2)
    assert game.current_player == 1

    game.player_move(1, 1)
    assert game.current_player == 2

    game.player_move(2, 1)
    assert game.current_player == 0


def test_max_take_rule():
    """Test custom rule with max_take limit."""
    game = NimGame([5, 6, 7], max_take=3)

    # Valid move
    game.player_move(0, 3)
    assert game.heaps[0] == 2

    # Invalid move (too many)
    try:
        game.player_move(1, 4)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "Cannot take more than 3" in str(e)


def test_northcott_basic():
    """Test basic Northcott game functionality."""
    game = NorthcottGame(board_size=8, num_rows=2, rows=[(1, 5), (2, 6)])

    # Check initial state
    gaps = game.get_gaps()
    assert gaps == [3, 3]
    assert game.nim_sum() == 0

    # Make a move
    game.make_move(0, "white", 2)
    gaps = game.get_gaps()
    assert gaps == [2, 3]

    # Test rendering
    output = game.render()
    assert "Northcott" in output
    assert "W" in output
    assert "B" in output


def test_northcott_invalid_moves():
    """Test that invalid moves are rejected."""
    game = NorthcottGame(board_size=8, num_rows=1, rows=[(2, 6)])

    # Try to move white past black
    try:
        game.make_move(0, "white", 7)
        assert False, "Should have raised ValueError"
    except ValueError:
        pass

    # Try to move black past white
    try:
        game.make_move(0, "black", 1)
        assert False, "Should have raised ValueError"
    except ValueError:
        pass


def test_wythoff_basic():
    """Test basic Wythoff game functionality."""
    game = WythoffGame(heap1=5, heap2=8)

    assert game.heap1 == 5
    assert game.heap2 == 8
    assert not game.is_over()

    # Remove from heap1
    game.make_move(2, 0)
    assert game.heap1 == 3
    assert game.heap2 == 8

    # Remove from heap2
    game.make_move(0, 3)
    assert game.heap1 == 3
    assert game.heap2 == 5

    # Diagonal move
    game.make_move(2, 2)
    assert game.heap1 == 1
    assert game.heap2 == 3


def test_wythoff_invalid_moves():
    """Test that invalid Wythoff moves are rejected."""
    game = WythoffGame(heap1=5, heap2=8)

    # Try to remove different amounts from both heaps
    try:
        game.make_move(2, 3)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "same amount" in str(e)

    # Try to remove more than heap contains
    try:
        game.make_move(10, 0)
        assert False, "Should have raised ValueError"
    except ValueError:
        pass


def test_wythoff_computer_move():
    """Test that Wythoff computer can make a move."""
    game = WythoffGame(heap1=3, heap2=5)
    initial_sum = game.heap1 + game.heap2

    h1, h2 = game.computer_move()

    # Check that something was removed
    assert game.heap1 + game.heap2 < initial_sum
    assert h1 >= 0 and h2 >= 0
    assert h1 > 0 or h2 > 0


def test_backward_compatibility():
    """Test that old code still works (computer_move without explain)."""
    game = NimGame([3, 4, 5])
    result = game.computer_move()
    assert len(result) == 2
    heap_idx, count = result
    assert isinstance(heap_idx, int)
    assert isinstance(count, int)


if __name__ == "__main__":
    test_graphical_rendering()
    test_strategy_hint()
    test_educational_mode()
    test_multiplayer()
    test_max_take_rule()
    test_northcott_basic()
    test_northcott_invalid_moves()
    test_wythoff_basic()
    test_wythoff_invalid_moves()
    test_wythoff_computer_move()
    test_backward_compatibility()
    print("All enhancement tests passed!")
