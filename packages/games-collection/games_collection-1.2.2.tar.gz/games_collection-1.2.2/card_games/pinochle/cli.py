"""Command line helpers for playing partnership double-deck Pinochle."""

from __future__ import annotations

from typing import List, Optional

from card_games.common.cards import Suit, format_cards
from card_games.pinochle.game import BiddingPhase, PinochleGame, PinochlePlayer

SUIT_INPUTS = {
    "s": Suit.SPADES,
    "h": Suit.HEARTS,
    "d": Suit.DIAMONDS,
    "c": Suit.CLUBS,
}


def _prompt(prompt: str) -> str:
    try:
        return input(prompt)
    except EOFError:  # pragma: no cover - safety for non-interactive runs
        return ""


def _prompt_bid(phase: BiddingPhase) -> int | None:
    player = phase.current_player()
    while True:
        raw = _prompt(f"{player.name}, enter your bid (>= {phase.min_bid}) or PASS: ").strip()
        if raw.lower() in {"p", "pass", ""}:
            return None
        try:
            value = int(raw)
        except ValueError:
            print("Please enter a number or PASS.")
            continue
        if value < phase.min_bid:
            print(f"Minimum bid is {phase.min_bid}.")
            continue
        if phase.high_bid is not None and value <= phase.high_bid:
            print(f"Bid must exceed {phase.high_bid}.")
            continue
        return value


def _prompt_trump(winner: PinochlePlayer) -> Suit:
    while True:
        choice = _prompt(f"{winner.name}, choose trump suit (S, H, D, C): ").strip().lower()
        if choice in SUIT_INPUTS:
            return SUIT_INPUTS[choice]
        print("Invalid suit. Use S, H, D, or C.")


def _choose_card(game: PinochleGame, player: PinochlePlayer) -> int:
    print(f"\n{player.name}'s turn")
    print(f"Current hand: {format_cards(player.hand)}")
    print("Playable cards:")
    for index, card in enumerate(player.hand, start=1):
        marker = ""
        if game.lead_suit and card.suit == game.lead_suit:
            marker = "*"
        print(f"  {index:2d}: {card}{marker}")
    print()
    while True:
        choice = _prompt("Select card number: ").strip()
        try:
            idx = int(choice) - 1
        except ValueError:
            print("Enter the number shown beside the card.")
            continue
        if idx < 0 or idx >= len(player.hand):
            print("That card number is not available.")
            continue
        card = player.hand[idx]
        if not game.is_valid_play(player, card):
            print("You must follow suit when able. Choose another card.")
            continue
        return idx


def _play_tricks(game: PinochleGame) -> None:
    while any(player.hand for player in game.players):
        player = game.players[game.current_player_index]  # type: ignore[index]
        choice = _choose_card(game, player)
        card = player.hand[choice]
        print(f"{player.name} plays {card}")
        game.play_card(card)
        if len(game.current_trick) == len(game.players):
            winner = game.complete_trick()
            print(f"Trick won by {winner.name}")
            print(f"Trick cards: {game.format_trick(game.trick_history[-1])}\n")
    print("All tricks complete.\n")


def _display_melds(game: PinochleGame) -> None:
    print("\nMeld results:")
    for player in game.players:
        breakdown = game.meld_breakdowns.get(player.name, {})
        pieces = ", ".join(f"{key.replace('_', ' ')}: {value}" for key, value in breakdown.items())
        if not pieces:
            pieces = "no meld"
        print(f"  {player.name}: {player.meld_points} points ({pieces})")


def main(names: Optional[List[str]] = None) -> None:
    """Run an interactive Pinochle round."""

    print("Welcome to double-deck Pinochle!\n")
    player_names: List[str] = []
    supplied = list(names or [])
    for idx in range(4):
        if idx < len(supplied) and supplied[idx]:
            entered = supplied[idx]
        else:
            entered = _prompt(f"Enter name for player {idx + 1}: ").strip() or f"Player {idx + 1}"
        player_names.append(entered)
    players = [PinochlePlayer(name=name) for name in player_names]
    game = PinochleGame(players)

    game.shuffle_and_deal()
    game.start_bidding()

    print("Bidding begins.\n")
    while not game.bidding_phase or not game.bidding_phase.finished:
        phase = game.bidding_phase
        assert phase is not None
        player = phase.current_player()
        result = _prompt_bid(phase)
        if result is None:
            phase.place_bid(None)
            print(f"{player.name} passes.")
        else:
            phase.place_bid(result)
            print(f"{player.name} bids {result}.")
        if phase.finished:
            break
    phase = game.bidding_phase
    assert phase is not None
    winner = phase.high_bidder
    assert winner is not None
    print(f"\n{winner.name} wins the bid at {phase.high_bid}.")

    trump = _prompt_trump(winner)
    game.set_trump(trump)
    print(f"Trump suit is {trump.name.title()}.\n")

    game.score_melds()
    _display_melds(game)

    print("\nTrick play begins. Follow suit whenever possible.\n")
    _play_tricks(game)

    results = game.resolve_round()
    print("Round totals:")
    for team, values in results.items():
        print(f"  Team {team + 1} - Meld: {values['meld']} Trick: {values['tricks']} Total: {values['total']}")
    print(f"Partnership scores: Team 1 = {game.partnership_scores[0]}, Team 2 = {game.partnership_scores[1]}")


if __name__ == "__main__":  # pragma: no cover - manual invocation
    main()
