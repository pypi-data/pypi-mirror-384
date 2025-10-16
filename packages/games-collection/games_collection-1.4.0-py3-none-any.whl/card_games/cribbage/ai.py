"""Heuristics for Cribbage AI decisions."""

from __future__ import annotations

from itertools import combinations
from statistics import mean
from typing import Sequence

MAX_STARTER_SAMPLES = 20
MAX_CRIB_COMBOS = 200

from card_games.common.cards import Card
from card_games.cribbage.game import CribbageGame


def select_discards(hand: Sequence[Card], is_dealer: bool, deck_cards: Sequence[Card]) -> list[Card]:
    """Select two cards to discard to the crib using simple expected-value heuristics."""

    if len(hand) < 2:
        raise ValueError("Hand must contain at least two cards")

    best_pair: tuple[Card, Card] | None = None
    best_value = float("-inf")

    for idxs in combinations(range(len(hand)), 2):
        discard = (hand[idxs[0]], hand[idxs[1]])
        keep = [card for i, card in enumerate(hand) if i not in idxs]
        hand_value = _expected_hand_score(keep, deck_cards)
        crib_value = _expected_crib_score(discard, deck_cards)
        total = hand_value + (crib_value if is_dealer else -crib_value)
        if total > best_value:
            best_value = total
            best_pair = discard

    return list(best_pair or hand[:2])


def choose_pegging_card(game: CribbageGame, player: int) -> Card | None:
    """Choose a pegging card for ``player`` using greedy heuristics."""

    playable = game.legal_plays(player)
    if not playable:
        return None

    best_card = playable[0]
    best_score = float("-inf")

    current_sequence = [card for _, card in game.play_sequence]

    for card in playable:
        new_total = game.play_count + CribbageGame.card_point_value(card)
        sequence = current_sequence + [card]
        points, _ = CribbageGame.pegging_points_for_sequence(sequence, new_total)

        score = points * 100.0
        if new_total == 31:
            score += 50
        elif new_total == 15:
            score += 25

        score += new_total

        risk_31 = 1 if 1 <= 31 - new_total <= 10 else 0
        risk_15 = 1 if 1 <= 15 - new_total <= 10 else 0
        score -= risk_31 * 5
        score -= risk_15 * 3

        if points == 0:
            score -= CribbageGame.card_point_value(card) * 0.1

        if score > best_score:
            best_score = score
            best_card = card

    return best_card


def _expected_hand_score(hand: Sequence[Card], deck_cards: Sequence[Card]) -> float:
    deck_list = list(deck_cards)
    if not deck_list:
        return 0.0

    starters = deck_list[:MAX_STARTER_SAMPLES]
    scores = [CribbageGame.score_hand_static(hand, starter, is_crib=False) for starter in starters]
    return mean(scores) if scores else 0.0


def _expected_crib_score(discard: Sequence[Card], deck_cards: Sequence[Card]) -> float:
    deck_list = list(deck_cards)
    if len(deck_list) < 3:
        return 0.0

    crib_scores: list[float] = []
    combo_count = 0
    for opp_discards in combinations(deck_list, 2):
        starters = [card for card in deck_list if card not in opp_discards][:MAX_STARTER_SAMPLES]
        if not starters:
            continue
        crib_cards = list(discard) + list(opp_discards)
        for starter in starters:
            crib_scores.append(CribbageGame.score_hand_static(crib_cards, starter, is_crib=True))
        combo_count += 1
        if combo_count >= MAX_CRIB_COMBOS:
            break

    return mean(crib_scores) if crib_scores else 0.0
