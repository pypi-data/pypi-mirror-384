"""Tests for new Hangman features: themes, difficulty, hints, multiplayer, and art styles."""

import json
from pathlib import Path

import pytest

from paper_games.hangman import HANGMAN_ART_STYLES, HangmanGame, load_default_words, load_themed_words, load_words_by_difficulty


def test_load_words_by_difficulty_easy():
    """Test loading easy difficulty words."""
    words = load_words_by_difficulty("easy")
    assert len(words) == 360
    # Easy words are 6+ letters
    assert all(len(w) >= 6 for w in words)


def test_load_words_by_difficulty_medium():
    """Test loading medium difficulty words."""
    words = load_words_by_difficulty("medium")
    assert len(words) == 360
    # Medium words are 4-5 letters
    assert all(4 <= len(w) <= 5 for w in words)


def test_load_words_by_difficulty_hard():
    """Test loading hard difficulty words."""
    words = load_words_by_difficulty("hard")
    assert len(words) == 360
    # Hard words are 3 letters
    assert all(len(w) == 3 for w in words)


def test_load_words_by_difficulty_all():
    """Test loading all difficulty words."""
    words = load_words_by_difficulty("all")
    assert len(words) == 1080
    # Should match load_default_words
    assert sorted(words) == sorted(load_default_words())


def test_load_words_by_difficulty_invalid():
    """Test that invalid difficulty raises an error."""
    with pytest.raises(ValueError, match="Invalid difficulty"):
        load_words_by_difficulty("invalid")


def test_load_themed_words_all():
    """Test loading all themed word categories."""
    themes = load_themed_words()
    assert isinstance(themes, dict)

    # Check that we have the expected themes
    expected_themes = {"movies", "countries", "sports", "animals", "food"}
    assert set(themes.keys()) == expected_themes

    # Check that each theme has words
    for theme, words in themes.items():
        assert isinstance(words, list)
        assert len(words) > 0
        assert all(isinstance(w, str) for w in words)
        assert all(w.islower() for w in words)
        assert all(w.isalpha() for w in words)


def test_load_themed_words_specific():
    """Test loading a specific theme."""
    movies = load_themed_words("movies")
    assert isinstance(movies, list)
    assert len(movies) > 0
    assert all(isinstance(w, str) for w in movies)


def test_load_themed_words_invalid():
    """Test that invalid theme raises an error."""
    with pytest.raises(ValueError, match="Unknown theme"):
        load_themed_words("invalid_theme")


def test_themed_words_file_structure():
    """Test that themed_words.json has the correct structure."""
    themed_path = Path(__file__).parent.parent / "paper_games" / "hangman" / "themed_words.json"

    if not themed_path.exists():
        pytest.skip("themed_words.json not found")

    with open(themed_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert isinstance(data, dict)
    for theme, words in data.items():
        assert isinstance(theme, str)
        assert isinstance(words, list)
        # Each word should be lowercase and alphabetic
        for word in words:
            assert word.islower()
            assert word.isalpha()


def test_hangman_game_with_theme():
    """Test creating a game with a theme."""
    game = HangmanGame(["test"], theme="movies")
    assert game.theme == "movies"

    # Check that theme appears in status lines
    status = game.status_lines()
    theme_line = [line for line in status if "Theme:" in line]
    assert len(theme_line) == 1
    assert "movies" in theme_line[0]


def test_hangman_game_without_theme():
    """Test creating a game without a theme."""
    game = HangmanGame(["test"])
    assert game.theme is None

    # Check that theme doesn't appear in status lines
    status = game.status_lines()
    theme_line = [line for line in status if "Theme:" in line]
    assert len(theme_line) == 0


def test_hangman_game_hints_enabled():
    """Test hint system when enabled."""
    game = HangmanGame(["test"], hints_enabled=True)
    assert game.hints_enabled is True
    assert game.hints_used == 0
    assert game.max_hints == 3

    # Get a hint
    hint = game.get_hint()
    assert hint in "test"
    assert hint in game.guessed_letters
    assert game.hints_used == 1

    # Check hints appear in status
    status = game.status_lines()
    hints_line = [line for line in status if "Hints remaining:" in line]
    assert len(hints_line) == 1
    assert "2" in hints_line[0]


def test_hangman_game_hints_disabled():
    """Test hint system when disabled."""
    game = HangmanGame(["test"], hints_enabled=False)
    assert game.hints_enabled is False

    # Try to get a hint - should return None
    hint = game.get_hint()
    assert hint is None
    assert game.hints_used == 0


def test_hangman_game_hints_exhausted():
    """Test that hints are limited."""
    game = HangmanGame(["testing"], hints_enabled=True, max_hints=2)

    # Use all hints
    hint1 = game.get_hint()
    assert hint1 is not None
    assert game.hints_used == 1

    hint2 = game.get_hint()
    assert hint2 is not None
    assert game.hints_used == 2

    # No more hints available
    hint3 = game.get_hint()
    assert hint3 is None
    assert game.hints_used == 2


def test_hangman_game_hint_reveals_unrevealed_letter():
    """Test that hints only reveal unguessed letters."""
    game = HangmanGame(["test"], hints_enabled=True)

    # Guess a letter
    game.guess("t")
    assert "t" in game.guessed_letters

    # Get a hint - should not be 't'
    hint = game.get_hint()
    assert hint in "es"
    assert hint != "t"


def test_hangman_game_hint_when_all_revealed():
    """Test hint behavior when all letters are revealed."""
    game = HangmanGame(["cat"], hints_enabled=True)

    # Reveal all letters through guessing
    game.guess("c")
    game.guess("a")
    game.guess("t")

    # No hint should be available
    hint = game.get_hint()
    assert hint is None


def test_art_styles_available():
    """Test that art styles are properly defined."""
    assert "classic" in HANGMAN_ART_STYLES
    assert "simple" in HANGMAN_ART_STYLES
    assert "minimal" in HANGMAN_ART_STYLES

    # Each style should have 7 stages
    for style_name, stages in HANGMAN_ART_STYLES.items():
        assert len(stages) == 7, f"{style_name} should have 7 stages"
        assert all(isinstance(stage, str) for stage in stages)


def test_hangman_game_with_art_style():
    """Test creating a game with different art styles."""
    game_classic = HangmanGame(["test"], art_style="classic")
    game_simple = HangmanGame(["test"], art_style="simple")
    game_minimal = HangmanGame(["test"], art_style="minimal")

    # Each should produce different ASCII art
    assert game_classic.stage != game_simple.stage
    assert game_classic.stage != game_minimal.stage
    assert game_simple.stage != game_minimal.stage


def test_hangman_game_art_style_progression():
    """Test that art style changes with wrong guesses."""
    game = HangmanGame(["cat"], art_style="simple", max_attempts=6)

    initial_stage = game.stage

    # Make a wrong guess
    game.guess("x")
    stage_after_one = game.stage

    # Stage should change
    assert initial_stage != stage_after_one

    # Make more wrong guesses
    game.guess("y")
    game.guess("z")
    stage_after_three = game.stage

    # Stage should continue to change
    assert stage_after_one != stage_after_three


def test_hangman_game_default_art_style():
    """Test that classic is the default art style."""
    game = HangmanGame(["test"])
    assert game.art_style == "classic"


def test_backwards_compatibility():
    """Test that the game still works with the old API."""
    words = ["test", "example"]
    game = HangmanGame(words, max_attempts=6)

    # Should work as before
    assert not game.is_won()
    assert not game.is_lost()

    # Guess a letter that's definitely in one of the words
    result = game.guess("t")
    # Check if 't' is in the secret word
    if "t" in game.secret_word:
        assert result is True
        assert "t" in game.guessed_letters
    else:
        assert result is False
        assert "t" in game.wrong_guesses

    status = game.status_lines()
    assert len(status) > 0


def test_themed_words_unique_within_theme():
    """Test that words within each theme are unique."""
    themes = load_themed_words()

    for theme_name, words in themes.items():
        assert len(words) == len(set(words)), f"Theme '{theme_name}' has duplicate words"


def test_themed_words_no_cross_theme_check():
    """Test words across themes (duplicates allowed between themes)."""
    themes = load_themed_words()

    all_themed_words = []
    for words in themes.values():
        all_themed_words.extend(words)

    # Just ensure we have words from all themes
    assert len(all_themed_words) > 0
