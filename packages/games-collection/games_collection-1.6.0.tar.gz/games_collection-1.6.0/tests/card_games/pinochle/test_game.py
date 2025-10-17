"""Unit tests for the double-deck Pinochle engine."""

from __future__ import annotations

import pytest

from card_games.common.cards import Card, Suit
from card_games.pinochle.game import MeldPhase, PinochleGame, PinochlePlayer


@pytest.fixture
def game() -> PinochleGame:
    players = [
        PinochlePlayer(name="South"),
        PinochlePlayer(name="West"),
        PinochlePlayer(name="North"),
        PinochlePlayer(name="East"),
    ]
    game = PinochleGame(players)
    game.shuffle_and_deal()
    game.start_bidding()
    return game


def test_bidding_requires_increasing_values(game: PinochleGame) -> None:
    game.place_bid(game.min_bid)
    with pytest.raises(ValueError):
        game.place_bid(game.min_bid)
    with pytest.raises(ValueError):
        game.place_bid(game.min_bid - 10)
    game.place_bid(None)
    assert game.bidding_phase is not None
    assert len(game.bidding_phase.history) == 2


def test_meld_scoring_combines_run_and_pinochle() -> None:
    hand = [
        Card("A", Suit.HEARTS),
        Card("T", Suit.HEARTS),
        Card("K", Suit.HEARTS),
        Card("Q", Suit.HEARTS),
        Card("J", Suit.HEARTS),
        Card("Q", Suit.SPADES),
        Card("J", Suit.DIAMONDS),
        Card("9", Suit.HEARTS),
        Card("Q", Suit.SPADES),
        Card("J", Suit.DIAMONDS),
        Card("Q", Suit.SPADES),
        Card("J", Suit.DIAMONDS),
    ]
    phase = MeldPhase(Suit.HEARTS)
    score, breakdown = phase.score_hand(hand)
    assert score == 150 + 40 + 10 + 300  # run + pinochle + dix + double pinochle
    assert breakdown["run"] == 150
    assert breakdown["pinochle"] == 40
    assert breakdown["double_pinochle"] == 300
    assert breakdown["dix"] == 10


def test_trick_resolution_respects_trump(game: PinochleGame) -> None:
    for player in game.players:
        player.hand = []
    game.trump = Suit.SPADES
    game.current_player_index = 0
    game.players[0].hand.append(Card("T", Suit.HEARTS))
    game.players[1].hand.append(Card("A", Suit.HEARTS))
    game.players[2].hand.append(Card("Q", Suit.SPADES))
    game.players[3].hand.append(Card("K", Suit.HEARTS))

    game.play_card(game.players[0].hand[0])
    game.play_card(game.players[1].hand[0])
    game.play_card(game.players[2].hand[0])
    game.play_card(game.players[3].hand[0])

    winner = game.complete_trick()
    assert winner is game.players[2]
    assert game.players[2].trick_points == 28  # 10 + 11 + 3 + 4
