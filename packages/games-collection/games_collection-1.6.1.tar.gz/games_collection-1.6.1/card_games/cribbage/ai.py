"""Heuristics and AI decision-making for the Cribbage card game.

This module provides functions for AI players to make strategic decisions,
such as selecting which cards to discard to the crib and choosing the best
card to play during the pegging phase.
"""

from __future__ import annotations

from itertools import combinations
from statistics import mean
from typing import Sequence

MAX_STARTER_SAMPLES = 20
MAX_CRIB_COMBOS = 200

from card_games.common.cards import Card
from card_games.cribbage.game import CribbageGame


def select_discards(hand: Sequence[Card], is_dealer: bool, deck_cards: Sequence[Card]) -> list[Card]:
    """Select two cards to discard to the crib using expected-value heuristics.

    This function evaluates all possible pairs of cards to discard, calculating
    the expected score of the remaining hand and the expected value of the
    crib (either positive or negative, depending on who is the dealer).

    Args:
        hand: The player's current 6-card hand.
        is_dealer: True if the player is the dealer.
        deck_cards: The remaining cards in the deck to sample from.

    Returns:
        A list containing the two cards selected for discard.
    """
    if len(hand) < 2:
        raise ValueError("Hand must contain at least two cards to discard.")

    best_pair: tuple[Card, Card] | None = None
    best_value = float("-inf")

    for C in combinations(hand, 2):
        discard = C
        keep = [card for card in hand if card not in discard]
        hand_value = _expected_hand_score(keep, deck_cards)
        crib_value = _expected_crib_score(discard, deck_cards)

        total_value = hand_value + (crib_value if is_dealer else -crib_value)

        if total_value > best_value:
            best_value = total_value
            best_pair = discard

    return list(best_pair) if best_pair else list(hand[:2])


def choose_pegging_card(game: CribbageGame, player: int) -> Card | None:
    """Choose the optimal card to play during the pegging phase.

    This function uses a greedy heuristic to evaluate each playable card,
    considering immediate points, potential future points, and risks.

    Args:
        game: The current ``CribbageGame`` instance.
        player: The player for whom to choose a card.

    Returns:
        The best card to play, or None if no card is playable.
    """
    playable = game.legal_plays(player)
    if not playable:
        return None

    best_card: Card = playable[0]
    best_score = float("-inf")
    current_sequence = [card for _, card in game.play_sequence]

    for card in playable:
        new_total = game.play_count + CribbageGame.card_point_value(card)
        sequence = current_sequence + [card]
        points, _ = CribbageGame.pegging_points_for_sequence(sequence, new_total)

        # A simple scoring heuristic to evaluate the move
        score = points * 100.0  # Prioritize immediate points
        if new_total in {15, 31}:
            score += 25  # Bonus for hitting key totals
        score += new_total  # Prefer higher counts to restrict opponent

        # Penalize moves that leave the opponent with easy points
        if 1 <= 31 - new_total <= 10:
            score -= 5
        if 1 <= 15 - new_total <= 10:
            score -= 3

        if score > best_score:
            best_score = score
            best_card = card

    return best_card


def _expected_hand_score(hand: Sequence[Card], deck_cards: Sequence[Card]) -> float:
    """Calculate the expected score of a hand by sampling starter cards."""
    if not deck_cards:
        return 0.0

    starters = deck_cards[:MAX_STARTER_SAMPLES]
    scores = [CribbageGame.score_hand_static(hand, starter) for starter in starters]
    return mean(scores) if scores else 0.0


def _expected_crib_score(discard: Sequence[Card], deck_cards: Sequence[Card]) -> float:
    """Calculate the expected score of a crib by sampling opponent discards."""
    if len(deck_cards) < 3:
        return 0.0

    crib_scores: list[float] = []
    # To avoid performance issues, limit the number of combinations to check
    combo_iter = combinations(deck_cards, 2)
    for i, opp_discards in enumerate(combo_iter):
        if i >= MAX_CRIB_COMBOS:
            break

        remaining_deck = [c for c in deck_cards if c not in opp_discards]
        starters = remaining_deck[:MAX_STARTER_SAMPLES]
        if not starters:
            continue

        crib_cards = list(discard) + list(opp_discards)
        for starter in starters:
            crib_scores.append(CribbageGame.score_hand_static(crib_cards, starter, is_crib=True))

    return mean(crib_scores) if crib_scores else 0.0
