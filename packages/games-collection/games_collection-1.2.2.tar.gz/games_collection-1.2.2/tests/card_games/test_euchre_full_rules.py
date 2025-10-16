"""Integration tests covering the extended Euchre rules."""

from __future__ import annotations

from card_games.common.cards import Card, Suit
from card_games.euchre.ai import BasicEuchreAI
from card_games.euchre.game import EuchreGame, GamePhase


def test_ordering_up_requires_dealer_discard() -> None:
    """Ordering up the turned card should force the dealer to discard before play."""

    game = EuchreGame()
    game.dealer = 1
    game.hands = [
        [Card("9", Suit.CLUBS)] * 5,
        [Card("A", Suit.SPADES), Card("K", Suit.SPADES), Card("Q", Suit.SPADES), Card("J", Suit.HEARTS), Card("T", Suit.SPADES)],
        [Card("9", Suit.HEARTS)] * 5,
        [Card("9", Suit.DIAMONDS)] * 5,
    ]
    game.up_card = Card("K", Suit.HEARTS)
    game.kitty = [game.up_card, Card("9", Suit.SPADES), Card("T", Suit.SPADES), Card("Q", Suit.CLUBS)]
    game.phase = GamePhase.BIDDING

    assert game.select_trump(Suit.HEARTS, player=2, require_dealer_pickup=True)
    assert game.phase == GamePhase.DEALER_DISCARD
    discard_candidate = game.hands[game.dealer][0]
    assert game.dealer_pickup(discard_candidate)
    assert game.phase == GamePhase.PLAY
    assert game.current_player == (game.dealer + 1) % 4
    assert len(game.hands[game.dealer]) == 5
    assert game.kitty[0] == discard_candidate


def test_follow_suit_with_left_bower_enforced() -> None:
    """Players must follow suit accounting for the left bower."""

    game = EuchreGame()
    game.dealer = 3
    game.trump = Suit.HEARTS
    game.phase = GamePhase.PLAY
    game.current_trick = []
    game.current_player = 0
    game.hands = [
        [Card("J", Suit.HEARTS), Card("A", Suit.SPADES)],
        [Card("J", Suit.DIAMONDS), Card("A", Suit.CLUBS)],
        [Card("9", Suit.SPADES), Card("T", Suit.SPADES)],
        [Card("9", Suit.CLUBS), Card("T", Suit.CLUBS)],
    ]

    assert game.play_card(0, Card("J", Suit.HEARTS))["success"]
    legal = game.get_legal_cards(1)
    assert legal == [Card("J", Suit.DIAMONDS)]
    assert not game.play_card(1, Card("A", Suit.CLUBS))["success"]
    assert game.play_card(1, Card("J", Suit.DIAMONDS))["success"]


def test_maker_goes_alone_scores_four_points() -> None:
    """A maker sweeping all tricks alone should earn four points."""

    game = EuchreGame()
    game.dealer = 3
    game.trump = Suit.HEARTS
    game.maker = 1
    game.going_alone = True
    game.alone_player = 0
    game.sitting_out_players = {2}
    game.phase = GamePhase.PLAY
    game.current_player = 0
    game.current_trick = []
    game.tricks_won = [0, 0]
    game.hands = [
        [Card("J", Suit.HEARTS), Card("J", Suit.DIAMONDS), Card("A", Suit.HEARTS), Card("K", Suit.HEARTS), Card("Q", Suit.HEARTS)],
        [Card("9", Suit.CLUBS), Card("9", Suit.SPADES), Card("T", Suit.CLUBS), Card("Q", Suit.CLUBS), Card("K", Suit.CLUBS)],
        [],
        [Card("9", Suit.HEARTS), Card("T", Suit.HEARTS), Card("K", Suit.SPADES), Card("Q", Suit.SPADES), Card("A", Suit.SPADES)],
    ]

    sequence = [
        (0, Card("J", Suit.HEARTS)),
        (1, Card("9", Suit.CLUBS)),
        (3, Card("9", Suit.HEARTS)),
        (0, Card("J", Suit.DIAMONDS)),
        (1, Card("T", Suit.CLUBS)),
        (3, Card("T", Suit.HEARTS)),
        (0, Card("A", Suit.HEARTS)),
        (1, Card("Q", Suit.CLUBS)),
        (3, Card("K", Suit.SPADES)),
        (0, Card("K", Suit.HEARTS)),
        (1, Card("K", Suit.CLUBS)),
        (3, Card("Q", Suit.SPADES)),
        (0, Card("Q", Suit.HEARTS)),
        (1, Card("9", Suit.SPADES)),
        (3, Card("A", Suit.SPADES)),
    ]

    for player, card in sequence:
        result = game.play_card(player, card)
        assert result["success"]

    assert game.team1_score == 4
    assert game.team2_score == 0


def test_defenders_euchre_maker_gain_two_points() -> None:
    """Defenders should earn two points when they euchre the makers."""

    game = EuchreGame()
    game.dealer = 3
    game.trump = Suit.SPADES
    game.maker = 1
    game.phase = GamePhase.PLAY
    game.current_player = 0
    game.current_trick = []
    game.hands = [
        [Card("9", Suit.HEARTS), Card("T", Suit.HEARTS), Card("Q", Suit.HEARTS), Card("K", Suit.HEARTS), Card("A", Suit.HEARTS)],
        [Card("J", Suit.SPADES), Card("9", Suit.SPADES), Card("A", Suit.SPADES), Card("K", Suit.SPADES), Card("Q", Suit.SPADES)],
        [Card("9", Suit.CLUBS), Card("T", Suit.CLUBS), Card("Q", Suit.CLUBS), Card("K", Suit.CLUBS), Card("A", Suit.CLUBS)],
        [Card("9", Suit.DIAMONDS), Card("T", Suit.DIAMONDS), Card("Q", Suit.DIAMONDS), Card("K", Suit.DIAMONDS), Card("A", Suit.DIAMONDS)],
    ]

    plays = [
        (0, Card("9", Suit.HEARTS)),
        (1, Card("J", Suit.SPADES)),
        (2, Card("9", Suit.CLUBS)),
        (3, Card("9", Suit.DIAMONDS)),
        (1, Card("A", Suit.SPADES)),
        (2, Card("T", Suit.CLUBS)),
        (3, Card("T", Suit.DIAMONDS)),
        (0, Card("T", Suit.HEARTS)),
        (1, Card("K", Suit.SPADES)),
        (2, Card("Q", Suit.CLUBS)),
        (3, Card("Q", Suit.DIAMONDS)),
        (0, Card("Q", Suit.HEARTS)),
        (1, Card("Q", Suit.SPADES)),
        (2, Card("K", Suit.CLUBS)),
        (3, Card("K", Suit.DIAMONDS)),
        (0, Card("K", Suit.HEARTS)),
        (1, Card("9", Suit.SPADES)),
        (2, Card("A", Suit.CLUBS)),
        (3, Card("A", Suit.DIAMONDS)),
        (0, Card("A", Suit.HEARTS)),
    ]

    for player, card in plays:
        result = game.play_card(player, card)
        assert result["success"]
        if game.phase == GamePhase.BIDDING:
            break

    assert game.team2_score == 2
    assert game.team1_score == 0


def test_euchred_lone_maker_penalized_four_points() -> None:
    """Defenders should gain four points when setting a lone maker."""

    game = EuchreGame()
    game.maker = 1
    game.going_alone = True
    game.alone_player = 0
    game.tricks_won = [2, 3]

    game._score_hand()

    assert game.team1_score == 0
    assert game.team2_score == 4


def test_basic_ai_prefers_bowers_and_tracks_cards() -> None:
    """The helper AI prioritises bowers and records played cards."""

    ai = BasicEuchreAI()
    hand = [Card("J", Suit.SPADES), Card("A", Suit.HEARTS)]
    assert ai.choose_card(hand, None, Suit.SPADES) == Card("J", Suit.SPADES)

    lead = Card("Q", Suit.HEARTS)
    hand = [Card("J", Suit.DIAMONDS), Card("9", Suit.CLUBS)]
    assert ai.choose_card(hand, lead, Suit.HEARTS) == Card("J", Suit.DIAMONDS)

    ai.record_card(Card("J", Suit.SPADES))
    ai.record_card(Card("9", Suit.CLUBS))
    assert ai.memory.played_cards == [Card("J", Suit.SPADES), Card("9", Suit.CLUBS)]
