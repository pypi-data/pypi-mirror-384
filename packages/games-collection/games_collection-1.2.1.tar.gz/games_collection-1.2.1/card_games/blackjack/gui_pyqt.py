from __future__ import annotations

"""PyQt5 implementation of the Blackjack table interface.

The ``BlackjackTable`` widget mirrors the aesthetics and behavior of the
Tkinter implementation using native Qt widgets. It reproduces the betting
controls, action buttons, and card rendering, while QTimer callbacks handle
dealer animations and round pacing.
"""

from typing import Optional

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QColor, QFont, QPen
from PyQt5.QtWidgets import (
    QApplication,
    QFrame,
    QGraphicsScene,
    QGraphicsView,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from card_games.blackjack.game import BlackjackGame, BlackjackHand, Outcome
from card_games.common.cards import Card, Suit
from card_games.common.soundscapes import initialize_game_soundscape
from common.gui_base_pyqt import BaseGUI, GUIConfig

_TABLE_GREEN = "#0b5d1e"
_TABLE_ACCENT = "#145c2a"
_CARD_BORDER = "#f5f5f5"
_CARD_FACE = "#ffffff"
_CARD_BACK = "#1e3a5f"
_CARD_BACK_ACCENT = "#f7b733"
_TEXT_PRIMARY = "#f2f2f2"
_TEXT_MUTED = "#c8e6c9"
_TEXT_ALERT = "#ffdf6b"
_BUTTON_BG = "#f7c548"
_ACTION_BG = "#16532a"
_HIGHLIGHT = "#22a45d"

_CARD_WIDTH = 90
_CARD_HEIGHT = 130
_CARD_SPACING = 12


class BlackjackTable(QWidget, BaseGUI):
    """PyQt5 widget that renders and controls a Blackjack table."""

    def __init__(
        self,
        bankroll: int = 500,
        min_bet: int = 10,
        decks: int = 6,
        rng=None,
        *,
        enable_sounds: bool = True,
        config: Optional[GUIConfig] = None,
    ) -> None:
        QWidget.__init__(self)
        gui_config = config or GUIConfig(
            window_title="Blackjack Table",
            window_width=920,
            window_height=640,
            enable_sounds=enable_sounds,
            enable_animations=True,
            theme_name="dark",
        )
        BaseGUI.__init__(self, root=self, config=gui_config)
        self.sound_manager = initialize_game_soundscape(
            "blackjack",
            module_file=__file__,
            enable_sounds=gui_config.enable_sounds,
            existing_manager=self.sound_manager,
        )
        self.game = BlackjackGame(bankroll=bankroll, min_bet=min_bet, decks=decks, rng=rng)

        self.round_active = False
        self.round_complete = False
        self.dealer_hidden = True
        self.current_hand_index: Optional[int] = None

        self._dealer_timer = QTimer(self)
        self._dealer_timer.setSingleShot(True)
        self._dealer_timer.timeout.connect(self._dealer_draw_step)

        self._build_layout()
        self._refresh_labels()
        self._render_table()
        self._update_buttons()

    def _build_layout(self) -> None:
        self.setWindowTitle("Blackjack Table")
        self.setMinimumSize(920, 640)
        self.setStyleSheet(
            f"""
            QWidget {{
                background-color: {_TABLE_GREEN};
                color: {_TEXT_PRIMARY};
                font-family: 'Segoe UI';
                font-size: 12pt;
            }}
            QPushButton {{
                background-color: {_ACTION_BG};
                color: {_TEXT_PRIMARY};
                border: none;
                padding: 9px 16px;
                border-radius: 6px;
            }}
            QPushButton:disabled {{
                background-color: {_ACTION_BG};
                color: {_TEXT_MUTED};
            }}
        """
        )

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 18)
        main_layout.setSpacing(12)

        header = QWidget(self)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(12)

        title_label = QLabel("Blackjack", header)
        title_label.setStyleSheet(f"color: {_TEXT_ALERT}; font-size: 26pt; font-weight: bold; letter-spacing: 1px;")
        header_layout.addWidget(title_label, alignment=Qt.AlignmentFlag.AlignLeft)

        info_panel = QWidget(header)
        info_layout = QVBoxLayout(info_panel)
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(2)

        bankroll_caption = QLabel("Bankroll", info_panel)
        bankroll_caption.setStyleSheet(f"color: {_TEXT_MUTED}; font-weight: bold;")
        info_layout.addWidget(bankroll_caption, alignment=Qt.AlignmentFlag.AlignRight)

        self.bankroll_label = QLabel("", info_panel)
        font = QFont("Segoe UI", 18, QFont.Weight.Bold)
        self.bankroll_label.setFont(font)
        info_layout.addWidget(self.bankroll_label, alignment=Qt.AlignmentFlag.AlignRight)

        self.shoe_label = QLabel("", info_panel)
        self.shoe_label.setStyleSheet(f"color: {_TEXT_MUTED}; font-size: 10pt;")
        info_layout.addWidget(self.shoe_label, alignment=Qt.AlignmentFlag.AlignRight)

        header_layout.addWidget(info_panel, alignment=Qt.AlignmentFlag.AlignRight)
        main_layout.addWidget(header)

        controls = QWidget(self)
        controls_layout = QHBoxLayout(controls)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.setSpacing(12)

        bet_panel = QWidget(controls)
        bet_layout = QHBoxLayout(bet_panel)
        bet_layout.setContentsMargins(0, 0, 0, 0)
        bet_layout.setSpacing(8)

        wager_caption = QLabel("Wager", bet_panel)
        wager_caption.setStyleSheet(f"color: {_TEXT_MUTED}; font-weight: bold;")
        bet_layout.addWidget(wager_caption)

        self.bet_spin = QSpinBox(bet_panel)
        self.bet_spin.setRange(self.game.min_bet, max(self.game.min_bet, self.game.player.bankroll))
        self.bet_spin.setSingleStep(self.game.min_bet)
        self.bet_spin.setValue(self.game.min_bet)
        self.bet_spin.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
        bet_layout.addWidget(self.bet_spin)

        controls_layout.addWidget(bet_panel, alignment=Qt.AlignmentFlag.AlignLeft)

        self.deal_button = QPushButton("Deal", controls)
        self.deal_button.clicked.connect(self.start_round)
        controls_layout.addWidget(self.deal_button)

        action_panel = QWidget(controls)
        action_layout = QHBoxLayout(action_panel)
        action_layout.setContentsMargins(0, 0, 0, 0)
        action_layout.setSpacing(8)

        self.hit_button = QPushButton("Hit", action_panel)
        self.hit_button.clicked.connect(self.hit)
        action_layout.addWidget(self.hit_button)

        self.stand_button = QPushButton("Stand", action_panel)
        self.stand_button.clicked.connect(self.stand)
        action_layout.addWidget(self.stand_button)

        self.double_button = QPushButton("Double", action_panel)
        self.double_button.clicked.connect(self.double_down)
        action_layout.addWidget(self.double_button)

        self.split_button = QPushButton("Split", action_panel)
        self.split_button.clicked.connect(self.split_hand)
        action_layout.addWidget(self.split_button)

        controls_layout.addWidget(action_panel, alignment=Qt.AlignmentFlag.AlignRight)
        main_layout.addWidget(controls)

        table_frame = QFrame(self)
        table_frame.setStyleSheet(f"background-color: {_TABLE_ACCENT}; border: 4px ridge {_TABLE_ACCENT}; border-radius: 12px;")
        table_layout = QVBoxLayout(table_frame)
        table_layout.setContentsMargins(24, 18, 24, 18)
        table_layout.setSpacing(18)

        dealer_section = QWidget(table_frame)
        dealer_layout = QVBoxLayout(dealer_section)
        dealer_layout.setContentsMargins(0, 0, 0, 0)
        dealer_layout.setSpacing(6)

        dealer_label = QLabel("Dealer", dealer_section)
        dealer_label.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        dealer_layout.addWidget(dealer_label, alignment=Qt.AlignmentFlag.AlignHCenter)

        self.dealer_cards_widget = QWidget(dealer_section)
        self.dealer_cards_layout = QVBoxLayout(self.dealer_cards_widget)
        self.dealer_cards_layout.setContentsMargins(0, 0, 0, 0)
        self.dealer_cards_layout.setSpacing(6)
        dealer_layout.addWidget(self.dealer_cards_widget)

        table_layout.addWidget(dealer_section)

        separator = QFrame(table_frame)
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet(f"color: {_TEXT_MUTED};")
        table_layout.addWidget(separator)

        player_section = QWidget(table_frame)
        player_layout = QVBoxLayout(player_section)
        player_layout.setContentsMargins(0, 0, 0, 0)
        player_layout.setSpacing(6)

        player_label = QLabel("Player", player_section)
        player_label.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        player_layout.addWidget(player_label, alignment=Qt.AlignmentFlag.AlignHCenter)

        self.player_hands_widget = QWidget(player_section)
        self.player_hands_layout = QHBoxLayout(self.player_hands_widget)
        self.player_hands_layout.setContentsMargins(0, 0, 0, 0)
        self.player_hands_layout.setSpacing(12)
        player_layout.addWidget(self.player_hands_widget)

        table_layout.addWidget(player_section)
        main_layout.addWidget(table_frame, stretch=1)

        footer = QWidget(self)
        footer_layout = QVBoxLayout(footer)
        footer_layout.setContentsMargins(0, 0, 0, 0)
        footer_layout.setSpacing(4)

        self.message_label = QLabel("Welcome to Blackjack!", footer)
        self.message_label.setWordWrap(True)
        footer_layout.addWidget(self.message_label)

        main_layout.addWidget(footer)

    def _refresh_labels(self) -> None:
        bankroll = self.game.player.bankroll
        self.bankroll_label.setText(f"${bankroll:,}")
        cards_remaining = len(self.game.shoe.cards)
        decks = self.game.shoe.decks
        self.shoe_label.setText(f"Shoe: {cards_remaining} cards · {decks} decks")

        maximum = max(self.game.min_bet, bankroll)
        self.bet_spin.setRange(self.game.min_bet, maximum)
        self.bet_spin.setSingleStep(self.game.min_bet)
        if not self.game.can_continue():
            self.bet_spin.setValue(self.game.player.bankroll)

    def _set_message(self, text: str, *, highlight_color: str = _TEXT_ALERT) -> None:
        """Update the status label and trigger the highlight animation."""

        self.message_label.setText(text)
        self.animate_highlight(self.message_label, highlight_color=highlight_color)

    def _render_table(self) -> None:
        self._clear_layout(self.dealer_cards_layout)
        self._clear_layout(self.player_hands_layout)

        dealer_hand = self.game.dealer_hand if self.game.dealer.hands else None
        if dealer_hand:
            dealer_view = self._create_hand_view(dealer_hand, hide_hole=self.dealer_hidden)
            self.dealer_cards_layout.addWidget(dealer_view, alignment=Qt.AlignmentFlag.AlignHCenter)
            info = self._hand_summary(dealer_hand, dealer=True, hide_hole=self.dealer_hidden)
            info_label = QLabel(info, self.dealer_cards_widget)
            info_label.setStyleSheet(f"color: {_TEXT_MUTED};")
            info_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
            self.dealer_cards_layout.addWidget(info_label)
            if not self.dealer_hidden:
                self.animate_highlight(dealer_view, highlight_color=_HIGHLIGHT)

        for index, hand in enumerate(self.game.player.hands):
            highlight = index == self.current_hand_index and self.round_active
            container = QFrame(self.player_hands_widget)
            background = _HIGHLIGHT if highlight else _ACTION_BG
            container.setStyleSheet(f"background-color: {background}; border: 3px solid {_TABLE_ACCENT}; border-radius: 12px;")
            hand_layout = QVBoxLayout(container)
            hand_layout.setContentsMargins(12, 12, 12, 12)
            hand_layout.setSpacing(8)

            header = QWidget(container)
            header_layout = QHBoxLayout(header)
            header_layout.setContentsMargins(0, 0, 0, 0)
            header_layout.setSpacing(6)

            if len(self.game.player.hands) > 1:
                label_text = f"Hand {index + 1}"
            else:
                label_text = "Your hand"
            label = QLabel(label_text, header)
            label.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
            header_layout.addWidget(label)

            bet_label = QLabel(f"Bet ${hand.bet:,}", header)
            bet_label.setFont(QFont("Segoe UI", 11))
            bet_label.setStyleSheet(f"color: {_TEXT_ALERT};")
            header_layout.addWidget(bet_label, alignment=Qt.AlignmentFlag.AlignRight)

            hand_layout.addWidget(header)

            cards_view = self._create_hand_view(hand, hide_hole=False)
            hand_layout.addWidget(cards_view)
            if highlight or len(hand.cards) >= 2:
                self.animate_highlight(cards_view, highlight_color=_HIGHLIGHT)

            summary = QLabel(self._hand_summary(hand), container)
            summary.setStyleSheet(f"color: {_TEXT_MUTED};")
            hand_layout.addWidget(summary, alignment=Qt.AlignmentFlag.AlignHCenter)

            self.player_hands_layout.addWidget(container)

        self.player_hands_layout.addStretch(1)

    def _create_hand_view(self, hand: BlackjackHand, *, hide_hole: bool) -> QGraphicsView:
        scene = QGraphicsScene()
        x = 0
        for index, card in enumerate(hand.cards):
            hidden = hide_hole and index == 1
            self._add_card(scene, card, hidden, x)
            x += _CARD_WIDTH + _CARD_SPACING

        width = max(_CARD_WIDTH, x - _CARD_SPACING) + 12
        scene.setSceneRect(0, 0, width, _CARD_HEIGHT + 12)

        view = QGraphicsView(scene)
        view.setFixedSize(width + 6, _CARD_HEIGHT + 18)
        view.setStyleSheet(f"background: {_TABLE_ACCENT}; border: none;")
        view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        return view

    def _add_card(self, scene: QGraphicsScene, card: Card, hidden: bool, x: int) -> None:
        pen = QPen(QColor(_CARD_BORDER))
        pen.setWidth(3)
        brush_color = _CARD_BACK if hidden else _CARD_FACE
        rect = scene.addRect(
            x + 6,
            6,
            _CARD_WIDTH - 12,
            _CARD_HEIGHT - 12,
            pen,
            QColor(brush_color),
        )
        rect.setZValue(1)

        if hidden:
            pen = QPen(QColor(_CARD_BACK_ACCENT))
            pen.setWidth(3)
            scene.addLine(x + 12, 12, x + _CARD_WIDTH - 12, _CARD_HEIGHT - 12, pen)
            scene.addLine(x + 12, _CARD_HEIGHT - 12, x + _CARD_WIDTH - 12, 12, pen)
            text = scene.addText("★")
            text.setDefaultTextColor(QColor(_TEXT_PRIMARY))
            text.setFont(QFont("Segoe UI", 30))
            text.setPos(x + (_CARD_WIDTH / 2) - 16, (_CARD_HEIGHT / 2) - 24)
        else:
            suit = card.suit
            rank_display = "10" if card.rank == "T" else card.rank
            suit_color = QColor("#d32f2f" if suit in (Suit.HEARTS, Suit.DIAMONDS) else "#1c1c1c")

            top_text = scene.addText(rank_display)
            top_text.setDefaultTextColor(suit_color)
            top_text.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
            top_text.setPos(x + 14, 12)

            bottom_text = scene.addText(rank_display)
            bottom_text.setDefaultTextColor(suit_color)
            bottom_text.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
            bottom_text.setPos(x + _CARD_WIDTH - 40, _CARD_HEIGHT - 40)

            center_text = scene.addText(suit.value)
            center_text.setDefaultTextColor(suit_color)
            center_text.setFont(QFont("Segoe UI Symbol", 32))
            center_text.setPos(x + (_CARD_WIDTH / 2) - 20, (_CARD_HEIGHT / 2) - 34)

    def _hand_summary(self, hand: BlackjackHand, *, dealer: bool = False, hide_hole: bool = False) -> str:
        if hide_hole:
            visible = BlackjackHand(cards=[hand.cards[0]])
            total = visible.best_total()
            return f"Showing {total}"

        parts: list[str] = []
        if hand.is_blackjack():
            parts.append("Blackjack!")
        elif hand.is_bust():
            parts.append("Bust")
        else:
            parts.append(f"Total {hand.best_total()}")
            if hand.is_soft() and hand.best_total() <= 21:
                parts.append("Soft")

        if hand.doubled:
            parts.append("Doubled")
        if hand.split_from is not None:
            parts.append("Split")
        if dealer and hand.stood and not hand.is_bust():
            parts.append("Stood")

        return " · ".join(parts)

    def _clear_layout(self, layout) -> None:
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def _update_buttons(self) -> None:
        if self.round_active:
            self._set_button_enabled(self.deal_button, False)

            for button in (self.hit_button, self.stand_button, self.double_button, self.split_button):
                self._set_button_enabled(button, False)

            hand = self._current_hand()
            if hand:
                actions = self.game.player_actions(hand)
                if "hit" in actions:
                    self._set_button_enabled(self.hit_button, True, highlight=True)
                if "stand" in actions:
                    self._set_button_enabled(self.stand_button, True, highlight=True)
                if "double" in actions:
                    self._set_button_enabled(self.double_button, True, highlight=True)
                if "split" in actions:
                    self._set_button_enabled(self.split_button, True, highlight=True)
        else:
            can_deal = self.game.can_continue()
            text = "Deal next hand" if self.round_complete else "Deal"
            self.deal_button.setText(text)
            self._set_button_enabled(self.deal_button, can_deal, primary=True)

            for button in (self.hit_button, self.stand_button, self.double_button, self.split_button):
                self._set_button_enabled(button, False)

    def _set_button_enabled(self, button: QPushButton, enabled: bool, *, highlight: bool = False, primary: bool = False) -> None:
        button.setEnabled(enabled)
        if not enabled:
            button.setStyleSheet(f"background-color: {_ACTION_BG}; color: {_TEXT_MUTED};")
        elif primary:
            button.setStyleSheet(f"background-color: {_BUTTON_BG}; color: #1c1c1c; font-weight: bold; padding: 10px 18px; border-radius: 6px;")
        elif highlight:
            button.setStyleSheet(f"background-color: {_HIGHLIGHT}; color: {_TEXT_PRIMARY}; font-weight: bold;")
        else:
            button.setStyleSheet(f"background-color: {_ACTION_BG}; color: {_TEXT_PRIMARY};")

    def _current_hand(self) -> Optional[BlackjackHand]:
        if self.current_hand_index is not None and self.current_hand_index < len(self.game.player.hands):
            return self.game.player.hands[self.current_hand_index]
        return None

    def start_round(self) -> None:
        if self.round_active:
            return

        if self.round_complete:
            self.game.reset()
            self.round_complete = False

        if not self.game.can_continue():
            self._set_message("Insufficient bankroll to place the minimum bet.")
            return

        bet = max(self.game.min_bet, int(self.bet_spin.value()))
        if bet > self.game.player.bankroll:
            bet = self.game.player.bankroll
            self.bet_spin.setValue(bet)

        try:
            self.game.start_round(bet)
        except ValueError as exc:
            self._set_message(str(exc))
            return

        self.round_active = True
        self.dealer_hidden = True
        self.current_hand_index = 0
        self._set_message("Cards dealt. Make your move!")

        self._refresh_labels()
        self._render_table()
        self._update_buttons()

        player_hand = self.game.player.hands[0]
        if self.game.dealer_hand.is_blackjack() or player_hand.is_blackjack():
            self.dealer_hidden = False
            self._set_message("Blackjack! Checking dealer's hand...")
            self._render_table()
            QTimer.singleShot(800, self.finish_round)
            return

        if player_hand.best_total() == 21:
            player_hand.stood = True
            QTimer.singleShot(600, self._advance_hand)

    def hit(self) -> None:
        hand = self._current_hand()
        if not hand:
            return

        card = self.game.hit(hand)
        self._set_message(f"Hit: drew {card}.")
        self._render_table()

        if hand.is_bust():
            hand.stood = True
            self._set_message("Bust! Hand is out of play.")
            QTimer.singleShot(500, self._advance_hand)
        elif hand.best_total() == 21:
            hand.stood = True
            self._set_message("21! Standing automatically.")
            QTimer.singleShot(500, self._advance_hand)
        else:
            self._update_buttons()

    def stand(self) -> None:
        hand = self._current_hand()
        if not hand:
            return

        self.game.stand(hand)
        self._set_message("Stand. Moving to next hand or dealer's turn.")
        self._render_table()
        QTimer.singleShot(400, self._advance_hand)

    def double_down(self) -> None:
        hand = self._current_hand()
        if not hand:
            return

        try:
            card = self.game.double_down(hand)
        except ValueError as exc:
            self._set_message(str(exc))
            return

        self._set_message(f"Double down! Drew {card}, standing on {hand.best_total()}.")
        self._refresh_labels()
        self._render_table()
        QTimer.singleShot(500, self._advance_hand)

    def split_hand(self) -> None:
        hand = self._current_hand()
        if not hand:
            return

        try:
            self.game.split(hand)
        except ValueError as exc:
            self._set_message(str(exc))
            return

        self._set_message("Split successful — play each hand in turn.")
        self._refresh_labels()
        self._render_table()
        self._update_buttons()

    def _advance_hand(self) -> None:
        if not self.round_active:
            return

        next_index: Optional[int] = None
        for idx, hand in enumerate(self.game.player.hands):
            if not (hand.is_bust() or hand.is_blackjack() or hand.stood):
                next_index = idx
                break

        self.current_hand_index = next_index
        if next_index is None:
            self._begin_dealer_turn()
        else:
            self._render_table()
            self._update_buttons()

    def _begin_dealer_turn(self) -> None:
        self.current_hand_index = None
        self.dealer_hidden = False
        self._render_table()
        self._update_buttons()

        if all(hand.is_bust() for hand in self.game.player.hands):
            QTimer.singleShot(600, self.finish_round)
            return

        self.game.dealer_hand.stood = False
        self._dealer_timer.start(600)

    def _dealer_draw_step(self) -> None:
        hand = self.game.dealer_hand
        if hand.best_total() < 17 or (hand.best_total() == 17 and hand.is_soft()):
            card = self.game.hit(hand)
            self._set_message(f"Dealer draws {card}.")
            self._render_table()
            self._dealer_timer.start(700)
        else:
            hand.stood = True
            self._set_message("Dealer stands.")
            self._render_table()
            QTimer.singleShot(700, self.finish_round)

    def finish_round(self) -> None:
        if not self.round_active:
            return

        if self._dealer_timer.isActive():
            self._dealer_timer.stop()

        outcomes_by_player = self.game.settle_round()
        player_outcomes = outcomes_by_player.get(self.game.player, [])

        messages: list[str] = []
        for idx, (hand, outcome) in enumerate(zip(self.game.player.hands, player_outcomes), start=1):
            descriptor = self._describe_outcome(hand, outcome)
            label = f"Hand {idx}: " if len(self.game.player.hands) > 1 else ""
            messages.append(f"{label}{descriptor}")

        summary = " | ".join(messages)
        text = f"{summary} Bankroll now ${self.game.player.bankroll:,}."
        if not self.game.can_continue():
            text += " Game over."
        self._set_message(text)

        self.round_active = False
        self.round_complete = True
        self.current_hand_index = None
        self._refresh_labels()
        self._render_table()
        self._update_buttons()

    def _describe_outcome(self, hand: BlackjackHand, outcome: Outcome) -> str:
        mapping = {
            Outcome.PLAYER_BLACKJACK: "Blackjack pays 3:2!",
            Outcome.PLAYER_WIN: "Win",
            Outcome.DEALER_BUST: "Dealer busts, you win!",
            Outcome.PUSH: "Push",
            Outcome.PLAYER_LOSS: "You lose",
            Outcome.PLAYER_BUST: "Bust",
        }
        base = mapping.get(outcome, outcome.value.replace("_", " ").title())

        if outcome in {Outcome.PLAYER_WIN, Outcome.DEALER_BUST, Outcome.PLAYER_BLACKJACK}:
            base = f"{base} (+${hand.bet:,})"
        elif outcome == Outcome.PUSH:
            base = f"{base} (stake returned)"
        else:
            base = f"{base} (-${hand.bet:,})"
        return base


def run_gui(
    *,
    bankroll: int = 500,
    min_bet: int = 10,
    decks: int = 6,
    rng=None,
) -> None:
    app = QApplication.instance()
    if app is None:
        import sys

        app = QApplication(sys.argv)

    window = BlackjackTable(bankroll=bankroll, min_bet=min_bet, decks=decks, rng=rng)
    window.show()
    app.exec()


__all__ = ["BlackjackTable", "run_gui"]
