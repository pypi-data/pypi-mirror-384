"""Engine, bot AI, and CLI utilities for a Texas Hold'em poker experience.

The module mirrors the structure of a real-world poker room and documents the
reasoning for each rule directly beside the implementation. By reading the
docstrings and comments, newcomers can follow the flow from high-level match
management down to the evaluation of individual five-card hands.

Key components:

* :class:`ActionType` and :class:`Action` encode the discrete decisions players
  can make during a betting round.
* :class:`Player` stores the mutable state of a participant, including their
  chip stack, hole cards, and recent betting history.
* :class:`BotSkill` and :class:`PokerBot` parameterise the behaviour of computer
  opponents, explaining how aggression, bluff frequency, and mistake rate
  influence their choices.
* :class:`PokerTable` models a single hand, coordinating blinds, betting rounds,
  and pot distribution with extensive inline commentary for each stage.
* :class:`PokerMatch` strings multiple hands together to form a short match that
  pits the user against three bot opponents.
* :func:`estimate_win_rate` demonstrates how Monte Carlo simulation can be used
  to approximate pre-flop equity.

Together with :mod:`card_games.poker.gui`, these components provide both a
playable experience and richly annotated sample code for anyone studying the
mechanics of poker software.
"""

from __future__ import annotations

import argparse
import itertools
import json
import random
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Iterable, Sequence

from ..common.cards import Card, Deck, format_cards
from .poker_core import HandRank, best_hand


class GameVariant(str, Enum):
    """Enumeration of poker game variants."""

    TEXAS_HOLDEM = "texas-holdem"
    OMAHA = "omaha"


class BettingLimit(str, Enum):
    """Enumeration of betting limit structures."""

    NO_LIMIT = "no-limit"
    POT_LIMIT = "pot-limit"
    FIXED_LIMIT = "fixed-limit"


class ActionType(str, Enum):
    """Enumeration of the types of actions a player can take during a betting round."""

    FOLD = "fold"
    CHECK = "check"
    CALL = "call"
    BET = "bet"
    RAISE = "raise"
    ALL_IN = "all-in"


@dataclass(frozen=True)
class Action:
    """Represents a single betting decision made by a player.

    Attributes:
        kind (ActionType): The type of action taken.
        target_bet (int): The total amount the player is betting or raising to.
    """

    kind: ActionType
    target_bet: int = 0


@dataclass
class PlayerStatistics:
    """Tracks performance statistics for a player across multiple hands.

    Attributes:
        hands_played (int): Total number of hands the player participated in.
        hands_won (int): Number of hands won.
        hands_folded (int): Number of times the player folded.
        total_wagered (int): Total chips wagered across all hands.
        total_winnings (int): Total chips won across all hands.
        showdowns_reached (int): Number of times player reached showdown.
        showdowns_won (int): Number of showdowns won.
    """

    hands_played: int = 0
    hands_won: int = 0
    hands_folded: int = 0
    total_wagered: int = 0
    total_winnings: int = 0
    showdowns_reached: int = 0
    showdowns_won: int = 0

    @property
    def fold_frequency(self) -> float:
        """Returns the percentage of hands folded."""
        return self.hands_folded / max(self.hands_played, 1) * 100

    @property
    def win_rate(self) -> float:
        """Returns the percentage of hands won."""
        return self.hands_won / max(self.hands_played, 1) * 100

    @property
    def net_profit(self) -> int:
        """Returns the net profit/loss."""
        return self.total_winnings - self.total_wagered

    def to_dict(self) -> dict:
        """Converts statistics to a dictionary."""
        return {
            "hands_played": self.hands_played,
            "hands_won": self.hands_won,
            "hands_folded": self.hands_folded,
            "total_wagered": self.total_wagered,
            "total_winnings": self.total_winnings,
            "showdowns_reached": self.showdowns_reached,
            "showdowns_won": self.showdowns_won,
            "fold_frequency": round(self.fold_frequency, 2),
            "win_rate": round(self.win_rate, 2),
            "net_profit": self.net_profit,
        }


@dataclass
class Player:
    """Represents a single player at the poker table.

    This class stores all state related to a player, including their name, chip stack,
    hole cards, and their status within the current hand (e.g., folded, all-in).
    """

    name: str
    chips: int = 1_000
    is_user: bool = False
    hole_cards: list[Card] = field(default_factory=list)
    folded: bool = False
    all_in: bool = False
    current_bet: int = 0
    total_invested: int = 0
    last_action: str = "waiting"
    last_wager: int = 0
    statistics: PlayerStatistics = field(default_factory=PlayerStatistics)

    def reset_for_hand(self) -> None:
        """Resets the player's state for the start of a new hand."""
        self.hole_cards.clear()
        self.folded = False
        self.all_in = False
        self.current_bet = 0
        self.total_invested = 0
        self.last_action = "waiting"
        self.last_wager = 0

    def receive_cards(self, cards: Iterable[Card]) -> None:
        """Adds cards to the player's hand."""
        self.hole_cards.extend(cards)

    def __str__(self) -> str:  # pragma: no cover - debug helper
        return f"{self.name} ({self.chips} chips)"


@dataclass(frozen=True)
class BotSkill:
    """Defines the personality and skill level of a poker bot.

    These parameters control the bot's decision-making process, such as how
    often it bluffs, how aggressively it bets, and how accurately it assesses
    its hand strength.
    """

    name: str
    tightness: float  # How selective the bot is with starting hands.
    aggression: float  # How often the bot bets or raises with strong hands.
    bluff: float  # How often the bot bluffs.
    mistake_rate: float  # The probability of making a random, unoptimal move.
    simulations: int  # The number of Monte Carlo simulations to run for equity estimation.


@dataclass
class TournamentMode:
    """Defines the blind structure for tournament play.

    Attributes:
        enabled (bool): Whether tournament mode is active.
        blind_schedule (list[tuple[int, int]]): List of (small_blind, big_blind) pairs.
        hands_per_level (int): Number of hands before blinds increase.
    """

    enabled: bool = False
    blind_schedule: list[tuple[int, int]] = field(default_factory=lambda: [(10, 20), (15, 30), (25, 50), (50, 100), (100, 200)])
    hands_per_level: int = 5
    current_level: int = 0

    def get_blinds(self, hand_number: int) -> tuple[int, int]:
        """Returns the current blind values based on hand number."""
        if not self.enabled:
            return self.blind_schedule[0]
        level = min(hand_number // self.hands_per_level, len(self.blind_schedule) - 1)
        self.current_level = level
        return self.blind_schedule[level]


@dataclass
class HandHistory:
    """Records the complete history of a single hand for later review.

    Attributes:
        hand_number (int): The sequential hand number.
        timestamp (str): When the hand was played.
        game_variant (str): The poker variant played.
        small_blind (int): Small blind amount.
        big_blind (int): Big blind amount.
        players (dict): Player names and starting chip counts.
        hole_cards (dict): Hole cards dealt to each player.
        community_cards (list[Card]): The community cards.
        actions (list[str]): All actions taken during the hand.
        showdown (list[tuple[str, str]]): Player names and hand descriptions at showdown.
        payouts (dict[str, int]): Chips won by each player.
    """

    hand_number: int
    timestamp: str
    game_variant: str
    small_blind: int
    big_blind: int
    players: dict[str, int]
    hole_cards: dict[str, list[str]]
    community_cards: list[str]
    actions: list[str]
    showdown: list[tuple[str, str]]
    payouts: dict[str, int]

    def to_dict(self) -> dict:
        """Converts the hand history to a dictionary for JSON serialization."""
        return {
            "hand_number": self.hand_number,
            "timestamp": self.timestamp,
            "game_variant": self.game_variant,
            "small_blind": self.small_blind,
            "big_blind": self.big_blind,
            "players": self.players,
            "hole_cards": self.hole_cards,
            "community_cards": self.community_cards,
            "actions": self.actions,
            "showdown": self.showdown,
            "payouts": self.payouts,
        }


# A pre-shuffled, full deck of cards for use in simulations.
FULL_DECK: tuple[Card, ...] = tuple(Deck().cards)


def fresh_deck(rng: random.Random | None = None) -> Deck:
    """Creates and shuffles a new deck of cards."""
    deck = Deck()
    deck.shuffle(rng=rng)
    return deck


# Pre-defined difficulty levels for the poker bots.
DIFFICULTIES: dict[str, BotSkill] = {
    "Noob": BotSkill(
        "Noob",
        tightness=0.32,
        aggression=0.10,
        bluff=0.30,
        mistake_rate=0.25,
        simulations=80,
    ),
    "Easy": BotSkill(
        "Easy",
        tightness=0.37,
        aggression=0.16,
        bluff=0.26,
        mistake_rate=0.18,
        simulations=120,
    ),
    "Medium": BotSkill(
        "Medium",
        tightness=0.43,
        aggression=0.22,
        bluff=0.22,
        mistake_rate=0.12,
        simulations=160,
    ),
    "Hard": BotSkill(
        "Hard",
        tightness=0.48,
        aggression=0.3,
        bluff=0.18,
        mistake_rate=0.07,
        simulations=220,
    ),
    "Insane": BotSkill(
        "Insane",
        tightness=0.54,
        aggression=0.42,
        bluff=0.14,
        mistake_rate=0.03,
        simulations=320,
    ),
}


class PokerBot:
    """An AI decision engine for a non-user poker player.

    This class uses the player's ``BotSkill`` profile and a Monte Carlo
    simulation (`estimate_win_rate`) to choose an appropriate action in a given
    game state.
    """

    def __init__(self, player: Player, skill: BotSkill, rng: random.Random) -> None:
        self.player = player
        self.skill = skill
        self.rng = rng

    def decide(self, table: "PokerTable") -> Action:
        """Chooses an action for the bot based on its skill and the current table state."""
        stage = table.stage
        player = self.player
        to_call = table.current_bet - player.current_bet

        if player.chips == 0:
            return Action(ActionType.CHECK)

        # Estimate the probability of winning the hand.
        win_rate = estimate_win_rate(
            hero=player,
            players=[p for p in table.players if not p.folded],
            community_cards=table.community_cards,
            simulations=self.skill.simulations,
            rng=self.rng,
        )
        # The Monte Carlo estimator serves as the bot's "sense" of hand strength.

        # Occasionally make a random mistake to simulate human-like imperfection.
        if self.rng.random() < self.skill.mistake_rate:
            return self._random_legal_action(table, to_call)

        # Adjust strategy based on the current stage of the hand.
        stage_adjustment = {
            "pre-flop": -0.08,
            "flop": 0.0,
            "turn": 0.04,
            "river": 0.08,
        }[stage]
        call_threshold = max(0.08, self.skill.tightness + stage_adjustment)
        strong_threshold = min(0.95, call_threshold + 0.25)
        # `call_threshold` defines when the bot is content to continue; a higher
        # `strong_threshold` gates aggressive raises and bets.

        # If there is no bet to call (the bot can check).
        if to_call == 0:
            if win_rate >= strong_threshold and player.chips > 0 and self.rng.random() < self.skill.aggression:
                target = self._bet_target(table, pot_factor=0.65)
                return Action(ActionType.BET, target_bet=target)
            if win_rate >= call_threshold or self.rng.random() < self.skill.bluff:
                return Action(ActionType.CHECK)
            if player.chips > 0:
                target = self._bet_target(table, pot_factor=0.35)
                return Action(ActionType.BET, target_bet=target)
            return Action(ActionType.CHECK)

        # If facing a bet.
        call_amount = min(to_call, player.chips)
        # Pot odds give the bot a baseline for whether calling is profitable.
        pot_odds = call_amount / max(table.pot + call_amount, 1)

        # Fold if hand is weak and pot odds are not favorable.
        if win_rate < call_threshold and win_rate < pot_odds and self.rng.random() > self.skill.bluff:
            return Action(ActionType.FOLD)

        # Raise if hand is very strong.
        if win_rate >= strong_threshold and player.chips > call_amount and self.rng.random() < self.skill.aggression:
            target = self._raise_target(table, pot_factor=0.8)
            return Action(ActionType.RAISE, target_bet=target)

        if call_amount >= player.chips:
            return Action(ActionType.ALL_IN, target_bet=player.current_bet + player.chips)

        return Action(ActionType.CALL, target_bet=table.current_bet)

    def _bet_target(self, table: "PokerTable", *, pot_factor: float) -> int:
        """Calculate a target bet size, typically a fraction of the pot."""
        min_total = max(table.min_raise_amount, table.big_blind)
        pot_sized = max(min_total, int((table.pot or table.big_blind) * pot_factor))
        return self.player.current_bet + min(self.player.chips, pot_sized)

    def _raise_target(self, table: "PokerTable", *, pot_factor: float) -> int:
        """Calculate a target raise size."""
        increment = max(table.min_raise_amount, int((table.pot or table.big_blind) * pot_factor))
        target = max(table.current_bet + increment, table.current_bet + table.min_raise_amount)
        target = min(self.player.current_bet + self.player.chips, target)
        return target if target > self.player.current_bet else self.player.current_bet + self.player.chips

    def _random_legal_action(self, table: "PokerTable", to_call: int) -> Action:
        """Return a randomly chosen legal action, used to simulate mistakes."""
        player = self.player
        options: list[Action] = []
        if to_call == 0:
            options.append(Action(ActionType.CHECK))
            if player.chips > 0:
                # Use a minimal raise size so "mistakes" stay plausible.
                target = player.current_bet + min(player.chips, max(table.big_blind, table.min_raise_amount))
                options.append(Action(ActionType.BET, target))
        else:
            options.append(Action(ActionType.CALL, table.current_bet))
            options.append(Action(ActionType.FOLD))
            if player.chips + player.current_bet > table.current_bet + table.min_raise_amount:
                # Choose a random raise between 20% and 80% of the pot to mimic
                # a hasty, imperfect decision.
                target = self._raise_target(table, pot_factor=self.rng.uniform(0.2, 0.8))
                options.append(Action(ActionType.RAISE, target))
            else:
                options.append(Action(ActionType.ALL_IN, player.current_bet + player.chips))
        return self.rng.choice(options)


class PokerTable:
    """Manages the state and progression of a single Texas Hold'em hand.

    This class handles the core game flow, including dealing cards, managing betting
    rounds, posting blinds, and distributing the pot.
    """

    def __init__(
        self,
        players: Sequence[Player],
        *,
        small_blind: int = 10,
        big_blind: int = 20,
        rng: random.Random | None = None,
        game_variant: GameVariant = GameVariant.TEXAS_HOLDEM,
        betting_limit: BettingLimit = BettingLimit.NO_LIMIT,
    ) -> None:
        if len(players) < 2:
            raise ValueError("At least two players are required")
        self.players = list(players)
        self.small_blind = small_blind
        self.big_blind = big_blind
        self.rng = rng or random.Random()
        self.game_variant = game_variant
        self.betting_limit = betting_limit
        self.deck: Deck = fresh_deck(self.rng)
        self.community_cards: list[Card] = []
        self.pot: int = 0
        self.dealer_index = 0
        self.current_player_index = 0
        self.stage: str = "pre-flop"
        self.current_bet: int = 0
        self.min_raise_amount: int = self.big_blind
        self.last_actions: list[str] = []
        self._players_who_acted: set[int] = set()

    def rotate_dealer(self) -> None:
        """Moves the dealer button to the next player."""
        self.dealer_index = (self.dealer_index + 1) % len(self.players)

    def start_hand(self) -> None:
        """Resets the table and player states to begin a new hand."""
        for player in self.players:
            player.reset_for_hand()

        self.deck = fresh_deck(self.rng)
        self.community_cards.clear()
        self.pot = 0
        self.stage = "pre-flop"
        self.current_bet = 0
        self.min_raise_amount = self.big_blind
        self._players_who_acted.clear()
        self.last_actions.clear()
        # With a clean slate we can redeal, so wipe every transient accumulator.

        # Deal hole cards to each player (2 for Texas Hold'em, 4 for Omaha).
        cards_to_deal = 4 if self.game_variant == GameVariant.OMAHA else 2
        for player in self.players:
            player.receive_cards(self.deck.deal(cards_to_deal))

        # Players with no chips are marked as folded.
        for player in self.players:
            if player.chips == 0:
                player.folded = True
                player.all_in = True

        self._post_blinds()
        self.current_player_index = self._first_to_act_index()

    def _post_blinds(self) -> None:
        """Posts the small and big blinds."""
        sb_index = (self.dealer_index + 1) % len(self.players)
        bb_index = (self.dealer_index + 2) % len(self.players)
        sb_player = self.players[sb_index]
        bb_player = self.players[bb_index]
        # The blinds are treated as forced bets, so move chips before the first action.
        self._commit(sb_player, sb_player.current_bet + min(self.small_blind, sb_player.chips))
        self._commit(bb_player, bb_player.current_bet + min(self.big_blind, bb_player.chips))
        self.current_bet = bb_player.current_bet
        self.min_raise_amount = self.big_blind
        self._players_who_acted = set()

    def _first_to_act_index(self) -> int:
        """Determines the index of the player who acts first in a betting round."""
        index = (self.dealer_index + 3) % len(self.players)  # UTG position
        # `_next_index` skips folded/all-in players while preserving order.
        return self._next_index(index - 1)

    def _next_index(self, start: int) -> int:
        """Finds the index of the next active player."""
        index = (start + 1) % len(self.players)
        for _ in range(len(self.players)):
            player = self.players[index]
            if not player.folded and not player.all_in:
                return index
            index = (index + 1) % len(self.players)
        return index

    def _commit(self, player: Player, target_bet: int) -> None:
        """Commits a player's chips to the pot up to the target amount."""
        amount_to_add = max(0, target_bet - player.current_bet)
        if amount_to_add == 0:
            return

        contribution = min(amount_to_add, player.chips)
        # Keep all bookkeeping in sync so UI layers can display chip counts accurately.
        player.chips -= contribution
        player.current_bet += contribution
        player.total_invested += contribution
        self.pot += contribution
        if player.chips == 0:
            player.all_in = True

    def valid_actions(self, player: Player) -> list[ActionType]:
        """Returns a list of legal actions for the given player."""
        to_call = self.current_bet - player.current_bet
        options: list[ActionType] = []
        if to_call <= 0:
            options.append(ActionType.CHECK)
            if player.chips > 0:
                options.append(ActionType.BET)
        else:
            options.append(ActionType.FOLD)
            options.append(ActionType.CALL)
            if player.chips + player.current_bet > self.current_bet:
                options.append(ActionType.RAISE)
            if player.chips > 0:
                options.append(ActionType.ALL_IN)
        return options

    def apply_action(self, player: Player, action: Action) -> None:
        """Applies a player's action and updates the game state."""
        to_call = self.current_bet - player.current_bet
        previous_high = self.current_bet

        if action.kind is ActionType.FOLD:
            player.folded = True
            player.last_action = "fold"
            player.last_wager = 0
        elif action.kind is ActionType.CHECK:
            if to_call > 0:
                raise ValueError("Cannot check when facing a bet")
            player.last_action = "check"
            player.last_wager = 0
        else:
            # Handle bet, raise, call, all-in
            target = min(action.target_bet, player.current_bet + player.chips)

            before_bet = player.current_bet
            if action.kind is ActionType.CALL:
                target = self.current_bet
            elif action.kind is ActionType.BET:
                if to_call > 0:
                    raise ValueError("Cannot bet when facing a wager; must call or raise")
                min_total = player.current_bet + max(self.min_raise_amount, self.big_blind)
                # Enforce a minimum opening bet so the pot grows at a realistic pace.
                target = max(target, min_total)
                # Enforce pot-limit betting if applicable.
                if self.betting_limit == BettingLimit.POT_LIMIT:
                    max_bet = player.current_bet + self.pot
                    target = min(target, max_bet)
            elif action.kind is ActionType.RAISE:
                if to_call <= 0:
                    raise ValueError("Cannot raise without a bet to match")
                min_total = self.current_bet + self.min_raise_amount
                # Raises must meet or exceed the previous increment unless the
                # player is moving all-in.
                target = max(target, min_total)
                # Enforce pot-limit betting if applicable.
                if self.betting_limit == BettingLimit.POT_LIMIT:
                    # In pot-limit, max raise is pot + amount to call + amount already bet.
                    max_raise = self.pot + to_call + player.current_bet
                    target = min(target, max_raise)
            elif action.kind is ActionType.ALL_IN:
                target = player.current_bet + player.chips

            self._commit(player, target)
            player.last_action = action.kind.value
            player.last_wager = player.current_bet - before_bet

            # If the bet was a raise, update the minimum raise amount.
            if player.current_bet > previous_high:
                raise_size = player.current_bet - previous_high
                if previous_high == 0:
                    self.min_raise_amount = max(raise_size, self.big_blind)
                elif raise_size >= self.min_raise_amount or player.all_in:
                    if not player.all_in:
                        self.min_raise_amount = raise_size
                else:
                    raise ValueError("Raise did not meet minimum size")
                self.current_bet = player.current_bet
                # Reset the tracker so everyone has a chance to respond to the new price.
                self._players_who_acted = {id(player)}

        self._players_who_acted.add(id(player))
        self.last_actions.append(f"{player.name} {action.kind.value}{self._action_suffix(player)}")

        # Advance to the next player if the round is not over.
        if self._active_player_count() > 1 and self.players_can_act():
            self.current_player_index = self._next_index(self.current_player_index)

    def _action_suffix(self, player: Player) -> str:
        """Generates a descriptive suffix for an action, e.g., ' (100 chips)'."""
        if player.folded or player.last_action == "check" or player.last_action == "fold":
            return ""
        if player.last_action == ActionType.CALL.value:
            return f" ({player.last_wager} chips)"
        if player.last_action == ActionType.ALL_IN.value:
            return f" for {player.current_bet} total"
        if player.last_action in {ActionType.RAISE.value, ActionType.BET.value}:
            return f" to {player.current_bet}"
        return ""

    def betting_round_complete(self) -> bool:
        """Checks if the current betting round is complete."""
        if self._active_player_count() <= 1:
            return True

        for player in self.players:
            if player.folded or player.all_in:
                continue
            if player.current_bet != self.current_bet:
                return False
            if id(player) not in self._players_who_acted:
                return False
        return True

    def proceed_to_next_stage(self) -> None:
        """Advances the game to the next stage (flop, turn, river)."""
        # Reset bets for the new round.
        for player in self.players:
            player.current_bet = 0
        self.current_bet = 0
        self.min_raise_amount = self.big_blind
        self._players_who_acted = set()

        if self.stage == "pre-flop":
            self._burn()
            self.community_cards.extend(self.deck.deal(3))
            self.stage = "flop"
        elif self.stage == "flop":
            self._burn()
            self.community_cards.extend(self.deck.deal(1))
            self.stage = "turn"
        elif self.stage == "turn":
            self._burn()
            self.community_cards.extend(self.deck.deal(1))
            self.stage = "river"
        else:
            raise RuntimeError("No further stage to proceed to")

        self.current_player_index = self._next_index(self.dealer_index)

    def _evaluate_hand(self, player: Player) -> HandRank:
        """Evaluates a player's best hand based on the game variant.

        For Texas Hold'em: Use any 5 cards from hole + community.
        For Omaha: Must use exactly 2 hole cards and 3 community cards.
        """
        if self.game_variant == GameVariant.OMAHA:
            # In Omaha, must use exactly 2 hole cards and 3 community cards.
            best_rank = None
            for hole_combo in itertools.combinations(player.hole_cards, 2):
                for board_combo in itertools.combinations(self.community_cards, 3):
                    rank = best_hand(list(hole_combo) + list(board_combo))
                    if best_rank is None or rank > best_rank:
                        best_rank = rank
            return best_rank if best_rank is not None else best_hand(player.hole_cards + self.community_cards)
        else:
            # Texas Hold'em: Use any 5 cards.
            return best_hand(player.hole_cards + self.community_cards)

    def showdown(self) -> list[tuple[Player, HandRank]]:
        """Determines the winner(s) at the end of a hand by comparing hand ranks."""
        contenders = [player for player in self.players if not player.folded]
        rankings = [(player, self._evaluate_hand(player)) for player in contenders]
        rankings.sort(key=lambda item: item[1], reverse=True)
        return rankings

    def distribute_pot(self) -> dict[str, int]:
        """Distributes the pot to the winner(s), handling side pots correctly."""
        payouts = {player.name: 0 for player in self.players}

        # If only one player remains, they win the whole pot.
        if self._active_player_count() == 1:
            winner = next(player for player in self.players if not player.folded)
            winner.chips += self.pot
            payouts[winner.name] = self.pot
            self.pot = 0
            return payouts

        # Handle side pots by processing contributions at different levels.
        contributions = sorted({p.total_invested for p in self.players if p.total_invested > 0})
        previous_level = 0
        remaining_pot = self.pot

        for level in contributions:
            eligible = [p for p in self.players if p.total_invested >= level]
            slice_amount = min((level - previous_level) * len(eligible), remaining_pot)
            if slice_amount <= 0:
                continue

            contenders = [p for p in eligible if not p.folded]
            if contenders:
                ranked_contenders = [(p, self._evaluate_hand(p)) for p in contenders]
                best_rank = max(rank for _, rank in ranked_contenders)
                winners = [p for p, rank in ranked_contenders if rank == best_rank]
            else:
                winners = eligible

            # Distribute the side pot among the winners.
            share = slice_amount // len(winners)
            for player in winners:
                player.chips += share
                payouts[player.name] += share

            # Distribute any remainder chips.
            for i, player in enumerate(winners[: slice_amount % len(winners)]):
                player.chips += 1
                payouts[player.name] += 1

            remaining_pot -= slice_amount
            previous_level = level

        if remaining_pot > 0:
            # Any leftover chips go to the player with the largest stack.
            richest = max(self.players, key=lambda p: p.chips)
            richest.chips += remaining_pot
            payouts[richest.name] += remaining_pot

        self.pot = 0
        for player in self.players:
            player.total_invested = 0
        return payouts

    def _burn(self) -> None:
        """Discards one card from the deck before dealing community cards."""
        self.deck.deal(1)

    def _active_player_count(self) -> int:
        """Returns the number of players who have not folded."""
        return sum(1 for player in self.players if not player.folded)

    def players_can_act(self) -> bool:
        """Checks if there are any players who can still make a move."""
        # Once every remaining player is all-in, betting rounds should skip straight to showdowns.
        return any(not player.folded and not player.all_in for player in self.players)


def estimate_win_rate(
    *,
    hero: Player,
    players: Sequence[Player],
    community_cards: Sequence[Card],
    simulations: int,
    rng: random.Random,
) -> float:
    """Estimates the probability of a player winning using Monte Carlo simulation.

    This function simulates the remainder of the hand many times to estimate the
    hero's equity (win rate) against their opponents.

    Args:
        hero: The player whose win rate is being estimated.
        players: All active players at the table.
        community_cards: The cards currently on the board.
        simulations: The number of simulations to run.
        rng: The random number generator to use.

    Returns:
        The estimated win rate as a float between 0.0 and 1.0.
    """
    active_opponents = [p for p in players if p is not hero and not p.folded]
    if not active_opponents:
        return 1.0

    known_cards = set(hero.hole_cards) | set(community_cards)
    # Build a deck minus the cards we already know about so that each simulation
    # draws fresh, non-conflicting combinations of hole cards and board cards.
    deck_pool = [card for card in FULL_DECK if card not in known_cards]
    wins = 0
    ties = 0

    needed_board = 5 - len(community_cards)
    opponent_count = len(active_opponents)

    for _ in range(max(simulations, 1)):
        rng.shuffle(deck_pool)
        iterator = iter(deck_pool)
        opponent_holes = [list(itertools.islice(iterator, 2)) for _ in range(opponent_count)]
        board_completion = list(community_cards) + list(itertools.islice(iterator, needed_board))

        hero_rank = best_hand(hero.hole_cards + board_completion)
        opponent_ranks = [best_hand(hole + board_completion) for hole in opponent_holes]
        best_opponent = max(opponent_ranks)

        if hero_rank > best_opponent:
            wins += 1
        elif hero_rank == best_opponent:
            ties += 1

    return (wins + ties / 2) / max(simulations, 1)


@dataclass
class MatchResult:
    """A data class to store the results of a completed poker hand."""

    stage: str
    community_cards: list[Card]
    showdown: list[tuple[str, HandRank]]
    payouts: dict[str, int]
    log: list[str]


class PokerMatch:
    """A high-level controller that manages a series of poker hands.

    This class orchestrates the entire match, from initialization to playing
    multiple hands and tracking player chip counts over time.
    """

    def __init__(
        self,
        difficulty: BotSkill,
        *,
        rounds: int = 3,
        starting_chips: int = 1_000,
        rng: random.Random | None = None,
        game_variant: GameVariant = GameVariant.TEXAS_HOLDEM,
        betting_limit: BettingLimit = BettingLimit.NO_LIMIT,
        tournament_mode: TournamentMode | None = None,
    ) -> None:
        if rounds <= 0:
            raise ValueError("rounds must be a positive integer")
        self.difficulty = difficulty
        self.rounds = rounds
        self.rng = rng or random.Random()
        self.game_variant = game_variant
        self.betting_limit = betting_limit
        self.tournament_mode = tournament_mode or TournamentMode()
        self.user = Player(name="You", is_user=True, chips=starting_chips)
        self.bots = [Player(name=f"{difficulty.name} Bot {i+1}", chips=starting_chips) for i in range(3)]
        self.players = [self.user, *self.bots]
        sb, bb = self.tournament_mode.get_blinds(0)
        self.table = PokerTable(
            self.players,
            small_blind=sb,
            big_blind=bb,
            rng=self.rng,
            game_variant=game_variant,
            betting_limit=betting_limit,
        )
        self.bot_controllers = [PokerBot(bot, difficulty, self.rng) for bot in self.bots]
        self.hand_number = 0
        self.hand_histories: list[HandHistory] = []

    def reset(self) -> None:
        """Resets the match to its initial state."""
        for player in self.players:
            player.chips = max(player.chips, 0)
        self.table.dealer_index = 0
        self.hand_number = 0

    def play_cli(self) -> None:
        """Runs the poker match using the command-line interface."""
        variant_name = "Omaha Hold'em" if self.game_variant == GameVariant.OMAHA else "Texas Hold'em"
        limit_name = self.betting_limit.value.replace("-", " ").title()
        mode_info = " (Tournament Mode)" if self.tournament_mode.enabled else ""
        print(f"Welcome to {variant_name} ({limit_name})! Playing {self.rounds} hands against {len(self.bots)} {self.difficulty.name} bots.{mode_info}")
        print()

        for round_num in range(1, self.rounds + 1):
            if self.user.chips <= 0:
                print("You are out of chips. Match over.")
                break
            if all(bot.chips <= 0 for bot in self.bots):
                print("All opponents are out of chips. You win!")
                break

            # Update blinds if tournament mode is enabled.
            if self.tournament_mode.enabled:
                sb, bb = self.tournament_mode.get_blinds(round_num - 1)
                self.table.small_blind = sb
                self.table.big_blind = bb
                if round_num > 1 and (round_num - 1) % self.tournament_mode.hands_per_level == 0:
                    print(f"*** Blinds increased to {sb}/{bb} ***")

            print(f"=== Hand {round_num} ===")
            if self.tournament_mode.enabled:
                print(f"Blinds: {self.table.small_blind}/{self.table.big_blind}")
            result = self.play_hand_cli()
            self._record_hand_history(round_num, result)
            self._display_hand_result(result)
            print(self._stack_summary())
            print()
            self.table.rotate_dealer()

        print("Match complete! Final chip counts:")
        print(self._stack_summary())
        self._display_player_statistics()
        self._save_hand_histories()

    def play_hand_cli(self) -> MatchResult:
        """Plays a single hand of poker in the CLI."""
        table = self.table
        table.start_hand()
        table.last_actions.clear()
        log: list[str] = []

        print(f"Your hole cards: {format_cards(self.user.hole_cards)}")

        while True:
            player = table.players[table.current_player_index]

            # Check if betting round or hand is over.
            if not table.players_can_act() or table._active_player_count() <= 1:
                log.extend(table.last_actions)
                if table.stage != "river" and table._active_player_count() > 1:
                    table.proceed_to_next_stage()
                    print(f"Board: {format_cards(table.community_cards)}")
                    continue
                break

            # Get action from user or bot.
            if player.is_user and not player.folded and not player.all_in:
                action = self._prompt_user_action(table, player)
            elif player.folded or player.all_in:
                table.current_player_index = table._next_index(table.current_player_index)
                continue
            else:
                controller = next(c for c in self.bot_controllers if c.player is player)
                action = controller.decide(table)

            table.apply_action(player, action)
            print(table.last_actions[-1])

            # If betting round is complete, advance to the next stage.
            if table.betting_round_complete():
                log.extend(table.last_actions)
                table.last_actions.clear()
                if table.stage == "river":
                    break
                table.proceed_to_next_stage()
                if table.stage != "pre-flop":
                    print(f"Board: {format_cards(table.community_cards)}")

        # Update player statistics for hands played and folded.
        for player in self.players:
            player.statistics.hands_played += 1
            if player.folded:
                player.statistics.hands_folded += 1
            player.statistics.total_wagered += player.total_invested

        # Determine winner and distribute pot.
        showdown = []
        if table._active_player_count() == 1:
            payouts = table.distribute_pot()
        else:
            rankings = table.showdown()
            for p, rank in rankings:
                print(f"{p.name}: {format_cards(p.hole_cards)} -> {rank.describe()}")
                p.statistics.showdowns_reached += 1
            payouts = table.distribute_pot()
            showdown = [(p.name, rank) for p, rank in rankings]

        # Update statistics for winners.
        for player in self.players:
            if payouts.get(player.name, 0) > 0:
                player.statistics.hands_won += 1
                player.statistics.total_winnings += payouts[player.name]
                if showdown:
                    player.statistics.showdowns_won += 1

        return MatchResult(table.stage, list(table.community_cards), showdown, payouts, log)

    def _prompt_user_action(self, table: PokerTable, player: Player) -> Action:
        """Prompts the user for an action and returns the chosen action."""
        to_call = table.current_bet - player.current_bet
        print(f"Pot: {table.pot} | To call: {to_call} | Stack: {player.chips}")
        if table.community_cards:
            print(f"Board: {format_cards(table.community_cards)}")

        options = table.valid_actions(player)
        prompt_parts = [opt.value for opt in options if opt not in {ActionType.BET, ActionType.RAISE}]
        if ActionType.BET in options or ActionType.RAISE in options:
            prompt_parts.append("bet/raise <amount>")

        while True:
            choice = input(f"Choose action [{', '.join(prompt_parts)}]: ").strip().lower()
            parts = choice.split()
            command = parts[0]

            if command in {"check", "c"} and ActionType.CHECK in options:
                return Action(ActionType.CHECK)
            if command in {"fold", "f"} and ActionType.FOLD in options:
                return Action(ActionType.FOLD)
            if command == "call" and ActionType.CALL in options:
                return Action(ActionType.CALL, target_bet=table.current_bet)
            if command in {"all-in", "allin", "a"} and ActionType.ALL_IN in options:
                return Action(ActionType.ALL_IN)

            if command == "bet" and ActionType.BET in options:
                amount = self._parse_amount(parts[1] if len(parts) > 1 else "", default=table.big_blind)
                return Action(ActionType.BET, target_bet=player.current_bet + amount)
            if command == "raise" and ActionType.RAISE in options:
                amount = self._parse_amount(parts[1] if len(parts) > 1 else "", default=table.min_raise_amount)
                return Action(ActionType.RAISE, target_bet=table.current_bet + amount)

            print("Invalid action. Please choose from the available options.")

    @staticmethod
    def _parse_amount(raw: str, *, default: int) -> int:
        """Parses a string into a valid bet/raise amount."""
        try:
            return max(default, int(raw.strip())) if raw.strip() else default
        except ValueError as exc:
            raise ValueError("Invalid amount specified") from exc

    def _display_hand_result(self, result: MatchResult) -> None:
        """Prints the results of a completed hand."""
        for name, payout in result.payouts.items():
            if payout > 0:
                print(f"{name} wins {payout} chips.")

    def _stack_summary(self) -> str:
        """Returns a string summarizing the current chip stacks of all players."""
        return "Chip stacks:\n" + "\n".join(f"  {p.name}: {p.chips}" for p in self.players)

    def _record_hand_history(self, hand_number: int, result: MatchResult) -> None:
        """Records the history of a completed hand."""
        history = HandHistory(
            hand_number=hand_number,
            timestamp=datetime.now().isoformat(),
            game_variant=self.game_variant.value,
            small_blind=self.table.small_blind,
            big_blind=self.table.big_blind,
            players={p.name: p.chips + p.total_invested for p in self.players},
            hole_cards={p.name: [str(c) for c in p.hole_cards] for p in self.players},
            community_cards=[str(c) for c in result.community_cards],
            actions=result.log,
            showdown=[(name, rank.describe()) for name, rank in result.showdown],
            payouts=result.payouts,
        )
        self.hand_histories.append(history)

    def _display_player_statistics(self) -> None:
        """Displays player statistics at the end of the match."""
        print("\n=== Player Statistics ===")
        for player in self.players:
            stats = player.statistics
            print(f"\n{player.name}:")
            print(f"  Hands played: {stats.hands_played}")
            print(f"  Hands won: {stats.hands_won} ({stats.win_rate:.1f}%)")
            print(f"  Hands folded: {stats.hands_folded} ({stats.fold_frequency:.1f}%)")
            print(f"  Showdowns: {stats.showdowns_won}/{stats.showdowns_reached}")
            print(f"  Net profit: {stats.net_profit:+d} chips")

    def _save_hand_histories(self) -> None:
        """Saves hand histories to a JSON file."""
        if not self.hand_histories:
            return

        filename = f"poker_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = Path.cwd() / filename

        try:
            data = {
                "game_variant": self.game_variant.value,
                "betting_limit": self.betting_limit.value,
                "tournament_mode": self.tournament_mode.enabled,
                "hands": [h.to_dict() for h in self.hand_histories],
                "final_statistics": {p.name: p.statistics.to_dict() for p in self.players},
            }
            with open(filepath, "w") as f:
                json.dump(data, f, indent=2)
            print(f"\nHand history saved to: {filename}")
        except Exception as e:
            print(f"\nFailed to save hand history: {e}")


def parse_arguments(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parses command-line arguments for the poker application."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--difficulty",
        choices=DIFFICULTIES.keys(),
        default="Noob",
        help="Bot skill level.",
    )
    parser.add_argument("--rounds", type=int, default=3, help="Number of hands to play.")
    parser.add_argument("--seed", type=int, help="Optional random seed for deterministic play.")
    parser.add_argument("--gui", action="store_true", help="Launch the graphical interface.")
    parser.add_argument(
        "--gui-framework",
        choices=["tkinter", "pyqt5"],
        default="tkinter",
        help="Select the GUI framework to launch when using --gui.",
    )
    parser.add_argument(
        "--variant",
        choices=["texas-holdem", "omaha"],
        default="texas-holdem",
        help="Poker variant to play.",
    )
    parser.add_argument(
        "--limit",
        choices=["no-limit", "pot-limit", "fixed-limit"],
        default="no-limit",
        help="Betting limit structure.",
    )
    parser.add_argument(
        "--tournament",
        action="store_true",
        help="Enable tournament mode with increasing blinds.",
    )
    return parser.parse_args(argv)


def run_cli(argv: Sequence[str] | None = None) -> None:
    """Runs the command-line interface for the poker match."""
    args = parse_arguments(argv)
    rng = random.Random(args.seed) if args.seed is not None else random.Random()
    difficulty = DIFFICULTIES[args.difficulty]

    # Parse game variant and betting limit.
    game_variant = GameVariant(args.variant)
    betting_limit = BettingLimit(args.limit)

    # Set up tournament mode if requested.
    tournament_mode = TournamentMode(enabled=args.tournament) if args.tournament else None

    match = PokerMatch(
        difficulty,
        rounds=args.rounds,
        rng=rng,
        game_variant=game_variant,
        betting_limit=betting_limit,
        tournament_mode=tournament_mode,
    )

    if getattr(args, "gui", False):
        if getattr(args, "gui_framework", "tkinter") == "pyqt5":
            try:
                from .gui_pyqt import launch_gui as launch_pyqt_gui
            except ImportError as exc:  # pragma: no cover - optional dependency
                raise RuntimeError("PyQt5 is required for the PyQt poker GUI but is not available.") from exc

            launch_pyqt_gui(match, rng=rng)
        else:
            from .gui import launch_gui as launch_tk_gui

            launch_tk_gui(match, rng=rng)
    else:
        match.play_cli()


def main() -> None:  # pragma: no cover - convenience wrapper
    run_cli()


__all__ = [
    "Action",
    "ActionType",
    "BotSkill",
    "DIFFICULTIES",
    "MatchResult",
    "Player",
    "PokerMatch",
    "PokerTable",
    "estimate_win_rate",
    "parse_arguments",
    "run_cli",
]
