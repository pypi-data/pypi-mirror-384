"""Gin Rummy card game package."""

from __future__ import annotations

from .game import GinRummyGame, GinRummyPlayer

__all__ = ["GinRummyGame", "GinRummyPlayer"]

# Tkinter GUI ---------------------------------------------------------------
try:  # pragma: no cover - optional dependency
    from .gui import GinRummyGUI, run_app

    __all__ += ["GinRummyGUI", "run_app"]
except ImportError:  # pragma: no cover - tkinter missing
    GinRummyGUI = None  # type: ignore
    run_app = None  # type: ignore

# PyQt5 GUI ----------------------------------------------------------------
try:  # pragma: no cover - optional dependency
    from .gui_pyqt import GinRummyPyQtGUI, run_pyqt_app

    __all__ += ["GinRummyPyQtGUI", "run_pyqt_app"]
except Exception:  # pragma: no cover - PyQt5 missing or unavailable
    GinRummyPyQtGUI = None  # type: ignore
    run_pyqt_app = None  # type: ignore
