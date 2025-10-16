"""Smoke tests for GUI preference persistence in enhanced card games."""

from __future__ import annotations

import pytest

from common import SettingsManager

_tk = pytest.importorskip("tkinter")
from tkinter import TclError  # noqa: E402  # Imported after pytest guard

from card_games.hearts.game import HeartsGame, HeartsPlayer  # noqa: E402
from card_games.hearts.gui import HeartsGUI  # noqa: E402
from card_games.spades.gui import SpadesGUI  # noqa: E402


@pytest.fixture
def tk_root():
    """Provide a hidden Tk root window for GUI smoke tests."""

    try:
        root = _tk.Tk()
    except TclError:  # pragma: no cover - depends on system display availability
        pytest.skip("Tkinter display is not available in the test environment")
    root.withdraw()
    yield root
    root.destroy()


def _default_hearts_game() -> HeartsGame:
    """Create a minimal Hearts game instance for GUI testing."""

    players = [
        HeartsPlayer(name="Tester", is_ai=False),
        HeartsPlayer(name="AI West", is_ai=True),
        HeartsPlayer(name="AI North", is_ai=True),
        HeartsPlayer(name="AI East", is_ai=True),
    ]
    return HeartsGame(players)


class TestSpadesPreferences:
    """Validate persistence integration for the Spades GUI."""

    def test_spades_gui_loads_persisted_preferences(self, tk_root, tmp_path):
        """The GUI should respect persisted preference values on launch."""

        manager = SettingsManager(config_dir=tmp_path)
        settings = manager.load_settings(
            "card_games.spades.gui",
            defaults={"theme": "dark", "enable_sounds": True, "enable_animations": True},
        )
        settings.set("theme", "light")
        settings.set("enable_sounds", False)
        settings.set("enable_animations", False)
        manager.save_settings("card_games.spades.gui", settings)

        gui = SpadesGUI(tk_root, player_name="Tester", settings_manager=manager)

        assert gui.config.theme_name == "light"
        assert gui.config.enable_sounds is False
        assert gui.config.enable_animations is False

    def test_spades_gui_updates_preferences(self, tk_root, tmp_path):
        """Updating preferences through the GUI helper should persist them."""

        manager = SettingsManager(config_dir=tmp_path)
        gui = SpadesGUI(tk_root, player_name="Tester", settings_manager=manager)

        gui.update_user_preferences(theme="high_contrast", enable_sounds=False, enable_animations=False)

        stored = manager.load_settings(
            "card_games.spades.gui",
            defaults={"theme": "dark", "enable_sounds": True, "enable_animations": True},
        )
        assert stored.get("theme") == "high_contrast"
        assert stored.get("enable_sounds") is False
        assert stored.get("enable_animations") is False


class TestHeartsPreferences:
    """Validate persistence integration for the Hearts GUI."""

    def test_hearts_gui_loads_persisted_preferences(self, tk_root, tmp_path):
        """Persisted preferences should override the default configuration."""

        manager = SettingsManager(config_dir=tmp_path)
        settings = manager.load_settings(
            "card_games.hearts.gui",
            defaults={"theme": "midnight", "enable_sounds": True, "enable_animations": True},
        )
        settings.set("theme", "light")
        settings.set("enable_sounds", False)
        settings.set("enable_animations", False)
        manager.save_settings("card_games.hearts.gui", settings)

        gui = HeartsGUI(
            tk_root,
            _default_hearts_game(),
            human_index=0,
            enable_sounds=True,
            settings_manager=manager,
        )

        assert gui.config.theme_name == "light"
        assert gui.config.enable_sounds is False
        assert gui.config.enable_animations is False

    def test_hearts_gui_updates_preferences(self, tk_root, tmp_path):
        """The update helper should write changes back to persistent storage."""

        manager = SettingsManager(config_dir=tmp_path)
        gui = HeartsGUI(
            tk_root,
            _default_hearts_game(),
            human_index=0,
            enable_sounds=True,
            settings_manager=manager,
        )

        gui.update_user_preferences(theme="high_contrast", enable_sounds=True, enable_animations=False)

        stored = manager.load_settings(
            "card_games.hearts.gui",
            defaults={"theme": "midnight", "enable_sounds": True, "enable_animations": True},
        )
        assert stored.get("theme") == "high_contrast"
        assert stored.get("enable_sounds") is True
        assert stored.get("enable_animations") is False
