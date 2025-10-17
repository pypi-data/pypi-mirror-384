"""Liar's Dice game engine."""

from __future__ import annotations

import random
from typing import List, Tuple

from common.ai_strategy import HeuristicStrategy
from common.game_engine import GameEngine, GameState


class LiarsDiceGame(GameEngine[Tuple[int, int], int]):
    """Liar's Dice bluffing game.

    Players roll dice secretly and make bids on total dice values
    across all players. Challenge or raise bids.
    """

    def __init__(
        self,
        num_players: int = 2,
        dice_per_player: int = 5,
        rng: random.Random | None = None,
    ) -> None:
        """Initialize game.

        Args:
            num_players: Number of players participating.
            dice_per_player: Dice allocated to each player.
            rng: Optional random generator for deterministic outcomes.
        """
        self.num_players = max(2, num_players)
        self.dice_per_player = dice_per_player
        self.rng = rng or random.Random()
        self.reset()

    def reset(self) -> None:
        """Reset game."""
        self.state = GameState.NOT_STARTED
        self.player_dice = [[self.rng.randint(1, 6) for _ in range(self.dice_per_player)] for _ in range(self.num_players)]
        self.current_player_idx = 0
        self.current_bid: Tuple[int, int] | None = None  # (quantity, face_value)
        self.eliminated = [False] * self.num_players

    def is_game_over(self) -> bool:
        """Check if game over."""
        return sum(not e for e in self.eliminated) <= 1

    def get_current_player(self) -> int:
        """Get current player."""
        return self.current_player_idx

    def get_valid_moves(self) -> List[Tuple[int, int]]:
        """Get valid moves: (quantity, face) or (-1, -1) for challenge."""
        if self.current_bid is None:
            return [(q, f) for q in range(1, self.num_players * self.dice_per_player + 1) for f in range(1, 7)]
        return [(q, f) for q in range(self.current_bid[0], self.num_players * self.dice_per_player + 1) for f in range(1, 7) if (q, f) > self.current_bid] + [
            (-1, -1)
        ]

    def make_move(self, move: Tuple[int, int]) -> bool:
        """Make a bid or challenge."""
        if self.state == GameState.NOT_STARTED:
            self.state = GameState.IN_PROGRESS

        if move == (-1, -1):  # Challenge
            return self._resolve_challenge()

        quantity, face = move
        if self.current_bid is None or (quantity, face) > self.current_bid:
            self.current_bid = (quantity, face)
            self._next_player()
            return True
        return False

    def _resolve_challenge(self) -> bool:
        """Resolve a challenge."""
        if self.current_bid is None:
            return False

        quantity, face = self.current_bid
        actual = sum(d.count(face) for d in self.player_dice if d)

        if actual >= quantity:
            # Bid was good, challenger loses
            self.player_dice[self.current_player_idx] = self.player_dice[self.current_player_idx][:-1]
        else:
            # Bid was bluff, bidder loses
            prev_player = (self.current_player_idx - 1) % self.num_players
            self.player_dice[prev_player] = self.player_dice[prev_player][:-1]

        # Check elimination
        for i, dice in enumerate(self.player_dice):
            if len(dice) == 0:
                self.eliminated[i] = True

        self.current_bid = None
        return True

    def _next_player(self) -> None:
        """Move to next non-eliminated player."""
        self.current_player_idx = (self.current_player_idx + 1) % self.num_players
        while self.eliminated[self.current_player_idx]:
            self.current_player_idx = (self.current_player_idx + 1) % self.num_players

    def get_winner(self) -> int | None:
        """Get winner."""
        if not self.is_game_over():
            return None
        for i, elim in enumerate(self.eliminated):
            if not elim:
                return i
        return None

    def get_game_state(self) -> GameState:
        """Get current game state.

        Returns:
            Current state of the game
        """
        return self.state

    def create_adaptive_ai(self) -> HeuristicStrategy[Tuple[int, int], "LiarsDiceGame"]:
        """Return a heuristic AI tuned for bluff detection and bidding."""

        return HeuristicStrategy(heuristic_fn=_liars_dice_move_heuristic)

    def get_active_dice_total(self) -> int:
        """Return the total number of dice still in play."""

        return sum(len(dice) for idx, dice in enumerate(self.player_dice) if not self.eliminated[idx])


def _liars_dice_move_heuristic(move: Tuple[int, int], game: LiarsDiceGame) -> float:
    """Score Liar's Dice moves using expected dice counts.

    Args:
        move: Proposed move from the AI strategy.
        game: Current Liar's Dice game engine instance.

    Returns:
        A floating point score representing the desirability of the move.
    """

    quantity, face = move
    current_player = game.get_current_player()
    player_dice = game.player_dice[current_player]
    total_dice = game.get_active_dice_total()
    unseen_dice = total_dice - len(player_dice)
    expected_from_unseen = unseen_dice / 6.0

    if move == (-1, -1):
        if game.current_bid is None:
            return -999.0
        bid_quantity, bid_face = game.current_bid
        visible = player_dice.count(bid_face)
        expected_total = visible + expected_from_unseen
        overbid = bid_quantity - expected_total
        if overbid <= 0:
            return -5.0
        return overbid * 12.0

    if quantity > total_dice or quantity <= 0:
        return -999.0

    visible = player_dice.count(face)
    expected_total = visible + expected_from_unseen
    distance_penalty = (quantity - expected_total) ** 2
    score = 25.0 - distance_penalty
    score += visible * 4.0

    if game.current_bid is not None:
        bid_quantity, bid_face = game.current_bid
        quantity_increase = quantity - bid_quantity
        face_change = face != bid_face
        score -= max(quantity_increase - 1, 0) * 2.5
        if not face_change:
            score -= 1.5
    else:
        score += 2.0 if visible else 0.0

    if quantity == total_dice:
        score -= 8.0

    return score
