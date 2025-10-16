"""Card game fixtures for testing."""

import pytest


@pytest.fixture
def standard_deck_cards():
    """Provide standard 52-card deck configuration."""
    suits = ["Hearts", "Diamonds", "Clubs", "Spades"]
    ranks = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]
    return [(rank, suit) for suit in suits for rank in ranks]


@pytest.fixture
def poker_hands():
    """Provide common poker hand scenarios for testing."""
    return {
        "royal_flush": [("A", "Hearts"), ("K", "Hearts"), ("Q", "Hearts"), ("J", "Hearts"), ("10", "Hearts")],
        "straight_flush": [("9", "Clubs"), ("8", "Clubs"), ("7", "Clubs"), ("6", "Clubs"), ("5", "Clubs")],
        "four_of_kind": [("A", "Hearts"), ("A", "Diamonds"), ("A", "Clubs"), ("A", "Spades"), ("K", "Hearts")],
        "full_house": [("K", "Hearts"), ("K", "Diamonds"), ("K", "Clubs"), ("Q", "Hearts"), ("Q", "Diamonds")],
        "flush": [("2", "Hearts"), ("5", "Hearts"), ("7", "Hearts"), ("9", "Hearts"), ("K", "Hearts")],
        "straight": [("9", "Hearts"), ("8", "Clubs"), ("7", "Diamonds"), ("6", "Spades"), ("5", "Hearts")],
        "three_of_kind": [("7", "Hearts"), ("7", "Diamonds"), ("7", "Clubs"), ("K", "Hearts"), ("2", "Diamonds")],
        "two_pair": [("J", "Hearts"), ("J", "Diamonds"), ("3", "Clubs"), ("3", "Spades"), ("A", "Hearts")],
        "one_pair": [("10", "Hearts"), ("10", "Diamonds"), ("5", "Clubs"), ("7", "Spades"), ("K", "Hearts")],
        "high_card": [("A", "Hearts"), ("10", "Diamonds"), ("8", "Clubs"), ("5", "Spades"), ("3", "Hearts")],
    }


@pytest.fixture
def blackjack_scenarios():
    """Provide common Blackjack scenarios for testing."""
    return {
        "blackjack": [("A", "Hearts"), ("K", "Spades")],
        "bust": [("10", "Hearts"), ("K", "Diamonds"), ("5", "Clubs")],
        "soft_17": [("A", "Hearts"), ("6", "Diamonds")],
        "hard_17": [("10", "Hearts"), ("7", "Diamonds")],
        "pair_aces": [("A", "Hearts"), ("A", "Diamonds")],
        "pair_eights": [("8", "Hearts"), ("8", "Diamonds")],
    }


@pytest.fixture
def uno_cards():
    """Provide UNO card configurations for testing."""
    colors = ["Red", "Yellow", "Green", "Blue"]
    numbers = list(range(10)) + list(range(1, 10))  # 0 appears once, 1-9 twice
    action_cards = ["Skip", "Reverse", "Draw Two"]
    wild_cards = ["Wild", "Wild Draw Four"]

    return {
        "colors": colors,
        "numbers": numbers,
        "actions": action_cards,
        "wilds": wild_cards,
    }
