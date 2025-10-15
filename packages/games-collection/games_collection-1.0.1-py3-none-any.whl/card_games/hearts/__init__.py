"""Hearts card game package."""

from .game import HeartsGame, HeartsPlayer

__all__ = ["HeartsGame", "HeartsPlayer"]

try:  # PyQt5 implementation (preferred)
    from .gui_pyqt import HeartsGUI as HeartsGUIPyQt
    from .gui_pyqt import run_app as run_app_pyqt

    __all__ += ["HeartsGUIPyQt", "run_app_pyqt"]
except (ImportError, RuntimeError):
    pass

try:  # Legacy Tkinter implementation
    from .gui import HeartsGUI, run_app

    __all__ += ["HeartsGUI", "run_app"]
except (ImportError, RuntimeError):
    pass
