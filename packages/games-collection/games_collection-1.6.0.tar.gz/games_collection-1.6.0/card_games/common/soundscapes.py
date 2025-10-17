"""Utilities for configuring per-game soundscapes for card game GUIs.

This module centralises the mapping between game identifiers and the sound
effects that their GUIs should preload.  Each GUI can call
``initialize_game_soundscape`` after constructing its ``BaseGUI`` to request a
``SoundManager`` instance that has attempted to load the relevant audio cues.

The helper keeps the integration lightweight: if pygame is unavailable or the
sound assets are missing, it simply returns ``None`` (or the existing manager)
without raising errors so the GUI continues operating silently.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional

from common.sound_manager import SoundManager, create_sound_manager

# Mapping of game identifiers to the sound cue filenames they expect.  The
# filenames are relative to a ``sounds`` directory that lives alongside the
# GUI module for that game.  The actual audio files are optional; the helper
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

    Args:
        game_key: Identifier of the game (e.g. ``"blackjack"``).
        module_file: ``__file__`` of the caller so we can locate the sounds
            directory that sits next to the module.
        enable_sounds: Whether the GUI has requested audio playback.
        existing_manager: A sound manager that may have been initialised by
            :class:`common.gui_base.BaseGUI` or the caller.

    Returns:
        A ``SoundManager`` initialised with the requested cues, or ``None`` if
        sounds are disabled or pygame is unavailable.
    """

    if not enable_sounds:
        return existing_manager

    sounds_dir = Path(module_file).with_name("sounds")
    manager = existing_manager

    if manager is None:
        manager = create_sound_manager(str(sounds_dir) if sounds_dir.exists() else None, enabled=True)
        if manager is None:
            return None

    cues = GAME_SOUND_CUES.get(game_key, {})
    if not cues or not sounds_dir.exists():
        return manager

    for cue, filename in cues.items():
        file_path = sounds_dir / filename
        if file_path.exists():
            manager.add_sound(cue, str(file_path))

    return manager
