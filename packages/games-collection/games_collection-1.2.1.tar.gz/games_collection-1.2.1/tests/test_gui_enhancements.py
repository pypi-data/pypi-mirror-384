"""Tests for GUI enhancement modules.

This module tests the theme system, sound manager, accessibility features,
internationalization, and keyboard shortcuts.
"""

from __future__ import annotations

import pytest

# Test theme system
from common.themes import ThemeColors, ThemeConfig, ThemeManager, get_theme_manager


class TestThemes:
    """Test theme system."""

    def test_theme_colors_creation(self):
        """Test creating theme colors."""
        colors = ThemeColors(
            background="#FFFFFF",
            foreground="#000000",
            primary="#007BFF",
        )
        assert colors.background == "#FFFFFF"
        assert colors.foreground == "#000000"
        assert colors.primary == "#007BFF"

    def test_theme_config_creation(self):
        """Test creating theme configuration."""
        colors = ThemeColors()
        theme = ThemeConfig(name="test", colors=colors)
        assert theme.name == "test"
        assert theme.colors == colors
        assert theme.font_family == "Helvetica"
        assert theme.font_size == 12

    def test_theme_manager_initialization(self):
        """Test theme manager initialization."""
        manager = ThemeManager()
        assert manager.get_current_theme().name == "light"
        assert "light" in manager.list_themes()
        assert "dark" in manager.list_themes()
        assert "high_contrast" in manager.list_themes()

    def test_theme_manager_set_theme(self):
        """Test setting current theme."""
        manager = ThemeManager()
        assert manager.set_current_theme("dark") is True
        assert manager.get_current_theme().name == "dark"

        # Non-existent theme
        assert manager.set_current_theme("nonexistent") is False

    def test_theme_manager_register_custom_theme(self):
        """Test registering custom theme."""
        manager = ThemeManager()
        colors = ThemeColors(background="#123456")
        theme = ThemeConfig(name="custom", colors=colors)

        manager.register_theme(theme)
        assert "custom" in manager.list_themes()
        assert manager.get_theme("custom").name == "custom"

    def test_theme_manager_create_custom_theme(self):
        """Test creating custom theme from base."""
        manager = ThemeManager()
        custom = manager.create_custom_theme(
            "custom_light",
            base_theme="light",
            color_overrides={"primary": "#FF0000"},
        )

        assert custom.name == "custom_light"
        assert custom.colors.primary == "#FF0000"
        assert custom.colors.background == manager.get_theme("light").colors.background

    def test_theme_manager_create_custom_theme_invalid_base(self):
        """Test creating custom theme with invalid base."""
        manager = ThemeManager()
        with pytest.raises(ValueError):
            manager.create_custom_theme("invalid", base_theme="nonexistent")

    def test_global_theme_manager(self):
        """Test global theme manager singleton."""
        manager1 = get_theme_manager()
        manager2 = get_theme_manager()
        assert manager1 is manager2


# Test sound system
from common.sound_manager import SoundManager, create_sound_manager


class TestSoundManager:
    """Test sound manager."""

    def test_sound_manager_initialization(self):
        """Test sound manager initialization."""
        manager = SoundManager(sounds_dir=None, enabled=False)
        assert not manager.is_available() or manager.enabled is False

    def test_sound_manager_volume_control(self):
        """Test volume control."""
        manager = SoundManager(sounds_dir=None, enabled=False)
        manager.set_volume(0.5)
        assert manager.get_volume() == 0.5

        manager.set_volume(1.5)  # Should clamp to 1.0
        assert manager.get_volume() == 1.0

        manager.set_volume(-0.5)  # Should clamp to 0.0
        assert manager.get_volume() == 0.0

    def test_sound_manager_enable_disable(self):
        """Test enabling/disabling sounds."""
        manager = SoundManager(sounds_dir=None, enabled=False)
        manager.set_enabled(True)
        # enabled might still be False if pygame not available
        manager.set_enabled(False)
        assert manager.enabled is False

    def test_sound_manager_list_sounds(self):
        """Test listing loaded sounds."""
        manager = SoundManager(sounds_dir=None, enabled=False)
        sounds = manager.list_sounds()
        assert isinstance(sounds, list)

    def test_create_sound_manager_factory(self):
        """Test sound manager factory function."""
        manager = create_sound_manager(enabled=False)
        # May be None if pygame not available
        assert manager is None or isinstance(manager, SoundManager)


# Test accessibility
from common.accessibility import AccessibilityManager, get_accessibility_manager


class TestAccessibility:
    """Test accessibility features."""

    def test_accessibility_manager_initialization(self):
        """Test accessibility manager initialization."""
        manager = AccessibilityManager(
            high_contrast=True,
            screen_reader=True,
            focus_indicators=True,
        )
        assert manager.high_contrast is True
        assert manager.screen_reader is True
        assert manager.focus_indicators is True

    def test_accessibility_manager_setters(self):
        """Test accessibility settings."""
        manager = AccessibilityManager()
        manager.set_high_contrast(True)
        assert manager.high_contrast is True

        manager.set_screen_reader(True)
        assert manager.screen_reader is True

        manager.set_focus_indicators(False)
        assert manager.focus_indicators is False

    def test_global_accessibility_manager(self):
        """Test global accessibility manager singleton."""
        manager1 = get_accessibility_manager()
        manager2 = get_accessibility_manager()
        assert manager1 is manager2


# Test i18n
from common.i18n import TranslationManager, _, get_translation_manager, set_language


class TestInternationalization:
    """Test internationalization."""

    def test_translation_manager_initialization(self):
        """Test translation manager initialization."""
        manager = TranslationManager(default_language="en")
        assert manager.current_language == "en"
        assert manager.fallback_language == "en"

    def test_translation_manager_translate(self):
        """Test translation."""
        manager = TranslationManager(default_language="en")
        # Should return key for untranslated strings
        result = manager.translate("unknown_key")
        assert result == "unknown_key"

        # Test with known key
        result = manager.translate("ok")
        assert result in ["OK", "ok"]  # Default translation

    def test_translation_manager_set_language(self):
        """Test setting language."""
        manager = TranslationManager()
        result = manager.set_language("en")
        assert result is True
        assert manager.current_language == "en"

    def test_translation_manager_add_translation(self):
        """Test adding translation."""
        manager = TranslationManager()
        manager.add_translation("test_lang", "hello", "Hola")
        manager.set_language("test_lang")
        assert manager.translate("hello") == "Hola"

    def test_translation_manager_format_params(self):
        """Test translation with format parameters."""
        manager = TranslationManager()
        manager.add_translation("en", "greeting", "Hello {name}!")
        result = manager.translate("greeting", name="World")
        assert result == "Hello World!"

    def test_global_translation_manager(self):
        """Test global translation manager singleton."""
        manager1 = get_translation_manager()
        manager2 = get_translation_manager()
        assert manager1 is manager2

    def test_shorthand_translation_function(self):
        """Test shorthand _ function."""
        result = _("ok")
        assert isinstance(result, str)

    def test_set_language_function(self):
        """Test global set_language function."""
        result = set_language("en")
        assert result is True


# Test keyboard shortcuts
from common.keyboard_shortcuts import KeyboardShortcut, ShortcutManager, get_shortcut_manager


class TestKeyboardShortcuts:
    """Test keyboard shortcuts."""

    def test_keyboard_shortcut_creation(self):
        """Test creating keyboard shortcut."""

        def callback():
            return "executed"

        shortcut = KeyboardShortcut("<Control-n>", callback, "New Game")
        assert shortcut.key == "<Control-n>"
        assert shortcut.description == "New Game"
        assert shortcut.enabled is True

    def test_keyboard_shortcut_trigger(self):
        """Test triggering shortcut."""
        executed = []

        def callback():
            executed.append(True)
            return "done"

        shortcut = KeyboardShortcut("<Control-n>", callback)
        result = shortcut.trigger()
        assert result == "done"
        assert len(executed) == 1

    def test_keyboard_shortcut_enable_disable(self):
        """Test enabling/disabling shortcut."""

        def callback():
            return "executed"

        shortcut = KeyboardShortcut("<Control-n>", callback)
        shortcut.enabled = False
        result = shortcut.trigger()
        assert result is None

    def test_shortcut_manager_initialization(self):
        """Test shortcut manager initialization."""
        manager = ShortcutManager()
        assert len(manager.get_shortcuts()) == 0

    def test_shortcut_manager_register(self):
        """Test registering shortcut."""

        def callback():
            pass

        manager = ShortcutManager()
        manager.register("<Control-n>", callback, "New Game")

        shortcuts = manager.get_shortcuts()
        assert "<Control-n>" in shortcuts
        assert shortcuts["<Control-n>"].description == "New Game"

    def test_shortcut_manager_unregister(self):
        """Test unregistering shortcut."""

        def callback():
            pass

        manager = ShortcutManager()
        manager.register("<Control-n>", callback)
        assert manager.unregister("<Control-n>") is True
        assert "<Control-n>" not in manager.get_shortcuts()

        # Unregister non-existent shortcut
        assert manager.unregister("<Control-x>") is False

    def test_shortcut_manager_enable_disable(self):
        """Test enabling/disabling shortcuts."""

        def callback():
            pass

        manager = ShortcutManager()
        manager.register("<Control-n>", callback)

        assert manager.disable("<Control-n>") is True
        assert not manager.get_shortcuts()["<Control-n>"].enabled

        assert manager.enable("<Control-n>") is True
        assert manager.get_shortcuts()["<Control-n>"].enabled

    def test_shortcut_manager_help_text(self):
        """Test getting help text."""

        def callback():
            pass

        manager = ShortcutManager()
        manager.register("<Control-n>", callback, "New Game")
        manager.register("<Control-q>", callback, "Quit")

        help_text = manager.get_shortcuts_help()
        assert "Keyboard Shortcuts" in help_text
        assert "New Game" in help_text

    def test_shortcut_manager_default_shortcuts(self):
        """Test registering default shortcuts."""

        def dummy():
            pass

        manager = ShortcutManager()
        callbacks = {
            "new_game": dummy,
            "quit": dummy,
            "undo": dummy,
            "help": dummy,
        }

        manager.register_default_shortcuts(callbacks)
        shortcuts = manager.get_shortcuts()

        assert "<Control-n>" in shortcuts
        assert "<Control-q>" in shortcuts
        assert "<Control-z>" in shortcuts
        assert "<F1>" in shortcuts

    def test_global_shortcut_manager(self):
        """Test global shortcut manager singleton."""
        manager1 = get_shortcut_manager()
        manager2 = get_shortcut_manager()
        assert manager1 is manager2


# Test animations (basic structure test since tkinter may not be available)
class TestAnimations:
    """Test animation framework."""

    def test_animation_imports(self):
        """Test that animation module can be imported."""
        from common.animations import Animation, ColorTransitionAnimation, PulseAnimation, SlideAnimation

        assert Animation is not None
        assert PulseAnimation is not None
        assert ColorTransitionAnimation is not None
        assert SlideAnimation is not None
