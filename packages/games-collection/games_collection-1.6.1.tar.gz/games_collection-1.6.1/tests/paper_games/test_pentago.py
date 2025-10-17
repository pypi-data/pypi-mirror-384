"""Unit tests for the Pentago game implementation."""

from __future__ import annotations

from common.game_engine import GameState
from paper_games.pentago import PentagoGame, PentagoMove


def test_quadrant_rotation_moves_marble() -> None:
    """Rotating a quadrant after placement should reposition the marble."""

    game = PentagoGame()
    move = PentagoMove(row=0, column=0, quadrant=0, direction="CW")
    assert game.make_move(move)
    board = game.get_board_snapshot()
    assert board[0][2] == 1
    assert board[0][0] == 0
    assert game.get_current_player() == 2


def test_detects_five_in_row_after_rotation() -> None:
    """Creating a five-in-a-row should end the game with a winner."""

    game = PentagoGame()
    for column in range(4):
        game._board[0][column] = 1
    game._current_player = 1
    move = PentagoMove(row=0, column=4, quadrant=3, direction="CW")
    assert game.make_move(move)
    assert game.is_game_over()
    assert game.get_game_state() == GameState.FINISHED
    assert game.get_winner() == 1
    assert game.get_winning_players() == (1,)


def test_draw_when_board_filled_without_five() -> None:
    """A completely filled board without a winner should be a draw."""

    game = PentagoGame()
    fill_pattern = [
        [2, 1, 2, 2, 2, 2],
        [2, 2, 1, 1, 2, 1],
        [1, 2, 1, 2, 1, 1],
        [2, 2, 1, 2, 2, 2],
        [0, 1, 2, 2, 2, 1],
        [1, 1, 2, 1, 2, 2],
    ]
    for row in range(6):
        for column in range(6):
            game._board[row][column] = fill_pattern[row][column]
    game._current_player = 1
    move = PentagoMove(row=4, column=0, quadrant=0, direction="CCW")
    assert game.make_move(move)
    assert game.is_game_over()
    assert game.get_game_state() == GameState.FINISHED
    assert game.get_winner() is None
    assert game.get_winning_players() == ()
