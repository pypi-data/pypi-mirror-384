"""A text-based user interface for the Canasta game engine.

This module provides a command-line interface (CLI) for playing Canasta,
allowing users to interact with the game through text commands. It handles
displaying hands, prompting for actions, and rendering game state.
"""

from __future__ import annotations

from typing import Iterable

from card_games.canasta.game import (
    CanastaGame,
    CanastaPlayer,
    DrawSource,
    JokerCard,
    MeldError,
)
from card_games.common.cards import Card
from common.cli_utils import THEMES, ASCIIArt

THEME = THEMES["forest"]


def _format_hand(cards: Iterable[Card | JokerCard]) -> str:
    """Return a readable representation for a collection of Canasta cards."""
    return " ".join(map(str, cards)) if cards else "—"


def _display_hand(player: CanastaPlayer) -> None:
    """Print the player's hand with 1-based positional indices."""
    print(f"\n{THEME.primary}Your hand ({len(player.hand)} cards):{THEME.text}")
    for i, card in enumerate(player.hand, 1):
        print(f"  {i:2}: {card}")


def _prompt_indices(prompt: str) -> list[int]:
    """Parse 1-based indices from user input."""
    response = input(prompt).strip()
    if not response:
        return []
    try:
        return [int(chunk) for chunk in response.replace(",", " ").split()]
    except ValueError:
        print("Invalid input. Please enter numeric positions.")
        return []


def _take_ai_turn(game: CanastaGame, player: CanastaPlayer) -> None:
    """Execute a simple, deterministic turn for an AI opponent."""
    drawn = game.draw(player, DrawSource.STOCK)
    discard_target = player.hand[0] if player.hand else drawn
    game.discard(player, discard_target)
    print(f"  {player.name} draws a card and discards {discard_target}.")


def _collect_cards_by_index(player: CanastaPlayer, indices: Iterable[int]) -> list[Card | JokerCard]:
    """Return a list of cards selected by their 1-based indices."""
    cards: list[Card | JokerCard] = []
    for index in indices:
        if not (1 <= index <= len(player.hand)):
            raise IndexError(f"Card index {index} is out of range.")
        cards.append(player.hand[index - 1])
    return cards


def _human_turn(game: CanastaGame, player: CanastaPlayer) -> None:
    """Conduct a turn for the human-controlled player."""
    print(ASCIIArt.banner(f"{player.name}'s turn", color=THEME.primary))
    _display_hand(player)

    source = DrawSource.STOCK
    if game.can_take_discard(player):
        choice = input("Draw from (S)tock or (D)iscard pile? ").strip().lower()
        if choice.startswith("d"):
            source = DrawSource.DISCARD
    else:
        print("Discard pile is frozen; drawing from stock.")

    drawn_card = game.draw(player, source)
    print(f"You drew: {drawn_card}")

    while True:
        indices = _prompt_indices("Enter card numbers to meld (e.g., '1, 2, 3'), or press Enter to skip: ")
        if not indices:
            break
        try:
            cards_to_meld = _collect_cards_by_index(player, indices)
            meld = game.add_meld(player, cards_to_meld)
            print(f"Successfully laid down meld: {_format_hand(meld.cards)}")
        except (IndexError, MeldError) as e:
            print(f"Could not create meld: {e}")
        _display_hand(player)

    if not player.hand:
        print("All cards have been melded; skipping discard.")
        return

    while True:
        indices = _prompt_indices("Choose a card number to discard: ")
        if not indices:
            print("You must discard a card.")
            continue
        try:
            card_to_discard = _collect_cards_by_index(player, [indices[0]])[0]
            game.discard(player, card_to_discard)
            print(f"You discarded {card_to_discard}.")
            break
        except (IndexError, ValueError) as e:
            print(f"Invalid discard choice: {e}")

    if not player.hand and game.can_go_out(player.team_index):
        if input("Go out and end the round? (y/n): ").strip().lower() == "y":
            scores = game.go_out(player)
            _print_round_results(game, scores)


def _print_round_results(game: CanastaGame, breakdown: dict[int, int]) -> None:
    """Display the scoring details at the end of a round."""
    print(ASCIIArt.banner("Round Complete", color=THEME.secondary))
    for i, team in enumerate(game.teams):
        meld_points = game.calculate_team_meld_points(i)
        deadwood = game.calculate_team_deadwood(i)
        round_score = breakdown.get(i, 0)
        print(f"{team.name}: Melds: {meld_points}, Deadwood: -{deadwood}, " f"Round Total: {round_score}, Grand Total: {team.score}")


def main() -> None:
    """Launch an interactive Canasta session."""
    print(ASCIIArt.banner("Welcome to Canasta", color=THEME.primary))
    human_name = input("Enter your name: ").strip() or "Player"

    players = [
        CanastaPlayer(name=human_name, team_index=0, is_ai=False),
        CanastaPlayer(name="AI East", team_index=1, is_ai=True),
        CanastaPlayer(name="AI Partner", team_index=0, is_ai=True),
        CanastaPlayer(name="AI West", team_index=1, is_ai=True),
    ]
    game = CanastaGame(players)

    while not game.round_over:
        current_player = game.players[game.current_player_index]
        if current_player.is_ai:
            _take_ai_turn(game, current_player)
        else:
            _human_turn(game, current_player)

        if game.round_over:
            break
        game.advance_turn()

    if not game.round_over:
        # Handle game ending due to empty stock pile.
        scores = {i: 0 for i in range(len(game.teams))}
        _print_round_results(game, scores)


if __name__ == "__main__":  # pragma: no cover
    main()
