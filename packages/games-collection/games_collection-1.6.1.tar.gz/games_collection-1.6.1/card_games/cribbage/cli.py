"""Command-line interface for the Cribbage card game.

This module provides the functions to run an interactive game of Cribbage in
the terminal, handling user input and displaying the game state.
"""

from __future__ import annotations

from itertools import combinations
from typing import Sequence

from card_games.common.cards import Card, Deck
from card_games.cribbage.game import CribbageGame, GamePhase


def format_cards(cards: Sequence[Card]) -> str:
    """Return a comma-separated representation of a sequence of cards."""
    return ", ".join(map(str, cards))


def print_scoreboard(game: CribbageGame) -> None:
    """Print the current scores and identify the dealer."""
    state = game.get_state_summary()
    print(f"Scoreboard: Player 1: {state['player1_score']} | " f"Player 2: {state['player2_score']} (Dealer: Player {state['dealer']})")


def cut_for_first_deal() -> int:
    """Determine the first dealer by having both players cut a card."""
    print("\nCutting for the first deal...")
    while True:
        deck = Deck()
        deck.shuffle()
        p1_card, p2_card = deck.deal(2)
        print(f"Player 1 cuts {p1_card}, Player 2 cuts {p2_card}.")
        if p1_card.value != p2_card.value:
            dealer = 1 if p1_card.value > p2_card.value else 2
            print(f"Player {dealer} deals first.\n")
            return dealer
        print("Tie on the cut. Cutting again.\n")


def prompt_discard_choice(hand: list[Card]) -> list[Card]:
    """Prompt the human player to choose two cards to discard to the crib."""
    options = list(combinations(range(len(hand)), 2))
    while True:
        print("\nChoose two cards to discard:")
        for i, (idx1, idx2) in enumerate(options, 1):
            print(f"  {i}. {hand[idx1]} and {hand[idx2]}")
        choice = input(f"Select an option (1-{len(options)}): ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(options):
            idx1, idx2 = options[int(choice) - 1]
            discards = [hand[idx1], hand[idx2]]
            print(f"You discarded {format_cards(discards)} to the crib.")
            return discards
        print("Invalid selection. Please try again.")


def display_pegging_history(game: CribbageGame) -> None:
    """Display the history of the current pegging sequence."""
    history = game.get_state_summary().get("pegging_history", [])
    if not history:
        print("\nPegging begins. The count is 0.")
        return
    print("\nPegging History:")
    # ... (implementation for displaying history)


def check_skunk_line(previous: tuple[int, int], game: CribbageGame) -> None:
    """Report when a player crosses a skunk line (61 or 91 points)."""
    # ... (implementation for checking skunk lines)


def announce_play(game: CribbageGame, player: int, card: Card, result: dict[str, object]) -> None:
    """Announce a pegging play and its result."""
    # ... (implementation for announcing a play)


def announce_go(game: CribbageGame, player: int, result: dict[str, object]) -> None:
    """Announce a "go" action and its result."""
    # ... (implementation for announcing a go)


def summarize_hand(hand: Sequence[Card], starter: Card, is_crib: bool) -> list[str]:
    """Return a human-readable summary of a hand's score."""
    # ... (implementation for summarizing a hand)


def handle_discard_phase(game: CribbageGame) -> tuple[list[Card], list[Card]]:
    """Run the discard phase of the game."""
    # ... (implementation for handling discards)


def handle_pegging_phase(game: CribbageGame) -> bool:
    """Run the pegging phase of the game. Return True if the game ends."""
    # ... (implementation for handling pegging)


def handle_show_phase(game: CribbageGame, p1_show: Sequence[Card], p2_show: Sequence[Card]) -> None:
    """Run the show phase, scoring both hands and the crib."""
    # ... (implementation for handling the show)


def describe_skunk(winner: int, game: CribbageGame) -> None:
    """Describe the skunk result at the end of the game."""
    # ... (implementation for describing skunk)


def game_loop(game: CribbageGame) -> None:
    """Play an interactive game of Cribbage in the terminal."""
    print("\n🎴 Welcome to Cribbage! First to 121 points wins. 🎴\n")
    dealer = cut_for_first_deal()
    game.start_new_hand(dealer=dealer)

    p1_show, p2_show = [], []
    while game.phase != GamePhase.GAME_OVER:
        if game.phase == GamePhase.DISCARD:
            p1_show, p2_show = handle_discard_phase(game)
        elif game.phase == GamePhase.PLAY:
            if handle_pegging_phase(game):
                break
        elif game.phase == GamePhase.SHOW:
            handle_show_phase(game, p1_show, p2_show)

    print("\n" + "=" * 60)
    print("GAME OVER")
    winner = game.winner or (1 if game.player1_score > game.player2_score else 2)
    print(f"🎉 Player {winner} wins! 🎉")
    print(f"Final Score: Player 1: {game.player1_score}, Player 2: {game.player2_score}")
    describe_skunk(winner, game)
    print("=" * 60)
