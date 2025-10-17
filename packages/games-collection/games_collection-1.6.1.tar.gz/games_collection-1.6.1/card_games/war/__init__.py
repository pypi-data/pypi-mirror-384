"""War card game module.

This module implements the classic War card game where players compare cards
and the higher card wins the round.
"""

from __future__ import annotations

from .game import WarGame

try:  # pragma: no cover - import guarded for environments without Tkinter
    from .gui import WarGUI, run_app

    __all__ = ["WarGame", "WarGUI", "run_app"]
except ImportError:  # pragma: no cover - GUI dependencies not available
    __all__ = ["WarGame"]
