"""A common sound effects manager for all games.

This module provides a robust, cross-platform `SoundManager` that uses the
`pygame.mixer` library to play sound effects during gameplay. It is designed
to be resilient, failing gracefully if `pygame` is not installed or if sound
files are missing.

Key features include:
- **Optional Pygame**: The entire sound system is optional. If `pygame` is not
  found, the `SoundManager` will be disabled, but the game will run without
  errors.
- **Dynamic Sound Loading**: Sounds can be loaded from a specified directory
  or added individually.
- **Volume Control**: Master volume can be set for all sounds, and individual
  sounds can be played with a volume override.
- **Enable/Disable**: Sound effects can be toggled on and off at runtime.

The recommended way to create a `SoundManager` is through the
`create_sound_manager` factory function, which handles the check for `pygame`
availability.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional

# Attempt to import pygame, but treat it as an optional dependency.
# This allows the game to run without sound if pygame is not installed.
try:
    import pygame.mixer

    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False


class SoundManager:
    """A class for managing and playing sound effects using `pygame.mixer`.

    This class handles the loading, playing, and management of sound files for
    various game events. It is designed to fail gracefully, so if `pygame` is
    not available or if sound files are missing, it will simply not play
    sounds, rather than crashing the application.

    Attributes:
        sounds_dir: The path to the directory containing the sound files.
        sounds: A dictionary mapping sound type identifiers (e.g., "click",
                "win") to the loaded `pygame.mixer.Sound` objects.
        enabled: A boolean indicating whether sound effects are currently
                 enabled.
        volume: The master volume level for all sounds, from 0.0 to 1.0.
    """

    def __init__(self, sounds_dir: Optional[str] = None, *, enabled: bool = True, volume: float = 1.0) -> None:
        """Initialize the sound manager.

        Args:
            sounds_dir: The directory path containing the sound files. This
                        can be a relative or absolute path.
            enabled: A flag to enable or disable sound effects upon
                     initialization.
            volume: The initial master volume level, from 0.0 (muted) to 1.0
                    (full volume).
        """
        self.sounds_dir = Path(sounds_dir) if sounds_dir else None
        self.sounds: Dict[str, "pygame.mixer.Sound"] = {}
        self.enabled = enabled and PYGAME_AVAILABLE
        self._volume = max(0.0, min(1.0, volume))

        # Initialize the pygame mixer if it's available and enabled
        if PYGAME_AVAILABLE and self.enabled and self.sounds_dir:
            try:
                pygame.mixer.init()
                if self.sounds_dir.exists():
                    self._load_sounds()
            except Exception as e:
                # If initialization fails, disable sound and log a warning
                print(f"Warning: Could not initialize pygame mixer: {e}")
                self.enabled = False

    def _load_sounds(self) -> None:
        """Load all supported sound files from the specified sounds directory."""
        if not self.sounds_dir or not self.sounds_dir.exists():
            return

        # Load all .wav and .mp3 files from the directory
        for extension in ("*.wav", "*.mp3"):
            for filepath in self.sounds_dir.glob(extension):
                sound_type = filepath.stem
                try:
                    self.sounds[sound_type] = pygame.mixer.Sound(str(filepath))
                except Exception as e:
                    # Log a warning if a specific sound file fails to load
                    print(f"Warning: Could not load {filepath.name}: {e}")

    def add_sound(self, sound_type: str, filepath: str) -> bool:
        """Add a specific sound file to the manager.

        Args:
            sound_type: A unique identifier for the sound (e.g., "explosion").
            filepath: The path to the sound file.

        Returns:
            True if the sound was loaded successfully, False otherwise.
        """
        if not self.is_available():
            return False

        try:
            self.sounds[sound_type] = pygame.mixer.Sound(filepath)
            return True
        except Exception as e:
            print(f"Warning: Could not load sound file {filepath}: {e}")
            return False

    def play(self, sound_type: str, volume: Optional[float] = None) -> bool:
        """Play a sound effect.

        Args:
            sound_type: The identifier of the sound to play.
            volume: An optional volume override for this specific playback,
                    from 0.0 to 1.0. If not provided, the master volume is
                    used.

        Returns:
            True if the sound was played successfully, False otherwise.
        """
        if not self.is_available() or sound_type not in self.sounds:
            return False

        try:
            sound = self.sounds[sound_type]
            # Use the override volume if provided, otherwise use the master volume
            play_volume = volume if volume is not None else self._volume
            play_volume = max(0.0, min(1.0, play_volume))
            sound.set_volume(play_volume)
            sound.play()
            return True
        except Exception:
            # Fail silently if there's an issue during playback
            return False

    def stop(self, sound_type: Optional[str] = None) -> None:
        """Stop playing a specific sound or all sounds.

        Args:
            sound_type: The identifier of the sound to stop. If None, all
                        currently playing sounds will be stopped.
        """
        if not self.is_available():
            return

        try:
            if sound_type and sound_type in self.sounds:
                self.sounds[sound_type].stop()
            elif sound_type is None:
                pygame.mixer.stop()
        except Exception:
            # Fail silently if there's an issue stopping the sound
            pass

    def set_enabled(self, enabled: bool) -> None:
        """Enable or disable all sound effects.

        Args:
            enabled: Set to True to enable sounds, False to disable them.
        """
        self.enabled = enabled and PYGAME_AVAILABLE

    def set_volume(self, volume: float) -> None:
        """Set the master volume for all sounds.

        Args:
            volume: The new volume level, from 0.0 (muted) to 1.0 (full).
        """
        self._volume = max(0.0, min(1.0, volume))

        if not self.is_available():
            return

        # Update the volume of all loaded sounds
        for sound in self.sounds.values():
            try:
                sound.set_volume(self._volume)
            except Exception:
                pass

    def get_volume(self) -> float:
        """Get the current master volume level.

        Returns:
            The current volume level, from 0.0 to 1.0.
        """
        return self._volume

    def is_available(self) -> bool:
        """Check if the sound system is available and enabled.

        Returns:
            True if `pygame` is available and sounds are currently enabled,
            False otherwise.
        """
        return PYGAME_AVAILABLE and self.enabled

    def list_sounds(self) -> list[str]:
        """Get a list of all loaded sound types.

        Returns:
            A list of the string identifiers for all loaded sounds.
        """
        return list(self.sounds.keys())


def create_sound_manager(sounds_dir: Optional[str] = None, enabled: bool = True, volume: float = 1.0) -> Optional[SoundManager]:
    """A factory function to create a `SoundManager` instance.

    This is the recommended way to create a sound manager, as it handles the
    case where `pygame` is not available.

    Args:
        sounds_dir: An optional directory path for the sound files.
        enabled: A flag to enable or disable sound effects.
        volume: The initial master volume level, from 0.0 to 1.0.

    Returns:
        A `SoundManager` instance if `pygame` is available, otherwise `None`.
    """
    if not PYGAME_AVAILABLE:
        return None

    return SoundManager(sounds_dir, enabled=enabled, volume=volume)
