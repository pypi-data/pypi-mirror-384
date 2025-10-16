"""PyQt5 GUI for double-deck Pinochle."""

from __future__ import annotations

from typing import Optional

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QApplication,
    QComboBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from card_games.pinochle.game import PinochleGame, PinochlePlayer
from common.gui_base_pyqt import PYQT5_AVAILABLE, BaseGUI, GUIConfig


class PinochlePyQtGUI(QMainWindow, BaseGUI):
    """Qt window that orchestrates a :class:`PinochleGame` instance."""

    def __init__(self, game: Optional[PinochleGame] = None) -> None:
        if not PYQT5_AVAILABLE:
            raise RuntimeError("PyQt5 must be installed to launch the Pinochle GUI")
        QMainWindow.__init__(self)
        config = GUIConfig(
            window_title="Card Games - Pinochle",
            window_width=1100,
            window_height=760,
            theme_name="emerald",
            enable_sounds=True,
            enable_animations=True,
        )
        BaseGUI.__init__(self, self, config)

        if game is None:
            players = [
                PinochlePlayer(name="South"),
                PinochlePlayer(name="West"),
                PinochlePlayer(name="North"),
                PinochlePlayer(name="East"),
            ]
            self.game = PinochleGame(players)
        else:
            self.game = game

        self.phase = "setup"
        self.status_label: Optional[QLabel] = None
        self.phase_label: Optional[QLabel] = None
        self.score_labels: list[QLabel] = []
        self.current_player_label: Optional[QLabel] = None
        self.trump_label: Optional[QLabel] = None
        self.bid_spinbox: Optional[QSpinBox] = None
        self.bid_button: Optional[QPushButton] = None
        self.pass_button: Optional[QPushButton] = None
        self.trump_combo: Optional[QComboBox] = None
        self.play_button: Optional[QPushButton] = None
        self.new_round_button: Optional[QPushButton] = None
        self.bid_history_text: Optional[QTextEdit] = None
        self.meld_text: Optional[QTextEdit] = None
        self.trick_text: Optional[QTextEdit] = None
        self.hand_list: Optional[QListWidget] = None

        self._layout_built = False
        self.build_layout()
        self.start_new_round()

    def build_layout(self) -> None:  # pragma: no cover - required by BaseGUI
        if not self._layout_built:
            self._build_layout()
            self._layout_built = True

    def update_display(self) -> None:
        scores = self.game.partnership_scores
        for index, label in enumerate(self.score_labels):
            label.setText(str(scores[index]))
        if self.game.bidding_history and self.bid_history_text:
            history_lines = [f"{name}: {action}" for name, action in self.game.bidding_history]
            self.bid_history_text.setPlainText("\n".join(history_lines))
        elif self.bid_history_text:
            self.bid_history_text.setPlainText("No bids yet")
        if self.phase == "bidding" and self.game.bidding_phase and self.current_player_label:
            current = self.game.players[self.game.bidding_phase.current_index]
            self.current_player_label.setText(current.name)
        elif self.game.current_player_index is not None and self.current_player_label:
            self.current_player_label.setText(self.game.players[self.game.current_player_index].name)
        if self.meld_text:
            if self.game.meld_breakdowns:
                lines = []
                for player in self.game.players:
                    breakdown = self.game.meld_breakdowns.get(player.name, {})
                    pieces = ", ".join(f"{key.replace('_', ' ')}: {value}" for key, value in breakdown.items())
                    if not pieces:
                        pieces = "no meld"
                    lines.append(f"{player.name}: {player.meld_points} ({pieces})")
                self.meld_text.setPlainText("\n".join(lines))
            else:
                self.meld_text.setPlainText("Meld not scored yet.")
        if self.hand_list:
            self.hand_list.clear()
            if self.game.current_player_index is not None:
                player = self.game.players[self.game.current_player_index]
            elif self.game.bidding_phase:
                player = self.game.players[self.game.bidding_phase.current_index]
            else:
                player = self.game.players[0]
            for card in player.hand:
                QListWidgetItem(str(card), self.hand_list)

    def _build_layout(self) -> None:
        central = QWidget(self)
        self.setCentralWidget(central)
        layout = QVBoxLayout()
        central.setLayout(layout)

        header = QHBoxLayout()
        self.status_label = QLabel("Click New Round to deal cards.")
        self.status_label.setWordWrap(True)
        header.addWidget(self.status_label, 1)
        self.phase_label = QLabel("Idle")
        self.phase_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        header.addWidget(self.phase_label)
        layout.addLayout(header)

        score_group = QGroupBox("Partnership scores")
        score_layout = QGridLayout()
        score_group.setLayout(score_layout)
        for index, name in enumerate(("South & North", "West & East")):
            label = QLabel(name)
            label.setStyleSheet("font-weight: bold;")
            score_layout.addWidget(label, index, 0)
            value_label = QLabel("0")
            value_label.setAlignment(Qt.AlignmentFlag.AlignRight)
            score_layout.addWidget(value_label, index, 1)
            self.score_labels.append(value_label)
        layout.addWidget(score_group)

        controls = QGroupBox("Round control")
        controls_layout = QGridLayout()
        controls.setLayout(controls_layout)
        layout.addWidget(controls)

        controls_layout.addWidget(QLabel("Current player:"), 0, 0)
        self.current_player_label = QLabel("-")
        controls_layout.addWidget(self.current_player_label, 0, 1)

        controls_layout.addWidget(QLabel("Trump suit:"), 1, 0)
        self.trump_label = QLabel("Undeclared")
        controls_layout.addWidget(self.trump_label, 1, 1)

        controls_layout.addWidget(QLabel("Bid:"), 2, 0)
        self.bid_spinbox = QSpinBox()
        self.bid_spinbox.setRange(self.game.min_bid, 1000)
        self.bid_spinbox.setSingleStep(10)
        controls_layout.addWidget(self.bid_spinbox, 2, 1)
        self.bid_button = QPushButton("Submit bid")
        self.bid_button.clicked.connect(self._submit_bid)
        controls_layout.addWidget(self.bid_button, 3, 0)
        self.pass_button = QPushButton("Pass")
        self.pass_button.clicked.connect(self._pass_bid)
        controls_layout.addWidget(self.pass_button, 3, 1)

        self.trump_combo = QComboBox()
        self.trump_combo.addItems(["Clubs", "Diamonds", "Hearts", "Spades"])
        controls_layout.addWidget(QLabel("Select trump:"), 4, 0)
        controls_layout.addWidget(self.trump_combo, 4, 1)
        confirm_button = QPushButton("Confirm trump")
        confirm_button.clicked.connect(self._confirm_trump)
        controls_layout.addWidget(confirm_button, 5, 0, 1, 2)

        self.play_button = QPushButton("Play selected card")
        self.play_button.clicked.connect(self._play_card)
        controls_layout.addWidget(self.play_button, 6, 0, 1, 2)

        self.new_round_button = QPushButton("New round")
        self.new_round_button.clicked.connect(self.start_new_round)
        controls_layout.addWidget(self.new_round_button, 7, 0, 1, 2)

        history_group = QGroupBox("Bidding history")
        history_layout = QVBoxLayout()
        history_group.setLayout(history_layout)
        self.bid_history_text = QTextEdit()
        self.bid_history_text.setReadOnly(True)
        history_layout.addWidget(self.bid_history_text)
        layout.addWidget(history_group)

        meld_group = QGroupBox("Meld summary")
        meld_layout = QVBoxLayout()
        meld_group.setLayout(meld_layout)
        self.meld_text = QTextEdit()
        self.meld_text.setReadOnly(True)
        meld_layout.addWidget(self.meld_text)
        layout.addWidget(meld_group)

        trick_group = QGroupBox("Trick history")
        trick_layout = QVBoxLayout()
        trick_group.setLayout(trick_layout)
        self.trick_text = QTextEdit()
        self.trick_text.setReadOnly(True)
        trick_layout.addWidget(self.trick_text)
        layout.addWidget(trick_group)

        hand_group = QGroupBox("Current hand")
        hand_layout = QVBoxLayout()
        hand_group.setLayout(hand_layout)
        self.hand_list = QListWidget()
        hand_layout.addWidget(self.hand_list)
        layout.addWidget(hand_group)

    def start_new_round(self) -> None:
        self.play_sound("shuffle")
        self.game.shuffle_and_deal()
        self.game.start_bidding()
        self.phase = "bidding"
        if self.status_label:
            self.status_label.setText("Bidding phase: submit bids for each player.")
        if self.phase_label:
            self.phase_label.setText("Bidding")
        if self.trump_label:
            self.trump_label.setText("Undeclared")
        self._append_trick_log("New round started. Deck shuffled and cards dealt.")
        self.update_display()

    def _append_trick_log(self, message: str) -> None:
        if self.trick_text:
            self.trick_text.append(message)

    def _submit_bid(self) -> None:
        if not self.game.bidding_phase or not self.bid_spinbox:
            return
        value = int(self.bid_spinbox.value())
        try:
            self.game.place_bid(value)
            self._append_trick_log(f"{self.game.bidding_history[-1][0]} bids {value}.")
        except ValueError as exc:
            QMessageBox.warning(self, "Invalid bid", str(exc))
            return
        if self.game.bidding_phase.finished:
            if self.status_label:
                self.status_label.setText("Bidding complete. Select trump suit.")
            if self.phase_label:
                self.phase_label.setText("Trump selection")
            if self.game.bidding_phase.high_bidder and self.current_player_label:
                self.current_player_label.setText(self.game.bidding_phase.high_bidder.name)
        self.update_display()

    def _pass_bid(self) -> None:
        if not self.game.bidding_phase:
            return
        self.game.place_bid(None)
        self._append_trick_log(f"{self.game.bidding_history[-1][0]} passes.")
        if self.game.bidding_phase.finished:
            if self.status_label:
                self.status_label.setText("Bidding complete. Select trump suit.")
            if self.phase_label:
                self.phase_label.setText("Trump selection")
            if self.game.bidding_phase.high_bidder and self.current_player_label:
                self.current_player_label.setText(self.game.bidding_phase.high_bidder.name)
        self.update_display()

    def _confirm_trump(self) -> None:
        if not self.game.bidding_phase or not self.game.bidding_phase.finished:
            QMessageBox.information(self, "Trump", "Finish bidding before choosing trump.")
            return
        if not self.trump_combo:
            return
        selection = self.trump_combo.currentText().lower()
        suit_map = {
            "clubs": "CLUBS",
            "diamonds": "DIAMONDS",
            "hearts": "HEARTS",
            "spades": "SPADES",
        }
        from card_games.common.cards import Suit

        suit = Suit[suit_map[selection]]
        self.game.set_trump(suit)
        self.game.score_melds()
        if self.trump_label:
            self.trump_label.setText(selection.title())
        if self.status_label:
            self.status_label.setText("Meld scored. Play out the hand using the card list.")
        if self.phase_label:
            self.phase_label.setText("Meld & play")
        self.phase = "tricks"
        self._append_trick_log(f"Trump suit set to {selection.title()}.")
        self.update_display()

    def _play_card(self) -> None:
        if self.phase != "tricks" or self.game.current_player_index is None:
            return
        if not self.hand_list:
            return
        selection = self.hand_list.currentRow()
        if selection < 0:
            QMessageBox.information(self, "Play card", "Select a card to play.")
            return
        player = self.game.players[self.game.current_player_index]
        card = player.hand[selection]
        if not self.game.is_valid_play(player, card):
            QMessageBox.warning(self, "Illegal play", "You must follow suit when able.")
            return
        self.game.play_card(card)
        self.play_sound("card")
        self._append_trick_log(f"{player.name} plays {card}.")
        if len(self.game.current_trick) == len(self.game.players):
            winner = self.game.complete_trick()
            self.play_sound("win")
            self._append_trick_log(f"Trick won by {winner.name}: {self.game.format_trick(self.game.trick_history[-1])}")
            if not any(p.hand for p in self.game.players):
                totals = self.game.resolve_round()
                summary = ", ".join(f"Team {team + 1}: {values['total']}" for team, values in totals.items())
                self._append_trick_log(f"Round complete. {summary}")
                if self.status_label:
                    self.status_label.setText("Round complete. Start a new round when ready.")
                if self.phase_label:
                    self.phase_label.setText("Scoring")
                self.phase = "scoring"
        self.update_display()


def run_app(player_names: Optional[list[str]] = None) -> None:
    """Launch the PyQt5 application."""

    if not PYQT5_AVAILABLE:
        raise RuntimeError("PyQt5 is not available on this system")
    app = QApplication.instance() or QApplication([])
    game = None
    if player_names:
        names = list(player_names)[:4]
        while len(names) < 4:
            names.append(f"Player {len(names) + 1}")
        players = [PinochlePlayer(name=name) for name in names]
        game = PinochleGame(players)
    window = PinochlePyQtGUI(game=game)
    window.show()
    app.exec_()


__all__ = ["PinochlePyQtGUI", "run_app"]
