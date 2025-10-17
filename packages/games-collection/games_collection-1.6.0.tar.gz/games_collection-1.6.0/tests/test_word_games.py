"""Tests for word games."""

from __future__ import annotations

import asyncio
from pathlib import Path

from word_games import (
    AnagramsGame,
    AsyncWordPlaySession,
    CrosswordGame,
    CrosswordPackManager,
    DictionaryValidator,
    TriviaGame,
    WordBuilderGame,
)
from word_games.trivia.trivia import TriviaCache, TriviaQuestion


class TestTrivia:
    """Test Trivia game."""

    def test_initialization(self) -> None:
        """Test game initializes correctly."""
        game = TriviaGame(num_questions=5, enable_online=False)
        assert len(game.questions) == 5
        assert game.current_question_idx == 0
        assert game.score == 0

    def test_get_question(self) -> None:
        """Test getting current question."""
        game = TriviaGame(enable_online=False)
        q = game.get_current_question()
        assert q is not None
        assert "question" in q
        assert "options" in q
        assert "correct" in q

    def test_answer_question(self) -> None:
        """Test answering question."""
        game = TriviaGame(enable_online=False)
        game.state = game.state.IN_PROGRESS
        initial_idx = game.current_question_idx
        game.make_move(0)
        assert game.current_question_idx == initial_idx + 1

    def test_offline_cache(self, tmp_path: Path) -> None:
        """Ensure offline cache supplies questions when API disabled."""

        cache_path = tmp_path / "cache.json"
        cache = TriviaCache(cache_path)
        cache.add(
            [
                TriviaQuestion("Cached Q", ["A", "B", "C", "D"], 0),
                TriviaQuestion("Cached Q2", ["A", "B", "C", "D"], 1),
            ]
        )
        game = TriviaGame(num_questions=2, enable_online=False, cache_path=cache_path)
        assert {q.question for q in game.questions} <= {"Cached Q", "Cached Q2"}


class TestCrossword:
    """Test Crossword game."""

    def test_initialization(self) -> None:
        """Test game initializes correctly."""
        game = CrosswordGame()
        assert len(game.get_clues()) > 0
        assert len(game.solved) == 0

    def test_valid_answer(self) -> None:
        """Test submitting valid answer."""
        game = CrosswordGame()
        game.state = game.state.IN_PROGRESS
        # Get first clue
        clue_id = list(game.get_clues().keys())[0]
        answer = game.get_clues()[clue_id].answer
        result = game.make_move((clue_id, answer))
        assert result
        assert clue_id in game.solved

    def test_pack_roundtrip(self, tmp_path: Path) -> None:
        """Crossword packs can be exported and reloaded."""

        game = CrosswordGame()
        export_path = tmp_path / "pack.json"
        game.export_pack(export_path)
        loaded = CrosswordPackManager.load(export_path)
        assert loaded == game.get_clues()
        new_game = CrosswordGame(loaded)
        assert len(new_game.get_clues()) == len(game.get_clues())


class TestAnagrams:
    """Test Anagrams game."""

    def test_initialization(self) -> None:
        """Test game initializes correctly."""
        game = AnagramsGame(num_rounds=5)
        assert len(game.pairs) == 5
        assert game.current_round == 0
        assert game.score == 0

    def test_get_scrambled(self) -> None:
        """Test getting scrambled word."""
        game = AnagramsGame()
        scrambled = game.get_current_scrambled()
        assert len(scrambled) > 0

    def test_correct_answer(self) -> None:
        """Test submitting correct answer."""
        game = AnagramsGame()
        game.state = game.state.IN_PROGRESS
        _, answer = game.pairs[0]
        game.make_move(answer)
        assert game.score == 1


class TestWordBuilder:
    """Test WordBuilder game."""

    def test_initialization(self) -> None:
        """Test game initializes correctly."""
        game = WordBuilderGame()
        assert len(game.hand) == 7
        assert game.score == 0
        assert game.turns == 0

    def test_tile_values(self) -> None:
        """Test all tiles have values."""
        game = WordBuilderGame()
        for letter in game.TILE_VALUES:
            assert isinstance(game.TILE_VALUES[letter], int)
            assert game.TILE_VALUES[letter] > 0

    def test_valid_word(self) -> None:
        """Test playing valid word."""
        validator = DictionaryValidator(words=["AA"])
        config = {"A": 7}
        game = WordBuilderGame(dictionary=validator, tile_bag_config=config)
        game.state = game.state.IN_PROGRESS
        game.hand = list("AAAAAAA")
        initial_turns = game.turns
        assert game.make_move("AA")
        assert game.turns == initial_turns + 1

    def test_dictionary_validation(self, tmp_path: Path) -> None:
        """Words not in dictionary are rejected."""

        custom_dict = tmp_path / "dict.txt"
        custom_dict.write_text("HELLO\nWORLD\n", encoding="utf-8")
        validator = DictionaryValidator(dictionary_path=custom_dict)
        game = WordBuilderGame(dictionary=validator)
        assert not game.make_move("invalid")

    def test_tile_bag_configuration(self) -> None:
        """Tile bag respects configured counts."""

        config = {"A": 1, "B": 1, "C": 1}
        game = WordBuilderGame(tile_bag_config=config)
        expected_remaining = max(0, sum(config.values()) - len(game.hand))
        assert game.tile_bag.remaining() == expected_remaining

    def test_async_session_records_events(self) -> None:
        """Async session captures join and move events."""

        session = AsyncWordPlaySession("Test Session")

        async def run() -> int:
            await session.join("Alice")
            await session.record_move("Alice", "WORD", 12)
            return len(session.export_history())

        history_length = asyncio.run(run())
        assert history_length == 2
