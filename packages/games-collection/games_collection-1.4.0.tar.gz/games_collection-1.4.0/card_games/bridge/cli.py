"""Command-line interface for Bridge."""

from __future__ import annotations

import random
from typing import Optional

from card_games.bridge.game import AuctionState, BidSuit, BridgeGame, BridgePlayer, Call, CallType, Vulnerability
from card_games.common.cards import Card, format_cards, parse_card

SUIT_SYMBOLS = {
    BidSuit.CLUBS: "♣",
    BidSuit.DIAMONDS: "♦",
    BidSuit.HEARTS: "♥",
    BidSuit.SPADES: "♠",
    BidSuit.NO_TRUMP: "NT",
}


def display_hand(player: BridgePlayer) -> None:
    """Display a player's hand.

    Args:
        player: The player whose hand should be printed.
    """

    print(f"\n{player.name} ({player.position}): {format_cards(player.hand)}")


def _show_bidding_history(history: list[Call]) -> None:
    """Print the current auction for review."""

    if not history:
        print("No calls yet.")
        return
    for call in history:
        line = format_call(call)
        if call.explanation:
            line += f" [{call.explanation}]"
        print(f"  {line}")


def _parse_call_input(token: str, legal_calls: list[Call]) -> Optional[Call]:
    """Translate ``token`` into a matching call from ``legal_calls``."""

    token = token.strip().upper()
    if not token:
        return None
    if token.isdigit():
        index = int(token) - 1
        if 0 <= index < len(legal_calls):
            return legal_calls[index]
        return None

    mapping = {
        "P": CallType.PASS,
        "PASS": CallType.PASS,
        "X": CallType.DOUBLE,
        "DOUBLE": CallType.DOUBLE,
        "XX": CallType.REDOUBLE,
        "REDOUBLE": CallType.REDOUBLE,
    }
    if token in mapping:
        target_type = mapping[token]
        for option in legal_calls:
            if option.call_type == target_type:
                return option
        return None

    level_part = ""
    suit_part = ""
    for char in token:
        if char.isdigit():
            level_part += char
        else:
            suit_part += char
    if not level_part or not suit_part:
        return None
    try:
        level = int(level_part)
    except ValueError:
        return None
    suit_part = suit_part.replace("NT", "N")
    suit_lookup = {
        "C": BidSuit.CLUBS,
        "D": BidSuit.DIAMONDS,
        "H": BidSuit.HEARTS,
        "S": BidSuit.SPADES,
        "N": BidSuit.NO_TRUMP,
    }
    suit_key = suit_lookup.get(suit_part)
    if suit_key is None:
        return None
    for option in legal_calls:
        if option.call_type == CallType.BID and option.bid is not None:
            if option.bid.level == level and option.bid.suit == suit_key:
                return option
    return None


def _prompt_human_call(
    game: BridgeGame,
    player: BridgePlayer,
    legal_calls: list[Call],
    history: list[Call],
    state: AuctionState,
) -> Call:
    """Prompt the human player to select a bidding call."""

    while True:
        display_hand(player)
        print("\nLegal calls:")
        for index, option in enumerate(legal_calls, start=1):
            entry = format_call(option)
            if option.forced:
                entry += " (forced)"
            print(f"  {index}. {entry}")

        print("Type a bid (e.g. 2H, 3NT), X, XX, PASS, a number, 'history', or 'suggest'.")
        choice = input("Your call: ").strip()
        if not choice:
            continue
        lowered = choice.lower()
        if lowered in {"history", "h"}:
            _show_bidding_history(history)
            continue
        if lowered in {"suggest", "s"}:
            suggestion = game.bidding_helper.choose_call(player, legal_calls, history.copy(), state)
            print(f"Suggested call: {format_call(suggestion)}")
            if suggestion.explanation:
                print(f"Explanation: {suggestion.explanation}")
            continue

        matched = _parse_call_input(choice, legal_calls)
        if matched is None:
            print("Input did not match any legal call. Try again.")
            continue
        return matched


def _prompt_card_selection(
    game: BridgeGame,
    acting_player: BridgePlayer,
    controller: BridgePlayer,
) -> Optional[Card]:
    """Prompt the controlling human for a card to play."""

    while True:
        display_hand(acting_player)
        print("\nCurrent trick:")
        if not game.current_trick:
            print("  (empty)")
        else:
            for played_player, played_card in game.current_trick:
                print(f"  {played_player.position}: {played_card}")

        valid_cards = game.get_valid_plays(acting_player)
        print(f"\nValid cards: {format_cards(valid_cards)}")
        print("Commands: enter a card code (e.g. AS), 'history', or 'claim N'.")
        choice = input("Play: ").strip()
        if not choice:
            continue
        lowered = choice.lower()
        if lowered in {"history", "h"}:
            summary = game.trick_history_summary()
            if not summary:
                print("No completed tricks yet.")
            else:
                for line in summary:
                    print(f"  {line}")
            continue
        if lowered.startswith("claim"):
            parts = lowered.split()
            if len(parts) != 2 or not parts[1].isdigit():
                print("Usage: claim <number>")
                continue
            tricks = int(parts[1])
            if game.claim_tricks(controller, tricks):
                print(f"Claim accepted for {tricks} tricks.")
                return None
            print("Claim rejected. Ensure the number is valid and no trick is in progress.")
            continue
        try:
            card = parse_card(choice.upper())
        except (ValueError, KeyError):
            print("Invalid card identifier.")
            continue
        if card not in valid_cards:
            print("That card cannot be played right now.")
            continue
        return card


def format_call(call: Call) -> str:
    """Return a printable representation of ``call``."""

    if call.call_type == CallType.BID and call.bid is not None:
        return f"{call.player.position}: {call.bid.level}{SUIT_SYMBOLS[call.bid.suit]}"
    if call.call_type == CallType.DOUBLE:
        return f"{call.player.position}: X"
    if call.call_type == CallType.REDOUBLE:
        return f"{call.player.position}: XX"
    message = f"{call.player.position}: Pass"
    if call.forced:
        message += " (forced)"
    return message


def game_loop() -> None:
    """Run the interactive loop for a single bridge deal."""

    print("\nWELCOME TO BRIDGE")
    print("=" * 60)
    print("Contract Bridge with realistic bidding, vulnerability, and scoring.")
    print("=" * 60)

    player_name = input("\nEnter your name (you are South): ").strip() or "Player"

    players = [
        BridgePlayer(name="North AI", is_ai=True),
        BridgePlayer(name="East AI", is_ai=True),
        BridgePlayer(name=f"South {player_name}", is_ai=False),
        BridgePlayer(name="West AI", is_ai=True),
    ]

    vulnerability = random.choice(list(Vulnerability))
    game = BridgeGame(players, vulnerability=vulnerability)

    print("\n" + "=" * 60)
    print("DEALING CARDS")
    print("=" * 60)
    print(f"Vulnerability: {game.vulnerability.value}")

    game.deal_cards()

    for player in players:
        if not player.is_ai:
            display_hand(player)
            hcp = game.evaluate_hand(player)
            print(f"High Card Points: {hcp}")

    print("\n" + "=" * 60)
    print("BIDDING PHASE")
    print("=" * 60)
    print("(Type commands during bidding to participate.)")

    def select_call(
        player: BridgePlayer,
        legal_calls: list[Call],
        history: list[Call],
        state: AuctionState,
    ) -> Call:
        if player.is_ai:
            chosen = game.bidding_helper.choose_call(player, legal_calls, history.copy(), state)
            call_text = format_call(chosen)
            if chosen.explanation:
                call_text += f" [{chosen.explanation}]"
            print(f"{player.position} ({player.name}) chooses {call_text}")
            return chosen
        return _prompt_human_call(game, player, legal_calls, history, state)

    contract = game.conduct_bidding(call_selector=select_call)

    if contract is None:
        print("\nAll players passed. No contract for this deal.")
        return

    print("\nBidding sequence:")
    for call in game.bidding_history:
        entry = format_call(call)
        if call.explanation:
            entry += f" [{call.explanation}]"
        print(f"  {entry}")

    declarer = contract.declarer
    dummy = game.players[declarer.partner_index]
    contract_str = f"{contract.bid.level}{SUIT_SYMBOLS[contract.bid.suit]}"
    if contract.doubled:
        contract_str += " X"
    if contract.redoubled:
        contract_str += " XX"

    print(f"\nContract: {contract_str} by {declarer.name} ({declarer.position})")
    print(f"Dummy: {dummy.name} ({dummy.position})")

    print("\n" + "=" * 60)
    print("PLAYING PHASE")
    print("=" * 60)

    opening_leader_index = game.starting_player_index()
    current_player_idx = opening_leader_index
    dummy_revealed = False

    while not game.hand_complete and len(game.trick_history) < 13:
        if not game.current_trick:
            trick_number = len(game.trick_history) + 1
            print(f"\n--- Trick {trick_number} ---")

        player = game.players[current_player_idx]
        if not player.hand:
            # No cards to play (likely after a claim).
            break

        controller = player
        if contract is not None:
            declarer = contract.declarer
            dummy = game.players[declarer.partner_index]
            if player == dummy:
                controller = declarer
        if controller.is_ai:
            card = game.select_card_to_play(player)
        else:
            selection = _prompt_card_selection(game, player, controller)
            if selection is None:
                if game.hand_complete:
                    break
                continue
            card = selection

        game.play_card(player, card)
        print(f"{player.position} plays {card}")

        if not dummy_revealed and game.players.index(player) == opening_leader_index:
            dummy_revealed = True
            dummy = game.players[contract.declarer.partner_index]
            if dummy.is_ai:
                display_hand(dummy)

        if len(game.current_trick) == 4:
            winner = game.complete_trick()
            print(f"{winner.position} wins the trick")
            current_player_idx = game.players.index(winner)
        else:
            current_player_idx = (current_player_idx + 1) % 4

        if game.hand_complete:
            break

    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)

    partner = game.players[declarer.partner_index]
    declarer_tricks = declarer.tricks_won + partner.tricks_won
    defender_tricks = 13 - declarer_tricks

    print(f"\nDeclarer partnership ({declarer.position}-{partner.position}): {declarer_tricks} tricks")
    print(f"Defender partnership: {defender_tricks} tricks")

    required = 6 + contract.bid.level
    print(f"\nContract required: {required} tricks")

    scores = game.calculate_score()
    if declarer_tricks >= required:
        print(f"✓ Contract MADE by {declarer.position}")
    else:
        print("✗ Contract FAILED")

    print(
        "Score summary - North/South: {north_south} | East/West: {east_west}".format(
            **scores,
        )
    )
