"""Tests for the hangman wordlist."""

import json
from pathlib import Path


def test_wordlist_structure():
    """Test that the wordlist has the correct structure."""
    wordlist_path = Path(__file__).parent.parent / "paper_games" / "hangman" / "wordlist.json"

    with open(wordlist_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Check that all required keys exist
    assert "version" in data
    assert "easy" in data
    assert "medium" in data
    assert "hard" in data

    # Check data types
    assert isinstance(data["easy"], list)
    assert isinstance(data["medium"], list)
    assert isinstance(data["hard"], list)


def test_wordlist_counts():
    """Test that each category has exactly 360 unique words."""
    wordlist_path = Path(__file__).parent.parent / "paper_games" / "hangman" / "wordlist.json"

    with open(wordlist_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Check word counts
    assert len(data["easy"]) == 360, f"Expected 360 easy words, got {len(data['easy'])}"
    assert len(data["medium"]) == 360, f"Expected 360 medium words, got {len(data['medium'])}"
    assert len(data["hard"]) == 360, f"Expected 360 hard words, got {len(data['hard'])}"

    # Check for uniqueness within categories
    assert len(set(data["easy"])) == 360, "Easy category has duplicate words"
    assert len(set(data["medium"])) == 360, "Medium category has duplicate words"
    assert len(set(data["hard"])) == 360, "Hard category has duplicate words"


def test_wordlist_no_cross_category_duplicates():
    """Test that words are unique across all categories."""
    wordlist_path = Path(__file__).parent.parent / "paper_games" / "hangman" / "wordlist.json"

    with open(wordlist_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    all_words = data["easy"] + data["medium"] + data["hard"]
    unique_words = set(all_words)

    assert len(all_words) == 1080, f"Expected 1080 total words, got {len(all_words)}"
    assert len(unique_words) == 1080, f"Found {len(all_words) - len(unique_words)} duplicate words across categories"


def test_wordlist_word_lengths():
    """Test that words in each category have appropriate lengths."""
    wordlist_path = Path(__file__).parent.parent / "paper_games" / "hangman" / "wordlist.json"

    with open(wordlist_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Hard: 3-letter words (shortest, easiest to guess)
    hard_lengths = [len(w) for w in data["hard"]]
    assert all(length == 3 for length in hard_lengths), "All hard words should be 3 letters"

    # Medium: 4-5 letter words
    medium_lengths = [len(w) for w in data["medium"]]
    assert all(4 <= length <= 5 for length in medium_lengths), "All medium words should be 4-5 letters"

    # Easy: 6+ letter words (longest, hardest to guess)
    easy_lengths = [len(w) for w in data["easy"]]
    assert all(length >= 6 for length in easy_lengths), "All easy words should be 6+ letters"


def test_wordlist_all_lowercase():
    """Test that all words are lowercase."""
    wordlist_path = Path(__file__).parent.parent / "paper_games" / "hangman" / "wordlist.json"

    with open(wordlist_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    for category in ["easy", "medium", "hard"]:
        for word in data[category]:
            assert word.islower(), f"Word '{word}' in {category} category is not lowercase"


def test_wordlist_all_alphabetic():
    """Test that all words contain only alphabetic characters."""
    wordlist_path = Path(__file__).parent.parent / "paper_games" / "hangman" / "wordlist.json"

    with open(wordlist_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    for category in ["easy", "medium", "hard"]:
        for word in data[category]:
            assert word.isalpha(), f"Word '{word}' in {category} category contains non-alphabetic characters"
