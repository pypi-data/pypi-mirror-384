"""Scenario-driven tests for the Rummy 500 engine."""

from __future__ import annotations

from card_games.common.cards import Card, Suit
from card_games.rummy500.game import GamePhase, Rummy500Game


def c(rank: str, suit: Suit) -> Card:
    """Convenience helper for creating cards."""

    return Card(rank, suit)


def test_discard_pickup_creates_meld() -> None:
    """Picking multiple cards from the discard pile should enable new melds."""

    game = Rummy500Game(num_players=2)
    game.current_player = 0
    game.phase = GamePhase.DRAW
    game.deck.cards = []
    game.discard_pile = [c("4", Suit.HEARTS), c("5", Suit.HEARTS)]
    game.hands[0] = [c("6", Suit.HEARTS), c("7", Suit.HEARTS), c("9", Suit.CLUBS), c("K", Suit.SPADES)]

    assert game.draw_card(from_discard=True, take_count=2)

    expected_run = {c("4", Suit.HEARTS), c("5", Suit.HEARTS), c("6", Suit.HEARTS), c("7", Suit.HEARTS)}
    meld_options = [set(meld) for meld in game.available_melds(0)]
    assert expected_run in meld_options

    assert game.lay_meld(0, list(expected_run))
    assert len(game.melds) == 1
    assert set(game.melds[0].cards) == expected_run


def test_multi_meld_turn_advances_round() -> None:
    """A player can lay multiple melds then discard to end their turn."""

    game = Rummy500Game(num_players=2)
    game.current_player = 0
    game.phase = GamePhase.MELD
    game.hands[0] = [
        c("3", Suit.HEARTS),
        c("4", Suit.HEARTS),
        c("5", Suit.HEARTS),
        c("9", Suit.CLUBS),
        c("9", Suit.DIAMONDS),
        c("9", Suit.SPADES),
        c("K", Suit.CLUBS),
        c("A", Suit.CLUBS),
    ]

    assert game.lay_meld(0, [c("3", Suit.HEARTS), c("4", Suit.HEARTS), c("5", Suit.HEARTS)])
    assert game.lay_meld(0, [c("9", Suit.CLUBS), c("9", Suit.DIAMONDS), c("9", Suit.SPADES)])
    assert len(game.melds) == 2
    assert len(game.hands[0]) == 2

    assert game.discard(0, c("K", Suit.CLUBS))
    assert game.phase == GamePhase.DRAW
    assert game.current_player == 1


def test_layoff_scoring_tracks_contributors() -> None:
    """Players earn points for cards they lay off onto existing melds."""

    game = Rummy500Game(num_players=2)
    game.current_player = 0
    game.phase = GamePhase.MELD
    game.hands[0] = [c("7", Suit.SPADES), c("7", Suit.HEARTS), c("7", Suit.DIAMONDS)]
    game.hands[1] = [c("7", Suit.CLUBS)]

    assert game.lay_meld(0, [c("7", Suit.SPADES), c("7", Suit.HEARTS), c("7", Suit.DIAMONDS)])
    assert len(game.melds) == 1
    assert set(game.melds[0].cards) == {c("7", Suit.SPADES), c("7", Suit.HEARTS), c("7", Suit.DIAMONDS)}
    game.current_player = 1
    game.phase = GamePhase.MELD

    assert game.lay_off(1, 0, [c("7", Suit.CLUBS)])
    assert set(game.melds[0].cards) == {
        c("7", Suit.SPADES),
        c("7", Suit.HEARTS),
        c("7", Suit.DIAMONDS),
        c("7", Suit.CLUBS),
    }
    assert game.melds[0].contributions[1] == [c("7", Suit.CLUBS)]

    game._score_round()
    assert game.scores == [21, 7]


def test_negative_deadwood_scoring_applied() -> None:
    """Players with deadwood receive negative points when an opponent goes out."""

    game = Rummy500Game(num_players=2)
    game.current_player = 0
    game.phase = GamePhase.MELD
    game.hands[0] = [c("4", Suit.CLUBS)]
    game.hands[1] = [c("K", Suit.SPADES), c("Q", Suit.HEARTS)]

    assert game.discard(0, c("4", Suit.CLUBS))
    assert game.scores == [0, -20]


def test_empty_stock_forces_round_end() -> None:
    """An empty stock with no discard options should end the round and score hands."""

    game = Rummy500Game(num_players=2)
    game.phase = GamePhase.DRAW
    game.deck.cards = []
    game.discard_pile = []
    game.hands[0] = [c("A", Suit.SPADES)]
    game.hands[1] = [c("5", Suit.HEARTS)]

    game.end_round_due_to_empty_stock()

    assert game.scores == [-15, -5]
    assert game.phase == GamePhase.DRAW
    assert not game.melds
