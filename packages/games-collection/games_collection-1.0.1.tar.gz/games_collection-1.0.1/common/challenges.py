"""Educational challenges and puzzle packs for games.

This module provides pre-defined scenarios and puzzles for practicing game skills.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, List, Optional


class DifficultyLevel(str, Enum):
    """Difficulty levels for challenges."""

    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


@dataclass
class Challenge:
    """Represents an educational challenge or puzzle.

    Attributes:
        id: Unique identifier for the challenge.
        title: Short title describing the challenge.
        description: Detailed description of the scenario.
        difficulty: Difficulty level.
        initial_state: Initial game state for the challenge.
        goal: Description of what needs to be achieved.
        solution: Optional solution or hint.
        validate: Optional function to validate if challenge is solved.
    """

    id: str
    title: str
    description: str
    difficulty: DifficultyLevel
    initial_state: Any
    goal: str
    solution: Optional[str] = None
    validate: Optional[Callable[[Any], bool]] = None


class ChallengePack:
    """Collection of related challenges."""

    def __init__(self, name: str, description: str) -> None:
        """Initialize a challenge pack.

        Args:
            name: Name of the challenge pack.
            description: Description of what the pack covers.
        """
        self.name = name
        self.description = description
        self.challenges: List[Challenge] = []

    def add_challenge(self, challenge: Challenge) -> None:
        """Add a challenge to this pack.

        Args:
            challenge: Challenge to add.
        """
        self.challenges.append(challenge)

    def get_challenge(self, challenge_id: str) -> Optional[Challenge]:
        """Get a challenge by ID.

        Args:
            challenge_id: ID of the challenge.

        Returns:
            Challenge if found, None otherwise.
        """
        for challenge in self.challenges:
            if challenge.id == challenge_id:
                return challenge
        return None

    def get_challenges_by_difficulty(self, difficulty: DifficultyLevel) -> List[Challenge]:
        """Get all challenges of a specific difficulty.

        Args:
            difficulty: Difficulty level to filter by.

        Returns:
            List of challenges matching the difficulty.
        """
        return [c for c in self.challenges if c.difficulty == difficulty]

    def __len__(self) -> int:
        """Return number of challenges in pack."""
        return len(self.challenges)


class ChallengeManager:
    """Manages all challenge packs across games."""

    def __init__(self) -> None:
        """Initialize challenge manager."""
        self.packs: dict[str, ChallengePack] = {}

    def register_pack(self, pack: ChallengePack) -> None:
        """Register a challenge pack.

        Args:
            pack: Challenge pack to register.
        """
        self.packs[pack.name] = pack

    def get_pack(self, name: str) -> Optional[ChallengePack]:
        """Get a challenge pack by name.

        Args:
            name: Name of the pack.

        Returns:
            ChallengePack if found, None otherwise.
        """
        return self.packs.get(name)

    def list_packs(self) -> List[str]:
        """List all available challenge packs.

        Returns:
            List of pack names.
        """
        return list(self.packs.keys())


# Poker Challenges
def create_poker_challenges() -> ChallengePack:
    """Create poker challenge pack.

    Returns:
        ChallengePack with poker scenarios.
    """
    pack = ChallengePack(
        name="Poker Fundamentals",
        description="Practice fundamental poker concepts and decision-making.",
    )

    pack.add_challenge(
        Challenge(
            id="poker_pot_odds_1",
            title="Basic Pot Odds",
            description=(
                "You're on the turn with a flush draw (9 outs). " "Pot is $100 and opponent bets $20. Should you call?\n\n" "Calculate: Pot odds vs Your equity"
            ),
            difficulty=DifficultyLevel.BEGINNER,
            initial_state={"pot": 100, "bet": 20, "outs": 9},
            goal="Determine if calling is profitable based on pot odds.",
            solution=("Pot odds = $20 / ($100 + $20) = 16.7%\n" "Equity with 9 outs (~36% rule): 9 × 2 = 18%\n" "18% > 16.7% → CALL is profitable!"),
        )
    )

    pack.add_challenge(
        Challenge(
            id="poker_position_1",
            title="Position Advantage",
            description=(
                "You have Q-J offsuit. Early position player raises 3x BB. "
                "You're on the button. Should you call, raise, or fold?\n\n"
                "Consider: Your position, opponent's range, hand strength"
            ),
            difficulty=DifficultyLevel.INTERMEDIATE,
            initial_state={"hand": "QJo", "position": "button", "action": "facing_raise"},
            goal="Make the optimal decision given position and hand strength.",
            solution=(
                "CALL is likely best. Q-J offsuit is too weak to 3-bet but has "
                "good playability in position. Folding is too tight from button. "
                "Your position advantage allows you to realize equity post-flop."
            ),
        )
    )

    pack.add_challenge(
        Challenge(
            id="poker_bluff_spot",
            title="River Bluff Decision",
            description=(
                "You missed your straight draw. Board: A♠ K♦ 7♣ 3♥ 2♣. "
                "Pot is $150. You have $100 left. Opponent checks to you. "
                "Should you bluff?\n\n"
                "Consider: Your range, opponent's likely hands, bluff sizing"
            ),
            difficulty=DifficultyLevel.ADVANCED,
            initial_state={"pot": 150, "stack": 100, "board": "AK732", "missed_draw": True},
            goal="Decide whether to bluff and with what sizing.",
            solution=(
                "Strong bluff spot! Opponent checked showing weakness. "
                "Bet ~$80 (representing Ace or King). You need opponent to fold ~35% "
                "of the time to profit. They likely have weak pairs or missed draws. "
                "Your perceived range includes many strong hands on this board."
            ),
        )
    )

    return pack


# Blackjack Challenges
def create_blackjack_challenges() -> ChallengePack:
    """Create blackjack challenge pack.

    Returns:
        ChallengePack with blackjack scenarios.
    """
    pack = ChallengePack(
        name="Blackjack Mastery",
        description="Master basic strategy and card counting scenarios.",
    )

    pack.add_challenge(
        Challenge(
            id="blackjack_basic_1",
            title="Hard 16 vs Dealer 10",
            description=("You have 10-6 (hard 16). Dealer shows 10. " "What's the correct play?\n\n" "Options: Hit, Stand, Double, Surrender (if allowed)"),
            difficulty=DifficultyLevel.BEGINNER,
            initial_state={"player": 16, "dealer": 10, "soft": False},
            goal="Apply basic strategy correctly.",
            solution=(
                "HIT (or surrender if allowed). Hard 16 vs 10 is one of the worst "
                "hands in blackjack. You have ~77% chance to bust if hitting, but "
                "standing has even worse expected value since dealer will likely "
                "make 17-21. If surrender is available, that's actually the best play!"
            ),
        )
    )

    pack.add_challenge(
        Challenge(
            id="blackjack_soft_hands",
            title="Soft 18 Decision",
            description=(
                "You have A-7 (soft 18). Dealer shows 9. " "Should you hit, stand, or double?\n\n" "Consider: Dealer's strong upcard, your hand flexibility"
            ),
            difficulty=DifficultyLevel.INTERMEDIATE,
            initial_state={"player": 18, "dealer": 9, "soft": True, "can_double": True},
            goal="Make the correct decision with a soft hand.",
            solution=(
                "HIT. Against dealer 9, 10, or Ace, soft 18 needs improvement. "
                "You can't bust (the Ace can count as 1), so there's no risk in hitting. "
                "Dealer showing 9 likely has 19, so you need to improve your 18. "
                "Don't double here - you want the option to hit multiple times."
            ),
        )
    )

    pack.add_challenge(
        Challenge(
            id="blackjack_counting_1",
            title="Card Counting Decision",
            description=(
                "Running count is +12, 3 decks remaining (true count +4). "
                "You have 12, dealer shows 3. Basic strategy says hit. "
                "Should you deviate?\n\n"
                "Consider: True count, basic strategy, index plays"
            ),
            difficulty=DifficultyLevel.ADVANCED,
            initial_state={"player": 12, "dealer": 3, "true_count": 4},
            goal="Decide whether to use a counting deviation from basic strategy.",
            solution=(
                "STAND. With true count +4, the deck is very rich in high cards. "
                "This increases dealer's bust probability significantly. The index "
                "play for 12 vs 3 is +2, so at +4 you should definitely stand. "
                "This is a profitable deviation from basic strategy."
            ),
        )
    )

    return pack


# Nim Challenges
def create_nim_challenges() -> ChallengePack:
    """Create Nim challenge pack.

    Returns:
        ChallengePack with Nim puzzles.
    """
    pack = ChallengePack(
        name="Nim Puzzles",
        description="Solve Nim positions using game theory and nim-sum.",
    )

    pack.add_challenge(
        Challenge(
            id="nim_basic_1",
            title="Three Heap Nim",
            description=("Heaps: [3, 5, 7]\n" "Find the winning move.\n\n" "Calculate the nim-sum and determine the optimal move."),
            difficulty=DifficultyLevel.BEGINNER,
            initial_state={"heaps": [3, 5, 7]},
            goal="Find the move that results in nim-sum = 0.",
            solution=(
                "Nim-sum: 3 XOR 5 XOR 7 = 1 (winning position!)\n"
                "Winning move: Reduce 7 to 6 → [3, 5, 6]\n"
                "Check: 3 XOR 5 XOR 6 = 0 ✓\n"
                "Alternative: Reduce 5 to 4 → [3, 4, 7] also gives nim-sum 0"
            ),
        )
    )

    pack.add_challenge(
        Challenge(
            id="nim_misere_1",
            title="Misère Endgame",
            description=(
                "Heaps: [1, 1, 1, 1] (Misère rules: last to move LOSES)\n" "What's the winning move?\n\n" "Remember: In misère, the endgame strategy changes!"
            ),
            difficulty=DifficultyLevel.INTERMEDIATE,
            initial_state={"heaps": [1, 1, 1, 1], "misere": True},
            goal="Win under misère rules where taking the last object loses.",
            solution=(
                "Take 1 from any heap → [1, 1, 1, 0]\n"
                "Leaving an ODD number of heaps is winning in misère endgame. "
                "Opponent must take one, leaving 2 heaps. You take one, leaving 1 heap. "
                "Opponent is forced to take the last and loses!"
            ),
        )
    )

    pack.add_challenge(
        Challenge(
            id="nim_advanced_1",
            title="Large Heap Puzzle",
            description=("Heaps: [1, 4, 16, 64]\n" "This position has a pattern. Find the winning move.\n\n" "Hint: These are powers of 2"),
            difficulty=DifficultyLevel.ADVANCED,
            initial_state={"heaps": [1, 4, 16, 64]},
            goal="Solve the puzzle involving powers of 2.",
            solution=(
                "Nim-sum: 1 XOR 4 XOR 16 XOR 64 = 85\n"
                "Winning move: Reduce 64 to 21 → [1, 4, 16, 21]\n"
                "Check: 1 XOR 4 XOR 16 XOR 21 = 0 ✓\n"
                "With powers of 2, the nim-sum reveals which bits are odd. "
                "We need to zero out all odd bits by modifying the largest heap."
            ),
        )
    )

    return pack


# Initialize default challenges
def get_default_challenge_manager() -> ChallengeManager:
    """Get a challenge manager with default challenge packs.

    Returns:
        ChallengeManager with poker, blackjack, and nim challenges loaded.
    """
    manager = ChallengeManager()
    manager.register_pack(create_poker_challenges())
    manager.register_pack(create_blackjack_challenges())
    manager.register_pack(create_nim_challenges())
    return manager
