"""Bidding helper for Contract Bridge, with support for standard conventions.

This module implements an auction assistant that understands a handful of
standard bidding conventions. The ``BiddingHelper`` collaborates with the core
``BridgeGame`` object to enumerate legal calls, apply conventions like Stayman
and Jacoby transfers, and make informed decisions about penalty doubles.

The goal is to produce sensible, explainable calls that can be integrated
with both command-line and graphical user interfaces.
"""

from __future__ import annotations

from dataclasses import replace
from typing import Iterable, Optional, Sequence

from card_games.bridge.game import (
    AuctionState,
    BidSuit,
    BridgeGame,
    BridgePlayer,
    Call,
    CallType,
)
from card_games.common.cards import Suit


class BiddingHelper:
    """A heuristic-based bidder for Contract Bridge.

    This class layers standard bidding conventions on top of natural bidding
    logic to provide more sophisticated and human-like bidding behavior.
    """

    def __init__(self, game: BridgeGame) -> None:
        """Initialize the bidding helper with a game instance."""
        self.game = game

    def choose_call(
        self,
        player: BridgePlayer,
        legal_calls: Sequence[Call],
        history: list[Call],
        state: AuctionState,
    ) -> Call:
        """Select an appropriate call from a list of legal options.

        This method uses a series of checks to determine the best call, from
        applying standard conventions to making natural bids based on hand
        strength and distribution.

        Args:
            player: The player who is currently bidding.
            legal_calls: A sequence of legal calls provided by the game engine.
            history: The complete call history of the auction so far.
            state: A snapshot of the current auction state.

        Returns:
            The chosen call, which is guaranteed to be one of the legal calls.
        """
        if not legal_calls:
            raise ValueError("At least one legal call must be provided.")

        partnership = self.game.partnership_for(player)
        hcp = self.game.evaluate_hand(player)
        distribution = self.game._hand_distribution(player.hand)
        last_non_pass = state.last_non_pass_call or self.game._last_non_pass_call(history)
        partner_last_bid = self.game._last_bid_from_partnership(history, partnership)

        # Prioritize redoubling for penalty if strong enough.
        redouble_option = self._find_call(legal_calls, CallType.REDOUBLE)
        if redouble_option and hcp >= 14:
            return replace(redouble_option, explanation="Redouble for penalty")

        # Consider a penalty double.
        penalty_double = self._consider_penalty_double(player, legal_calls, state, hcp)
        if penalty_double:
            return penalty_double

        # Apply standard bidding conventions.
        convention_call = self._apply_conventions(player, legal_calls, partner_last_bid, hcp, distribution)
        if convention_call:
            return convention_call

        # Fall back to natural bidding logic.
        candidate: Optional[Call] = None
        current_bid = state.current_bid

        if last_non_pass is None:
            candidate = self.game._suggest_opening_call(player, hcp, distribution, current_bid)
        elif last_non_pass.call_type in {CallType.DOUBLE, CallType.REDOUBLE}:
            candidate = Call(player, CallType.PASS)
        elif self.game.partnership_for(last_non_pass.player) == partnership:
            candidate = self.game._suggest_response_call(player, hcp, distribution, last_non_pass, current_bid)
        else:
            double_call = self.game._consider_double_call(player, hcp, history, last_non_pass)
            candidate = double_call or self.game._suggest_overcall_call(player, hcp, distribution, current_bid)

        return self._ensure_legal(candidate, legal_calls)

    def _apply_conventions(
        self,
        player: BridgePlayer,
        legal_calls: Sequence[Call],
        partner_last_bid: Optional[Call],
        hcp: int,
        distribution: Iterable[tuple[Suit, int]] | dict[Suit, int],
    ) -> Optional[Call]:
        """Return a conventional call if one is appropriate."""
        if not partner_last_bid or not partner_last_bid.bid:
            return None

        bid = partner_last_bid.bid
        # Apply Stayman convention over a 1NT opening.
        if bid.suit == BidSuit.NO_TRUMP and bid.level == 1 and hcp >= 8:
            counts = dict(distribution) if not isinstance(distribution, dict) else distribution
            if transfer := self._jacoby_transfer(legal_calls, counts):
                return transfer
            if self._has_four_card_major(counts):
                if stayman := self._find_call(legal_calls, CallType.BID, level=2, suit=BidSuit.CLUBS):
                    return replace(stayman, explanation="Stayman inquiry")

        # Apply Blackwood convention for slam bidding.
        if bid.suit != BidSuit.NO_TRUMP and hcp >= 32:
            if blackwood := self._find_call(legal_calls, CallType.BID, level=4, suit=BidSuit.NO_TRUMP):
                return replace(blackwood, explanation="Blackwood ace ask")

        return None

    def _has_four_card_major(self, distribution: Iterable[tuple[Suit, int]] | dict[Suit, int]) -> bool:
        """Return True if the hand distribution contains a four-card major."""
        items = distribution.items() if isinstance(distribution, dict) else distribution
        return any(count >= 4 for suit, count in items if suit in {Suit.HEARTS, Suit.SPADES})

    def _jacoby_transfer(
        self,
        legal_calls: Sequence[Call],
        distribution: Iterable[tuple[Suit, int]] | dict[Suit, int],
    ) -> Optional[Call]:
        """Return a Jacoby transfer bid if applicable."""
        counts = dict(distribution) if not isinstance(distribution, dict) else distribution
        if counts.get(Suit.HEARTS, 0) >= 5:
            if transfer := self._find_call(legal_calls, CallType.BID, level=2, suit=BidSuit.DIAMONDS):
                return replace(transfer, explanation="Jacoby transfer to hearts")
        if counts.get(Suit.SPADES, 0) >= 5:
            if transfer := self._find_call(legal_calls, CallType.BID, level=2, suit=BidSuit.HEARTS):
                return replace(transfer, explanation="Jacoby transfer to spades")
        return None

    def _consider_penalty_double(
        self,
        player: BridgePlayer,
        legal_calls: Sequence[Call],
        state: AuctionState,
        hcp: int,
    ) -> Optional[Call]:
        """Return a penalty double if the conditions are met."""
        double_option = self._find_call(legal_calls, CallType.DOUBLE)
        if not double_option or not state.current_bid or not state.current_bidder:
            return None

        if hcp >= 15 and state.current_bid.level >= 3:
            return replace(double_option, explanation="Penalty double")
        return None

    def _find_call(
        self,
        legal_calls: Sequence[Call],
        call_type: CallType,
        *,
        level: Optional[int] = None,
        suit: Optional[BidSuit] = None,
    ) -> Optional[Call]:
        """Return the first legal call that matches the provided criteria."""
        for option in legal_calls:
            if option.call_type != call_type:
                continue
            if call_type == CallType.BID:
                if not option.bid:
                    continue
                if level is not None and option.bid.level != level:
                    continue
                if suit is not None and option.bid.suit != suit:
                    continue
            return option
        return None

    def _ensure_legal(self, candidate: Optional[Call], legal_calls: Sequence[Call]) -> Call:
        """Return the candidate call if it's legal, otherwise fall back to a pass."""
        if candidate:
            for option in legal_calls:
                if option.call_type == candidate.call_type and option.bid == candidate.bid:
                    return replace(option, explanation=candidate.explanation)

        # Default to the first pass entry, which may be forced.
        return next(
            (call for call in legal_calls if call.call_type == CallType.PASS),
            legal_calls[0],
        )
