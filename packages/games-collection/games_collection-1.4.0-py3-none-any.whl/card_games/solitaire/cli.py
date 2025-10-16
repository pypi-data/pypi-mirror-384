"""Command-line interface helpers for the Klondike Solitaire engine."""

from __future__ import annotations

from card_games.solitaire.game import SolitaireGame


def display_game(game: SolitaireGame) -> None:
    """Display the current game state.

    Args:
        game: The solitaire game instance.
    """
    print("\n" + "=" * 80)
    print("SOLITAIRE (KLONDIKE)")
    print("=" * 80)

    summary = game.get_state_summary()

    # Stock and Waste
    stock_count = summary["stock"]
    waste_cards = game.waste.cards[-game.draw_count :]
    waste_display = " ".join(str(card) for card in waste_cards[::-1]) if waste_cards else "[]"
    draw_note = f"draw {game.draw_count}" + (
        " (limitless redeals)" if summary["recycles_remaining"] is None else f" ({summary['recycles_remaining']} redeal(s) left)"
    )
    print(f"\nStock: [{stock_count} cards] {draw_note}")
    print(f"Waste: {waste_display}")

    # Foundations
    print("\nFoundations:")
    for i, foundation in enumerate(game.foundations):
        top = foundation.top_card()
        display = str(top) if top else "[_]"
        suit_name = ["♣", "♦", "♥", "♠"][i]
        print(f"  {suit_name}: {display} ({len(foundation.cards)} cards)", end="  ")
    print()

    # Tableau
    print("\nTableau:")
    max_height = max(len(pile.cards) for pile in game.tableau)

    for row in range(max_height):
        line = ""
        for col in range(7):
            pile = game.tableau[col]
            if row < len(pile.cards):
                card = pile.cards[row]
                face_down_count = len(pile.cards) - pile.face_up_count
                if row < face_down_count:
                    line += "[##]  "
                else:
                    line += f"{str(card):4}  "
            else:
                if row == 0 and not pile.cards:
                    line += "[_]   "
                else:
                    line += "      "
        print(f"  {line}")

    print("\n  0     1     2     3     4     5     6")

    # Statistics
    print("\nStats:")
    print(f"  Score: {summary['score']}  Moves: {summary['moves_made']}  Auto moves: {summary['auto_moves']}  " f"Recycles used: {summary['recycles_used']}")


def parse_move(user_input: str, game: SolitaireGame) -> bool:
    """Parse and execute a move command.

    Args:
        user_input: The user's input string.
        game: The solitaire game instance.

    Returns:
        True if a valid move was made, False otherwise.
    """
    parts = user_input.strip().lower().split()

    if not parts:
        return False

    command = parts[0]

    # Draw from stock
    if command in ("d", "draw"):
        before_waste = len(game.waste.cards)
        if game.draw_from_stock():
            drawn = len(game.waste.cards) - before_waste
            drawn_cards = " ".join(str(card) for card in game.waste.cards[-drawn:][::-1])
            print(f"Drew: {drawn_cards}")
            return True
        else:
            if game.can_reset_stock():
                print("Stock is empty. Use 'reset' to flip the waste back onto the stock.")
            else:
                print("No cards left to draw.")
            return False

    # Reset stock
    if command in ("r", "reset"):
        if game.reset_stock():
            print("Reset stock from waste pile.")
            return True
        else:
            if game.waste.cards:
                print("No redeals remaining. Finish the tableau or undo moves from foundations.")
            else:
                print("Waste pile is empty.")
            return False

    # Auto-move to foundation
    if command in ("a", "auto"):
        if game.auto_move_to_foundation():
            print("Moved available cards to the foundations.")
            return True
        else:
            print("No cards can be automatically moved to foundation.")
            return False

    if command in ("s", "stats"):
        summary = game.get_state_summary()
        print(
            "Current stats -> "
            f"Score: {summary['score']} | Moves: {summary['moves_made']} | Auto: {summary['auto_moves']} | "
            f"Recycles used: {summary['recycles_used']}"
        )
        return False

    # Move commands: "w 0" (waste to tableau 0), "0 f" (tableau 0 to foundation)
    if len(parts) >= 2:
        source = parts[0]
        dest = parts[1]

        # Determine source pile
        source_pile = None
        if source == "w":
            source_pile = game.waste
        elif source.isdigit():
            tableau_idx = int(source)
            if 0 <= tableau_idx < 7:
                source_pile = game.tableau[tableau_idx]

        if not source_pile:
            print("Invalid source. Use 'w' for waste or 0-6 for tableau.")
            return False

        # Move to foundation
        if dest == "f":
            for i in range(4):
                if game.move_to_foundation(source_pile, i):
                    print("Moved card to foundation.")
                    return True
            print("Cannot move to any foundation.")
            return False

        # Move to tableau
        if dest.isdigit():
            tableau_idx = int(dest)
            if 0 <= tableau_idx < 7:
                # Determine how many cards to move (for tableau to tableau)
                num_cards = 1
                if len(parts) >= 3 and parts[2].isdigit():
                    num_cards = int(parts[2])

                if game.move_to_tableau(source_pile, tableau_idx, num_cards):
                    print(f"Moved {num_cards} card(s) to tableau {tableau_idx}.")
                    return True
                else:
                    print("Invalid move.")
                    return False

    print("Invalid command.")
    return False


def print_help() -> None:
    """Print help information about available commands."""
    print("\n" + "=" * 80)
    print("COMMANDS")
    print("=" * 80)
    print("  d, draw           - Draw from stock to waste (respecting draw setting)")
    print("  r, reset          - Recycle waste back to stock when allowed")
    print("  a, auto           - Auto-move eligible cards to foundations")
    print("  s, stats          - Show score, move count, and recycle usage")
    print("  w <dest>          - Move waste card (e.g., 'w 0' moves to tableau 0)")
    print("  <src> f           - Move tableau card to foundation (e.g., '0 f')")
    print("  <src> <dest> [n]  - Move n cards from tableau src to dest (e.g., '0 1 3')")
    print("  h, help           - Show this help")
    print("  q, quit           - Quit game")
    print("\nTableau columns are numbered 0-6 from left to right.")
    print("Foundation piles are automatically selected based on card suit.")
    print("Standard scoring: +10 to foundations, +5 flip bonuses, -15 when pulling from foundations.")
    print("Vegas scoring: buy-in of -52 with +5 per card moved to the foundations.")
    print("=" * 80)


def game_loop(game: SolitaireGame) -> None:
    """Main game loop for CLI solitaire.

    Args:
        game: The solitaire game instance.
    """
    print("\nWelcome to Solitaire (Klondike)!")
    print("Type 'help' or 'h' for commands.")

    while True:
        display_game(game)

        if game.is_won():
            print("\n" + "=" * 80)
            print("🎉 CONGRATULATIONS! You won! 🎉")
            print("=" * 80)
            break

        user_input = input("\nYour move: ").strip().lower()

        if user_input in ("q", "quit"):
            print("Thanks for playing!")
            break

        if user_input in ("h", "help"):
            print_help()
            continue

        parse_move(user_input, game)
