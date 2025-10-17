"""Blackjack game engine and supporting data structures.

This module contains the core logic for a game of Blackjack, including the
rules for hands, player actions, and game progression. It is designed to be
reusable and adaptable for different interfaces, such as a command-line or
graphical user interface.

The main components are:
- ``Outcome``: An ``Enum`` representing the possible results of a hand.
- ``SideBetType``: An ``Enum`` for supported side bets like "21+3".
- ``TableRules``: A dataclass to configure table-specific rules.
- ``BlackjackHand``: A class that manages the cards in a hand, calculates totals,
  and checks for conditions like blackjack or bust.
- ``Shoe``: Represents a collection of multiple decks of cards, from which
  cards are drawn during the game, including card counting features.
- ``Player``: A dataclass for players, managing their bankroll and hands.
- ``BlackjackGame``: The main game engine that orchestrates the game flow,
  manages player and dealer actions, and resolves outcomes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Iterable, Optional

from card_games.common.cards import Card, Deck, Suit, format_cards


class Outcome(str, Enum):
    """Enumeration of the possible outcomes for a single blackjack hand.

    Each member represents a specific result from the player's perspective.
    - ``PLAYER_BLACKJACK``: Player wins with a natural 21.
    - ``PLAYER_WIN``: Player's hand beats the dealer's.
    - ``PUSH``: The hand is a tie.
    - ``PLAYER_LOSS``: Player's hand loses to the dealer's.
    - ``PLAYER_BUST``: Player's hand exceeds 21.
    - ``DEALER_BUST``: Dealer's hand exceeds 21, and player wins.
    - ``SURRENDER``: Player surrendered the hand.
    """

    PLAYER_BLACKJACK = "player_blackjack"
    PLAYER_WIN = "player_win"
    PUSH = "push"
    PLAYER_LOSS = "player_loss"
    PLAYER_BUST = "player_bust"
    DEALER_BUST = "dealer_bust"
    SURRENDER = "surrender"


class SideBetType(str, Enum):
    """Enumeration of available side bet types.

    - ``TWENTY_ONE_PLUS_THREE``: A bet on the poker hand formed by the player's
      first two cards and the dealer's up-card.
    - ``PERFECT_PAIRS``: A bet on whether the player's first two cards form a pair.
    """

    TWENTY_ONE_PLUS_THREE = "21+3"
    PERFECT_PAIRS = "perfect_pairs"


class TwentyOnePlusThreeOutcome(str, Enum):
    """Outcomes for the 21+3 side bet, with typical payout ratios."""

    SUITED_TRIPS = "suited_trips"  # 100:1
    STRAIGHT_FLUSH = "straight_flush"  # 40:1
    THREE_OF_A_KIND = "three_of_a_kind"  # 30:1
    STRAIGHT = "straight"  # 10:1
    FLUSH = "flush"  # 5:1
    LOSE = "lose"


class PerfectPairsOutcome(str, Enum):
    """Outcomes for the Perfect Pairs side bet, with typical payout ratios."""

    PERFECT_PAIR = "perfect_pair"  # Same rank and suit - 25:1
    COLORED_PAIR = "colored_pair"  # Same rank and color - 12:1
    MIXED_PAIR = "mixed_pair"  # Same rank, different color - 6:1
    LOSE = "lose"


@dataclass
class TableRules:
    """Configuration for blackjack table rules.

    This dataclass allows for easy customization of common blackjack rule
    variations, making the game engine adaptable to different casino styles.

    Attributes:
        blackjack_payout (float): Payout ratio for blackjack (e.g., 1.5 for 3:2).
        dealer_hits_soft_17 (bool): Whether the dealer hits on a soft 17.
        double_after_split (bool): Whether doubling down is allowed after splitting.
        resplit_aces (bool): Whether Aces can be re-split.
        max_splits (int): Maximum number of times a hand can be split.
        surrender_allowed (bool): Whether late surrender is allowed.
        insurance_allowed (bool): Whether insurance is offered against a dealer's Ace.
    """

    blackjack_payout: float = 1.5  # 3:2 payout
    dealer_hits_soft_17: bool = False
    double_after_split: bool = True
    resplit_aces: bool = False
    max_splits: int = 3
    surrender_allowed: bool = True
    insurance_allowed: bool = True


# Predefined table rule configurations for easy setup.
TABLE_CONFIGS = {
    "Standard": TableRules(
        blackjack_payout=1.5,
        dealer_hits_soft_17=False,
        double_after_split=True,
        resplit_aces=False,
        max_splits=3,
        surrender_allowed=True,
        insurance_allowed=True,
    ),
    "Liberal": TableRules(
        blackjack_payout=1.5,
        dealer_hits_soft_17=False,
        double_after_split=True,
        resplit_aces=True,
        max_splits=4,
        surrender_allowed=True,
        insurance_allowed=True,
    ),
    "Conservative": TableRules(
        blackjack_payout=1.2,  # 6:5 payout
        dealer_hits_soft_17=True,
        double_after_split=False,
        resplit_aces=False,
        max_splits=2,
        surrender_allowed=False,
        insurance_allowed=True,
    ),
}


@dataclass
class SideBet:
    """Represents a side bet placed on a hand.

    Attributes:
        bet_type (SideBetType): The type of side bet (e.g., Perfect Pairs).
        amount (int): The wagered amount.
        outcome (Optional[str]): The result of the side bet after resolution.
        payout (int): The amount won from the bet.
    """

    bet_type: SideBetType
    amount: int
    outcome: Optional[str] = None
    payout: int = 0


@dataclass
class BlackjackHand:
    """A blackjack hand belonging to either the dealer or a player.

    This class manages the cards in a hand, calculates possible totals (especially
    with Aces), and tracks the hand's state, such as whether it has been stood,
    doubled, or split.

    Attributes:
        cards (list[Card]): The cards currently in the hand.
        bet (int): The wager placed on this hand.
        stood (bool): True if the player has chosen to "stand".
        doubled (bool): True if the hand has been "doubled down".
        split_from (Optional[Card]): The card from which this hand was split.
        surrendered (bool): True if the player has surrendered this hand.
        side_bets (list[SideBet]): A list of side bets placed on this hand.
    """

    cards: list[Card] = field(default_factory=list)
    bet: int = 0
    stood: bool = False
    doubled: bool = False
    split_from: Optional[Card] = None
    surrendered: bool = False
    side_bets: list[SideBet] = field(default_factory=list)

    def add_card(self, card: Card) -> None:
        """Add a card to the hand."""
        self.cards.append(card)

    def totals(self) -> list[int]:
        """Return all possible totals for the hand, accounting for Aces.

        Aces can be valued at 1 or 11. This method calculates all valid totals,
        with and without busting, and returns them in descending order.

        For example, a hand with an Ace and a 5 can be 6 or 16.
        A hand with two Aces and a 5 can be 7 or 17.

        Returns:
            A sorted list of possible hand totals, with the best (highest without
            busting) first. If all totals are over 21, it returns the lowest
            bust total.
        """
        num_aces = sum(1 for card in self.cards if card.rank == "A")
        base_total = sum(self._card_value(card) for card in self.cards)

        totals = {base_total}
        # Each Ace can be 1 or 11. The base total initially assumes 11.
        # Subtract 10 for each Ace to get the alternative values.
        for _ in range(num_aces):
            base_total -= 10
            totals.add(base_total)

        valid_totals = sorted([t for t in totals if t <= 21], reverse=True)
        if valid_totals:
            return valid_totals

        # If all possible totals are a bust, return the smallest bust total.
        return [min(totals)]

    def best_total(self) -> int:
        """Return the best (highest non-busting) total for the hand."""
        return self.totals()[0]

    def is_blackjack(self) -> bool:
        """Check if the hand is a natural blackjack (2 cards totaling 21)."""
        return self.split_from is None and len(self.cards) == 2 and self.best_total() == 21

    def is_bust(self) -> bool:
        """Check if the hand's best total is over 21."""
        return self.best_total() > 21

    def is_soft(self) -> bool:
        """Check if the hand is "soft" (an Ace is counted as 11).

        A soft hand has multiple possible totals, meaning it contains an Ace
        that can be either 1 or 11 without busting.
        """
        totals = self.totals()
        return len(totals) > 1 and totals[0] <= 21

    def can_double(self, balance: int) -> bool:
        """Check if the hand can be doubled down.

        A player can double down on their initial two cards if they have
        sufficient balance to match their original bet.
        """
        return not self.doubled and not self.stood and len(self.cards) == 2 and balance >= self.bet

    def can_split(self, balance: int) -> bool:
        """Check if the hand can be split.

        A player can split a hand if it consists of two cards of the same rank
        and they have enough balance to place an equal bet on the new hand.
        """
        return len(self.cards) == 2 and self.cards[0].rank == self.cards[1].rank and balance >= self.bet

    def split(self) -> BlackjackHand:
        """Split the hand into two, returning the new hand.

        This method modifies the current hand by removing one card and creates
        a new hand with that card. Both hands are marked as having been split.

        Returns:
            The new hand created from the split.

        Raises:
            ValueError: If the hand is not splittable.
        """
        if not self.can_split(balance=self.bet):
            raise ValueError("Hand cannot be split")

        card_to_move = self.cards.pop()
        new_hand = BlackjackHand(cards=[card_to_move], bet=self.bet, split_from=card_to_move)
        self.split_from = self.cards[0]
        return new_hand

    def describe(self) -> str:
        """Return a string description of the hand, including cards and total."""
        return f"{format_cards(self.cards)} ({self.best_total()})"

    def can_surrender(self) -> bool:
        """Check if the hand can be surrendered.

        A player can surrender on their initial two cards before taking any other action.
        """
        return not self.surrendered and not self.stood and not self.doubled and len(self.cards) == 2

    @staticmethod
    def _card_value(card: Card) -> int:
        """Calculate the blackjack value of a single card.

        Face cards (J, Q, K, T) are 10. Aces are 11. Other cards are their
        face value.
        """
        if card.rank in {"J", "Q", "K", "T"}:
            return 10
        if card.rank == "A":
            return 11
        return int(card.rank)


class Shoe:
    """A blackjack shoe comprised of one or more standard decks.

    A shoe is a container for multiple decks of cards, used in casino games to
    reduce the frequency of shuffling. This implementation automatically
    reshuffles when the number of remaining cards falls below a threshold and
    includes basic Hi-Lo card counting.

    Attributes:
        decks (int): The number of decks in the shoe.
        cards (list[Card]): The list of cards currently in the shoe.
        running_count (int): The Hi-Lo running count for card counting.
        cards_dealt_since_shuffle (int): Cards dealt since the last shuffle.
    """

    def __init__(self, decks: int = 6, *, rng=None) -> None:
        """Initialize the shoe with a specified number of decks."""
        if decks <= 0:
            raise ValueError("Number of decks must be positive")
        self.decks = decks
        self._rng = rng
        self.cards: list[Card] = []
        self.running_count = 0
        self.cards_dealt_since_shuffle = 0
        self._reshuffle()

    def _reshuffle(self) -> None:
        """Reshuffle the shoe with a full set of cards and reset counts."""
        self.cards = []
        for _ in range(self.decks):
            self.cards.extend(Deck().cards)

        # Use the provided RNG for shuffling, or the default `random` module.
        if self._rng is None:
            import random

            random.shuffle(self.cards)
        else:
            self._rng.shuffle(self.cards)

        # Reset card counting metrics.
        self.running_count = 0
        self.cards_dealt_since_shuffle = 0

    def draw(self) -> Card:
        """Draw a single card from the shoe.

        If the number of cards is below the reshuffle threshold (typically 25%
        of the total), the shoe is reshuffled before drawing.
        """
        # Reshuffle if the shoe penetration is too high.
        if len(self.cards) < max(20, self.decks * 52 // 4):
            self._reshuffle()

        if not self.cards:
            raise RuntimeError("The shoe is empty and cannot be drawn from.")

        card = self.cards.pop()
        self.cards_dealt_since_shuffle += 1

        # Update Hi-Lo running count based on the card's value.
        if card.rank in {"2", "3", "4", "5", "6"}:
            self.running_count += 1
        elif card.rank in {"T", "J", "Q", "K", "A"}:
            self.running_count -= 1
        # Cards 7, 8, 9 are neutral and do not change the count.

        return card

    def true_count(self) -> float:
        """Calculate the true count (running count divided by decks remaining).

        The true count provides a more accurate measure of the shoe's richness
        in high cards.

        Returns:
            The true count, or 0.0 if no cards have been dealt.
        """
        if self.cards_dealt_since_shuffle == 0:
            return 0.0
        decks_remaining = len(self.cards) / 52
        if decks_remaining <= 0:
            return 0.0
        return self.running_count / decks_remaining

    def penetration(self) -> float:
        """Calculate shoe penetration as a percentage.

        Returns:
            The percentage of cards dealt from the shoe (0-100).
        """
        total_cards = self.decks * 52
        if total_cards == 0:
            return 0.0
        return (self.cards_dealt_since_shuffle / total_cards) * 100


def evaluate_twenty_one_plus_three(player_cards: list[Card], dealer_up_card: Card) -> tuple[TwentyOnePlusThreeOutcome, int]:
    """Evaluate the 21+3 side bet outcome.

    This function forms a three-card poker hand from the player's first two
    cards and the dealer's up-card and determines its payout.

    Args:
        player_cards: The player's first two cards.
        dealer_up_card: The dealer's up-card.

    Returns:
        A tuple containing the outcome and the payout multiplier.
    """
    if len(player_cards) < 2:
        return TwentyOnePlusThreeOutcome.LOSE, 0

    cards = [player_cards[0], player_cards[1], dealer_up_card]
    ranks = [c.rank for c in cards]
    suits = [c.suit for c in cards]

    # Convert ranks to numeric values for easier comparison.
    rank_values = []
    for rank in ranks:
        if rank == "A":
            rank_values.append(14)
        elif rank == "K":
            rank_values.append(13)
        elif rank == "Q":
            rank_values.append(12)
        elif rank == "J":
            rank_values.append(11)
        elif rank == "T":
            rank_values.append(10)
        else:
            rank_values.append(int(rank))

    sorted_values = sorted(rank_values)

    # Check for suited trips (all same rank and suit).
    if ranks[0] == ranks[1] == ranks[2] and suits[0] == suits[1] == suits[2]:
        return TwentyOnePlusThreeOutcome.SUITED_TRIPS, 100

    # Check for straight flush.
    is_flush = suits[0] == suits[1] == suits[2]
    is_straight = (sorted_values[2] - sorted_values[1] == 1 and sorted_values[1] - sorted_values[0] == 1) or (
        sorted_values == [2, 3, 14]
    )  # Special case for A-2-3 straight.

    if is_straight and is_flush:
        return TwentyOnePlusThreeOutcome.STRAIGHT_FLUSH, 40

    # Check for three of a kind.
    if ranks[0] == ranks[1] == ranks[2]:
        return TwentyOnePlusThreeOutcome.THREE_OF_A_KIND, 30

    # Check for straight.
    if is_straight:
        return TwentyOnePlusThreeOutcome.STRAIGHT, 10

    # Check for flush.
    if is_flush:
        return TwentyOnePlusThreeOutcome.FLUSH, 5

    return TwentyOnePlusThreeOutcome.LOSE, 0


def evaluate_perfect_pairs(
    player_cards: list[Card],
) -> tuple[PerfectPairsOutcome, int]:
    """Evaluate the Perfect Pairs side bet outcome.

    This function checks if the player's first two cards form a pair and
    determines the payout based on its type (perfect, colored, or mixed).

    Args:
        player_cards: The player's first two cards.

    Returns:
        A tuple containing the outcome and the payout multiplier.
    """
    if len(player_cards) < 2:
        return PerfectPairsOutcome.LOSE, 0

    card1, card2 = player_cards[0], player_cards[1]

    # Not a pair.
    if card1.rank != card2.rank:
        return PerfectPairsOutcome.LOSE, 0

    # Perfect pair: same rank and suit.
    if card1.suit == card2.suit:
        return PerfectPairsOutcome.PERFECT_PAIR, 25

    # Colored pair: same rank and color (both red or both black).
    red_suits = {Suit.HEARTS, Suit.DIAMONDS}
    black_suits = {Suit.CLUBS, Suit.SPADES}

    if (card1.suit in red_suits and card2.suit in red_suits) or (card1.suit in black_suits and card2.suit in black_suits):
        return PerfectPairsOutcome.COLORED_PAIR, 12

    # Mixed pair: same rank, different color.
    return PerfectPairsOutcome.MIXED_PAIR, 6


@dataclass(unsafe_hash=True)
class Player:
    """A blackjack player with a bankroll and a set of hands.

    Attributes:
        name (str): The player's name.
        bankroll (int): The player's current money balance.
        hands (list[BlackjackHand]): The list of hands the player is currently playing.
    """

    name: str
    bankroll: int = field(compare=False)
    hands: list[BlackjackHand] = field(default_factory=list, compare=False, hash=False)

    def active_hands(self) -> Iterable[BlackjackHand]:
        """Return an iterator over the player's hands that are still in play."""
        return (hand for hand in self.hands if not hand.stood and not hand.is_bust())


class BlackjackGame:
    """Manages a game of blackjack for multiple players against the dealer.

    This class orchestrates the entire game flow, from starting a round and
    placing bets to handling player actions (hit, stand, double, split) and
    resolving the outcomes. It supports multiple players, configurable table
    rules, and educational features like card counting hints.

    Attributes:
        min_bet (int): The minimum allowed bet.
        max_bet (int): The maximum allowed bet.
        players (list[Player]): The list of players at the table.
        dealer (Player): The dealer.
        shoe (Shoe): The shoe of cards for the game.
        history (list): A log of outcomes from previous hands.
        educational_mode (bool): If True, shows card counting hints.
        table_rules (TableRules): The rules for this table.
    """

    def __init__(
        self,
        *,
        bankroll: int = 500,
        min_bet: int = 10,
        max_bet: int = 1000,
        decks: int = 6,
        rng=None,
        educational_mode: bool = False,
        table_rules: Optional[TableRules] = None,
        num_players: int = 1,
    ) -> None:
        """Initialize the Blackjack game engine."""
        if bankroll <= 0:
            raise ValueError("bankroll must be positive")
        if min_bet <= 0:
            raise ValueError("min_bet must be positive")
        if max_bet < min_bet:
            raise ValueError("max_bet must be >= min_bet")
        if min_bet > bankroll:
            raise ValueError("bankroll must cover at least one min bet")
        if not (1 <= num_players <= 7):
            raise ValueError("num_players must be between 1 and 7")

        self.min_bet = min_bet
        self.max_bet = max_bet
        self.table_rules = table_rules or TableRules()

        # Create players for the game.
        self.players = []
        if num_players == 1:
            self.players.append(Player("You", bankroll))
        else:
            for i in range(num_players):
                name = f"Player {i + 1}" if i > 0 else "You"
                self.players.append(Player(name, bankroll))

        self.dealer = Player("Dealer", bankroll=0)  # Dealer has an infinite bankroll.
        self.shoe = Shoe(decks, rng=rng)
        self.history: list[tuple[Outcome, BlackjackHand, BlackjackHand]] = []
        self.educational_mode = educational_mode

    # Backward compatibility property for single-player mode.
    @property
    def player(self) -> Player:
        """Return the first player for backward compatibility."""
        return self.players[0]

    def can_continue(self) -> bool:
        """Check if the primary player has enough money to continue playing."""
        return self.player.bankroll >= self.min_bet

    def start_round(
        self,
        bet: int,
        side_bets: Optional[dict[SideBetType, int]] = None,
    ) -> None:
        """Start a new round of blackjack for a single player (backward compatible).

        Args:
            bet: The amount the player wishes to bet.
            side_bets: A dictionary of side bet types to wagered amounts.
        """
        bets = {self.player: bet}
        player_side_bets = {self.player: side_bets} if side_bets else {}
        self.start_multiplayer_round(bets, player_side_bets)

    def start_multiplayer_round(
        self,
        bets: dict[Player, int],
        side_bets: Optional[dict[Player, dict[SideBetType, int]]] = None,
    ) -> None:
        """Start a new round of blackjack for multiple players.

        This method validates bets, creates hands, deals cards, and resolves
        initial side bets.

        Args:
            bets: A dictionary mapping each player to their bet amount.
            side_bets: A dictionary mapping players to their side bets.
        """
        side_bets = side_bets or {}

        # Clear all hands from the previous round.
        for player in self.players:
            player.hands.clear()
        self.dealer.hands.clear()

        dealer_hand = BlackjackHand()
        self.dealer.hands = [dealer_hand]

        # Validate bets and create hands for each player.
        for player in self.players:
            if player not in bets:
                continue  # Player is sitting out this round.

            bet = bets[player]
            if bet < self.min_bet:
                raise ValueError(f"Bet for {player.name} must be at least {self.min_bet}")
            if bet > self.max_bet:
                raise ValueError(f"Bet for {player.name} cannot exceed {self.max_bet}")
            if bet > player.bankroll:
                raise ValueError(f"Insufficient bankroll for {player.name}")

            # Validate and create side bets.
            player_side_bets = side_bets.get(player, {})
            total_side_bet = 0
            side_bet_objects = []

            if player_side_bets:
                for bet_type, amount in player_side_bets.items():
                    if amount < 0:
                        raise ValueError("Side bet amount must be non-negative")
                    if amount > 0:
                        total_side_bet += amount
                        side_bet_objects.append(SideBet(bet_type=bet_type, amount=amount))

            if bet + total_side_bet > player.bankroll:
                raise ValueError(f"Insufficient bankroll for {player.name} bet and side bets")

            # Deduct bet and create hand.
            player.bankroll -= bet + total_side_bet
            player_hand = BlackjackHand(bet=bet, side_bets=side_bet_objects)
            player.hands = [player_hand]

        # Deal cards in casino order: one to each player, one to dealer,
        # then a second card to each player and the dealer's hole card.
        for _ in range(2):
            for player in self.players:
                if player.hands:  # Only deal to players in this round.
                    player.hands[0].add_card(self.shoe.draw())
            dealer_hand.add_card(self.shoe.draw())

        # Evaluate side bets for all players now that initial cards are dealt.
        for player in self.players:
            if player.hands:
                self._resolve_side_bets(player.hands[0])

    @property
    def dealer_hand(self) -> BlackjackHand:
        """A convenience property to access the dealer's single hand."""
        return self.dealer.hands[0]

    def player_actions(self, hand: BlackjackHand, player: Optional[Player] = None) -> list[str]:
        """Return a list of valid actions for the player's current hand.

        Args:
            hand: The hand to check actions for.
            player: The player who owns the hand. If None, uses the first player.
        """
        if player is None:
            player = self.player

        actions = ["hit", "stand"]
        if hand.can_double(player.bankroll):
            actions.append("double")
        if hand.can_split(player.bankroll):
            actions.append("split")
        if hand.can_surrender() and self.table_rules.surrender_allowed:
            actions.append("surrender")
        return actions

    def hit(self, hand: BlackjackHand) -> Card:
        """Add a card to the specified hand (player's or dealer's)."""
        card = self.shoe.draw()
        hand.add_card(card)
        return card

    def stand(self, hand: BlackjackHand) -> None:
        """Mark the player's hand as "stood" (no more cards)."""
        hand.stood = True

    def double_down(self, hand: BlackjackHand, player: Optional[Player] = None) -> Card:
        """Double a player's bet, deal one more card, and stand.

        Args:
            hand: The hand to double down.
            player: The player who owns the hand. If None, uses the first player.
        """
        if player is None:
            player = self.player

        if not hand.can_double(player.bankroll):
            raise ValueError("Cannot double this hand")

        player.bankroll -= hand.bet
        hand.bet *= 2
        hand.doubled = True

        # Doubling down ends the turn after a single forced hit.
        card = self.hit(hand)
        hand.stood = True
        return card

    def split(self, hand: BlackjackHand, player: Optional[Player] = None) -> BlackjackHand:
        """Split a player's hand into two separate hands.

        Args:
            hand: The hand to split.
            player: The player who owns the hand. If None, uses the first player.
        """
        if player is None:
            player = self.player

        if not hand.can_split(player.bankroll):
            raise ValueError("Cannot split this hand")

        player.bankroll -= hand.bet
        new_hand = hand.split()

        # Insert the new hand immediately after the original.
        index = player.hands.index(hand)
        player.hands.insert(index + 1, new_hand)

        # Add one card to each of the newly split hands.
        for split_hand in (hand, new_hand):
            split_hand.add_card(self.shoe.draw())

        return new_hand

    def surrender(self, hand: BlackjackHand, player: Optional[Player] = None) -> None:
        """Surrender the hand and get half the bet back.

        Args:
            hand: The hand to surrender.
            player: The player who owns the hand. If None, uses the first player.
        """
        if not self.table_rules.surrender_allowed:
            raise ValueError("Surrender is not allowed at this table")

        if not hand.can_surrender():
            raise ValueError("Cannot surrender this hand")

        if player is None:
            player = self.player

        hand.surrendered = True
        hand.stood = True
        # Return half the bet to the player.
        player.bankroll += hand.bet // 2

    def dealer_play(self) -> None:
        """Perform the dealer's turn according to table rules.

        The dealer must hit on 16 or less. Behavior on soft 17 depends on
        the configured table rules.
        """
        hand = self.dealer_hand
        hand.stood = False
        while hand.best_total() < 17:
            self.hit(hand)

        # Check if the dealer should hit a soft 17 based on table rules.
        if self.table_rules.dealer_hits_soft_17 and hand.best_total() == 17 and hand.is_soft():
            while hand.best_total() < 17 or (hand.best_total() == 17 and hand.is_soft()):
                self.hit(hand)

        hand.stood = True

    def _resolve_side_bets(self, hand: BlackjackHand, player: Optional[Player] = None) -> None:
        """Resolve side bets for a hand.

        Args:
            hand: The hand with side bets to resolve.
            player: The player who owns the hand. If None, the owner is found.
        """
        if not hand.side_bets:
            return

        # Find the player who owns the hand if not provided.
        if player is None:
            for p in self.players:
                if hand in p.hands:
                    player = p
                    break
            if player is None:
                return  # Should not happen in a valid game state.

        dealer_up_card = self.dealer_hand.cards[0] if self.dealer_hand.cards else None

        for side_bet in hand.side_bets:
            if side_bet.bet_type == SideBetType.TWENTY_ONE_PLUS_THREE:
                if dealer_up_card:
                    outcome, multiplier = evaluate_twenty_one_plus_three(hand.cards, dealer_up_card)
                    side_bet.outcome = outcome.value
                    side_bet.payout = side_bet.amount * multiplier
                    if multiplier > 0:
                        # Payout includes original bet plus winnings.
                        player.bankroll += side_bet.amount + side_bet.payout
            elif side_bet.bet_type == SideBetType.PERFECT_PAIRS:
                outcome, multiplier = evaluate_perfect_pairs(hand.cards)
                side_bet.outcome = outcome.value
                side_bet.payout = side_bet.amount * multiplier
                if multiplier > 0:
                    player.bankroll += side_bet.amount + side_bet.payout

    def resolve(self, hand: BlackjackHand) -> Outcome:
        """Resolve a single player hand against the dealer's hand.

        This method determines the outcome (win, loss, push) and adjusts the
        player's bankroll accordingly.

        Args:
            hand: The player's hand to be resolved.

        Returns:
            The outcome of the hand.
        """
        # Check if the hand was surrendered first.
        if hand.surrendered:
            outcome = Outcome.SURRENDER
            self.history.append((outcome, hand, self.dealer_hand))
            return outcome

        dealer_total = self.dealer_hand.best_total()
        player_total = hand.best_total()

        if hand.is_blackjack() and not self.dealer_hand.is_blackjack():
            # Blackjack pays according to table rules.
            payout = int(hand.bet * self.table_rules.blackjack_payout)
            for p in self.players:
                if hand in p.hands:
                    p.bankroll += hand.bet + payout
                    break
            outcome = Outcome.PLAYER_BLACKJACK
        elif hand.is_bust():
            outcome = Outcome.PLAYER_BUST
        elif self.dealer_hand.is_bust():
            for p in self.players:
                if hand in p.hands:
                    p.bankroll += hand.bet * 2
                    break
            outcome = Outcome.DEALER_BUST
        elif self.dealer_hand.is_blackjack() and not hand.is_blackjack():
            outcome = Outcome.PLAYER_LOSS
        elif player_total > dealer_total:
            for p in self.players:
                if hand in p.hands:
                    p.bankroll += hand.bet * 2
                    break
            outcome = Outcome.PLAYER_WIN
        elif player_total == dealer_total:
            # Push: return the original bet to the player.
            for p in self.players:
                if hand in p.hands:
                    p.bankroll += hand.bet
                    break
            outcome = Outcome.PUSH
        else:  # player_total < dealer_total
            outcome = Outcome.PLAYER_LOSS

        self.history.append((outcome, hand, self.dealer_hand))
        return outcome

    def settle_round(self) -> dict[Player, list[Outcome]]:
        """Settle all hands for all players at the end of a round.

        Returns:
            A map of players to their list of hand outcomes for the round.
        """
        results = {}
        for player in self.players:
            outcomes = [self.resolve(hand) for hand in player.hands]
            if outcomes:
                results[player] = outcomes
        return results

    def reset(self) -> None:
        """Clear all players' and the dealer's hands for the next round."""
        for player in self.players:
            player.hands.clear()
        self.dealer.hands.clear()

    def add_player(self, name: str, bankroll: int) -> Player:
        """Add a new player to the table.

        Args:
            name: The player's name.
            bankroll: The player's starting bankroll.

        Returns:
            The newly added player instance.

        Raises:
            ValueError: If the table is full (maximum of 7 players).
        """
        if len(self.players) >= 7:
            raise ValueError("Table is full (maximum 7 players)")

        player = Player(name, bankroll)
        self.players.append(player)
        return player

    def remove_player(self, player: Player) -> None:
        """Remove a player from the table.

        Args:
            player: The player instance to remove.
        """
        if player in self.players:
            self.players.remove(player)

    def format_hand(self, hand: BlackjackHand) -> str:
        """Return a formatted string representation of a hand."""
        return hand.describe()

    def get_counting_hint(self, hand: BlackjackHand) -> str:
        """Get a card counting hint for the current hand.

        This function provides educational hints based on the true count and
        basic strategy deviations if educational mode is enabled.

        Args:
            hand: The player's hand.

        Returns:
            A hint string, or an empty string if educational mode is off.
        """
        if not self.educational_mode:
            return ""

        true_count = self.shoe.true_count()
        dealer_up_card = self.dealer_hand.cards[0] if self.dealer_hand.cards else None
        player_total = hand.best_total()

        hints = [
            f"Running Count: {self.shoe.running_count}",
            f"True Count: {true_count:.1f}",
        ]

        # Basic betting advice based on the true count.
        if true_count >= 2:
            hints.append("Count is favorable - consider increasing bet")
        elif true_count <= -2:
            hints.append("Count is unfavorable - consider minimum bet")
        else:
            hints.append("Count is neutral")

        # Basic strategy deviation hints.
        if dealer_up_card and len(hand.cards) == 2:
            dealer_value = BlackjackHand._card_value(dealer_up_card)

            # Insurance hint.
            if dealer_up_card.rank == "A" and true_count >= 3:
                hints.append("Consider insurance (high count)")

            # Hit/Stand hints for common deviation plays.
            if player_total == 16 and dealer_value == 10:
                hint = "Deviation: Stand on 16 vs 10 (positive count)" if true_count >= 0 else "Basic: Hit on 16 vs 10"
                hints.append(hint)
            elif player_total == 12 and dealer_value in {2, 3}:
                hint = "Deviation: Stand on 12 vs 2/3 (high count)" if true_count >= 3 else "Basic: Hit on 12 vs 2/3"
                hints.append(hint)

        return " | ".join(hints)


__all__ = [
    "BlackjackGame",
    "BlackjackHand",
    "Outcome",
    "SideBet",
    "SideBetType",
    "TwentyOnePlusThreeOutcome",
    "PerfectPairsOutcome",
    "TableRules",
    "TABLE_CONFIGS",
    "Player",
]
