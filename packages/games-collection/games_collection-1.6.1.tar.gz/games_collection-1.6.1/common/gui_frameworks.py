from __future__ import annotations

"""Utility helpers for launching GUIs across multiple frameworks.

This module centralizes detection of supported GUI frameworks (currently
Tkinter and PyQt5) and provides helpers for selecting and launching the
preferred implementation. Games can use these helpers from their entry points
instead of duplicating availability checks and fallback logic.
"""

from typing import Callable, Dict, Iterable, Literal, Optional, Tuple

Framework = Literal["tkinter", "pyqt5"]

try:  # pragma: no cover - runtime availability check
    import tkinter  # noqa: F401

    _TKINTER_AVAILABLE = True
except ImportError:  # pragma: no cover - runtime availability check
    _TKINTER_AVAILABLE = False

try:  # pragma: no cover - runtime availability check
    from PyQt5 import QtWidgets  # noqa: F401

    _PYQT5_AVAILABLE = True
except ImportError:  # pragma: no cover - runtime availability check
    _PYQT5_AVAILABLE = False


def frameworks_available() -> Dict[Framework, bool]:
    """Return a mapping of GUI frameworks to their availability."""

    return {"tkinter": _TKINTER_AVAILABLE, "pyqt5": _PYQT5_AVAILABLE}


def choose_framework(preferred: Optional[Framework] = None) -> Optional[Framework]:
    """Select the best available GUI framework.

    Args:
        preferred: Framework requested by the caller/user.

    Returns:
        The selected framework, or ``None`` when none are available.
    """

    availability = frameworks_available()

    candidates: Iterable[Optional[Framework]] = (
        preferred,
        "pyqt5",
        "tkinter",
    )

    for candidate in candidates:
        if candidate is None:
            continue
        if availability.get(candidate, False):
            return candidate
    return None


def launch_preferred_gui(
    *,
    preferred: Optional[Framework] = None,
    tkinter_launcher: Optional[Callable[[], None]] = None,
    pyqt_launcher: Optional[Callable[[], None]] = None,
) -> Tuple[bool, Optional[Framework]]:
    """Launch a GUI using the best available framework.

    Args:
        preferred: Framework requested by the caller/user.
        tkinter_launcher: Callable that starts the Tkinter GUI (if available).
        pyqt_launcher: Callable that starts the PyQt5 GUI (if available).

    Returns:
        Tuple of (``launched``, ``framework_used``).
    """

    availability = frameworks_available()
    order: list[Framework] = []
    if preferred:
        order.append(preferred)
    order.extend(["pyqt5", "tkinter"])

    seen: set[Framework] = set()
    for candidate in order:
        if candidate in seen:
            continue
        seen.add(candidate)
        if not availability.get(candidate, False):
            continue
        if candidate == "pyqt5" and pyqt_launcher is not None:
            pyqt_launcher()
            return True, "pyqt5"
        if candidate == "tkinter" and tkinter_launcher is not None:
            tkinter_launcher()
            return True, "tkinter"

    return False, None


__all__ = ["Framework", "frameworks_available", "choose_framework", "launch_preferred_gui"]
