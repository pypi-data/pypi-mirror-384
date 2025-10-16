"""Solitaire (Klondike) game engine.

This module implements a feature-complete version of Klondike (Solitaire).
It supports both *draw-one* and *draw-three* styles, limited stock recycles,
standard and Vegas scoring, automatic moves to the foundations, and detailed
state statistics so the CLI (and tests) can surface a realistic experience.

The core gameplay concepts are:

* Building four foundation piles (one per suit) from Ace to King.
* Seven tableau piles that build down in alternating colours and allow moving
  whole face-up runs.
* A stock pile from which cards are drawn one or three at a time into the
  waste pile, with optional limits on how often the waste may be recycled
  back to the stock.
* Scoring that mirrors the Windows "Standard" rules (+10 per foundation move,
  +5 when flipping tableau cards, -15 for withdrawing from a foundation) and
  the Vegas casino rules (-52 buy-in, +5 per foundation move).

The engine purposefully keeps UI concerns out of the logic so both CLI and
future GUI front-ends can provide a rich depiction of a Klondike session.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from random import Random
from typing import Optional

from card_games.common.cards import Card, Deck, Suit

RANK_ORDER = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "T", "J", "Q", "K"]


class PileType(Enum):
    """Types of piles in Klondike solitaire."""

    FOUNDATION = auto()  # Four piles, built up by suit from Ace to King
    TABLEAU = auto()  # Seven piles, built down in alternating colors
    STOCK = auto()  # Draw pile
    WASTE = auto()  # Discard pile


@dataclass
class Pile:
    """Represents a pile of cards in solitaire.

    Attributes:
        pile_type: The type of pile (foundation, tableau, etc.)
        cards: List of cards in the pile (bottom to top)
        face_up_count: Number of face-up cards (for tableau piles)
    """

    pile_type: PileType
    cards: list[Card] = field(default_factory=list)
    face_up_count: int = 0

    def top_card(self) -> Optional[Card]:
        """Get the top card of the pile without removing it."""
        return self.cards[-1] if self.cards else None

    def can_add_to_foundation(self, card: Card) -> bool:
        """Check if a card can be added to this foundation pile."""
        if self.pile_type != PileType.FOUNDATION:
            return False

        if not self.cards:
            return card.rank == "A"

        top = self.top_card()
        if top and top.suit == card.suit:
            # Must be one rank higher
            return RANK_ORDER.index(card.rank) == RANK_ORDER.index(top.rank) + 1

        return False

    def can_add_to_tableau(self, card: Card) -> bool:
        """Check if a card can be added to this tableau pile."""
        if self.pile_type != PileType.TABLEAU:
            return False

        if not self.cards:
            return card.rank == "K"

        top = self.top_card()
        if top:
            # Must be opposite color and one rank lower
            is_opposite_color = self._is_opposite_color(card, top)
            is_one_rank_lower = RANK_ORDER.index(card.rank) == RANK_ORDER.index(top.rank) - 1
            return is_opposite_color and is_one_rank_lower

        return False

    @staticmethod
    def _is_opposite_color(card1: Card, card2: Card) -> bool:
        """Check if two cards are opposite colors."""
        red_suits = {Suit.HEARTS, Suit.DIAMONDS}
        card1_red = card1.suit in red_suits
        card2_red = card2.suit in red_suits
        return card1_red != card2_red


class SolitaireGame:
    """Main engine for Klondike solitaire.

    This class manages the game state and provides methods for moving cards
    between piles according to solitaire rules.
    """

    def __init__(
        self,
        *,
        draw_count: int = 3,
        max_recycles: Optional[int] = None,
        scoring_mode: str = "standard",
        rng: Optional[Random] = None,
    ):
        """Initialize a new solitaire game.

        Args:
            draw_count: Number of cards to draw from the stock at a time (1 or 3).
            max_recycles: Optional limit for how many times the waste may be
                recycled back into the stock. ``None`` indicates no limit.
            scoring_mode: Scoring variant to use (``"standard"`` or ``"vegas"``).
            rng: Optional random number generator for shuffling.

        Raises:
            ValueError: If any configuration option is invalid.
        """
        if draw_count not in (1, 3):
            raise ValueError("draw_count must be 1 or 3 for Klondike")

        if scoring_mode not in {"standard", "vegas"}:
            raise ValueError("scoring_mode must be either 'standard' or 'vegas'")

        self.draw_count = draw_count
        self.max_recycles = max_recycles if max_recycles is not None else (3 if draw_count == 3 else None)
        self.recycles_used = 0
        self.scoring_mode = scoring_mode
        self.score = -52 if scoring_mode == "vegas" else 0
        self.moves_made = 0
        self.auto_moves_made = 0

        self.rng = rng
        self.deck = Deck()
        if rng:
            self.deck.shuffle(rng=rng)
        else:
            self.deck.shuffle()

        # Initialize piles
        self.foundations: list[Pile] = [Pile(PileType.FOUNDATION) for _ in range(4)]
        self.tableau: list[Pile] = [Pile(PileType.TABLEAU) for _ in range(7)]
        self.stock = Pile(PileType.STOCK)
        self.waste = Pile(PileType.WASTE)

        self._setup_game()

    def _setup_game(self) -> None:
        """Deal cards to tableau and stock piles."""
        # Deal to tableau: 1 card to first pile, 2 to second, etc.
        for i in range(7):
            for _ in range(i + 1):
                card = self.deck.deal(1)[0]
                self.tableau[i].cards.append(card)
            # Only the top card is face up
            self.tableau[i].face_up_count = 1

        # Remaining cards go to stock
        self.stock.cards = self.deck.cards.copy()
        self.deck.cards.clear()

    def draw_from_stock(self) -> bool:
        """Draw card(s) from stock to waste.

        Returns:
            True if at least one card was drawn, False if stock is empty.
        """
        if not self.stock.cards:
            return False

        cards_to_draw = min(self.draw_count, len(self.stock.cards))
        for _ in range(cards_to_draw):
            card = self.stock.cards.pop()
            self.waste.cards.append(card)

        self.moves_made += 1
        return True

    def can_reset_stock(self) -> bool:
        """Check whether the waste may be recycled back into the stock."""

        if not self.waste.cards or self.stock.cards:
            return False

        if self.max_recycles is None:
            return True

        return self.recycles_used < self.max_recycles

    def reset_stock(self) -> bool:
        """Move all cards from waste back to stock respecting recycle limits."""

        if not self.can_reset_stock():
            return False

        self.stock.cards = list(reversed(self.waste.cards))
        self.waste.cards.clear()
        self.recycles_used += 1
        return True

    def move_to_foundation(self, source_pile: Pile, foundation_index: int, *, register_move: bool = True) -> bool:
        """Move top card from source pile to foundation.

        Args:
            source_pile: The pile to move from.
            foundation_index: Index of the foundation pile (0-3).
            register_move: Whether to count the move towards statistics.

        Returns:
            True if move was successful, False otherwise.
        """
        if not source_pile.cards:
            return False

        if source_pile.pile_type == PileType.FOUNDATION:
            # Foundations only ever receive cards
            return False

        card = source_pile.top_card()
        if card and self.foundations[foundation_index].can_add_to_foundation(card):
            self.foundations[foundation_index].cards.append(source_pile.cards.pop())

            # Update face-up count for tableau piles
            if source_pile.pile_type == PileType.TABLEAU and source_pile.cards:
                source_pile.face_up_count -= 1
                if source_pile.face_up_count < 0:
                    source_pile.face_up_count = 0
                self._reveal_top_card(source_pile)
            elif source_pile.pile_type == PileType.TABLEAU:
                source_pile.face_up_count = 0

            if register_move:
                self.moves_made += 1

            self._apply_scoring_on_foundation_move(source_pile.pile_type)

            return True
        return False

    def move_to_tableau(self, source_pile: Pile, tableau_index: int, num_cards: int = 1) -> bool:
        """Move cards from source pile to tableau.

        Args:
            source_pile: The pile to move from.
            tableau_index: Index of the tableau pile (0-6).
            num_cards: Number of cards to move (for tableau to tableau moves).

        Returns:
            True if move was successful, False otherwise.
        """
        if not source_pile.cards or num_cards > len(source_pile.cards):
            return False

        # For waste and foundation, can only move 1 card
        if source_pile.pile_type in (PileType.WASTE, PileType.FOUNDATION) and num_cards != 1:
            return False

        # For tableau, check face-up count
        if source_pile.pile_type == PileType.TABLEAU:
            if num_cards > source_pile.face_up_count:
                return False
        elif source_pile.pile_type == PileType.FOUNDATION and self.scoring_mode == "vegas":
            # Vegas rules do not allow removing cards from the foundation
            return False

        # Get the cards to move
        cards_to_move = source_pile.cards[-num_cards:]
        bottom_card = cards_to_move[0]

        # Check if the move is valid
        if self.tableau[tableau_index].can_add_to_tableau(bottom_card):
            # Move the cards
            self.tableau[tableau_index].cards.extend(cards_to_move)
            self.tableau[tableau_index].face_up_count += num_cards

            # Remove from source
            source_pile.cards = source_pile.cards[:-num_cards]

            # Update source face-up count
            if source_pile.pile_type == PileType.TABLEAU:
                source_pile.face_up_count -= num_cards
                if source_pile.face_up_count < 0:
                    source_pile.face_up_count = 0
                self._reveal_top_card(source_pile)
            elif source_pile.pile_type == PileType.FOUNDATION and self.scoring_mode == "standard":
                # Standard scoring penalises withdrawing from the foundation
                self.score -= 15

            if source_pile.pile_type == PileType.WASTE and self.scoring_mode == "standard":
                self.score += 5

            self.moves_made += 1
            return True
        return False

    def is_won(self) -> bool:
        """Check if the game is won.

        Returns:
            True if all foundations have 13 cards (complete), False otherwise.
        """
        return all(len(foundation.cards) == 13 for foundation in self.foundations)

    def auto_move_to_foundation(self) -> bool:
        """Automatically move any valid cards to foundations.

        Returns:
            True if at least one card was moved, False otherwise.
        """
        moved_any = False
        candidates: list[Pile] = []

        if self.waste.cards:
            candidates.append(self.waste)

        for tableau_pile in self.tableau:
            if tableau_pile.cards and tableau_pile.face_up_count > 0:
                candidates.append(tableau_pile)

        while candidates:
            source = candidates.pop(0)
            moved_from_source = False

            for i in range(4):
                if self.move_to_foundation(source, i, register_move=False):
                    moved_any = True
                    moved_from_source = True
                    break

            if not moved_from_source:
                continue

            if source is self.waste and self.waste.cards:
                if self.waste not in candidates:
                    candidates.insert(0, self.waste)
            elif source is not self.waste and source.cards and source.face_up_count > 0:
                if source not in candidates:
                    candidates.insert(0, source)

        if moved_any:
            self.auto_moves_made += 1

        return moved_any

    def get_state_summary(self) -> dict:
        """Get a summary of the current game state.

        Returns:
            Dictionary containing counts and information about each pile type.
        """
        return {
            "stock": len(self.stock.cards),
            "waste": len(self.waste.cards),
            "foundations": [len(f.cards) for f in self.foundations],
            "tableau": [
                {
                    "total": len(t.cards),
                    "face_up": t.face_up_count,
                    "face_down": len(t.cards) - t.face_up_count,
                }
                for t in self.tableau
            ],
            "draw_count": self.draw_count,
            "score": self.score,
            "moves_made": self.moves_made,
            "auto_moves": self.auto_moves_made,
            "recycles_used": self.recycles_used,
            "recycles_remaining": None if self.max_recycles is None else max(self.max_recycles - self.recycles_used, 0),
            "scoring_mode": self.scoring_mode,
        }

    def _apply_scoring_on_foundation_move(self, source_type: PileType) -> None:
        """Adjust the score for a successful move to a foundation."""

        if self.scoring_mode == "vegas":
            self.score += 5
            return

        if source_type == PileType.WASTE or source_type == PileType.TABLEAU:
            self.score += 10

    def _reveal_top_card(self, pile: Pile) -> None:
        """Flip the next tableau card face up and apply scoring if relevant."""

        if pile.pile_type != PileType.TABLEAU:
            return

        if not pile.cards:
            pile.face_up_count = 0
            return

        if pile.face_up_count == 0:
            pile.face_up_count = 1
            if self.scoring_mode == "standard":
                self.score += 5
