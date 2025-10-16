"""High-level helpers for working with :class:`~common.profile.PlayerProfile` instances.

The :mod:`common.profile` module implements the data structures that persist
player progress.  This helper module wraps those primitives with convenience
methods tailored for command-line launchers and individual games.  It provides
a global profile service that lazily loads a profile at startup, exposes
profile management utilities (selection, rename, reset), and offers a
``GameSession`` helper that automatically records experience and playtime when
games finish.
"""

from __future__ import annotations

import pathlib
import time
from dataclasses import dataclass, field
from datetime import date
from typing import Dict, List, Optional

from common.profile import PlayerProfile, get_default_profile_dir, load_or_create_profile


class ProfileServiceError(RuntimeError):
    """Raised when a profile management operation cannot be completed."""


@dataclass
class GameSession:
    """Track metadata for a single play session and record results on completion."""

    service: "ProfileService"
    game_id: str
    start_time: float = field(default_factory=time.perf_counter)
    _completed: bool = field(default=False, init=False, repr=False)

    def complete(
        self,
        *,
        result: str,
        experience: int = 0,
        metadata: Optional[Dict[str, object]] = None,
        playtime_override: Optional[float] = None,
    ) -> List[str]:
        """Finalize the session and record its outcome in the active profile.

        Args:
            result: ``"win"``, ``"loss"``, or ``"draw"`` depending on the outcome.
            experience: Optional experience to award for the session.
            metadata: Optional game-specific metrics (perfect game flags, etc.).
            playtime_override: Explicit playtime in seconds; otherwise elapsed time
                since the session started is used.

        Returns:
            A list of achievement identifiers that were unlocked.

        Raises:
            ProfileServiceError: If ``complete`` is invoked more than once.
        """

        if self._completed:
            raise ProfileServiceError("Session has already been completed.")

        playtime = playtime_override if playtime_override is not None else time.perf_counter() - self.start_time
        unlocked = self.service.record_game(
            self.game_id,
            result=result,
            playtime=playtime,
            experience=experience,
            metadata=metadata,
        )
        self._completed = True
        return unlocked

    # Allow ``with profile_service.start_session(...) as session`` usage.
    def __enter__(self) -> "GameSession":
        return self

    def __exit__(self, exc_type, exc, exc_tb) -> None:
        # If the session exits because of an exception we simply leave it unrecorded.
        # Callers explicitly decide when to persist a result via ``complete``.
        return None


class ProfileService:
    """Manage player profiles and expose convenience helpers for games."""

    def __init__(
        self,
        *,
        profile_dir: Optional[pathlib.Path] = None,
        default_player_id: str = "default",
        default_display_name: str = "Player",
    ) -> None:
        self.profile_dir = profile_dir or get_default_profile_dir()
        self.profile_dir.mkdir(parents=True, exist_ok=True)
        self._profile_cache: Dict[str, PlayerProfile] = {}
        self._active_profile_id = default_player_id
        self._active_profile = self._load_profile(default_player_id, default_display_name)
        # Ensure the profile is persisted immediately so it appears in listings.
        self.save_active_profile()

    @property
    def active_profile(self) -> PlayerProfile:
        """Return the currently selected profile."""

        return self._active_profile

    def _profile_path(self, player_id: str) -> pathlib.Path:
        return self.profile_dir / f"{player_id}.json"

    def _load_profile(self, player_id: str, display_name: str) -> PlayerProfile:
        profile = load_or_create_profile(player_id, display_name, self.profile_dir)
        self._profile_cache[player_id] = profile
        self._active_profile_id = player_id
        self._active_profile = profile
        return profile

    def save_active_profile(self) -> None:
        """Persist the active profile to disk."""

        self._active_profile.save(self._profile_path(self._active_profile_id))

    def list_profiles(self) -> List[str]:
        """Return sorted profile identifiers stored in ``profile_dir``."""

        available = {path.stem for path in self.profile_dir.glob("*.json")}
        available.add(self._active_profile_id)
        return sorted(available)

    def select_profile(self, player_id: str, display_name: Optional[str] = None) -> PlayerProfile:
        """Load ``player_id`` and mark it as the active profile."""

        player_id = player_id.strip()
        if not player_id:
            raise ProfileServiceError("Player identifier cannot be empty.")

        display_input = display_name.strip() if display_name else ""
        display = display_input or player_id.title()
        if player_id in self._profile_cache:
            profile = self._profile_cache[player_id]
            profile.display_name = display
            self._active_profile_id = player_id
            self._active_profile = profile
        else:
            profile = self._load_profile(player_id, display)

        self.save_active_profile()
        return profile

    def rename_active_profile(self, new_player_id: str, new_display_name: Optional[str] = None) -> PlayerProfile:
        """Rename the active profile both on disk and in memory."""

        new_player_id = new_player_id.strip()
        if not new_player_id:
            raise ProfileServiceError("New player identifier cannot be empty.")

        if new_player_id == self._active_profile_id:
            if new_display_name:
                self._active_profile.display_name = new_display_name.strip() or self._active_profile.display_name
                self.save_active_profile()
            return self._active_profile

        new_path = self._profile_path(new_player_id)
        if new_path.exists():
            raise ProfileServiceError(f"Profile '{new_player_id}' already exists.")

        old_path = self._profile_path(self._active_profile_id)
        # Persist the current state before renaming.
        self.save_active_profile()
        if old_path.exists():
            old_path.rename(new_path)

        profile = self._active_profile
        profile.player_id = new_player_id
        if new_display_name:
            profile.display_name = new_display_name.strip() or profile.display_name

        # Update caches and identifiers.
        self._profile_cache.pop(self._active_profile_id, None)
        self._active_profile_id = new_player_id
        self._profile_cache[new_player_id] = profile
        self._active_profile = profile
        self.save_active_profile()
        return profile

    def reset_active_profile(self, *, keep_display_name: bool = True) -> PlayerProfile:
        """Replace the active profile with a fresh instance."""

        display_name = self._active_profile.display_name if keep_display_name else self._active_profile_id.title()
        profile = PlayerProfile(player_id=self._active_profile_id, display_name=display_name)
        self._active_profile = profile
        self._profile_cache[self._active_profile_id] = profile
        self.save_active_profile()
        return profile

    def summary(self) -> str:
        """Return ``PlayerProfile.summary`` for the active profile."""

        return self._active_profile.summary()

    def start_session(self, game_id: str) -> GameSession:
        """Create a :class:`GameSession` helper for ``game_id``."""

        return GameSession(service=self, game_id=game_id)

    def record_game(
        self,
        game_id: str,
        *,
        result: str,
        playtime: float,
        experience: int = 0,
        metadata: Optional[Dict[str, object]] = None,
    ) -> List[str]:
        """Record ``game_id`` using ``PlayerProfile.record_game`` and persist changes."""

        unlocked = self._active_profile.record_game(
            game_id,
            result,
            playtime=playtime,
            experience_gained=experience,
            metadata=metadata,
        )
        self.save_active_profile()
        return unlocked

    def record_daily_challenge_completion(
        self,
        challenge_id: str,
        *,
        when: Optional[date] = None,
    ) -> List[str]:
        """Record the completion of the daily challenge for the active profile."""

        completion_date = when or date.today()
        progress = self._active_profile.daily_challenge_progress
        if progress.is_completed(completion_date):
            return []
        unlocked = self._active_profile.record_daily_challenge(challenge_id, completion_date)
        self.save_active_profile()
        return unlocked


_GLOBAL_PROFILE_SERVICE: Optional[ProfileService] = None


def get_profile_service() -> ProfileService:
    """Return the lazily-instantiated global :class:`ProfileService`."""

    global _GLOBAL_PROFILE_SERVICE
    if _GLOBAL_PROFILE_SERVICE is None:
        _GLOBAL_PROFILE_SERVICE = ProfileService()
    return _GLOBAL_PROFILE_SERVICE


def set_profile_service(service: Optional[ProfileService]) -> None:
    """Override the global profile service (primarily used in tests)."""

    global _GLOBAL_PROFILE_SERVICE
    _GLOBAL_PROFILE_SERVICE = service
