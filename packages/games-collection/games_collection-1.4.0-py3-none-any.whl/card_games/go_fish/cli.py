"""Command-line interface for the Go Fish card game."""

from __future__ import annotations

from card_games.common.cards import RANKS
from card_games.go_fish.game import GoFishGame, Player


def display_game(game: GoFishGame, show_all_hands: bool = False) -> None:
    """Display the current game state.

    Args:
        game: The Go Fish game instance
        show_all_hands: If True, show all players' hands (for debugging)
    """
    summary = game.get_state_summary()
    print("\n" + "=" * 70)
    print(f"GO FISH - {summary['current_player']}'s Turn")
    print("=" * 70)

    for player_info in summary["players"]:
        books_str = "⭐" * player_info["books"]
        print(f"{player_info['name']:15} - {player_info['hand_size']:2} cards, {player_info['books']:2} books {books_str}")

    print(f"\nDeck: {summary['deck_cards']} cards remaining")

    if summary["last_action"]:
        print(f"\nLast action: {summary['last_action']}")

    print("=" * 70)

    # Show current player's hand
    current_player = game.get_current_player()
    print(f"\n{current_player.name}'s hand:")
    display_hand(current_player)

    if show_all_hands:
        print("\nAll hands (debug mode):")
        for player in game.players:
            print(f"\n{player.name}:")
            display_hand(player)


def display_hand(player: Player) -> None:
    """Display a player's hand organized by rank.

    Args:
        player: The player whose hand to display
    """
    if not player.hand:
        print("  (no cards)")
        return

    # Group cards by rank
    rank_groups: dict[str, list[str]] = {}
    for card in player.hand:
        if card.rank not in rank_groups:
            rank_groups[card.rank] = []
        rank_groups[card.rank].append(str(card))

    # Display in rank order
    for rank in RANKS:
        if rank in rank_groups:
            cards_str = ", ".join(rank_groups[rank])
            count = len(rank_groups[rank])
            print(f"  {rank}: {cards_str} ({count})")


def get_player_input(game: GoFishGame) -> tuple[str, str]:
    """Get player input for their turn.

    Args:
        game: The Go Fish game instance

    Returns:
        Tuple of (target_player_name, rank)
    """
    current_player = game.get_current_player()
    other_players = [p for p in game.players if p != current_player]

    print("\nOther players:")
    for i, player in enumerate(other_players, 1):
        print(f"  {i}. {player.name}")

    while True:
        try:
            player_input = input("\nWho do you want to ask? (number or name): ").strip()

            # Try to parse as number
            target_player = None
            try:
                idx = int(player_input) - 1
                if 0 <= idx < len(other_players):
                    target_player = other_players[idx]
            except ValueError:
                # Try as name
                target_player = game.get_player_by_name(player_input)
                if target_player == current_player:
                    target_player = None

            if target_player is None:
                print("Invalid player. Try again.")
                continue

            # Get rank
            rank_input = input(f"What rank do you want to ask {target_player.name} for? ").strip().upper()
            if rank_input == "10":
                rank_input = "T"

            if rank_input not in RANKS:
                print(f"Invalid rank. Valid ranks: {', '.join(RANKS)}")
                continue

            if not current_player.has_rank(rank_input):
                print(f"You don't have any {rank_input}s! You must ask for a rank you have.")
                continue

            return target_player.name, rank_input

        except (ValueError, KeyboardInterrupt):
            print("\nInvalid input. Try again.")


def game_loop(game: GoFishGame) -> None:
    """Main game loop for Go Fish.

    Args:
        game: The Go Fish game instance
    """
    print("\n" + "=" * 70)
    print("WELCOME TO GO FISH!")
    print("=" * 70)
    print("\nRules:")
    print("* Try to collect sets of 4 cards of the same rank (books)")
    print("* On your turn, ask another player for cards of a specific rank")
    print("* You must have at least one card of that rank to ask for it")
    print("* If they have it, you get all their cards of that rank and go again")
    print("* If not, they say 'Go Fish!' and you draw a card")
    print("* If you draw the rank you asked for, you get another turn")
    print("* When you complete a set of 4, you lay it down (make a book)")
    print("* Player with the most books when all cards are gone wins!")
    print("=" * 70)

    input("\nPress Enter to start...")

    while not game.is_game_over():
        display_game(game)

        current_player = game.get_current_player()
        print(f"\n{current_player.name}'s turn!")

        # Get player action
        target_name, rank = get_player_input(game)

        # Execute action
        result = game.ask_for_cards(target_name, rank)

        print(f"\n{result['message']}")

        if result.get("game_over"):
            break

        input("\nPress Enter to continue...")

    # Game over - show final results
    summary = game.get_state_summary()
    print("\n" + "=" * 70)
    print("GAME OVER!")
    print("=" * 70)
    print("\nFinal Scores:")
    for player_info in sorted(summary["players"], key=lambda p: p["books"], reverse=True):
        books_str = "⭐" * player_info["books"]
        print(f"  {player_info['name']:15} - {player_info['books']:2} books {books_str}")

    winner_info = max(summary["players"], key=lambda p: p["books"])
    print(f"\n🎉 {winner_info['name']} wins with {winner_info['books']} books!")
    print("=" * 70)
