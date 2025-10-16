"""Tests for word games."""

from __future__ import annotations

from word_games import AnagramsGame, CrosswordGame, TriviaGame, WordBuilderGame


class TestTrivia:
    """Test Trivia game."""

    def test_initialization(self) -> None:
        """Test game initializes correctly."""
        game = TriviaGame(num_questions=5)
        assert len(game.questions) == 5
        assert game.current_question_idx == 0
        assert game.score == 0

    def test_get_question(self) -> None:
        """Test getting current question."""
        game = TriviaGame()
        q = game.get_current_question()
        assert q is not None
        assert "question" in q
        assert "options" in q
        assert "correct" in q

    def test_answer_question(self) -> None:
        """Test answering question."""
        game = TriviaGame()
        game.state = game.state.IN_PROGRESS
        initial_idx = game.current_question_idx
        game.make_move(0)
        assert game.current_question_idx == initial_idx + 1


class TestCrossword:
    """Test Crossword game."""

    def test_initialization(self) -> None:
        """Test game initializes correctly."""
        game = CrosswordGame()
        assert len(game.PUZZLE) > 0
        assert len(game.solved) == 0

    def test_valid_answer(self) -> None:
        """Test submitting valid answer."""
        game = CrosswordGame()
        game.state = game.state.IN_PROGRESS
        # Get first clue
        clue_id = list(game.PUZZLE.keys())[0]
        _, _, _, answer, _ = game.PUZZLE[clue_id]
        result = game.make_move((clue_id, answer))
        assert result
        assert clue_id in game.solved


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
        game = WordBuilderGame()
        game.state = game.state.IN_PROGRESS
        # Create simple word from hand
        if len(game.hand) >= 2:
            word = game.hand[0] + game.hand[1]
            initial_turns = game.turns
            game.make_move(word)
            assert game.turns == initial_turns + 1
