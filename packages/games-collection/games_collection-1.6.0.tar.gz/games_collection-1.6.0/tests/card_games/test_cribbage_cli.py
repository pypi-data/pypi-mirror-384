"""Regression tests for the Cribbage CLI helpers and AI heuristics."""

from __future__ import annotations

from card_games.common.cards import Card, Deck, Suit
from card_games.cribbage.ai import choose_pegging_card, select_discards
from card_games.cribbage.game import CribbageGame, GamePhase


def test_select_discards_prefers_strong_hand() -> None:
    """The discard heuristic should preserve strong run combinations."""

    hand = [
        Card("5", Suit.HEARTS),
        Card("5", Suit.DIAMONDS),
        Card("6", Suit.SPADES),
        Card("7", Suit.CLUBS),
        Card("8", Suit.HEARTS),
        Card("9", Suit.DIAMONDS),
    ]
    deck = Deck()
    for card in hand:
        deck.cards.remove(card)

    discards = select_discards(hand, is_dealer=False, deck_cards=deck.cards)
    assert {card.rank for card in discards} == {"8", "9"}


def test_pegging_ai_prefers_scoring_play() -> None:
    """The pegging AI should choose a card that immediately scores points."""

    game = CribbageGame()
    game.phase = GamePhase.PLAY
    game.current_player = 2
    game.play_sequence = [
        (1, Card("5", Suit.HEARTS)),
        (2, Card("5", Suit.DIAMONDS)),
    ]
    game.play_count = 10
    game.player2_hand = [Card("5", Suit.CLUBS), Card("K", Suit.SPADES)]

    choice = choose_pegging_card(game, 2)
    assert choice == Card("5", Suit.CLUBS)


def test_score_hand_static_counts_29() -> None:
    """Scoring helper recognises the 29-point hand."""

    hand = [
        Card("5", Suit.DIAMONDS),
        Card("5", Suit.CLUBS),
        Card("5", Suit.SPADES),
        Card("J", Suit.HEARTS),
    ]
    starter = Card("5", Suit.HEARTS)
    assert CribbageGame.score_hand_static(hand, starter, is_crib=False) == 29


def test_play_card_detects_win() -> None:
    """Reaching 121 points through pegging should end the game."""

    game = CribbageGame()
    game.phase = GamePhase.PLAY
    game.current_player = 1
    game.player1_score = 119
    game.player2_score = 80
    game.play_sequence = [(2, Card("7", Suit.CLUBS))]
    game.play_count = 7
    winning_card = Card("8", Suit.HEARTS)
    game.player1_hand = [winning_card]

    result = game.play_card(1, winning_card)
    assert result["game_over"] is True
    assert game.winner == 1
    assert game.player1_score >= 121
