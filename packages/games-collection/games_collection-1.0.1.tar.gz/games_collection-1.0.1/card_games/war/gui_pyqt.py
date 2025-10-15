"""PyQt5 GUI for the War card game.

This module recreates the Tkinter-based War interface using PyQt5 widgets. The
layout retains the original structure with panels that highlight deck sizes,
the shared pile, and round statistics while a scrollable log narrates each
battle. Controls let players advance one round at a time or trigger an
auto-play loop with an adjustable delay.

War's dramatic moments are emphasized through :class:`WarBattleCanvas`, a
custom widget that draws stacked face-down cards and flashes alerts whenever a
war occurs. The GUI also integrates the shared :class:`~common.architecture.
persistence.SaveLoadManager` so players can persist and restore games using
native PyQt dialogs.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import Any, Dict, Optional

from PyQt5.QtCore import QRect, Qt, QTimer
from PyQt5.QtGui import QColor, QFont, QPainter, QPen
from PyQt5.QtWidgets import (
    QApplication,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSlider,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from card_games.war.game import WarGame
from common.architecture.persistence import SaveLoadManager

try:  # pragma: no cover - optional dependency for stats tracking
    from card_games.common.stats import CardGameStats

    STATS_AVAILABLE = True
except ImportError:  # pragma: no cover - environments without optional stats
    STATS_AVAILABLE = False
    CardGameStats = None  # type: ignore[assignment]


class WarBattleCanvas(QWidget):
    """Custom widget that renders stacked cards and flashing alerts during wars."""

    CARD_WIDTH = 54
    CARD_HEIGHT = 82
    STACK_OFFSET = 11

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """Initialize the canvas widget."""

        super().__init__(parent)
        self.setMinimumHeight(140)
        self._war_result: Optional[Dict[str, Any]] = None
        self._message = "No war in progress."
        self._flash_on = False
        self._flash_cycles_remaining = 0
        self._flash_timer = QTimer(self)
        self._flash_timer.setInterval(220)
        self._flash_timer.timeout.connect(self._toggle_flash)
        self.setAutoFillBackground(True)

    def show_war(self, result: Dict[str, Any], cycles: int = 8) -> None:
        """Display a war animation and start flashing alerts."""

        self._war_result = result
        self._message = self._describe_war(result)
        self._flash_cycles_remaining = max(cycles, 1)
        self._flash_on = True
        self._flash_timer.start()
        self.update()

    def clear(self) -> None:
        """Reset the canvas to an idle state."""

        self._war_result = None
        self._message = "No war in progress."
        self._flash_timer.stop()
        self._flash_on = False
        self._flash_cycles_remaining = 0
        self.update()

    def _describe_war(self, result: Dict[str, Any]) -> str:
        """Create a descriptive message for the given war result."""

        if result.get("reason") == "insufficient_cards":
            return "War ends: insufficient cards"
        if result.get("nested_war"):
            return "WAR continues! Another tie"
        return "WAR! Cards matched"

    def _toggle_flash(self) -> None:
        """Toggle the flash state and repaint."""

        if self._flash_cycles_remaining <= 0:
            self._flash_timer.stop()
            self._flash_on = False
            self.update()
            return

        self._flash_on = not self._flash_on
        self._flash_cycles_remaining -= 1
        self.update()

    def paintEvent(self, event) -> None:  # type: ignore[override]
        """Render the card stacks and alert message."""

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        base_color = QColor("#0F1C2E")
        flash_color = QColor("#B71C1C")
        painter.fillRect(self.rect(), flash_color if self._flash_on else base_color)

        if not self._war_result:
            painter.setPen(QColor("#EEEEEE"))
            painter.setFont(QFont("Arial", 12, QFont.Weight.Bold))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self._message)
            return

        width = self.width()
        height = self.height()
        left_x = int(width * 0.2)
        right_x = int(width * 0.6)
        top_y = int((height - self.CARD_HEIGHT) / 2)

        self._draw_stack(painter, left_x, top_y, QColor("#1E88E5"))
        self._draw_stack(painter, right_x, top_y, QColor("#F4511E"))

        painter.setPen(QColor("#FFFFFF"))
        painter.setFont(QFont("Arial", 13, QFont.Weight.Bold))
        text_rect = self.rect().adjusted(0, 0, 0, -8)
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter, self._message)

    def _draw_stack(self, painter: QPainter, x: int, y: int, color: QColor) -> None:
        """Draw three face-down cards and one highlighted face-up card."""

        facedown_color = QColor(color)
        facedown_color.setAlpha(140)
        outline = QPen(QColor("#ECEFF1"), 2)

        for idx in range(3):
            offset = idx * self.STACK_OFFSET
            rect = self._card_rect(x + offset, y + offset)
            painter.fillRect(rect, facedown_color)
            painter.setPen(outline)
            painter.drawRect(rect)

        face_up_rect = self._card_rect(x + self.STACK_OFFSET * 3, y)
        painter.fillRect(face_up_rect, QColor("#FAFAFA"))
        painter.setPen(QPen(color, 3))
        painter.drawRect(face_up_rect)

    def _card_rect(self, x: int, y: int) -> QRect:
        """Return the QRect describing a card at the given location."""

        return QRect(x, y, self.CARD_WIDTH, self.CARD_HEIGHT)


class WarGUI(QWidget):
    """PyQt5 interface that visualizes and controls a :class:`WarGame`."""

    def __init__(self, game: Optional[WarGame] = None) -> None:
        """Initialize the War GUI."""

        super().__init__()
        self.game = game or WarGame()
        self._save_load_manager = SaveLoadManager()
        self._start_time = time.time()
        self._last_result: Optional[Dict[str, Any]] = None
        self._auto_running = False

        self.player1_faceup_label: QLabel
        self.player2_faceup_label: QLabel
        self.log_widget: QTextEdit

        self.auto_timer = QTimer(self)
        self.auto_timer.setSingleShot(True)
        self.auto_timer.timeout.connect(self._auto_step)

        self.setWindowTitle("Card Games - War")
        self.resize(920, 740)

        self._build_layout()
        self._update_speed_display()
        self.update_display()
        self._log_message("Game initialized. Click Play Round to begin.")

    def _build_layout(self) -> None:
        """Construct the full GUI layout."""

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)
        self.setLayout(main_layout)

        header = QLabel("War")
        header_font = QFont("Arial", 22, QFont.Weight.Bold)
        header.setFont(header_font)
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(header)

        stats_row = QHBoxLayout()
        stats_row.setSpacing(16)
        main_layout.addLayout(stats_row)

        deck_group = self._build_deck_group()
        stats_row.addWidget(deck_group)

        summary_group = self._build_summary_group()
        stats_row.addWidget(summary_group)

        battle_group = self._build_battle_group()
        main_layout.addWidget(battle_group)

        log_group = QGroupBox("Battle Log")
        log_layout = QVBoxLayout()
        self.log_widget = QTextEdit()
        self.log_widget.setReadOnly(True)
        self.log_widget.setMinimumHeight(160)
        log_layout.addWidget(self.log_widget)
        log_group.setLayout(log_layout)
        main_layout.addWidget(log_group, stretch=1)

        controls_group = self._build_controls_group()
        main_layout.addWidget(controls_group)

        self.status_label = QLabel("Click Play Round to begin.")
        self.status_label.setWordWrap(True)
        status_font = QFont("Arial", 11)
        self.status_label.setFont(status_font)
        main_layout.addWidget(self.status_label)

    def _build_deck_group(self) -> QGroupBox:
        """Create the deck sizes panel."""

        deck_group = QGroupBox("Deck Sizes")
        layout = QVBoxLayout()

        player1_header = QLabel("Player 1")
        player1_header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        player1_header.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.player1_cards_label = QLabel("Cards: 26")
        self.player1_cards_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(player1_header)
        layout.addWidget(self.player1_cards_label)

        player2_header = QLabel("Player 2")
        player2_header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        player2_header.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.player2_cards_label = QLabel("Cards: 26")
        self.player2_cards_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(player2_header)
        layout.addWidget(self.player2_cards_label)

        deck_group.setLayout(layout)
        return deck_group

    def _build_summary_group(self) -> QGroupBox:
        """Create the summary panel displaying pile and round statistics."""

        summary_group = QGroupBox("Game Summary")
        layout = QVBoxLayout()

        self.pile_cards_label = QLabel("Pile size: 0")
        self.rounds_label = QLabel("Rounds played: 0")
        self.wars_label = QLabel("Wars fought: 0")

        for label in (self.pile_cards_label, self.rounds_label, self.wars_label):
            label.setAlignment(Qt.AlignmentFlag.AlignLeft)
            layout.addWidget(label)

        summary_group.setLayout(layout)
        return summary_group

    def _build_battle_group(self) -> QGroupBox:
        """Create the panel showing face-up cards and the war canvas."""

        battle_group = QGroupBox("Current Battle")
        layout = QVBoxLayout()
        card_row = QHBoxLayout()
        card_row.setSpacing(24)

        player1_column = self._create_card_label("Player 1")
        player2_column = self._create_card_label("Player 2")

        card_row.addLayout(player1_column)
        card_row.addStretch(1)
        card_row.addLayout(player2_column)

        layout.addLayout(card_row)

        self.battle_canvas = WarBattleCanvas()
        layout.addWidget(self.battle_canvas)
        battle_group.setLayout(layout)
        return battle_group

    def _create_card_label(self, title: str) -> QVBoxLayout:
        """Create a layout containing the player title and card display."""

        column = QVBoxLayout()
        header = QLabel(title)
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setFont(QFont("Arial", 13, QFont.Weight.Bold))

        card_label = QLabel("—")
        card_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_label.setStyleSheet("background-color: #0D47A1; color: white; padding: 8px;")
        card_label.setFont(QFont("Courier New", 16, QFont.Weight.Bold))

        column.addWidget(header)
        column.addWidget(card_label)

        if title == "Player 1":
            self.player1_faceup_label = card_label
        else:
            self.player2_faceup_label = card_label

        return column

    def _build_controls_group(self) -> QGroupBox:
        """Create the controls panel with buttons and auto-play slider."""

        controls_group = QGroupBox("Controls")
        layout = QVBoxLayout()

        button_row = QHBoxLayout()
        button_row.setSpacing(10)

        self.play_button = QPushButton("Play Round")
        self.play_button.clicked.connect(self._on_play_clicked)
        button_row.addWidget(self.play_button)

        self.auto_button = QPushButton("Start Auto Play")
        self.auto_button.clicked.connect(self._toggle_auto_play)
        button_row.addWidget(self.auto_button)

        save_button = QPushButton("Save Game")
        save_button.clicked.connect(self._save_game)
        button_row.addWidget(save_button)

        load_button = QPushButton("Load Game")
        load_button.clicked.connect(self._load_game)
        button_row.addWidget(load_button)

        shortcuts_button = QPushButton("Show Shortcuts")
        shortcuts_button.clicked.connect(self._show_shortcuts)
        button_row.addWidget(shortcuts_button)
        button_row.addStretch(1)

        layout.addLayout(button_row)

        speed_label = QLabel("Auto-play speed (ms between rounds)")
        layout.addWidget(speed_label)

        slider_row = QHBoxLayout()
        self.speed_slider = QSlider(Qt.Orientation.Horizontal)
        self.speed_slider.setRange(150, 2000)
        self.speed_slider.setValue(700)
        self.speed_slider.valueChanged.connect(lambda _: self._update_speed_display())
        slider_row.addWidget(self.speed_slider)

        self.speed_value_label = QLabel("700 ms")
        self.speed_value_label.setMinimumWidth(70)
        self.speed_value_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        slider_row.addWidget(self.speed_value_label)

        layout.addLayout(slider_row)
        controls_group.setLayout(layout)
        return controls_group

    def update_display(self) -> None:
        """Refresh all dynamic labels to match the current game state."""

        summary = self.game.get_state_summary()
        self.player1_cards_label.setText(f"Cards: {summary['player1_cards']}")
        self.player2_cards_label.setText(f"Cards: {summary['player2_cards']}")
        self.pile_cards_label.setText(f"Pile size: {summary['pile_cards']}")
        self.rounds_label.setText(f"Rounds played: {summary['rounds_played']}")
        self.wars_label.setText(f"Wars fought: {summary['wars_fought']}")

        if self._last_result and "player1_card" in self._last_result:
            self.player1_faceup_label.setText(str(self._last_result["player1_card"]))
            self.player2_faceup_label.setText(str(self._last_result["player2_card"]))
        else:
            self.player1_faceup_label.setText("—")
            self.player2_faceup_label.setText("—")

        if summary["state"] == "GAME_OVER":
            self.status_label.setText(f"Game over. Player {summary['winner']} wins!")
            self.play_button.setEnabled(False)
            self.auto_button.setEnabled(False)
        else:
            if not self._auto_running:
                self.play_button.setEnabled(True)
            self.auto_button.setEnabled(True)

    def _on_play_clicked(self) -> None:
        """Handle the Play Round button."""

        self._stop_auto_play()
        self._play_round()

    def _play_round(self) -> None:
        """Execute a single game round and update the interface."""

        if self.game.is_game_over():
            self._handle_game_over()
            return

        result = self.game.play_round()
        self._last_result = result

        if "player1_card" in result:
            summary_line = f"Round {self.game.rounds_played}: {result['player1_card']} vs {result['player2_card']}"
            if result.get("round_type") == "war":
                summary_line += " — WAR!"
            self._log_message(summary_line)
            self._log_message(f"Player {result['winner']} claims {result['cards_won']} cards.")

        if result.get("round_type") == "war":
            self.battle_canvas.show_war(result)
        else:
            self.battle_canvas.clear()

        self.status_label.setText(f"Player {result.get('winner', '—')} won the round.")
        self.update_display()

        if result.get("game_over"):
            self._handle_game_over(result)

    def _toggle_auto_play(self) -> None:
        """Toggle auto-play loop on or off."""

        if self._auto_running:
            self._stop_auto_play()
            return

        if self.game.is_game_over():
            self.status_label.setText("Game finished. Start a new game to auto-play again.")
            return

        self._auto_running = True
        self.auto_button.setText("Stop Auto Play")
        self.play_button.setEnabled(False)
        self._schedule_next_round()
        self.status_label.setText("Auto-play running…")

    def _schedule_next_round(self) -> None:
        """Schedule the next automatic round."""

        delay = max(int(self.speed_slider.value()), 150)
        self.auto_timer.start(delay)

    def _auto_step(self) -> None:
        """Play a round as part of the auto-play loop."""

        self._play_round()
        if not self.game.is_game_over() and self._auto_running:
            self._schedule_next_round()
        else:
            self._stop_auto_play()

    def _stop_auto_play(self) -> None:
        """Stop the auto-play loop if active."""

        if self.auto_timer.isActive():
            self.auto_timer.stop()
        self._auto_running = False
        self.auto_button.setText("Start Auto Play")
        if not self.game.is_game_over():
            self.play_button.setEnabled(True)

    def _update_speed_display(self) -> None:
        """Update the label describing the auto-play delay."""

        self.speed_value_label.setText(f"{int(self.speed_slider.value())} ms")

    def _handle_game_over(self, result: Optional[Dict[str, Any]] = None) -> None:
        """Display information when the game concludes."""

        self._stop_auto_play()
        summary = self.game.get_state_summary()
        winner = summary.get("winner")
        rounds = summary.get("rounds_played")
        wars = summary.get("wars_fought")
        duration = time.time() - self._start_time

        if result and result.get("reason") == "insufficient_cards":
            message = "A player ran out of cards during war."
        else:
            message = "One player captured the entire deck."

        detail = f"Player {winner} wins after {rounds} rounds with {wars} wars fought.\n" f"Game duration: {duration:.1f} seconds.\n{message}"

        QMessageBox.information(self, "War - Game Over", detail)

        if STATS_AVAILABLE and winner in {1, 2}:
            self._maybe_save_stats(duration, int(winner))

    def _maybe_save_stats(self, duration: float, winner: int) -> None:
        """Offer to persist statistics when the game ends."""

        response = QMessageBox.question(
            self,
            "Save Statistics",
            "Save this result to your War stats?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if response != QMessageBox.StandardButton.Yes:
            self.status_label.setText("Statistics not saved.")
            return

        try:
            assert CardGameStats is not None  # For static type checking
            stats = CardGameStats("war")
            stats.record_win(f"Player {winner}", duration)
            stats.record_loss(f"Player {3 - winner}", duration)
            stats.save()
            self.status_label.setText("Game statistics saved successfully.")
        except Exception as exc:  # pragma: no cover - depends on user environment
            self.status_label.setText(f"Could not save statistics: {exc}")

    def _save_game(self) -> None:
        """Persist the current game state."""

        if self.game.is_game_over():
            QMessageBox.warning(self, "Cannot Save", "Game is already over. Nothing to save.")
            return

        try:
            state = self.game.to_dict()
            filepath = self._save_load_manager.save("war", state)
            self.status_label.setText(f"Game saved to {filepath.name}")
            self._log_message(f"Game saved successfully to {filepath}")
            QMessageBox.information(self, "Save Successful", f"Game saved to:\n{filepath}")
        except Exception as exc:
            error_msg = f"Failed to save game: {exc}"
            self.status_label.setText(error_msg)
            self._log_message(error_msg)
            QMessageBox.critical(self, "Save Failed", error_msg)

    def _load_game(self) -> None:
        """Load a previously saved game state."""

        try:
            saves = self._save_load_manager.list_saves("war")
            default_dir = saves[0].parent if saves else Path("./saves")
            default_dir.mkdir(parents=True, exist_ok=True)

            filepath_str, _ = QFileDialog.getOpenFileName(
                self,
                "Load War Game",
                str(default_dir),
                "Save files (*.save);;All files (*.*)",
            )

            if not filepath_str:
                return

            data = self._save_load_manager.load(Path(filepath_str))
            if data.get("game_type") != "war":
                QMessageBox.critical(self, "Invalid Save", "This save file is not for War.")
                return

            self._stop_auto_play()
            self.game = WarGame.from_dict(data["state"])
            self._last_result = None
            self._start_time = time.time()
            self.battle_canvas.clear()

            self.play_button.setEnabled(True)
            self.auto_button.setEnabled(True)

            self.update_display()
            self.status_label.setText(f"Game loaded from {Path(filepath_str).name}")
            self._log_message(f"Game loaded successfully from {filepath_str}")
            QMessageBox.information(self, "Load Successful", "Game loaded successfully!")

        except Exception as exc:
            error_msg = f"Failed to load game: {exc}"
            self.status_label.setText(error_msg)
            self._log_message(error_msg)
            QMessageBox.critical(self, "Load Failed", error_msg)

    def _show_shortcuts(self) -> None:
        """Display the available keyboard shortcuts."""

        QMessageBox.information(
            self,
            "Keyboard Shortcuts",
            "Space: Play a round\nCtrl+A: Toggle auto-play",
        )

    def _log_message(self, message: str) -> None:
        """Append a message to the log widget."""

        self.log_widget.append(message)
        scrollbar = self.log_widget.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())


def run_gui(game: Optional[WarGame] = None) -> int:
    """Launch the PyQt5 War GUI."""

    app = QApplication.instance() or QApplication(sys.argv)
    window = WarGUI(game=game)
    window.show()
    return app.exec()


__all__ = ["WarBattleCanvas", "WarGUI", "run_gui"]


if __name__ == "__main__":
    sys.exit(run_gui())
