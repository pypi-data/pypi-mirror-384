"""Utilities for configuring per-game soundscapes for card game GUIs.

This module centralises the mapping between game identifiers and the sound
effects that their GUIs should preload. Each GUI can call
``initialize_game_soundscape`` after constructing its ``BaseGUI`` to request a
``SoundManager`` instance that has attempted to load the relevant audio cues.

The helper keeps the integration lightweight: if pygame is unavailable or the
sound assets are missing, it simply returns ``None`` (or the existing manager)
without raising errors so the GUI continues operating silently.

To add a new game's soundscape:
1. Add a new entry to the ``GAME_SOUND_CUES`` dictionary.
2. The key should be the game's identifier (e.g., "solitaire").
3. The value should be a dictionary mapping cue names to sound file names.
4. Place the audio files in a ``sounds`` directory next to the game's GUI module.

Example:
    # In your game's GUI module:
    # self.sound_manager = initialize_game_soundscape(
    #     "my_game",
    #     module_file=__file__,
    #     enable_sounds=True,
    #     existing_manager=self.sound_manager,
    # )
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional

from common.sound_manager import SoundManager, create_sound_manager

# Mapping of game identifiers to the sound cue filenames they expect. The
# filenames are relative to a ``sounds`` directory that lives alongside the
# GUI module for that game. The actual audio files are optional; the helper
# only loads cues that exist on disk.
GAME_SOUND_CUES: Dict[str, Dict[str, str]] = {
    "blackjack": {
        "card_flip": "card_flip.wav",
        "chip_stack": "chip_stack.wav",
        "dealer_bust": "dealer_bust.wav",
        "blackjack": "blackjack.wav",
    },
    "bluff": {
        "card_flip": "card_flip.wav",
        "call_bluff": "call_bluff.wav",
        "successful_bluff": "successful_bluff.wav",
        "round_win": "round_win.wav",
    },
    "bridge": {
        "card_flip": "card_flip.wav",
        "trick_win": "trick_win.wav",
        "contract_made": "contract_made.wav",
    },
    "canasta": {
        "card_flip": "card_flip.wav",
        "meld_success": "meld_success.wav",
        "discard": "discard.wav",
        "round_win": "round_win.wav",
    },
    "crazy_eights": {
        "card_play": "card_play.wav",
        "special_card": "special_card.wav",
        "draw_card": "draw_card.wav",
        "round_win": "round_win.wav",
    },
    "gin_rummy": {
        "card_draw": "card_draw.wav",
        "meld": "meld.wav",
        "knock": "knock.wav",
        "gin": "gin.wav",
    },
    "go_fish": {
        "ask": "ask.wav",
        "go_fish": "go_fish.wav",
        "book_complete": "book_complete.wav",
        "round_win": "round_win.wav",
    },
    "hearts": {
        "card_play": "card_play.wav",
        "trick_win": "trick_win.wav",
        "heart_break": "heart_break.wav",
        "shoot_moon": "shoot_moon.wav",
    },
    "poker": {
        "card_flip": "card_flip.wav",
        "chip_stack": "chip_stack.wav",
        "bet": "bet.wav",
        "showdown": "showdown.wav",
    },
    "solitaire": {
        "card_flip": "card_flip.wav",
        "foundation": "foundation.wav",
        "invalid_move": "invalid_move.wav",
        "win": "win.wav",
    },
    "spades": {
        "card_play": "card_play.wav",
        "trick_win": "trick_win.wav",
        "bid_made": "bid_made.wav",
        "bag_penalty": "bag_penalty.wav",
    },
    "uno": {
        "card_play": "card_play.wav",
        "wild": "wild.wav",
        "skip": "skip.wav",
        "reverse": "reverse.wav",
        "draw_penalty": "draw_penalty.wav",
        "uno": "uno.wav",
        "win": "win.wav",
    },
    "war": {
        "card_flip": "card_flip.wav",
        "battle": "battle.wav",
        "war": "war.wav",
        "round_win": "round_win.wav",
    },
}


def initialize_game_soundscape(
    game_key: str,
    *,
    module_file: str,
    enable_sounds: bool,
    existing_manager: Optional[SoundManager],
) -> Optional[SoundManager]:
    """Create or augment a ``SoundManager`` with the cues for ``game_key``.

    This function finds the appropriate sound cues for a given game and loads
    them into a ``SoundManager``. It gracefully handles cases where sounds are
    disabled, the `pygame` library is not available, or sound files are missing.

    Args:
        game_key: Identifier of the game (e.g., ``"blackjack"``).
        module_file: The ``__file__`` attribute of the calling module, used to
            locate the ``sounds`` directory.
        enable_sounds: A boolean indicating whether the GUI has requested
            audio playback.
        existing_manager: An optional existing ``SoundManager`` instance to
            augment. If not provided, a new one is created.

    Returns:
        A ``SoundManager`` instance initialized with the requested cues, or
        ``None`` if sounds are disabled or `pygame` is unavailable.
    """
    # If sounds are disabled, there's nothing to do.
    if not enable_sounds:
        return existing_manager

    # Determine the directory where sound files are expected to be.
    sounds_dir = Path(module_file).with_name("sounds")
    manager = existing_manager

    # If no sound manager exists, create one.
    if manager is None:
        manager = create_sound_manager(str(sounds_dir) if sounds_dir.exists() else None, enabled=True)
        # If creation fails (e.g., pygame not installed), return None.
        if manager is None:
            return None

    # Get the sound cues for the specified game.
    cues = GAME_SOUND_CUES.get(game_key, {})
    if not cues or not sounds_dir.exists():
        return manager

    # Load each sound cue into the manager.
    for cue, filename in cues.items():
        file_path = sounds_dir / filename
        if file_path.exists():
            manager.add_sound(cue, str(file_path))

    return manager
