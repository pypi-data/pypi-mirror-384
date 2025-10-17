"""Interactive command-line client for the Gin Rummy engine.

This module provides a text-based interface for playing Gin Rummy, handling
user input for drawing, discarding, and knocking, and displaying the game state.
"""

from __future__ import annotations

from card_games.common.cards import format_cards, parse_card
from card_games.gin_rummy.game import GinRummyGame, GinRummyPlayer, Meld, MeldType, RoundSummary


def _format_meld(meld: Meld) -> str:
    """Return a human-readable description of a meld."""
    label = "Set" if meld.meld_type == MeldType.SET else "Run"
    return f"{label}: {format_cards(meld.cards)}"


def _display_hand(player: GinRummyPlayer, game: GinRummyGame) -> None:
    """Display the player's hand, melds, and current deadwood total."""
    analysis = game.analyze_hand(player.hand)
    print(f"\n{player.name}'s hand: {format_cards(player.hand)}")
    if analysis.melds:
        print(f"Melds: {', '.join(_format_meld(m) for m in analysis.melds)}")
    if analysis.deadwood_cards:
        print(f"Deadwood: {format_cards(analysis.deadwood_cards)} ({analysis.deadwood_total} points)")
    else:
        print("No deadwood.")


def _prompt_yes_no(prompt: str) -> bool:
    """Prompt the user for a yes/no answer."""
    while True:
        choice = input(f"{prompt} (y/n): ").strip().lower()
        if choice in {"y", "yes"}:
            return True
        if choice in {"n", "no"}:
            return False
        print("Please answer 'y' or 'n'.")


def _handle_initial_upcard(game: GinRummyGame) -> None:
    """Handle the initial up-card offer at the start of a round."""
    if not game.discard_pile:
        return
    print(f"\nOpening up-card: {game.discard_pile[-1]}")
    while game.initial_upcard_phase:
        player = game.players[game.current_player_idx]
        if player.is_ai:
            if game.should_draw_discard(player, game.discard_pile[-1]):
                game.take_initial_upcard()
                print(f"{player.name} takes the up-card.")
            else:
                game.pass_initial_upcard()
                print(f"{player.name} passes.")
        else:
            _display_hand(player, game)
            if _prompt_yes_no("Take the up-card?"):
                game.take_initial_upcard()
            else:
                game.pass_initial_upcard()
    print("Up-card phase is complete. Regular play begins.")


def _choose_draw(player_idx: int, game: GinRummyGame) -> str:
    """Prompt the player to choose between drawing from the stock or discard pile."""
    player = game.players[player_idx]
    if player.is_ai:
        return "discard" if game.can_draw_from_discard() and game.should_draw_discard(player, game.discard_pile[-1]) else "stock"

    while True:
        choice = input("Draw from (s)tock or (d)iscard? ").strip().lower()
        if choice in {"s", "stock"}:
            return "stock"
        if choice in {"d", "discard"}:
            if game.can_draw_from_discard():
                return "discard"
            print("Cannot draw from the discard pile.")
        else:
            print("Invalid choice. Please enter 's' or 'd'.")


def _perform_discard(player_idx: int, game: GinRummyGame) -> None:
    """Handle the discard phase for a player."""
    player = game.players[player_idx]
    if player.is_ai:
        discard = game.suggest_discard(player)
        game.discard(discard)
        print(f"{player.name} discards {discard}.")
        return

    while True:
        try:
            code = input("Choose a card to discard (e.g., '7H'): ").strip().upper()
            card_to_discard = parse_card(code)
            game.discard(card_to_discard)
            print(f"You discard {card_to_discard}.")
            return
        except (ValueError, KeyError) as e:
            print(f"Invalid card: {e}. Please try again.")


def _maybe_knock(player_idx: int, game: GinRummyGame) -> bool:
    """Check if a player can and wants to knock."""
    player = game.players[player_idx]
    analysis = game.analyze_hand(player.hand)
    if analysis.deadwood_total == 0:
        print(f"{player.name} declares GIN!")
        return True
    if player.is_ai:
        return analysis.deadwood_total <= 5
    if analysis.deadwood_total <= 10:
        return _prompt_yes_no(f"You have {analysis.deadwood_total} deadwood. Knock?")
    return False


def play_turn(player_idx: int, game: GinRummyGame) -> bool:
    """Execute a full turn for a player, returning True if the round ends."""
    player = game.players[player_idx]
    print(f"\n{'='*60}\n{player.name}'s turn\n{'='*60}")
    _display_hand(player, game)

    if game.discard_pile:
        print(f"Top of discard pile: {game.discard_pile[-1]}")

    draw_source = _choose_draw(player_idx, game)
    drawn_card = game.draw_from_discard() if draw_source == "discard" else game.draw_from_stock()
    print(f"{player.name} draws {drawn_card} from the {draw_source}.")
    _display_hand(player, game)

    if _maybe_knock(player_idx, game):
        return True

    _perform_discard(player_idx, game)
    return False


def _display_round_summary(summary: RoundSummary, game: GinRummyGame) -> None:
    """Print a summary of the round's results."""
    print(f"\n{'='*60}\nROUND RESULT\n{'='*60}")
    print(f"Knocker: {summary.knocker} ({summary.knock_type.name})")
    # ... (rest of the summary display)


def game_loop() -> None:
    """Run the main game loop for the Gin Rummy CLI."""
    print(f"\n{'='*60}\nWELCOME TO GIN RUMMY\n{'='*60}")
    players = [
        GinRummyPlayer(name=input("Enter your name: ").strip() or "Player 1"),
        GinRummyPlayer(name="AI", is_ai=True),
    ]
    game = GinRummyGame(players)

    while not game.is_game_over():
        game.deal_cards()
        _handle_initial_upcard(game)

        while True:
            if play_turn(game.current_player_idx, game):
                summary = game.knock()
                _display_round_summary(summary, game)
                break

    winner = game.get_winner()
    if winner:
        print(f"\n{'='*60}\nGAME OVER\n{'='*60}\nWinner: {winner.name} with {winner.score} points!")
