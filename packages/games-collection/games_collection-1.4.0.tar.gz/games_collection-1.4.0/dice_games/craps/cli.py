"""Command-line interface for Craps."""

from __future__ import annotations

from typing import Dict

from common.architecture.events import Event, EventBus, EventHandler, GameEventType

from .craps import CrapsGame


class CrapsCLIEventHandler(EventHandler):
    """Simple CLI event handler that prints significant game events."""

    def handle(self, event: Event) -> None:
        """Handle incoming events by printing user-friendly messages."""

        if event.type == GameEventType.SCORE_UPDATED.value:
            bankroll = event.data.get("bankroll")
            print(f"[event] Bankroll updated: ${bankroll}")
        elif event.type == GameEventType.TURN_COMPLETE.value:
            roll = event.data.get("roll")
            point = event.data.get("point")
            status = f"point {point}" if point else "no point"
            print(f"[event] Roll {roll} complete, {status}.")
        elif event.type == GameEventType.GAME_OVER.value:
            print("[event] Game over!")


def _analytics_hook(event: str, payload: Dict[str, int | str | None]) -> None:
    """Log analytics callbacks in a concise form."""

    important = {
        "line_bet_placed",
        "line_bet_resolved",
        "odds_bet_placed",
        "odds_bet_resolved",
        "place_bet_placed",
        "place_bet_removed",
        "place_bet_paid",
        "place_bets_cleared",
        "point_established",
    }
    if event in important:
        print(f"[analytics] {event}: {payload}")


def _display_active_bets(game: CrapsGame) -> None:
    """Display the currently active bets."""

    if game.current_bet:
        print(f"Line bet: ${game.current_bet} on {game.bet_type.value}")
    else:
        print("No active line bet")

    if game.odds_bet:
        print(f"  Odds bet: ${game.odds_bet}")

    active_place = {number: amount for number, amount in game.place_bets.items() if amount > 0}
    if active_place:
        bets = ", ".join(f"{number}: ${amount}" for number, amount in sorted(active_place.items()))
        print(f"  Place bets -> {bets}")


def main() -> None:
    """Run Craps game."""
    print("CRAPS".center(50, "="))
    print("\nCasino dice game. Bet on dice rolls!")

    event_bus = EventBus()
    game = CrapsGame()
    game.set_event_bus(event_bus)
    game.register_analytics_hook(_analytics_hook)
    event_bus.subscribe_all(CrapsCLIEventHandler())
    game.state = game.state.IN_PROGRESS

    print("\nStarting bankroll: $1000")
    print("Commands:")
    print("  roll")
    print("  bet_pass <amount>")
    print("  bet_dont_pass <amount>")
    print("  bet_odds <amount>")
    print("  bet_place_<number> <amount> (numbers 4,5,6,8,9,10)")
    print("  remove_place_<number>")
    print("  quit")

    while not game.is_game_over():
        print(f"\nBankroll: ${game.bankroll}")
        if game.point:
            print(f"Point: {game.point}")
        else:
            print("Come-out roll")
        _display_active_bets(game)

        cmd = input("Command: ").strip().lower()
        if cmd == "quit":
            break

        if game.make_move(cmd):
            print("Move executed")
        else:
            print("Invalid move")

    print("\nGame over!")


if __name__ == "__main__":
    main()
