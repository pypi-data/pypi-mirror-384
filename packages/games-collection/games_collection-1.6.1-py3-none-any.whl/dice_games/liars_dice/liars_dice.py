"""Liar's Dice game engine.

This module provides the core implementation of the Liar's Dice game, a classic
game of bluffing and statistical reasoning. Each player has a cup of dice, which
they roll and keep hidden from others. Players then take turns making bids on
the total number of dice of a certain face value across all players' hands.

The game proceeds with players either raising the bid or challenging the
previous bid. When a challenge occurs, the dice are revealed, and one player
loses a die. The last player with dice remaining wins.

Classes:
    LiarsDiceGame: The main engine for managing the game state and rules.

Functions:
    _liars_dice_move_heuristic: A heuristic function for AI decision-making.
"""

from __future__ import annotations

import random
from typing import List, Tuple

from common.ai_strategy import HeuristicStrategy
from common.game_engine import GameEngine, GameState


class LiarsDiceGame(GameEngine[Tuple[int, int], int]):
    """A game engine for Liar's Dice.

    This class manages the game state, including player dice, bids, and player
    elimination. It enforces the rules of bidding and challenges.

    A move is represented as a tuple `(quantity, face_value)`. A challenge is
    represented by the special move `(-1, -1)`.
    """

    def __init__(
        self,
        num_players: int = 2,
        dice_per_player: int = 5,
        rng: random.Random | None = None,
    ) -> None:
        """Initializes the Liar's Dice game.

        Args:
            num_players: The number of players participating in the game.
            dice_per_player: The number of dice each player starts with.
            rng: An optional random number generator for deterministic outcomes.
        """
        self.num_players = max(2, num_players)
        self.dice_per_player = dice_per_player
        self.rng = rng or random.Random()
        self.reset()

    def reset(self) -> None:
        """Resets the game to its initial state for a new round."""
        self.state = GameState.NOT_STARTED
        # Each player gets a new set of dice.
        self.player_dice = [[self.rng.randint(1, 6) for _ in range(self.dice_per_player)] for _ in range(self.num_players)]
        self.current_player_idx = 0
        self.current_bid: Tuple[int, int] | None = None  # (quantity, face_value)
        self.eliminated = [False] * self.num_players

    def is_game_over(self) -> bool:
        """Checks if the game has concluded.

        The game ends when only one player has dice remaining.

        Returns:
            True if the game is over, False otherwise.
        """
        return sum(not e for e in self.eliminated) <= 1

    def get_current_player(self) -> int:
        """Returns the index of the current player.

        Returns:
            The zero-based index of the player whose turn it is.
        """
        return self.current_player_idx

    def get_valid_moves(self) -> List[Tuple[int, int]]:
        """Returns a list of valid moves for the current player.

        A move can be either a new bid or a challenge. A bid is valid if it is
        higher than the current bid, either by quantity or by face value.

        Returns:
            A list of valid moves, where each move is a tuple `(quantity, face)`.
            A challenge is represented as `(-1, -1)`.
        """
        total_dice = self.get_active_dice_total()
        # If there's no current bid, any valid bid is possible.
        if self.current_bid is None:
            return [(q, f) for q in range(1, total_dice + 1) for f in range(1, 7)]

        # Generate all possible higher bids.
        valid_bids = [(q, f) for q in range(self.current_bid[0], total_dice + 1) for f in range(1, 7) if (q, f) > self.current_bid]
        # A challenge is always a valid move if there is a bid.
        return valid_bids + [(-1, -1)]

    def make_move(self, move: Tuple[int, int]) -> bool:
        """Processes a player's move, which can be a bid or a challenge.

        Args:
            move: The move to be made, as a tuple `(quantity, face)`.

        Returns:
            True if the move was valid and processed, False otherwise.
        """
        if self.state == GameState.NOT_STARTED:
            self.state = GameState.IN_PROGRESS

        # A move of (-1, -1) signifies a challenge.
        if move == (-1, -1):
            return self._resolve_challenge()

        # Otherwise, the move is a bid.
        quantity, face = move
        if self.current_bid is None or (quantity, face) > self.current_bid:
            self.current_bid = (quantity, face)
            self._next_player()
            return True
        return False  # Invalid bid.

    def _resolve_challenge(self) -> bool:
        """Resolves a challenge made by the current player.

        The dice are revealed, and the total count of the bid's face value is
        compared to the bid quantity. The loser of the challenge loses one die.

        Returns:
            True if the challenge was successfully resolved, False if there was
            no active bid to challenge.
        """
        if self.current_bid is None:
            return False  # Cannot challenge if there is no bid.

        bid_quantity, bid_face = self.current_bid
        # Count the actual number of dice matching the bid's face value.
        actual_count = sum(d.count(bid_face) for d in self.player_dice if d)

        # Determine the loser of the challenge.
        if actual_count >= bid_quantity:
            # The bid was accurate or an under-call. The challenger loses a die.
            loser_idx = self.current_player_idx
        else:
            # The bid was a bluff. The previous player (the bidder) loses a die.
            loser_idx = (self.current_player_idx - 1 + self.num_players) % self.num_players
            # Ensure the previous player is not eliminated.
            while self.eliminated[loser_idx]:
                loser_idx = (loser_idx - 1 + self.num_players) % self.num_players

        # Remove a die from the loser.
        if self.player_dice[loser_idx]:
            self.player_dice[loser_idx].pop()

        # Check if the loser has been eliminated.
        if not self.player_dice[loser_idx]:
            self.eliminated[loser_idx] = True

        # Start a new round of bidding.
        self.current_bid = None
        # The loser of the challenge starts the next round.
        self.current_player_idx = loser_idx
        return True

    def _next_player(self) -> None:
        """Advances the turn to the next active (non-eliminated) player."""
        self.current_player_idx = (self.current_player_idx + 1) % self.num_players
        # Skip any players who have been eliminated.
        while self.eliminated[self.current_player_idx]:
            self.current_player_idx = (self.current_player_idx + 1) % self.num_players

    def get_winner(self) -> int | None:
        """Determines the winner of the game.

        The winner is the last player remaining who has not been eliminated.

        Returns:
            The index of the winning player, or None if the game is not over.
        """
        if not self.is_game_over():
            return None
        # Find the first player who is not eliminated.
        for i, is_eliminated in enumerate(self.eliminated):
            if not is_eliminated:
                return i
        return None  # Should be unreachable if is_game_over is true.

    def get_game_state(self) -> GameState:
        """Returns the current state of the game.

        Returns:
            The current `GameState`.
        """
        return self.state

    def create_adaptive_ai(self) -> HeuristicStrategy[Tuple[int, int], "LiarsDiceGame"]:
        """Creates a heuristic-based AI strategy for Liar's Dice.

        This AI uses statistical expectations to evaluate bids and challenges.

        Returns:
            A `HeuristicStrategy` instance configured for Liar's Dice.
        """
        return HeuristicStrategy(heuristic_fn=_liars_dice_move_heuristic)

    def get_active_dice_total(self) -> int:
        """Returns the total number of dice currently in play.

        Returns:
            The sum of dice held by all non-eliminated players.
        """
        return sum(len(dice) for idx, dice in enumerate(self.player_dice) if not self.eliminated[idx])


def _liars_dice_move_heuristic(move: Tuple[int, int], game: LiarsDiceGame) -> float:
    """Provides a heuristic evaluation for a move in Liar's Dice.

    This function scores moves based on the statistical likelihood of the bid
    being true, considering the AI's own dice and the expected distribution of
    the unseen dice.

    Args:
        move: The proposed move (a bid or a challenge).
        game: The current state of the game.

    Returns:
        A float representing the desirability of the move. Higher is better.
    """
    quantity, face = move
    current_player_idx = game.get_current_player()
    player_dice = game.player_dice[current_player_idx]
    total_dice = game.get_active_dice_total()
    unseen_dice = total_dice - len(player_dice)
    # The expected number of a given face value from unseen dice is n/6.
    expected_from_unseen = unseen_dice / 6.0

    # Evaluate a challenge.
    if move == (-1, -1):
        if game.current_bid is None:
            return -999.0  # Cannot challenge without a bid.
        bid_quantity, bid_face = game.current_bid
        visible_count = player_dice.count(bid_face)
        expected_total = visible_count + expected_from_unseen
        # The score is proportional to how much of an overbid it seems to be.
        overbid_margin = bid_quantity - expected_total
        return overbid_margin * 12.0 if overbid_margin > 0 else -5.0

    # Evaluate a bid.
    if quantity > total_dice or quantity <= 0:
        return -999.0  # Invalid bid quantity.

    visible_count = player_dice.count(face)
    expected_total = visible_count + expected_from_unseen
    # Penalize bids that deviate significantly from the statistical expectation.
    distance_penalty = (quantity - expected_total) ** 2
    score = 25.0 - distance_penalty
    score += visible_count * 4.0  # Bonus for bidding on faces the AI holds.

    # Adjust score based on the previous bid.
    if game.current_bid is not None:
        bid_quantity, bid_face = game.current_bid
        quantity_increase = quantity - bid_quantity
        face_has_changed = face != bid_face
        # Penalize large jumps in quantity.
        score -= max(quantity_increase - 1, 0) * 2.5
        if not face_has_changed:
            score -= 1.5  # Small penalty for not changing the face value.
    else:
        # Bonus for starting a bid with dice in hand.
        score += 2.0 if visible_count > 0 else 0.0

    # A bid of all dice in play is risky.
    if quantity == total_dice:
        score -= 8.0

    return score
