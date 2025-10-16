"""Internationalization (i18n) support for games.

This module provides translation and localization support for game interfaces.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional


class TranslationManager:
    """Manager for translations and localization.

    Attributes:
        current_language: Currently active language code.
        fallback_language: Fallback language if translation not found.
        translations: Dictionary of loaded translations.
    """

    def __init__(self, translations_dir: Optional[Path] = None, default_language: str = "en") -> None:
        """Initialize translation manager.

        Args:
            translations_dir: Directory containing translation files.
            default_language: Default language code.
        """
        self.translations_dir = translations_dir or Path(__file__).parent / "translations"
        self.current_language = default_language
        self.fallback_language = "en"
        self.translations: Dict[str, Dict[str, str]] = {}

        # Load default language
        self._load_language(default_language)

    def _load_language(self, language: str) -> bool:
        """Load translation file for a language.

        Args:
            language: Language code to load.

        Returns:
            True if loaded successfully.
        """
        if language in self.translations:
            return True

        filepath = self.translations_dir / f"{language}.json"
        if not filepath.exists():
            # Create default translations directory and file if missing
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
        """Get default English translations.

        Returns:
            Dictionary of default translations.
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
        """Translate a key to the current language.

        Args:
            key: Translation key.
            **kwargs: Optional format parameters.

        Returns:
            Translated string or key if not found.
        """
        # Try current language
        if self.current_language in self.translations:
            text = self.translations[self.current_language].get(key)
            if text:
                return text.format(**kwargs) if kwargs else text

        # Try fallback language
        if self.fallback_language != self.current_language:
            if self.fallback_language in self.translations:
                text = self.translations[self.fallback_language].get(key)
                if text:
                    return text.format(**kwargs) if kwargs else text

        # Return key if no translation found
        return key

    def set_language(self, language: str) -> bool:
        """Set the current language.

        Args:
            language: Language code to set.

        Returns:
            True if language was set successfully.
        """
        if self._load_language(language):
            self.current_language = language
            return True
        return False

    def get_available_languages(self) -> list[str]:
        """Get list of available languages.

        Returns:
            List of language codes.
        """
        languages = ["en"]  # Always include English

        if self.translations_dir.exists():
            for filepath in self.translations_dir.glob("*.json"):
                lang_code = filepath.stem
                if lang_code not in languages:
                    languages.append(lang_code)

        return sorted(languages)

    def add_translation(self, language: str, key: str, value: str) -> None:
        """Add or update a translation.

        Args:
            language: Language code.
            key: Translation key.
            value: Translation value.
        """
        if language not in self.translations:
            self.translations[language] = {}

        self.translations[language][key] = value

    def save_translations(self, language: str) -> bool:
        """Save translations for a language to file.

        Args:
            language: Language code to save.

        Returns:
            True if saved successfully.
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
        """Get human-readable name for a language code.

        Args:
            language: Language code.

        Returns:
            Human-readable language name.
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


# Global translation manager
_translation_manager: Optional[TranslationManager] = None


def get_translation_manager() -> TranslationManager:
    """Get the global translation manager.

    Returns:
        Global TranslationManager instance.
    """
    global _translation_manager
    if _translation_manager is None:
        _translation_manager = TranslationManager()
    return _translation_manager


def _(key: str, **kwargs: Any) -> str:
    """Shorthand function for translation.

    Args:
        key: Translation key.
        **kwargs: Optional format parameters.

    Returns:
        Translated string.
    """
    return get_translation_manager().translate(key, **kwargs)


def set_language(language: str) -> bool:
    """Set the current application language.

    Args:
        language: Language code to set.

    Returns:
        True if language was set successfully.
    """
    return get_translation_manager().set_language(language)


def get_current_language() -> str:
    """Get the current application language.

    Returns:
        Current language code.
    """
    return get_translation_manager().current_language
