"""Tests for newly implemented card games."""

from __future__ import annotations

from card_games.bridge import BridgeGame, BridgePlayer
from card_games.common.cards import Card, Deck, Suit
from card_games.gin_rummy import GinRummyGame, GinRummyPlayer
from card_games.gin_rummy.game import KnockType
from card_games.hearts import HeartsGame, HeartsPlayer
from card_games.solitaire import SolitaireGame
from card_games.spades import SpadesGame, SpadesPlayer


class TestSolitaire:
    """Test Solitaire (Klondike) game."""

    def test_game_initialization(self):
        """Test that a solitaire game initializes correctly."""
        game = SolitaireGame()

        assert len(game.foundations) == 4
        assert len(game.tableau) == 7
        assert game.stock is not None
        assert game.waste is not None

    def test_tableau_setup(self):
        """Test that tableau is set up correctly."""
        game = SolitaireGame()

        # Verify tableau has correct number of cards
        for i, pile in enumerate(game.tableau):
            assert len(pile.cards) == i + 1
            assert pile.face_up_count == 1

    def test_draw_from_stock(self):
        """Test drawing from stock."""
        game = SolitaireGame()
        initial_stock = len(game.stock.cards)
        initial_waste = len(game.waste.cards)

        result = game.draw_from_stock()

        assert result is True
        assert len(game.stock.cards) == initial_stock - game.draw_count
        assert len(game.waste.cards) == initial_waste + game.draw_count
        assert game.moves_made == 1

    def test_is_won(self):
        """Test win detection."""
        game = SolitaireGame()

        # Initially not won
        assert game.is_won() is False

        # Simulate winning condition
        from card_games.common.cards import Card, Suit

        for foundation in game.foundations:
            foundation.cards = [Card(r, Suit.HEARTS) for r in ["A", "2", "3", "4", "5", "6", "7", "8", "9", "T", "J", "Q", "K"]]

        assert game.is_won() is True

    def test_recycle_limit_respected(self):
        """Draw-three games allow only three redeals by default."""
        game = SolitaireGame(draw_count=3)

        # Exhaust the stock by drawing until empty
        while game.draw_from_stock():
            continue

        for _ in range(3):
            assert game.reset_stock() is True
            while game.draw_from_stock():
                continue

        assert game.reset_stock() is False

    def test_standard_scoring_events(self):
        """Moves should award standard scoring bonuses and penalties."""
        game = SolitaireGame(draw_count=1, scoring_mode="standard")

        # Prepare a tableau pile with a hidden card
        source = game.tableau[0]
        source.cards = [Card("Q", Suit.HEARTS), Card("J", Suit.SPADES), Card("T", Suit.CLUBS)]
        source.face_up_count = 1

        destination = game.tableau[1]
        destination.cards = [Card("K", Suit.CLUBS), Card("Q", Suit.HEARTS), Card("J", Suit.DIAMONDS)]
        destination.face_up_count = 3

        score_before = game.score
        assert game.move_to_tableau(source, 1, num_cards=1) is True
        assert game.score == score_before + 5  # flip bonus

        # Move Ace of hearts to its foundation for +10
        game.tableau[2].cards = [Card("A", Suit.HEARTS)]
        game.tableau[2].face_up_count = 1
        assert game.move_to_foundation(game.tableau[2], 0) is True
        assert game.score == score_before + 5 + 10

        # Prepare a legal withdrawal target for the 2♥
        game.foundations[0].cards.append(Card("2", Suit.HEARTS))
        game.tableau[3].cards = [Card("3", Suit.CLUBS)]
        game.tableau[3].face_up_count = 1

        # Pull back from foundation (allowed under standard scoring)
        assert game.move_to_tableau(game.foundations[0], 3) is True
        assert game.score == score_before + 5 + 10 - 15

    def test_vegas_scoring(self):
        """Vegas scoring pays out five per foundation card from a -52 start."""
        game = SolitaireGame(draw_count=1, scoring_mode="vegas")
        assert game.score == -52

        game.tableau[0].cards = [Card("A", Suit.SPADES)]
        game.tableau[0].face_up_count = 1

        assert game.move_to_foundation(game.tableau[0], 0) is True
        assert game.score == -47

        # Vegas rules forbid withdrawing from foundations
        assert game.move_to_tableau(game.foundations[0], 1) is False

    def test_auto_move_collects_all_eligible_cards(self):
        """Auto play should continue until no further foundation moves exist."""
        game = SolitaireGame(draw_count=1)

        ace_clubs = Card("A", Suit.CLUBS)
        two_clubs = Card("2", Suit.CLUBS)
        three_clubs = Card("3", Suit.CLUBS)

        game.waste.cards = [ace_clubs]
        game.tableau[0].cards = [Card("5", Suit.HEARTS), two_clubs]
        game.tableau[0].face_up_count = 2
        game.tableau[1].cards = [Card("6", Suit.DIAMONDS), three_clubs]
        game.tableau[1].face_up_count = 2
        # Clear other tableau piles to avoid interference from random initialization
        for i in range(2, 7):
            game.tableau[i].cards = []
            game.tableau[i].face_up_count = 0

        assert game.auto_move_to_foundation() is True
        assert len(game.foundations[0].cards) == 3
        assert game.auto_moves_made == 1


class TestHearts:
    """Test Hearts game."""

    def test_game_initialization(self):
        """Test that a hearts game initializes correctly."""
        players = [HeartsPlayer(f"Player {i}", is_ai=True) for i in range(4)]
        game = HeartsGame(players)

        assert len(game.players) == 4
        assert game.hearts_broken is False

    def test_deal_cards(self):
        """Test card dealing."""
        players = [HeartsPlayer(f"Player {i}", is_ai=True) for i in range(4)]
        game = HeartsGame(players)
        game.deal_cards()

        for player in players:
            assert len(player.hand) == 13

    def test_calculate_round_points(self):
        """Test round points calculation."""
        player = HeartsPlayer("Test", is_ai=True)
        # Add some hearts and queen of spades
        player.tricks_won = [
            Card("2", Suit.HEARTS),
            Card("3", Suit.HEARTS),
            Card("Q", Suit.SPADES),
        ]

        points = player.calculate_round_points()
        assert points == 15  # 2 hearts + 13 for queen

    def test_shooting_the_moon(self):
        """Test shooting the moon detection."""
        players = [HeartsPlayer(f"Player {i}", is_ai=True) for i in range(4)]
        game = HeartsGame(players)

        # Give one player all hearts and queen of spades
        players[0].tricks_won = [Card(r, Suit.HEARTS) for r in ["2", "3", "4", "5", "6", "7", "8", "9", "T", "J", "Q", "K", "A"]]
        players[0].tricks_won.append(Card("Q", Suit.SPADES))

        # Before calculating scores, check points
        points_0 = players[0].calculate_round_points()
        assert points_0 == 26  # Shot the moon

        # Calculate scores
        game.calculate_scores()

        # Shooter gets 0, others get 26
        assert players[0].score == 0
        assert players[1].score == 26
        assert game.last_round_events.get(players[0].name) == "shot_the_moon"

    def test_shooting_the_sun_records_event(self):
        """Winning every trick should be recorded as shooting the sun."""
        players = [HeartsPlayer(f"Player {i}", is_ai=True) for i in range(4)]
        game = HeartsGame(players)

        deck = Deck()
        players[0].tricks_won = list(deck.cards)

        game.calculate_scores()

        assert players[0].score == 0
        assert all(players[i].score == 26 for i in range(1, 4))
        assert game.last_round_events.get(players[0].name) == "shot_the_sun"

    def test_first_trick_penalty_restrictions(self):
        """Players without clubs cannot dump points on the opening trick when avoidable."""
        players = [HeartsPlayer(f"Player {i}", is_ai=True) for i in range(4)]
        game = HeartsGame(players)

        players[0].hand = [Card("2", Suit.CLUBS)]
        players[1].hand = [Card("5", Suit.DIAMONDS), Card("Q", Suit.SPADES)]
        players[2].hand = [Card("7", Suit.DIAMONDS)]
        players[3].hand = [Card("9", Suit.DIAMONDS)]

        game.current_trick = [(players[0], Card("2", Suit.CLUBS))]
        game.lead_suit = Suit.CLUBS

        assert game.is_valid_play(players[1], Card("Q", Suit.SPADES)) is False

        players[1].hand = [Card("Q", Suit.SPADES), Card("5", Suit.HEARTS)]
        assert game.is_valid_play(players[1], Card("Q", Suit.SPADES)) is True

    def test_queen_of_spades_breaks_hearts(self):
        """Playing the queen of spades should break hearts immediately."""
        players = [HeartsPlayer(f"Player {i}", is_ai=True) for i in range(4)]
        game = HeartsGame(players)

        game.trick_number = 1
        game.current_trick = [(players[0], Card("5", Suit.SPADES))]
        game.lead_suit = Suit.SPADES
        players[1].hand = [Card("Q", Suit.SPADES)]

        game.play_card(players[1], Card("Q", Suit.SPADES))

        assert game.hearts_broken is True

    def test_trick_history_records_leader_and_winner(self):
        """Completed tricks should be stored with descriptive metadata."""
        players = [HeartsPlayer(f"Player {i}", is_ai=True) for i in range(4)]
        game = HeartsGame(players)

        cards = [Card("2", Suit.CLUBS), Card("3", Suit.CLUBS), Card("4", Suit.CLUBS), Card("5", Suit.CLUBS)]
        for i, card in enumerate(cards):
            game.current_trick.append((players[i], card))
        game.lead_suit = Suit.CLUBS
        game._current_trick_leader = players[0]

        winner = game.complete_trick()

        assert winner == players[3]
        assert len(game.trick_history) == 1
        record = game.trick_history[0]
        assert record.leader == players[0].name
        assert record.winner == players[3].name
        assert record.cards[0] == (players[0].name, Card("2", Suit.CLUBS))


class TestSpades:
    """Test Spades game."""

    def test_game_initialization(self):
        """Test that a spades game initializes correctly."""
        players = [SpadesPlayer(f"Player {i}", is_ai=True) for i in range(4)]
        game = SpadesGame(players)

        assert len(game.players) == 4
        assert game.spades_broken is False

        # Check partnerships
        assert game.players[0].partner_index == 2
        assert game.players[1].partner_index == 3

    def test_deal_cards(self):
        """Test card dealing."""
        players = [SpadesPlayer(f"Player {i}", is_ai=True) for i in range(4)]
        game = SpadesGame(players)
        game.deal_cards()

        for player in players:
            assert len(player.hand) == 13

    def test_suggest_bid(self):
        """Test AI bidding."""
        players = [SpadesPlayer(f"Player {i}", is_ai=True) for i in range(4)]
        game = SpadesGame(players)
        game.deal_cards()

        bid = game.suggest_bid(players[0])
        assert 0 <= bid <= 13

    def test_start_new_round_sets_two_of_clubs_leader(self):
        """The opening leader should be the player holding the two of clubs."""
        players = [SpadesPlayer(f"Player {i}", is_ai=True) for i in range(4)]
        game = SpadesGame(players)

        ordered_deck = Deck()
        hands = [ordered_deck.cards[i * 13 : (i + 1) * 13] for i in range(4)]

        def rigged_deal() -> None:
            for idx, hand in enumerate(hands):
                players[idx].hand = list(hand)
                players[idx].tricks_won = 0
                players[idx].bid = None
                players[idx].blind_nil = False
            game.total_tricks_played = 0
            game.trick_history = []
            game.bidding_history = []
            game.current_trick = []
            game.lead_suit = None
            game.spades_broken = False

        game.deal_cards = rigged_deal  # type: ignore[assignment]
        game.start_new_round()

        assert game.current_player_index == 0
        opener = game.players[game.current_player_index]
        two_clubs = Card("2", Suit.CLUBS)
        non_two_card = next(card for card in opener.hand if card != two_clubs)

        assert game.is_valid_play(opener, two_clubs) is True
        assert game.is_valid_play(opener, non_two_card) is False

    def test_spades_cannot_be_led_before_broken(self):
        """Spades should not be led until broken unless holding only spades."""
        players = [SpadesPlayer(f"Player {i}", is_ai=True) for i in range(4)]
        game = SpadesGame(players)

        ordered_deck = Deck()
        hands = [ordered_deck.cards[i * 13 : (i + 1) * 13] for i in range(4)]
        hands[0][1], hands[3][0] = hands[3][0], hands[0][1]

        def mixed_deal() -> None:
            for idx, hand in enumerate(hands):
                players[idx].hand = list(hand)
                players[idx].tricks_won = 0
                players[idx].bid = None
                players[idx].blind_nil = False
            game.total_tricks_played = 1
            game.trick_history = []
            game.bidding_history = []
            game.current_trick = []
            game.lead_suit = None
            game.spades_broken = False

        game.deal_cards = mixed_deal  # type: ignore[assignment]
        game.start_new_round()

        opener = game.players[game.current_player_index]
        spade_card = next(card for card in opener.hand if card.suit == Suit.SPADES)
        assert game.is_valid_play(opener, spade_card) is False

        # Separate scenario: player with only spades may lead them
        spade_players = [SpadesPlayer(f"Spade {i}", is_ai=True) for i in range(4)]
        spade_game = SpadesGame(spade_players)

        spade_only_hand = [Card(rank, Suit.SPADES) for rank in ("2", "3", "4", "5", "6", "7", "8", "9", "T", "J", "Q", "K", "A")]
        spade_players[0].hand = list(spade_only_hand)
        for idx in range(1, 4):
            spade_players[idx].hand = [Card("2", Suit.CLUBS)] * 13
        for player in spade_players:
            player.tricks_won = 0
            player.bid = None
            player.blind_nil = False
        spade_game.round_number = 1
        spade_game.total_tricks_played = 1
        spade_game.trick_history = []
        spade_game.bidding_history = []
        spade_game.current_trick = []
        spade_game.lead_suit = None
        spade_game.spades_broken = False
        spade_game.current_player_index = 0

        assert all(card.suit == Suit.SPADES for card in spade_players[0].hand)
        assert spade_game.is_valid_play(spade_players[0], spade_players[0].hand[0]) is True

    def test_complete_trick_records_history(self):
        """Completing a trick should record the play order for review."""
        players = [SpadesPlayer(f"Player {i}", is_ai=True) for i in range(4)]
        game = SpadesGame(players)

        ordered_deck = Deck()
        hands = [ordered_deck.cards[i * 13 : (i + 1) * 13] for i in range(4)]

        def rigged_deal() -> None:
            for idx, hand in enumerate(hands):
                players[idx].hand = list(hand)
                players[idx].tricks_won = 0
                players[idx].bid = None
                players[idx].blind_nil = False
            game.total_tricks_played = 0
            game.trick_history = []
            game.bidding_history = []
            game.current_trick = []
            game.lead_suit = None
            game.spades_broken = False

        game.deal_cards = rigged_deal  # type: ignore[assignment]
        game.start_new_round()

        for _ in range(4):
            current_idx = game.current_player_index or 0
            player = game.players[current_idx]
            card_to_play = game.get_valid_plays(player)[0]
            game.play_card(player, card_to_play)

        winner = game.complete_trick()
        assert winner in players
        assert len(game.trick_history) == 1
        assert len(game.trick_history[0]) == 4

    def test_round_scoring_with_nil_and_bags(self):
        """Round scoring should account for nil bids and bag penalties."""
        players = [SpadesPlayer(f"Player {i}") for i in range(4)]
        game = SpadesGame(players)

        players[0].bid = 4
        players[0].tricks_won = 5
        players[1].bid = 5
        players[1].tricks_won = 5
        players[2].bid = 0
        players[2].tricks_won = 0
        players[3].bid = 3
        players[3].tricks_won = 3
        players[2].blind_nil = True

        game.bags = [9, 0]

        scores = game.calculate_round_score()

        assert scores[0] == (4 * 10) + 1 + 200 - 100
        assert scores[1] == (5 + 3) * 10
        assert game.team_scores[0] == scores[0]
        assert game.team_scores[1] == scores[1]
        assert game.bags[0] == 0

    def test_game_over_detection(self):
        """Game over when a team reaches or exceeds the target score."""
        players = [SpadesPlayer(f"Player {i}") for i in range(4)]
        game = SpadesGame(players)

        game.team_scores = [505, 420]

        assert game.is_game_over() is True
        assert game.get_winner() == 0


class TestGinRummy:
    """Test Gin Rummy game."""

    def test_game_initialization(self):
        """Test that a gin rummy game initializes correctly."""
        players = [GinRummyPlayer(f"Player {i}", is_ai=True) for i in range(2)]
        game = GinRummyGame(players)

        assert len(game.players) == 2

    def test_deal_cards_sets_initial_state(self):
        """Dealing creates 10-card hands and triggers the upcard offer."""

        players = [GinRummyPlayer(f"Player {i}", is_ai=True) for i in range(2)]
        game = GinRummyGame(players)
        game.deal_cards()

        for player in players:
            assert len(player.hand) == 10

        assert len(game.discard_pile) == 1
        assert game.initial_upcard_phase is True
        assert game.blocked_discard_card is None
        assert game.current_player_idx == game.initial_offer_order[0]

    def test_analyze_hand_chooses_best_melds(self):
        """Optimal meld search should prefer runs that free high cards."""

        from card_games.common.cards import Card, Suit

        players = [GinRummyPlayer("Player", is_ai=True) for _ in range(2)]
        game = GinRummyGame(players)
        hand = [
            Card("4", Suit.HEARTS),
            Card("5", Suit.HEARTS),
            Card("6", Suit.HEARTS),
            Card("7", Suit.HEARTS),
            Card("7", Suit.CLUBS),
            Card("7", Suit.DIAMONDS),
            Card("9", Suit.SPADES),
            Card("K", Suit.SPADES),
        ]

        analysis = game.analyze_hand(hand)
        assert analysis.deadwood_total == 19  # 9♠ + K♠
        meld_cards = {card for meld in analysis.melds for card in meld.cards}
        assert Card("7", Suit.HEARTS) in meld_cards
        assert Card("7", Suit.CLUBS) in meld_cards

    def test_calculate_round_score_gin_and_big_gin(self):
        """Gin and big gin scoring should award the correct bonuses."""

        from card_games.common.cards import Card, Suit

        players = [GinRummyPlayer("Knocker"), GinRummyPlayer("Opponent")]
        game = GinRummyGame(players)

        gin_hand = [
            Card("3", Suit.HEARTS),
            Card("4", Suit.HEARTS),
            Card("5", Suit.HEARTS),
            Card("6", Suit.HEARTS),
            Card("7", Suit.CLUBS),
            Card("7", Suit.DIAMONDS),
            Card("7", Suit.SPADES),
            Card("9", Suit.CLUBS),
            Card("9", Suit.DIAMONDS),
            Card("9", Suit.HEARTS),
        ]
        players[0].hand = gin_hand
        players[1].hand = [
            Card("A", Suit.SPADES),
            Card("2", Suit.SPADES),
            Card("3", Suit.SPADES),
            Card("4", Suit.SPADES),
            Card("5", Suit.SPADES),
            Card("7", Suit.CLUBS),
            Card("8", Suit.HEARTS),
            Card("Q", Suit.DIAMONDS),
            Card("K", Suit.DIAMONDS),
            Card("K", Suit.HEARTS),
        ]

        summary = game.calculate_round_score(players[0], players[1])
        assert summary.knock_type == KnockType.GIN
        assert summary.points_awarded["Knocker"] == summary.opponent_deadwood + 25

        # Big gin: add one more card that still keeps zero deadwood.
        players[0].hand = gin_hand + [Card("7", Suit.HEARTS)]
        summary = game.calculate_round_score(players[0], players[1])
        assert summary.knock_type == KnockType.BIG_GIN
        assert summary.points_awarded["Knocker"] == summary.opponent_deadwood + 31

    def test_knock_with_layoff_and_undercut(self):
        """Layoffs reduce opponent deadwood and can trigger undercuts."""

        from card_games.common.cards import Card, Suit

        players = [GinRummyPlayer("Knocker"), GinRummyPlayer("Opponent")]
        game = GinRummyGame(players)

        # Knocker knocks with melds and modest deadwood.
        players[0].hand = [
            Card("4", Suit.HEARTS),
            Card("5", Suit.HEARTS),
            Card("6", Suit.HEARTS),
            Card("9", Suit.CLUBS),
            Card("9", Suit.DIAMONDS),
            Card("9", Suit.HEARTS),
            Card("2", Suit.SPADES),
            Card("3", Suit.SPADES),
            Card("4", Suit.SPADES),
            Card("5", Suit.CLUBS),
        ]

        players[1].hand = [
            Card("7", Suit.HEARTS),
            Card("8", Suit.HEARTS),
            Card("9", Suit.SPADES),
            Card("T", Suit.SPADES),
            Card("J", Suit.SPADES),
            Card("Q", Suit.SPADES),
            Card("4", Suit.CLUBS),
            Card("5", Suit.CLUBS),
            Card("6", Suit.CLUBS),
            Card("K", Suit.DIAMONDS),
        ]

        summary = game.calculate_round_score(players[0], players[1])
        assert summary.knock_type == KnockType.KNOCK
        # Opponent should lay off the 7♥-8♥ run extensions.
        assert Card("7", Suit.HEARTS) in summary.layoff_cards
        assert Card("8", Suit.HEARTS) in summary.layoff_cards
        assert summary.points_awarded["Knocker"] == summary.opponent_deadwood - summary.knocker_deadwood

        # Modify opponent to undercut.
        players[1].hand = [
            Card("4", Suit.HEARTS),
            Card("5", Suit.HEARTS),
            Card("6", Suit.HEARTS),
            Card("7", Suit.HEARTS),
            Card("8", Suit.HEARTS),
            Card("4", Suit.CLUBS),
            Card("5", Suit.CLUBS),
            Card("6", Suit.CLUBS),
            Card("7", Suit.CLUBS),
            Card("8", Suit.CLUBS),
        ]
        summary = game.calculate_round_score(players[0], players[1])
        assert summary.knock_type == KnockType.UNDERCUT
        assert summary.points_awarded["Opponent"] == (summary.knocker_deadwood - summary.opponent_deadwood) + 25

    def test_stock_reshuffle(self):
        """Drawing from an empty stock should recycle the discard pile."""

        from card_games.common.cards import Card, Suit

        players = [GinRummyPlayer(f"Player {i}") for i in range(2)]
        game = GinRummyGame(players)
        game.deal_cards()

        # Exhaust the stock manually.
        game.deck.cards = []
        game.discard_pile.extend(
            [
                Card("2", Suit.CLUBS),
                Card("3", Suit.CLUBS),
                Card("4", Suit.CLUBS),
            ]
        )

        drawn = game.draw_from_stock()
        assert drawn is not None
        assert len(game.discard_pile) == 1

    def test_initial_upcard_blocking(self):
        """The declined opening upcard cannot be redrawn until stock is taken."""

        players = [GinRummyPlayer(f"Player {i}") for i in range(2)]
        game = GinRummyGame(players)
        game.deal_cards()

        first_player = game.initial_offer_order[0]
        second_player = game.initial_offer_order[1]

        game.pass_initial_upcard(first_player)
        game.pass_initial_upcard(second_player)

        assert game.blocked_discard_card == game.discard_pile[-1]
        assert game.can_draw_from_discard(first_player) is False
        game.draw_from_stock()
        assert game.can_draw_from_discard(first_player) is True


class TestBridge:
    """Test Bridge game."""

    def test_game_initialization(self):
        """Test that a bridge game initializes correctly."""
        players = [BridgePlayer(f"Player {i}", is_ai=True) for i in range(4)]
        game = BridgeGame(players)

        assert len(game.players) == 4

        # Check positions
        positions = [p.position for p in game.players]
        assert positions == ["N", "E", "S", "W"]

        # Check partnerships
        assert game.players[0].partner_index == 2  # N-S
        assert game.players[1].partner_index == 3  # E-W

    def test_deal_cards(self):
        """Test card dealing."""
        players = [BridgePlayer(f"Player {i}", is_ai=True) for i in range(4)]
        game = BridgeGame(players)
        game.deal_cards()

        for player in players:
            assert len(player.hand) == 13

    def test_evaluate_hand(self):
        """Test HCP calculation."""
        players = [BridgePlayer("Player", is_ai=True) for _ in range(4)]
        game = BridgeGame(players)

        from card_games.common.cards import Card, Suit

        players[0].hand = [
            Card("A", Suit.HEARTS),  # 4 points
            Card("K", Suit.DIAMONDS),  # 3 points
            Card("Q", Suit.CLUBS),  # 2 points
            Card("J", Suit.SPADES),  # 1 point
        ]

        hcp = game.evaluate_hand(players[0])
        assert hcp == 10
