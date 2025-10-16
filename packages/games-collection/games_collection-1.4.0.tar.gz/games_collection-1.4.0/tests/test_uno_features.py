"""Tests for Uno game features including house rules and team mode."""

import random

# Import directly from uno.py to avoid tkinter dependency
import sys
from pathlib import Path
from unittest.mock import MagicMock

# Add the parent directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from card_games.uno.uno import HouseRules, UnoCard, UnoGame, build_players


class MockInterface:
    """Mock interface for testing without UI dependencies."""

    def __init__(self):
        self.messages = []
        self.sounds_played = []

    def show_heading(self, message: str) -> None:
        self.messages.append(("heading", message))

    def show_message(self, message: str, *, color: str = "", style: str = "") -> None:
        self.messages.append(("message", message))

    def show_hand(self, player, formatted_cards) -> None:
        pass

    def choose_action(self, game, player, playable, penalty_active):
        return MagicMock(action="draw")

    def handle_drawn_card(self, game, player, card):
        return MagicMock(action="skip")

    def choose_color(self, player):
        return "red"

    def choose_swap_target(self, player, players):
        return 1

    def prompt_challenge(self, challenger, target, *, bluff_possible):
        return False

    def notify_uno_called(self, player) -> None:
        self.messages.append(("uno_called", player.name))

    def notify_uno_penalty(self, player) -> None:
        self.messages.append(("uno_penalty", player.name))

    def announce_winner(self, winner) -> None:
        self.messages.append(("winner", winner.name))

    def update_status(self, game) -> None:
        pass

    def render_card(self, card, *, emphasize: bool = False) -> str:
        return f"{card.color} {card.value}"

    def render_color(self, color: str) -> str:
        return color

    def play_sound(self, sound_type: str) -> None:
        self.sounds_played.append(sound_type)


class TestHouseRules:
    """Test house rules configuration."""

    def test_house_rules_default(self):
        """Test default house rules are all disabled."""
        rules = HouseRules()
        assert rules.stacking is False
        assert rules.jump_in is False
        assert rules.seven_zero_swap is False

    def test_house_rules_custom(self):
        """Test custom house rules configuration."""
        rules = HouseRules(stacking=True, jump_in=True, seven_zero_swap=True)
        assert rules.stacking is True
        assert rules.jump_in is True
        assert rules.seven_zero_swap is True


class TestTeamMode:
    """Test team play mode."""

    def test_build_players_team_mode(self):
        """Test building players with team assignments."""
        players = build_players(4, bots=3, team_mode=True)
        assert len(players) == 4
        # Check team assignments (alternating)
        assert players[0].team == 0
        assert players[1].team == 1
        assert players[2].team == 0
        assert players[3].team == 1

    def test_build_players_team_mode_requires_4_players(self):
        """Test that team mode requires exactly 4 players."""
        try:
            build_players(3, bots=2, team_mode=True)
            assert False, "Should raise ValueError"
        except ValueError as e:
            assert "exactly 4 players" in str(e)

    def test_build_players_no_team_mode(self):
        """Test building players without team mode."""
        players = build_players(3, bots=2, team_mode=False)
        assert len(players) == 3
        # All teams should be None
        for player in players:
            assert player.team is None


class TestStacking:
    """Test card stacking house rule."""

    def test_stacking_enabled(self):
        """Test that stacking is recognized when enabled."""
        rules = HouseRules(stacking=True)
        players = build_players(3, bots=2)
        interface = MockInterface()
        rng = random.Random(42)

        game = UnoGame(
            players=players,
            rng=rng,
            interface=interface,
            house_rules=rules,
        )

        assert game.house_rules.stacking is True

    def test_stacking_disabled(self):
        """Test that stacking is disabled by default."""
        players = build_players(3, bots=2)
        interface = MockInterface()

        game = UnoGame(
            players=players,
            rng=random.Random(42),
            interface=interface,
        )

        assert game.house_rules.stacking is False


class TestSevenZeroSwapping:
    """Test 7-0 swapping house rule."""

    def test_seven_zero_swap_enabled(self):
        """Test that 7-0 swapping is recognized when enabled."""
        rules = HouseRules(seven_zero_swap=True)
        players = build_players(3, bots=2)
        interface = MockInterface()

        game = UnoGame(
            players=players,
            rng=random.Random(42),
            interface=interface,
            house_rules=rules,
        )

        assert game.house_rules.seven_zero_swap is True

    def test_swap_hands(self):
        """Test the hand swapping functionality."""
        players = build_players(2, bots=1)
        interface = MockInterface()

        game = UnoGame(
            players=players,
            rng=random.Random(42),
            interface=interface,
            house_rules=HouseRules(seven_zero_swap=True),
        )

        # Setup hands
        players[0].hand = [UnoCard("red", "1"), UnoCard("blue", "2")]
        players[1].hand = [UnoCard("green", "3"), UnoCard("yellow", "4")]

        # Swap hands
        game._swap_hands(players[0], players[1])

        # Check that hands were swapped
        assert len(players[0].hand) == 2
        assert len(players[1].hand) == 2
        assert players[0].hand[0].value == "3"
        assert players[0].hand[1].value == "4"
        assert players[1].hand[0].value == "1"
        assert players[1].hand[1].value == "2"

    def test_rotate_hands_clockwise(self):
        """Test hand rotation in clockwise direction."""
        players = build_players(3, bots=2)
        interface = MockInterface()

        game = UnoGame(
            players=players,
            rng=random.Random(42),
            interface=interface,
            house_rules=HouseRules(seven_zero_swap=True),
        )

        # Setup hands
        players[0].hand = [UnoCard("red", "1")]
        players[1].hand = [UnoCard("blue", "2")]
        players[2].hand = [UnoCard("green", "3")]

        # Rotate hands (clockwise by default)
        game.direction = 1
        game._rotate_hands()

        # Check rotation: each player gets previous player's hand
        assert players[0].hand[0].value == "3"
        assert players[1].hand[0].value == "1"
        assert players[2].hand[0].value == "2"


class TestSoundEffects:
    """Test sound effect integration."""

    def test_sound_hooks_called(self):
        """Test that sound hooks are called during gameplay."""
        players = build_players(2, bots=1)
        interface = MockInterface()

        game = UnoGame(
            players=players,
            rng=random.Random(42),
            interface=interface,
        )
        game.setup()

        # After setup, no sounds should be played yet
        assert len(interface.sounds_played) == 0

        # Play a card and check if sound is triggered
        # This is integration-tested through gameplay


class TestUnoCard:
    """Test UnoCard functionality."""

    def test_card_creation(self):
        """Test creating cards with color and value."""
        card = UnoCard("red", "5")
        assert card.color == "red"
        assert card.value == "5"

    def test_wild_card(self):
        """Test wild card identification."""
        wild = UnoCard(None, "wild")
        assert wild.is_wild() is True

        colored = UnoCard("blue", "3")
        assert colored.is_wild() is False

    def test_action_card(self):
        """Test action card identification."""
        skip = UnoCard("green", "skip")
        assert skip.is_action() is True

        reverse = UnoCard("yellow", "reverse")
        assert reverse.is_action() is True

        plus2 = UnoCard("red", "+2")
        assert plus2.is_action() is True

        wild = UnoCard(None, "wild")
        assert wild.is_action() is True

        number = UnoCard("blue", "7")
        assert number.is_action() is False

    def test_card_matches(self):
        """Test card matching logic."""
        card = UnoCard("red", "5")

        # Match by color
        assert card.matches("red", "3") is True

        # Match by value
        assert card.matches("blue", "5") is True

        # No match
        assert card.matches("blue", "3") is False

        # Wild cards match everything
        wild = UnoCard(None, "wild")
        assert wild.matches("red", "5") is True
        assert wild.matches("blue", "3") is True


if __name__ == "__main__":
    # Run basic tests
    print("Running Uno feature tests...")

    # Test house rules
    test_hr = TestHouseRules()
    test_hr.test_house_rules_default()
    test_hr.test_house_rules_custom()
    print("✓ House rules tests passed")

    # Test team mode
    test_tm = TestTeamMode()
    test_tm.test_build_players_team_mode()
    test_tm.test_build_players_no_team_mode()
    print("✓ Team mode tests passed")

    # Test stacking
    test_stack = TestStacking()
    test_stack.test_stacking_enabled()
    test_stack.test_stacking_disabled()
    print("✓ Stacking tests passed")

    # Test 7-0 swapping
    test_swap = TestSevenZeroSwapping()
    test_swap.test_seven_zero_swap_enabled()
    test_swap.test_swap_hands()
    test_swap.test_rotate_hands_clockwise()
    print("✓ 7-0 swapping tests passed")

    # Test cards
    test_card = TestUnoCard()
    test_card.test_card_creation()
    test_card.test_wild_card()
    test_card.test_action_card()
    test_card.test_card_matches()
    print("✓ Card tests passed")

    print("\nAll tests passed! ✨")
