"""Tests for the Uno jump-in rule implementation."""

from __future__ import annotations

import random

from card_games.uno.uno import HouseRules, PlayerDecision, UnoCard, UnoGame, UnoPlayer


class MockInterface:
    """Mock interface for testing."""

    def __init__(self):
        self.messages = []
        self.jump_in_responses = []
        self.current_jump_in_idx = 0

    def show_heading(self, message: str) -> None:
        self.messages.append(("heading", message))

    def show_message(self, message: str, *, color: str = "", style: str = "") -> None:
        self.messages.append(("message", message, color, style))

    def show_hand(self, player: UnoPlayer, formatted_cards: list) -> None:
        pass

    def choose_action(self, game: UnoGame, player: UnoPlayer, playable: list, penalty_active: bool) -> PlayerDecision:
        return PlayerDecision(action="draw")

    def handle_drawn_card(self, game: UnoGame, player: UnoPlayer, card: UnoCard) -> PlayerDecision:
        return PlayerDecision(action="pass")

    def choose_color(self, player: UnoPlayer) -> str:
        return "red"

    def choose_swap_target(self, player: UnoPlayer, players: list) -> int:
        return 0

    def prompt_challenge(self, challenger: UnoPlayer, target: UnoPlayer, *, bluff_possible: bool) -> bool:
        return False

    def notify_uno_called(self, player: UnoPlayer) -> None:
        pass

    def notify_uno_penalty(self, player: UnoPlayer) -> None:
        pass

    def announce_winner(self, winner: UnoPlayer) -> None:
        pass

    def update_status(self, game: UnoGame) -> None:
        pass

    def render_card(self, card: UnoCard, *, emphasize: bool = False) -> str:
        return f"{card.color} {card.value}"

    def render_color(self, color: str) -> str:
        return color

    def play_sound(self, sound_type: str) -> None:
        self.messages.append(("sound", sound_type))

    def prompt_jump_in(self, player: UnoPlayer, card: UnoCard) -> bool:
        """Return pre-configured responses for jump-in prompts."""
        if self.current_jump_in_idx < len(self.jump_in_responses):
            response = self.jump_in_responses[self.current_jump_in_idx]
            self.current_jump_in_idx += 1
            return response
        return False


class TestJumpInRule:
    """Test the jump-in rule functionality."""

    def test_jump_in_disabled_by_default(self):
        """Test that jump-in is disabled by default."""
        house_rules = HouseRules()
        assert house_rules.jump_in is False

    def test_jump_in_can_be_enabled(self):
        """Test that jump-in can be enabled."""
        house_rules = HouseRules(jump_in=True)
        assert house_rules.jump_in is True

    def test_check_jump_in_no_identical_cards(self):
        """Test that check_jump_in returns None when no player has identical cards."""
        interface = MockInterface()
        house_rules = HouseRules(jump_in=True)
        players = [
            UnoPlayer("Player 1", is_human=True),
            UnoPlayer("Player 2", is_human=True),
        ]

        game = UnoGame(players=players, interface=interface, house_rules=house_rules, rng=random.Random(42))

        # Set up hands with non-identical cards
        players[0].hand = [UnoCard("red", "5"), UnoCard("blue", "3")]
        players[1].hand = [UnoCard("green", "7"), UnoCard("yellow", "2")]

        played_card = UnoCard("red", "1")
        result = game._check_jump_in(played_card, players[0])

        assert result is None

    def test_check_jump_in_with_identical_card_human_accepts(self):
        """Test that check_jump_in returns player and card index when human accepts."""
        interface = MockInterface()
        interface.jump_in_responses = [True]
        house_rules = HouseRules(jump_in=True)
        players = [
            UnoPlayer("Player 1", is_human=True),
            UnoPlayer("Player 2", is_human=True),
        ]

        game = UnoGame(players=players, interface=interface, house_rules=house_rules, rng=random.Random(42))

        # Set up hands
        players[0].hand = [UnoCard("red", "5")]
        players[1].hand = [UnoCard("red", "5"), UnoCard("blue", "3")]  # Has identical card

        played_card = UnoCard("red", "5")
        result = game._check_jump_in(played_card, players[0])

        assert result is not None
        assert result[0] == players[1]
        assert result[1] == 0  # Index of identical card

    def test_check_jump_in_with_identical_card_human_declines(self):
        """Test that check_jump_in returns None when human declines."""
        interface = MockInterface()
        interface.jump_in_responses = [False]
        house_rules = HouseRules(jump_in=True)
        players = [
            UnoPlayer("Player 1", is_human=True),
            UnoPlayer("Player 2", is_human=True),
        ]

        game = UnoGame(players=players, interface=interface, house_rules=house_rules, rng=random.Random(42))

        # Set up hands
        players[0].hand = [UnoCard("red", "5")]
        players[1].hand = [UnoCard("red", "5"), UnoCard("blue", "3")]

        played_card = UnoCard("red", "5")
        result = game._check_jump_in(played_card, players[0])

        assert result is None

    def test_check_jump_in_cannot_jump_on_wild_cards(self):
        """Test that players cannot jump in on wild cards."""
        interface = MockInterface()
        house_rules = HouseRules(jump_in=True)
        players = [
            UnoPlayer("Player 1", is_human=True),
            UnoPlayer("Player 2", is_human=True),
        ]

        game = UnoGame(players=players, interface=interface, house_rules=house_rules, rng=random.Random(42))

        # Set up hands
        players[0].hand = [UnoCard(None, "wild")]
        players[1].hand = [UnoCard(None, "wild"), UnoCard("blue", "3")]

        played_card = UnoCard(None, "wild")
        result = game._check_jump_in(played_card, players[0])

        assert result is None

    def test_check_jump_in_bot_decision(self):
        """Test that bots can decide to jump in based on personality."""
        interface = MockInterface()
        house_rules = HouseRules(jump_in=True)
        players = [
            UnoPlayer("Player 1", is_human=True),
            UnoPlayer("Bot 1", is_human=False, personality="aggressive"),
        ]

        game = UnoGame(players=players, interface=interface, house_rules=house_rules, rng=random.Random(42))

        # Set up hands - bot has few cards and an identical action card
        players[0].hand = [UnoCard("red", "skip")]
        players[1].hand = [UnoCard("red", "skip"), UnoCard("blue", "3")]

        played_card = UnoCard("red", "skip")

        # Test multiple times to check probabilistic behavior
        jump_in_count = 0
        for _ in range(10):
            game.rng = game.rng  # Keep the same RNG state
            result = game._check_jump_in(played_card, players[0])
            if result is not None:
                jump_in_count += 1
                assert result[0] == players[1]
                assert result[1] == 0

        # Aggressive bot with action card and 2 cards should jump in often
        assert jump_in_count > 0

    def test_bot_should_jump_in_personality(self):
        """Test that bot jump-in probability varies by personality."""
        interface = MockInterface()
        house_rules = HouseRules(jump_in=True)

        aggressive_bot = UnoPlayer("Aggressive", is_human=False, personality="aggressive")
        balanced_bot = UnoPlayer("Balanced", is_human=False, personality="balanced")
        easy_bot = UnoPlayer("Easy", is_human=False, personality="easy")

        game = UnoGame(players=[aggressive_bot, balanced_bot, easy_bot], interface=interface, house_rules=house_rules, rng=random.Random(42))

        # Set up hands with few cards (should increase probability)
        for player in game.players:
            player.hand = [UnoCard("red", "5"), UnoCard("blue", "3")]

        played_card = UnoCard("red", "5")
        identical_cards = [0]

        # Count jump-ins for each personality over many trials
        aggressive_jumps = sum(1 for _ in range(100) if game._bot_should_jump_in(aggressive_bot, played_card, identical_cards))
        balanced_jumps = sum(1 for _ in range(100) if game._bot_should_jump_in(balanced_bot, played_card, identical_cards))
        easy_jumps = sum(1 for _ in range(100) if game._bot_should_jump_in(easy_bot, played_card, identical_cards))

        # Aggressive should jump in most often, easy least often
        assert aggressive_jumps > balanced_jumps
        assert balanced_jumps > easy_jumps

    def test_bot_should_jump_in_hand_size(self):
        """Test that bots are more likely to jump in with fewer cards."""
        interface = MockInterface()
        house_rules = HouseRules(jump_in=True)

        bot = UnoPlayer("Bot", is_human=False, personality="balanced")
        game = UnoGame(players=[bot, UnoPlayer("P2", is_human=True)], interface=interface, house_rules=house_rules, rng=random.Random(42))

        played_card = UnoCard("red", "5")
        identical_cards = [0]

        # Test with 2 cards (few)
        bot.hand = [UnoCard("red", "5"), UnoCard("blue", "3")]
        few_cards_jumps = sum(1 for _ in range(100) if game._bot_should_jump_in(bot, played_card, identical_cards))

        # Test with 7 cards (many)
        bot.hand = [UnoCard("red", "5")] + [UnoCard("blue", str(i)) for i in range(6)]
        many_cards_jumps = sum(1 for _ in range(100) if game._bot_should_jump_in(bot, played_card, identical_cards))

        # Should jump in more often with fewer cards
        assert few_cards_jumps > many_cards_jumps

    def test_bot_should_jump_in_action_cards(self):
        """Test that bots are more likely to jump in on action cards."""
        interface = MockInterface()
        house_rules = HouseRules(jump_in=True)

        bot = UnoPlayer("Bot", is_human=False, personality="balanced")
        game = UnoGame(players=[bot, UnoPlayer("P2", is_human=True)], interface=interface, house_rules=house_rules, rng=random.Random(42))

        bot.hand = [UnoCard("red", "skip"), UnoCard("red", "5")]
        identical_cards = [0]

        # Test with action card
        action_card = UnoCard("red", "skip")
        action_jumps = sum(1 for _ in range(100) if game._bot_should_jump_in(bot, action_card, identical_cards))

        # Test with number card
        number_card = UnoCard("red", "5")
        number_jumps = sum(1 for _ in range(100) if game._bot_should_jump_in(bot, number_card, identical_cards))

        # Should jump in more often on action cards
        assert action_jumps > number_jumps

    def test_check_jump_in_priority_clockwise(self):
        """Test that jump-in priority goes clockwise from current player."""
        interface = MockInterface()
        interface.jump_in_responses = [True]  # First player asked accepts
        house_rules = HouseRules(jump_in=True)
        players = [
            UnoPlayer("Player 1", is_human=True),
            UnoPlayer("Player 2", is_human=True),
            UnoPlayer("Player 3", is_human=True),
            UnoPlayer("Player 4", is_human=True),
        ]

        game = UnoGame(players=players, interface=interface, house_rules=house_rules, rng=random.Random(42))

        # Only Player 2 has an identical card (to test priority)
        played_card = UnoCard("red", "5")
        players[0].hand = [UnoCard("red", "5"), UnoCard("blue", "3")]
        players[1].hand = [UnoCard("red", "5"), UnoCard("blue", "3")]  # Has identical card
        players[2].hand = [UnoCard("green", "7"), UnoCard("yellow", "2")]  # No identical card
        players[3].hand = [UnoCard("green", "8"), UnoCard("yellow", "3")]  # No identical card

        # Player 1 plays, should check in order: Player 2, Player 3, Player 4
        result = game._check_jump_in(played_card, players[0])

        # Player 2 should be selected (closest clockwise with identical card)
        assert result is not None
        assert result[0] == players[1]

    def test_jump_in_sound_played(self):
        """Test that jump-in sound is played when someone jumps in."""
        interface = MockInterface()
        interface.jump_in_responses = [True]
        house_rules = HouseRules(jump_in=True)
        players = [
            UnoPlayer("Player 1", is_human=True),
            UnoPlayer("Player 2", is_human=True),
        ]

        game = UnoGame(players=players, interface=interface, house_rules=house_rules, rng=random.Random(42))
        game.setup(starting_hand=2)

        # Set up specific hands
        players[0].hand = [UnoCard("red", "5")]
        players[1].hand = [UnoCard("red", "5"), UnoCard("blue", "3")]
        game.discard_pile = [UnoCard("red", "3")]
        game.active_color = "red"
        game.active_value = "3"

        # Player 1 plays red 5, Player 2 should jump in
        game._execute_play(players[0], 0)

        # Check that jump_in sound was played
        sound_messages = [msg for msg in interface.messages if msg[0] == "sound" and msg[1] == "jump_in"]
        assert len(sound_messages) > 0


class TestJumpInIntegration:
    """Integration tests for jump-in rule."""

    def test_jump_in_changes_turn_order(self):
        """Test that jump-in successfully changes the turn order."""
        interface = MockInterface()
        interface.jump_in_responses = [True]
        house_rules = HouseRules(jump_in=True)
        players = [
            UnoPlayer("Player 1", is_human=True),
            UnoPlayer("Player 2", is_human=True),
            UnoPlayer("Player 3", is_human=True),
        ]

        game = UnoGame(players=players, interface=interface, house_rules=house_rules, rng=random.Random(42))
        game.setup(starting_hand=2)

        # Set up hands
        players[0].hand = [UnoCard("red", "5")]
        players[1].hand = [UnoCard("red", "5"), UnoCard("blue", "3")]
        players[2].hand = [UnoCard("green", "7"), UnoCard("yellow", "2")]
        game.discard_pile = [UnoCard("red", "3")]
        game.active_color = "red"
        game.active_value = "3"
        game.current_index = 0

        # Player 1 plays, Player 2 jumps in and plays
        initial_index = game.current_index
        game._execute_play(players[0], 0)

        # After Player 2 jumps in and plays, turn advances to next player (Player 3, index 2)
        # since _execute_play recursively calls itself for jump-in and then advances turn
        assert game.current_index != initial_index

    def test_jump_in_logs_message(self):
        """Test that jumping in logs an appropriate message."""
        interface = MockInterface()
        interface.jump_in_responses = [True]
        house_rules = HouseRules(jump_in=True)
        players = [
            UnoPlayer("Player 1", is_human=True),
            UnoPlayer("Player 2", is_human=True),
        ]

        game = UnoGame(players=players, interface=interface, house_rules=house_rules, rng=random.Random(42))
        game.setup(starting_hand=2)

        # Set up hands
        players[0].hand = [UnoCard("red", "5")]
        players[1].hand = [UnoCard("red", "5"), UnoCard("blue", "3")]
        game.discard_pile = [UnoCard("red", "3")]
        game.active_color = "red"
        game.active_value = "3"

        # Clear previous messages
        interface.messages.clear()

        # Player 1 plays, Player 2 jumps in
        game._execute_play(players[0], 0)

        # Check that jump-in message was logged
        jump_in_messages = [msg for msg in interface.messages if "jump" in msg[1].lower()]
        assert len(jump_in_messages) > 0
        assert "Player 2" in jump_in_messages[0][1]
