"""Tests for the Boggle dictionary loader and game logic."""

from __future__ import annotations

import time

import pytest

from common.game_engine import GameState
from paper_games.boggle.boggle import BoggleGame, BoggleMove
from paper_games.boggle.dictionary import BoggleDictionary


@pytest.fixture(scope="module")
def small_dictionary() -> BoggleDictionary:
    """Provide a small in-memory dictionary for deterministic testing."""

    dictionary = BoggleDictionary()
    dictionary.load_words(["TEST", "TESTS", "QUIZ", "TEAM"])
    return dictionary


def test_dictionary_contains_and_prefix() -> None:
    """The packaged ENABLE lexicon should expose common English words."""

    dictionary = BoggleDictionary(language="en", lexicon="enable")
    assert dictionary.contains("quiz")
    assert dictionary.has_prefix("qu")
    assert "QUIZ" in dictionary


def test_qu_tile_search(small_dictionary: BoggleDictionary) -> None:
    """QU tiles should count as the digraph when searching the board."""

    game = BoggleGame(size=4, time_limit=60, dictionary=small_dictionary, player_names=["Alice"], seed=42)
    game._grid = [
        ["Qu", "I", "Z", "E"],
        ["E", "B", "C", "D"],
        ["E", "F", "G", "H"],
        ["I", "J", "K", "L"],
    ]
    assert game.is_word_in_grid("QUIZ")
    assert game.is_word_in_grid("QUE")
    assert not game.is_word_in_grid("QUILL")


def test_time_expiry_sets_game_over(small_dictionary: BoggleDictionary) -> None:
    """Time limits should automatically finish the round when expired."""

    game = BoggleGame(size=4, time_limit=1, dictionary=small_dictionary, player_names=["Solo"], seed=1)
    game._start_time = time.monotonic() - 5
    assert game.is_game_over()
    assert game.get_game_state() == GameState.FINISHED


def test_scoring_and_duplicates(small_dictionary: BoggleDictionary) -> None:
    """Scoring should follow official values and remove duplicate finds."""

    game = BoggleGame(size=4, time_limit=120, dictionary=small_dictionary, player_names=["Alice", "Bob"], seed=7)
    game._grid = [
        ["T", "E", "S", "T"],
        ["A", "S", "E", "S"],
        ["A", "M", "E", "D"],
        ["L", "O", "P", "Q"],
    ]
    assert game.make_move(BoggleMove(word="test", player_id=0))
    feedback = game.get_last_feedback()
    assert feedback is not None and feedback.points == 1
    assert game.get_scores()["Alice"] == 1

    assert game.make_move(BoggleMove(word="test", player_id=1))
    feedback = game.get_last_feedback()
    assert feedback is not None and feedback.points == 0
    assert feedback.reason and "Duplicate" in feedback.reason
    scores = game.get_scores()
    assert scores["Alice"] == 0
    assert scores["Bob"] == 0

    assert game.make_move(BoggleMove(word="tests", player_id=1))
    feedback = game.get_last_feedback()
    assert feedback is not None and feedback.points == 2
    assert game.get_scores()["Bob"] == 2

    assert game.make_move(BoggleMove(word="tests", player_id=0))
    feedback = game.get_last_feedback()
    assert feedback is not None and feedback.points == 0
    assert feedback.reason and "Duplicate" in feedback.reason
    scores = game.get_scores()
    assert scores["Alice"] == 0
    assert scores["Bob"] == 0

    claims = game.get_word_claims()
    assert claims["TEST"] == {"Alice", "Bob"}
    unique_alice = game.get_unique_words(0)
    assert "TESTS" not in unique_alice
    assert "TEST" not in unique_alice
