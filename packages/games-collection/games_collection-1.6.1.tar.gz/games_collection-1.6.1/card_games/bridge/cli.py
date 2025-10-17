"""Command-line interface for the Contract Bridge game.

This module provides the functions to run a game of Contract Bridge in the
terminal, handling user input for bidding and card play, and rendering the
game state to the console.
"""

from __future__ import annotations

import random
from typing import Optional

from card_games.bridge.game import (
    AuctionState,
    BidSuit,
    BridgeGame,
    BridgePlayer,
    Call,
    CallType,
    Vulnerability,
)
from card_games.common.cards import Card, format_cards, parse_card

SUIT_SYMBOLS = {
    BidSuit.CLUBS: "♣",
    BidSuit.DIAMONDS: "♦",
    BidSuit.HEARTS: "♥",
    BidSuit.SPADES: "♠",
    BidSuit.NO_TRUMP: "NT",
}


def display_hand(player: BridgePlayer) -> None:
    """Display a player's hand in a formatted way.

    Args:
        player: The player whose hand is to be displayed.
    """
    print(f"\n{player.name} ({player.position}): {format_cards(player.hand)}")


def _show_bidding_history(history: list[Call]) -> None:
    """Print the bidding history for review."""
    if not history:
        print("No calls have been made yet.")
        return
    for call in history:
        line = format_call(call)
        if call.explanation:
            line += f" [{call.explanation}]"
        print(f"  {line}")


def _parse_call_input(token: str, legal_calls: list[Call]) -> Optional[Call]:
    """Translate a string token into a matching legal call."""
    token = token.strip().upper()
    if not token:
        return None

    if token.isdigit():
        index = int(token) - 1
        if 0 <= index < len(legal_calls):
            return legal_calls[index]
        return None

    call_type_map = {
        "P": CallType.PASS,
        "PASS": CallType.PASS,
        "X": CallType.DOUBLE,
        "DOUBLE": CallType.DOUBLE,
        "XX": CallType.REDOUBLE,
        "REDOUBLE": CallType.REDOUBLE,
    }
    if call_type := call_type_map.get(token):
        return next((c for c in legal_calls if c.call_type == call_type), None)

    level_part = "".join(filter(str.isdigit, token))
    suit_part = "".join(filter(str.isalpha, token)).replace("NT", "N")
    if not level_part or not suit_part:
        return None

    try:
        level = int(level_part)
        suit_map = {"C": BidSuit.CLUBS, "D": BidSuit.DIAMONDS, "H": BidSuit.HEARTS, "S": BidSuit.SPADES, "N": BidSuit.NO_TRUMP}
        suit = suit_map.get(suit_part)
        if suit:
            return next((c for c in legal_calls if c.call_type == CallType.BID and c.bid and c.bid.level == level and c.bid.suit == suit), None)
    except ValueError:
        return None
    return None


def _prompt_human_call(game: BridgeGame, player: BridgePlayer, legal_calls: list[Call], history: list[Call], state: AuctionState) -> Call:
    """Prompt the human player to select a bidding call."""
    while True:
        display_hand(player)
        print("\nLegal calls:")
        for i, option in enumerate(legal_calls, 1):
            print(f"  {i}. {format_call(option)}{' (forced)' if option.forced else ''}")

        print("\nType a bid (e.g., '1H', '3NT'), 'X', 'P', or a number.")
        choice = input("Your call: ").strip().lower()

        if choice in {"history", "h"}:
            _show_bidding_history(history)
        elif choice in {"suggest", "s"}:
            suggestion = game.bidding_helper.choose_call(player, legal_calls, history, state)
            print(f"Suggested call: {format_call(suggestion)}")
            if suggestion.explanation:
                print(f"  Explanation: {suggestion.explanation}")
        elif matched := _parse_call_input(choice, legal_calls):
            return matched
        else:
            print("Invalid input. Please try again.")


def _prompt_card_selection(game: BridgeGame, acting_player: BridgePlayer, controller: BridgePlayer) -> Optional[Card]:
    """Prompt the controlling human player for a card to play."""
    while True:
        display_hand(acting_player)
        print("\nCurrent trick:")
        if game.current_trick:
            for p, card in game.current_trick:
                print(f"  {p.position}: {card}")
        else:
            print("  (No cards played yet)")

        valid_cards = game.get_valid_plays(acting_player)
        print(f"\nValid cards: {format_cards(valid_cards)}")
        choice = input("Play a card (e.g., 'AS') or 'claim N': ").strip().lower()

        if choice.startswith("claim"):
            try:
                tricks = int(choice.split()[1])
                if game.claim_tricks(controller, tricks):
                    print(f"Claim for {tricks} tricks accepted.")
                    return None
                print("Claim rejected.")
            except (ValueError, IndexError):
                print("Invalid claim format. Use 'claim <number>'.")
        else:
            try:
                card = parse_card(choice.upper())
                if card in valid_cards:
                    return card
                print("That card cannot be played right now.")
            except (ValueError, KeyError):
                print("Invalid card identifier.")


def format_call(call: Call) -> str:
    """Return a printable representation of a call."""
    if call.call_type == CallType.BID and call.bid:
        return f"{call.player.position}: {call.bid.level}{SUIT_SYMBOLS[call.bid.suit]}"
    if call.call_type == CallType.DOUBLE:
        return f"{call.player.position}: X"
    if call.call_type == CallType.REDOUBLE:
        return f"{call.player.position}: XX"
    return f"{call.player.position}: Pass{' (forced)' if call.forced else ''}"


def game_loop() -> None:
    """Run the interactive loop for a single deal of Bridge."""
    print("\n--- Welcome to Contract Bridge ---")
    player_name = input("Enter your name (you are South): ").strip() or "Player"
    players = [
        BridgePlayer(name="North (AI)", is_ai=True),
        BridgePlayer(name="East (AI)", is_ai=True),
        BridgePlayer(name=f"South ({player_name})", is_ai=False),
        BridgePlayer(name="West (AI)", is_ai=True),
    ]
    game = BridgeGame(players, vulnerability=random.choice(list(Vulnerability)))
    game.deal_cards()

    print(f"\nVulnerability: {game.vulnerability.value}")
    for player in players:
        if not player.is_ai:
            display_hand(player)
            print(f"High Card Points: {game.evaluate_hand(player)}")

    print("\n--- Bidding Phase ---")
    contract = game.conduct_bidding(
        call_selector=lambda p, lc, h, s: _prompt_human_call(game, p, lc, h, s) if not p.is_ai else game.bidding_helper.choose_call(p, lc, h, s)
    )

    if not contract:
        print("\nAll players passed. The hand is passed out.")
        return

    print("\n--- Bidding Summary ---")
    _show_bidding_history(game.bidding_history)
    declarer, dummy = contract.declarer, game.players[contract.declarer.partner_index]
    print(f"\nContract: {contract.bid} by {declarer.name}")
    print(f"Dummy: {dummy.name}")

    print("\n--- Playing Phase ---")
    while not game.hand_complete and len(game.trick_history) < 13:
        if not game.current_trick:
            print(f"\n--- Trick {len(game.trick_history) + 1} ---")

        player = game.players[game.current_player_index]
        controller = dummy if player == dummy else player

        if controller.is_ai:
            card = game.select_card_to_play(player)
        else:
            card = _prompt_card_selection(game, player, controller)
            if card is None:
                break

        game.play_card(player, card)
        print(f"{player.position} plays {card}")

        if len(game.current_trick) == 4:
            winner = game.complete_trick()
            print(f"--> {winner.position} wins the trick.")

    print("\n--- Results ---")
    declarer_tricks = sum(p.tricks_won for p in game.partnership_for(declarer))
    print(f"Declarer tricks: {declarer_tricks}")
    print(f"Contract required: {6 + contract.bid.level}")

    scores = game.calculate_score()
    print("Contract " + ("MADE" if declarer_tricks >= 6 + contract.bid.level else "FAILED"))
    print(f"Score: N/S {scores['north_south']}, E/W {scores['east_west']}")
