"""Interactive command-line client for the Gin Rummy engine."""

from __future__ import annotations

from card_games.common.cards import format_cards, parse_card
from card_games.gin_rummy.game import GinRummyGame, GinRummyPlayer, Meld, MeldType, RoundSummary


def _format_meld(meld: Meld) -> str:
    """Return a human readable description of a meld."""

    label = "Set" if meld.meld_type == MeldType.SET else "Run"
    return f"{label}: {format_cards(meld.cards)}"


def _display_hand(player: GinRummyPlayer, game: GinRummyGame) -> None:
    """Display the player's hand, melds, and current deadwood tally."""

    analysis = game.analyze_hand(player.hand)
    print(f"\n{player.name}'s hand: {format_cards(player.hand)}")
    if analysis.melds:
        meld_lines = ", ".join(_format_meld(m) for m in analysis.melds)
        print(f"Melds: {meld_lines}")
    if analysis.deadwood_cards:
        print(f"Deadwood: {format_cards(analysis.deadwood_cards)} ({analysis.deadwood_total} points)")
    else:
        print("Deadwood: none")


def _prompt_yes_no(prompt: str) -> bool:
    """Return True for yes, False for no based on user input."""

    while True:
        choice = input(f"{prompt} (y/n): ").strip().lower()
        if choice in {"y", "yes"}:
            return True
        if choice in {"n", "no"}:
            return False
        print("Please answer with 'y' or 'n'.")


def _handle_initial_upcard(game: GinRummyGame) -> None:
    """Resolve the optional first upcard before regular turns begin."""

    if not game.discard_pile:
        return
    print(f"\nOpening upcard is {game.discard_pile[-1]}")
    while game.initial_upcard_phase:
        player_idx = game.initial_offer_order[game.initial_offer_position]
        player = game.players[player_idx]
        if player.is_ai:
            take = game.should_draw_discard(player, game.discard_pile[-1])
            if take:
                card = game.take_initial_upcard(player_idx)
                print(f"{player.name} takes the upcard {card}.")
            else:
                game.pass_initial_upcard(player_idx)
                print(f"{player.name} passes on the upcard.")
        else:
            _display_hand(player, game)
            if _prompt_yes_no("Do you want to take the upcard?"):
                card = game.take_initial_upcard(player_idx)
                print(f"You take the upcard {card}. Remember to discard a different card.")
            else:
                game.pass_initial_upcard(player_idx)
                print("You pass on the upcard.")
    print("Upcard phase resolved. Regular play begins.")


def _choose_draw(player_idx: int, game: GinRummyGame) -> str:
    """Return either 'stock' or 'discard' for the draw choice."""

    player = game.players[player_idx]
    top_discard = game.discard_pile[-1] if game.discard_pile else None
    if player.is_ai:
        if top_discard and game.can_draw_from_discard(player_idx) and game.should_draw_discard(player, top_discard):
            return "discard"
        return "stock"

    while True:
        choice = input("Draw from (s)tock or (d)iscard? ").strip().lower()
        if choice in {"s", "stock"}:
            return "stock"
        if choice in {"d", "discard"}:
            if top_discard and game.can_draw_from_discard(player_idx):
                return "discard"
            print("You cannot draw from the discard pile right now.")
        else:
            print("Please choose 's' or 'd'.")


def _perform_discard(player_idx: int, game: GinRummyGame) -> None:
    """Handle discard phase for either a human or AI player."""

    player = game.players[player_idx]
    if player.is_ai:
        discard_card = game.suggest_discard(player)
        game.discard(player_idx, discard_card)
        print(f"{player.name} discards {discard_card}.")
        player.hand.sort(key=lambda c: (c.suit.value, c.value))
        return

    print("\nChoose a card to discard (example: 7H for Seven of Hearts).")
    while True:
        try:
            code = input("Card: ").strip().upper()
            discard_card = parse_card(code)
            game.discard(player_idx, discard_card)
            print(f"You discard {discard_card}.")
            player.hand.sort(key=lambda c: (c.suit.value, c.value))
            return
        except ValueError as exc:
            print(f"{exc}. Try again.")


def _maybe_knock(player_idx: int, game: GinRummyGame) -> bool:
    """Return True if the player decides to end the round."""

    player = game.players[player_idx]
    analysis = game.analyze_hand(player.hand)
    if analysis.deadwood_total == 0:
        print(f"{player.name} declares GIN!")
        return True

    if player.is_ai:
        if analysis.deadwood_total <= 5:
            print(f"{player.name} knocks with {analysis.deadwood_total} deadwood.")
            return True
        return False

    if analysis.deadwood_total <= 10:
        print(f"You may knock (deadwood = {analysis.deadwood_total}).")
        return _prompt_yes_no("Do you want to knock?")
    return False


def play_turn(player_idx: int, game: GinRummyGame) -> bool:
    """Execute a full turn for ``player_idx``. Return True if the round ends."""

    player = game.players[player_idx]
    print("\n" + "=" * 60)
    print(f"{player.name}'s turn")
    print("=" * 60)

    _display_hand(player, game)

    top_discard = game.discard_pile[-1] if game.discard_pile else None
    if top_discard:
        print(f"Top of discard pile: {top_discard}")

    draw_choice = _choose_draw(player_idx, game)
    if draw_choice == "discard":
        drawn_card = game.draw_from_discard()
    else:
        drawn_card = game.draw_from_stock()
    player.hand.append(drawn_card)
    player.hand.sort(key=lambda c: (c.suit.value, c.value))
    print(f"{player.name} draws {drawn_card} from {'discard' if draw_choice == 'discard' else 'stock'}.")

    _display_hand(player, game)

    if _maybe_knock(player_idx, game):
        return True

    _perform_discard(player_idx, game)
    return False


def _display_round_summary(summary: RoundSummary, game: GinRummyGame) -> None:
    """Print scoring, melds, and layoff information for the round."""

    print("\n" + "=" * 60)
    print("ROUND RESULT")
    print("=" * 60)

    print(f"Dealer: {summary.dealer}")
    print(f"Knocker: {summary.knocker} ({summary.knock_type.name.replace('_', ' ').title()})")
    print(f"Opponent: {summary.opponent}")
    print(f"Knocker deadwood: {summary.knocker_deadwood}")
    print("Opponent deadwood: " f"{summary.opponent_deadwood} (was {summary.opponent_initial_deadwood} before layoffs)")

    if summary.melds_shown:
        print("Melds revealed:")
        for meld in summary.melds_shown:
            print(f"  - {_format_meld(meld)}")
    else:
        print("No melds were revealed.")

    if summary.layoff_cards:
        print(f"Opponent laid off: {format_cards(summary.layoff_cards)}")
    else:
        print("No layoff cards were available.")

    print("\nPoints awarded:")
    for name, points in summary.points_awarded.items():
        delta = f"+{points}" if points >= 0 else str(points)
        print(f"  {name}: {delta}")

    print("\nRunning totals:")
    for player in game.players:
        print(f"  {player.name}: {player.score} points")


def game_loop() -> None:
    """Main game loop for Gin Rummy."""

    print("\nWELCOME TO GIN RUMMY")
    print("=" * 60)

    player_name = input("Enter your name: ").strip() or "Player"
    players = [
        GinRummyPlayer(name=player_name, is_ai=False),
        GinRummyPlayer(name="AI", is_ai=True),
    ]
    game = GinRummyGame(players)
    round_num = 0

    while not game.is_game_over():
        round_num += 1
        print("\n" + "=" * 60)
        print(f"ROUND {round_num}")
        print("=" * 60)

        game.deal_cards()
        print(f"Dealer this round: {game.players[game.dealer_idx].name}")
        _handle_initial_upcard(game)

        while True:
            player_idx = game.current_player_idx
            if play_turn(player_idx, game):
                knocker = game.players[player_idx]
                opponent = game.players[(player_idx + 1) % len(game.players)]
                summary = game.calculate_round_score(knocker, opponent)
                game.record_points(summary)
                _display_round_summary(summary, game)
                break

        if not game.is_game_over():
            input("\nPress Enter to continue to the next round...")

    winner = game.get_winner()
    print("\n" + "=" * 60)
    print("GAME OVER")
    print("=" * 60)
    print(f"Winner: {winner.name} with {winner.score} points!")


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    game_loop()
