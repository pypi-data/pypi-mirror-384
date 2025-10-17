"""Internationalization (i18n) support for games.

This module provides a robust and easy-to-use system for translating and
localizing game interfaces. It is built around a central `TranslationManager`
that handles loading language files, translating text, and managing different
languages.

Key features include:
- **JSON-based Translations**: Language files are stored in a simple JSON
  format, making them easy to create and edit.
- **Fallback Language**: A fallback language (English, by default) is used if
  a translation is not found in the current language.
- **Dynamic Language Switching**: The application's language can be changed at
  runtime.
- **Singleton Manager**: A global `TranslationManager` instance is used to
  ensure consistency across the application.
- **Shorthand Function**: A convenient `_()` function is provided as a
  shorthand for `get_translation_manager().translate()`, which is a common
  convention in i18n systems.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional


class TranslationManager:
    """A manager for handling translations and localization.

    This class is responsible for loading translation files, retrieving
    translated strings, and managing the current language of the application.

    Attributes:
        current_language: The currently active language code (e.g., "en", "fr").
        fallback_language: The language to use if a translation is not found
                           in the current language.
        translations: A dictionary that stores the loaded translations for
                      each language.
    """

    def __init__(self, translations_dir: Optional[Path] = None, default_language: str = "en") -> None:
        """Initialize the translation manager.

        Args:
            translations_dir: The directory where the translation files (JSON)
                              are located. If not provided, it defaults to a
                              "translations" subdirectory.
            default_language: The default language to use for the application.
        """
        self.translations_dir = translations_dir or Path(__file__).parent / "translations"
        self.current_language = default_language
        self.fallback_language = "en"
        self.translations: Dict[str, Dict[str, str]] = {}

        # Load the default language upon initialization
        self._load_language(default_language)

    def _load_language(self, language: str) -> bool:
        """Load the translation file for a given language.

        Args:
            language: The language code of the translation file to load.

        Returns:
            True if the language was loaded successfully, False otherwise.
        """
        if language in self.translations:
            return True

        filepath = self.translations_dir / f"{language}.json"
        if not filepath.exists():
            # If the default English file is missing, create it with default
            # translations.
            if language == "en":
                self.translations[language] = self._get_default_translations()
                return True
            return False

        try:
            with filepath.open("r", encoding="utf-8") as f:
                self.translations[language] = json.load(f)
            return True
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Could not load translations for {language}: {e}")
            return False

    def _get_default_translations(self) -> Dict[str, str]:
        """Provide a set of default English translations as a fallback.

        Returns:
            A dictionary of default English translations.
        """
        return {
            # Common UI elements
            "ok": "OK",
            "cancel": "Cancel",
            "yes": "Yes",
            "no": "No",
            "save": "Save",
            "load": "Load",
            "quit": "Quit",
            "new_game": "New Game",
            "settings": "Settings",
            "help": "Help",
            "about": "About",
            "close": "Close",
            # Game elements
            "player": "Player",
            "score": "Score",
            "turn": "Turn",
            "winner": "Winner",
            "game_over": "Game Over",
            "your_turn": "Your Turn",
            "thinking": "Thinking...",
            "invalid_move": "Invalid Move",
            # Settings
            "volume": "Volume",
            "theme": "Theme",
            "language": "Language",
            "difficulty": "Difficulty",
            "easy": "Easy",
            "medium": "Medium",
            "hard": "Hard",
            # Accessibility
            "high_contrast": "High Contrast",
            "screen_reader": "Screen Reader",
            "keyboard_shortcuts": "Keyboard Shortcuts",
        }

    def translate(self, key: str, **kwargs: Any) -> str:
        """Translate a given key into the current language.

        If the key is not found in the current language, it will try the
        fallback language. If it's still not found, the key itself is
        returned.

        Args:
            key: The translation key to look up.
            **kwargs: Optional keyword arguments for string formatting.

        Returns:
            The translated string, or the key if no translation is found.
        """
        # First, try to find the translation in the current language
        if self.current_language in self.translations:
            text = self.translations[self.current_language].get(key)
            if text:
                return text.format(**kwargs) if kwargs else text

        # If not found, try the fallback language
        if self.fallback_language != self.current_language:
            if self.fallback_language in self.translations:
                text = self.translations[self.fallback_language].get(key)
                if text:
                    return text.format(**kwargs) if kwargs else text

        # If no translation is found in either language, return the key
        return key

    def set_language(self, language: str) -> bool:
        """Set the current language for the application.

        Args:
            language: The language code to set as the current language.

        Returns:
            True if the language was set successfully, False otherwise.
        """
        if self._load_language(language):
            self.current_language = language
            return True
        return False

    def get_available_languages(self) -> list[str]:
        """Get a list of all available languages.

        This is determined by the JSON files present in the translations
        directory.

        Returns:
            A sorted list of available language codes.
        """
        languages = ["en"]  # English is always available as a fallback

        if self.translations_dir.exists():
            for filepath in self.translations_dir.glob("*.json"):
                lang_code = filepath.stem
                if lang_code not in languages:
                    languages.append(lang_code)

        return sorted(languages)

    def add_translation(self, language: str, key: str, value: str) -> None:
        """Add or update a translation in memory.

        Args:
            language: The language code for the translation.
            key: The translation key.
            value: The translated string.
        """
        if language not in self.translations:
            self.translations[language] = {}
        self.translations[language][key] = value

    def save_translations(self, language: str) -> bool:
        """Save the translations for a given language to a JSON file.

        Args:
            language: The language code of the translations to save.

        Returns:
            True if the translations were saved successfully, False otherwise.
        """
        if language not in self.translations:
            return False

        self.translations_dir.mkdir(parents=True, exist_ok=True)
        filepath = self.translations_dir / f"{language}.json"

        try:
            with filepath.open("w", encoding="utf-8") as f:
                json.dump(self.translations[language], f, indent=2, ensure_ascii=False)
            return True
        except IOError as e:
            print(f"Warning: Could not save translations for {language}: {e}")
            return False

    def get_language_name(self, language: str) -> str:
        """Get the human-readable name for a given language code.

        Args:
            language: The language code (e.g., "en", "es").

        Returns:
            The human-readable name of the language (e.g., "English",
            "Español").
        """
        language_names = {
            "en": "English",
            "es": "Español",
            "fr": "Français",
            "de": "Deutsch",
            "it": "Italiano",
            "pt": "Português",
            "ru": "Русский",
            "ja": "日本語",
            "zh": "中文",
            "ko": "한국어",
            "ar": "العربية",
        }
        return language_names.get(language, language.upper())


# A global instance of the TranslationManager to ensure a single source of
# truth for translations throughout the application.
_translation_manager: Optional[TranslationManager] = None


def get_translation_manager() -> TranslationManager:
    """Get the global singleton instance of the `TranslationManager`.

    This function ensures that a single instance of the `TranslationManager`
    is used throughout the application, providing a consistent state for
    translations.

    Returns:
        The global `TranslationManager` instance.
    """
    global _translation_manager
    if _translation_manager is None:
        _translation_manager = TranslationManager()
    return _translation_manager


def _(key: str, **kwargs: Any) -> str:
    """A shorthand function for translating a key.

    This function provides a convenient, concise way to access translations,
    following a common convention in i18n systems (e.g., gettext).

    Args:
        key: The translation key to look up.
        **kwargs: Optional keyword arguments for string formatting.

    Returns:
        The translated string.
    """
    return get_translation_manager().translate(key, **kwargs)


def set_language(language: str) -> bool:
    """A convenience function to set the current application language.

    Args:
        language: The language code to set as the current language.

    Returns:
        True if the language was set successfully, False otherwise.
    """
    return get_translation_manager().set_language(language)


def get_current_language() -> str:
    """A convenience function to get the current application language.

    Returns:
        The current language code.
    """
    return get_translation_manager().current_language
