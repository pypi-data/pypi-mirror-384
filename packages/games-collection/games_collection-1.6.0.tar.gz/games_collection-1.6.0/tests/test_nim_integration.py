"""Integration tests for Nim enhancements.

These tests verify that all features work together correctly in realistic scenarios.
"""

import pathlib
import sys

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from paper_games.nim import NimGame, NorthcottGame, WythoffGame


def test_complete_game_flow():
    """Test a complete game from start to finish."""
    game = NimGame([3, 4, 5])

    # Human makes a move
    game.player_move(0, 2)
    assert game.heaps == [1, 4, 5]

    # Computer responds
    heap_idx, count = game.computer_move()
    assert game.heaps[heap_idx] >= 0

    # Continue until game over
    moves = 0
    while not game.is_over() and moves < 20:
        if any(h > 0 for h in game.heaps):
            available_heap = next(i for i, h in enumerate(game.heaps) if h > 0)
            take_amount = min(game.heaps[available_heap], 2)
            game.player_move(available_heap, take_amount)
        if not game.is_over():
            game.computer_move()
        moves += 1

    assert game.is_over()
    assert all(h == 0 for h in game.heaps)


def test_educational_game():
    """Test that educational features don't interfere with gameplay."""
    game = NimGame([5, 6, 7])

    # Get hint before move
    hint = game.get_strategy_hint()
    assert "Strategy Analysis" in hint

    # Make explained computer move
    heap_idx, count, explanation = game.computer_move(explain=True)
    assert len(explanation) > 0

    # Continue playing normally
    game.player_move(0, 1)
    assert not game.is_over()

    # Mix explained and normal moves
    game.computer_move(explain=False)
    game.player_move(1, 1)

    # Get another hint mid-game
    hint2 = game.get_strategy_hint()
    assert "Nim-sum" in hint2


def test_multiplayer_complete_game():
    """Test a complete multiplayer game."""
    game = NimGame([4, 5, 6], num_players=3)

    move_count = 0
    expected_player = 0

    while not game.is_over() and move_count < 30:
        assert game.current_player == expected_player

        # Find a valid move
        available_heap = next(i for i, h in enumerate(game.heaps) if h > 0)
        game.player_move(available_heap, 1)

        if not game.is_over():
            expected_player = (expected_player + 1) % 3

        move_count += 1

    assert game.is_over()


def test_custom_rules_enforcement():
    """Test that custom rules are consistently enforced."""
    game = NimGame([10, 12, 15], max_take=4)

    # Valid moves under limit
    game.player_move(0, 4)
    game.player_move(1, 3)
    game.player_move(2, 2)

    # Computer should also respect the limit
    heap_idx, count = game.computer_move()
    assert count <= 4

    # Continue with more moves
    game.player_move(0, 1)
    heap_idx, count = game.computer_move()
    assert count <= 4


def test_variant_games_playable():
    """Test that variant games can be played to completion."""
    # Northcott game
    north = NorthcottGame(board_size=6, num_rows=2, rows=[(0, 4), (1, 5)])

    moves = 0
    while not north.is_over() and moves < 20:
        row_idx, piece, new_pos = north.computer_move()
        assert 0 <= new_pos < 6
        moves += 1

    assert north.is_over()

    # Wythoff game
    wyth = WythoffGame(heap1=3, heap2=5)

    moves = 0
    while not wyth.is_over() and moves < 20:
        h1_remove, h2_remove = wyth.computer_move()
        assert h1_remove >= 0 and h2_remove >= 0
        moves += 1

    assert wyth.is_over()


def test_graphical_render_with_various_sizes():
    """Test graphical rendering with different heap sizes."""
    # Small heaps
    game1 = NimGame([1, 2, 3])
    output1 = game1.render(graphical=True)
    assert "▓▓▓" in output1
    assert "[  1]" in output1

    # Medium heaps
    game2 = NimGame([5, 8, 12])
    output2 = game2.render(graphical=True)
    assert "▓▓▓" in output2

    # Large heaps (should be truncated)
    game3 = NimGame([20, 25, 30])
    output3 = game3.render(graphical=True)
    assert "showing top 15 levels only" in output3


def test_misere_with_educational_mode():
    """Test that misère mode works with educational features."""
    # Test with singleton heaps (misère endgame)
    game = NimGame([1, 1, 1], misere=True)

    # Get hint for misère game at endgame
    hint = game.get_strategy_hint()
    assert "Misère" in hint or "Endgame" in hint

    # Computer should handle misère endgame
    heap_idx, count, explanation = game.computer_move(explain=True)
    assert "Misère" in explanation or "misère" in explanation.lower()


def test_mixed_features():
    """Test using multiple features together."""
    # Create game with multiple enhancements
    game = NimGame(heaps=[8, 10, 12], num_players=3, max_take=5, misere=True)

    # Verify all features are active
    assert game.num_players == 3
    assert game.max_take == 5
    assert game.misere is True

    # Get graphical rendering
    output = game.render(graphical=True)
    assert "▓▓▓" in output

    # Get strategy hint
    hint = game.get_strategy_hint()
    assert len(hint) > 0

    # Make moves respecting max_take
    game.player_move(0, 5)  # Max allowed

    # Computer move with explanation
    heap_idx, count, explanation = game.computer_move(explain=True)
    assert count <= 5  # Should respect max_take

    # Continue game
    game.player_move(1, 3)
    assert not game.is_over()


if __name__ == "__main__":
    test_complete_game_flow()
    test_educational_game()
    test_multiplayer_complete_game()
    test_custom_rules_enforcement()
    test_variant_games_playable()
    test_graphical_render_with_various_sizes()
    test_misere_with_educational_mode()
    test_mixed_features()
    print("All integration tests passed!")
