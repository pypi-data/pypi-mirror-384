"""Tests for Uno custom deck designer support."""

from __future__ import annotations

import random
from typing import Sequence

import pytest

from card_games.uno import (
    CustomDeckLoader,
    CustomDeckValidationError,
    HouseRules,
    PlayerDecision,
    UnoCard,
    UnoGame,
    UnoInterface,
    UnoPlayer,
)


class DummyInterface(UnoInterface):
    """Minimal UnoInterface used for custom deck testing."""

    def __init__(self, swap_choice: int = 1) -> None:
        self.swap_choice = swap_choice
        self.messages: list[str] = []

    def show_heading(self, message: str) -> None:  # pragma: no cover - no output for tests
        self.messages.append(message)

    def show_message(self, message: str, *, color: str = "", style: str = "") -> None:
        self.messages.append(message)

    def show_hand(self, player: UnoPlayer, formatted_cards: Sequence[str]) -> None:
        # No-op for tests
        pass

    def choose_action(
        self,
        game: UnoGame,
        player: UnoPlayer,
        playable: Sequence[int],
        penalty_active: bool,
    ) -> PlayerDecision:
        raise AssertionError("choose_action should not be called in custom deck tests")

    def handle_drawn_card(self, game: UnoGame, player: UnoPlayer, card: UnoCard) -> PlayerDecision:
        return PlayerDecision(action="skip")

    def choose_color(self, player: UnoPlayer) -> str:
        return getattr(player, "available_colors", ("red", "blue"))[0]

    def choose_swap_target(self, player: UnoPlayer, players: Sequence[UnoPlayer]) -> int:
        return self.swap_choice

    def prompt_challenge(self, challenger: UnoPlayer, target: UnoPlayer, *, bluff_possible: bool) -> bool:
        return False

    def notify_uno_called(self, player: UnoPlayer) -> None:
        pass

    def notify_uno_penalty(self, player: UnoPlayer) -> None:
        pass

    def announce_winner(self, winner: UnoPlayer) -> None:
        self.messages.append(f"Winner: {winner.name}")

    def update_status(self, game: UnoGame) -> None:
        pass

    def render_card(self, card: UnoCard, *, emphasize: bool = False) -> str:
        return card.label()

    def render_color(self, color: str) -> str:
        return color

    def play_sound(self, sound_type: str) -> None:
        pass

    def prompt_jump_in(self, player: UnoPlayer, card: UnoCard) -> bool:
        return False


@pytest.fixture
def custom_deck_definition() -> dict:
    """Provide a reusable custom deck definition for tests."""

    colors = ["red", "blue", "purple"]
    cards = []
    for color in colors:
        cards.append({"color": color, "value": "0", "count": 1})
        cards.append({"color": color, "value": "1", "count": 2})
    cards.extend(
        [
            {"color": None, "value": "wild", "count": 4},
            {"color": None, "value": "+4", "count": 4},
            {"color": "purple", "value": "swap", "count": 2, "effect": "swap_with_any"},
            {"color": "purple", "value": "reverse", "count": 1},
        ]
    )
    return {"name": "Test Deck", "colors": colors, "cards": cards}


def test_custom_deck_loader_validates_and_populates(custom_deck_definition: dict) -> None:
    """Ensure the custom deck loader validates input and UnoGame applies colors."""

    deck = CustomDeckLoader.load_from_mapping(custom_deck_definition)
    interface = DummyInterface()
    players = [UnoPlayer("Alice", is_human=True), UnoPlayer("Bob", is_human=True)]
    game = UnoGame(players=players, interface=interface, house_rules=HouseRules(), rng=random.Random(5), custom_deck=deck)

    assert game.available_colors == ("red", "blue", "purple")
    assert players[0].available_colors == ("red", "blue", "purple")
    assert any(card.effect == "swap_with_any" for card in game.deck.cards)


def test_custom_swap_effect_swaps_hands(custom_deck_definition: dict) -> None:
    """Playing a custom swap card should exchange player hands."""

    deck = CustomDeckLoader.load_from_mapping(custom_deck_definition)
    interface = DummyInterface(swap_choice=1)
    players = [UnoPlayer("Alice", is_human=True), UnoPlayer("Bob", is_human=True)]
    game = UnoGame(players=players, interface=interface, house_rules=HouseRules(), rng=random.Random(7), custom_deck=deck)

    swap_card = UnoCard("purple", "swap", effect="swap_with_any")
    players[0].hand = [swap_card]
    players[1].hand = [UnoCard("blue", "5"), UnoCard("red", "2")]
    game.discard_pile = [UnoCard("purple", "1")]
    game.active_color = "purple"
    game.active_value = "1"
    game.current_index = 0

    winner = game._execute_play(players[0], 0, declare_uno=True)

    assert winner is None
    assert [card.value for card in players[0].hand] == ["5", "2"]
    assert [card.value for card in players[1].hand] == ["swap"]


def test_custom_deck_loader_rejects_invalid_definition() -> None:
    """Invalid deck definitions should raise a validation error."""

    with pytest.raises(CustomDeckValidationError):
        CustomDeckLoader.load_from_mapping({"colors": ["red"], "cards": []})
