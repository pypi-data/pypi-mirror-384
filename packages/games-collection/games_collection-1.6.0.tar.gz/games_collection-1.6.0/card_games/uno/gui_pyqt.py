"""PyQt5-powered graphical interface for the Uno card game.

This module introduces :class:`PyQtUnoInterface`, a widget-based front-end that
mirrors the Tkinter GUI. It renders the scoreboard, action log (with ANSI colour
stripping), and hand controls using native PyQt5 widgets while delegating all
rule enforcement to :class:`card_games.uno.uno.UnoGame`. The interface hooks into
the shared sound manager, keeps UNO declaration state, and uses a nested
:class:`~PyQt5.QtCore.QEventLoop` to synchronously wait for human decisions in a
manner similar to ``wait_variable`` in Tkinter.
"""

from __future__ import annotations

import html
import random
import re
import sys
from typing import Callable, Dict, List, Optional, Sequence

from colorama import Fore, Style

try:  # pragma: no cover - import guard for optional dependency
    from PyQt5.QtCore import QEventLoop, Qt, QTimer, pyqtSignal
    from PyQt5.QtWidgets import (
        QApplication,
        QCheckBox,
        QDialog,
        QGridLayout,
        QGroupBox,
        QHBoxLayout,
        QLabel,
        QMessageBox,
        QPushButton,
        QScrollArea,
        QTextEdit,
        QVBoxLayout,
        QWidget,
    )
except ImportError as exc:  # pragma: no cover - PyQt5 optional dependency
    raise ImportError("PyQt5 is required to use the Uno PyQt interface.") from exc

from common.gui_base_pyqt import BaseGUI, GUIConfig

from .sound_manager import create_sound_manager
from .uno import COLORS, HouseRules, PlayerDecision, UnoCard, UnoGame, UnoPlayer, build_players

# Emojis that match the Tkinter interface so messaging stays consistent.
COLOR_EMOJI = {"red": "🟥", "yellow": "🟨", "green": "🟩", "blue": "🟦", None: "⬜"}

# Regex to strip ANSI escape codes from console-formatted text.
ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")

# Mapping from colorama colours to hex strings for QTextEdit rich text output.
COLOR_HEX: Dict[str, str] = {
    Fore.WHITE: "#f5f5f5",
    Fore.RED: "#ef5350",
    Fore.GREEN: "#66bb6a",
    Fore.YELLOW: "#fdd835",
    Fore.CYAN: "#4dd0e1",
    Fore.MAGENTA: "#ba68c8",
}


def strip_ansi(text: str) -> str:
    """Remove ANSI escape codes from a string."""

    return ANSI_RE.sub("", text)


class PyQtUnoInterface(QWidget, BaseGUI):
    """Bridge the Uno engine with a PyQt5 graphical front-end.

    Implements the UnoInterface protocol without direct inheritance to avoid metaclass conflicts.
    """

    decision_made = pyqtSignal()

    def __init__(
        self,
        players: Sequence[UnoPlayer],
        *,
        parent: Optional[QWidget] = None,
        enable_animations: bool = True,
        enable_sounds: bool = True,
        config: Optional[GUIConfig] = None,
    ) -> None:
        """Initialise the interface and build the widget layout."""

        QWidget.__init__(self, parent)
        gui_config = config or GUIConfig(
            window_title="Card Games - Uno",
            window_width=1180,
            window_height=820,
            enable_sounds=enable_sounds,
            enable_animations=enable_animations,
            theme_name="light",
        )
        BaseGUI.__init__(self, root=self, config=gui_config)
        self.setWindowTitle(gui_config.window_title)
        self.resize(gui_config.window_width, gui_config.window_height)
        self.players = list(players)
        self.game: Optional[UnoGame] = None
        self.enable_animations = gui_config.enable_animations
        self.sound_manager = create_sound_manager(enabled=gui_config.enable_sounds) or self.sound_manager

        self.pending_decision: Optional[PlayerDecision] = None
        self.decision_loop: Optional[QEventLoop] = None
        self.card_buttons: List[QPushButton] = []
        self.score_labels: List[QLabel] = []
        self.uno_checkbox: Optional[QCheckBox] = None

        self._build_layout()
        self._build_scoreboard()
        self.decision_made.connect(self._quit_decision_loop)

    # UnoInterface API -------------------------------------------------
    def set_game(self, game: UnoGame) -> None:
        """Register the active game instance so helper methods can access it."""

        self.game = game
        self.update_status(game)

    def show_heading(self, message: str) -> None:
        """Display a heading message at the top of the window."""

        self.heading_label.setText(strip_ansi(message))
        QApplication.processEvents()

    def show_message(self, message: str, *, color: str = Fore.WHITE, style: str = "") -> None:
        """Append a message to the log widget, respecting colour and emphasis."""

        safe_text = html.escape(strip_ansi(message))
        hex_color = COLOR_HEX.get(color, "#f5f5f5")
        weight = "font-weight:600;" if style == Style.BRIGHT else ""
        html_message = f'<span style="color:{hex_color}; {weight} font-family:"Courier New",monospace;">{safe_text}</span>'
        self.log_widget.append(html_message)
        self.log_widget.verticalScrollBar().setValue(self.log_widget.verticalScrollBar().maximum())
        QApplication.processEvents()

    def show_hand(self, player: UnoPlayer, formatted_cards: Sequence[str]) -> None:
        """Render the player's hand as disabled buttons ready for activation."""

        self._clear_hand_buttons()
        self.hand_info_label.setText("Select a card or choose an action below.")
        self.card_buttons = []

        max_columns = 5
        for index, label in enumerate(formatted_cards):
            button = QPushButton(strip_ansi(label))
            button.setEnabled(False)
            button.setMinimumWidth(140)
            button.clicked.connect(self._card_clicked_factory(index))
            row, column = divmod(index, max_columns)
            self.hand_buttons_layout.addWidget(button, row, column)
            self.card_buttons.append(button)
        QApplication.processEvents()

    def choose_action(
        self,
        game: UnoGame,
        player: UnoPlayer,
        playable: Sequence[int],
        penalty_active: bool,
    ) -> PlayerDecision:
        """Wait synchronously for the human player to select an action."""

        self._prepare_action_controls(playable, penalty_active, game)
        self.pending_decision = None
        loop = QEventLoop()
        self.decision_loop = loop
        loop.exec_()
        decision = self.pending_decision or PlayerDecision(action="draw")
        self.decision_loop = None
        self._teardown_action_controls()
        return decision

    def handle_drawn_card(self, game: UnoGame, player: UnoPlayer, card: UnoCard) -> PlayerDecision:
        """Ask the player whether to play the drawn card immediately."""

        self.show_hand(player, [game.interface.render_card(c) for c in player.hand])
        if not card.matches(game.active_color, game.active_value):
            self.show_message("The drawn card cannot be played.", color=Fore.YELLOW)
            return PlayerDecision(action="skip")

        self._clear_action_controls()
        info_label = QLabel("Play the drawn card or keep it?")
        info_label.setWordWrap(True)
        self.action_layout.addWidget(info_label)

        self.uno_checkbox = QCheckBox("Declare UNO")
        self.uno_checkbox.setChecked(False)
        self.action_layout.addWidget(self.uno_checkbox)

        button_row = QWidget()
        row_layout = QHBoxLayout()
        row_layout.setContentsMargins(0, 0, 0, 0)
        button_row.setLayout(row_layout)

        play_button = QPushButton("Play Drawn Card")
        play_button.clicked.connect(self._play_drawn_card_handler(player))
        keep_button = QPushButton("Keep Card")
        keep_button.clicked.connect(self._keep_drawn_card_handler())
        row_layout.addWidget(play_button)
        row_layout.addWidget(keep_button)
        self.action_layout.addWidget(button_row)

        loop = QEventLoop()
        self.decision_loop = loop
        loop.exec_()
        self.decision_loop = None

        self._clear_action_controls()
        return self.pending_decision or PlayerDecision(action="skip")

    def choose_color(self, player: UnoPlayer) -> str:
        """Prompt the user to select a colour after playing a wild card."""

        dialog = QDialog(self)
        dialog.setWindowTitle("Choose a Color")
        layout = QVBoxLayout(dialog)
        prompt = QLabel("Select the new active color:")
        prompt.setWordWrap(True)
        layout.addWidget(prompt)

        selected: Optional[str] = None

        for idx, color in enumerate(COLORS):
            button = QPushButton(color.capitalize())
            button.clicked.connect(lambda _=False, choice=idx: dialog.done(choice + 1))
            layout.addWidget(button)

        result = dialog.exec_()
        if result <= 0:
            return COLORS[0]
        selected_index = result - 1
        if 0 <= selected_index < len(COLORS):
            selected = COLORS[selected_index]
        return selected or COLORS[0]

    def choose_swap_target(self, player: UnoPlayer, players: Sequence[UnoPlayer]) -> int:
        """Prompt the player to choose another player to swap hands with."""

        dialog = QDialog(self)
        dialog.setWindowTitle("Choose Swap Target")
        layout = QVBoxLayout(dialog)
        prompt = QLabel("Choose a player to swap hands with:")
        prompt.setWordWrap(True)
        layout.addWidget(prompt)

        valid_targets = [i for i, p in enumerate(players) if p != player]
        for position, idx in enumerate(valid_targets):
            opponent = players[idx]
            button = QPushButton(f"{opponent.name} ({len(opponent.hand)} cards)")
            button.clicked.connect(lambda _=False, offset=position: dialog.done(offset + 1))
            layout.addWidget(button)

        result = dialog.exec_()
        if result <= 0:
            return valid_targets[0]
        choice_idx = result - 1
        if 0 <= choice_idx < len(valid_targets):
            return valid_targets[choice_idx]
        return valid_targets[0]

    def prompt_challenge(self, challenger: UnoPlayer, target: UnoPlayer, *, bluff_possible: bool) -> bool:
        """Ask a player whether to challenge a +4 card."""

        prompt = f"{challenger.name}, challenge {target.name}'s +4?"
        if not bluff_possible:
            prompt = f"{challenger.name}, challenge {target.name}'s +4? (unlikely to help)"
        result = QMessageBox.question(
            self,
            "Challenge +4?",
            prompt,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        return result == QMessageBox.StandardButton.Yes

    def notify_uno_called(self, player: UnoPlayer) -> None:
        """Inform players that someone has called UNO."""

        self.show_message(f"{player.name} calls UNO!", color=Fore.CYAN, style=Style.BRIGHT)

    def notify_uno_penalty(self, player: UnoPlayer) -> None:
        """Notify that a player failed to call UNO and must draw cards."""

        self.show_message(
            f"{player.name} failed to call UNO and must draw two cards!",
            color=Fore.RED,
            style=Style.BRIGHT,
        )

    def announce_winner(self, winner: UnoPlayer) -> None:
        """Announce the winner of the game."""

        self.show_message(f"{winner.name} wins the round!", color=Fore.CYAN, style=Style.BRIGHT)
        QMessageBox.information(self, "Uno", f"{winner.name} wins the game!")

    def update_status(self, game: UnoGame) -> None:
        """Update scoreboard counts to match the engine state."""

        for label, player in zip(self.score_labels, self.players):
            label.setText(f"{len(player.hand)} cards")
        QApplication.processEvents()

    def render_card(self, card: UnoCard, *, emphasize: bool = False) -> str:
        """Return a human-readable label for a card with emoji prefix."""

        prefix = COLOR_EMOJI.get(card.color, "⬜")
        label = card.label().upper() if emphasize else card.label()
        return f"{prefix} {label}"

    def render_color(self, color: str) -> str:
        """Return a colour name with its corresponding emoji."""

        return f"{COLOR_EMOJI.get(color, '⬜')} {color.capitalize()}"

    def play_sound(self, sound_type: str) -> None:
        """Play a sound effect through the shared sound manager."""

        if not self.config.enable_sounds or self.sound_manager is None:
            return
        self.sound_manager.play(sound_type)

    def prompt_jump_in(self, player: UnoPlayer, card: UnoCard) -> bool:
        """Ask a human player whether to jump in with an identical card."""

        if not player.is_human:
            return False
        message = f"{player.name}, someone just played {card.color} {card.value}!\n\n" "Do you want to JUMP IN with an identical card?"
        result = QMessageBox.question(
            self,
            "Jump In?",
            message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        return result == QMessageBox.StandardButton.Yes

    # Internal helpers -------------------------------------------------
    def _build_layout(self) -> None:
        """Construct the widget hierarchy for the interface."""

        main_layout = QVBoxLayout(self)
        self.heading_label = QLabel("Welcome to Uno!")
        self.heading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.heading_label.setStyleSheet("font-size: 18pt; font-weight: bold; padding: 10px;")
        main_layout.addWidget(self.heading_label)

        content = QWidget()
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(8, 8, 8, 8)
        content.setLayout(content_layout)
        main_layout.addWidget(content)

        self.status_group = QGroupBox("Players")
        self.status_layout = QVBoxLayout()
        self.status_group.setLayout(self.status_layout)
        content_layout.addWidget(self.status_group, 0)

        log_group = QGroupBox("Table Log")
        log_layout = QVBoxLayout()
        self.log_widget = QTextEdit()
        self.log_widget.setReadOnly(True)
        self.log_widget.setAcceptRichText(True)
        self.log_widget.setStyleSheet("font-family: 'Courier New', monospace; font-size: 11pt; background-color: #1e1e1e; color: #f5f5f5;")
        log_layout.addWidget(self.log_widget)
        log_group.setLayout(log_layout)
        content_layout.addWidget(log_group, 1)

        action_panel = QVBoxLayout()

        action_group = QGroupBox("Actions")
        self.action_layout = QVBoxLayout()
        action_group.setLayout(self.action_layout)
        action_panel.addWidget(action_group)

        hand_group = QGroupBox("Your Hand")
        hand_layout = QVBoxLayout()
        self.hand_info_label = QLabel("Select a card or choose an action below.")
        self.hand_info_label.setWordWrap(True)
        hand_layout.addWidget(self.hand_info_label)

        self.hand_scroll = QScrollArea()
        self.hand_scroll.setWidgetResizable(True)
        self.hand_buttons_widget = QWidget()
        self.hand_buttons_layout = QGridLayout()
        self.hand_buttons_layout.setContentsMargins(4, 4, 4, 4)
        self.hand_buttons_layout.setSpacing(6)
        self.hand_buttons_widget.setLayout(self.hand_buttons_layout)
        self.hand_scroll.setWidget(self.hand_buttons_widget)
        hand_layout.addWidget(self.hand_scroll)
        hand_group.setLayout(hand_layout)
        action_panel.addWidget(hand_group, 1)

        action_container = QWidget()
        action_container.setLayout(action_panel)
        content_layout.addWidget(action_container, 1)

    def _build_scoreboard(self) -> None:
        """Populate the scoreboard with player rows."""

        for i in reversed(range(self.status_layout.count())):
            item = self.status_layout.itemAt(i)
            widget = item.widget()
            if widget:
                widget.setParent(None)
        self.score_labels = []
        for player in self.players:
            row = QWidget()
            layout = QHBoxLayout()
            layout.setContentsMargins(4, 2, 4, 2)
            row.setLayout(layout)

            name_label = QLabel(player.name)
            name_label.setStyleSheet("font-weight: bold; font-size: 12pt;")
            layout.addWidget(name_label, 1)

            count_label = QLabel(f"{len(player.hand)} cards")
            count_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            layout.addWidget(count_label)
            self.score_labels.append(count_label)
            self.status_layout.addWidget(row)

        self.status_layout.addStretch(1)

    def _prepare_action_controls(self, playable: Sequence[int], penalty_active: bool, game: UnoGame) -> None:
        """Enable relevant card buttons and configure action controls."""

        for index, button in enumerate(self.card_buttons):
            button.setEnabled(index in playable)

        self._clear_action_controls()
        self.uno_checkbox = QCheckBox("Declare UNO")
        self.uno_checkbox.setChecked(False)
        self.action_layout.addWidget(self.uno_checkbox)

        if penalty_active and not playable:
            label = QLabel(f"Accept the +{game.penalty_amount} penalty.")
            label.setWordWrap(True)
            self.action_layout.addWidget(label)
            accept_button = QPushButton(f"Draw {game.penalty_amount}")
            accept_button.clicked.connect(self._accept_penalty_handler())
            self.action_layout.addWidget(accept_button)
        else:
            draw_button = QPushButton("Draw Card")
            draw_button.clicked.connect(self._draw_card_handler())
            self.action_layout.addWidget(draw_button)
            if penalty_active:
                accept_button = QPushButton(f"Accept +{game.penalty_amount}")
                accept_button.clicked.connect(self._accept_penalty_handler())
                self.action_layout.addWidget(accept_button)
        QApplication.processEvents()

    def _teardown_action_controls(self) -> None:
        """Reset action controls and disable card buttons after a turn."""

        for button in self.card_buttons:
            button.setEnabled(False)
            button.setStyleSheet("")
        self._clear_action_controls()
        self.uno_checkbox = None
        QApplication.processEvents()

    def _clear_action_controls(self) -> None:
        """Remove all widgets from the action layout."""

        while self.action_layout.count():
            item = self.action_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)

    def _clear_hand_buttons(self) -> None:
        """Remove all card buttons from the hand area."""

        while self.hand_buttons_layout.count():
            item = self.hand_buttons_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)

    def _card_clicked_factory(self, index: int) -> Callable[[bool], None]:
        """Create a click handler for card buttons that stores the selection."""

        def handler(_checked: bool = False) -> None:
            swap_target: Optional[int] = None
            if (
                self.game
                and self.game.house_rules.seven_zero_swap
                and self.game.players[self.game.current_index].hand
                and 0 <= index < len(self.game.players[self.game.current_index].hand)
            ):
                current_player = self.game.players[self.game.current_index]
                card = current_player.hand[index]
                if card.value == "7":
                    swap_target = self.choose_swap_target(current_player, self.game.players)

            self._animate_card_play(index)
            declare_uno = self.uno_checkbox.isChecked() if self.uno_checkbox else False
            self.pending_decision = PlayerDecision(
                action="play",
                card_index=index,
                declare_uno=declare_uno,
                swap_target=swap_target,
            )
            self.decision_made.emit()

        return handler

    def _draw_card_handler(self) -> Callable[[bool], None]:
        """Return a handler that records a draw decision."""

        def handler(_checked: bool = False) -> None:
            self.pending_decision = PlayerDecision(action="draw")
            self.decision_made.emit()

        return handler

    def _accept_penalty_handler(self) -> Callable[[bool], None]:
        """Return a handler that records accepting a penalty."""

        def handler(_checked: bool = False) -> None:
            self.pending_decision = PlayerDecision(action="accept_penalty")
            self.decision_made.emit()

        return handler

    def _play_drawn_card_handler(self, player: UnoPlayer) -> Callable[[bool], None]:
        """Return a handler for playing the drawn card."""

        def handler(_checked: bool = False) -> None:
            declare = bool(self.uno_checkbox and self.uno_checkbox.isChecked() and len(player.hand) == 1)
            self.pending_decision = PlayerDecision(
                action="play",
                card_index=len(player.hand) - 1,
                declare_uno=declare,
            )
            self.decision_made.emit()

        return handler

    def _keep_drawn_card_handler(self) -> Callable[[bool], None]:
        """Return a handler for keeping the drawn card."""

        def handler(_checked: bool = False) -> None:
            self.pending_decision = PlayerDecision(action="skip")
            self.decision_made.emit()

        return handler

    def _animate_card_play(self, card_index: int) -> None:
        """Create a subtle highlight animation on the played card button."""

        if not self.enable_animations:
            return
        if not (0 <= card_index < len(self.card_buttons)):
            return

        button = self.card_buttons[card_index]
        original_style = button.styleSheet()
        highlight_style = original_style + "; background-color: #FFD700; font-weight: bold;"

        def animate(step: int = 0) -> None:
            if step >= 6:
                button.setStyleSheet(original_style)
                return
            button.setStyleSheet(highlight_style if step % 2 == 0 else original_style)
            QTimer.singleShot(80, lambda: animate(step + 1))

        animate()

    def _quit_decision_loop(self) -> None:
        """Exit the nested event loop once a decision has been captured."""

        if self.decision_loop is not None and self.decision_loop.isRunning():
            self.decision_loop.quit()


def launch_uno_gui_pyqt(
    total_players: int,
    *,
    bots: int,
    bot_skill: str,
    seed: Optional[int] = None,
    house_rules: Optional[HouseRules] = None,
    team_mode: bool = False,
    enable_sounds: bool = True,
) -> None:
    """Launch the Uno PyQt5 GUI application."""

    rng = random.Random(seed)
    players = build_players(total_players, bots=bots, bot_skill=bot_skill, team_mode=team_mode)

    app = QApplication.instance() or QApplication(sys.argv)
    interface = PyQtUnoInterface(players, enable_sounds=enable_sounds)
    game = UnoGame(
        players=players,
        rng=rng,
        interface=interface,
        house_rules=house_rules or HouseRules(),
        team_mode=team_mode,
    )
    interface.set_game(game)

    def run_game() -> None:
        game.setup()
        try:
            game.play()
        except Exception as exc:  # pragma: no cover - defensive GUI error dialog
            QMessageBox.critical(interface, "Uno Error", f"An unexpected error occurred: {exc}")
            raise

    QTimer.singleShot(0, run_game)
    interface.show()
    app.exec_()


__all__ = ["PyQtUnoInterface", "launch_uno_gui_pyqt"]
