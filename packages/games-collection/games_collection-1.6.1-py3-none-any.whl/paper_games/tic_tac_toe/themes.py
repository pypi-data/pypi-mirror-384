"""Themed symbol sets for Tic-Tac-Toe boards.

This module provides a collection of themed symbol sets to enhance the visual
experience of the Tic-Tac-Toe game. It includes a variety of themes, from
classic "X" and "O" to emojis, holiday themes, and more.

The module offers functions to retrieve a specific theme, list all available
themes, and validate custom symbols to ensure they are suitable for gameplay.

Constants:
    THEMES: A dictionary mapping theme names to their corresponding symbols
            and descriptions.

Functions:
    get_theme(theme_name): Retrieves the symbols for a given theme.
    list_themes(): Generates a formatted list of all available themes.
    validate_symbols(symbol1, symbol2): Validates that two symbols are
                                        distinct and suitable for use.
"""

from __future__ import annotations

from typing import Dict, Tuple

# A dictionary defining the available themed symbol sets. Each theme includes
# two symbols and a description.
THEMES: Dict[str, Tuple[str, str, str]] = {
    "classic": ("X", "O", "Classic X and O"),
    "hearts": ("♥", "♡", "Hearts and Hollow Hearts"),
    "stars": ("★", "☆", "Stars and Hollow Stars"),
    "circles": ("●", "○", "Filled and Hollow Circles"),
    "squares": ("■", "□", "Filled and Hollow Squares"),
    "chess": ("♔", "♚", "Chess King Pieces"),
    "emoji": ("😀", "😎", "Happy and Cool Emojis"),
    "holiday": ("🎄", "🎁", "Christmas Tree and Gift"),
    "halloween": ("🎃", "👻", "Pumpkin and Ghost"),
    "animals": ("🐱", "🐶", "Cat and Dog"),
    "numbers": ("1", "2", "Numbers 1 and 2"),
    "arrows": ("↑", "↓", "Up and Down Arrows"),
    "music": ("♪", "♫", "Musical Notes"),
    "weather": ("☀", "☁", "Sun and Cloud"),
    "food": ("🍕", "🍔", "Pizza and Burger"),
}


def get_theme(theme_name: str) -> Tuple[str, str]:
    """Retrieves the symbols for a given theme.

    This function looks up the specified theme in the `THEMES` dictionary and
    returns the two symbols associated with it.

    Args:
        theme_name (str): The name of the theme to retrieve.

    Returns:
        Tuple[str, str]: A tuple containing the two symbols for the theme.

    Raises:
        ValueError: If the specified theme name is not found in `THEMES`.
    """
    if theme_name not in THEMES:
        raise ValueError(f"Unknown theme: {theme_name}. Available themes: {', '.join(THEMES.keys())}")
    # Return the first two elements of the theme tuple (the symbols).
    return THEMES[theme_name][:2]


def list_themes() -> str:
    """Generates a human-readable list of all available themes.

    This function iterates through the `THEMES` dictionary and creates a
    formatted string that lists each theme's name, description, and symbols.

    Returns:
        str: A formatted string listing all available themes.
    """
    lines = ["Available themes:"]
    for name, (sym1, sym2, description) in sorted(THEMES.items()):
        lines.append(f"  {name:12} - {description} ({sym1} vs {sym2})")
    return "\n".join(lines)


def validate_symbols(symbol1: str, symbol2: str) -> bool:
    """Validates that two symbols are distinct and suitable for gameplay.

    This function checks that the symbols are not identical, not empty, and do
    not contain spaces, which could interfere with board rendering.

    Args:
        symbol1 (str): The first player's symbol.
        symbol2 (str): The second player's symbol.

    Returns:
        bool: True if the symbols are valid for use in the game.

    Raises:
        ValueError: If the symbols are identical, empty, or contain spaces.
    """
    if symbol1 == symbol2:
        raise ValueError("Players must use distinct symbols.")
    if not symbol1 or not symbol2:
        raise ValueError("Symbols cannot be empty.")
    if " " in symbol1 or " " in symbol2:
        raise ValueError("Symbols cannot contain spaces.")
    return True
