"""Command-line interface for the Craps dice game.

This module provides a text-based interface to play Craps. It allows the user
to interact with the game engine by typing commands to roll the dice, place
bets, and manage their bankroll.

The CLI uses an event-driven approach to display game state changes and an
analytics hook to provide detailed logging of game events.

Classes:
    CrapsCLIEventHandler: Handles game events and prints them to the console.

Functions:
    _analytics_hook: Logs detailed analytics events.
    _display_active_bets: Shows the player's current bets.
    main: The main entry point for the CLI application.
"""

from __future__ import annotations

from typing import Dict

from common.architecture.events import Event, EventBus, EventHandler, GameEventType

from .craps import CrapsGame


class CrapsCLIEventHandler(EventHandler):
    """A simple CLI event handler that prints significant game events.

    This class listens for events from the game engine and translates them into
    human-readable messages printed to the standard output.
    """

    def handle(self, event: Event) -> None:
        """Handle incoming game events by printing user-friendly messages.

        Args:
            event: The game event to be handled.
        """
        if event.type == GameEventType.SCORE_UPDATED.value:
            bankroll = event.data.get("bankroll")
            print(f"[event] Bankroll updated: ${bankroll}")
        elif event.type == GameEventType.TURN_COMPLETE.value:
            roll = event.data.get("roll")
            point = event.data.get("point")
            status = f"point is {point}" if point else "no point established"
            print(f"[event] Roll {roll} complete, {status}.")
        elif event.type == GameEventType.GAME_OVER.value:
            print("[event] Game over! Your bankroll is depleted.")


def _analytics_hook(event: str, payload: Dict[str, int | str | None]) -> None:
    """A callback to log detailed analytics events in a concise form.

    This function is registered with the `CrapsGame` engine to receive telemetry
    about important game actions, such as bets being placed and resolved.

    Args:
        event: The name of the analytics event.
        payload: A dictionary containing data related to the event.
    """
    # Filter for the most important events to avoid verbose logging.
    important_events = {
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
    if event in important_events:
        print(f"[analytics] {event}: {payload}")


def _display_active_bets(game: CrapsGame) -> None:
    """Display the currently active bets for the player.

    Args:
        game: The `CrapsGame` instance containing the bet information.
    """
    if game.current_bet:
        print(f"  Line bet: ${game.current_bet} on {game.bet_type.value}")
    else:
        print("  No active line bet.")

    if game.odds_bet:
        print(f"  Odds bet: ${game.odds_bet}")

    active_place_bets = {num: amt for num, amt in game.place_bets.items() if amt > 0}
    if active_place_bets:
        bets_str = ", ".join(f"{num}: ${amt}" for num, amt in sorted(active_place_bets.items()))
        print(f"  Place bets: {bets_str}")


def main() -> None:
    """Runs the main loop for the Craps command-line interface.

    This function initializes the game, displays instructions, and enters a
    loop to accept and process user commands until the game is over or the
    user quits.
    """
    print("CRAPS".center(50, "="))
    print("\nWelcome to the casino dice game. Bet on the roll of the dice!")

    # Set up the game engine and event handling.
    event_bus = EventBus()
    game = CrapsGame()
    game.set_event_bus(event_bus)
    game.register_analytics_hook(_analytics_hook)
    event_bus.subscribe_all(CrapsCLIEventHandler())
    game.state = game.state.IN_PROGRESS  # Manually start the game.

    # Display game instructions.
    print("\nStarting bankroll: $1000")
    print("Commands:")
    print("  - roll")
    print("  - bet_pass <amount>")
    print("  - bet_dont_pass <amount>")
    print("  - bet_odds <amount>")
    print("  - bet_place <number> <amount> (e.g., bet_place 6 10)")
    print("  - remove_place <number> (e.g., remove_place 6)")
    print("  - quit")

    # Main game loop.
    while not game.is_game_over():
        print("-" * 20)
        print(f"Bankroll: ${game.bankroll}")
        if game.point:
            print(f"The Point is: {game.point}")
        else:
            print("Status: Come-out roll")
        _display_active_bets(game)

        cmd = input("Enter command: ").strip().lower()
        if cmd == "quit":
            print("Thanks for playing!")
            break

        if not game.make_move(cmd):
            print("Invalid move or command format. Please try again.")

    print("\n" + "=" * 50)
    print("Game over!")


if __name__ == "__main__":
    main()
