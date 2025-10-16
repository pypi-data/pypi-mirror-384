"""Command-line interface for the Crazy Eights card game."""

from __future__ import annotations

from card_games.common.cards import Suit
from card_games.crazy_eights.game import CrazyEightsGame, Player


def display_game(game: CrazyEightsGame) -> None:
    """Display the current game state.

    Args:
        game: The Crazy Eights game instance
    """
    summary = game.get_state_summary()
    print("\n" + "=" * 70)
    print(f"CRAZY EIGHTS - {summary['current_player']}'s Turn")
    print("=" * 70)

    # Show active card
    top_card = game.get_top_card()
    if top_card:
        print(f"\nActive card: {top_card} (Suit: {summary['active_suit']}, Rank: {summary['active_rank']})")
    print(f"Deck: {summary['deck_cards']} cards remaining")

    # Show all players
    print("\nPlayers:")
    for player_info in summary["players"]:
        marker = "→ " if player_info["name"] == summary["current_player"] else "  "
        print(f"{marker}{player_info['name']:15} - {player_info['hand_size']:2} cards")

    print("=" * 70)


def display_hand(player: Player, game: CrazyEightsGame) -> None:
    """Display a player's hand with playability indicators.

    Args:
        player: The player whose hand to display
        game: The game instance for checking playability
    """
    if not player.hand:
        print("  (no cards)")
        return

    print(f"\n{player.name}'s hand:")

    # Group by suit
    suits = [Suit.CLUBS, Suit.DIAMONDS, Suit.HEARTS, Suit.SPADES]
    playable = player.get_playable_cards(game.active_suit, game.active_rank)

    for suit in suits:
        cards_in_suit = [card for card in player.hand if card.suit == suit]
        if cards_in_suit:
            cards_str = []
            for card in sorted(cards_in_suit, key=lambda c: c.value):
                marker = "✓" if card in playable else " "
                cards_str.append(f"{marker}{str(card)}")
            print(f"  {suit.value}: {', '.join(cards_str)}")


def get_player_action(game: CrazyEightsGame) -> dict[str, any]:
    """Get player input for their turn.

    Args:
        game: The Crazy Eights game instance

    Returns:
        Dictionary with action type and parameters
    """
    current_player = game.get_current_player()
    playable = current_player.get_playable_cards(game.active_suit, game.active_rank)

    if not playable:
        print("\n❌ No playable cards! You must draw.")
        return {"action": "draw"}

    print("\nYour playable cards:")
    for i, card in enumerate(playable, 1):
        print(f"  {i}. {card}")

    print("\nActions:")
    print("  [number] - Play that card")
    print("  d - Draw a card")

    while True:
        try:
            action = input("\nYour choice: ").strip().lower()

            if action == "d":
                return {"action": "draw"}

            # Try to parse as card index
            try:
                idx = int(action) - 1
                if 0 <= idx < len(playable):
                    card = playable[idx]

                    # If playing an 8, ask for suit
                    new_suit = None
                    if card.rank == "8":
                        print("\nChoose new suit:")
                        print("  1. Clubs ♣")
                        print("  2. Diamonds ♦")
                        print("  3. Hearts ♥")
                        print("  4. Spades ♠")

                        while True:
                            suit_choice = input("Suit (1-4): ").strip()
                            if suit_choice == "1":
                                new_suit = Suit.CLUBS
                                break
                            elif suit_choice == "2":
                                new_suit = Suit.DIAMONDS
                                break
                            elif suit_choice == "3":
                                new_suit = Suit.HEARTS
                                break
                            elif suit_choice == "4":
                                new_suit = Suit.SPADES
                                break
                            else:
                                print("Invalid choice. Enter 1-4.")

                    return {"action": "play", "card": card, "new_suit": new_suit}
            except ValueError:
                pass

            print("Invalid choice. Try again.")

        except (KeyboardInterrupt, EOFError):
            print("\nThanks for playing!")
            return {"action": "quit"}


def game_loop(game: CrazyEightsGame) -> None:
    """Main game loop for Crazy Eights.

    Args:
        game: The Crazy Eights game instance
    """
    print("\n" + "=" * 70)
    print("WELCOME TO CRAZY EIGHTS!")
    print("=" * 70)
    print("\nRules:")
    print("* Match the rank OR suit of the active card")
    print("* Eights are wild - play them to change the suit")
    print("* If you can't play, draw cards until you can (max 3)")
    print("* First player to get rid of all cards wins!")
    print("* Scoring: Winner gets points for cards in opponents' hands")
    print("  - Eights = 50 points")
    print("  - Face cards = 10 points")
    print("  - Number cards = face value")
    print("=" * 70)

    input("\nPress Enter to start...")

    while not game.is_game_over():
        display_game(game)
        current_player = game.get_current_player()
        display_hand(current_player, game)

        action = get_player_action(game)

        if action["action"] == "quit":
            print("\nThanks for playing!")
            return

        elif action["action"] == "play":
            result = game.play_card(action["card"], action.get("new_suit"))
            print(f"\n{result['message']}")

            if result.get("game_over"):
                break

        elif action["action"] == "draw":
            # Draw up to draw_limit cards or until can play
            draws = 0
            can_play = False

            while draws < (game.draw_limit if game.draw_limit > 0 else 999):
                result = game.draw_card()
                if not result["success"]:
                    print(f"\n{result['message']}")
                    break

                draws += 1
                print(f"\n{result['message']}")

                # Check if we can now play
                if current_player.has_playable_card(game.active_suit, game.active_rank):
                    print("You can now play!")
                    can_play = True
                    break

                if game.draw_limit > 0 and draws >= game.draw_limit:
                    print(f"Drew {draws} cards (limit reached)")
                    break

            # If still can't play after drawing, pass
            if not can_play and draws > 0:
                result = game.pass_turn()
                print(f"\n{result['message']}")

        input("\nPress Enter to continue...")

    # Game over
    summary = game.get_state_summary()
    print("\n" + "=" * 70)
    print("GAME OVER!")
    print("=" * 70)

    winner_info = max(summary["players"], key=lambda p: p["score"])
    print(f"\n🎉 {winner_info['name']} wins with {winner_info['score']} points!")

    print("\nFinal Scores:")
    for player_info in sorted(summary["players"], key=lambda p: p["score"], reverse=True):
        print(f"  {player_info['name']:15} - {player_info['score']:3} points")

    print("=" * 70)
