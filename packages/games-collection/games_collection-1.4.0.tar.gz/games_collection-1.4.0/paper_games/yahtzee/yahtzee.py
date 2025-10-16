"""Core logic and CLI for Yahtzee.

This module implements the dice scoring game where players roll five dice
up to three times per turn, trying to achieve specific combinations for points.
"""

from __future__ import annotations

import random
from collections import Counter
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Set

from common.game_engine import GameEngine, GameState


class YahtzeeCategory(Enum):
    """Scoring categories in Yahtzee."""

    ONES = "ones"
    TWOS = "twos"
    THREES = "threes"
    FOURS = "fours"
    FIVES = "fives"
    SIXES = "sixes"
    THREE_OF_A_KIND = "three_of_a_kind"
    FOUR_OF_A_KIND = "four_of_a_kind"
    FULL_HOUSE = "full_house"
    SMALL_STRAIGHT = "small_straight"
    LARGE_STRAIGHT = "large_straight"
    YAHTZEE = "yahtzee"
    CHANCE = "chance"


@dataclass(frozen=True)
class YahtzeeMove:
    """Representation of a Yahtzee move (scoring a category)."""

    category: YahtzeeCategory


class YahtzeeGame(GameEngine[YahtzeeMove, int]):
    """Yahtzee game implementation with dice rolling and scoring."""

    CATEGORY_NAMES = {
        YahtzeeCategory.ONES: "Ones",
        YahtzeeCategory.TWOS: "Twos",
        YahtzeeCategory.THREES: "Threes",
        YahtzeeCategory.FOURS: "Fours",
        YahtzeeCategory.FIVES: "Fives",
        YahtzeeCategory.SIXES: "Sixes",
        YahtzeeCategory.THREE_OF_A_KIND: "Three of a Kind",
        YahtzeeCategory.FOUR_OF_A_KIND: "Four of a Kind",
        YahtzeeCategory.FULL_HOUSE: "Full House",
        YahtzeeCategory.SMALL_STRAIGHT: "Small Straight",
        YahtzeeCategory.LARGE_STRAIGHT: "Large Straight",
        YahtzeeCategory.YAHTZEE: "Yahtzee",
        YahtzeeCategory.CHANCE: "Chance",
    }

    def __init__(self, num_players: int = 1) -> None:
        """Initialize Yahtzee game.

        Args:
            num_players: Number of players (1-4)
        """
        if num_players < 1 or num_players > 4:
            raise ValueError("Number of players must be between 1 and 4")

        self.num_players = num_players
        self._current_player = 0
        self._dice: List[int] = []
        self._rolls_left = 3
        self._scores: List[Dict[YahtzeeCategory, Optional[int]]] = []
        self._used_categories: List[Set[YahtzeeCategory]] = []
        self._turns_played: List[int] = []
        self._state = GameState.NOT_STARTED
        self._winner: Optional[int] = None
        self.reset()

    def reset(self) -> None:
        """Reset the game to initial state."""
        self._current_player = 0
        self._dice = [1, 1, 1, 1, 1]
        self._rolls_left = 3
        self._scores = [{category: None for category in YahtzeeCategory} for _ in range(self.num_players)]
        self._used_categories = [set() for _ in range(self.num_players)]
        self._turns_played = [0] * self.num_players
        self._state = GameState.IN_PROGRESS
        self._winner = None

    def is_game_over(self) -> bool:
        """Check if the game has ended (all categories used by all players)."""
        if self._state == GameState.FINISHED:
            return True
        # Game ends when all players have used all 13 categories
        return all(len(used) == 13 for used in self._used_categories)

    def get_current_player(self) -> int:
        """Get the current player (0-indexed)."""
        return self._current_player

    def get_valid_moves(self) -> List[YahtzeeMove]:
        """Get valid moves (unused categories)."""
        if self.is_game_over():
            return []
        unused = set(YahtzeeCategory) - self._used_categories[self._current_player]
        return [YahtzeeMove(category=cat) for cat in unused]

    def roll_dice(self, keep: Optional[List[int]] = None) -> List[int]:
        """Roll the dice, optionally keeping some.

        Args:
            keep: List of dice indices (0-4) to keep from previous roll

        Returns:
            The new dice values
        """
        if self._rolls_left <= 0:
            return self._dice

        if keep is None:
            keep = []

        # Roll non-kept dice
        for i in range(5):
            if i not in keep:
                self._dice[i] = random.randint(1, 6)

        self._rolls_left -= 1
        return self._dice.copy()

    def calculate_score(self, category: YahtzeeCategory, dice: Optional[List[int]] = None) -> int:
        """Calculate score for a category given dice values.

        Args:
            category: The category to score
            dice: The dice values (uses current if None)

        Returns:
            The score for this category
        """
        if dice is None:
            dice = self._dice

        counts = Counter(dice)
        total = sum(dice)

        # Upper section (ones through sixes)
        if category == YahtzeeCategory.ONES:
            return counts[1] * 1
        elif category == YahtzeeCategory.TWOS:
            return counts[2] * 2
        elif category == YahtzeeCategory.THREES:
            return counts[3] * 3
        elif category == YahtzeeCategory.FOURS:
            return counts[4] * 4
        elif category == YahtzeeCategory.FIVES:
            return counts[5] * 5
        elif category == YahtzeeCategory.SIXES:
            return counts[6] * 6

        # Lower section
        elif category == YahtzeeCategory.THREE_OF_A_KIND:
            return total if any(count >= 3 for count in counts.values()) else 0
        elif category == YahtzeeCategory.FOUR_OF_A_KIND:
            return total if any(count >= 4 for count in counts.values()) else 0
        elif category == YahtzeeCategory.FULL_HOUSE:
            values = sorted(counts.values())
            return 25 if values == [2, 3] else 0
        elif category == YahtzeeCategory.SMALL_STRAIGHT:
            sorted_dice = sorted(set(dice))
            # Check for sequences of 4
            for i in range(len(sorted_dice) - 3):
                if sorted_dice[i : i + 4] == list(range(sorted_dice[i], sorted_dice[i] + 4)):
                    return 30
            return 0
        elif category == YahtzeeCategory.LARGE_STRAIGHT:
            sorted_dice = sorted(dice)
            if sorted_dice == [1, 2, 3, 4, 5] or sorted_dice == [2, 3, 4, 5, 6]:
                return 40
            return 0
        elif category == YahtzeeCategory.YAHTZEE:
            return 50 if len(counts) == 1 else 0
        elif category == YahtzeeCategory.CHANCE:
            return total

        return 0

    def make_move(self, move: YahtzeeMove) -> bool:
        """Execute a move (score a category).

        Args:
            move: The category to score

        Returns:
            True if move was valid and executed
        """
        if self.is_game_over():
            return False

        if move.category in self._used_categories[self._current_player]:
            return False

        # Score the category
        score = self.calculate_score(move.category)
        self._scores[self._current_player][move.category] = score
        self._used_categories[self._current_player].add(move.category)
        self._turns_played[self._current_player] += 1

        # Reset for next turn
        self._rolls_left = 3
        self._dice = [1, 1, 1, 1, 1]

        # Next player
        self._current_player = (self._current_player + 1) % self.num_players

        # Check if game is over
        if self.is_game_over():
            self._state = GameState.FINISHED
            self._determine_winner()

        return True

    def _determine_winner(self) -> None:
        """Determine the winner based on total scores."""
        totals = [self.get_total_score(i) for i in range(self.num_players)]
        max_score = max(totals)
        self._winner = totals.index(max_score)

    def get_winner(self) -> Optional[int]:
        """Get the winner if game is over."""
        return self._winner

    def get_game_state(self) -> GameState:
        """Get the current game state."""
        return self._state

    def get_state_representation(self) -> Dict[str, any]:
        """Get a representation of the game state."""
        return {
            "dice": tuple(self._dice),
            "rolls_left": self._rolls_left,
            "current_player": self._current_player,
            "scores": [{cat.value: score for cat, score in player_scores.items()} for player_scores in self._scores],
        }

    def get_total_score(self, player: int) -> int:
        """Calculate total score for a player including bonus.

        Args:
            player: Player index (0-indexed)

        Returns:
            Total score including upper section bonus
        """
        if player < 0 or player >= self.num_players:
            raise ValueError(f"Player must be between 0 and {self.num_players - 1}")

        scores = self._scores[player]

        # Upper section
        upper = sum(
            scores.get(cat, 0) or 0
            for cat in [
                YahtzeeCategory.ONES,
                YahtzeeCategory.TWOS,
                YahtzeeCategory.THREES,
                YahtzeeCategory.FOURS,
                YahtzeeCategory.FIVES,
                YahtzeeCategory.SIXES,
            ]
        )

        # Bonus for upper section >= 63
        bonus = 35 if upper >= 63 else 0

        # Lower section
        lower = sum(
            scores.get(cat, 0) or 0
            for cat in [
                YahtzeeCategory.THREE_OF_A_KIND,
                YahtzeeCategory.FOUR_OF_A_KIND,
                YahtzeeCategory.FULL_HOUSE,
                YahtzeeCategory.SMALL_STRAIGHT,
                YahtzeeCategory.LARGE_STRAIGHT,
                YahtzeeCategory.YAHTZEE,
                YahtzeeCategory.CHANCE,
            ]
        )

        return upper + bonus + lower

    def get_dice(self) -> List[int]:
        """Get the current dice values."""
        return self._dice.copy()

    def get_rolls_left(self) -> int:
        """Get the number of rolls remaining this turn."""
        return self._rolls_left


class YahtzeeCLI:
    """Command line interface for Yahtzee."""

    def __init__(self) -> None:
        """Initialize the CLI."""
        self.game: Optional[YahtzeeGame] = None

    def run(self) -> None:
        """Run the game loop."""
        print("Welcome to Yahtzee!")
        print("=" * 60)

        # Get number of players
        while True:
            try:
                num_players = int(input("Enter number of players (1-4): "))
                if 1 <= num_players <= 4:
                    break
                print("Please enter a number between 1 and 4")
            except ValueError:
                print("Please enter a valid number")

        self.game = YahtzeeGame(num_players=num_players)

        print(f"\nStarting game with {num_players} player(s)!")
        print("Roll dice up to 3 times per turn, then score a category.")
        print()

        # Game loop
        while not self.game.is_game_over():
            self._play_turn()

        # Game over
        self._show_final_scores()

    def _play_turn(self) -> None:
        """Play one turn for the current player."""
        if self.game is None:
            return

        current = self.game.get_current_player()
        print(f"\n{'=' * 60}")
        print(f"Player {current + 1}'s Turn")
        print(f"{'=' * 60}")

        # Show current scorecard
        self._show_scorecard(current)

        # Reset rolls for new turn
        self.game._rolls_left = 3

        # Rolling phase
        while self.game.get_rolls_left() > 0:
            input("\nPress Enter to roll the dice...")

            if self.game.get_rolls_left() == 3:
                # First roll - roll all dice
                self.game.roll_dice()
            else:
                # Subsequent rolls - ask which to keep
                keep_input = input("Enter dice positions to keep (1-5, or 'all' to keep all): ")
                if keep_input.lower() == "all":
                    break
                try:
                    keep = [int(x) - 1 for x in keep_input.split() if x.strip().isdigit()]
                    keep = [k for k in keep if 0 <= k < 5]
                    self.game.roll_dice(keep=keep)
                except ValueError:
                    self.game.roll_dice()

            # Show dice
            dice = self.game.get_dice()
            print(f"\n🎲 Dice: {' '.join(str(d) for d in dice)}")
            print("   Positions: 1  2  3  4  5")
            print(f"Rolls left: {self.game.get_rolls_left()}")

            if self.game.get_rolls_left() > 0:
                reroll = input("\nReroll? (y/n): ").lower()
                if reroll != "y":
                    break

        # Scoring phase
        print("\n--- Choose a category to score ---")
        self._show_available_categories()

        while True:
            choice = input("\nEnter category number: ").strip()
            try:
                cat_idx = int(choice) - 1
                valid_moves = self.game.get_valid_moves()
                if 0 <= cat_idx < len(valid_moves):
                    move = valid_moves[cat_idx]
                    score = self.game.calculate_score(move.category)
                    print(f"Scoring {self.game.CATEGORY_NAMES[move.category]}: {score} points")
                    self.game.make_move(move)
                    break
                else:
                    print("Invalid category number")
            except (ValueError, IndexError):
                print("Please enter a valid number")

    def _show_scorecard(self, player: int) -> None:
        """Show the scorecard for a player."""
        if self.game is None:
            return

        print(f"\nPlayer {player + 1}'s Scorecard:")
        print("-" * 40)

        scores = self.game._scores[player]

        # Upper section
        print("UPPER SECTION:")
        upper_cats = [
            YahtzeeCategory.ONES,
            YahtzeeCategory.TWOS,
            YahtzeeCategory.THREES,
            YahtzeeCategory.FOURS,
            YahtzeeCategory.FIVES,
            YahtzeeCategory.SIXES,
        ]
        upper_total = 0
        for cat in upper_cats:
            score = scores[cat]
            score_str = str(score) if score is not None else "-"
            print(f"  {self.game.CATEGORY_NAMES[cat]:20s}: {score_str:>3s}")
            if score is not None:
                upper_total += score

        print(f"  {'Upper Total':20s}: {upper_total:>3d}")
        bonus = 35 if upper_total >= 63 else 0
        print(f"  {'Bonus (63+)':20s}: {bonus:>3d}")

        # Lower section
        print("\nLOWER SECTION:")
        lower_cats = [
            YahtzeeCategory.THREE_OF_A_KIND,
            YahtzeeCategory.FOUR_OF_A_KIND,
            YahtzeeCategory.FULL_HOUSE,
            YahtzeeCategory.SMALL_STRAIGHT,
            YahtzeeCategory.LARGE_STRAIGHT,
            YahtzeeCategory.YAHTZEE,
            YahtzeeCategory.CHANCE,
        ]
        for cat in lower_cats:
            score = scores[cat]
            score_str = str(score) if score is not None else "-"
            print(f"  {self.game.CATEGORY_NAMES[cat]:20s}: {score_str:>3s}")

        print(f"\n  {'TOTAL SCORE':20s}: {self.game.get_total_score(player):>3d}")
        print("-" * 40)

    def _show_available_categories(self) -> None:
        """Show available categories with potential scores."""
        if self.game is None:
            return

        valid_moves = self.game.get_valid_moves()
        for idx, move in enumerate(valid_moves, 1):
            score = self.game.calculate_score(move.category)
            print(f"  {idx}. {self.game.CATEGORY_NAMES[move.category]:20s} ({score} pts)")

    def _show_final_scores(self) -> None:
        """Show final scores and winner."""
        if self.game is None:
            return

        print(f"\n{'=' * 60}")
        print("GAME OVER - Final Scores")
        print(f"{'=' * 60}")

        for i in range(self.game.num_players):
            total = self.game.get_total_score(i)
            print(f"Player {i + 1}: {total} points")

        winner = self.game.get_winner()
        if winner is not None:
            print(f"\n🎉 Player {winner + 1} wins! 🎉")
        print(f"{'=' * 60}")
