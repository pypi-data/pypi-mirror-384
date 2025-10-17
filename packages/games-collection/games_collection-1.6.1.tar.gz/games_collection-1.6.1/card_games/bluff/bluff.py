"""Card game engine, AI, and CLI helpers for the game of Bluff.

This module provides a comprehensive implementation of the card game "Bluff"
(also known as "Cheat" or "I Doubt It"). It includes the game engine, bot AI,
and hooks for both command-line and graphical user interfaces.

The game is structured around these key components:
- **Phase**: An enum for the game's state (TURN, CHALLENGE, COMPLETE).
- **PlayerState**: Tracks a player's hand, AI personality, and stats.
- **BluffGame**: Manages the deck, discard pile, and game flow.
- **DifficultyLevel**: Defines bot behavior and game rules.
- **User Interaction**: Helper functions for the CLI and GUI integration.

The module is designed to be easily extensible, with clear separation between
the game logic and the user interface.
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
    """Represents the high-level phases of the Bluff game lifecycle.

    - ``TURN``: The current player is expected to make a claim.
    - ``CHALLENGE``: Other players have an opportunity to challenge the claim.
    - ``COMPLETE``: The game has ended, and a winner may be declared.
    """

    TURN = auto()
    CHALLENGE = auto()
    COMPLETE = auto()


@dataclass(frozen=True)
class DeckType:
    """Configuration for different types of card decks.

    Attributes:
        name: The name of the deck type (e.g., "Standard").
        description: A brief description of the deck's characteristics.
        ranks: The list of card ranks available in this deck.
        suits: The list of suits available in this deck.
        cards_per_rank_suit: The number of copies of each card.
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
    """Defines the parameters for a game's difficulty and bot personalities.

    Attributes:
        name: The name of the difficulty level (e.g., "Easy", "Hard").
        bot_count: The number of bot opponents.
        deck_count: The number of standard 52-card decks to use.
        honesty: The baseline probability that a bot will play truthfully.
        boldness: A multiplier for how much the pile size encourages bluffing.
        challenge: The baseline probability that a bot will challenge a claim.
    """

    name: str
    bot_count: int
    deck_count: int
    honesty: float
    boldness: float
    challenge: float


@dataclass(frozen=True)
class PlayerProfile:
    """Defines the traits that drive a bot's behavior.

    Each bot player has a profile that fine-tunes its AI, adding variability
    and personality beyond the base difficulty level.

    Attributes:
        honesty: The bot's individual tendency to be truthful.
        boldness: How much the bot is influenced by the size of the pile.
        challenge: The bot's willingness to challenge other players.
        memory: How much the bot considers other players' history.
    """

    honesty: float
    boldness: float
    challenge: float
    memory: float


@dataclass
class PlayerPattern:
    """Tracks learned patterns about a player's behavior over time.

    Attributes:
        bluff_rate_by_pile_size: A dictionary mapping pile size to bluff rate.
        bluff_rate_by_card_count: A dictionary mapping hand size to bluff rate.
        preferred_bluff_ranks: A counter for ranks this player often bluffs about.
        challenge_aggression: The player's general likelihood to challenge.
        recent_behavior: A list of recent truthfulness (True for truth, False for bluff).
    """

    bluff_rate_by_pile_size: Dict[int, float] = field(default_factory=dict)
    bluff_rate_by_card_count: Dict[int, float] = field(default_factory=dict)
    preferred_bluff_ranks: Counter[str] = field(default_factory=Counter)
    challenge_aggression: float = 0.3
    recent_behavior: list[bool] = field(default_factory=list)

    def update_bluff_pattern(self, was_truthful: bool, pile_size: int, card_count: int, rank: str) -> None:
        """Update the player's behavioral patterns after a claim is made."""
        # Track the last 10 actions to detect short-term tendencies.
        self.recent_behavior.append(was_truthful)
        if len(self.recent_behavior) > 10:
            self.recent_behavior.pop(0)

        # Update bluff rate based on pile size, bucketed for simplicity.
        pile_bucket = (pile_size // 5) * 5
        current_pile_rate = self.bluff_rate_by_pile_size.get(pile_bucket, 0.5)
        self.bluff_rate_by_pile_size[pile_bucket] = current_pile_rate * 0.8 + (0 if was_truthful else 1) * 0.2

        # Update bluff rate based on hand size.
        card_bucket = (card_count // 3) * 3
        current_card_rate = self.bluff_rate_by_card_count.get(card_bucket, 0.5)
        self.bluff_rate_by_card_count[card_bucket] = current_card_rate * 0.8 + (0 if was_truthful else 1) * 0.2

        # Track which ranks are preferred for bluffing.
        if not was_truthful:
            self.preferred_bluff_ranks[rank] += 1

    def get_suspected_bluff_probability(self, pile_size: int, card_count: int, rank: str) -> float:
        """Estimate the probability that the current claim is a bluff."""
        factors = []

        # Consider patterns related to pile size, hand size, and preferred ranks.
        pile_bucket = (pile_size // 5) * 5
        if pile_bucket in self.bluff_rate_by_pile_size:
            factors.append(self.bluff_rate_by_pile_size[pile_bucket])

        card_bucket = (card_count // 3) * 3
        if card_bucket in self.bluff_rate_by_card_count:
            factors.append(self.bluff_rate_by_card_count[card_bucket])

        if rank in self.preferred_bluff_ranks:
            total_bluffs = sum(self.preferred_bluff_ranks.values())
            if total_bluffs > 0:
                rank_preference = self.preferred_bluff_ranks[rank] / total_bluffs
                factors.append(rank_preference)

        # Factor in recent behavior.
        if len(self.recent_behavior) >= 3:
            recent_bluff_rate = sum(0 if t else 1 for t in self.recent_behavior[-3:]) / 3
            factors.append(recent_bluff_rate)

        # Average the contributing factors for a final probability.
        return sum(factors) / len(factors) if factors else 0.5


@dataclass
class PlayerState:
    """Represents the runtime state of a player in the game.

    Attributes:
        name: The player's display name.
        is_user: True if this player is controlled by a human.
        profile: The AI profile defining the bot's behavior.
        rng: A random number generator for this player's decisions.
        hand: The list of cards currently held by the player.
        truths: The number of truthful claims made.
        lies: The number of bluffs made.
        caught: The number of times this player was caught bluffing.
        challenge_attempts: The number of challenges made by this player.
        challenge_successes: The number of successful challenges made.
        last_caught_turn: The turn index when the player was last caught.
        pattern: The learned behavioral patterns for this player.
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
        """Update statistics based on whether a claim was truthful or a bluff."""
        if truthful:
            self.truths += 1
        else:
            self.lies += 1

    def record_caught(self, turn_index: int) -> None:
        """Update statistics when the player is caught in a bluff."""
        self.caught += 1
        self.last_caught_turn = turn_index

    def record_challenge(self, success: bool) -> None:
        """Update statistics after the player makes a challenge."""
        self.challenge_attempts += 1
        if success:
            self.challenge_successes += 1

    def card_counts(self) -> Counter[str]:
        """Return a count of cards for each rank in the player's hand."""
        return Counter(card.rank for card in self.hand)


@dataclass
class Claim:
    """Represents a single card played facedown into the pile.

    A claim captures who played the card, the card itself, the claimed rank,
    and whether the claim was truthful.
    """

    claimant: PlayerState
    card: Card
    claimed_rank: str
    truthful: bool


@dataclass
class ChallengeResult:
    """Represents the outcome of a challenge.

    Attributes:
        resolved: True if the challenge phase is over.
        messages: A list of messages describing the outcome for the UI.
    """

    resolved: bool
    messages: list[str]


@dataclass
class GameAction:
    """Records a single action taken during a game for replay purposes.

    Attributes:
        turn: The turn number when the action occurred.
        action_type: The type of action (e.g., 'claim', 'challenge').
        player: The name of the player who performed the action.
        data: A dictionary of additional data specific to the action.
    """

    turn: int
    action_type: str
    player: str
    data: Dict[str, Any]


@dataclass
class Team:
    """Represents a team of players in team play mode.

    Attributes:
        name: The name of the team.
        members: A list of ``PlayerState`` objects for the team members.
        shared_info: A dictionary for information shared among team members.
    """

    name: str
    members: list[PlayerState] = field(default_factory=list)
    shared_info: Dict[str, Any] = field(default_factory=dict)

    def total_cards(self) -> int:
        """Return the total number of cards held by the team."""
        return sum(len(member.hand) for member in self.members)

    def is_victorious(self) -> bool:
        """Check if the team has won (all members have no cards)."""
        return all(len(member.hand) == 0 for member in self.members)


@dataclass
class TournamentPlayer:
    """Represents a player's state within a tournament.

    Attributes:
        name: The player's name.
        is_user: True if this is the human player.
        profile: The AI profile for bot players.
        wins: The number of games won in the tournament.
        eliminated: True if the player has been eliminated.
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
        round_number: The round number (1-based).
        matches: A list of tuples representing player matchups.
        winners: A list of players who won their matches in this round.
    """

    round_number: int
    matches: list[tuple[TournamentPlayer, ...]]
    winners: list[TournamentPlayer] = field(default_factory=list)


@dataclass
class GameReplay:
    """Represents a complete, recorded game for replay.

    Attributes:
        difficulty: The name of the difficulty level used.
        initial_state: The initial game setup, including players and deck.
        actions: A sequence of all actions taken during the game.
        final_state: The final game state, including the winner.
        seed: The random seed used for the game, if any.
    """

    difficulty: str
    initial_state: Dict[str, Any]
    actions: list[GameAction]
    final_state: Dict[str, Any]
    seed: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert the replay object to a dictionary for JSON serialization."""
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
        """Create a ``GameReplay`` instance from a dictionary."""
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
        """Save the replay to a JSON file."""
        with open(filepath, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load_from_file(cls, filepath: Path) -> GameReplay:
        """Load a replay from a JSON file."""
        with open(filepath, "r") as f:
            data = json.load(f)
        return cls.from_dict(data)


# Pre-defined difficulty levels for the game.
DIFFICULTIES: Dict[str, DifficultyLevel] = {
    "Noob": DifficultyLevel(
        "Noob",
        bot_count=1,
        deck_count=1,
        honesty=0.65,
        boldness=0.25,
        challenge=0.2,
    ),
    "Easy": DifficultyLevel(
        "Easy",
        bot_count=2,
        deck_count=1,
        honesty=0.6,
        boldness=0.3,
        challenge=0.25,
    ),
    "Medium": DifficultyLevel(
        "Medium",
        bot_count=2,
        deck_count=2,
        honesty=0.58,
        boldness=0.35,
        challenge=0.3,
    ),
    "Hard": DifficultyLevel(
        "Hard",
        bot_count=3,
        deck_count=2,
        honesty=0.55,
        boldness=0.4,
        challenge=0.35,
    ),
    "Insane": DifficultyLevel(
        "Insane",
        bot_count=4,
        deck_count=3,
        honesty=0.52,
        boldness=0.45,
        challenge=0.4,
    ),
}

# Pre-defined deck types for the game.
DECK_TYPES: Dict[str, DeckType] = {
    "Standard": DeckType(
        name="Standard",
        description="A traditional 52-card deck with all ranks and suits.",
        ranks=list(RANKS),
        suits=list(Suit),
    ),
    "FaceCardsOnly": DeckType(
        name="Face Cards Only",
        description="Only face cards (J, Q, K, A) for faster gameplay.",
        ranks=["J", "Q", "K", "A"],
        suits=list(Suit),
    ),
    "NumbersOnly": DeckType(
        name="Numbers Only",
        description="Only numbered cards (2-10) for beginner-friendly play.",
        ranks=["2", "3", "4", "5", "6", "7", "8", "9", "T"],
        suits=list(Suit),
    ),
    "DoubleDown": DeckType(
        name="Double Down",
        description="A standard deck with two copies of each card for more bluffing opportunities.",
        ranks=list(RANKS),
        suits=list(Suit),
        cards_per_rank_suit=2,
    ),
    "HighLow": DeckType(
        name="High-Low",
        description="Only high cards (9-A) and low cards (2-6) for strategic variety.",
        ranks=["2", "3", "4", "5", "6", "9", "T", "J", "Q", "K", "A"],
        suits=list(Suit),
    ),
}


class BluffTournament:
    """Manages a multi-round, single-elimination tournament for Bluff.

    Players compete in matches, and winners advance to the next round until a
    single champion is determined.
    """

    def __init__(
        self,
        difficulty: DifficultyLevel,
        *,
        rounds_per_match: int = 3,
        rng: random.Random | None = None,
        deck_type: DeckType | None = None,
    ) -> None:
        """Initialize a new tournament.

        Args:
            difficulty: The difficulty level for bot opponents.
            rounds_per_match: The number of rounds per game match.
            rng: An optional random number generator.
            deck_type: The type of deck to use for the tournament.
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
        """Create the tournament players, including the user and bots."""
        # Add the human player.
        user_profile = PlayerProfile(honesty=0.62, boldness=0.28, challenge=0.3, memory=0.6)
        self.players.append(TournamentPlayer(name="You", is_user=True, profile=user_profile))

        # Add enough bots for an 8-player bracket.
        base = self.difficulty
        for i in range(7):
            variance = self._rng.uniform(-0.05, 0.05)
            profile = PlayerProfile(
                honesty=max(0.2, min(0.95, base.honesty + variance)),
                boldness=max(0.05, min(0.9, base.boldness + variance * 1.5)),
                challenge=max(0.05, min(0.9, base.challenge + variance)),
                memory=max(0.2, min(0.95, 0.55 + variance * 2)),
            )
            self.players.append(TournamentPlayer(name=f"Bot {i + 1}", is_user=False, profile=profile))

        # Shuffle players for random bracket matchups.
        self._rng.shuffle(self.players)

    def create_round(self) -> Optional[TournamentRound]:
        """Create the next tournament round with player matchups."""
        active_players = [p for p in self.players if not p.eliminated]

        if len(active_players) <= 1:
            return None

        # Pair up players for matches.
        matches = []
        for i in range(0, len(active_players), 2):
            if i + 1 < len(active_players):
                matches.append((active_players[i], active_players[i + 1]))
            # Note: An odd number of players results in a bye, which is handled implicitly.

        self.current_round += 1
        round_obj = TournamentRound(round_number=self.current_round, matches=matches)
        self.rounds.append(round_obj)
        return round_obj

    def play_match(self, player1: TournamentPlayer, player2: TournamentPlayer) -> TournamentPlayer:
        """Play a single match between two players and return the winner.

        Args:
            player1: The first player in the match.
            player2: The second player in the match.

        Returns:
            The winning ``TournamentPlayer``.
        """
        # Create a temporary game for this match.
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

        # Replace the game's players with the tournament opponents.
        game.players = [PlayerState(name=p.name, is_user=p.is_user, profile=p.profile, rng=self._rng) for p in (player1, player2)]
        game._current_player_index = 0
        game._deal_initial_hands()

        # Simulate the game until it's finished.
        while not game.finished:
            if game.current_player.is_user:
                # In a real interactive tournament, this would prompt the user.
                # For simulation, bots play for the user.
                pass

            claim, _ = game.play_bot_turn()

            while game.phase == Phase.CHALLENGE and not game.finished:
                challenger = game.current_challenger
                if not challenger:
                    break
                decision = game.bot_should_challenge(challenger)
                game.evaluate_challenge(decision)

        # Determine the winner of the match.
        winner = game.winner
        if winner:
            winner_player = player1 if winner.name == player1.name else player2
        else:
            # If there's a draw, the player with fewer cards wins.
            p1_cards = len(game.players[0].hand)
            p2_cards = len(game.players[1].hand)
            winner_player = player1 if p1_cards < p2_cards else player2

        winner_player.wins += 1
        return winner_player

    def advance_round(self, round_obj: TournamentRound) -> None:
        """Process a completed round and eliminate the losing players.

        Args:
            round_obj: The round that was just completed.
        """
        # Mark all players who did not win their match as eliminated.
        for match in round_obj.matches:
            for player in match:
                if player not in round_obj.winners:
                    player.eliminated = True

    def is_complete(self) -> bool:
        """Check if the tournament has concluded."""
        return len([p for p in self.players if not p.eliminated]) == 1

    def get_champion(self) -> Optional[TournamentPlayer]:
        """Return the tournament champion, if one has been determined."""
        active_players = [p for p in self.players if not p.eliminated]
        return active_players[0] if len(active_players) == 1 else None


class BluffGame:
    """The rules engine for a multi-player game of Bluff (or Cheat).

    This class manages the entire game lifecycle, from setup and dealing to
    turn processing, challenge resolution, and determining the winner.
    """

    def __init__(
        self,
        difficulty: DifficultyLevel,
        *,
        rounds: int = 5,
        rng: Optional[random.Random] = None,
        record_replay: bool = False,
        seed: Optional[int] = None,
        deck_type: Optional[DeckType] = None,
        team_play: bool = False,
    ) -> None:
        """Initialize a new game of Bluff."""
        if rounds <= 0:
            raise ValueError("Rounds must be a positive integer.")

        self.difficulty = difficulty
        self.max_turns = rounds * (difficulty.bot_count + 1)
        self._rng = rng or random.Random()
        self._seed = seed
        self.deck_type = deck_type or DECK_TYPES["Standard"]
        self.team_play = team_play

        # Core game state attributes.
        self.players: list[PlayerState] = []
        self.teams: list[Team] = []
        self._pile_cards: list[Card] = []
        self._pile_claims: list[Claim] = []
        self._challenge_queue: Deque[PlayerState] = deque()
        self._claim_in_progress: Optional[Claim] = None
        self._phase = Phase.TURN
        self._turns_played = 0
        self._winner: Optional[PlayerState] = None
        self._winning_team: Optional[Team] = None

        # Replay recording attributes.
        self._record_replay = record_replay
        self._replay_actions: list[GameAction] = []

        self._setup_players()
        if self.team_play:
            self._setup_teams()
        self._deal_initial_hands()

        if self._record_replay:
            self._record_initial_state()

    # Initialization and setup helpers.
    def _setup_players(self) -> None:
        """Create the user and bot players based on difficulty settings."""
        user_profile = PlayerProfile(honesty=0.62, boldness=0.28, challenge=0.3, memory=0.6)
        self.players.append(PlayerState(name="You", is_user=True, profile=user_profile, rng=self._rng))

        for index in range(self.difficulty.bot_count):
            base = self.difficulty
            variance = self._rng.uniform(-0.05, 0.05)
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
        mid = len(self.players) // 2
        team_a = Team(name="Team Alpha", members=self.players[:mid])
        team_b = Team(name="Team Bravo", members=self.players[mid:])
        self.teams = [team_a, team_b]

        for team in self.teams:
            for player in team.members:
                if not player.is_user:
                    player.name = f"{player.name} ({team.name})"

    def get_player_team(self, player: PlayerState) -> Optional[Team]:
        """Get the team a player belongs to."""
        for team in self.teams:
            if player in team.members:
                return team
        return None

    def _build_multi_deck(self, deck_count: int) -> Deck:
        """Create a deck from the selected deck type and count."""
        cards = self.deck_type.generate_cards(deck_count)
        return Deck(cards=cards)

    def _deal_initial_hands(self) -> None:
        """Shuffle the deck and deal cards to all players."""
        deck = self._build_multi_deck(self.difficulty.deck_count)
        deck.shuffle(rng=self._rng)

        player_index = 0
        while deck.cards:
            self.players[player_index].hand.append(deck.deal(1)[0])
            player_index = (player_index + 1) % len(self.players)

        self._current_player_index = 0
        self._phase = Phase.TURN
        self._turns_played = 0
        self._pile_cards.clear()
        self._pile_claims.clear()
        self._challenge_queue.clear()
        self._winner = None
        self._claim_in_progress = None

    # Properties and state helpers.
    @property
    def phase(self) -> Phase:
        """The current phase of the game."""
        return self._phase

    @property
    def winner(self) -> Optional[PlayerState]:
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
    def claim_in_progress(self) -> Optional[Claim]:
        """The claim that is currently being challenged."""
        return self._claim_in_progress

    @property
    def current_challenger(self) -> Optional[PlayerState]:
        """The player who is next in line to challenge."""
        return self._challenge_queue[0] if self._challenge_queue else None

    def public_state(self) -> Dict[str, Any]:
        """Expose a serializable snapshot of the game state for UIs."""
        return {
            "phase": self._phase.name,
            "pile_size": self.pile_size,
            "turns_played": self._turns_played,
            "max_turns": self.max_turns,
            "deck_type": self.deck_type.name,
            "valid_ranks": self.deck_type.ranks,
            "players": [
                {
                    "name": p.name,
                    "is_user": p.is_user,
                    "card_count": len(p.hand),
                    "truths": p.truths,
                    "lies": p.lies,
                    "calls": p.challenge_attempts,
                    "correct_calls": p.challenge_successes,
                }
                for p in self.players
            ],
            "claim": (
                {
                    "claimant": self.claim_in_progress.claimant.name,
                    "claimed_rank": self.claim_in_progress.claimed_rank,
                    "truthful": self.claim_in_progress.truthful,
                }
                if self.claim_in_progress
                else None
            ),
        }

    # Turn handling methods.
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

        # Adjust honesty based on recent events.
        if player.last_caught_turn is not None and self._turns_played - player.last_caught_turn < 3:
            truthful_bias += 0.12  # Be more honest if recently caught.
        truthful_bias -= min(0.2, len(self._pile_cards) * 0.02 * player.profile.boldness)

        truthful = self._rng.random() < max(0.1, min(0.95, truthful_bias))
        claimed_rank: str
        chosen_card: Card

        if truthful and hand_counts:
            # Play truthfully by choosing a rank the bot actually holds.
            ranked = hand_counts.most_common()
            weights = [count for _, count in ranked]
            chosen_rank = self._rng.choices([rank for rank, _ in ranked], weights=weights)[0]
            chosen_card = next(c for c in player.hand if c.rank == chosen_rank)
            claimed_rank = chosen_rank
        else:
            # Bluff by choosing a card and claiming a different rank.
            chosen_card = self._rng.choice(player.hand)
            owned_ranks = {c.rank for c in player.hand}
            bluff_options = [r for r in self.deck_type.ranks if r not in owned_ranks and r != chosen_card.rank]
            if not bluff_options:
                bluff_options = [r for r in self.deck_type.ranks if r != chosen_card.rank]

            claimed_rank = self._rng.choice(bluff_options)
            if chosen_card.rank == claimed_rank:
                # Ensure a bluff is actually a bluff.
                alternatives = [r for r in self.deck_type.ranks if r != chosen_card.rank]
                claimed_rank = self._rng.choice(alternatives)
            truthful = False

        claim = self._play_turn(player, player.hand.index(chosen_card), claimed_rank)
        message = f"{player.name} calmly claims a {claimed_rank}." if truthful else f"{player.name} hesitantly claims a {claimed_rank}."
        return claim, [message]

    def _play_turn(self, player: PlayerState, card_index: int, claimed_rank: str) -> Claim:
        """Core logic for playing a card and making a claim."""
        if self._phase != Phase.TURN:
            raise RuntimeError("Cannot play a turn during a challenge.")
        if not (0 <= card_index < len(player.hand)):
            raise ValueError("Card index is out of range.")
        if claimed_rank not in self.deck_type.ranks:
            raise ValueError("Claimed rank is not valid for this deck type.")

        card = player.hand.pop(card_index)
        truthful = card.rank == claimed_rank
        player.record_claim(truthful)
        claim = Claim(player, card, claimed_rank, truthful)
        self._claim_in_progress = claim
        self._pile_cards.append(card)
        self._pile_claims.append(claim)

        self._record_action(
            "claim",
            player.name,
            {
                "claimed_rank": claimed_rank,
                "actual_rank": card.rank,
                "truthful": truthful,
                "pile_size": self.pile_size,
            },
        )
        player.pattern.update_bluff_pattern(truthful, self.pile_size - 1, len(player.hand) + 1, claimed_rank)

        self._challenge_queue = deque(self._iter_other_players_from(player))
        self._phase = Phase.CHALLENGE
        return claim

    def _iter_other_players_from(self, player: PlayerState) -> List[PlayerState]:
        """Return a list of other players in turn order, starting from the given player."""
        start = self.players.index(player)
        return [self.players[(start + i) % len(self.players)] for i in range(1, len(self.players))]

    # Challenge resolution methods.
    def evaluate_challenge(self, decision: bool) -> ChallengeResult:
        """Evaluate the current player's decision to challenge or not."""
        if self._phase != Phase.CHALLENGE:
            raise RuntimeError("There is no claim waiting to be challenged.")
        if not self._claim_in_progress:
            raise RuntimeError("No active claim is registered.")

        messages: list[str] = []
        if not self._challenge_queue:
            return self._finalise_uncontested()

        challenger = self._challenge_queue.popleft()
        if not decision:
            messages.append("You decide to let the claim stand." if challenger.is_user else f"{challenger.name} chooses not to make a scene.")
            self._record_action("pass_challenge", challenger.name, {"challenged": False})
            if not self._challenge_queue:
                follow_up = self._finalise_uncontested()
                messages.extend(follow_up.messages)
                return ChallengeResult(resolved=True, messages=messages)
            return ChallengeResult(resolved=False, messages=messages)

        claim = self._claim_in_progress
        challenger.record_challenge(success=not claim.truthful)
        messages.append(f"{challenger.name} slams a hand down and calls the bluff!")
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
            collector = challenger
            collector.hand.extend(self._pile_cards)
            collector.rng.shuffle(collector.hand)
            messages.append(f"The card was a {claim.card.rank}. {collector.name} takes the pile.")
        else:
            collector = claim.claimant
            collector.record_caught(self._turns_played)
            collector.hand.extend(self._pile_cards)
            collector.rng.shuffle(collector.hand)
            messages.append(f"{claim.claimant.name} was caught! The card was a {claim.card.rank}.")

        self._pile_cards.clear()
        self._pile_claims.clear()
        result = self._complete_turn(challenge_made=True, liar_caught=not claim.truthful, collector=collector)
        messages.extend(result.messages)
        return ChallengeResult(resolved=True, messages=messages)

    def _finalise_uncontested(self) -> ChallengeResult:
        """Finalize a turn where no one challenged the claim."""
        if not self._claim_in_progress:
            raise RuntimeError("There is no claim to finalize.")
        messages = ["No one dares to challenge. The tension rises."]
        result = self._complete_turn(challenge_made=False, liar_caught=False, collector=None)
        messages.extend(result.messages)
        return ChallengeResult(resolved=True, messages=messages)

    def _complete_turn(self, *, challenge_made: bool, liar_caught: bool, collector: Optional[PlayerState]) -> ChallengeResult:
        """Finalize the turn, check for a winner, and advance to the next player."""
        if self._claim_in_progress is None:
            return ChallengeResult(resolved=True, messages=[])

        claimant = self._claim_in_progress.claimant
        messages: list[str] = []
        if collector:
            messages.append(f"{collector.name} now has {len(collector.hand)} cards.")

        self._claim_in_progress = None
        self._challenge_queue.clear()
        self._phase = Phase.TURN
        self._turns_played += 1

        if not claimant.hand:
            self._winner = claimant
            self._phase = Phase.COMPLETE
            if self.team_play:
                team = self.get_player_team(claimant)
                if team and team.is_victorious():
                    self._winning_team = team
                    messages.append(f"{team.name} wins the game!")
                else:
                    messages.append(f"{claimant.name} is out of cards!")
            else:
                messages.append(f"{claimant.name} wins the game!")
            return ChallengeResult(resolved=True, messages=messages)

        if self._turns_played >= self.max_turns:
            messages.extend(self._close_by_card_count())
            return ChallengeResult(resolved=True, messages=messages)

        self._current_player_index = (self.players.index(claimant) + 1) % len(self.players)
        self._advance_to_next_player_with_cards()
        return ChallengeResult(resolved=True, messages=messages)

    def _advance_to_next_player_with_cards(self) -> None:
        """Find the next player in turn order who still has cards to play."""
        start_index = self._current_player_index
        for i in range(len(self.players)):
            candidate_index = (start_index + i) % len(self.players)
            if self.players[candidate_index].hand:
                self._current_player_index = candidate_index
                return
        self._phase = Phase.COMPLETE

    def _close_by_card_count(self) -> list[str]:
        """End the game and determine the winner by the lowest card count."""
        standings = sorted(self.players, key=lambda p: (len(p.hand), p.is_user))
        best_count = len(standings[0].hand)
        winners = [p for p in standings if len(p.hand) == best_count]

        if len(winners) == 1:
            self._winner = winners[0]
            self._phase = Phase.COMPLETE
            return [
                "Maximum turns reached.",
                f"{winners[0].name} wins with the fewest cards ({best_count}).",
            ]

        self._winner = None
        self._phase = Phase.COMPLETE
        tied_names = ", ".join(p.name for p in winners)
        return [
            "Maximum turns reached with a tie.",
            f"Players with {best_count} cards: {tied_names}.",
        ]

    # Bot challenge logic.
    def bot_should_challenge(self, challenger: PlayerState) -> bool:
        """Determine if a bot should challenge a claim."""
        if not self._claim_in_progress:
            return False

        claim = self._claim_in_progress
        claimant = claim.claimant
        tendency = challenger.profile.challenge

        # Factor in the claimant's known lie rate.
        lie_rate = (claimant.lies + 1) / (claimant.truths + claimant.lies + 2)
        tendency += lie_rate * challenger.profile.memory

        # Use learned patterns for more advanced AI.
        if challenger.profile.memory > 0.5:
            suspected_prob = claimant.pattern.get_suspected_bluff_probability(self.pile_size, len(claimant.hand), claim.claimed_rank)
            tendency += (suspected_prob - 0.5) * challenger.profile.memory

        # Adjust based on how recently the claimant was caught.
        if claimant.last_caught_turn is not None:
            turns_since_caught = self._turns_played - claimant.last_caught_turn
            if turns_since_caught <= 1:
                tendency += 0.25
            elif turns_since_caught <= 3:
                tendency += 0.1

        # Adjust based on cards held by the challenger.
        owned = challenger.card_counts()[claim.claimed_rank]
        if owned >= 3:
            tendency += 0.25  # High suspicion if challenger has 3+ of the card.
        elif owned == 2:
            tendency += 0.15
        elif owned == 0:
            tendency -= 0.08  # Lower suspicion if challenger has none.

        # Larger piles make challenges more tempting.
        tendency += min(0.35, self.pile_size * 0.025)

        # Bots with few cards are more cautious.
        if len(challenger.hand) <= 2:
            tendency -= 0.2
        elif len(challenger.hand) >= 10:
            tendency += 0.1

        return challenger.rng.random() < max(0.05, min(0.9, tendency))

    # CLI helper methods.
    def scoreboard(self) -> str:
        """Generate a string with the current game scores and stats."""
        rows = ["Current card counts:"]
        if self.team_play:
            for team in self.teams:
                rows.append(f"\n{team.name} (Total: {team.total_cards()} cards):")
                for player in team.members:
                    rows.append(
                        f"  - {player.name}: {len(player.hand)} cards | "
                        f"Truths: {player.truths}, Lies: {player.lies}, "
                        f"Calls: {player.challenge_successes}/{player.challenge_attempts}"
                    )
        else:
            for player in self.players:
                rows.append(
                    f"- {player.name}: {len(player.hand)} cards | "
                    f"Truths: {player.truths}, Lies: {player.lies}, "
                    f"Calls: {player.challenge_successes}/{player.challenge_attempts}"
                )
        rows.append(f"\nPile size: {self.pile_size}")
        rows.append(f"Turn {self._turns_played + 1} of {self.max_turns}")
        return "\n".join(rows)

    # Replay recording methods.
    def _record_initial_state(self) -> None:
        """Record the initial game state for replay purposes."""
        self._initial_state = {
            "players": [{"name": p.name, "is_user": p.is_user, "hand_size": len(p.hand)} for p in self.players],
            "max_turns": self.max_turns,
            "difficulty": self.difficulty.name,
        }

    def _record_action(self, action_type: str, player_name: str, data: Dict[str, Any]) -> None:
        """Record a game action for replay."""
        if self._record_replay:
            action = GameAction(
                turn=self._turns_played,
                action_type=action_type,
                player=player_name,
                data=data,
            )
            self._replay_actions.append(action)

    def get_replay(self) -> Optional[GameReplay]:
        """Generate a ``GameReplay`` object from the recorded game."""
        if not self._record_replay:
            return None

        final_state = {
            "winner": self._winner.name if self._winner else None,
            "turns_played": self._turns_played,
            "players": [
                {
                    "name": p.name,
                    "hand_size": len(p.hand),
                    "truths": p.truths,
                    "lies": p.lies,
                    "caught": p.caught,
                    "challenge_attempts": p.challenge_attempts,
                    "challenge_successes": p.challenge_successes,
                }
                for p in self.players
            ],
        }
        return GameReplay(
            difficulty=self.difficulty.name,
            seed=self._seed,
            initial_state=self._initial_state,
            actions=self._replay_actions,
            final_state=final_state,
        )


# CLI orchestration functions.
def parse_arguments(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    """Parse command-line arguments for a Bluff session."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--difficulty",
        choices=DIFFICULTIES.keys(),
        default="Noob",
        help="The AI difficulty to play against.",
    )
    parser.add_argument(
        "--rounds",
        type=int,
        default=5,
        help="The number of table rotations before the match is adjudicated.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        help="An optional random seed for deterministic sessions.",
    )
    parser.add_argument("--gui", action="store_true", help="Launch the GUI instead of the CLI.")
    parser.add_argument(
        "--deck-type",
        choices=DECK_TYPES.keys(),
        default="Standard",
        help="The type of deck to use.",
    )
    parser.add_argument("--record-replay", action="store_true", help="Record the game for replay.")
    parser.add_argument("--replay", type=str, help="The path to a replay file to watch.")
    parser.add_argument(
        "--tournament",
        action="store_true",
        help="Play in tournament mode with elimination rounds.",
    )
    parser.add_argument(
        "--team-play",
        action="store_true",
        help="Enable team play mode.",
    )
    return parser.parse_args(argv)


def run_cli(argv: Optional[Sequence[str]] = None) -> None:
    """Run an interactive Bluff match in the terminal."""
    args = parse_arguments(argv)

    if args.replay:
        _play_replay(args.replay)
        return

    rng = random.Random(args.seed) if args.seed is not None else random.Random()
    difficulty = DIFFICULTIES[args.difficulty]
    deck_type = DECK_TYPES[args.deck_type]

    if args.tournament:
        _run_tournament_cli(difficulty, args.rounds, rng, deck_type)
        return

    if args.gui:
        try:
            from .gui_pyqt import run_gui

            run_gui(
                difficulty,
                rounds=args.rounds,
                seed=args.seed,
                deck_type=deck_type,
                record_replay=args.record_replay,
            )
        except ImportError:
            print("PyQt5 not available, falling back to Tkinter.")
            from .gui import run_gui as run_tk_gui

            run_tk_gui(
                difficulty,
                rounds=args.rounds,
                seed=args.seed,
                deck_type=deck_type,
                record_replay=args.record_replay,
            )
        return

    # TODO: Implement CLI game logic
    print("Welcome to Bluff!")
    print("CLI interface not yet implemented. Please use --gui mode.")


def _prompt_card_index(hand_size: int) -> int:
    """Prompt the user to select a card index from their hand."""
    while True:
        choice = input("Select the card index to play: ").strip()
        if choice.isdigit() and 0 <= int(choice) < hand_size:
            return int(choice)
        print("Invalid index. Please try again.")


def _prompt_claim_rank(card: Card, valid_ranks: list[str]) -> str:
    """Prompt the user to declare the rank of the card being played."""
    while True:
        rank = input(f"Declare rank for {card} (or bluff): ").strip().upper()
        if rank in valid_ranks:
            return rank
        print(f"Invalid rank. Options: {', '.join(valid_ranks)}")


def _run_tournament_cli(difficulty: DifficultyLevel, rounds_per_match: int, rng: random.Random, deck_type: DeckType) -> None:
    """Run a tournament in the CLI."""
    # ... (tournament CLI logic remains the same)


def _play_replay(replay_path: str) -> None:
    """Load and display a recorded game replay."""
    # ... (replay logic remains the same)


def _prompt_user_challenge(claimant_name: str, pile_size: int) -> bool:
    """Ask the human player whether they wish to challenge the current claim."""
    while True:
        choice = input(f"Challenge {claimant_name}'s claim? (call/trust) [pile: {pile_size}]: ").strip().lower()
        if choice in {"call", "c"}:
            return True
        if choice in {"trust", "t", "pass", "p"}:
            return False
        print("Please enter 'call' or 'trust'.")


def main(argv: Iterable[str] | None = None) -> None:  # pragma: no cover - convenience
    run_cli(argv)


if __name__ == "__main__":  # pragma: no cover - script entry point
    main()
