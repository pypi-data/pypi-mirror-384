"""Common sound effects manager for all games.

This module provides a cross-platform sound manager using pygame.mixer for
playing sound effects during gameplay. Sounds can be enabled/disabled and
gracefully handle missing sound files or pygame library.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional

# Try to import pygame, but make it optional
try:
    import pygame.mixer

    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False


class SoundManager:
    """Manages sound effects using pygame.mixer.

    This class loads and plays sound files for various game events. If pygame
    is not available or sound files are missing, it fails gracefully.

    Attributes:
        sounds_dir: Path to the directory containing sound files.
        sounds: Dictionary mapping sound types to pygame Sound objects.
        enabled: Whether sound effects are currently enabled.
        volume: Master volume level (0.0 to 1.0).
    """

    def __init__(self, sounds_dir: Optional[str] = None, *, enabled: bool = True, volume: float = 1.0) -> None:
        """Initialize the sound manager.

        Args:
            sounds_dir: Directory path containing sound files (relative or absolute).
            enabled: Whether to enable sound effects on initialization.
            volume: Initial volume level (0.0 to 1.0).
        """
        self.sounds_dir = Path(sounds_dir) if sounds_dir else None
        self.sounds: Dict[str, object] = {}
        self.enabled = enabled and PYGAME_AVAILABLE
        self._volume = max(0.0, min(1.0, volume))

        if PYGAME_AVAILABLE and self.enabled and self.sounds_dir:
            try:
                pygame.mixer.init()
                if self.sounds_dir.exists():
                    self._load_sounds()
            except Exception as e:
                print(f"Warning: Could not initialize pygame mixer: {e}")
                self.enabled = False

    def _load_sounds(self) -> None:
        """Load all sound files from the sounds directory."""
        if not self.sounds_dir or not self.sounds_dir.exists():
            return

        # Load all .wav and .mp3 files from the directory
        for filepath in self.sounds_dir.glob("*.wav"):
            sound_type = filepath.stem
            try:
                self.sounds[sound_type] = pygame.mixer.Sound(str(filepath))
            except Exception as e:
                print(f"Warning: Could not load {filepath.name}: {e}")

        for filepath in self.sounds_dir.glob("*.mp3"):
            sound_type = filepath.stem
            try:
                self.sounds[sound_type] = pygame.mixer.Sound(str(filepath))
            except Exception as e:
                print(f"Warning: Could not load {filepath.name}: {e}")

    def add_sound(self, sound_type: str, filepath: str) -> bool:
        """Add a specific sound file.

        Args:
            sound_type: Type identifier for the sound.
            filepath: Path to the sound file.

        Returns:
            True if sound was loaded successfully.
        """
        if not PYGAME_AVAILABLE or not self.enabled:
            return False

        try:
            self.sounds[sound_type] = pygame.mixer.Sound(filepath)
            return True
        except Exception as e:
            print(f"Warning: Could not load {filepath}: {e}")
            return False

    def play(self, sound_type: str, volume: Optional[float] = None) -> bool:
        """Play a sound effect.

        Args:
            sound_type: Type of sound to play.
            volume: Optional volume override (0.0 to 1.0). Uses master volume if None.

        Returns:
            True if sound was played successfully.
        """
        if not self.enabled or not PYGAME_AVAILABLE or sound_type not in self.sounds:
            return False

        try:
            sound = self.sounds[sound_type]
            vol = volume if volume is not None else self._volume
            vol = max(0.0, min(1.0, vol))
            sound.set_volume(vol)
            sound.play()
            return True
        except Exception:
            # Silently fail if sound playback has issues
            return False

    def stop(self, sound_type: Optional[str] = None) -> None:
        """Stop playing a sound or all sounds.

        Args:
            sound_type: Optional sound type to stop. If None, stops all sounds.
        """
        if not PYGAME_AVAILABLE or not self.enabled:
            return

        try:
            if sound_type and sound_type in self.sounds:
                self.sounds[sound_type].stop()
            elif sound_type is None:
                pygame.mixer.stop()
        except Exception:
            pass

    def set_enabled(self, enabled: bool) -> None:
        """Enable or disable sound effects.

        Args:
            enabled: True to enable sounds, False to disable.
        """
        self.enabled = enabled and PYGAME_AVAILABLE

    def set_volume(self, volume: float) -> None:
        """Set master volume for all sounds.

        Args:
            volume: Volume level (0.0 to 1.0).
        """
        self._volume = max(0.0, min(1.0, volume))

        if not PYGAME_AVAILABLE or not self.enabled:
            return

        for sound in self.sounds.values():
            try:
                sound.set_volume(self._volume)
            except Exception:
                pass

    def get_volume(self) -> float:
        """Get current master volume level.

        Returns:
            Volume level (0.0 to 1.0).
        """
        return self._volume

    def is_available(self) -> bool:
        """Check if sound system is available.

        Returns:
            True if pygame is available and sounds are enabled.
        """
        return PYGAME_AVAILABLE and self.enabled

    def list_sounds(self) -> list[str]:
        """List all loaded sound types.

        Returns:
            List of sound type identifiers.
        """
        return list(self.sounds.keys())


def create_sound_manager(sounds_dir: Optional[str] = None, enabled: bool = True, volume: float = 1.0) -> Optional[SoundManager]:
    """Factory function to create a sound manager.

    Args:
        sounds_dir: Optional directory path for sound files.
        enabled: Whether to enable sound effects.
        volume: Initial volume level (0.0 to 1.0).

    Returns:
        A SoundManager instance if successful, None if pygame is not available.
    """
    if not PYGAME_AVAILABLE:
        return None

    return SoundManager(sounds_dir, enabled=enabled, volume=volume)
