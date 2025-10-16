"""Tests for CLI utilities."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from common.cli_utils import (
    THEMES,
    ASCIIArt,
    Color,
    CommandHistory,
    InteractiveMenu,
    ProgressBar,
    RichText,
    Spinner,
    TextStyle,
    Theme,
    clear_screen,
    get_terminal_size,
)


class TestTheme:
    """Tests for Theme class."""

    def test_default_theme_creation(self):
        """Test creating a default theme."""
        theme = Theme()
        assert theme.primary == Color.CYAN
        assert theme.secondary == Color.YELLOW
        assert theme.success == Color.GREEN
        assert theme.error == Color.RED

    def test_custom_theme_creation(self):
        """Test creating a custom theme."""
        theme = Theme(
            primary=Color.BLUE,
            secondary=Color.GREEN,
            success=Color.CYAN,
            error=Color.MAGENTA,
        )
        assert theme.primary == Color.BLUE
        assert theme.secondary == Color.GREEN
        assert theme.success == Color.CYAN
        assert theme.error == Color.MAGENTA

    def test_predefined_themes(self):
        """Test predefined themes exist."""
        assert "default" in THEMES
        assert "dark" in THEMES
        assert "light" in THEMES
        assert "ocean" in THEMES
        assert "forest" in THEMES


class TestASCIIArt:
    """Tests for ASCIIArt class."""

    def test_banner_creation(self):
        """Test banner creation."""
        banner = ASCIIArt.banner("Test", color=Color.CYAN, width=20)
        assert "Test" in banner
        assert "=" in banner
        assert len(banner.split("\n")) == 3

    def test_box_creation(self):
        """Test box creation."""
        box = ASCIIArt.box("Test", color=Color.WHITE)
        assert "Test" in box
        assert "┌" in box
        assert "└" in box
        assert "│" in box

    def test_victory_art(self):
        """Test victory ASCII art."""
        art = ASCIIArt.victory(Color.YELLOW)
        assert "VICTORY" in art or "██" in art

    def test_defeat_art(self):
        """Test defeat ASCII art."""
        art = ASCIIArt.defeat(Color.RED)
        assert "GAME" in art or "OVER" in art or "██" in art

    def test_draw_art(self):
        """Test draw ASCII art."""
        art = ASCIIArt.draw(Color.CYAN)
        assert "DRAW" in art or "██" in art


class TestRichText:
    """Tests for RichText class."""

    def test_colorize(self):
        """Test text colorization."""
        text = RichText.colorize("Test", Color.RED)
        assert "Test" in text
        assert Color.RED.value in text

    def test_colorize_with_style(self):
        """Test text colorization with style."""
        text = RichText.colorize("Test", Color.BLUE, TextStyle.BRIGHT)
        assert "Test" in text
        assert Color.BLUE.value in text

    def test_header_levels(self):
        """Test header formatting at different levels."""
        h1 = RichText.header("Header 1", level=1)
        h2 = RichText.header("Header 2", level=2)
        h3 = RichText.header("Header 3", level=3)

        assert "Header 1" in h1
        assert "Header 2" in h2
        assert "Header 3" in h3

    def test_highlight(self):
        """Test text highlighting."""
        text = RichText.highlight("Important")
        assert "Important" in text

    def test_success_message(self):
        """Test success message formatting."""
        msg = RichText.success("Operation successful")
        assert "Operation successful" in msg
        assert "✓" in msg

    def test_error_message(self):
        """Test error message formatting."""
        msg = RichText.error("Operation failed")
        assert "Operation failed" in msg
        assert "✗" in msg

    def test_warning_message(self):
        """Test warning message formatting."""
        msg = RichText.warning("Warning message")
        assert "Warning message" in msg
        assert "⚠" in msg

    def test_info_message(self):
        """Test info message formatting."""
        msg = RichText.info("Info message")
        assert "Info message" in msg
        assert "ℹ" in msg


class TestProgressBar:
    """Tests for ProgressBar class."""

    def test_progress_bar_initialization(self):
        """Test progress bar initialization."""
        bar = ProgressBar(total=10, width=20)
        assert bar.total == 10
        assert bar.current == 0
        assert bar.width == 20

    def test_progress_bar_update(self, capsys):
        """Test progress bar update."""
        bar = ProgressBar(total=10, width=20)
        bar.update(5)
        captured = capsys.readouterr()
        assert "50%" in captured.out

    def test_progress_bar_increment(self, capsys):
        """Test progress bar increment."""
        bar = ProgressBar(total=5, width=20)
        bar.update()
        bar.update()
        captured = capsys.readouterr()
        assert "40%" in captured.out

    def test_progress_bar_completion(self, capsys):
        """Test progress bar completion."""
        bar = ProgressBar(total=10, width=20)
        bar.complete()
        captured = capsys.readouterr()
        assert "100%" in captured.out


class TestSpinner:
    """Tests for Spinner class."""

    def test_spinner_initialization(self):
        """Test spinner initialization."""
        spinner = Spinner(message="Loading")
        assert spinner.message == "Loading"
        assert not spinner.running

    def test_spinner_start(self, capsys):
        """Test spinner start."""
        spinner = Spinner(message="Processing")
        spinner.start()
        assert spinner.running
        captured = capsys.readouterr()
        assert "Processing" in captured.out

    def test_spinner_stop(self, capsys):
        """Test spinner stop."""
        spinner = Spinner(message="Loading")
        spinner.start()
        spinner.stop()
        assert not spinner.running

    def test_spinner_tick(self, capsys):
        """Test spinner tick."""
        spinner = Spinner(message="Working")
        spinner.start()
        spinner.tick()
        captured = capsys.readouterr()
        assert "Working" in captured.out


class TestInteractiveMenu:
    """Tests for InteractiveMenu class."""

    def test_menu_initialization(self):
        """Test menu initialization."""
        options = ["Option 1", "Option 2", "Option 3"]
        menu = InteractiveMenu("Test Menu", options)
        assert menu.title == "Test Menu"
        assert menu.options == options
        assert menu.selected == 0

    @patch("builtins.input", return_value="2")
    def test_numbered_menu_selection(self, mock_input):
        """Test numbered menu selection."""
        options = ["Option 1", "Option 2", "Option 3"]
        menu = InteractiveMenu("Test Menu", options)
        choice = menu.display(allow_arrow_keys=False)
        assert choice == 1

    @patch("builtins.input", side_effect=["invalid", "5", "2"])
    def test_numbered_menu_invalid_input(self, mock_input, capsys):
        """Test numbered menu with invalid input."""
        options = ["Option 1", "Option 2", "Option 3"]
        menu = InteractiveMenu("Test Menu", options)
        choice = menu.display(allow_arrow_keys=False)
        assert choice == 1

    @patch("sys.stdin.isatty", return_value=False)
    def test_menu_no_tty_support(self, mock_isatty):
        """Test menu without TTY support."""
        options = ["Option 1", "Option 2"]
        menu = InteractiveMenu("Test Menu", options)
        assert not menu._has_terminal_support()


class TestCommandHistory:
    """Tests for CommandHistory class."""

    def test_history_initialization(self):
        """Test command history initialization."""
        history = CommandHistory(max_size=10)
        assert len(history.history) == 0
        assert history.position == 0

    def test_add_command(self):
        """Test adding command to history."""
        history = CommandHistory()
        history.add("command1")
        history.add("command2")
        assert len(history.history) == 2
        assert "command1" in history.history
        assert "command2" in history.history

    def test_add_duplicate_command(self):
        """Test adding duplicate command."""
        history = CommandHistory()
        history.add("command1")
        history.add("command1")
        assert len(history.history) == 1

    def test_previous_command(self):
        """Test getting previous command."""
        history = CommandHistory()
        history.add("command1")
        history.add("command2")
        history.add("command3")

        prev = history.previous()
        assert prev == "command3"
        prev = history.previous()
        assert prev == "command2"
        prev = history.previous()
        assert prev == "command1"

    def test_next_command(self):
        """Test getting next command."""
        history = CommandHistory()
        history.add("command1")
        history.add("command2")
        history.add("command3")

        # Go back first
        history.previous()
        history.previous()

        # Then forward
        next_cmd = history.next()
        assert next_cmd == "command3"

    def test_search_history(self):
        """Test searching command history."""
        history = CommandHistory()
        history.add("start game")
        history.add("stop game")
        history.add("start server")

        results = history.search("start")
        assert len(results) == 2
        assert "start game" in results
        assert "start server" in results

    def test_autocomplete_single_match(self):
        """Test autocomplete with single match."""
        history = CommandHistory()
        candidates = ["play", "pause", "stop", "restart"]

        result = history.autocomplete("pla", candidates)
        assert result == "play"

    def test_autocomplete_multiple_matches(self):
        """Test autocomplete with multiple matches."""
        history = CommandHistory()
        candidates = ["play", "player", "playlist"]

        result = history.autocomplete("pla", candidates)
        assert result == "play"  # Common prefix

    def test_autocomplete_no_match(self):
        """Test autocomplete with no match."""
        history = CommandHistory()
        candidates = ["play", "pause", "stop"]

        result = history.autocomplete("xyz", candidates)
        assert result is None

    def test_history_max_size(self):
        """Test history max size limit."""
        history = CommandHistory(max_size=3)
        history.add("command1")
        history.add("command2")
        history.add("command3")
        history.add("command4")

        assert len(history.history) == 3
        assert "command1" not in history.history
        assert "command4" in history.history


class TestUtilityFunctions:
    """Tests for utility functions."""

    @patch("os.system")
    def test_clear_screen(self, mock_system):
        """Test clearing the screen."""
        clear_screen()
        mock_system.assert_called_once()

    @patch("os.get_terminal_size", return_value=MagicMock(columns=100, lines=30))
    def test_get_terminal_size(self, mock_size):
        """Test getting terminal size."""
        width, height = get_terminal_size()
        assert width == 100
        assert height == 30

    @patch("os.get_terminal_size", side_effect=OSError)
    def test_get_terminal_size_fallback(self, mock_size):
        """Test getting terminal size with fallback."""
        width, height = get_terminal_size()
        assert width == 80
        assert height == 24


class TestIntegration:
    """Integration tests for CLI utilities."""

    def test_themed_menu(self):
        """Test menu with custom theme."""
        theme = THEMES["ocean"]
        options = ["Option 1", "Option 2"]
        menu = InteractiveMenu("Test Menu", options, theme=theme)
        assert menu.theme == theme

    def test_progress_with_theme(self, capsys):
        """Test progress bar with custom theme."""
        theme = THEMES["forest"]
        bar = ProgressBar(total=10, width=20, theme=theme)
        bar.update(5)
        captured = capsys.readouterr()
        assert "50%" in captured.out

    def test_rich_text_with_theme(self):
        """Test rich text with custom theme."""
        theme = THEMES["dark"]
        success = RichText.success("Test", theme=theme)
        error = RichText.error("Test", theme=theme)
        warning = RichText.warning("Test", theme=theme)

        assert "Test" in success
        assert "Test" in error
        assert "Test" in warning
