"""Command-line interface for the Crazy Eights card game.

This module provides the functions to run a game of Crazy Eights in the
terminal, handling user input and displaying the game state.
"""

from __future__ import annotations

from card_games.common.cards import Suit
from card_games.crazy_eights.game import CrazyEightsGame, Player


def display_game(game: CrazyEightsGame) -> None:
    """Display the current game state, including players and active card.

    Args:
        game: The ``CrazyEightsGame`` instance.
    """
    summary = game.get_state_summary()
    print("\n" + "=" * 70)
    print(f"CRAZY EIGHTS - {summary['current_player']}'s Turn")
    print("=" * 70)

    top_card = game.get_top_card()
    if top_card:
        print(f"\nActive card: {top_card} " f"(Suit: {summary['active_suit']}, Rank: {summary['active_rank']})")
    print(f"Deck: {summary['deck_cards']} cards remaining")

    print("\nPlayers:")
    for player_info in summary["players"]:
        marker = "→" if player_info["name"] == summary["current_player"] else " "
        print(f"  {marker} {player_info['name']:<15} - {player_info['hand_size']:2} cards")

    print("=" * 70)


def display_hand(player: Player, game: CrazyEightsGame) -> None:
    """Display a player's hand with indicators for playable cards.

    Args:
        player: The player whose hand to display.
        game: The game instance, used for checking playability.
    """
    if not player.hand:
        print("  (Your hand is empty)")
        return

    print(f"\n{player.name}'s hand:")
    playable_cards = player.get_playable_cards(game.active_suit, game.active_rank)

    for suit in sorted(Suit, key=lambda s: s.value):
        cards_in_suit = sorted([c for c in player.hand if c.suit == suit], key=lambda c: c.value)
        if cards_in_suit:
            card_strs = [f"{'✓' if card in playable_cards else ' '}{card}" for card in cards_in_suit]
            print(f"  {suit.value}: {', '.join(card_strs)}")


def get_player_action(game: CrazyEightsGame) -> dict[str, any]:
    """Prompt the current player for their action.

    Args:
        game: The ``CrazyEightsGame`` instance.

    Returns:
        A dictionary representing the chosen action and its parameters.
    """
    player = game.get_current_player()
    playable = player.get_playable_cards(game.active_suit, game.active_rank)

    if not playable:
        print("\n❌ No playable cards! You must draw.")
        return {"action": "draw"}

    print("\nYour playable cards:")
    for i, card in enumerate(playable, 1):
        print(f"  {i}. {card}")

    print("\nChoose an action: [number] to play a card, or (d)raw.")
    while True:
        choice = input("Your choice: ").strip().lower()
        if choice == "d":
            return {"action": "draw"}
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(playable):
                card = playable[idx]
                new_suit = None
                if card.rank == "8":
                    new_suit = _prompt_for_suit()
                return {"action": "play", "card": card, "new_suit": new_suit}
        except ValueError:
            pass
        print("Invalid choice. Please try again.")


def _prompt_for_suit() -> Suit:
    """Prompt the player to choose a suit after playing an eight."""
    while True:
        print("\nChoose a new suit:")
        for i, suit in enumerate(Suit, 1):
            print(f"  {i}. {suit.name.title()} {suit.value}")
        choice = input("Suit (1-4): ").strip()
        if choice in "1234":
            return list(Suit)[int(choice) - 1]
        print("Invalid choice. Please enter a number from 1 to 4.")


def game_loop(game: CrazyEightsGame) -> None:
    """Run the main game loop for the Crazy Eights CLI.

    Args:
        game: The ``CrazyEightsGame`` instance to run.
    """
    print("\n" + "=" * 70)
    print("WELCOME TO CRAZY EIGHTS!")
    print("=" * 70)
    # ... (rules explanation)

    input("\nPress Enter to start...")

    while not game.is_game_over():
        display_game(game)
        player = game.get_current_player()
        display_hand(player, game)

        action = get_player_action(game)
        if action["action"] == "quit":
            break
        elif action["action"] == "play":
            result = game.play_card(action["card"], action.get("new_suit"))
            print(f"\n{result['message']}")
        elif action["action"] == "draw":
            draws = 0
            while draws < (game.draw_limit or 999):
                result = game.draw_card()
                print(f"\n{result['message']}")
                if not result["success"] or player.has_playable_card(game.active_suit, game.active_rank):
                    break
                draws += 1
            if not player.has_playable_card(game.active_suit, game.active_rank):
                result = game.pass_turn()
                print(f"\n{result['message']}")

        if not game.is_game_over():
            input("\nPress Enter to continue...")

    # Game over
    summary = game.get_state_summary()
    print("\n" + "=" * 70)
    print("GAME OVER!")
    print("=" * 70)

    winner = max(summary["players"], key=lambda p: p["score"])
    print(f"\n🎉 {winner['name']} wins with {winner['score']} points!")

    print("\nFinal Scores:")
    for p_info in sorted(summary["players"], key=lambda p: p["score"], reverse=True):
        print(f"  {p_info['name']:<15} - {p_info['score']:3} points")
    print("=" * 70)
