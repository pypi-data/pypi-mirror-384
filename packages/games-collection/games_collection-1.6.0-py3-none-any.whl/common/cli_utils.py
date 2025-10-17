"""Enhanced CLI utilities for terminal-based games.

This module provides colorful ASCII art, rich text formatting, progress indicators,
interactive menus, command history, and theme support for command-line interfaces.
"""

from __future__ import annotations

import os
import sys
from collections import deque
from dataclasses import dataclass
from enum import Enum
from typing import Iterable, Optional

try:
    import colorama
    from colorama import Fore, Style

    colorama.init(autoreset=True)
except ImportError:
    # Fallback to minimal ANSI code shims if colorama is not available
    class _FallbackFore:
        BLACK = "\033[30m"
        RED = "\033[31m"
        GREEN = "\033[32m"
        YELLOW = "\033[33m"
        BLUE = "\033[34m"
        MAGENTA = "\033[35m"
        CYAN = "\033[36m"
        WHITE = "\033[37m"

    class _FallbackStyle:
        RESET_ALL = "\033[0m"
        BRIGHT = "\033[1m"
        NORMAL = "\033[22m"

    Fore = _FallbackFore()  # type: ignore[assignment]
    Style = _FallbackStyle()  # type: ignore[assignment]


# Platform-specific imports for arrow key navigation
if sys.platform == "win32":
    import msvcrt
else:
    import select
    import termios
    import tty


class Color(str, Enum):
    """Color constants for terminal output."""

    BLACK = Fore.BLACK
    RED = Fore.RED
    GREEN = Fore.GREEN
    YELLOW = Fore.YELLOW
    BLUE = Fore.BLUE
    MAGENTA = Fore.MAGENTA
    CYAN = Fore.CYAN
    WHITE = Fore.WHITE
    RESET = Style.RESET_ALL


class TextStyle(str, Enum):
    """Text style constants for terminal output."""

    RESET = Style.RESET_ALL
    BRIGHT = Style.BRIGHT
    DIM = "\033[2m"
    NORMAL = "\033[22m"


@dataclass
class Theme:
    """Color theme for CLI elements."""

    primary: Color = Color.CYAN
    secondary: Color = Color.YELLOW
    success: Color = Color.GREEN
    error: Color = Color.RED
    warning: Color = Color.YELLOW
    info: Color = Color.BLUE
    text: Color = Color.WHITE
    accent: Color = Color.MAGENTA


# Predefined themes
THEMES = {
    "default": Theme(),
    "dark": Theme(
        primary=Color.BLUE,
        secondary=Color.CYAN,
        success=Color.GREEN,
        error=Color.RED,
        warning=Color.YELLOW,
        info=Color.MAGENTA,
        text=Color.WHITE,
        accent=Color.CYAN,
    ),
    "light": Theme(
        primary=Color.BLUE,
        secondary=Color.CYAN,
        success=Color.GREEN,
        error=Color.RED,
        warning=Color.YELLOW,
        info=Color.BLUE,
        text=Color.BLACK,
        accent=Color.MAGENTA,
    ),
    "ocean": Theme(
        primary=Color.CYAN,
        secondary=Color.BLUE,
        success=Color.GREEN,
        error=Color.RED,
        warning=Color.YELLOW,
        info=Color.CYAN,
        text=Color.WHITE,
        accent=Color.BLUE,
    ),
    "forest": Theme(
        primary=Color.GREEN,
        secondary=Color.CYAN,
        success=Color.GREEN,
        error=Color.RED,
        warning=Color.YELLOW,
        info=Color.CYAN,
        text=Color.WHITE,
        accent=Color.GREEN,
    ),
}


class ASCIIArt:
    """Colorful ASCII art templates for game states."""

    @staticmethod
    def banner(text: str, color: Color = Color.CYAN, width: int = 60) -> str:
        """Create a banner with the given text.

        Args:
            text: Text to display in banner.
            color: Color for the banner.
            width: Width of the banner.

        Returns:
            Formatted banner string.
        """
        border = "=" * width
        padded_text = text.center(width)
        return f"{color}{border}\n{padded_text}\n{border}{Style.RESET_ALL}"

    @staticmethod
    def box(text: str, color: Color = Color.WHITE, padding: int = 1) -> str:
        """Create a box around text.

        Args:
            text: Text to box.
            color: Color for the box.
            padding: Padding around text.

        Returns:
            Text in a box.
        """
        lines = text.split("\n")
        max_width = max(len(line) for line in lines)
        width = max_width + 2 * padding

        top = "┌" + "─" * width + "┐"
        bottom = "└" + "─" * width + "┘"
        pad = " " * padding

        boxed_lines = [f"{color}{top}{Style.RESET_ALL}"]
        for line in lines:
            padded = line.ljust(max_width)
            boxed_lines.append(f"{color}│{Style.RESET_ALL}{pad}{padded}{pad}{color}│{Style.RESET_ALL}")
        boxed_lines.append(f"{color}{bottom}{Style.RESET_ALL}")

        return "\n".join(boxed_lines)

    @staticmethod
    def victory(color: Color = Color.YELLOW) -> str:
        """ASCII art for victory.

        Args:
            color: Color for the art.

        Returns:
            Victory ASCII art.
        """
        art = """
 ██╗   ██╗██╗ ██████╗████████╗ ██████╗ ██████╗ ██╗   ██╗
 ██║   ██║██║██╔════╝╚══██╔══╝██╔═══██╗██╔══██╗╚██╗ ██╔╝
 ██║   ██║██║██║        ██║   ██║   ██║██████╔╝ ╚████╔╝
 ╚██╗ ██╔╝██║██║        ██║   ██║   ██║██╔══██╗  ╚██╔╝
  ╚████╔╝ ██║╚██████╗   ██║   ╚██████╔╝██║  ██║   ██║
   ╚═══╝  ╚═╝ ╚═════╝   ╚═╝    ╚═════╝ ╚═╝  ╚═╝   ╚═╝
        """
        return f"{color}{art}{Style.RESET_ALL}"

    @staticmethod
    def defeat(color: Color = Color.RED) -> str:
        """ASCII art for defeat.

        Args:
            color: Color for the art.

        Returns:
            Defeat ASCII art.
        """
        art = """
 ██████╗  █████╗ ███╗   ███╗███████╗     ██████╗ ██╗   ██╗███████╗██████╗
██╔════╝ ██╔══██╗████╗ ████║██╔════╝    ██╔═══██╗██║   ██║██╔════╝██╔══██╗
██║  ███╗███████║██╔████╔██║█████╗      ██║   ██║██║   ██║█████╗  ██████╔╝
██║   ██║██╔══██║██║╚██╔╝██║██╔══╝      ██║   ██║╚██╗ ██╔╝██╔══╝  ██╔══██╗
╚██████╔╝██║  ██║██║ ╚═╝ ██║███████╗    ╚██████╔╝ ╚████╔╝ ███████╗██║  ██║
 ╚═════╝ ╚═╝  ╚═╝╚═╝     ╚═╝╚══════╝     ╚═════╝   ╚═══╝  ╚══════╝╚═╝  ╚═╝
        """
        return f"{color}{art}{Style.RESET_ALL}"

    @staticmethod
    def draw(color: Color = Color.CYAN) -> str:
        """ASCII art for draw/tie.

        Args:
            color: Color for the art.

        Returns:
            Draw ASCII art.
        """
        art = """
██████╗ ██████╗  █████╗ ██╗    ██╗
██╔══██╗██╔══██╗██╔══██╗██║    ██║
██║  ██║██████╔╝███████║██║ █╗ ██║
██║  ██║██╔══██╗██╔══██║██║███╗██║
██████╔╝██║  ██║██║  ██║╚███╔███╔╝
╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝ ╚══╝╚══╝
        """
        return f"{color}{art}{Style.RESET_ALL}"


class RichText:
    """Rich text formatting utilities."""

    @staticmethod
    def colorize(text: str, color: Color, style: Optional[TextStyle] = None) -> str:
        """Colorize text with optional style.

        Args:
            text: Text to colorize.
            color: Color to apply.
            style: Optional text style.

        Returns:
            Colored text.
        """
        style_code = style.value if style else ""
        color_code = color.value if isinstance(color, Color) else color
        return f"{style_code}{color_code}{text}{Style.RESET_ALL}"

    @staticmethod
    def header(text: str, level: int = 1, theme: Theme = THEMES["default"]) -> str:
        """Format text as a header.

        Args:
            text: Header text.
            level: Header level (1-3).
            theme: Color theme.

        Returns:
            Formatted header.
        """
        colors = {1: theme.primary, 2: theme.secondary, 3: theme.text}
        color = colors.get(level, theme.text)
        style = TextStyle.BRIGHT if level == 1 else None
        return RichText.colorize(text, color, style)

    @staticmethod
    def highlight(text: str, theme: Theme = THEMES["default"]) -> str:
        """Highlight important text.

        Args:
            text: Text to highlight.
            theme: Color theme.

        Returns:
            Highlighted text.
        """
        return RichText.colorize(text, theme.accent, TextStyle.BRIGHT)

    @staticmethod
    def success(text: str, theme: Theme = THEMES["default"]) -> str:
        """Format success message.

        Args:
            text: Success message.
            theme: Color theme.

        Returns:
            Formatted success message.
        """
        return f"{theme.success}✓ {text}{Style.RESET_ALL}"

    @staticmethod
    def error(text: str, theme: Theme = THEMES["default"]) -> str:
        """Format error message.

        Args:
            text: Error message.
            theme: Color theme.

        Returns:
            Formatted error message.
        """
        return f"{theme.error}✗ {text}{Style.RESET_ALL}"

    @staticmethod
    def warning(text: str, theme: Theme = THEMES["default"]) -> str:
        """Format warning message.

        Args:
            text: Warning message.
            theme: Color theme.

        Returns:
            Formatted warning message.
        """
        return f"{theme.warning}⚠ {text}{Style.RESET_ALL}"

    @staticmethod
    def info(text: str, theme: Theme = THEMES["default"]) -> str:
        """Format info message.

        Args:
            text: Info message.
            theme: Color theme.

        Returns:
            Formatted info message.
        """
        return f"{theme.info}ℹ {text}{Style.RESET_ALL}"


class ProgressBar:
    """Progress bar for loading states."""

    def __init__(self, total: int, width: int = 40, theme: Theme = THEMES["default"]):
        """Initialize progress bar.

        Args:
            total: Total number of steps.
            width: Width of progress bar.
            theme: Color theme.
        """
        self.total = total
        self.current = 0
        self.width = width
        self.theme = theme

    def update(self, current: Optional[int] = None) -> None:
        """Update progress bar.

        Args:
            current: Current progress value. If None, increment by 1.
        """
        if current is not None:
            self.current = current
        else:
            self.current += 1

        self._render()

    def _render(self) -> None:
        """Render the progress bar."""
        percentage = min(100, int(100 * self.current / self.total))
        filled = int(self.width * self.current / self.total)
        bar = "█" * filled + "░" * (self.width - filled)

        sys.stdout.write(f"\r{self.theme.primary}[{bar}] {percentage}%{Style.RESET_ALL}")
        sys.stdout.flush()

        if self.current >= self.total:
            sys.stdout.write("\n")
            sys.stdout.flush()

    def complete(self) -> None:
        """Mark progress as complete."""
        self.current = self.total
        self._render()


class Spinner:
    """Animated spinner for loading states."""

    FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

    def __init__(self, message: str = "Loading", theme: Theme = THEMES["default"]):
        """Initialize spinner.

        Args:
            message: Message to display.
            theme: Color theme.
        """
        self.message = message
        self.theme = theme
        self.frame_index = 0
        self.running = False

    def start(self) -> None:
        """Start the spinner (single frame for testing)."""
        self.running = True
        self._render()

    def stop(self) -> None:
        """Stop the spinner."""
        self.running = False
        sys.stdout.write("\r" + " " * (len(self.message) + 10) + "\r")
        sys.stdout.flush()

    def _render(self) -> None:
        """Render current frame."""
        frame = self.FRAMES[self.frame_index % len(self.FRAMES)]
        sys.stdout.write(f"\r{self.theme.primary}{frame} {self.message}...{Style.RESET_ALL}")
        sys.stdout.flush()
        self.frame_index += 1

    def tick(self) -> None:
        """Advance to next frame."""
        if self.running:
            self._render()


class InteractiveMenu:
    """Interactive command-line menu with arrow key navigation."""

    def __init__(self, title: str, options: list[str], theme: Theme = THEMES["default"]):
        """Initialize interactive menu.

        Args:
            title: Menu title.
            options: List of menu options.
            theme: Color theme.
        """
        self.title = title
        self.options = options
        self.theme = theme
        self.selected = 0

    def display(self, allow_arrow_keys: bool = True) -> int:
        """Display menu and get user selection.

        Args:
            allow_arrow_keys: Enable arrow key navigation (platform-dependent).

        Returns:
            Index of selected option.
        """
        # For environments without proper terminal support, use numbered menu
        if not allow_arrow_keys or not self._has_terminal_support():
            return self._display_numbered_menu()

        # Try arrow key navigation
        try:
            return self._display_interactive_menu()
        except Exception:
            # Fallback to numbered menu
            return self._display_numbered_menu()

    def _has_terminal_support(self) -> bool:
        """Check if terminal supports interactive features.

        Returns:
            True if terminal supports interactive features.
        """
        if not sys.stdin.isatty():
            return False
        if sys.platform == "win32":
            return True
        try:
            # Check if we can get terminal attributes
            termios.tcgetattr(sys.stdin)
            return True
        except Exception:
            return False

    def _display_numbered_menu(self) -> int:
        """Display numbered menu (fallback).

        Returns:
            Index of selected option.
        """
        print(f"\n{self.theme.primary}{self.title}{Style.RESET_ALL}")
        print(f"{self.theme.secondary}{'─' * 40}{Style.RESET_ALL}")

        for i, option in enumerate(self.options, 1):
            print(f"{self.theme.text}{i}. {option}{Style.RESET_ALL}")

        while True:
            try:
                choice = input(f"\n{self.theme.info}Select option (1-{len(self.options)}): {Style.RESET_ALL}").strip()
                idx = int(choice) - 1
                if 0 <= idx < len(self.options):
                    return idx
                print(f"{self.theme.error}Invalid selection. Please try again.{Style.RESET_ALL}")
            except (ValueError, KeyboardInterrupt):
                print(f"\n{self.theme.error}Invalid input. Please enter a number.{Style.RESET_ALL}")

    def _display_interactive_menu(self) -> int:
        """Display interactive menu with arrow key navigation.

        Returns:
            Index of selected option.
        """
        if sys.platform == "win32":
            return self._display_windows_menu()
        else:
            return self._display_unix_menu()

    def _display_windows_menu(self) -> int:
        """Display menu with arrow keys on Windows.

        Returns:
            Index of selected option.
        """
        while True:
            self._render_menu()

            if msvcrt.kbhit():
                key = msvcrt.getch()
                if key == b"\xe0":  # Arrow key prefix
                    key = msvcrt.getch()
                    if key == b"H":  # Up arrow
                        self.selected = (self.selected - 1) % len(self.options)
                    elif key == b"P":  # Down arrow
                        self.selected = (self.selected + 1) % len(self.options)
                elif key in (b"\r", b"\n"):  # Enter key
                    print("\n")
                    return self.selected

    def _display_unix_menu(self) -> int:
        """Display menu with arrow keys on Unix.

        Returns:
            Index of selected option.
        """
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)

        try:
            tty.setraw(fd)

            while True:
                self._render_menu()

                if select.select([sys.stdin], [], [], 0.1)[0]:
                    ch = sys.stdin.read(1)

                    if ch == "\x1b":  # Escape sequence
                        ch = sys.stdin.read(2)
                        if ch == "[A":  # Up arrow
                            self.selected = (self.selected - 1) % len(self.options)
                        elif ch == "[B":  # Down arrow
                            self.selected = (self.selected + 1) % len(self.options)
                    elif ch in ("\r", "\n"):  # Enter key
                        print("\n")
                        return self.selected
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

    def _render_menu(self) -> None:
        """Render the current menu state."""
        # Clear previous output
        sys.stdout.write("\033[H\033[J")

        print(f"{self.theme.primary}{self.title}{Style.RESET_ALL}")
        print(f"{self.theme.secondary}{'─' * 40}{Style.RESET_ALL}\n")

        for i, option in enumerate(self.options):
            if i == self.selected:
                print(f"{self.theme.accent}▶ {option}{Style.RESET_ALL}")
            else:
                print(f"{self.theme.text}  {option}{Style.RESET_ALL}")

        print(f"\n{self.theme.info}Use ↑/↓ arrows to navigate, Enter to select{Style.RESET_ALL}")


class CommandHistory:
    """Command history with autocomplete support."""

    def __init__(self, max_size: int = 100):
        """Initialize command history.

        Args:
            max_size: Maximum number of commands to store.
        """
        self.history: deque[str] = deque(maxlen=max_size)
        self.position = 0

    def add(self, command: str) -> None:
        """Add command to history.

        Args:
            command: Command to add.
        """
        if command and (not self.history or command != self.history[-1]):
            self.history.append(command)
        self.position = len(self.history)

    def previous(self) -> Optional[str]:
        """Get previous command in history.

        Returns:
            Previous command or None if at beginning.
        """
        if self.position > 0:
            self.position -= 1
            return self.history[self.position]
        return None

    def next(self) -> Optional[str]:
        """Get next command in history.

        Returns:
            Next command or None if at end.
        """
        if self.position < len(self.history) - 1:
            self.position += 1
            return self.history[self.position]
        elif self.position == len(self.history) - 1:
            self.position = len(self.history)
            return ""
        return None

    def search(self, prefix: str) -> list[str]:
        """Search history for commands matching prefix.

        Args:
            prefix: Prefix to search for.

        Returns:
            List of matching commands.
        """
        return [cmd for cmd in self.history if cmd.startswith(prefix)]

    def autocomplete(self, partial: str, candidates: Iterable[str]) -> Optional[str]:
        """Autocomplete partial command.

        Args:
            partial: Partial command.
            candidates: List of valid commands.

        Returns:
            Completed command or None if no match.
        """
        matches = [cmd for cmd in candidates if cmd.startswith(partial)]

        if len(matches) == 1:
            return matches[0]
        elif len(matches) > 1:
            # Find common prefix
            common = os.path.commonprefix(matches)
            if len(common) > len(partial):
                return common
        return None


def clear_screen() -> None:
    """Clear the terminal screen."""
    os.system("cls" if sys.platform == "win32" else "clear")


def get_terminal_size() -> tuple[int, int]:
    """Get terminal size.

    Returns:
        Tuple of (width, height).
    """
    try:
        size = os.get_terminal_size()
        return size.columns, size.lines
    except OSError:
        return 80, 24  # Default size
