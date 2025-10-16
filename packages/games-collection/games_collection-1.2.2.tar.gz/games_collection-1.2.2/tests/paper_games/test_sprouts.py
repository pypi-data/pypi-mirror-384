"""Unit tests for the Sprouts implementation."""

from __future__ import annotations

import pytest

from paper_games.sprouts.sprouts import SproutsGame


def test_legal_move_updates_degrees() -> None:
    game = SproutsGame(initial_dots=3)
    assert game.make_move((0, 1))

    state = game.get_state_representation()
    assert state["dots"][0]["degree"] == 1
    assert state["dots"][1]["degree"] == 1

    new_dot_id = max(state["dots"].keys())
    assert state["dots"][new_dot_id]["degree"] == 2
    assert game.remaining_lives(0) == 2
    assert game.remaining_lives(1) == 2


def test_loop_requires_two_lives() -> None:
    game = SproutsGame(initial_dots=2)
    assert game.make_move((0, 0))
    assert game.remaining_lives(0) == 1
    assert not game.make_move((0, 0))
    assert game.get_last_error() is not None


def test_crossing_move_rejected() -> None:
    game = SproutsGame(initial_dots=4)
    game._dots[0].x, game._dots[0].y = 0.1, 0.1
    game._dots[1].x, game._dots[1].y = 0.9, 0.1
    game._dots[2].x, game._dots[2].y = 0.1, 0.9
    game._dots[3].x, game._dots[3].y = 0.9, 0.9

    assert game.make_move((0, 3))
    assert not game.make_move((1, 2))
    assert "crosses" in (game.get_last_error() or "")


def test_game_termination_detection() -> None:
    game = SproutsGame(initial_dots=1)
    while True:
        move = game.suggest_move()
        if move is None:
            break
        assert game.make_move(move)

    assert game.is_game_over()
    assert game.get_game_state().name == "FINISHED"
    assert not game.has_moves_remaining()


@pytest.mark.parametrize(
    "dots,expected_nimber",
    [
        (0, 0),
        (1, 0),
        (2, 0),
    ],
)
def test_nimber_values(dots: int, expected_nimber: int) -> None:
    game = SproutsGame(initial_dots=dots)
    assert game.compute_nimber() == expected_nimber
