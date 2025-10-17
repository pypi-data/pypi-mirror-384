"""Bidding helper for Contract Bridge.

This module implements an auction assistant that understands a handful of
standard bidding conventions. The :class:`BiddingHelper` collaborates with the
core :class:`~card_games.bridge.game.BridgeGame` object to enumerate legal
calls, apply Stayman and Jacoby transfer conventions after no-trump openings,
offer 4NT Blackwood queries when slam is in sight, and choose between natural
and penalty doubles. The helper is intentionally pragmatic—the goal is to
produce sensible, explainable calls that integrate cleanly with both the CLI
and GUI front ends.
"""

from __future__ import annotations

from dataclasses import replace
from typing import Iterable, Optional, Sequence

from card_games.bridge.game import AuctionState, BidSuit, BridgeGame, BridgePlayer, Call, CallType
from card_games.common.cards import Suit


class BiddingHelper:
    """Heuristic bidder that layers conventions on top of natural bidding."""

    def __init__(self, game: BridgeGame) -> None:
        self.game = game

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def choose_call(
        self,
        player: BridgePlayer,
        legal_calls: Sequence[Call],
        history: list[Call],
        state: AuctionState,
    ) -> Call:
        """Select an appropriate call from ``legal_calls``.

        Args:
            player: The bidding player.
            legal_calls: Legal options produced by the game engine.
            history: Complete call history up to this point.
            state: Snapshot of the active auction.

        Returns:
            The chosen call (which must be present in ``legal_calls``).
        """

        if not legal_calls:
            raise ValueError("At least one legal call must be provided")

        partnership = self.game.partnership_for(player)
        hcp = self.game.evaluate_hand(player)
        distribution = self.game._hand_distribution(player.hand)
        last_non_pass = state.last_non_pass_call or self.game._last_non_pass_call(history)
        partner_last_bid = self.game._last_bid_from_partnership(history, partnership)

        redouble_option = self._find_call(legal_calls, CallType.REDOUBLE)
        if redouble_option and hcp >= 14:
            return replace(redouble_option, explanation="Redouble for penalty")

        penalty_double = self._consider_penalty_double(player, legal_calls, state, hcp)
        if penalty_double is not None:
            return penalty_double

        convention_call = self._apply_conventions(
            player,
            legal_calls,
            partner_last_bid,
            hcp,
            distribution,
        )
        if convention_call is not None:
            return convention_call

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

    # ------------------------------------------------------------------
    # Conventions and heuristics
    # ------------------------------------------------------------------
    def _apply_conventions(
        self,
        player: BridgePlayer,
        legal_calls: Sequence[Call],
        partner_last_bid: Optional[Call],
        hcp: int,
        distribution: Iterable[tuple[Suit, int]] | dict[Suit, int],
    ) -> Optional[Call]:
        """Return a conventional call if one is appropriate."""

        if partner_last_bid is None or partner_last_bid.bid is None:
            return None

        bid = partner_last_bid.bid
        # Stayman over 1NT openings.
        if bid.suit == BidSuit.NO_TRUMP and bid.level == 1 and hcp >= 8:
            counts = dict(distribution) if not isinstance(distribution, dict) else distribution
            transfer_call = self._jacoby_transfer(legal_calls, counts)
            if transfer_call is not None:
                return transfer_call
            if self._has_four_card_major(counts):
                stayman = self._find_call(legal_calls, CallType.BID, level=2, suit=BidSuit.CLUBS)
                if stayman is not None:
                    return replace(stayman, explanation="Stayman inquiry")

        # Basic Blackwood over agreed suits when enough strength is present.
        if bid.suit != BidSuit.NO_TRUMP and hcp >= 32:
            blackwood = self._find_call(legal_calls, CallType.BID, level=4, suit=BidSuit.NO_TRUMP)
            if blackwood is not None:
                return replace(blackwood, explanation="Blackwood ace ask")

        return None

    def _has_four_card_major(self, distribution: Iterable[tuple[Suit, int]] | dict[Suit, int]) -> bool:
        """Return ``True`` if ``distribution`` contains a four-card major."""

        items = distribution.items() if isinstance(distribution, dict) else distribution
        for suit, count in items:
            if suit in {Suit.HEARTS, Suit.SPADES} and count >= 4:
                return True
        return False

    def _jacoby_transfer(
        self,
        legal_calls: Sequence[Call],
        distribution: Iterable[tuple[Suit, int]] | dict[Suit, int],
    ) -> Optional[Call]:
        """Return a Jacoby transfer bid when possible."""

        counts = dict(distribution) if not isinstance(distribution, dict) else distribution
        if counts.get(Suit.HEARTS, 0) >= 5:
            transfer = self._find_call(legal_calls, CallType.BID, level=2, suit=BidSuit.DIAMONDS)
            if transfer is not None:
                return replace(transfer, explanation="Jacoby transfer to hearts")
        if counts.get(Suit.SPADES, 0) >= 5:
            transfer = self._find_call(legal_calls, CallType.BID, level=2, suit=BidSuit.HEARTS)
            if transfer is not None:
                return replace(transfer, explanation="Jacoby transfer to spades")
        return None

    def _consider_penalty_double(
        self,
        player: BridgePlayer,
        legal_calls: Sequence[Call],
        state: AuctionState,
        hcp: int,
    ) -> Optional[Call]:
        """Return a penalty double when conditions are met."""

        double_option = self._find_call(legal_calls, CallType.DOUBLE)
        if double_option is None or state.current_bid is None or state.current_bidder is None:
            return None

        if hcp < 15:
            return None

        # Emphasise penalty doubles when opponents push to high levels.
        if state.current_bid.level >= 3:
            return replace(double_option, explanation="Penalty double")
        return None

    # ------------------------------------------------------------------
    # Utility helpers
    # ------------------------------------------------------------------
    def _find_call(
        self,
        legal_calls: Sequence[Call],
        call_type: CallType,
        *,
        level: Optional[int] = None,
        suit: Optional[BidSuit] = None,
    ) -> Optional[Call]:
        """Return the first legal call matching the provided criteria."""

        for option in legal_calls:
            if option.call_type != call_type:
                continue
            if call_type == CallType.BID:
                if option.bid is None:
                    continue
                if level is not None and option.bid.level != level:
                    continue
                if suit is not None and option.bid.suit != suit:
                    continue
            return option
        return None

    def _ensure_legal(self, candidate: Optional[Call], legal_calls: Sequence[Call]) -> Call:
        """Return ``candidate`` if legal, otherwise fall back to a pass."""

        if candidate is not None:
            for option in legal_calls:
                if option.call_type == candidate.call_type and option.bid == candidate.bid:
                    return replace(option, explanation=candidate.explanation)

        # Default to the first pass entry (forced if necessary).
        for option in legal_calls:
            if option.call_type == CallType.PASS:
                return option
        return legal_calls[0]
