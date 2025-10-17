"""Command-line interface for the Go Fish card game with autosave support."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from card_games.common.cards import RANKS
from card_games.go_fish.game import GoFishGame, Player
from common.architecture.persistence import SaveLoadManager

_AUTOSAVE_NAME = "go_fish_autosave"
_AUTOSAVE_PATH = Path("./saves") / f"{_AUTOSAVE_NAME}.save"


def display_game(game: GoFishGame, show_all_hands: bool = False) -> None:
    """Display the current game state."""

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

    current_player = game.get_current_player()
    print(f"\n{current_player.name}'s hand:")
    display_hand(current_player)

    if show_all_hands:
        print("\nAll hands (debug mode):")
        for player in game.players:
            print(f"\n{player.name}:")
            display_hand(player)


def display_hand(player: Player) -> None:
    """Display a player's hand organized by rank."""

    if not player.hand:
        print("  (no cards)")
        return

    rank_groups: dict[str, list[str]] = {}
    for card in player.hand:
        rank_groups.setdefault(card.rank, []).append(str(card))

    for rank in RANKS:
        if rank in rank_groups:
            cards_str = ", ".join(rank_groups[rank])
            count = len(rank_groups[rank])
            print(f"  {rank}: {cards_str} ({count})")


def get_player_input(game: GoFishGame) -> tuple[str, str]:
    """Get player input for their turn."""

    current_player = game.get_current_player()
    other_players = [p for p in game.players if p != current_player]

    print("\nOther players:")
    for i, player in enumerate(other_players, 1):
        print(f"  {i}. {player.name}")

    while True:
        try:
            player_input = input("\nWho do you want to ask? (number or name): ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nInput cancelled. Try again.")
            continue

        target_player = None
        try:
            idx = int(player_input) - 1
            if 0 <= idx < len(other_players):
                target_player = other_players[idx]
        except ValueError:
            target_player = game.get_player_by_name(player_input)
            if target_player == current_player:
                target_player = None

        if target_player is None:
            print("Invalid player. Try again.")
            continue

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


def game_loop(game: GoFishGame) -> None:
    """Main game loop for Go Fish with autosave integration."""

    save_manager = SaveLoadManager()
    resumed_game = _load_autosave(save_manager)
    if resumed_game is not None:
        game = resumed_game
        print("\nResumed saved Go Fish match.")

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

        target_name, rank = get_player_input(game)
        result = game.ask_for_cards(target_name, rank)

        print(f"\n{result['message']}")

        if result.get("success"):
            _save_autosave(save_manager, game, metadata={"last_action": result["message"], "next_turn": result["next_turn"]})

        if result.get("game_over"):
            break

        input("\nPress Enter to continue...")

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

    _clear_autosave(save_manager)


def _load_autosave(save_manager: SaveLoadManager) -> Optional[GoFishGame]:
    """Load an autosaved game if available and approved by the player."""

    if not _AUTOSAVE_PATH.exists():
        return None

    try:
        choice = input("Found a saved Go Fish match. Resume? [y/N]: ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        choice = ""

    if not choice.startswith("y"):
        save_manager.delete_save(_AUTOSAVE_PATH)
        return None

    try:
        data = save_manager.load(_AUTOSAVE_PATH)
    except FileNotFoundError:
        return None

    state = data.get("state", {})
    if not state:
        return None

    return GoFishGame.from_state(state)


def _save_autosave(save_manager: SaveLoadManager, game: GoFishGame, *, metadata: Optional[dict[str, str]] = None) -> None:
    """Persist the current game state to the autosave slot."""

    summary = game.get_state_summary()
    autosave_metadata = {
        "current_player": summary["current_player"],
        "deck_cards": str(summary["deck_cards"]),
        "last_action": summary["last_action"],
    }
    if metadata:
        autosave_metadata.update(metadata)

    save_manager.save("go_fish", game.to_state(), save_name=_AUTOSAVE_NAME, metadata=autosave_metadata)


def _clear_autosave(save_manager: SaveLoadManager) -> None:
    """Remove the autosave file once a match completes."""

    if _AUTOSAVE_PATH.exists():
        save_manager.delete_save(_AUTOSAVE_PATH)
