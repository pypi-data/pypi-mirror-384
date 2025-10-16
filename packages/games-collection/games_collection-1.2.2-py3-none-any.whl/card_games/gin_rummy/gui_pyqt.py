"""PyQt5-powered graphical interface for the Gin Rummy card game.

The layout mirrors the Tkinter implementation while embracing Qt idioms. Player
panels, meld analysis, and round logs are arranged using Qt layouts so that the
game flow is easy to follow. The hand view renders cards as selectable buttons
to preserve the discard workflow, and meld/deadwood details stay in sync with
the game engine.
"""

from __future__ import annotations

import sys
from typing import Dict, List, Optional

from card_games.common.cards import Card, format_cards
from card_games.common.soundscapes import initialize_game_soundscape
from card_games.gin_rummy.game import GinRummyGame, GinRummyPlayer, HandAnalysis, Meld, MeldType
from common.gui_base_pyqt import PYQT5_AVAILABLE, BaseGUI, GUIConfig

if PYQT5_AVAILABLE:  # pragma: no cover - import guarded by availability
    from PyQt5.QtCore import Qt
    from PyQt5.QtWidgets import QApplication, QHBoxLayout, QLabel, QMainWindow, QPushButton, QScrollArea, QTextEdit, QVBoxLayout, QWidget
else:  # pragma: no cover - provide shims for type checkers
    Qt = None  # type: ignore
    QApplication = None  # type: ignore
    QHBoxLayout = None  # type: ignore
    QLabel = None  # type: ignore
    QMainWindow = object  # type: ignore
    QPushButton = None  # type: ignore
    QScrollArea = None  # type: ignore
    QTextEdit = None  # type: ignore
    QVBoxLayout = None  # type: ignore
    QWidget = None  # type: ignore


def _format_meld(meld: Meld) -> str:
    """Return a short textual description for ``meld``."""

    label = "Set" if meld.meld_type == MeldType.SET else "Run"
    return f"{label}: {format_cards(meld.cards)}"


class GinRummyPyQtGUI(QMainWindow, BaseGUI):
    """PyQt5 interface that visualises a Gin Rummy match."""

    def __init__(
        self,
        *,
        players: Optional[List[GinRummyPlayer]] = None,
        enable_sounds: bool = True,
        config: Optional[GUIConfig] = None,
    ) -> None:
        if not PYQT5_AVAILABLE:  # pragma: no cover - defensive guard
            raise RuntimeError("PyQt5 is required to launch the Gin Rummy GUI")

        QMainWindow.__init__(self)
        config = config or GUIConfig(
            window_title="Gin Rummy",
            window_width=1024,
            window_height=780,
            log_height=12,
            log_width=100,
            enable_sounds=enable_sounds,
            enable_animations=True,
        )
        BaseGUI.__init__(self, root=self, config=config)
        self.sound_manager = initialize_game_soundscape(
            "gin_rummy",
            module_file=__file__,
            enable_sounds=config.enable_sounds,
            existing_manager=self.sound_manager,
        )

        self.players = players or [
            GinRummyPlayer(name="You", is_ai=False),
            GinRummyPlayer(name="AI", is_ai=True),
        ]
        self.game = GinRummyGame(self.players)
        self.round_number = 0
        self.round_over = False
        self.phase: str = "waiting"
        self.selected_card: Optional[Card] = None
        self.log_index = 0

        self.score_labels: List[QLabel] = []
        self.deadwood_labels: List[QLabel] = []
        self.player_status_labels: List[QLabel] = []
        self.card_buttons: Dict[Card, QPushButton] = {}

        self.status_label: QLabel
        self.top_discard_label: QLabel
        self.stock_count_label: QLabel
        self.selection_label: QLabel
        self.melds_label: QLabel
        self.deadwood_cards_label: QLabel
        self.hand_container: QWidget
        self.hand_layout: QHBoxLayout
        self.log_widget: QTextEdit

        self.build_layout()
        self.apply_theme()
        self._update_controls()

    # ------------------------------------------------------------------
    # Layout and display helpers
    # ------------------------------------------------------------------
    def build_layout(self) -> None:
        central = QWidget(self)
        self.setCentralWidget(central)

        main_layout = QVBoxLayout()
        main_layout.setSpacing(12)
        central.setLayout(main_layout)

        # Player panels -------------------------------------------------------
        info_container = QWidget(central)
        info_layout = QHBoxLayout()
        info_layout.setSpacing(12)
        info_container.setLayout(info_layout)

        for player in self.players:
            panel = self.create_label_frame(info_container, player.name)
            panel_layout = QVBoxLayout()
            panel_layout.setContentsMargins(10, 8, 10, 8)
            panel.setLayout(panel_layout)

            score_label = QLabel("Score: 0", panel)
            score_label.setStyleSheet("font-weight: bold; font-size: 14pt;")
            panel_layout.addWidget(score_label)

            deadwood_label = QLabel("Deadwood: —", panel)
            deadwood_label.setStyleSheet("color: #666666;")
            panel_layout.addWidget(deadwood_label)

            status_badge = QLabel("Waiting", panel)
            status_badge.setAlignment(Qt.AlignmentFlag.AlignLeft)
            status_badge.setStyleSheet("padding: 4px 8px; border-radius: 4px; font-weight: bold;")
            panel_layout.addWidget(status_badge)

            panel_layout.addStretch()
            info_layout.addWidget(panel)

            self.score_labels.append(score_label)
            self.deadwood_labels.append(deadwood_label)
            self.player_status_labels.append(status_badge)

        main_layout.addWidget(info_container)

        # Status and pile information ----------------------------------------
        self.status_label = QLabel("Click 'Start Next Round' to begin.", central)
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet("font-size: 13pt; color: #0D6EFD;")
        main_layout.addWidget(self.status_label)

        pile_widget = QWidget(central)
        pile_layout = QHBoxLayout()
        pile_layout.setContentsMargins(0, 0, 0, 0)
        pile_layout.setSpacing(20)
        pile_widget.setLayout(pile_layout)

        self.top_discard_label = QLabel("Discard pile: —", pile_widget)
        pile_layout.addWidget(self.top_discard_label)

        self.stock_count_label = QLabel("Stock remaining: —", pile_widget)
        pile_layout.addWidget(self.stock_count_label)

        pile_layout.addStretch()

        self.selection_label = QLabel("No card selected.", pile_widget)
        self.selection_label.setStyleSheet("color: #666666;")
        pile_layout.addWidget(self.selection_label, alignment=Qt.AlignmentFlag.AlignRight)

        main_layout.addWidget(pile_widget)

        # Hand visualisation --------------------------------------------------
        hand_group = self.create_label_frame(central, "Your Hand")
        hand_layout = QVBoxLayout()
        hand_group.setLayout(hand_layout)

        hand_scroll = QScrollArea(hand_group)
        hand_scroll.setWidgetResizable(True)
        self.hand_container = QWidget(hand_scroll)
        self.hand_layout = QHBoxLayout()
        self.hand_layout.setContentsMargins(8, 8, 8, 8)
        self.hand_layout.setSpacing(6)
        self.hand_container.setLayout(self.hand_layout)
        hand_scroll.setWidget(self.hand_container)
        hand_layout.addWidget(hand_scroll)

        main_layout.addWidget(hand_group)

        # Meld analysis -------------------------------------------------------
        meld_group = self.create_label_frame(central, "Meld Analysis")
        meld_layout = QVBoxLayout()
        meld_group.setLayout(meld_layout)

        self.melds_label = QLabel("Melds will appear here once available.", meld_group)
        self.melds_label.setWordWrap(True)
        meld_layout.addWidget(self.melds_label)

        self.deadwood_cards_label = QLabel("Deadwood cards will be highlighted during play.", meld_group)
        self.deadwood_cards_label.setWordWrap(True)
        self.deadwood_cards_label.setStyleSheet("color: #666666;")
        meld_layout.addWidget(self.deadwood_cards_label)

        main_layout.addWidget(meld_group)

        # Action buttons ------------------------------------------------------
        actions_widget = QWidget(central)
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(8)
        actions_widget.setLayout(actions_layout)

        self.take_upcard_button = QPushButton("Take Upcard", actions_widget)
        self.take_upcard_button.clicked.connect(self.on_take_initial_upcard)
        actions_layout.addWidget(self.take_upcard_button)

        self.pass_upcard_button = QPushButton("Pass Upcard", actions_widget)
        self.pass_upcard_button.clicked.connect(self.on_pass_initial_upcard)
        actions_layout.addWidget(self.pass_upcard_button)

        self.draw_stock_button = QPushButton("Draw Stock", actions_widget)
        self.draw_stock_button.clicked.connect(self.on_draw_from_stock)
        actions_layout.addWidget(self.draw_stock_button)

        self.draw_discard_button = QPushButton("Draw Discard", actions_widget)
        self.draw_discard_button.clicked.connect(self.on_draw_from_discard)
        actions_layout.addWidget(self.draw_discard_button)

        self.knock_button = QPushButton("Knock / Gin", actions_widget)
        self.knock_button.clicked.connect(self.on_knock)
        actions_layout.addWidget(self.knock_button)

        self.discard_button = QPushButton("Discard Selected", actions_widget)
        self.discard_button.clicked.connect(self.on_discard)
        actions_layout.addWidget(self.discard_button)

        actions_layout.addStretch()

        self.next_round_button = QPushButton("Start Next Round", actions_widget)
        self.next_round_button.clicked.connect(self.start_next_round)
        actions_layout.addWidget(self.next_round_button)

        main_layout.addWidget(actions_widget)

        # Log -----------------------------------------------------------------
        log_group = self.create_label_frame(central, "Round Log")
        log_layout = QVBoxLayout()
        log_group.setLayout(log_layout)
        self.log_widget = self.create_log_widget(log_group)
        log_layout.addWidget(self.log_widget)

        main_layout.addWidget(log_group, stretch=1)

    def update_display(self) -> None:
        for idx, player in enumerate(self.players):
            analysis = self.game.analyze_hand(player.hand)
            self.score_labels[idx].setText(f"Score: {player.score}")
            self.deadwood_labels[idx].setText(f"Deadwood: {analysis.deadwood_total}")
            if idx == 0:
                self._update_meld_display(analysis)

        self._render_hand()

        if self.game.discard_pile:
            top_card = self.game.discard_pile[-1]
            self.top_discard_label.setText(f"Discard pile: {top_card} (total {len(self.game.discard_pile)})")
        else:
            self.top_discard_label.setText("Discard pile: empty")

        self.stock_count_label.setText(f"Stock remaining: {len(self.game.deck.cards)}")

        if self.selected_card and self.phase == "discard":
            self.selection_label.setText(f"Selected discard: {self.selected_card}")
        elif self.phase == "discard":
            self.selection_label.setText("Select a card to discard or knock.")
        else:
            self.selection_label.setText("No card selected.")

        self._update_player_badges()

    # ------------------------------------------------------------------
    # Shortcut registration
    # ------------------------------------------------------------------
    def _setup_shortcuts(self) -> None:
        super()._setup_shortcuts()
        if not PYQT5_AVAILABLE:  # pragma: no cover - defensive
            return
        self.register_shortcut("S", self.on_draw_from_stock, "Draw from stock")
        self.register_shortcut("D", self.on_draw_from_discard, "Draw from discard")
        self.register_shortcut("K", self.on_knock, "Knock or declare gin")
        self.register_shortcut("G", self.on_knock, "Knock or declare gin")

    # ------------------------------------------------------------------
    # Game control logic
    # ------------------------------------------------------------------
    def start_next_round(self) -> None:
        if self.game.is_game_over():
            self.status_label.setText("Game over. Close the window to exit.")
            return

        self.round_number += 1
        self.round_over = False
        self.selected_card = None
        self.phase = "waiting"
        self.game.deal_cards()
        self.log_index = 0
        self.clear_log(self.log_widget)

        self.log_message(
            self.log_widget,
            f"--- Round {self.round_number} begins. Dealer: {self.players[self.game.dealer_idx].name} ---",
        )
        if self.game.discard_pile:
            self.log_message(
                self.log_widget,
                f"Opening upcard: {self.game.discard_pile[-1]}",
            )

        self._prepare_next_action()
        self.update_display()
        self._update_controls()
        self._process_ai_turns()

    def on_take_initial_upcard(self) -> None:
        if self.round_over or not self.game.initial_upcard_phase:
            return
        if not self.game.can_take_initial_upcard(0):
            self.status_label.setText("You cannot take the upcard right now.")
            return
        card = self.game.take_initial_upcard(0)
        self._flush_turn_log()
        self.players[0].hand.sort(key=lambda c: (c.suit.value, c.value))
        self.phase = "discard"
        self.status_label.setText(f"You take {card}. Select a different card to discard or knock.")
        self.update_display()
        self._update_controls()

    def on_pass_initial_upcard(self) -> None:
        if self.round_over or not self.game.initial_upcard_phase:
            return
        if not self.game.can_take_initial_upcard(0):
            self.status_label.setText("It is not your turn to act on the upcard.")
            return
        self.game.pass_initial_upcard(0)
        self._flush_turn_log()
        self._prepare_next_action(override_message="Waiting for opponent's decision...")
        self.update_display()
        self._update_controls()
        self._process_ai_turns()

    def on_draw_from_stock(self) -> None:
        if self.round_over or self.phase != "draw":
            return
        card = self.game.draw_from_stock()
        self.players[0].hand.append(card)
        self.players[0].hand.sort(key=lambda c: (c.suit.value, c.value))
        self._flush_turn_log()
        self.phase = "discard"
        self.status_label.setText(f"You draw {card} from the stock.")
        self.update_display()
        self._update_controls()

    def on_draw_from_discard(self) -> None:
        if self.round_over or self.phase != "draw":
            return
        if not self.game.discard_pile or not self.game.can_draw_from_discard(0):
            self.status_label.setText("You cannot draw from the discard pile right now.")
            return
        card = self.game.draw_from_discard()
        self.players[0].hand.append(card)
        self.players[0].hand.sort(key=lambda c: (c.suit.value, c.value))
        self._flush_turn_log()
        self.phase = "discard"
        self.status_label.setText(f"You take {card} from the discard pile. Choose a discard or knock.")
        self.update_display()
        self._update_controls()

    def on_select_card(self, card: Card) -> None:
        if self.phase != "discard" or self.round_over:
            return
        if self.selected_card == card:
            self.selected_card = None
        else:
            self.selected_card = card
        self.update_display()
        self._update_controls()

    def on_discard(self) -> None:
        if self.round_over or self.phase != "discard":
            return
        if not self.selected_card:
            self.status_label.setText("Select a card to discard first.")
            return
        try:
            self.game.discard(0, self.selected_card)
        except ValueError as exc:
            self.status_label.setText(str(exc))
            return
        self.players[0].hand.sort(key=lambda c: (c.suit.value, c.value))
        discarded = self.selected_card
        self.selected_card = None
        self._flush_turn_log()
        self._prepare_next_action(override_message=f"You discard {discarded}. Waiting for opponent...")
        self.update_display()
        self._update_controls()
        self._process_ai_turns()

    def on_knock(self) -> None:
        if self.round_over or self.phase != "discard":
            return
        analysis = self.game.analyze_hand(self.players[0].hand)
        if analysis.deadwood_total > 10:
            self.status_label.setText("You need 10 or fewer deadwood points to knock.")
            return
        if analysis.deadwood_total == 0:
            self.log_message(self.log_widget, f"{self.players[0].name} declares GIN!")
        else:
            self.log_message(
                self.log_widget,
                f"{self.players[0].name} knocks with {analysis.deadwood_total} deadwood.",
            )
        self._finish_round(knocker_idx=0)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _render_hand(self) -> None:
        while self.hand_layout.count():
            item = self.hand_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        self.card_buttons.clear()

        theme = self.current_theme
        for card in sorted(self.players[0].hand, key=lambda c: (c.suit.value, c.value)):
            button = QPushButton(str(card), self.hand_container)
            button.setCheckable(True)
            button.setChecked(card == self.selected_card)
            button.clicked.connect(lambda checked, c=card: self.on_select_card(c))
            if card == self.selected_card:
                button.setStyleSheet(f"background-color: {theme.colors.primary}; color: {theme.colors.button_active_fg};" "font-weight: bold;")
            else:
                button.setStyleSheet("")
            self.hand_layout.addWidget(button)
            self.card_buttons[card] = button

        self.hand_layout.addStretch()

    def _update_meld_display(self, analysis: HandAnalysis) -> None:
        if analysis.melds:
            meld_lines = "\n".join(_format_meld(meld) for meld in analysis.melds)
            self.melds_label.setText(meld_lines)
        else:
            self.melds_label.setText("No melds detected yet.")

        if analysis.deadwood_cards:
            self.deadwood_cards_label.setText(f"Deadwood cards: {format_cards(analysis.deadwood_cards)}")
        else:
            self.deadwood_cards_label.setText("No deadwood cards!")

    def _update_player_badges(self) -> None:
        colors = self.current_theme.colors
        for idx, badge in enumerate(self.player_status_labels):
            text = "Waiting"
            bg = colors.secondary
            fg = colors.foreground

            if self.round_over:
                text = "Round Complete"
                bg = colors.info
                fg = colors.background
            elif self.game.initial_upcard_phase and self.game.can_take_initial_upcard(idx):
                text = "Upcard Decision"
                bg = colors.warning
                fg = colors.background
            elif not self.game.initial_upcard_phase and self.game.current_player_idx == idx:
                if idx == 0 and self.phase == "discard":
                    text = "Choose Discard"
                    bg = colors.warning
                    fg = colors.background
                elif idx == 0 and self.phase == "draw":
                    text = "Draw Now"
                    bg = colors.warning
                    fg = colors.background
                else:
                    text = "Active Turn"
                    bg = colors.primary
                    fg = colors.background

            badge.setText(text)
            badge.setStyleSheet(f"background-color: {bg}; color: {fg}; padding: 4px 8px; border-radius: 4px; font-weight: bold;")

    def _prepare_next_action(self, *, override_message: Optional[str] = None) -> None:
        if self.round_over:
            message = "Round complete. Review the summary and start the next round."
            if self.game.is_game_over():
                winner = self.game.get_winner()
                message = f"Game over! {winner.name} wins with {winner.score} points."
            self.phase = "round-complete"
        elif self.game.initial_upcard_phase:
            if self.game.can_take_initial_upcard(0):
                top_card = self.game.discard_pile[-1] if self.game.discard_pile else "the upcard"
                message = f"Opening upcard {top_card}: take it or pass."
                self.phase = "initial-offer"
            else:
                message = "Waiting for opponent's decision..."
                self.phase = "waiting"
        else:
            if self.game.current_player_idx == 0:
                if self.game.current_turn_draw is None:
                    message = "Draw from the stock or the discard pile."
                    self.phase = "draw"
                else:
                    message = "Select a discard or declare knock/gin."
                    self.phase = "discard"
            else:
                message = "Waiting for opponent..."
                self.phase = "waiting"

        if override_message is not None:
            message = override_message
        self.status_label.setText(message)

    def _flush_turn_log(self) -> None:
        while self.log_index < len(self.game.turn_log):
            entry = self.game.turn_log[self.log_index]
            self.log_message(self.log_widget, entry)
            self.log_index += 1

    def _execute_ai_turn(self, player_idx: int) -> None:
        player = self.players[player_idx]
        if self.game.current_turn_draw is None:
            top_card = self.game.discard_pile[-1] if self.game.discard_pile else None
            if top_card and self.game.can_draw_from_discard(player_idx) and self.game.should_draw_discard(player, top_card):
                card = self.game.draw_from_discard()
            else:
                card = self.game.draw_from_stock()
            player.hand.append(card)
            player.hand.sort(key=lambda c: (c.suit.value, c.value))
            self._flush_turn_log()

        analysis = self.game.analyze_hand(player.hand)
        if analysis.deadwood_total == 0:
            self.log_message(self.log_widget, f"{player.name} declares GIN!")
            self._finish_round(knocker_idx=player_idx)
            return
        if analysis.deadwood_total <= 5:
            self.log_message(
                self.log_widget,
                f"{player.name} knocks with {analysis.deadwood_total} deadwood.",
            )
            self._finish_round(knocker_idx=player_idx)
            return

        discard_card = self.game.suggest_discard(player)
        self.game.discard(player_idx, discard_card)
        player.hand.sort(key=lambda c: (c.suit.value, c.value))
        self._flush_turn_log()

    def _process_ai_turns(self) -> None:
        while not self.round_over:
            if self.game.initial_upcard_phase:
                idx = self.game.initial_offer_order[self.game.initial_offer_position]
                player = self.players[idx]
                if not player.is_ai:
                    break
                top_card = self.game.discard_pile[-1] if self.game.discard_pile else None
                if top_card and self.game.should_draw_discard(player, top_card):
                    self.game.take_initial_upcard(idx)
                    self._flush_turn_log()
                    self._execute_ai_turn(idx)
                else:
                    self.game.pass_initial_upcard(idx)
                    self._flush_turn_log()
                continue

            current_idx = self.game.current_player_idx
            if current_idx >= len(self.players) or not self.players[current_idx].is_ai:
                break
            self._execute_ai_turn(current_idx)
            if self.round_over:
                break

        self._prepare_next_action()
        self.update_display()
        self._update_controls()

    def _finish_round(self, knocker_idx: int) -> None:
        if self.round_over:
            return

        opponent_idx = (knocker_idx + 1) % len(self.players)
        knocker = self.players[knocker_idx]
        opponent = self.players[opponent_idx]

        summary = self.game.calculate_round_summary(knocker, opponent)
        self.game.record_points(summary)
        self.round_over = True
        self._flush_turn_log()

        knock_label = summary.knock_type.name.replace("_", " ").title()
        self.log_message(
            self.log_widget,
            f"Round ends: {summary.knocker} ({knock_label}).",
        )
        self.log_message(
            self.log_widget,
            "Deadwood — "
            f"{summary.knocker}: {summary.knocker_deadwood}, "
            f"{summary.opponent}: {summary.opponent_deadwood} "
            f"(was {summary.opponent_initial_deadwood}).",
        )

        if summary.melds_shown:
            self.log_message(self.log_widget, "Melds shown:")
            for meld in summary.melds_shown:
                self.log_message(self.log_widget, f"  • {_format_meld(meld)}")
        else:
            self.log_message(self.log_widget, "No melds were revealed.")

        if summary.layoff_cards:
            self.log_message(
                self.log_widget,
                f"Layoff cards: {format_cards(summary.layoff_cards)}",
            )
        else:
            self.log_message(self.log_widget, "No layoff cards were played.")

        self.log_message(self.log_widget, "Points awarded:")
        for name, points in summary.points_awarded.items():
            delta = f"+{points}" if points >= 0 else str(points)
            total = next(p.score for p in self.players if p.name == name)
            self.log_message(self.log_widget, f"  {name}: {delta} (total {total})")

        if self.game.is_game_over():
            winner = self.game.get_winner()
            self.log_message(
                self.log_widget,
                f"Game over! {winner.name} reaches {winner.score} points.",
            )

        self._prepare_next_action()
        self.update_display()
        self._update_controls()

    def _update_controls(self) -> None:
        state_initial = not self.round_over and self.phase == "initial-offer"
        self.take_upcard_button.setEnabled(state_initial)
        self.pass_upcard_button.setEnabled(state_initial)

        state_draw_stock = not self.round_over and self.phase == "draw"
        self.draw_stock_button.setEnabled(state_draw_stock)

        can_draw_discard = not self.round_over and self.phase == "draw" and bool(self.game.discard_pile) and self.game.can_draw_from_discard(0)
        self.draw_discard_button.setEnabled(can_draw_discard)

        analysis = self.game.analyze_hand(self.players[0].hand)
        can_knock = not self.round_over and self.phase == "discard" and analysis.deadwood_total <= 10
        self.knock_button.setEnabled(can_knock)
        if analysis.deadwood_total == 0:
            self.knock_button.setText("Declare Gin")
        else:
            self.knock_button.setText("Knock / Gin")

        can_discard = not self.round_over and self.phase == "discard" and self.selected_card is not None
        self.discard_button.setEnabled(can_discard)

        next_state = self.round_over and not self.game.is_game_over()
        self.next_round_button.setEnabled(next_state)


def run_pyqt_app(*, player_name: str = "You", opponent_name: str = "AI") -> None:
    """Launch the Gin Rummy PyQt5 GUI application."""

    if not PYQT5_AVAILABLE:  # pragma: no cover - defensive branch
        raise RuntimeError("PyQt5 is not available in this environment")

    app = QApplication.instance() or QApplication(sys.argv)
    players = [
        GinRummyPlayer(name=player_name, is_ai=False),
        GinRummyPlayer(name=opponent_name, is_ai=True),
    ]
    window = GinRummyPyQtGUI(players=players)
    window.start_next_round()
    window.show()
    app.exec()


__all__ = ["GinRummyPyQtGUI", "run_pyqt_app"]
