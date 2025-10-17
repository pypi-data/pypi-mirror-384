"""Command-line interface for playing Rummy 500."""

from __future__ import annotations

from typing import Iterable, Sequence

from card_games.common.cards import RANK_TO_VALUE, Card, parse_card
from card_games.rummy500.ai import DrawDecision, Rummy500AI
from card_games.rummy500.game import GamePhase, Rummy500Game

SUIT_SYMBOL_TO_CODE = {"♣": "C", "♦": "D", "♥": "H", "♠": "S"}


def card_value(card: Card) -> int:
    """Return the scoring value for *card*."""

    if card.rank == "A":
        return 15
    if card.rank in {"K", "Q", "J", "T"}:
        return 10
    return int(card.rank)


def sort_cards(cards: Iterable[Card]) -> list[Card]:
    """Return cards sorted by rank then suit."""

    return sorted(cards, key=lambda c: (RANK_TO_VALUE[c.rank], c.suit.value))


def card_to_code(card: Card) -> str:
    """Return a two-character code for *card* (e.g., ``AS``)."""

    return f"{card.rank}{SUIT_SYMBOL_TO_CODE[card.suit.value]}"


def format_cards_with_codes(cards: Sequence[Card]) -> str:
    """Return cards formatted with both codes and suit symbols."""

    if not cards:
        return "—"
    return " ".join(f"{card_to_code(card)}({card})" for card in sort_cards(cards))


def display_game_state(game: Rummy500Game) -> None:
    """Display high-level game information."""

    state = game.get_state_summary()
    print("\n" + "=" * 72)
    print(f"RUMMY 500 - {state['phase']}")
    print("=" * 72)
    for i, score in enumerate(state["scores"]):
        marker = " <--" if i == state["current_player"] else ""
        print(f"Player {i}: {score} points ({state['hand_sizes'][i]} cards){marker}")

    if game.discard_pile:
        visible = " ".join(str(card) for card in game.discard_pile[-7:])
        if len(game.discard_pile) > 7:
            visible = "… " + visible
        print(f"Discard pile (top on right): {visible}")
    else:
        print("Discard pile is empty")

    print(f"Deck: {state['deck_size']} cards remaining")

    if state["melds"]:
        print("\nTable melds:")
        for index, meld in enumerate(state["melds"]):
            cards = " ".join(meld["cards"])
            contributors = ", ".join(f"P{player}: {' '.join(cards)}" for player, cards in meld["contributors"].items())
            print(f"  [{index}] Player {meld['owner']}: {cards}")
            if contributors:
                print(f"       Contributions -> {contributors}")

    print("=" * 72)


def show_deadwood_summary(summary: dict[str, object]) -> None:
    """Pretty-print a deadwood summary returned by the game engine."""

    meld_points = summary["meld_points"]
    deadwood_points = summary["deadwood_points"]
    net_points = summary["net_points"]
    print(f"  Meld points: {meld_points} | Deadwood: {deadwood_points} | Net: {net_points}")

    melds: list[list[Card]] = summary.get("melds", [])  # type: ignore[assignment]
    if melds:
        print("  Best melds:")
        for meld in melds:
            print(f"    - {format_cards_with_codes(meld)}")
    else:
        print("  No melds available yet")

    deadwood_cards: list[Card] = summary.get("deadwood", [])  # type: ignore[assignment]
    if deadwood_cards:
        print(f"  Deadwood cards: {format_cards_with_codes(deadwood_cards)}")


def show_discard_pile(game: Rummy500Game) -> None:
    """Display the entire discard pile for reference."""

    if not game.discard_pile:
        print("Discard pile is empty.")
        return

    print("Discard pile (top on right):")
    print("  " + " ".join(str(card) for card in game.discard_pile))


def parse_cards_from_input(text: str, available: Sequence[Card]) -> list[Card] | None:
    """Convert a user string into concrete cards from *available*."""

    tokens = [token.upper() for token in text.replace(",", " ").split() if token]
    if not tokens:
        return []

    try:
        desired = [parse_card(token) for token in tokens]
    except ValueError:
        print("  Invalid card code. Use format like 'AS' for Ace of Spades.")
        return None

    remaining = list(available)
    resolved: list[Card] = []
    for wanted in desired:
        for idx, candidate in enumerate(remaining):
            if candidate == wanted:
                resolved.append(candidate)
                remaining.pop(idx)
                break
        else:
            print(f"  You do not have {card_to_code(wanted)} available.")
            return None

    return resolved


def request_cards(
    prompt: str,
    available: Sequence[Card],
    *,
    minimum: int = 1,
    allow_empty: bool = False,
) -> list[Card] | None:
    """Prompt the user for cards, validating against *available*."""

    while True:
        raw = input(prompt).strip()
        if not raw:
            if allow_empty:
                return []
            print("  Please enter card codes (e.g., 'AS KD 3C').")
            continue

        cards = parse_cards_from_input(raw, available)
        if cards is None:
            continue

        if not cards and not allow_empty:
            print("  Please enter at least one card.")
            continue

        if cards and len(cards) < minimum:
            print(f"  Please enter at least {minimum} cards.")
            continue

        return cards


def human_draw(game: Rummy500Game) -> None:
    """Handle the draw phase for the human player."""

    player = game.current_player
    assert player == 0

    while True:
        choice = input("Draw from (d)eck or (p)ile? [d]: ").strip().lower()
        if choice in {"p", "pile"}:
            if not game.discard_pile:
                print("  The discard pile is empty. Drawing from deck instead.")
                choice = "d"
            else:
                try:
                    max_take = len(game.discard_pile)
                    take_str = input(f"  How many cards from discard? [1-{max_take}]: ").strip()
                    take_count = int(take_str) if take_str else 1
                except ValueError:
                    print("  Please enter a number.")
                    continue

                if take_count < 1 or take_count > max_take:
                    print("  That many cards aren't available from the discard pile.")
                    continue

                if game.draw_card(from_discard=True, take_count=take_count):
                    taken = " ".join(str(card) for card in game.hands[player][-take_count:])
                    print(f"  You take from discard: {taken}")
                    break

                print("  You must be able to use the top discard in a meld immediately.")
                continue

        if choice in {"", "d", "deck"}:
            if game.draw_card():
                print("  You draw from the deck.")
                break
            print("  Deck empty! Try drawing from the discard pile.")
        else:
            print("  Please choose 'd' for deck or 'p' for discard pile.")


def show_table_melds(game: Rummy500Game) -> None:
    """Display current table melds with indices."""

    state = game.get_state_summary()
    if not state["melds"]:
        print("There are no melds on the table yet.")
        return

    print("Table melds:")
    for index, meld in enumerate(state["melds"]):
        cards = " ".join(meld["cards"])
        contributors = ", ".join(f"P{player}: {' '.join(cards)}" for player, cards in meld["contributors"].items())
        print(f"  [{index}] Player {meld['owner']}: {cards}")
        if contributors:
            print(f"       Contributions -> {contributors}")


def human_meld_phase(game: Rummy500Game) -> None:
    """Allow the human player to form melds, lay off, and discard."""

    player = game.current_player
    assert player == 0

    while game.phase == GamePhase.MELD and game.current_player == player:
        hand = sort_cards(game.hands[player])
        print(f"\nYour hand: {format_cards_with_codes(hand)}")
        summary = game.get_deadwood_summary(player)
        show_deadwood_summary(summary)

        if not game.hands[player]:
            choice = input("You have no cards. Go (o)ut? [o]: ").strip().lower()
            if choice in {"", "o", "out"}:
                if game.go_out(player):
                    print("You go out!")
                else:
                    print("Unable to go out right now.")
                return
            continue

        print("Options: (m)eld  (l)ay off  (v)iew discard  (d)iscard  (o)ut")
        choice = input("Select action: ").strip().lower()

        if choice in {"v", "view"}:
            show_discard_pile(game)
            continue

        if choice in {"o", "out"}:
            if game.go_out(player):
                print("You go out!")
            else:
                print("You still have cards or cannot go out yet.")
            return

        if choice in {"m", "meld"}:
            cards = request_cards(
                "  Enter cards for meld (e.g., 'AS KD QD'). Leave blank to cancel: ",
                game.hands[player],
                minimum=3,
                allow_empty=True,
            )
            if cards == []:
                continue
            if cards is None or len(cards) < 3:
                continue
            if not game.is_valid_meld(cards):
                print("  Those cards do not form a valid meld.")
                continue

            preview = game.preview_after_cards(player, cards)
            print("  Preview after laying meld:")
            show_deadwood_summary(preview)
            confirm = input("  Lay this meld? [y/N]: ").strip().lower()
            if confirm in {"y", "yes"}:
                if game.lay_meld(player, cards):
                    print(f"  Meld laid: {format_cards_with_codes(cards)}")
                else:
                    print("  Unable to lay that meld right now.")
            continue

        if choice in {"l", "lay", "layoff"}:
            if not game.melds:
                print("  No melds on the table to lay off onto.")
                continue
            show_table_melds(game)
            try:
                index = int(input("  Choose meld index: ").strip())
            except ValueError:
                print("  Please enter a valid number.")
                continue

            if index < 0 or index >= len(game.melds):
                print("  Invalid meld index.")
                continue

            cards = request_cards(
                "  Enter cards to lay off. Leave blank to cancel: ",
                game.hands[player],
                minimum=1,
                allow_empty=True,
            )
            if cards == []:
                continue
            if cards is None:
                continue
            if not game.can_lay_off(index, cards):
                print("  Those cards cannot be added to that meld.")
                continue

            preview = game.preview_after_cards(player, cards)
            gained = sum(card_value(card) for card in cards if game.melds[index].owner == player)
            print("  Preview after laying off:")
            show_deadwood_summary(preview)
            if gained:
                print(f"  Additional meld points this round: +{gained}")
            confirm = input("  Commit layoff? [y/N]: ").strip().lower()
            if confirm in {"y", "yes"}:
                if game.lay_off(player, index, cards):
                    print(f"  Laid off {format_cards_with_codes(cards)} onto meld {index}")
                else:
                    print("  Unable to lay off those cards right now.")
            continue

        if choice in {"", "d", "discard"}:
            break

        print("  Unknown option. Please choose again.")

    if game.phase != GamePhase.MELD or game.current_player != player:
        return

    if not game.hands[player]:
        if game.go_out(player):
            print("You go out!")
        return

    while True:
        print(f"\nYour hand: {format_cards_with_codes(game.hands[player])}")
        raw = input("Select card to discard (e.g., 'AS') or 'p' to preview: ").strip()
        if raw.lower() in {"p", "preview"}:
            summary = game.get_deadwood_summary(player)
            show_deadwood_summary(summary)
            continue

        cards = parse_cards_from_input(raw, game.hands[player])
        if cards is None:
            continue
        if len(cards) != 1:
            print("  Please choose exactly one card to discard.")
            continue

        card = cards[0]
        preview = game.preview_after_cards(player, [card])
        print("  Preview after discarding:")
        show_deadwood_summary(preview)
        confirm = input(f"  Discard {card_to_code(card)} ({card})? [Y/n]: ").strip().lower()
        if confirm in {"", "y", "yes"}:
            game.discard(player, card)
            print(f"  You discard {card}")
            break


def game_loop(game: Rummy500Game) -> None:
    """Main game loop for the interactive CLI."""

    print("\n🃏 Welcome to Rummy 500! 🃏")
    print(f"{game.num_players} players - First to 500 points wins!")
    print("Use two-character codes for cards (rank + suit letter, e.g., 'AS' for Ace of Spades).\n")

    ai_players = {index: Rummy500AI(index) for index in range(1, game.num_players)}

    while game.phase != GamePhase.GAME_OVER:
        display_game_state(game)
        player = game.current_player

        if game.phase == GamePhase.DRAW:
            if player == 0:
                human_draw(game)
            else:
                ai = ai_players[player]
                decision: DrawDecision = ai.choose_draw(game)
                if decision.from_discard:
                    game.draw_card(from_discard=True, take_count=decision.take_count)
                    print(f"Player {player} draws {decision.take_count} card(s) from the discard pile")
                else:
                    drew_from_deck = game.draw_card()
                    if drew_from_deck:
                        print(f"Player {player} draws from the deck")
                    else:
                        forced = False
                        if game.discard_pile:
                            forced = game.draw_card(from_discard=True, take_count=1)
                        if forced:
                            print(f"Player {player} draws the top discard because the deck is empty.")
                        else:
                            print("No cards are available to draw. Ending the round due to an empty stock.")
                            game.end_round_due_to_empty_stock()
                            continue

        if game.phase == GamePhase.MELD and game.phase != GamePhase.GAME_OVER:
            player = game.current_player
            if player == 0:
                human_meld_phase(game)
            else:
                ai = ai_players[player]
                went_out = ai.perform_melds_and_layoffs(game)
                if went_out:
                    print(f"Player {player} goes out!")
                    continue

                if game.phase != GamePhase.MELD or game.current_player != player:
                    continue

                discard_card = ai.choose_discard(game)
                game.discard(player, discard_card)
                print(f"Player {player} discards {discard_card}")

    state = game.get_state_summary()
    print("\n" + "=" * 72)
    print("GAME OVER")
    print("=" * 72)
    print(f"🎉 Player {state['winner']} wins!")
    print("\nFinal Scores:")
    for i, score in enumerate(state["scores"]):
        print(f"  Player {i}: {score} points")
    print("=" * 72)
