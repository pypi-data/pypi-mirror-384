"""Scheduling helpers for rotating daily challenges across the games collection."""

from __future__ import annotations

import json
import pathlib
import random
from dataclasses import dataclass
from datetime import date
from typing import Dict, List, Optional, Tuple

from common.challenges import Challenge, ChallengeManager, ChallengePack, DifficultyLevel
from common.profile import get_default_profile_dir


_DIFFICULTY_ROTATION: Tuple[DifficultyLevel, ...] = (
    DifficultyLevel.BEGINNER,
    DifficultyLevel.INTERMEDIATE,
    DifficultyLevel.ADVANCED,
    DifficultyLevel.EXPERT,
)


@dataclass
class DailyChallengeSelection:
    """Container describing a scheduled challenge for a specific date."""

    target_date: date
    pack: ChallengePack
    challenge: Challenge

    def summary(self) -> str:
        """Return a formatted summary of the selection."""

        difficulty_label = self.challenge.difficulty.value.title()
        return f"{self.pack.name}: {self.challenge.title} ({difficulty_label})"


class DailyChallengeScheduler:
    """Select and persist a daily challenge using deterministic rotation."""

    def __init__(
        self,
        manager: ChallengeManager,
        *,
        storage_path: Optional[pathlib.Path] = None,
    ) -> None:
        self._manager = manager
        default_root = get_default_profile_dir().parent
        self._storage_path = storage_path or (default_root / "daily_challenges.json")
        self._schedule: Dict[str, Dict[str, str]] = {}
        self._load_schedule()

    @property
    def storage_path(self) -> pathlib.Path:
        """Return the path used for persisting the schedule."""

        return self._storage_path

    def get_challenge_for_date(self, target: Optional[date] = None) -> DailyChallengeSelection:
        """Return the scheduled challenge for ``target`` (defaults to today)."""

        current_date = target or date.today()
        key = current_date.isoformat()

        stored = self._schedule.get(key)
        if stored:
            pack = self._manager.get_pack(stored.get("pack", ""))
            if pack is not None:
                challenge = pack.get_challenge(stored.get("challenge", ""))
                if challenge is not None:
                    return DailyChallengeSelection(current_date, pack, challenge)

        pack, challenge = self._select_challenge(current_date)
        self._schedule[key] = {"pack": pack.name, "challenge": challenge.id}
        self._save_schedule()
        return DailyChallengeSelection(current_date, pack, challenge)

    def clear_cache(self) -> None:
        """Clear the in-memory schedule (useful for tests)."""

        self._schedule.clear()

    def _load_schedule(self) -> None:
        if not self._storage_path.exists():
            self._schedule = {}
            return

        with self._storage_path.open() as handle:
            try:
                payload = json.load(handle)
            except json.JSONDecodeError:
                payload = {}

        if isinstance(payload, dict):
            self._schedule = {
                key: value
                for key, value in payload.items()
                if isinstance(key, str) and isinstance(value, dict)
            }
        else:
            self._schedule = {}

    def _save_schedule(self) -> None:
        self._storage_path.parent.mkdir(parents=True, exist_ok=True)
        with self._storage_path.open("w") as handle:
            json.dump(self._schedule, handle, indent=2, sort_keys=True)

    def _select_challenge(self, current_date: date) -> Tuple[ChallengePack, Challenge]:
        difficulty = self._determine_difficulty(current_date)
        candidates = self._collect_candidates(difficulty)
        if not candidates:
            # Fallback: use the first difficulty with available challenges.
            for fallback in _DIFFICULTY_ROTATION:
                candidates = self._collect_candidates(fallback)
                if candidates:
                    break
        if not candidates:
            raise RuntimeError("No challenges registered with the challenge manager.")

        rng = random.Random(current_date.toordinal())
        pack_name, challenge = rng.choice(candidates)
        pack = self._manager.get_pack(pack_name)
        if pack is None:
            raise RuntimeError(f"Challenge pack '{pack_name}' is no longer registered.")
        return pack, challenge

    def _determine_difficulty(self, current_date: date) -> DifficultyLevel:
        rotation_index = current_date.toordinal() % len(_DIFFICULTY_ROTATION)
        return _DIFFICULTY_ROTATION[rotation_index]

    def _collect_candidates(self, difficulty: DifficultyLevel) -> List[Tuple[str, Challenge]]:
        candidates: List[Tuple[str, Challenge]] = []
        for pack_name in self._manager.list_packs():
            pack = self._manager.get_pack(pack_name)
            if pack is None:
                continue
            candidates.extend((pack_name, challenge) for challenge in pack.get_challenges_by_difficulty(difficulty))
        return candidates

