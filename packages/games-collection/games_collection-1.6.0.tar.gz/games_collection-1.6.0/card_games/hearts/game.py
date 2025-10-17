"""Hearts game engine.

Hearts is a trick-taking card game where the goal is to avoid taking hearts and
the Queen of Spades (which are worth penalty points). However, a player who takes
ALL the hearts and the Queen of Spades "shoots the moon" and instead gives 26 points
to all other players.

The game includes:
- Passing cards phase (3 cards passed in rotating directions)
- Trick-taking with hearts and Queen of Spades as penalty cards
- Shooting the moon detection and scoring
- AI that tries to avoid hearts
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Iterable, Optional, Sequence

from card_games.common.cards import Card, Deck, Suit


class PassDirection(Enum):
    """Direction to pass cards in Hearts."""

    LEFT = auto()
    RIGHT = auto()
    ACROSS = auto()
    NONE = auto()  # No passing on 4th hand


TWO_OF_CLUBS = Card("2", Suit.CLUBS)
QUEEN_OF_SPADES = Card("Q", Suit.SPADES)


@dataclass(eq=False)
class HeartsPlayer:
    """Represents a player in Hearts.

    Attributes:
        name: Player's name
        hand: Cards currently in hand
        tricks_won: Cards won in tricks this round
        score: Total score across all rounds
        is_ai: Whether this is an AI player
    """

    name: str
    hand: list[Card] = field(default_factory=list)
    tricks_won: list[Card] = field(default_factory=list)
    score: int = 0
    is_ai: bool = False

    def has_suit(self, suit: Suit) -> bool:
        """Check if player has any cards of the given suit."""
        return any(card.suit == suit for card in self.hand)

    def has_only_hearts(self) -> bool:
        """Check if player has only hearts in hand."""
        return all(card.suit == Suit.HEARTS for card in self.hand)

    def calculate_round_points(self) -> int:
        """Calculate points for this round based on tricks won.

        Returns:
            Points (higher is worse in Hearts).
        """
        points = 0
        for card in self.tricks_won:
            if card.suit == Suit.HEARTS:
                points += 1
            elif card == QUEEN_OF_SPADES:
                points += 13
        return points


@dataclass(frozen=True)
class TrickRecord:
    """Snapshot of a completed trick used for post-round analysis.

    Attributes:
        leader: Name of the player who led the trick.
        cards: Ordered sequence of ``(player_name, card)`` tuples in play order.
        winner: Name of the player who captured the trick.
    """

    leader: str
    cards: tuple[tuple[str, Card], ...]
    winner: str


class HeartsGame:
    """Main engine for the Hearts card game.

    This class manages the game flow including dealing, passing cards,
    trick-taking, and scoring.
    """

    def __init__(self, players: list[HeartsPlayer], *, rng=None):
        """Initialize a Hearts game.

        Args:
            players: List of 4 players
            rng: Optional random number generator
        """
        if len(players) != 4:
            raise ValueError("Hearts requires exactly 4 players")

        self.players = players
        self.rng = rng
        self.deck = Deck()
        self.round_number = 0
        self.hearts_broken = False
        self.current_trick: list[tuple[HeartsPlayer, Card]] = []
        self.lead_suit: Optional[Suit] = None
        self._current_trick_leader: Optional[HeartsPlayer] = None
        self.trick_number = 0
        self.trick_history: list[TrickRecord] = []
        self.last_round_tricks: list[TrickRecord] = []
        self.last_round_scores: dict[str, int] = {}
        self.last_round_events: dict[str, str] = {}
        self.pass_history: list[dict[str, list[Card]]] = []

    def deal_cards(self) -> None:
        """Deal all 52 cards evenly to 4 players (13 each)."""
        self.deck = Deck()
        if self.rng:
            self.deck.shuffle(rng=self.rng)
        else:
            self.deck.shuffle()

        # Archive the just-completed round for post-game inspection
        if self.trick_history:
            self.last_round_tricks = list(self.trick_history)
        self.trick_history = []
        self.current_trick = []
        self.lead_suit = None
        self._current_trick_leader = None
        self.trick_number = 0
        self.hearts_broken = False

        # Clear hands and tricks
        for player in self.players:
            player.hand = []
            player.tricks_won = []

        # Deal 13 cards to each player
        for _ in range(13):
            for player in self.players:
                player.hand.append(self.deck.deal(1)[0])

        # Sort hands by suit and rank
        for player in self.players:
            self._sort_hand(player)

    def get_pass_direction(self) -> PassDirection:
        """Get the passing direction for the current round.

        Returns:
            PassDirection based on round number (cycles every 4 rounds).
        """
        directions = [PassDirection.LEFT, PassDirection.RIGHT, PassDirection.ACROSS, PassDirection.NONE]
        return directions[self.round_number % 4]

    def pass_cards(self, passes: dict[HeartsPlayer, Sequence[Card]]) -> None:
        """Execute the card passing phase.

        Args:
            passes: Dictionary mapping each player to 3 cards they want to pass.
        """
        direction = self.get_pass_direction()

        if direction == PassDirection.NONE:
            return

        # Validate passes
        if set(passes.keys()) != set(self.players):
            raise ValueError("Passes must include all players in the round")

        for player, cards in passes.items():
            if len(cards) != 3:
                raise ValueError(f"{player.name} must pass exactly 3 cards")
            seen: set[Card] = set()
            for card in cards:
                if card not in player.hand:
                    raise ValueError(f"{player.name} doesn't have {card}")
                if card in seen:
                    raise ValueError(f"{player.name} cannot pass duplicate cards")
                seen.add(card)

        # Remove cards from hands
        temp_passes = {}
        for player, cards in passes.items():
            temp_passes[player] = list(cards)
            for card in cards:
                player.hand.remove(card)

        # Give cards to recipients
        for i, player in enumerate(self.players):
            if direction == PassDirection.LEFT:
                recipient = self.players[(i + 1) % 4]
            elif direction == PassDirection.RIGHT:
                recipient = self.players[(i - 1) % 4]
            else:  # ACROSS
                recipient = self.players[(i + 2) % 4]

            recipient.hand.extend(temp_passes[player])

        # Sort hands again
        for player in self.players:
            self._sort_hand(player)

        # Record the pass for history purposes
        pass_snapshot = {player.name: list(cards) for player, cards in temp_passes.items()}
        self.pass_history.append(pass_snapshot)

    def find_starting_player(self) -> HeartsPlayer:
        """Find the player with the 2 of Clubs (starts the game).

        Returns:
            The player who has the 2 of Clubs.
        """
        for player in self.players:
            if TWO_OF_CLUBS in player.hand:
                return player
        raise RuntimeError("No player has 2 of Clubs")

    @staticmethod
    def _sort_hand(player: HeartsPlayer) -> None:
        """Sort a player's hand in-place by suit then rank."""

        player.hand.sort(key=lambda c: (c.suit.value, c.value))

    @staticmethod
    def _is_penalty_card(card: Card) -> bool:
        """Return whether a card is worth penalty points."""

        return card.suit == Suit.HEARTS or card == QUEEN_OF_SPADES

    def is_valid_play(self, player: HeartsPlayer, card: Card) -> bool:
        """Check if a card play is valid.

        Args:
            player: The player attempting to play
            card: The card to play

        Returns:
            True if the play is valid, False otherwise.
        """
        if card not in player.hand:
            return False

        is_first_trick = self.trick_number == 0

        # Leading a trick
        if not self.current_trick:
            if is_first_trick:
                return card == TWO_OF_CLUBS
            if card.suit == Suit.HEARTS and not (self.hearts_broken or player.has_only_hearts()):
                return False
            return True

        # Following a trick: must follow suit if possible
        if self.lead_suit and player.has_suit(self.lead_suit):
            return card.suit == self.lead_suit

        # Out of suit: additional first trick restrictions
        if is_first_trick:
            if self._is_penalty_card(card):
                safe_cards = [c for c in player.hand if not self._is_penalty_card(c)]
                return not safe_cards

        return True

    def play_card(self, player: HeartsPlayer, card: Card) -> None:
        """Play a card to the current trick.

        Args:
            player: The player playing the card
            card: The card to play
        """
        if not self.is_valid_play(player, card):
            raise ValueError(f"Invalid play: {player.name} cannot play {card}")

        player.hand.remove(card)
        self.current_trick.append((player, card))

        # Set lead suit for this trick
        if len(self.current_trick) == 1:
            self.lead_suit = card.suit
            self._current_trick_leader = player

        # Break hearts if a heart or the queen of spades is played
        if card.suit == Suit.HEARTS or card == QUEEN_OF_SPADES:
            self.hearts_broken = True

    def complete_trick(self) -> HeartsPlayer:
        """Complete the current trick and determine the winner.

        Returns:
            The player who won the trick.
        """
        if len(self.current_trick) != 4:
            raise RuntimeError("Trick is not complete")

        # Find highest card of lead suit
        winner = self.current_trick[0][0]
        winning_card = self.current_trick[0][1]

        for player, card in self.current_trick[1:]:
            if card.suit == self.lead_suit and card.value > winning_card.value:
                winner = player
                winning_card = card

        # Give all cards to winner
        for _, card in self.current_trick:
            winner.tricks_won.append(card)

        trick_snapshot = TrickRecord(
            leader=self._current_trick_leader.name if self._current_trick_leader else self.current_trick[0][0].name,
            cards=tuple((p.name, c) for p, c in self.current_trick),
            winner=winner.name,
        )
        self.trick_history.append(trick_snapshot)

        # Reset for next trick
        self.current_trick = []
        self.lead_suit = None
        self._current_trick_leader = None
        self.trick_number += 1

        return winner

    def calculate_scores(self) -> dict[str, int]:
        """Calculate scores for the round and check for shooting the moon.

        Returns:
            Dictionary mapping player names to their points for this round.
        """
        round_scores = {player.name: player.calculate_round_points() for player in self.players}

        shooter: Optional[HeartsPlayer] = None
        events: dict[str, str] = {}
        for player in self.players:
            if round_scores[player.name] == 26:
                shooter = player
                if len(player.tricks_won) == 52:
                    events[player.name] = "shot_the_sun"
                else:
                    events[player.name] = "shot_the_moon"
                break

        final_scores: dict[str, int] = {}
        if shooter:
            for player in self.players:
                if player == shooter:
                    final_scores[player.name] = 0
                    player.score += 0
                else:
                    final_scores[player.name] = 26
                    player.score += 26
        else:
            for player in self.players:
                final_scores[player.name] = round_scores[player.name]
                player.score += round_scores[player.name]

        self.last_round_scores = dict(final_scores)
        self.last_round_events = events
        self.last_round_tricks = list(self.trick_history)
        return final_scores

    def is_game_over(self, target_score: int = 100) -> bool:
        """Check if the game is over.

        Args:
            target_score: Score at which game ends (default 100).

        Returns:
            True if any player has reached the target score.
        """
        return any(player.score >= target_score for player in self.players)

    def get_winner(self) -> HeartsPlayer:
        """Get the winner (player with lowest score).

        Returns:
            The winning player.
        """
        return min(self.players, key=lambda p: p.score)

    def get_valid_plays(self, player: HeartsPlayer) -> list[Card]:
        """Get all valid cards a player can play.

        Args:
            player: The player to check

        Returns:
            List of valid cards to play.
        """
        return [card for card in player.hand if self.is_valid_play(player, card)]

    def select_cards_to_pass(self, player: HeartsPlayer) -> list[Card]:
        """AI logic to select 3 cards to pass.

        Args:
            player: The player (AI) selecting cards

        Returns:
            List of 3 cards to pass.
        """
        suits: dict[Suit, list[Card]] = {}
        for card in player.hand:
            suits.setdefault(card.suit, []).append(card)

        for cards in suits.values():
            cards.sort(key=lambda c: c.value)

        selection: list[Card] = []

        # Always pass the queen of spades if possible
        if QUEEN_OF_SPADES in player.hand:
            selection.append(QUEEN_OF_SPADES)
            suits[Suit.SPADES].remove(QUEEN_OF_SPADES)

        # Pass other dangerous spades (Ace/King) when holding few spades
        spades = suits.get(Suit.SPADES, [])
        while spades and len(selection) < 3 and (len(spades) <= 2 or spades[-1].rank in {"A", "K"}):
            selection.append(spades.pop())

        # Try to void short suits (excluding hearts) by shedding highest cards
        non_heart_suits = [suit for suit in suits if suit not in {Suit.HEARTS, Suit.SPADES}]
        non_heart_suits.sort(key=lambda suit: (len(suits[suit]), -suits[suit][-1].value if suits[suit] else -1))
        for suit in non_heart_suits:
            while suits[suit] and len(selection) < 3 and len(suits[suit]) <= 3:
                selection.append(suits[suit].pop())

        # Shed high hearts if still needing cards
        hearts = suits.get(Suit.HEARTS, [])
        while hearts and len(selection) < 3:
            selection.append(hearts.pop())

        # Fallback: highest remaining cards regardless of suit
        if len(selection) < 3:
            remaining_cards = [card for pile in suits.values() for card in pile]
            remaining_cards.sort(key=lambda c: c.value, reverse=True)
            for card in remaining_cards:
                if card not in selection:
                    selection.append(card)
                    if len(selection) == 3:
                        break

        return selection[:3]

    def select_card_to_play(self, player: HeartsPlayer) -> Card:
        """AI logic to select a card to play.

        Args:
            player: The player (AI) selecting a card

        Returns:
            The card to play.
        """
        valid_cards = self.get_valid_plays(player)

        if not valid_cards:
            raise RuntimeError(f"{player.name} has no valid plays")

        # If only one valid card, play it
        if len(valid_cards) == 1:
            return valid_cards[0]

        # Leading a trick: favour safe, low cards from non-penalty suits
        if not self.current_trick:
            return self._select_lead_card(valid_cards)

        # Following a trick
        lead_suit_cards = [c for c in valid_cards if c.suit == self.lead_suit]

        if lead_suit_cards:
            highest_so_far = max(card.value for _, card in self.current_trick if card.suit == self.lead_suit)
            safe_cards = [c for c in lead_suit_cards if c.value < highest_so_far]
            if safe_cards:
                return max(safe_cards, key=lambda c: c.value)

            return min(lead_suit_cards, key=lambda c: c.value)

        # Discarding: dump penalties first, otherwise shed high cards
        penalty_cards = [c for c in valid_cards if self._is_penalty_card(c)]
        if penalty_cards:
            if QUEEN_OF_SPADES in penalty_cards:
                return QUEEN_OF_SPADES
            return max(penalty_cards, key=lambda c: c.value)

        return max(valid_cards, key=lambda c: (c.value, c.suit.value))

    @staticmethod
    def _select_lead_card(valid_cards: Iterable[Card]) -> Card:
        """Pick a low-risk lead from the available valid cards."""

        suit_buckets: dict[Suit, list[Card]] = {}
        for card in valid_cards:
            suit_buckets.setdefault(card.suit, []).append(card)

        for cards in suit_buckets.values():
            cards.sort(key=lambda c: c.value)

        def suit_priority(cards: list[Card]) -> tuple[int, int, int, int]:
            highest = cards[-1].value
            has_penalty = any(HeartsGame._is_penalty_card(c) for c in cards)
            has_queen = QUEEN_OF_SPADES in cards
            return (
                1 if has_penalty else 0,
                1 if has_queen else 0,
                highest,
                len(cards),
            )

        _, best_cards = min(suit_buckets.items(), key=lambda item: suit_priority(item[1]))
        return best_cards[0]
