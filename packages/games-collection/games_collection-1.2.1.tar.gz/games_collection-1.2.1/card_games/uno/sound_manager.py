"""Sound effects manager for the Uno game.

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
    """

    def __init__(self, sounds_dir: str = "sounds/", *, enabled: bool = True) -> None:
        """Initialize the sound manager.

        Args:
            sounds_dir: Directory path containing sound files (relative or absolute).
            enabled: Whether to enable sound effects on initialization.
        """
        self.sounds_dir = Path(sounds_dir)
        self.sounds: Dict[str, object] = {}
        self.enabled = enabled and PYGAME_AVAILABLE

        if PYGAME_AVAILABLE and self.enabled:
            try:
                pygame.mixer.init()
                self._load_sounds()
            except Exception as e:
                print(f"Warning: Could not initialize pygame mixer: {e}")
                self.enabled = False

    def _load_sounds(self) -> None:
        """Load all sound files from the sounds directory."""
        sound_files = {
            "card_play": "card_play.wav",
            "wild": "wild.wav",
            "skip": "skip.wav",
            "reverse": "reverse.wav",
            "draw_penalty": "draw_penalty.wav",
            "uno": "uno.wav",
            "win": "win.wav",
            "swap": "swap.wav",
            "rotate": "rotate.wav",
            "draw": "draw.wav",
        }

        for sound_type, filename in sound_files.items():
            filepath = self.sounds_dir / filename
            if filepath.exists():
                try:
                    self.sounds[sound_type] = pygame.mixer.Sound(str(filepath))
                except Exception as e:
                    print(f"Warning: Could not load {filename}: {e}")

    def play(self, sound_type: str, volume: float = 1.0) -> None:
        """Play a sound effect.

        Args:
            sound_type: Type of sound to play (e.g., 'card_play', 'uno', 'win').
            volume: Volume level (0.0 to 1.0).
        """
        if not self.enabled or not PYGAME_AVAILABLE or sound_type not in self.sounds:
            return

        try:
            sound = self.sounds[sound_type]
            sound.set_volume(volume)
            sound.play()
        except Exception:
            # Silently fail if sound playback has issues
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
        if not PYGAME_AVAILABLE or not self.enabled:
            return

        for sound in self.sounds.values():
            try:
                sound.set_volume(volume)
            except Exception:
                pass


def create_sound_manager(sounds_dir: Optional[str] = None, enabled: bool = True) -> Optional[SoundManager]:
    """Factory function to create a sound manager.

    Args:
        sounds_dir: Optional directory path for sound files. If None, uses default.
        enabled: Whether to enable sound effects.

    Returns:
        A SoundManager instance if successful, None if pygame is not available.
    """
    if not PYGAME_AVAILABLE:
        return None

    # Default sound directory relative to this module
    if sounds_dir is None:
        sounds_dir = str(Path(__file__).parent / "sounds")

    return SoundManager(sounds_dir, enabled=enabled)
