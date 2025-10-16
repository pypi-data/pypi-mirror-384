from __future__ import annotations

from card_games.canasta.game import (
    CanastaGame,
    CanastaPlayer,
    DrawSource,
    JokerCard,
    is_wild,
    minimum_meld_points,
    validate_meld,
)
from card_games.common.cards import Card, Suit


def test_validate_meld_accepts_mixed_canasta() -> None:
    cards = [
        Card("K", Suit.CLUBS),
        Card("K", Suit.DIAMONDS),
        Card("K", Suit.HEARTS),
        Card("K", Suit.SPADES),
        Card("K", Suit.CLUBS),
        Card("2", Suit.HEARTS),
        JokerCard(),
    ]
    result = validate_meld(cards)
    assert result.is_valid
    assert result.meld is not None
    assert result.meld.is_canasta
    assert not result.meld.is_natural


def test_validate_meld_rejects_excess_wilds() -> None:
    cards = [
        Card("Q", Suit.CLUBS),
        Card("Q", Suit.DIAMONDS),
        JokerCard(),
        JokerCard(),
        JokerCard(),
    ]
    result = validate_meld(cards)
    assert not result.is_valid
    assert "Wild cards" in result.message


def test_minimum_meld_points_thresholds() -> None:
    assert minimum_meld_points(0) == 50
    assert minimum_meld_points(2400) == 90
    assert minimum_meld_points(3200) == 120
    assert minimum_meld_points(6000) == 150


def test_round_flow_scoring_and_freeze_behavior() -> None:
    players = [
        CanastaPlayer("North", team_index=0, is_ai=False),
        CanastaPlayer("East", team_index=1, is_ai=True),
        CanastaPlayer("South", team_index=0, is_ai=True),
        CanastaPlayer("West", team_index=1, is_ai=True),
    ]
    game = CanastaGame(players)

    # Configure deterministic hands for the round.
    north = game.players[0]
    south = game.players[2]
    east = game.players[1]
    west = game.players[3]

    north.hand = [
        Card("K", Suit.CLUBS),
        Card("K", Suit.DIAMONDS),
        Card("K", Suit.HEARTS),
        Card("K", Suit.SPADES),
        Card("K", Suit.CLUBS),
        Card("2", Suit.HEARTS),
        JokerCard(),
        JokerCard(),
    ]
    south.hand = [
        Card("K", Suit.DIAMONDS),
        Card("K", Suit.HEARTS),
    ]
    east.hand = [Card("9", Suit.CLUBS), Card("4", Suit.HEARTS)]
    west.hand = [Card("A", Suit.SPADES)]

    # North lays a canasta immediately meeting the meld requirement.
    meld_cards = north.hand[:7]
    meld = game.add_meld(north, meld_cards)
    assert meld.is_canasta
    assert game.teams[0].requirement_met
    assert len(north.hand) == 1

    # South contributes remaining natural kings to the meld.
    south_cards = list(south.hand)
    game.add_meld(south, south_cards, meld_index=0)
    assert not south.hand

    # Discarding a wild card freezes the pile.
    game.discard(north, north.hand[0])
    assert game.discard_frozen

    # East cannot draw the frozen discard with insufficient natural matches.
    assert not game.can_take_discard(east)
    game.draw(east, DrawSource.STOCK)

    # West discards a natural card leaving deadwood for scoring.
    west_card = west.hand[0]
    game.discard(west, west_card)
    assert not is_wild(west_card)

    # Empty the human partner hands to prepare for going out.
    north.hand.clear()
    game.discard_pile.clear()

    meld_points_before = game.calculate_team_meld_points(0)
    opponents_deadwood = game.calculate_team_deadwood(1)

    breakdown = game.go_out(north)
    assert game.round_over
    assert breakdown[0] == meld_points_before + 100
    assert breakdown[1] == -opponents_deadwood
    assert game.teams[0].score == breakdown[0]
    assert game.teams[1].score == breakdown[1]
