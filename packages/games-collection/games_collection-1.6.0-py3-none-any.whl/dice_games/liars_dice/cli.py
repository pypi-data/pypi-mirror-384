"""CLI for Liar's Dice."""

from __future__ import annotations

from typing import Dict, List, Tuple

from common.ai_strategy import HeuristicStrategy
from common.game_engine import GameState

from .liars_dice import LiarsDiceGame


def _prompt_configuration() -> Tuple[int, int]:
    """Prompt for total players and AI opponents."""

    while True:
        try:
            players = int(input("Enter number of players (2-6): "))
            if 2 <= players <= 6:
                break
            print("Please choose between 2 and 6 players.")
        except ValueError:
            print("Please enter a valid number.")

    while True:
        try:
            ai_players = int(input("Number of AI opponents: "))
            if 0 <= ai_players < players:
                break
            print("AI opponents must be fewer than the total players.")
        except ValueError:
            print("Please enter a valid number.")

    return players, ai_players


def _prompt_int(prompt: str, minimum: int, maximum: int) -> int:
    """Prompt for an integer within a range."""

    while True:
        try:
            value = int(input(prompt))
            if minimum <= value <= maximum:
                return value
            print(f"Enter a value between {minimum} and {maximum}.")
        except ValueError:
            print("Please enter a valid number.")


def _print_table_state(game: LiarsDiceGame) -> None:
    """Display the number of dice remaining for each player."""

    summaries = []
    for idx, dice in enumerate(game.player_dice):
        status = f"P{idx + 1}: {len(dice)} dice"
        if game.eliminated[idx]:
            status += " (out)"
        summaries.append(status)
    print("Dice remaining: " + ", ".join(summaries))


def _summarize_challenge(game: LiarsDiceGame, bid: Tuple[int, int] | None, before: List[int]) -> None:
    """Print the outcome of a challenge."""

    if bid is None:
        print("Challenge resolved without an active bid.")
        return

    quantity, face = bid
    actual = sum(d.count(face) for d in game.player_dice)
    after = [len(d) for d in game.player_dice]
    loser = next((i for i, (b, a) in enumerate(zip(before, after)) if a < b), None)

    if actual >= quantity:
        print(f"Challenge failed! There were {actual} dice showing {face}.")
    else:
        print(f"Challenge succeeded! Only {actual} dice showing {face}.")

    if loser is not None:
        print(f"Player {loser + 1} loses a die and now has {after[loser]} remaining.")


def _handle_ai_turn(game: LiarsDiceGame, strategy: HeuristicStrategy[Tuple[int, int], LiarsDiceGame]) -> None:
    """Execute an AI player's turn."""

    player = game.get_current_player()
    print(f"\nAI Player {player + 1}'s turn")
    if game.current_bid:
        print(f"Current bid: {game.current_bid[0]}x {game.current_bid[1]}'s")

    valid_moves = game.get_valid_moves()
    move = strategy.select_move(valid_moves, game)

    if move == (-1, -1):
        print("AI calls a challenge!")
        before = [len(d) for d in game.player_dice]
        bid = game.current_bid
        game.make_move(move)
        _summarize_challenge(game, bid, before)
    else:
        quantity, face = move
        print(f"AI bids {quantity}x {face}'s")
        game.make_move(move)


def _handle_human_turn(game: LiarsDiceGame) -> None:
    """Prompt the human player for their action."""

    player = game.get_current_player()
    print(f"\nPlayer {player + 1}'s dice: {sorted(game.player_dice[player])}")

    if game.current_bid:
        print(f"Current bid: {game.current_bid[0]}x {game.current_bid[1]}'s")
        choice = input("(B)id higher or (C)hallenge? ").strip().upper()
        if choice == "C":
            before = [len(d) for d in game.player_dice]
            bid = game.current_bid
            game.make_move((-1, -1))
            _summarize_challenge(game, bid, before)
            return

    while True:
        quantity = _prompt_int("Bid quantity: ", 1, game.get_active_dice_total())
        face = _prompt_int("Bid face value (1-6): ", 1, 6)
        if game.make_move((quantity, face)):
            break
        print("Bid must exceed the previous bid. Try again.")


def main() -> None:
    """Run Liar's Dice."""

    print("LIAR'S DICE".center(50, "="))
    total_players, ai_players = _prompt_configuration()
    game = LiarsDiceGame(num_players=total_players)
    game.state = GameState.IN_PROGRESS

    ai_indices = set(range(total_players - ai_players, total_players)) if ai_players else set()
    ai_strategies: Dict[int, HeuristicStrategy[Tuple[int, int], LiarsDiceGame]] = {idx: game.create_adaptive_ai() for idx in ai_indices}

    while not game.is_game_over():
        _print_table_state(game)
        player = game.get_current_player()

        if player in ai_indices:
            _handle_ai_turn(game, ai_strategies[player])
        else:
            _handle_human_turn(game)

    winner = game.get_winner()
    assert winner is not None
    print(f"\nPlayer {winner + 1} wins!")


if __name__ == "__main__":
    main()
