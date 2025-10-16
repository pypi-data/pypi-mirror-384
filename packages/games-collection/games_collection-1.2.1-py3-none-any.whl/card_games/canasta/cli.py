"""Text-based interface for the Canasta engine."""

from __future__ import annotations

from typing import Iterable

from card_games.canasta.game import CanastaGame, CanastaPlayer, DrawSource, JokerCard, MeldError
from card_games.common.cards import Card
from common.cli_utils import THEMES, ASCIIArt

THEME = THEMES["forest"]


def _format_hand(cards: Iterable[Card | JokerCard]) -> str:
    """Return a readable representation for mixed card collections."""

    parts: list[str] = []
    for card in cards:
        parts.append(str(card))
    return " ".join(parts) if parts else "—"


def _display_hand(player: CanastaPlayer) -> None:
    """Print the player's hand with positional indices."""

    print(f"\n{THEME.primary}Your hand ({len(player.hand)} cards):{THEME.text}")
    for index, card in enumerate(player.hand, start=1):
        print(f"  {index:2}: {card}")


def _prompt_indices(prompt: str) -> list[int]:
    """Return 1-based indices parsed from user input."""

    response = input(prompt).strip()
    if not response:
        return []
    indices: list[int] = []
    for chunk in response.replace(",", " ").split():
        try:
            value = int(chunk)
        except ValueError:
            print("Please enter numeric positions.")
            return []
        if value <= 0:
            print("Positions must be positive.")
            return []
        indices.append(value)
    return indices


def _take_ai_turn(game: CanastaGame, player: CanastaPlayer) -> None:
    """Execute a very small deterministic turn for AI opponents."""

    drawn = game.draw(player, DrawSource.STOCK)
    discard_target = player.hand[0] if player.hand else drawn
    game.discard(player, discard_target)
    print(f"  {player.name} draws {drawn} and discards {discard_target}.")


def _collect_cards_by_index(player: CanastaPlayer, indices: Iterable[int]) -> list[Card | JokerCard]:
    """Return cards selected via 1-based ``indices``."""

    cards: list[Card | JokerCard] = []
    hand_size = len(player.hand)
    for index in indices:
        if index < 1 or index > hand_size:
            raise IndexError("Card selection out of range.")
        cards.append(player.hand[index - 1])
    return cards


def _human_turn(game: CanastaGame, player: CanastaPlayer) -> None:
    """Conduct a turn for the human-controlled player."""

    print(ASCIIArt.banner(f"{player.name}'s turn", color=THEME.primary))
    _display_hand(player)

    if game.can_take_discard(player):
        draw_choice = input("Draw from (S)tock or (D)iscard pile? ").strip().lower()
        source = DrawSource.DISCARD if draw_choice.startswith("d") else DrawSource.STOCK
    else:
        print("Discard pile is frozen or unavailable; drawing from stock.")
        source = DrawSource.STOCK

    drawn = game.draw(player, source)
    print(f"You draw {drawn}.")

    while True:
        indices = _prompt_indices("Enter card numbers to meld (or press Enter to skip): ")
        if not indices:
            break
        try:
            cards = _collect_cards_by_index(player, indices)
            meld = game.add_meld(player, cards)
            print(f"Meld laid: {_format_hand(meld.cards)}")
        except (IndexError, MeldError) as exc:
            print(f"Could not lay meld: {exc}")
        finally:
            _display_hand(player)

    if not player.hand:
        print("All cards used in melds; skipping discard phase.")
        return

    while True:
        try:
            discard_index = _prompt_indices("Choose a card to discard: ")
            if not discard_index:
                print("A discard is required each turn.")
                continue
            card_to_discard = _collect_cards_by_index(player, [discard_index[0]])[0]
            game.discard(player, card_to_discard)
            print(f"Discarded {card_to_discard}.")
            break
        except (IndexError, ValueError) as exc:
            print(f"Invalid discard: {exc}")

    if not player.hand and game.can_go_out(player.team_index):
        choice = input("Go out and end the round? (y/N): ").strip().lower()
        if choice.startswith("y"):
            breakdown = game.go_out(player)
            _print_round_results(game, breakdown)


def _print_round_results(game: CanastaGame, breakdown: dict[int, int]) -> None:
    """Display round scoring details."""

    print(ASCIIArt.banner("Round complete", color=THEME.secondary))
    for team_index, team in enumerate(game.teams):
        meld_points = game.calculate_team_meld_points(team_index)
        deadwood = game.calculate_team_deadwood(team_index)
        print(
            f"{team.name}: meld {meld_points} – deadwood {deadwood} + delta {breakdown[team_index]} (total {team.score})"
        )


def main() -> None:
    """Launch the interactive Canasta session."""

    print(ASCIIArt.banner("Welcome to Canasta", color=THEME.primary))
    human_name = input("Enter your name: ").strip() or "You"

    players = [
        CanastaPlayer(name=human_name, team_index=0, is_ai=False),
        CanastaPlayer(name="AI East", team_index=1, is_ai=True),
        CanastaPlayer(name="Partner", team_index=0, is_ai=True),
        CanastaPlayer(name="AI West", team_index=1, is_ai=True),
    ]
    game = CanastaGame(players)

    while not game.round_over:
        player = game.players[game.current_player_index]
        if player.is_ai:
            _take_ai_turn(game, player)
        else:
            _human_turn(game, player)
            if game.round_over:
                break
        game.advance_turn()

    if not game.round_over:
        breakdown = {idx: 0 for idx in range(len(game.teams))}
        _print_round_results(game, breakdown)


if __name__ == "__main__":  # pragma: no cover - manual entry point
    main()
