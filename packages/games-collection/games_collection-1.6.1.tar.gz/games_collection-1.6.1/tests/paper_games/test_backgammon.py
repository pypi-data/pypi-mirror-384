"""Tests for the Backgammon game engine."""

from __future__ import annotations

import pytest

from paper_games.backgammon.backgammon import BAR, BEAR_OFF, BackgammonGame, Move


def _blank_board() -> list[tuple[int | None, int]]:
    return [(None, 0) for _ in range(24)]


def test_hit_and_reentry() -> None:
    """A hit should place a checker on the bar and allow re-entry."""

    game = BackgammonGame()
    points = _blank_board()
    points[10] = (1, 1)
    points[7] = (-1, 1)
    game.load_position(points, bars={1: 0, -1: 0}, bear_off={1: 0, -1: 0}, current_player=1)
    game.set_dice([3])
    hit_move = Move(10, 7, 3, True)
    assert (hit_move,) in game.get_valid_moves()
    assert game.make_move((hit_move,))
    assert game.bars[-1] == 1

    game.set_dice([3])
    reentry_move = Move(BAR, 2, 3, False)
    valid_reentries = game.get_valid_moves()
    assert (reentry_move,) in valid_reentries
    assert game.make_move((reentry_move,))
    assert game.bars[-1] == 0


def test_higher_die_required_when_only_one_checker_can_move() -> None:
    """When only one die can be used, the move must use the higher value die."""

    game = BackgammonGame()
    points = _blank_board()
    points[17] = (-1, 2)
    game.load_position(points, bars={1: 1, -1: 0}, bear_off={1: 0, -1: 0}, current_player=1)
    game.set_dice([6, 1])

    moves = game.get_valid_moves()
    assert moves, "Expected at least one legal move"
    assert any(sequence and sequence[0].die == 6 for sequence in moves)
    assert all(not sequence or sequence[0].die == 6 for sequence in moves)


def test_bearing_off_completes_game() -> None:
    """Bearing off the last checkers should end the game."""

    game = BackgammonGame()
    points = _blank_board()
    points[0] = (1, 1)
    points[1] = (1, 1)
    game.load_position(points, bars={1: 0, -1: 0}, bear_off={1: 13, -1: 0}, current_player=1)
    game.set_dice([1, 2])
    move_one = Move(0, BEAR_OFF, 1, False)
    move_two = Move(1, BEAR_OFF, 2, False)
    legal = game.get_valid_moves()
    assert (move_one, move_two) in legal or (move_two, move_one) in legal
    sequence = (move_one, move_two) if (move_one, move_two) in legal else (move_two, move_one)
    assert game.make_move(sequence)
    assert game.is_game_over()
    assert game.get_winner() == 1


def test_doubling_cube_flow() -> None:
    """Accepting or declining doubles should update cube state appropriately."""

    game = BackgammonGame()
    game.offer_double()
    assert game.pending_double_from == 1
    game.accept_double(-1)
    assert game.cube_value == 2
    assert game.cube_owner == -1
    assert game.pending_double_from is None

    game_two = BackgammonGame()
    game_two.offer_double()
    game_two.decline_double(-1)
    assert game_two.is_game_over()
    assert game_two.get_winner() == 1
    assert game_two.scores[1] == 1


def test_make_move_blocked_while_double_pending() -> None:
    """A move cannot be played until a pending double is resolved."""

    game = BackgammonGame()
    points = _blank_board()
    points[0] = (1, 1)
    game.load_position(points, bars={1: 0, -1: 0}, bear_off={1: 14, -1: 0}, current_player=1)
    game.set_dice([1])
    move = (Move(0, BEAR_OFF, 1, False),)
    assert move in game.get_valid_moves()

    game.offer_double()
    with pytest.raises(RuntimeError):
        game.make_move(move)


def test_gammon_and_backgammon_scoring() -> None:
    """Game completion should award gammons and backgammons."""

    gammon_game = BackgammonGame()
    points = _blank_board()
    points[0] = (1, 1)
    points[10] = (-1, 1)
    gammon_game.load_position(points, bars={1: 0, -1: 0}, bear_off={1: 14, -1: 0}, current_player=1)
    gammon_game.set_dice([1])
    gammon_game.make_move((Move(0, BEAR_OFF, 1, False),))
    assert gammon_game.is_game_over()
    assert gammon_game.scores[1] == 2

    backgammon_game = BackgammonGame()
    points = _blank_board()
    points[0] = (1, 1)
    backgammon_game.load_position(points, bars={1: 0, -1: 1}, bear_off={1: 14, -1: 0}, current_player=1)
    backgammon_game.set_dice([1])
    backgammon_game.make_move((Move(0, BEAR_OFF, 1, False),))
    assert backgammon_game.is_game_over()
    assert backgammon_game.scores[1] == 3
