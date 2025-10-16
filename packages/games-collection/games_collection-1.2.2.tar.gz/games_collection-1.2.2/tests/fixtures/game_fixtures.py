"""Common game fixtures for testing."""

import random

import pytest


@pytest.fixture
def nim_game_scenarios():
    """Provide common Nim game scenarios for testing."""
    return {
        "simple_win": [3, 4, 5],  # Simple winning position
        "losing_position": [1, 1],  # Losing position
        "single_heap": [7],  # Single heap
        "many_heaps": [1, 2, 3, 4, 5],  # Multiple heaps
        "large_heaps": [15, 20, 25],  # Large values
        "all_ones": [1, 1, 1, 1],  # All smallest values
    }


@pytest.fixture
def tic_tac_toe_boards():
    """Provide common Tic-Tac-Toe board states for testing."""
    return {
        "empty": [[None] * 3 for _ in range(3)],
        "x_wins_row": [["X", "X", "X"], [None, None, None], [None, None, None]],
        "o_wins_col": [["O", None, None], ["O", None, None], ["O", None, None]],
        "x_wins_diag": [["X", None, None], [None, "X", None], [None, None, "X"]],
        "tie": [["X", "O", "X"], ["O", "X", "O"], ["O", "X", "O"]],
        "in_progress": [["X", None, "O"], [None, "X", None], [None, None, None]],
    }


@pytest.fixture
def battleship_fleet_configs():
    """Provide common Battleship fleet configurations for testing."""
    return {
        "standard": [(5, 1), (4, 1), (3, 1), (3, 1), (2, 1)],
        "small": [(4, 1), (3, 1), (2, 1)],
        "single": [(3, 1)],
    }


@pytest.fixture
def dots_and_boxes_sizes():
    """Provide common Dots and Boxes board sizes for testing."""
    return [3, 4, 5, 6]


@pytest.fixture
def hangman_words():
    """Provide common words for Hangman testing."""
    return ["python", "testing", "fixture", "coverage", "pytest", "games"]


@pytest.fixture
def unscramble_words():
    """Provide common words for Unscramble testing."""
    return {
        "easy": ["cat", "dog", "hat", "run", "sun"],
        "medium": ["python", "coding", "games", "tests", "debug"],
        "hard": ["algorithm", "implementation", "optimization", "architecture"],
    }


@pytest.fixture
def seeded_random():
    """Provide a seeded random generator for reproducible tests."""
    return random.Random(12345)
