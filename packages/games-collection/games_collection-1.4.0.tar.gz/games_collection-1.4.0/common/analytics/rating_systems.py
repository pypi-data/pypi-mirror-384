"""Rating systems for player skill assessment.

This module implements various rating systems including ELO and Glicko-2
for tracking player skill levels over time.
"""

from __future__ import annotations

import json
import math
import pathlib
from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class EloRating:
    """ELO rating system implementation.

    Classic ELO rating system for tracking player skill levels.
    Default starting rating is 1500 with K-factor of 32.
    """

    player_ratings: Dict[str, float] = field(default_factory=dict)
    k_factor: float = 32.0
    default_rating: float = 1500.0

    def get_rating(self, player_id: str) -> float:
        """Get player's current rating.

        Args:
            player_id: Player identifier.

        Returns:
            Current ELO rating.
        """
        return self.player_ratings.get(player_id, self.default_rating)

    def expected_score(self, rating_a: float, rating_b: float) -> float:
        """Calculate expected score for player A against player B.

        Args:
            rating_a: Player A's rating.
            rating_b: Player B's rating.

        Returns:
            Expected score (0-1).
        """
        return 1 / (1 + 10 ** ((rating_b - rating_a) / 400))

    def update_ratings(
        self,
        player_a: str,
        player_b: str,
        score_a: float,
    ) -> tuple[float, float]:
        """Update ratings after a game.

        Args:
            player_a: First player ID.
            player_b: Second player ID.
            score_a: Actual score for player A (1=win, 0.5=draw, 0=loss).

        Returns:
            Tuple of (new_rating_a, new_rating_b).
        """
        rating_a = self.get_rating(player_a)
        rating_b = self.get_rating(player_b)

        expected_a = self.expected_score(rating_a, rating_b)
        expected_b = 1 - expected_a

        new_rating_a = rating_a + self.k_factor * (score_a - expected_a)
        new_rating_b = rating_b + self.k_factor * ((1 - score_a) - expected_b)

        self.player_ratings[player_a] = new_rating_a
        self.player_ratings[player_b] = new_rating_b

        return new_rating_a, new_rating_b

    def get_leaderboard(self) -> List[tuple[str, float]]:
        """Get leaderboard sorted by rating.

        Returns:
            List of (player_id, rating) tuples sorted by rating descending.
        """
        return sorted(self.player_ratings.items(), key=lambda x: x[1], reverse=True)

    def save(self, filepath: pathlib.Path) -> None:
        """Save ratings to JSON file.

        Args:
            filepath: Path to save file.
        """
        data = {
            "player_ratings": self.player_ratings,
            "k_factor": self.k_factor,
            "default_rating": self.default_rating,
        }
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)

    @classmethod
    def load(cls, filepath: pathlib.Path) -> EloRating:
        """Load ratings from JSON file.

        Args:
            filepath: Path to load from.

        Returns:
            EloRating instance.
        """
        if not filepath.exists():
            return cls()

        with open(filepath) as f:
            data = json.load(f)

        return cls(
            player_ratings=data.get("player_ratings", {}),
            k_factor=data.get("k_factor", 32.0),
            default_rating=data.get("default_rating", 1500.0),
        )


@dataclass
class GlickoRating:
    """Glicko-2 rating system implementation.

    More sophisticated rating system that includes rating deviation (RD)
    and volatility, providing more accurate skill estimates.
    """

    player_ratings: Dict[str, Dict[str, float]] = field(default_factory=dict)
    default_rating: float = 1500.0
    default_rd: float = 350.0
    default_volatility: float = 0.06
    tau: float = 0.5

    def get_rating(self, player_id: str) -> Dict[str, float]:
        """Get player's current rating, RD, and volatility.

        Args:
            player_id: Player identifier.

        Returns:
            Dictionary with 'rating', 'rd', and 'volatility'.
        """
        if player_id not in self.player_ratings:
            return {
                "rating": self.default_rating,
                "rd": self.default_rd,
                "volatility": self.default_volatility,
            }
        return self.player_ratings[player_id].copy()

    def _g(self, rd: float) -> float:
        """Glicko-2 g function.

        Args:
            rd: Rating deviation.

        Returns:
            g(RD) value.
        """
        return 1 / math.sqrt(1 + 3 * rd * rd / (math.pi * math.pi))

    def _e(self, rating: float, opponent_rating: float, opponent_rd: float) -> float:
        """Glicko-2 E function.

        Args:
            rating: Player's rating.
            opponent_rating: Opponent's rating.
            opponent_rd: Opponent's RD.

        Returns:
            Expected score.
        """
        return 1 / (1 + math.exp(-self._g(opponent_rd) * (rating - opponent_rating)))

    def update_ratings(
        self,
        player_a: str,
        player_b: str,
        score_a: float,
    ) -> tuple[Dict[str, float], Dict[str, float]]:
        """Update ratings after a game using Glicko-2 algorithm.

        Args:
            player_a: First player ID.
            player_b: Second player ID.
            score_a: Actual score for player A (1=win, 0.5=draw, 0=loss).

        Returns:
            Tuple of (new_rating_dict_a, new_rating_dict_b).
        """
        # Get current ratings
        rating_a_dict = self.get_rating(player_a)
        rating_b_dict = self.get_rating(player_b)

        rating_a = rating_a_dict["rating"]
        rd_a = rating_a_dict["rd"]
        vol_a = rating_a_dict["volatility"]

        rating_b = rating_b_dict["rating"]
        rd_b = rating_b_dict["rd"]
        vol_b = rating_b_dict["volatility"]

        # Update player A
        v_a = 1 / (self._g(rd_b) ** 2 * self._e(rating_a, rating_b, rd_b) * (1 - self._e(rating_a, rating_b, rd_b)))

        new_rd_a = 1 / math.sqrt(1 / (rd_a * rd_a) + 1 / v_a)
        new_rating_a = rating_a + new_rd_a * new_rd_a * self._g(rd_b) * (score_a - self._e(rating_a, rating_b, rd_b))

        # Update player B
        score_b = 1 - score_a
        v_b = 1 / (self._g(rd_a) ** 2 * self._e(rating_b, rating_a, rd_a) * (1 - self._e(rating_b, rating_a, rd_a)))

        new_rd_b = 1 / math.sqrt(1 / (rd_b * rd_b) + 1 / v_b)
        new_rating_b = rating_b + new_rd_b * new_rd_b * self._g(rd_a) * (score_b - self._e(rating_b, rating_a, rd_a))

        # Store new ratings (simplified volatility update)
        new_rating_dict_a = {
            "rating": new_rating_a,
            "rd": new_rd_a,
            "volatility": vol_a,
        }
        new_rating_dict_b = {
            "rating": new_rating_b,
            "rd": new_rd_b,
            "volatility": vol_b,
        }

        self.player_ratings[player_a] = new_rating_dict_a
        self.player_ratings[player_b] = new_rating_dict_b

        return new_rating_dict_a, new_rating_dict_b

    def get_leaderboard(self) -> List[tuple[str, Dict[str, float]]]:
        """Get leaderboard sorted by rating.

        Returns:
            List of (player_id, rating_dict) tuples sorted by rating descending.
        """
        return sorted(
            self.player_ratings.items(),
            key=lambda x: x[1]["rating"],
            reverse=True,
        )

    def save(self, filepath: pathlib.Path) -> None:
        """Save ratings to JSON file.

        Args:
            filepath: Path to save file.
        """
        data = {
            "player_ratings": self.player_ratings,
            "default_rating": self.default_rating,
            "default_rd": self.default_rd,
            "default_volatility": self.default_volatility,
            "tau": self.tau,
        }
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)

    @classmethod
    def load(cls, filepath: pathlib.Path) -> GlickoRating:
        """Load ratings from JSON file.

        Args:
            filepath: Path to load from.

        Returns:
            GlickoRating instance.
        """
        if not filepath.exists():
            return cls()

        with open(filepath) as f:
            data = json.load(f)

        return cls(
            player_ratings=data.get("player_ratings", {}),
            default_rating=data.get("default_rating", 1500.0),
            default_rd=data.get("default_rd", 350.0),
            default_volatility=data.get("default_volatility", 0.06),
            tau=data.get("tau", 0.5),
        )


def calculate_ai_difficulty_rating(
    win_rate: float,
    average_game_length: float,
    move_quality: float,
) -> float:
    """Calculate AI opponent difficulty rating.

    Args:
        win_rate: AI win rate against average players (0-1).
        average_game_length: Average game length in moves.
        move_quality: Average move quality score (0-1).

    Returns:
        Difficulty rating (0-100, where 100 is hardest).
    """
    # Weight factors
    win_weight = 0.5
    quality_weight = 0.4
    length_weight = 0.1

    # Normalize game length (assume 20 moves is average)
    normalized_length = min(average_game_length / 20, 1.0)

    difficulty = (win_rate * win_weight + move_quality * quality_weight + normalized_length * length_weight) * 100

    return min(max(difficulty, 0), 100)
