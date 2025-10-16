"""Theme support for tic-tac-toe boards.

This module provides themed symbol sets for different occasions and styles.
"""

from __future__ import annotations

from typing import Dict, Tuple

# Define themed symbol sets
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
    """Get the symbols for a given theme.

    Args:
        theme_name: The name of the theme to use.

    Returns:
        A tuple of (player1_symbol, player2_symbol).

    Raises:
        ValueError: If the theme name is not recognized.
    """
    if theme_name not in THEMES:
        raise ValueError(f"Unknown theme: {theme_name}. Available themes: {', '.join(THEMES.keys())}")
    return THEMES[theme_name][:2]


def list_themes() -> str:
    """Generate a list of available themes with descriptions.

    Returns:
        A formatted string listing all available themes.
    """
    lines = ["Available themes:"]
    for name, (sym1, sym2, description) in sorted(THEMES.items()):
        lines.append(f"  {name:12} - {description} ({sym1} vs {sym2})")
    return "\n".join(lines)


def validate_symbols(symbol1: str, symbol2: str) -> bool:
    """Validate that two symbols are distinct and suitable for use.

    Args:
        symbol1: First player's symbol.
        symbol2: Second player's symbol.

    Returns:
        True if the symbols are valid.

    Raises:
        ValueError: If the symbols are invalid.
    """
    if symbol1 == symbol2:
        raise ValueError("Players must use distinct symbols.")
    if not symbol1 or not symbol2:
        raise ValueError("Symbols cannot be empty.")
    if " " in symbol1 or " " in symbol2:
        raise ValueError("Symbols cannot contain spaces.")
    return True
