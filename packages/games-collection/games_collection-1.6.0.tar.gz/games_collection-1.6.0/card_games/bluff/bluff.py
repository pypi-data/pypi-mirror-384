"""Card game engine, AI, and CLI helpers for the game of Bluff (a.k.a. Cheat).

This module provides a comprehensive implementation of the card game "Bluff"
(also known as "Cheat" or "I Doubt It"). It includes the game engine, bot AI,
and hooks for both command-line and graphical user interfaces.

The game is structured around these key components:

* **Phases** – The :class:`Phase` enum models the three states of play
  (``TURN``, ``CHALLENGE``, and ``COMPLETE``) so the engine can react
  appropriately to user and AI choices.
* **Player representation** – :class:`PlayerState` tracks a player's hand, bot
  personality, and historical statistics that inform the AI's decision making.
* **Game state** – The :class:`BluffGame` class manages the deck, discard pile,
  pending challenges, and the overall flow of the match.
* **Bot AI** – Bot behaviour is parameterised by :class:`DifficultyLevel`
  objects, giving each difficulty setting a distinct "personality".
* **User interaction** – Helper functions at the bottom of the module wire the
  engine into an interactive CLI, while :mod:`card_games.bluff.gui` provides a
  Tkinter interface.

In addition to the public API, the module contains numerous helper functions
with richly documented behaviour intended to act as executable documentation for
the game's rules. These docstrings deliberately repeat concepts established in
other parts of the file so that each class or function can be understood in
isolation.
"""

from __future__ import annotations

import argparse
import json
import random
from collections import Counter, deque
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Any, Deque, Dict, Iterable, List, Optional, Sequence

from ..common.cards import RANKS, Card, Deck, Suit


class Phase(Enum):
    """High-level phases of the bluff game lifecycle.

    - ``TURN``: The current player is expected to make a claim.
    - ``CHALLENGE``: Other players have the opportunity to challenge the claim.
    - ``COMPLETE``: The game has ended, and a winner may be declared.
    """

    TURN = auto()
    CHALLENGE = auto()
    COMPLETE = auto()


@dataclass(frozen=True)
class DeckType:
    """Configuration for different types of card decks.

    Attributes:
        name (str): The name of the deck type.
        description (str): A brief description of the deck characteristics.
        ranks (list[str]): The card ranks available in this deck.
        suits (list[Suit]): The suits available in this deck.
        cards_per_rank_suit (int): Number of copies of each rank-suit combination.
    """

    name: str
    description: str
    ranks: list[str]
    suits: list[Suit]
    cards_per_rank_suit: int = 1

    def generate_cards(self, deck_count: int = 1) -> list[Card]:
        """Generate a list of cards based on this deck type."""
        cards: list[Card] = []
        for _ in range(deck_count):
            for _ in range(self.cards_per_rank_suit):
                for suit in self.suits:
                    for rank in self.ranks:
                        cards.append(Card(rank, suit))
        return cards


@dataclass(frozen=True)
class DifficultyLevel:
    """Configuration bucket for bluff bot personalities and game rules.

    This dataclass defines the parameters for a game's difficulty, including
    the number of bots, decks, and the baseline AI characteristics.

    Attributes:
        name (str): The name of the difficulty level (e.g., "Easy", "Hard").
        bot_count (int): The number of bot opponents.
        deck_count (int): The number of standard 52-card decks to use.
        honesty (float): Baseline probability that a bot will play truthfully.
        boldness (float): Multiplier for how much the pile size encourages bluffing.
        challenge (float): Baseline probability that a bot will challenge a claim.
    """

    name: str
    bot_count: int
    deck_count: int
    honesty: float
    boldness: float
    challenge: float


@dataclass(frozen=True)
class PlayerProfile:
    """Traits that drive a bot's bluffing and challenge behaviour.

    Each bot player has a profile that fine-tunes its AI, adding variability
    and personality beyond the base difficulty level.

    Attributes:
        honesty (float): The bot's individual tendency to be truthful.
        boldness (float): How much the bot is influenced by the size of the pile.
        challenge (float): The bot's willingness to call out others.
        memory (float): How much the bot considers other players' history.
    """

    honesty: float
    boldness: float
    challenge: float
    memory: float


@dataclass
class PlayerPattern:
    """Tracks learned patterns about a player's behavior.

    Attributes:
        bluff_rate_by_pile_size (Dict[int, float]): Bluff rate based on pile size.
        bluff_rate_by_card_count (Dict[int, float]): Bluff rate based on hand size.
        preferred_bluff_ranks (Counter[str]): Ranks this player tends to bluff about.
        challenge_aggression (float): How likely they are to challenge.
        recent_behavior (list[bool]): Recent truthfulness (True=truth, False=bluff).
    """

    bluff_rate_by_pile_size: Dict[int, float] = field(default_factory=dict)
    bluff_rate_by_card_count: Dict[int, float] = field(default_factory=dict)
    preferred_bluff_ranks: Counter[str] = field(default_factory=Counter)
    challenge_aggression: float = 0.3
    recent_behavior: list[bool] = field(default_factory=list)

    def update_bluff_pattern(self, was_truthful: bool, pile_size: int, card_count: int, rank: str) -> None:
        """Update pattern tracking after a claim."""
        # Track recent behavior (keep last 10)
        self.recent_behavior.append(was_truthful)
        if len(self.recent_behavior) > 10:
            self.recent_behavior.pop(0)

        # Update pile size pattern
        pile_bucket = (pile_size // 5) * 5  # Bucket by 5s
        if pile_bucket not in self.bluff_rate_by_pile_size:
            self.bluff_rate_by_pile_size[pile_bucket] = 0.5
        current_rate = self.bluff_rate_by_pile_size[pile_bucket]
        # Moving average
        self.bluff_rate_by_pile_size[pile_bucket] = current_rate * 0.8 + (0 if was_truthful else 1) * 0.2

        # Update card count pattern
        card_bucket = (card_count // 3) * 3  # Bucket by 3s
        if card_bucket not in self.bluff_rate_by_card_count:
            self.bluff_rate_by_card_count[card_bucket] = 0.5
        current_rate = self.bluff_rate_by_card_count[card_bucket]
        self.bluff_rate_by_card_count[card_bucket] = current_rate * 0.8 + (0 if was_truthful else 1) * 0.2

        # Track preferred bluff ranks
        if not was_truthful:
            self.preferred_bluff_ranks[rank] += 1

    def get_suspected_bluff_probability(self, pile_size: int, card_count: int, rank: str) -> float:
        """Estimate probability that current claim is a bluff."""
        factors = []

        # Check pile size pattern
        pile_bucket = (pile_size // 5) * 5
        if pile_bucket in self.bluff_rate_by_pile_size:
            factors.append(self.bluff_rate_by_pile_size[pile_bucket])

        # Check card count pattern
        card_bucket = (card_count // 3) * 3
        if card_bucket in self.bluff_rate_by_card_count:
            factors.append(self.bluff_rate_by_card_count[card_bucket])

        # Check if this rank is a preferred bluff rank
        if rank in self.preferred_bluff_ranks:
            total_bluffs = sum(self.preferred_bluff_ranks.values())
            rank_preference = self.preferred_bluff_ranks[rank] / total_bluffs
            factors.append(rank_preference)

        # Check recent behavior
        if len(self.recent_behavior) >= 3:
            recent_bluff_rate = sum(0 if truthful else 1 for truthful in self.recent_behavior[-3:]) / 3
            factors.append(recent_bluff_rate)

        # Average the factors
        if factors:
            return sum(factors) / len(factors)
        return 0.5  # Default neutral probability


@dataclass
class PlayerState:
    """Runtime information about a seated player, including their hand and stats.

    Attributes:
        name (str): The player's display name.
        is_user (bool): True if this player is controlled by a human.
        profile (PlayerProfile): The AI profile for this player.
        rng (random.Random): The random number generator for this player.
        hand (list[Card]): The cards currently held by the player.
        truths (int): The number of truthful claims made.
        lies (int): The number of bluffs made.
        caught (int): The number of times this player was caught bluffing.
        challenge_attempts (int): The number of challenges made.
        challenge_successes (int): The number of successful challenges.
        last_caught_turn (Optional[int]): The turn index when the player was last caught.
        pattern (PlayerPattern): Learned behavioral patterns for this player.
    """

    name: str
    is_user: bool
    profile: PlayerProfile
    rng: random.Random
    hand: list[Card] = field(default_factory=list)
    truths: int = 0
    lies: int = 0
    caught: int = 0
    challenge_attempts: int = 0
    challenge_successes: int = 0
    last_caught_turn: Optional[int] = None
    pattern: PlayerPattern = field(default_factory=PlayerPattern)

    def record_claim(self, truthful: bool) -> None:
        """Update statistics based on a claim being truthful or a bluff."""
        if truthful:
            self.truths += 1
        else:
            self.lies += 1

    def record_caught(self, turn_index: int) -> None:
        """Record that the player was caught in a bluff."""
        self.caught += 1
        self.last_caught_turn = turn_index

    def record_challenge(self, success: bool) -> None:
        """Update statistics after making a challenge."""
        self.challenge_attempts += 1
        if success:
            self.challenge_successes += 1

    def card_counts(self) -> Counter[str]:
        """Return a count of cards for each rank in the player's hand."""
        return Counter(card.rank for card in self.hand)


@dataclass
class Claim:
    """Representation of a single facedown card played into the pile.

    A claim captures who played the card, the card itself, what rank they
    claimed it was, and whether that claim was truthful.
    """

    claimant: PlayerState
    card: Card
    claimed_rank: str
    truthful: bool


@dataclass
class ChallengeResult:
    """Outcome information from evaluating a pending challenge.

    Attributes:
        resolved (bool): True if the challenge phase is over.
        messages (list[str]): A list of messages describing the outcome.
    """

    resolved: bool
    messages: list[str]


@dataclass
class GameAction:
    """Records a single action taken during a game for replay purposes.

    Attributes:
        turn (int): The turn number when this action occurred.
        action_type (str): Type of action (e.g., 'claim', 'challenge', 'result').
        player (str): Name of the player who performed the action.
        data (Dict[str, Any]): Additional data specific to the action type.
    """

    turn: int
    action_type: str
    player: str
    data: Dict[str, Any]


@dataclass
class Team:
    """Represents a team in team play mode.

    Attributes:
        name (str): Team name.
        members (list[PlayerState]): Team members.
        shared_info (Dict[str, Any]): Information shared among team members.
    """

    name: str
    members: list[PlayerState] = field(default_factory=list)
    shared_info: Dict[str, Any] = field(default_factory=dict)

    def total_cards(self) -> int:
        """Return total cards held by the team."""
        return sum(len(member.hand) for member in self.members)

    def is_victorious(self) -> bool:
        """Check if team has won (all members have no cards)."""
        return all(len(member.hand) == 0 for member in self.members)


@dataclass
class TournamentPlayer:
    """Represents a player in a tournament.

    Attributes:
        name (str): Player's name.
        is_user (bool): True if this is the human player.
        profile (PlayerProfile): AI profile for bots.
        wins (int): Number of games won.
        eliminated (bool): Whether the player is eliminated.
    """

    name: str
    is_user: bool
    profile: PlayerProfile
    wins: int = 0
    eliminated: bool = False


@dataclass
class TournamentRound:
    """Represents a single round in a tournament.

    Attributes:
        round_number (int): The round number (1-based).
        matches (list[tuple[TournamentPlayer, ...]]): List of player matchups.
        winners (list[TournamentPlayer]): Players who won their matches.
    """

    round_number: int
    matches: list[tuple[TournamentPlayer, ...]]
    winners: list[TournamentPlayer] = field(default_factory=list)


@dataclass
class GameReplay:
    """Complete recording of a game for replay purposes.

    Attributes:
        difficulty (str): Name of the difficulty level used.
        initial_state (Dict[str, Any]): Initial game setup including players and deck.
        actions (list[GameAction]): Sequence of all actions taken during the game.
        final_state (Dict[str, Any]): Final game state including winner.
        seed (Optional[int]): Random seed used for the game, if any.
    """

    difficulty: str
    initial_state: Dict[str, Any]
    actions: list[GameAction]
    final_state: Dict[str, Any]
    seed: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert replay to a dictionary for JSON serialization."""
        return {
            "difficulty": self.difficulty,
            "seed": self.seed,
            "initial_state": self.initial_state,
            "actions": [
                {
                    "turn": action.turn,
                    "action_type": action.action_type,
                    "player": action.player,
                    "data": action.data,
                }
                for action in self.actions
            ],
            "final_state": self.final_state,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> GameReplay:
        """Create a GameReplay from a dictionary."""
        actions = [
            GameAction(
                turn=a["turn"],
                action_type=a["action_type"],
                player=a["player"],
                data=a["data"],
            )
            for a in data["actions"]
        ]
        return cls(
            difficulty=data["difficulty"],
            seed=data.get("seed"),
            initial_state=data["initial_state"],
            actions=actions,
            final_state=data["final_state"],
        )

    def save_to_file(self, filepath: Path) -> None:
        """Save replay to a JSON file."""
        with open(filepath, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load_from_file(cls, filepath: Path) -> GameReplay:
        """Load replay from a JSON file."""
        with open(filepath, "r") as f:
            data = json.load(f)
        return cls.from_dict(data)


# Pre-defined difficulty levels for the game.
DIFFICULTIES: Dict[str, DifficultyLevel] = {
    "Noob": DifficultyLevel("Noob", bot_count=1, deck_count=1, honesty=0.65, boldness=0.25, challenge=0.2),
    "Easy": DifficultyLevel("Easy", bot_count=2, deck_count=1, honesty=0.6, boldness=0.3, challenge=0.25),
    "Medium": DifficultyLevel("Medium", bot_count=2, deck_count=2, honesty=0.58, boldness=0.35, challenge=0.3),
    "Hard": DifficultyLevel("Hard", bot_count=3, deck_count=2, honesty=0.55, boldness=0.4, challenge=0.35),
    "Insane": DifficultyLevel("Insane", bot_count=4, deck_count=3, honesty=0.52, boldness=0.45, challenge=0.4),
}

# Pre-defined deck types for the game.
DECK_TYPES: Dict[str, DeckType] = {
    "Standard": DeckType(
        name="Standard",
        description="Traditional 52-card deck with all ranks and suits",
        ranks=list(RANKS),
        suits=list(Suit),
        cards_per_rank_suit=1,
    ),
    "FaceCardsOnly": DeckType(
        name="Face Cards Only",
        description="Only face cards (J, Q, K, A) for faster gameplay",
        ranks=["J", "Q", "K", "A"],
        suits=list(Suit),
        cards_per_rank_suit=1,
    ),
    "NumbersOnly": DeckType(
        name="Numbers Only",
        description="Only numbered cards (2-10) for beginner-friendly play",
        ranks=["2", "3", "4", "5", "6", "7", "8", "9", "T"],
        suits=list(Suit),
        cards_per_rank_suit=1,
    ),
    "DoubleDown": DeckType(
        name="Double Down",
        description="Standard deck with two copies of each card for more bluffing",
        ranks=list(RANKS),
        suits=list(Suit),
        cards_per_rank_suit=2,
    ),
    "HighLow": DeckType(
        name="High-Low",
        description="Only high cards (9-A) and low cards (2-6) for strategic variety",
        ranks=["2", "3", "4", "5", "6", "9", "T", "J", "Q", "K", "A"],
        suits=list(Suit),
        cards_per_rank_suit=1,
    ),
}


class BluffTournament:
    """Manages a multi-round elimination tournament.

    Players compete in matches, and winners advance to the next round
    until a champion is determined.
    """

    def __init__(
        self,
        difficulty: DifficultyLevel,
        *,
        rounds_per_match: int = 3,
        rng: random.Random | None = None,
        deck_type: DeckType | None = None,
    ) -> None:
        """Initialize a tournament.

        Args:
            difficulty: Difficulty level for bot opponents.
            rounds_per_match: Number of rounds per game.
            rng: Random number generator.
            deck_type: Type of deck to use.
        """
        self.difficulty = difficulty
        self.rounds_per_match = rounds_per_match
        self._rng = rng or random.Random()
        self.deck_type = deck_type or DECK_TYPES["Standard"]

        # Initialize tournament players
        self.players: list[TournamentPlayer] = []
        self.rounds: list[TournamentRound] = []
        self.current_round = 0
        self.champion: TournamentPlayer | None = None

        self._setup_tournament_players()

    def _setup_tournament_players(self) -> None:
        """Create tournament players including the user and bots."""
        # Add user
        user_profile = PlayerProfile(honesty=0.62, boldness=0.28, challenge=0.3, memory=0.6)
        self.players.append(TournamentPlayer(name="You", is_user=True, profile=user_profile))

        # Add bots - need enough for a power of 2 for bracket
        # For 8-player tournament (3 rounds to finals)
        base = self.difficulty
        for i in range(7):
            variance = self._rng.uniform(-0.05, 0.05)
            profile = PlayerProfile(
                honesty=max(0.2, min(0.95, base.honesty + variance)),
                boldness=max(0.05, min(0.9, base.boldness + variance * 1.5)),
                challenge=max(0.05, min(0.9, base.challenge + variance)),
                memory=max(0.2, min(0.95, 0.55 + variance * 2)),
            )
            self.players.append(
                TournamentPlayer(
                    name=f"Bot {i + 1}",
                    is_user=False,
                    profile=profile,
                )
            )

        # Shuffle players for random brackets
        self._rng.shuffle(self.players)

    def create_round(self) -> TournamentRound:
        """Create the next tournament round with matchups."""
        active_players = [p for p in self.players if not p.eliminated]

        if len(active_players) <= 1:
            return None

        # Pair up players for matches
        matches = []
        for i in range(0, len(active_players), 2):
            if i + 1 < len(active_players):
                # Standard 1v1 match
                matches.append((active_players[i], active_players[i + 1]))
            else:
                # Odd player gets a bye (automatically advances)
                pass

        self.current_round += 1
        round_obj = TournamentRound(round_number=self.current_round, matches=matches)
        self.rounds.append(round_obj)
        return round_obj

    def play_match(self, player1: TournamentPlayer, player2: TournamentPlayer) -> TournamentPlayer:
        """Play a single match between two players and return the winner.

        Args:
            player1: First player.
            player2: Second player.

        Returns:
            The winning player.
        """
        # Create a mini game with just these two players
        # We'll simulate by creating profiles and running a game
        difficulty_for_match = DifficultyLevel(
            name="Tournament",
            bot_count=1,
            deck_count=1,
            honesty=self.difficulty.honesty,
            boldness=self.difficulty.boldness,
            challenge=self.difficulty.challenge,
        )

        game = BluffGame(
            difficulty_for_match,
            rounds=self.rounds_per_match,
            rng=self._rng,
            deck_type=self.deck_type,
        )

        # Replace game players with tournament players
        game.players.clear()
        game.players.append(
            PlayerState(
                name=player1.name,
                is_user=player1.is_user,
                profile=player1.profile,
                rng=self._rng,
            )
        )
        game.players.append(
            PlayerState(
                name=player2.name,
                is_user=player2.is_user,
                profile=player2.profile,
                rng=self._rng,
            )
        )
        game._current_player_index = 0
        game._deal_initial_hands()

        # Simulate the game
        while not game.finished:
            player = game.current_player
            if player.is_user:
                # For tournament simulation, bots play for the user
                # In a real interactive tournament, this would prompt the user
                pass

            # Bot plays
            claim, _ = game.play_bot_turn()

            # Process challenges
            while game.phase == Phase.CHALLENGE and not game.finished:
                challenger = game.current_challenger
                if not challenger:
                    break
                decision = game.bot_should_challenge(challenger)
                game.evaluate_challenge(decision)

        # Determine winner
        winner = game.winner
        if winner:
            winner_tournament_player = player1 if winner.name == player1.name else player2
        else:
            # In case of tie, winner is the one with fewer cards
            p1_state = game.players[0]
            p2_state = game.players[1]
            winner_tournament_player = player1 if len(p1_state.hand) < len(p2_state.hand) else player2

        winner_tournament_player.wins += 1
        return winner_tournament_player

    def advance_round(self, round_obj: TournamentRound) -> None:
        """Process a round and eliminate losers.

        Args:
            round_obj: The round that was just completed.
        """
        # Mark losers as eliminated
        for match in round_obj.matches:
            for player in match:
                if player not in round_obj.winners:
                    player.eliminated = True

    def is_complete(self) -> bool:
        """Check if the tournament is complete."""
        active_players = [p for p in self.players if not p.eliminated]
        return len(active_players) == 1

    def get_champion(self) -> TournamentPlayer | None:
        """Return the tournament champion, if any."""
        active_players = [p for p in self.players if not p.eliminated]
        return active_players[0] if len(active_players) == 1 else None


class BluffGame:
    """Rules engine for a realistic multi-player game of Cheat/Bluff.

    This class manages the entire game lifecycle, from setup and dealing to
    turn processing, challenge resolution, and determining the winner.
    """

    def __init__(
        self,
        difficulty: DifficultyLevel,
        *,
        rounds: int = 5,
        rng: random.Random | None = None,
        record_replay: bool = False,
        seed: Optional[int] = None,
        deck_type: DeckType | None = None,
        team_play: bool = False,
    ) -> None:
        if rounds <= 0:
            raise ValueError("rounds must be a positive integer")

        self.difficulty = difficulty
        self.max_turns = rounds * (difficulty.bot_count + 1)
        self._rng = rng or random.Random()
        self._seed = seed
        self.deck_type = deck_type or DECK_TYPES["Standard"]
        self.team_play = team_play

        # Game state attributes
        self.players: list[PlayerState] = []
        self.teams: list[Team] = []
        self._pile_cards: list[Card] = []
        self._pile_claims: list[Claim] = []
        self._challenge_queue: Deque[PlayerState] = deque()
        self._claim_in_progress: Claim | None = None
        self._phase = Phase.TURN
        self._turns_played = 0
        self._winner: PlayerState | None = None
        self._winning_team: Team | None = None

        # Replay recording
        self._record_replay = record_replay
        self._replay_actions: list[GameAction] = []

        self._setup_players()
        if self.team_play:
            self._setup_teams()
        self._deal_initial_hands()

        # Record initial state for replay
        if self._record_replay:
            self._record_initial_state()

    # ------------------------------------------------------------------
    # Initialisation helpers
    # ------------------------------------------------------------------
    def _setup_players(self) -> None:
        """Create the user and bot players based on the difficulty settings."""
        user_profile = PlayerProfile(honesty=0.62, boldness=0.28, challenge=0.3, memory=0.6)
        self.players.append(PlayerState(name="You", is_user=True, profile=user_profile, rng=self._rng))

        for index in range(self.difficulty.bot_count):
            base = self.difficulty
            variance = self._rng.uniform(-0.05, 0.05)
            # Each bot inherits the base difficulty personality but receives a
            # small random variance so the table feels less predictable.
            profile = PlayerProfile(
                honesty=max(0.2, min(0.95, base.honesty + variance)),
                boldness=max(0.05, min(0.9, base.boldness + variance * 1.5)),
                challenge=max(0.05, min(0.9, base.challenge + variance)),
                memory=max(0.2, min(0.95, 0.55 + variance * 2)),
            )
            bot = PlayerState(
                name=f"{self.difficulty.name} Bot {index + 1}",
                is_user=False,
                profile=profile,
                rng=self._rng,
            )
            self.players.append(bot)

    def _setup_teams(self) -> None:
        """Organize players into teams for team play mode."""
        # Create two teams by splitting players
        mid = len(self.players) // 2

        team_a = Team(name="Team Alpha")
        team_b = Team(name="Team Bravo")

        for i, player in enumerate(self.players):
            if i < mid:
                team_a.members.append(player)
            else:
                team_b.members.append(player)

        self.teams = [team_a, team_b]

        # Update player names to show team affiliation
        for team in self.teams:
            for player in team.members:
                if not player.is_user:
                    player.name = f"{player.name} ({team.name})"

    def get_player_team(self, player: PlayerState) -> Team | None:
        """Get the team a player belongs to."""
        for team in self.teams:
            if player in team.members:
                return team
        return None

    def _build_multi_deck(self, deck_count: int) -> Deck:
        """Create a deck based on the selected deck type and count."""
        cards = self.deck_type.generate_cards(deck_count)
        return Deck(cards=cards)

    def _deal_initial_hands(self) -> None:
        """Shuffle the deck and deal cards to all players."""
        deck = self._build_multi_deck(self.difficulty.deck_count)
        deck.shuffle(rng=self._rng)

        # Deal cards one by one to each player
        player_index = 0
        while deck.cards:
            self.players[player_index].hand.append(deck.deal(1)[0])
            player_index = (player_index + 1) % len(self.players)

        # Reset game state for a new round
        self._current_player_index = 0
        self._phase = Phase.TURN
        self._turns_played = 0
        self._pile_cards.clear()
        self._pile_claims.clear()
        self._challenge_queue.clear()
        self._winner = None
        self._claim_in_progress = None

    # ------------------------------------------------------------------
    # Properties and state helpers
    # ------------------------------------------------------------------
    @property
    def phase(self) -> Phase:
        """The current phase of the game."""
        return self._phase

    @property
    def winner(self) -> PlayerState | None:
        """The winning player, if the game is complete."""
        return self._winner

    @property
    def finished(self) -> bool:
        """True if the game has finished."""
        return self._phase == Phase.COMPLETE

    @property
    def current_player(self) -> PlayerState:
        """The player whose turn it is."""
        return self.players[self._current_player_index]

    @property
    def pile_size(self) -> int:
        """The number of cards in the central pile."""
        return len(self._pile_cards)

    @property
    def claim_in_progress(self) -> Claim | None:
        """The claim that is currently being challenged."""
        return self._claim_in_progress

    @property
    def current_challenger(self) -> PlayerState | None:
        """The player who is next in line to challenge."""
        return self._challenge_queue[0] if self._challenge_queue else None

    def public_state(self) -> Dict[str, object]:
        """Expose a serialisable snapshot of the game state for UIs."""
        return {
            "phase": self._phase.name,
            "pile_size": len(self._pile_cards),
            "turns_played": self._turns_played,
            "max_turns": self.max_turns,
            "deck_type": self.deck_type.name,
            "valid_ranks": self.deck_type.ranks,
            "players": [
                {
                    "name": player.name,
                    "is_user": player.is_user,
                    "card_count": len(player.hand),
                    "truths": player.truths,
                    "lies": player.lies,
                    "calls": player.challenge_attempts,
                    "correct_calls": player.challenge_successes,
                }
                for player in self.players
            ],
            "claim": (
                None
                if not self._claim_in_progress
                else {
                    "claimant": self._claim_in_progress.claimant.name,
                    "claimed_rank": self._claim_in_progress.claimed_rank,
                    "truthful": self._claim_in_progress.truthful,
                }
            ),
        }

    # ------------------------------------------------------------------
    # Turn handling
    # ------------------------------------------------------------------
    def play_user_turn(self, card_index: int, claimed_rank: str) -> Claim:
        """Process a turn for the human user."""
        player = self.current_player
        if not player.is_user:
            raise RuntimeError("It is not the user's turn.")
        return self._play_turn(player, card_index, claimed_rank)

    def play_bot_turn(self) -> tuple[Claim, list[str]]:
        """Determine and execute a bot's turn based on its AI profile."""
        player = self.current_player
        if player.is_user:
            raise RuntimeError("It is not a bot's turn.")

        hand_counts = player.card_counts()
        truthful_bias = player.profile.honesty

        # If recently caught, a bot becomes more honest
        if player.last_caught_turn is not None and self._turns_played - player.last_caught_turn < 3:
            truthful_bias += 0.12

        # Larger piles encourage more daring (less honest) plays
        truthful_bias -= min(0.2, len(self._pile_cards) * 0.02 * player.profile.boldness)

        # Clamp the bias into a sensible range so pathological bot settings
        # still result in believable behaviour.
        truthful = self._rng.random() < max(0.1, min(0.95, truthful_bias))
        claimed_rank: str
        chosen_card: Card

        if truthful and hand_counts:
            # Play truthfully: choose a rank the bot holds
            ranked = hand_counts.most_common()
            weights = [count for _, count in ranked]
            # Weighted sampling means the bot mirrors human tendencies—more
            # plentiful ranks are more likely to be played when honest.
            chosen_rank = self._rng.choices([rank for rank, _ in ranked], weights=weights)[0]
            chosen_card = next(card for card in player.hand if card.rank == chosen_rank)
            claimed_rank = chosen_rank
        else:
            # Bluff: choose a card and claim it's a different rank
            chosen_card = self._rng.choice(player.hand)
            owned_ranks = set(card.rank for card in player.hand)
            valid_ranks = self.deck_type.ranks
            bluff_options = [rank for rank in valid_ranks if rank not in owned_ranks and rank != chosen_card.rank]
            if not bluff_options:
                bluff_options = [rank for rank in valid_ranks if rank != chosen_card.rank]

            claimed_rank = self._rng.choice(bluff_options)
            truthful = chosen_card.rank == claimed_rank
            if truthful:
                # This was supposed to be a bluff, but we accidentally chose a truthful rank.
                # Nudge it to a different rank to ensure it remains a bluff.
                alternatives = [rank for rank in valid_ranks if rank != chosen_card.rank]
                claimed_rank = self._rng.choice(alternatives)
                truthful = False

        claim = self._play_turn(player, player.hand.index(chosen_card), claimed_rank)

        if truthful:
            message = f"{player.name} calmly slides a card forward, claiming it is a {claimed_rank}."
        else:
            message = f"{player.name} hesitates before declaring their card to be a {claimed_rank}."
        return claim, [message]

    def _play_turn(self, player: PlayerState, card_index: int, claimed_rank: str) -> Claim:
        """Core logic for playing a card and making a claim."""
        if self._phase != Phase.TURN:
            raise RuntimeError("Cannot play a turn while a challenge is unresolved.")
        if not 0 <= card_index < len(player.hand):
            raise ValueError("card_index out of range")
        if claimed_rank not in self.deck_type.ranks:
            raise ValueError("claimed_rank must be a valid rank for this deck type")

        # Create and record the claim
        card = player.hand.pop(card_index)
        truthful = card.rank == claimed_rank
        player.record_claim(truthful)

        claim = Claim(claimant=player, card=card, claimed_rank=claimed_rank, truthful=truthful)
        self._claim_in_progress = claim
        self._pile_cards.append(card)
        self._pile_claims.append(claim)

        # Record action for replay
        self._record_action(
            "claim",
            player.name,
            {
                "claimed_rank": claimed_rank,
                "actual_rank": card.rank,
                "truthful": truthful,
                "pile_size": len(self._pile_cards),
            },
        )

        # Update pattern learning for this player
        player.pattern.update_bluff_pattern(truthful, len(self._pile_cards) - 1, len(player.hand) + 1, claimed_rank)

        # Transition to the challenge phase by lining up every other player so
        # they can decide whether to call the claim.
        self._challenge_queue = deque(self._iter_other_players_from(player))
        self._phase = Phase.CHALLENGE

        return claim

    def _iter_other_players_from(self, player: PlayerState) -> List[PlayerState]:
        """Return a list of other players in turn order, starting from the given player."""
        start = self.players.index(player)
        ordering: list[PlayerState] = []
        for offset in range(1, len(self.players)):
            ordering.append(self.players[(start + offset) % len(self.players)])
        return ordering

    # ------------------------------------------------------------------
    # Challenge resolution
    # ------------------------------------------------------------------
    def evaluate_challenge(self, decision: bool) -> ChallengeResult:
        """Evaluate the current player's decision to challenge or not."""
        if self._phase != Phase.CHALLENGE:
            raise RuntimeError("There is no claim waiting to be challenged.")
        if not self._claim_in_progress:
            raise RuntimeError("No active claim is registered.")

        messages: list[str] = []
        if not self._challenge_queue:
            # No one left to challenge; finalize the turn.
            return self._finalise_uncontested()

        # Evaluate challengers in the order they queued up during the turn.
        challenger = self._challenge_queue.popleft()
        if not decision:
            # Player chooses not to challenge
            if challenger.is_user:
                messages.append("You decide to let the claim stand.")
            else:
                messages.append(f"{challenger.name} chooses not to make a scene.")

            # Record non-challenge action for replay
            self._record_action("pass_challenge", challenger.name, {"challenged": False})

            if not self._challenge_queue:
                # No one else can challenge, so finalize the turn
                follow_up = self._finalise_uncontested()
                messages.extend(follow_up.messages)
                return ChallengeResult(resolved=True, messages=messages)

            return ChallengeResult(resolved=False, messages=messages)

        # A challenge has been made
        claim = self._claim_in_progress
        # Record the attempt so bot AI can adapt to success/failure later.
        challenger.record_challenge(success=not claim.truthful)
        messages.append(f"{challenger.name} slams a hand down and calls the bluff!")

        # Record challenge action for replay
        self._record_action(
            "challenge",
            challenger.name,
            {
                "challenged": True,
                "claim_was_truthful": claim.truthful,
                "claimant": claim.claimant.name,
            },
        )

        if claim.truthful:
            # The claim was true; challenger picks up the pile
            collector = challenger
            # Shuffle the enlarged hand so future draws do not reveal pile order.
            collector.hand.extend(self._pile_cards)
            collector.rng.shuffle(collector.hand)
            self._pile_cards.clear()
            self._pile_claims.clear()
            messages.append(f"The card really was a {claim.card.rank}. {collector.name} must scoop up the entire pile.")
            result = self._complete_turn(challenge_made=True, liar_caught=False, collector=collector)
            messages.extend(result.messages)
            return ChallengeResult(resolved=True, messages=messages)
        else:
            # The claim was a bluff; claimant picks up the pile
            collector = claim.claimant
            collector.record_caught(self._turns_played)
            # The claimant inherits every facedown card to keep them honest in
            # future rounds.
            collector.hand.extend(self._pile_cards)
            collector.rng.shuffle(collector.hand)
            self._pile_cards.clear()
            self._pile_claims.clear()
            messages.append(f"{claim.claimant.name} was caught! Their card was actually a {claim.card.rank}.")
            result = self._complete_turn(challenge_made=True, liar_caught=True, collector=collector)
            messages.extend(result.messages)
            return ChallengeResult(resolved=True, messages=messages)

    def _finalise_uncontested(self) -> ChallengeResult:
        """Finalize a turn where no one challenged the claim."""
        if not self._claim_in_progress:
            raise RuntimeError("There is no claim to finalise.")

        messages = ["No one dares to challenge. The table tension rises."]
        result = self._complete_turn(challenge_made=False, liar_caught=False, collector=None)
        messages.extend(result.messages)
        return ChallengeResult(resolved=True, messages=messages)

    def _complete_turn(
        self,
        *,
        challenge_made: bool,
        liar_caught: bool,
        collector: PlayerState | None,
    ) -> ChallengeResult:
        """Finalize the turn, check for a winner, and advance to the next player."""
        assert self._claim_in_progress is not None
        claimant = self._claim_in_progress.claimant
        messages: list[str] = []

        if liar_caught and collector:
            messages.append(f"{collector.name} drags the pile back, their hand growing to {len(collector.hand)} cards.")
        elif challenge_made and collector:
            messages.append(f"{collector.name} adds the pile to their hand, now holding {len(collector.hand)} cards.")

        # Reset for the next turn
        self._claim_in_progress = None
        self._challenge_queue.clear()
        self._phase = Phase.TURN
        self._turns_played += 1

        # Check for a winner
        if not claimant.hand:
            self._winner = claimant
            self._phase = Phase.COMPLETE

            # Check for team victory
            if self.team_play:
                team = self.get_player_team(claimant)
                if team and team.is_victorious():
                    self._winning_team = team
                    messages.append(f"{claimant.name} has shed every card!")
                    messages.append(f"{team.name} wins the table!")
                else:
                    messages.append(f"{claimant.name} has shed every card! Their team still has cards.")
            else:
                messages.append(f"{claimant.name} has shed every card and wins the table!")

            return ChallengeResult(resolved=True, messages=messages)

        # Check if the game should end due to reaching the max turn limit
        if self._turns_played >= self.max_turns:
            messages.extend(self._close_by_card_count())
            return ChallengeResult(resolved=True, messages=messages)

        # Advance to the next player, skipping anyone who just emptied their hand.
        self._current_player_index = (self.players.index(claimant) + 1) % len(self.players)
        self._advance_to_next_player_with_cards()
        return ChallengeResult(resolved=True, messages=messages)

    def _advance_to_next_player_with_cards(self) -> None:
        """Find the next player in turn order who still has cards to play."""
        start = self._current_player_index
        for offset in range(len(self.players)):
            candidate_index = (start + offset) % len(self.players)
            if self.players[candidate_index].hand:
                self._current_player_index = candidate_index
                return

        # If no players have cards, the game is over.
        self._phase = Phase.COMPLETE

    def _close_by_card_count(self) -> list[str]:
        """End the game and determine the winner by the lowest card count."""
        # Sort players by card count (ascending), with user as tie-breaker
        standings = sorted(self.players, key=lambda p: (len(p.hand), p.is_user))
        best_count = len(standings[0].hand)
        winners = [p for p in standings if len(p.hand) == best_count]

        if len(winners) == 1:
            self._winner = winners[0]
            self._phase = Phase.COMPLETE
            return [
                "Maximum rounds reached.",
                f"{winners[0].name} holds the fewest cards ({best_count}) and is declared the winner.",
            ]

        # Handle a tie
        self._winner = None
        self._phase = Phase.COMPLETE
        # Multiple players share the title, so enumerate them for the match log.
        tied_names = ", ".join(p.name for p in winners)
        return [
            "Maximum rounds reached with a tie.",
            f"Players with the fewest cards ({best_count}): {tied_names}.",
        ]

    # ------------------------------------------------------------------
    # Bot challenge logic
    # ------------------------------------------------------------------
    def bot_should_challenge(self, challenger: PlayerState) -> bool:
        """Determine if a bot should challenge a claim, using learned patterns and profile."""
        if not self._claim_in_progress:
            return False

        claim = self._claim_in_progress
        claimant = claim.claimant

        # Base tendency to challenge from profile
        tendency = challenger.profile.challenge

        # Factor in the claimant's history of lying
        history_total = claimant.truths + claimant.lies
        lie_rate = (claimant.lies + 1) / (history_total + 2)  # +1/+2 to avoid division by zero
        tendency += lie_rate * challenger.profile.memory

        # USE LEARNED PATTERNS - This is the advanced AI feature
        if challenger.profile.memory > 0.5:  # High-memory bots use pattern learning
            suspected_bluff_prob = claimant.pattern.get_suspected_bluff_probability(len(self._pile_cards), len(claimant.hand), claim.claimed_rank)
            # Weight the learned pattern based on memory
            pattern_influence = (suspected_bluff_prob - 0.5) * challenger.profile.memory
            tendency += pattern_influence

        # Adjust based on how recently the claimant was caught
        if claimant.last_caught_turn is not None:
            distance = self._turns_played - claimant.last_caught_turn
            if distance <= 1:
                tendency += 0.25
            elif distance <= 3:
                tendency += 0.1

        # Check if the challenger holds cards of the claimed rank
        owned = challenger.card_counts()[claim.claimed_rank]
        ownership_pressure = 0.0
        if owned >= 3:
            ownership_pressure += 0.25  # High suspicion
        elif owned == 2:
            ownership_pressure += 0.15
        elif owned == 0:
            ownership_pressure -= 0.08  # Lower suspicion

        # The size of the pile can make challenging more tempting
        pile_pressure = min(0.35, len(self._pile_cards) * 0.025)

        tendency += ownership_pressure + pile_pressure
        tendency = max(0.05, min(0.9, tendency))  # Clamp probability

        # Bots with few cards become more cautious to avoid picking up the pile
        if len(challenger.hand) <= 2:
            tendency -= 0.2
        elif len(challenger.hand) >= 10:
            tendency += 0.1

        return challenger.rng.random() < tendency

    # ------------------------------------------------------------------
    # CLI helpers
    # ------------------------------------------------------------------
    def scoreboard(self) -> str:
        """Generate a string with the current game scores and stats."""
        rows = ["Current card counts:"]

        if self.team_play:
            # Show team-based scoreboard
            for team in self.teams:
                rows.append(f"\n{team.name} (Total: {team.total_cards()} cards):")
                for player in team.members:
                    rows.append(
                        f"  - {player.name}: {len(player.hand)} cards | "
                        f"Truths: {player.truths} | Lies: {player.lies} | "
                        f"Calls: {player.challenge_successes}/{player.challenge_attempts}"
                    )
        else:
            # Show individual scoreboard
            for player in self.players:
                rows.append(
                    f"- {player.name}: {len(player.hand)} cards | "
                    f"Truths: {player.truths} | Lies: {player.lies} | "
                    f"Calls: {player.challenge_successes}/{player.challenge_attempts}"
                )

        rows.append(f"\nPile size: {len(self._pile_cards)}")
        rows.append(f"Turn {self._turns_played + 1} of {self.max_turns}")
        return "\n".join(rows)

    # ------------------------------------------------------------------
    # Replay recording
    # ------------------------------------------------------------------
    def _record_initial_state(self) -> None:
        """Record the initial game state for replay."""
        self._initial_state = {
            "players": [
                {
                    "name": player.name,
                    "is_user": player.is_user,
                    "hand_size": len(player.hand),
                }
                for player in self.players
            ],
            "max_turns": self.max_turns,
            "difficulty": self.difficulty.name,
        }

    def _record_action(self, action_type: str, player: str, data: Dict[str, Any]) -> None:
        """Record a game action for replay."""
        if self._record_replay:
            action = GameAction(turn=self._turns_played, action_type=action_type, player=player, data=data)
            self._replay_actions.append(action)

    def get_replay(self) -> Optional[GameReplay]:
        """Generate a GameReplay object from the recorded game."""
        if not self._record_replay:
            return None

        final_state = {
            "winner": self._winner.name if self._winner else None,
            "turns_played": self._turns_played,
            "players": [
                {
                    "name": player.name,
                    "hand_size": len(player.hand),
                    "truths": player.truths,
                    "lies": player.lies,
                    "caught": player.caught,
                    "challenge_attempts": player.challenge_attempts,
                    "challenge_successes": player.challenge_successes,
                }
                for player in self.players
            ],
        }

        return GameReplay(
            difficulty=self.difficulty.name,
            seed=self._seed,
            initial_state=self._initial_state,
            actions=self._replay_actions,
            final_state=final_state,
        )


# ----------------------------------------------------------------------
# CLI orchestration
# ----------------------------------------------------------------------


def parse_arguments(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Return parsed command-line arguments for a Bluff session.

    The CLI supports both human-vs-bot matches and a Tkinter-powered GUI.  This
    helper centralises argument parsing so that :func:`run_cli` and the module's
    ``__main__`` entry point share the exact same behaviour.

    Args:
        argv: Optional sequence of command-line arguments. Passing ``None``
            allows :func:`argparse.ArgumentParser.parse_args` to consume
            arguments directly from :data:`sys.argv`.

    Returns:
        argparse.Namespace: A namespace containing the chosen difficulty,
        number of rounds, optional random seed, and whether the GUI was
        requested.
    """

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--difficulty",
        choices=DIFFICULTIES.keys(),
        default="Noob",
        help="Which AI difficulty to face.",
    )
    parser.add_argument(
        "--rounds",
        type=int,
        default=5,
        help="Number of table rotations before the match is adjudicated (default: 5).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Optional random seed for deterministic sessions.",
    )
    parser.add_argument(
        "--gui",
        action="store_true",
        help="Launch the Tkinter interface instead of the CLI.",
    )
    parser.add_argument(
        "--deck-type",
        choices=DECK_TYPES.keys(),
        default="Standard",
        help="Type of deck to use (default: Standard).",
    )
    parser.add_argument(
        "--record-replay",
        action="store_true",
        help="Record the game for replay purposes.",
    )
    parser.add_argument(
        "--replay",
        type=str,
        help="Path to a replay file to watch.",
    )
    parser.add_argument(
        "--tournament",
        action="store_true",
        help="Play in tournament mode with elimination rounds.",
    )
    parser.add_argument(
        "--team-play",
        action="store_true",
        help="Enable team play mode where players are divided into teams.",
    )
    return parser.parse_args(argv)


def run_cli(argv: Sequence[str] | None = None) -> None:
    """Run an interactive Bluff match in the terminal.

    This function wires together :func:`parse_arguments`, the
    :class:`~card_games.bluff.BluffGame` engine, and the text prompts defined
    below.  The implementation doubles as living documentation for the game
    flow—reading the code explains precisely when the player is prompted, how
    challenges are resolved, and under which conditions the match concludes.

    Args:
        argv: Optional command-line arguments to parse. ``None`` means the
            function should read directly from :data:`sys.argv`.
    """

    args = parse_arguments(argv)

    # Handle replay viewing mode
    if args.replay:
        _play_replay(args.replay)
        return

    rng = random.Random(args.seed) if args.seed is not None else random.Random()
    difficulty = DIFFICULTIES[args.difficulty]
    deck_type = DECK_TYPES[args.deck_type]

    # Handle tournament mode
    if args.tournament:
        _run_tournament_cli(difficulty, args.rounds, rng, deck_type)
        return

    if args.gui:
        try:
            from .gui_pyqt import run_gui as run_pyqt_gui

            run_pyqt_gui(
                difficulty,
                rounds=args.rounds,
                seed=args.seed,
                deck_type=deck_type,
                record_replay=args.record_replay,
            )
            return
        except ImportError:  # pragma: no cover - PyQt5 optional dependency
            print("PyQt5 is not available; falling back to the Tkinter GUI.")
            from .gui import run_gui as run_tk_gui

            run_tk_gui(
                difficulty,
                rounds=args.rounds,
                seed=args.seed,
                deck_type=deck_type,
                record_replay=args.record_replay,
            )
            return

    game = BluffGame(
        difficulty,
        rounds=args.rounds,
        rng=rng,
        record_replay=args.record_replay,
        seed=args.seed,
        deck_type=deck_type,
        team_play=args.team_play,
    )

    print(
        "Welcome to Bluff! Each player discards one card facedown, claiming its rank."
        " If someone challenges and the card was truthful, the challenger collects the"
        " whole pile. If it was a bluff, the liar takes the pile. First to empty their"
        " hand wins."
    )
    print(f"Difficulty: {difficulty.name} | Opponents: {difficulty.bot_count}")
    print(f"Deck Type: {deck_type.name} - {deck_type.description}")
    if args.team_play:
        print("Team Play: ENABLED - Players are divided into teams!")
    print()

    while not game.finished:
        player = game.current_player
        print(game.scoreboard())
        print()
        if player.is_user:
            print("Your hand:")
            for idx, card in enumerate(player.hand):
                print(f"  [{idx}] {card} ({card.rank})")

            chosen_index = _prompt_card_index(len(player.hand))
            claimed_rank = _prompt_claim_rank(player.hand[chosen_index], game.deck_type.ranks)
            claim = game.play_user_turn(chosen_index, claimed_rank)
            print(f"You slide forward {claim.card} and claim it is a {claim.claimed_rank}.")
        else:
            claim, messages = game.play_bot_turn()
            for message in messages:
                print(message)

        while game.phase == Phase.CHALLENGE and not game.finished:
            challenger = game.current_challenger
            if challenger is None:
                break
            if challenger.is_user:
                decision = _prompt_user_challenge(claim.claimant.name, game.pile_size)
            else:
                decision = game.bot_should_challenge(challenger)
                if decision:
                    print(f"{challenger.name} eyes the pile and prepares to challenge...")
                else:
                    print(f"{challenger.name} stays quiet.")
            result = game.evaluate_challenge(decision)
            for line in result.messages:
                print(line)

        print()

    print("Match complete!\n")
    if game.winner is not None:
        if game.winner.is_user:
            print("Congratulations, you outmaneuvered the table!")
        else:
            print(f"{game.winner.name} claims victory this time.")
    else:
        print("It's a draw—multiple players share the honours.")

    # Save replay if recording was enabled
    if args.record_replay:
        replay = game.get_replay()
        if replay:
            replay_dir = Path.home() / ".bluff_replays"
            replay_dir.mkdir(exist_ok=True)
            import datetime

            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            replay_file = replay_dir / f"bluff_replay_{timestamp}.json"
            replay.save_to_file(replay_file)
            print(f"\nReplay saved to: {replay_file}")
            print(f"Watch it again with: python -m card_games.bluff --replay {replay_file}")


def _prompt_card_index(hand_size: int) -> int:
    """Prompt the user to select a card index from their hand.

    The helper loops until a valid integer within the bounds of the player's
    hand is supplied. It intentionally avoids raising exceptions so that the
    user receives human-friendly feedback for invalid input.

    Args:
        hand_size: The number of cards currently held by the user.

    Returns:
        int: The zero-based index corresponding to the chosen card.
    """

    while True:
        choice = input("Select the index of the card you want to play: ").strip()
        if choice.isdigit():
            index = int(choice)
            if 0 <= index < hand_size:
                return index
        print("Please enter a valid index from your hand.")


def _prompt_claim_rank(card: Card, valid_ranks: list[str]) -> str:
    """Prompt the user to declare the rank of the card being played.

    For honesty they may repeat the actual rank, but bluffing is as simple as
    naming a different value from the valid ranks for the deck type.  The
    prompting loop doubles as in-game documentation by reminding the user which
    ranks are legal.

    Args:
        card: The actual card about to be placed on the pile. The card is not
            modified—only its rank is used for the optional prompt text.
        valid_ranks: List of valid ranks for the current deck type.

    Returns:
        str: A single-character rank chosen from valid_ranks.
    """

    while True:
        rank = input("Declare your card's rank (e.g. 'A', 'K', '7'). You may bluff by stating a different rank: ").strip().upper()
        if rank in valid_ranks:
            return rank
        print("Unknown rank. Valid options are: " + ", ".join(valid_ranks))


def _run_tournament_cli(
    difficulty: DifficultyLevel,
    rounds_per_match: int,
    rng: random.Random,
    deck_type: DeckType,
) -> None:
    """Run a tournament in the CLI.

    Args:
        difficulty: Difficulty level for bots.
        rounds_per_match: Number of rounds per match.
        rng: Random number generator.
        deck_type: Type of deck to use.
    """
    print("=" * 60)
    print("BLUFF TOURNAMENT MODE")
    print("=" * 60)
    print(f"Difficulty: {difficulty.name}")
    print(f"Deck Type: {deck_type.name}")
    print(f"Rounds per match: {rounds_per_match}")
    print("\nThis is an 8-player single-elimination tournament.")
    print("Win your matches to advance to the next round!\n")

    tournament = BluffTournament(difficulty, rounds_per_match=rounds_per_match, rng=rng, deck_type=deck_type)

    # Play through tournament rounds
    while not tournament.is_complete():
        round_obj = tournament.create_round()
        if not round_obj:
            break

        print("=" * 60)
        print(f"ROUND {round_obj.round_number}")
        print("=" * 60)

        for match_idx, match in enumerate(round_obj.matches, 1):
            player1, player2 = match
            print(f"\nMatch {match_idx}: {player1.name} vs {player2.name}")
            print("Playing match...")

            winner = tournament.play_match(player1, player2)
            round_obj.winners.append(winner)

            print(f"Winner: {winner.name}")

        tournament.advance_round(round_obj)

        # Show remaining players
        active = [p for p in tournament.players if not p.eliminated]
        print(f"\nPlayers remaining: {', '.join(p.name for p in active)}\n")

        if not tournament.is_complete():
            input("Press Enter to continue to the next round...")

    # Announce champion
    champion = tournament.get_champion()
    print("\n" + "=" * 60)
    print("TOURNAMENT COMPLETE!")
    print("=" * 60)
    if champion:
        if champion.is_user:
            print("🏆 CONGRATULATIONS! You are the tournament champion! 🏆")
        else:
            print(f"Tournament Champion: {champion.name}")
        print(f"Total wins: {champion.wins}")

    print("\nFinal standings:")
    sorted_players = sorted(tournament.players, key=lambda p: p.wins, reverse=True)
    for i, player in enumerate(sorted_players, 1):
        status = "CHAMPION" if player == champion else "ELIMINATED"
        print(f"{i}. {player.name}: {player.wins} wins - {status}")


def _play_replay(replay_path: str) -> None:
    """Load and display a recorded game replay.

    Args:
        replay_path: Path to the replay JSON file.
    """
    try:
        replay = GameReplay.load_from_file(Path(replay_path))
    except FileNotFoundError:
        print(f"Error: Replay file not found: {replay_path}")
        return
    except json.JSONDecodeError:
        print(f"Error: Invalid replay file format: {replay_path}")
        return

    print("=" * 60)
    print("BLUFF GAME REPLAY")
    print("=" * 60)
    print(f"Difficulty: {replay.difficulty}")
    if replay.seed:
        print(f"Seed: {replay.seed}")
    print("\nInitial Setup:")
    for player in replay.initial_state["players"]:
        print(f"  - {player['name']}: {player['hand_size']} cards {'(Human)' if player['is_user'] else '(Bot)'}")
    print(f"\nMax turns: {replay.initial_state['max_turns']}")
    print("\n" + "=" * 60)
    print("GAME ACTIONS")
    print("=" * 60 + "\n")

    import time

    for action in replay.actions:
        print(f"Turn {action.turn + 1}: {action.player}", end=" ")

        if action.action_type == "claim":
            data = action.data
            if data["truthful"]:
                print(f"plays a {data['actual_rank']} and truthfully claims {data['claimed_rank']}")
            else:
                print(f"plays a {data['actual_rank']} but claims {data['claimed_rank']} (BLUFF!)")
            print(f"  Pile size: {data['pile_size']}")

        elif action.action_type == "challenge":
            data = action.data
            print(f"challenges {data['claimant']}'s claim!")
            if data["claim_was_truthful"]:
                print(f"  The claim was TRUTHFUL - {action.player} takes the pile")
            else:
                print(f"  The claim was a BLUFF - {data['claimant']} caught and takes the pile")

        elif action.action_type == "pass_challenge":
            print("passes on the challenge")

        print()
        time.sleep(0.5)  # Pause for readability

    print("=" * 60)
    print("FINAL RESULTS")
    print("=" * 60)
    winner_name = replay.final_state.get("winner")
    if winner_name:
        print(f"Winner: {winner_name}")
    else:
        print("Game ended in a draw")

    print(f"\nTurns played: {replay.final_state['turns_played']}")
    print("\nFinal player statistics:")
    for player in replay.final_state["players"]:
        print(f"  {player['name']}: {player['hand_size']} cards remaining")
        print(f"    Truths: {player['truths']}, Lies: {player['lies']}, Caught: {player['caught']}")
        print(f"    Challenges: {player['challenge_successes']}/{player['challenge_attempts']}")


def _prompt_user_challenge(claimant_name: str, pile_size: int) -> bool:
    """Ask the human player whether they wish to challenge the current claim.

    The decision matters: calling a bluff risks collecting the entire pile if
    the claimant was truthful, but refusing allows the next player in the
    challenge queue to decide.  The function keeps prompting until a recognised
    response is entered, providing in-line documentation for the accepted
    commands (``call``/``trust`` and their short aliases).

    Args:
        claimant_name: The name of the player who made the claim.
        pile_size: The number of facedown cards currently in the pile. This is
            shown to help the user gauge the risk/reward of challenging.

    Returns:
        bool: ``True`` if the user wants to challenge, ``False`` otherwise.
    """

    while True:
        choice = input(f"Do you want to challenge {claimant_name}'s claim? (call/trust) [pile has {pile_size} cards]: ").strip().lower()
        if choice in {"call", "c"}:
            return True
        if choice in {"trust", "t", "pass", "p"}:
            return False
        print("Please answer with 'call' or 'trust'.")


def main(argv: Iterable[str] | None = None) -> None:  # pragma: no cover - convenience
    run_cli(argv)


if __name__ == "__main__":  # pragma: no cover - script entry point
    main()
