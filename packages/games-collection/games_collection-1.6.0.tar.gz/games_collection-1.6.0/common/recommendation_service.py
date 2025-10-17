"""Personalised recommendation engine for launcher and post-game surfaces."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Dict, List, Mapping, Optional, Sequence, Tuple

from common.analytics.game_stats import GameStatistics
from common.profile import PlayerProfile


@dataclass(frozen=True)
class GameDescriptor:
    """Metadata describing a game for recommendation purposes."""

    game_id: str
    name: str
    mechanics: Tuple[str, ...] = ()
    tags: Tuple[str, ...] = ()
    average_duration: Optional[float] = None
    difficulty: Optional[int] = None


@dataclass(frozen=True)
class RecommendationWeights:
    """Weighting configuration for the recommendation algorithm."""

    collaborative: float = 0.5
    challenge: float = 0.2
    content: float = 0.3

    def normalised(self) -> Tuple[float, float, float]:
        """Return weights scaled so their sum equals 1.0."""

        total = self.collaborative + self.challenge + self.content
        if total == 0:
            return 0.0, 0.0, 0.0
        return (
            self.collaborative / total,
            self.challenge / total,
            self.content / total,
        )


@dataclass(frozen=True)
class RecommendationResult:
    """Recommendation payload surfaced to the launcher."""

    game_id: str
    game_name: str
    score: float
    reasons: Tuple[str, ...]
    explanation: str


class RecommendationService:
    """Combine collaborative and content signals to recommend games."""

    def __init__(
        self,
        game_catalog: Mapping[str, GameDescriptor],
        weights: Optional[RecommendationWeights] = None,
        cache_ttl: timedelta = timedelta(hours=4),
    ) -> None:
        self._catalog = dict(game_catalog)
        self._weights = weights or RecommendationWeights()
        self._cache_ttl = cache_ttl

    def recommend(
        self,
        profile: PlayerProfile,
        analytics: Mapping[str, GameStatistics],
        limit: int = 3,
    ) -> List[RecommendationResult]:
        """Return personalised recommendations for a profile."""

        ttl_seconds = self._cache_ttl.total_seconds() if self._cache_ttl else None
        if profile.recommendation_cache.is_valid(ttl_seconds):
            return [
                RecommendationResult(
                    game_id=item["game_id"],
                    game_name=item.get("game_name", item["game_id"]),
                    score=float(item.get("score", 0.0)),
                    reasons=tuple(item.get("reasons", [])),
                    explanation=item.get("explanation", ""),
                )
                for item in profile.recommendation_cache.recommendations
            ][:limit]

        results = self._generate_recommendations(profile, analytics)
        results.sort(key=lambda rec: rec.score, reverse=True)
        limited = results[:limit]
        profile.cache_recommendations(limited)
        return limited

    def record_feedback(self, profile: PlayerProfile, game_id: str, accepted: bool) -> None:
        """Persist feedback about the surfaced recommendation."""

        profile.record_recommendation_feedback(game_id, accepted)

    def _generate_recommendations(
        self,
        profile: PlayerProfile,
        analytics: Mapping[str, GameStatistics],
    ) -> List[RecommendationResult]:
        collaborative_weight, challenge_weight, content_weight = self._weights.normalised()
        popularity = self._calculate_popularity(analytics)
        challenge_completion = self._calculate_challenge_completion(analytics)
        favourites = self._favourite_games(profile)
        favourite_mechanics = self._aggregate_mechanics(favourites)
        average_session = self._average_session_length(profile)

        results: List[RecommendationResult] = []
        for descriptor in self._catalog.values():
            collab_score = self._collaborative_score(descriptor.game_id, popularity)
            challenge_score = challenge_completion.get(descriptor.game_id, 0.0)
            content_score, reasons = self._content_score(
                profile,
                descriptor,
                favourite_mechanics,
                average_session,
            )
            feedback_multiplier = profile.recommendation_cache.feedback_modifier(descriptor.game_id)
            score = (collab_score * collaborative_weight + challenge_score * challenge_weight + content_score * content_weight) * feedback_multiplier

            explanation = self._build_explanation(descriptor, reasons)
            results.append(
                RecommendationResult(
                    game_id=descriptor.game_id,
                    game_name=descriptor.name,
                    score=score,
                    reasons=tuple(reasons),
                    explanation=explanation,
                )
            )

        return results

    def _calculate_popularity(self, analytics: Mapping[str, GameStatistics]) -> Dict[str, float]:
        totals = {gid: self._total_games(stats) for gid, stats in analytics.items()}
        if not totals:
            return {}
        max_total = max(totals.values()) or 1.0
        return {gid: total / max_total for gid, total in totals.items()}

    @staticmethod
    def _total_games(stats: GameStatistics) -> float:
        return sum(player.total_games for player in stats.players.values())

    def _calculate_challenge_completion(self, analytics: Mapping[str, GameStatistics]) -> Dict[str, float]:
        completion: Dict[str, float] = {}
        for game_id, stats in analytics.items():
            if not stats.game_history:
                completion[game_id] = 0.0
                continue
            completed = 0
            for record in stats.game_history:
                metadata = record.get("metadata", {}) if isinstance(record, Mapping) else {}
                if metadata.get("challenge_completed"):
                    completed += 1
            completion[game_id] = completed / len(stats.game_history)
        return completion

    def _favourite_games(self, profile: PlayerProfile) -> List[GameDescriptor]:
        if not profile.game_profiles:
            return []
        ordered = sorted(
            profile.game_profiles.values(),
            key=lambda gp: gp.games_played,
            reverse=True,
        )
        favourites: List[GameDescriptor] = []
        for game_profile in ordered[:3]:
            descriptor = self._catalog.get(game_profile.game_id)
            if descriptor:
                favourites.append(descriptor)
        return favourites

    def _aggregate_mechanics(self, favourites: Sequence[GameDescriptor]) -> Tuple[str, ...]:
        mechanics: List[str] = []
        for descriptor in favourites:
            mechanics.extend(descriptor.mechanics)
        return tuple(dict.fromkeys(mechanics))

    def _average_session_length(self, profile: PlayerProfile) -> Optional[float]:
        total_games = profile.total_games_played()
        if total_games == 0:
            return None
        return profile.total_playtime() / total_games

    def _collaborative_score(self, game_id: str, popularity: Mapping[str, float]) -> float:
        return popularity.get(game_id, 0.0)

    def _content_score(
        self,
        profile: PlayerProfile,
        descriptor: GameDescriptor,
        favourite_mechanics: Sequence[str],
        average_session: Optional[float],
    ) -> Tuple[float, List[str]]:
        mechanics_score, mechanic_reason = self._mechanics_similarity(descriptor, favourite_mechanics)
        duration_score, duration_reason = self._duration_alignment(descriptor, average_session)
        familiarity_score, familiarity_reason = self._familiarity_bonus(profile, descriptor)

        score = mechanics_score * 0.6 + duration_score * 0.2 + familiarity_score * 0.2
        reasons = [reason for reason in (mechanic_reason, duration_reason, familiarity_reason) if reason]
        return score, reasons

    def _mechanics_similarity(
        self,
        descriptor: GameDescriptor,
        favourite_mechanics: Sequence[str],
    ) -> Tuple[float, Optional[str]]:
        candidate = {mechanic.lower() for mechanic in descriptor.mechanics}
        favourites = {mechanic.lower() for mechanic in favourite_mechanics}
        if not candidate or not favourites:
            return 0.0, None
        intersection = candidate.intersection(favourites)
        union = candidate.union(favourites)
        score = len(intersection) / len(union)
        if not intersection:
            return score, None
        primary = next(iter(intersection))
        reason = f"You enjoy {primary} games"
        return score, reason

    def _duration_alignment(
        self,
        descriptor: GameDescriptor,
        average_session: Optional[float],
    ) -> Tuple[float, Optional[str]]:
        if descriptor.average_duration is None or average_session is None:
            return 0.0, None
        difference = abs(descriptor.average_duration - average_session)
        baseline = max(average_session, descriptor.average_duration, 1.0)
        score = max(0.0, 1.0 - difference / baseline)
        if score >= 0.6:
            return score, "Matches your typical session length"
        return score, None

    def _familiarity_bonus(self, profile: PlayerProfile, descriptor: GameDescriptor) -> Tuple[float, Optional[str]]:
        if descriptor.game_id not in profile.game_profiles:
            return 0.3, "Fresh challenge similar to your favourites"
        played = profile.game_profiles[descriptor.game_id]
        if played.games_played == 0:
            return 0.4, "You unlocked this game but haven't explored it yet"
        if played.games_played < 3:
            return 0.5, "You've sampled this before—time to dive deeper"
        return 0.2, None

    def _build_explanation(self, descriptor: GameDescriptor, reasons: Sequence[str]) -> str:
        if reasons:
            return f"{reasons[0]}; try {descriptor.name}"
        return f"Give {descriptor.name} a try to expand your library"
