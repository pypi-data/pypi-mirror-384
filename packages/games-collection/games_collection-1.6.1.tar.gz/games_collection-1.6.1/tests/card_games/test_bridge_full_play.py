"""Integration tests covering the complete Bridge flow."""

from __future__ import annotations

from typing import Iterable

from card_games.bridge.game import AuctionState, Bid, BidSuit, BridgeGame, BridgePlayer, Call, CallType, Contract, Vulnerability
from card_games.common.cards import RANKS, Card, Suit


def _match_call(token: str, legal_calls: Iterable[Call]) -> Call:
    token = token.strip().upper()
    mapping = {
        "P": CallType.PASS,
        "PASS": CallType.PASS,
        "X": CallType.DOUBLE,
        "DOUBLE": CallType.DOUBLE,
        "XX": CallType.REDOUBLE,
        "REDOUBLE": CallType.REDOUBLE,
    }
    if token in mapping:
        target = mapping[token]
        for option in legal_calls:
            if option.call_type == target:
                return option
        raise AssertionError(f"Call {token!r} not legal")
    level = ""
    suit = ""
    for char in token:
        if char.isdigit():
            level += char
        else:
            suit += char
    if not level or not suit:
        raise AssertionError(f"Unrecognised token {token!r}")
    suit = suit.replace("NT", "N")
    suits = {
        "C": BidSuit.CLUBS,
        "D": BidSuit.DIAMONDS,
        "H": BidSuit.HEARTS,
        "S": BidSuit.SPADES,
        "N": BidSuit.NO_TRUMP,
    }
    bid_suit = suits.get(suit)
    if bid_suit is None:
        raise AssertionError(f"Unrecognised suit in {token!r}")
    level_value = int(level)
    for option in legal_calls:
        if option.call_type == CallType.BID and option.bid is not None:
            if option.bid.level == level_value and option.bid.suit == bid_suit:
                return option
    raise AssertionError(f"Bid {token!r} not legal")


def _ordered_players() -> list[BridgePlayer]:
    """Return players arranged clockwise starting North, East, South, West."""

    return [
        BridgePlayer("North", is_ai=True),
        BridgePlayer("East", is_ai=True),
        BridgePlayer("South", is_ai=True),
        BridgePlayer("West", is_ai=True),
    ]


def test_auction_records_forced_pass_and_declarer() -> None:
    players = _ordered_players()
    game = BridgeGame(players)

    sequence = iter(["1C", "PASS", "PASS", "X", "PASS", "PASS", "PASS"])

    def selector(player: BridgePlayer, legal: list[Call], history: list[Call], state: AuctionState) -> Call:
        token = next(sequence)
        return _match_call(token, legal)

    contract = game.conduct_bidding(call_selector=selector)
    assert contract is not None
    assert contract.bid.level == 1
    assert contract.bid.suit == BidSuit.CLUBS
    assert contract.doubled is True
    assert contract.redoubled is False
    assert contract.declarer.position == "N"
    assert game.declarer_index == 0

    history = game.bidding_history
    assert history[4].call_type == CallType.PASS and history[4].forced is True
    assert history[5].forced is False
    assert history[6].forced is True


def test_bidding_helper_applies_stayman_and_jacoby() -> None:
    # Stayman scenario
    players = _ordered_players()
    game = BridgeGame(players)
    north, east, south, west = game.players

    north.hand = [
        Card("A", Suit.SPADES),
        Card("J", Suit.SPADES),
        Card("9", Suit.SPADES),
        Card("5", Suit.SPADES),
        Card("K", Suit.HEARTS),
        Card("Q", Suit.HEARTS),
        Card("7", Suit.HEARTS),
        Card("K", Suit.DIAMONDS),
        Card("J", Suit.DIAMONDS),
        Card("9", Suit.DIAMONDS),
        Card("Q", Suit.CLUBS),
        Card("J", Suit.CLUBS),
        Card("8", Suit.CLUBS),
    ]
    south.hand = [
        Card("A", Suit.HEARTS),
        Card("T", Suit.HEARTS),
        Card("9", Suit.HEARTS),
        Card("8", Suit.HEARTS),
        Card("K", Suit.DIAMONDS),
        Card("J", Suit.DIAMONDS),
        Card("T", Suit.DIAMONDS),
        Card("9", Suit.DIAMONDS),
        Card("8", Suit.SPADES),
        Card("7", Suit.SPADES),
        Card("6", Suit.CLUBS),
        Card("5", Suit.CLUBS),
        Card("4", Suit.CLUBS),
    ]
    east.hand = [Card("2", Suit.CLUBS)] * 13
    west.hand = [Card("3", Suit.DIAMONDS)] * 13

    contract = game.conduct_bidding()
    assert contract is not None
    explanations = [call.explanation for call in game.bidding_history if call.explanation]
    assert "Stayman inquiry" in explanations

    # Jacoby transfer scenario
    game2 = BridgeGame(_ordered_players())
    north2, east2, south2, west2 = game2.players
    north2.hand = north.hand.copy()
    south2.hand = [
        Card("K", Suit.SPADES),
        Card("Q", Suit.SPADES),
        Card("J", Suit.SPADES),
        Card("T", Suit.SPADES),
        Card("9", Suit.SPADES),
        Card("A", Suit.HEARTS),
        Card("Q", Suit.HEARTS),
        Card("8", Suit.HEARTS),
        Card("7", Suit.CLUBS),
        Card("6", Suit.CLUBS),
        Card("5", Suit.DIAMONDS),
        Card("4", Suit.DIAMONDS),
        Card("3", Suit.DIAMONDS),
    ]
    east2.hand = [Card("2", Suit.CLUBS)] * 13
    west2.hand = [Card("3", Suit.DIAMONDS)] * 13

    contract2 = game2.conduct_bidding()
    assert contract2 is not None
    explanations2 = [call.explanation for call in game2.bidding_history if call.explanation]
    assert any(explanation in {"Jacoby transfer to hearts", "Jacoby transfer to spades"} for explanation in explanations2)


def test_bidding_helper_penalty_double() -> None:
    players = _ordered_players()
    game = BridgeGame(players)
    north, east, south, west = game.players

    north.hand = [Card("A", Suit.SPADES)] * 13
    east.hand = [
        Card("A", Suit.HEARTS),
        Card("K", Suit.HEARTS),
        Card("Q", Suit.HEARTS),
        Card("J", Suit.HEARTS),
        Card("T", Suit.HEARTS),
        Card("9", Suit.HEARTS),
        Card("8", Suit.HEARTS),
        Card("A", Suit.DIAMONDS),
        Card("K", Suit.DIAMONDS),
        Card("Q", Suit.DIAMONDS),
        Card("A", Suit.CLUBS),
        Card("K", Suit.CLUBS),
        Card("Q", Suit.CLUBS),
    ]
    south.hand = [Card("2", Suit.CLUBS)] * 13
    west.hand = [Card("3", Suit.DIAMONDS)] * 13

    captured: list[Call] = []
    sequence = iter(["4S", "AUTO", "PASS", "PASS", "PASS"])

    def selector(player: BridgePlayer, legal: list[Call], history: list[Call], state: AuctionState) -> Call:
        token = next(sequence)
        if token == "AUTO":
            call = game.bidding_helper.choose_call(player, legal, history.copy(), state)
            captured.append(call)
            return call
        return _match_call(token, legal)

    contract = game.conduct_bidding(call_selector=selector)
    assert contract is not None
    assert captured, "Expected the helper to produce a call"
    penalty_call = captured[0]
    assert penalty_call.call_type == CallType.DOUBLE
    assert penalty_call.explanation == "Penalty double"


def test_scoring_tables_for_doubles_and_redoubles() -> None:
    players = _ordered_players()
    game = BridgeGame(players, vulnerability=Vulnerability.NONE)
    north, east, south, west = game.players
    north.tricks_won = 7
    south.tricks_won = 0
    east.tricks_won = 3
    west.tricks_won = 3
    game.contract = Contract(Bid(4, BidSuit.SPADES), north, doubled=True)
    scores = game.calculate_score()
    assert scores["east_west"] == 500
    assert scores["north_south"] == 0

    game2 = BridgeGame(_ordered_players(), vulnerability=Vulnerability.NORTH_SOUTH)
    north2, east2, south2, west2 = game2.players
    north2.tricks_won = 6
    south2.tricks_won = 4
    east2.tricks_won = 2
    west2.tricks_won = 1
    game2.contract = Contract(Bid(3, BidSuit.NO_TRUMP), north2, doubled=False, redoubled=True)
    scores2 = game2.calculate_score()
    assert scores2["north_south"] == 1400
    assert scores2["east_west"] == 0


def test_full_trick_play_completes_thirteen_tricks() -> None:
    players = _ordered_players()
    game = BridgeGame(players, vulnerability=Vulnerability.NORTH_SOUTH)
    north, east, south, west = game.players

    north.hand = [Card(rank, Suit.SPADES) for rank in RANKS]
    east.hand = [Card(rank, Suit.DIAMONDS) for rank in RANKS]
    south.hand = [Card(rank, Suit.HEARTS) for rank in RANKS]
    west.hand = [Card(rank, Suit.CLUBS) for rank in RANKS]
    for player in players:
        player.tricks_won = 0

    game.contract = Contract(Bid(7, BidSuit.SPADES), north)
    game.trump_suit = Suit.SPADES
    game.declarer_index = 0

    current = game.starting_player_index()
    for _ in range(13):
        for offset in range(4):
            player = game.players[(current + offset) % 4]
            valid = game.get_valid_plays(player)
            card = valid[0]
            game.play_card(player, card)
        winner = game.complete_trick()
        current = game.players.index(winner)

    assert game.hand_complete is True
    assert len(game.trick_history) == 13
    scores = game.calculate_score()
    assert scores["north_south"] == 2210
    assert scores["east_west"] == 0
    assert game.tricks_remaining() == 0
