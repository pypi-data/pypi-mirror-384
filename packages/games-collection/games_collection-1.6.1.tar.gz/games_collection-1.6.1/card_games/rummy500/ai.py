"""Simple AI helpers for the Rummy 500 command-line interface.

This module provides a basic AI for playing Rummy 500. The AI makes decisions
on drawing, melding, laying off, and discarding based on a simple heuristic
of maximizing points and minimizing deadwood.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from typing import Optional, Tuple

from card_games.common.cards import Card
from card_games.rummy500.game import GamePhase, Rummy500Game


def _card_value(card: Card) -> int:
    """Return the scoring value for *card*.

    Args:
        card: The card to evaluate.

    Returns:
        The point value of the card.
    """
    if card.rank == "A":
        return 15
    if card.rank in {"K", "Q", "J", "T"}:
        return 10
    return int(card.rank)


@dataclass
class DrawDecision:
    """Container describing how the AI wants to draw cards.

    Attributes:
        from_discard: Whether to draw from the discard pile.
        take_count: The number of cards to take from the discard pile.
    """

    from_discard: bool
    take_count: int


class Rummy500AI:
    """Decision helpers for non-human players in the CLI experience.

    This class encapsulates the logic for an AI player, providing methods to
    make decisions at each stage of the game.

    Attributes:
        player_index: The index of the player the AI is controlling.
    """

    def __init__(self, player_index: int) -> None:
        """Initializes the Rummy500AI.

        Args:
            player_index: The index of the player the AI will control.
        """
        self.player_index = player_index

    # ------------------------------------------------------------------
    # Draw phase
    # ------------------------------------------------------------------
    def choose_draw(self, game: Rummy500Game) -> DrawDecision:
        """Decide whether to draw from the deck or discard pile.

        The AI evaluates the discard pile to see if taking one or more cards
        improves its hand. If not, it draws from the deck.

        Args:
            game: The current game state.

        Returns:
            A DrawDecision object indicating the AI's choice.
        """
        if game.phase != GamePhase.DRAW:
            return DrawDecision(from_discard=False, take_count=1)

        hand = list(game.hands[self.player_index])
        base_summary = game.summarize_cards(hand)
        best_summary = base_summary
        best_choice = DrawDecision(from_discard=False, take_count=1)

        if not game.discard_pile:
            return best_choice

        top_card = game.discard_pile[-1]
        max_take = min(len(game.discard_pile), 5)

        for take_count in range(1, max_take + 1):
            grabbed = game.discard_pile[-take_count:]
            candidate_hand = hand + grabbed
            summary = game.summarize_cards(candidate_hand)

            top_in_meld = any(top_card in meld for meld in summary["melds"])
            top_layoff = False
            others: list[Card] = []
            used_top = False
            for card in candidate_hand:
                if not used_top and card == top_card:
                    used_top = True
                    continue
                others.append(card)

            max_extra = min(2, len(others))
            for idx in range(len(game.melds)):
                for extra in range(max_extra + 1):
                    for combo in combinations(others, extra):
                        if game.can_lay_off(idx, [top_card, *combo]):
                            top_layoff = True
                            break
                    if top_layoff:
                        break
                if top_layoff:
                    break

            if not top_in_meld and not top_layoff:
                continue

            if self._is_better_summary(summary, best_summary):
                best_summary = summary
                best_choice = DrawDecision(from_discard=True, take_count=take_count)

        return best_choice

    # ------------------------------------------------------------------
    # Meld / Layoff phase
    # ------------------------------------------------------------------
    def perform_melds_and_layoffs(self, game: Rummy500Game) -> bool:
        """Play available melds and lay-offs.

        The AI will lay down all possible melds from its hand and then lay off
        any cards it can on existing melds.

        Args:
            game: The current game state.

        Returns:
            True if the AI goes out, False otherwise.
        """
        if game.phase != GamePhase.MELD:
            return False

        summary = game.get_deadwood_summary(self.player_index)
        for meld_cards in summary["melds"]:
            game.lay_meld(self.player_index, list(meld_cards))

        # Lay off highest-value cards first
        while True:
            option = self._select_best_layoff(game)
            if option is None:
                break
            meld_index, card = option
            game.lay_off(self.player_index, meld_index, [card])

        if not game.hands[self.player_index]:
            return game.go_out(self.player_index)

        return False

    def choose_discard(self, game: Rummy500Game) -> Card:
        """Choose the best discard from the current hand.

        The AI chooses a discard that maximizes the net point value of its hand.

        Args:
            game: The current game state.

        Returns:
            The card the AI has chosen to discard.
        """
        hand = list(game.hands[self.player_index])
        assert hand, "Cannot choose a discard from an empty hand"

        best_card = hand[0]
        best_summary = game.preview_after_cards(self.player_index, [best_card])

        for card in hand[1:]:
            summary = game.preview_after_cards(self.player_index, [card])
            if self._is_better_summary(summary, best_summary):
                best_card = card
                best_summary = summary
            elif summary["net_points"] == best_summary["net_points"]:
                if _card_value(card) < _card_value(best_card):
                    best_card = card
                    best_summary = summary

        return best_card

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _is_better_summary(self, candidate: dict, current: dict) -> bool:
        """Return True if *candidate* is preferable to *current*.

        A summary is considered better if it has a higher net score. Ties are
        broken by lower deadwood points, then higher meld points.

        Args:
            candidate: The candidate hand summary.
            current: The current best hand summary.

        Returns:
            True if the candidate summary is better, False otherwise.
        """
        if candidate["net_points"] != current["net_points"]:
            return candidate["net_points"] > current["net_points"]

        if candidate["deadwood_points"] != current["deadwood_points"]:
            return candidate["deadwood_points"] < current["deadwood_points"]

        return candidate["meld_points"] > current["meld_points"]

    def _select_best_layoff(self, game: Rummy500Game) -> Optional[Tuple[int, Card]]:
        """Return the layoff yielding the greatest immediate benefit.

        The AI selects the layoff option that gets rid of the highest-value card.

        Args:
            game: The current game state.

        Returns:
            A tuple containing the meld index and the card to lay off, or
            None if no layoff is possible.
        """
        best_option: Optional[Tuple[int, Card]] = None
        best_value = -1

        for option in game.get_layoff_options(self.player_index):
            meld_index = option["meld_index"]
            for card in option["cards"]:
                value = _card_value(card)
                if value > best_value:
                    best_value = value
                    best_option = (meld_index, card)

        return best_option
