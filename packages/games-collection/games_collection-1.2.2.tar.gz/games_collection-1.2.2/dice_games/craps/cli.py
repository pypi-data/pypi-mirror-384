"""Command-line interface for Craps."""

from __future__ import annotations

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


def main() -> None:
    """Run Craps game."""
    print("CRAPS".center(50, "="))
    print("\nCasino dice game. Bet on dice rolls!")

    event_bus = EventBus()
    game = CrapsGame()
    game.set_event_bus(event_bus)
    event_bus.subscribe_all(CrapsCLIEventHandler())
    game.state = game.state.IN_PROGRESS

    print("\nStarting bankroll: $1000")
    print("Commands: roll, bet_pass, bet_dont_pass, quit")

    while not game.is_game_over():
        print(f"\nBankroll: ${game.bankroll}")
        if game.point:
            print(f"Point: {game.point}")
        else:
            print("Come-out roll")

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
