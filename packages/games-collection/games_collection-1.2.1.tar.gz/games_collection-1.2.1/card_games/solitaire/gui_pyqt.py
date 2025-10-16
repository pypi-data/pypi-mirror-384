"""PyQt5-powered graphical interface for Klondike Solitaire.

This module ports the original Tkinter interface to PyQt5, keeping the same
toolbar actions, scoreboard layout, and tableau rendering while embracing Qt's
painting primitives. Custom pile canvases render card stacks using ``QPainter``
so selection outlines and legal drop targets mirror the look-and-feel of the
Tkinter edition. Interaction flows are preserved: players click a pile to
select cards, review the highlighted targets, and click again to commit the
move.

The implementation uses the shared ``BaseGUI`` infrastructure for theming and
keyboard shortcuts, provides status updates that fade using ``QTimer`` and
exposes the familiar actions (draw, auto-play, reset, new deal). The module can
be used as a drop-in replacement for the Tkinter GUI and is wired into the
package entry point.
"""

from __future__ import annotations

import random
from typing import Callable, Optional, Tuple

from card_games.common.cards import Card
from card_games.common.soundscapes import initialize_game_soundscape
from card_games.solitaire.game import Pile, SolitaireGame
from common.gui_base_pyqt import PYQT5_AVAILABLE, BaseGUI, GUIConfig

if PYQT5_AVAILABLE:  # pragma: no cover - Import guarded by availability checks
    from PyQt5.QtCore import QRectF, Qt, QTimer, pyqtSignal
    from PyQt5.QtGui import QColor, QFont, QMouseEvent, QPainter, QPaintEvent, QPen
    from PyQt5.QtWidgets import (
        QApplication,
        QFrame,
        QGridLayout,
        QHBoxLayout,
        QLabel,
        QMainWindow,
        QMessageBox,
        QPushButton,
        QSizePolicy,
        QVBoxLayout,
        QWidget,
    )
else:  # pragma: no cover - Provides placeholders when PyQt5 is missing
    QApplication = None  # type: ignore
    QFrame = None  # type: ignore
    QGridLayout = None  # type: ignore
    QHBoxLayout = None  # type: ignore
    QLabel = None  # type: ignore
    QMessageBox = None  # type: ignore
    QPushButton = None  # type: ignore
    QSizePolicy = None  # type: ignore
    QVBoxLayout = None  # type: ignore
    QWidget = None  # type: ignore
    QMainWindow = None  # type: ignore
    QPointF = None  # type: ignore
    QRectF = None  # type: ignore
    Qt = None  # type: ignore
    QTimer = None  # type: ignore
    QColor = None  # type: ignore
    QFont = None  # type: ignore
    QMouseEvent = None  # type: ignore
    QPaintEvent = None  # type: ignore
    QPainter = None  # type: ignore
    QPen = None  # type: ignore
    pyqtSignal = None  # type: ignore


CARD_WIDTH = 90
CARD_HEIGHT = 120
FACE_DOWN_HEIGHT = 42
FACE_DOWN_SPACING = 18
FACE_UP_SPACING = 32


SelectedSource = Tuple[str, int, int]
TargetKey = Tuple[str, int]


if PYQT5_AVAILABLE:

    class PileContainer(QFrame):
        """Frame wrapper that manages highlight state for a pile."""

        def __init__(
            self,
            *,
            background: str,
            default_border: str,
            selection_border: str,
            target_border: str,
        ) -> None:
            super().__init__()
            self._background = background
            self._default_border = default_border
            self._selection_border = selection_border
            self._target_border = target_border
            self._state = "default"

            self.setFrameShape(QFrame.Shape.NoFrame)
            self.setAutoFillBackground(False)
            layout = QVBoxLayout(self)
            layout.setContentsMargins(6, 6, 6, 6)
            self._apply_state("default")

        def set_highlight(self, state: str) -> None:
            """Update the border colour according to the highlight state."""

            if state == self._state:
                return
            self._apply_state(state)

        def _apply_state(self, state: str) -> None:
            color = {
                "default": self._default_border,
                "selected": self._selection_border,
                "target": self._target_border,
            }.get(state, self._default_border)
            self._state = state
            self.setStyleSheet(("QFrame {" f"background-color: {self._background};" f"border: 2px solid {color};" "border-radius: 10px;" "}"))

    class PileCanvas(QWidget):
        """Custom widget that renders a solitaire pile using QPainter."""

        clicked = pyqtSignal(str, int, float)

        def __init__(
            self,
            gui: "SolitaireWindow",
            pile_type: str,
            index: int,
            *,
            width: int,
            height: int,
            scalable_height: bool = False,
        ) -> None:
            super().__init__()
            self.gui = gui
            self.pile_type = pile_type
            self.index = index
            self.card_positions: list[Tuple[float, float, int]] = []

            self.setMinimumWidth(width)
            if scalable_height:
                self.setMinimumHeight(height)
                self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
            else:
                self.setFixedHeight(height)
            self.setFixedWidth(width)
            self.setMouseTracking(False)

        def paintEvent(self, _event: QPaintEvent) -> None:  # pragma: no cover - GUI paint routine
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            self.card_positions = self.gui.paint_pile(self, painter)

        def mousePressEvent(self, event: QMouseEvent) -> None:  # pragma: no cover - GUI interaction
            if event.button() == Qt.MouseButton.LeftButton:
                self.clicked.emit(self.pile_type, self.index, float(event.pos().y()))
            super().mousePressEvent(event)

        def card_index_at(self, y: float) -> Optional[int]:
            """Return the index of the card at the given Y coordinate."""

            for start_y, end_y, card_index in reversed(self.card_positions):
                if start_y <= y <= end_y:
                    return card_index
            if self.card_positions:
                return self.card_positions[-1][2]
            return None

    class SolitaireWindow(QMainWindow):
        """Main PyQt5 window that visualises and controls ``SolitaireGame``.

        Note: Does not inherit from BaseGUI as it's designed for Tkinter,
        and would cause metaclass conflicts with QMainWindow.
        """

        def __init__(
            self,
            game: SolitaireGame,
            *,
            enable_sounds: bool = True,
            config: Optional[GUIConfig] = None,
            new_game_factory: Optional[Callable[[], SolitaireGame]] = None,
        ) -> None:
            if not PYQT5_AVAILABLE:
                raise RuntimeError("PyQt5 is not available on this system.")

            QMainWindow.__init__(self)
            gui_config = config or GUIConfig(
                window_title="Klondike Solitaire",
                window_width=1100,
                window_height=760,
                enable_sounds=enable_sounds,
                enable_animations=True,
            )
            BaseGUI.__init__(self, self, gui_config)
            self.sound_manager = initialize_game_soundscape(
                "solitaire",
                module_file=__file__,
                enable_sounds=gui_config.enable_sounds,
                existing_manager=self.sound_manager,
            )

            self.game = game
            self._new_game_factory = new_game_factory

            self.selected_source: Optional[SelectedSource] = None
            self.legal_targets: set[TargetKey] = set()

            colors = self.current_theme.colors
            self._background = colors.background or "#0d3b24"
            self._canvas_bg = colors.canvas_bg or "#0f4c2c"
            self._default_border = colors.border or "#CCCCCC"
            self._target_border = colors.highlight or colors.primary or "#FFD700"
            self._selection_border = colors.primary or "#1e88e5"
            self._card_face_color = "#FFFFFF"
            self._card_back_color = "#1e3a5f"
            self._card_back_accent = "#f7b733"

            self.status_timer = QTimer(self)
            self.status_timer.setSingleShot(True)
            self.status_timer.timeout.connect(self._restore_default_status)

            self._default_status = "Welcome to Klondike Solitaire!"

            self.score_value: Optional[QLabel] = None
            self.moves_value: Optional[QLabel] = None
            self.recycle_value: Optional[QLabel] = None
            self.draw_mode_value: Optional[QLabel] = None
            self.status_label: Optional[QLabel] = None

            self.stock_container: Optional[PileContainer] = None
            self.waste_container: Optional[PileContainer] = None
            self.foundation_containers: list[PileContainer] = []
            self.tableau_containers: list[PileContainer] = []

            self.stock_canvas: Optional[PileCanvas] = None
            self.waste_canvas: Optional[PileCanvas] = None
            self.foundation_canvases: list[PileCanvas] = []
            self.tableau_canvases: list[PileCanvas] = []

            self.build_layout()
            self.update_display()

        # ------------------------------------------------------------------
        # BaseGUI overrides
        # ------------------------------------------------------------------
        def build_layout(self) -> None:
            """Create the full PyQt5 widget hierarchy for the solitaire board."""

            central = QWidget(self.root)
            central.setStyleSheet(f"background-color: {self._background};")
            self.setCentralWidget(central)

            main_layout = QVBoxLayout(central)
            main_layout.setContentsMargins(16, 16, 16, 12)
            main_layout.setSpacing(12)

            header_widget = QWidget(central)
            header_layout = QHBoxLayout(header_widget)
            header_layout.setContentsMargins(0, 0, 0, 0)
            header_layout.setSpacing(12)

            title_label = QLabel("Klondike Solitaire", header_widget)
            title_font = QFont(self.config.font_family, self.config.font_size + 10, QFont.Weight.Bold)
            title_label.setFont(title_font)
            title_label.setStyleSheet("color: white;")
            header_layout.addWidget(title_label)

            header_layout.addStretch(1)

            toolbar = QWidget(header_widget)
            toolbar_layout = QHBoxLayout(toolbar)
            toolbar_layout.setContentsMargins(0, 0, 0, 0)
            toolbar_layout.setSpacing(8)

            button_specs = [
                ("Draw", self.handle_draw),
                ("Auto", self.handle_auto),
                ("Reset", self.handle_reset),
                ("New Game", self.handle_new_game),
            ]

            for label, handler in button_specs:
                btn = QPushButton(label, toolbar)
                btn.setCursor(Qt.CursorShape.PointingHandCursor)
                btn.clicked.connect(handler)
                toolbar_layout.addWidget(btn)

            header_layout.addWidget(toolbar)
            main_layout.addWidget(header_widget)

            scoreboard = QWidget(central)
            scoreboard_layout = QGridLayout(scoreboard)
            scoreboard_layout.setContentsMargins(0, 0, 0, 0)
            scoreboard_layout.setHorizontalSpacing(24)
            scoreboard_layout.setVerticalSpacing(4)

            labels = [
                ("Score", "0"),
                ("Moves", "0"),
                ("Recycles", "0"),
                ("Draw Mode", "Draw 3"),
            ]

            value_refs: list[QLabel] = []
            for column, (label_text, default_text) in enumerate(labels):
                caption = QLabel(label_text, scoreboard)
                caption.setStyleSheet("color: white; font-weight: bold;")
                scoreboard_layout.addWidget(caption, 0, column)

                value_label = QLabel(default_text, scoreboard)
                value_font = QFont(self.config.font_family, self.config.font_size + 2)
                value_label.setFont(value_font)
                value_label.setStyleSheet("color: white;")
                scoreboard_layout.addWidget(value_label, 1, column)
                value_refs.append(value_label)

            self.score_value, self.moves_value, self.recycle_value, self.draw_mode_value = value_refs
            main_layout.addWidget(scoreboard)

            board_area = QWidget(central)
            board_layout = QVBoxLayout(board_area)
            board_layout.setContentsMargins(0, 0, 0, 0)
            board_layout.setSpacing(20)

            top_row = QWidget(board_area)
            top_layout = QHBoxLayout(top_row)
            top_layout.setContentsMargins(0, 0, 0, 0)
            top_layout.setSpacing(24)

            piles_left = QWidget(top_row)
            piles_left_layout = QHBoxLayout(piles_left)
            piles_left_layout.setContentsMargins(0, 0, 0, 0)
            piles_left_layout.setSpacing(16)

            self.stock_container = PileContainer(
                background=self._canvas_bg,
                default_border=self._default_border,
                selection_border=self._selection_border,
                target_border=self._target_border,
            )
            self.stock_canvas = PileCanvas(self, "stock", 0, width=CARD_WIDTH + 20, height=CARD_HEIGHT + 20)
            self.stock_canvas.clicked.connect(self._on_pile_clicked)
            self.stock_container.layout().addWidget(self.stock_canvas)
            piles_left_layout.addWidget(self.stock_container)

            self.waste_container = PileContainer(
                background=self._canvas_bg,
                default_border=self._default_border,
                selection_border=self._selection_border,
                target_border=self._target_border,
            )
            self.waste_canvas = PileCanvas(self, "waste", 0, width=CARD_WIDTH + 20, height=CARD_HEIGHT + 20)
            self.waste_canvas.clicked.connect(self._on_pile_clicked)
            self.waste_container.layout().addWidget(self.waste_canvas)
            piles_left_layout.addWidget(self.waste_container)

            top_layout.addWidget(piles_left)
            top_layout.addStretch(1)

            foundations_widget = QWidget(top_row)
            foundations_layout = QHBoxLayout(foundations_widget)
            foundations_layout.setContentsMargins(0, 0, 0, 0)
            foundations_layout.setSpacing(16)

            for index in range(4):
                container = PileContainer(
                    background=self._canvas_bg,
                    default_border=self._default_border,
                    selection_border=self._selection_border,
                    target_border=self._target_border,
                )
                canvas = PileCanvas(self, "foundation", index, width=CARD_WIDTH + 20, height=CARD_HEIGHT + 36)
                canvas.clicked.connect(self._on_pile_clicked)
                container.layout().addWidget(canvas)
                self.foundation_containers.append(container)
                self.foundation_canvases.append(canvas)
                foundations_layout.addWidget(container)

            top_layout.addWidget(foundations_widget)
            board_layout.addWidget(top_row)

            tableau_widget = QWidget(board_area)
            tableau_layout = QHBoxLayout(tableau_widget)
            tableau_layout.setContentsMargins(0, 0, 0, 0)
            tableau_layout.setSpacing(16)

            for index in range(7):
                container = PileContainer(
                    background=self._canvas_bg,
                    default_border=self._default_border,
                    selection_border=self._selection_border,
                    target_border=self._target_border,
                )
                canvas = PileCanvas(
                    self,
                    "tableau",
                    index,
                    width=CARD_WIDTH + 20,
                    height=540,
                    scalable_height=True,
                )
                canvas.clicked.connect(self._on_pile_clicked)
                container.layout().addWidget(canvas)
                container.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
                self.tableau_containers.append(container)
                self.tableau_canvases.append(canvas)
                tableau_layout.addWidget(container)

            board_layout.addWidget(tableau_widget)
            main_layout.addWidget(board_area, 1)

            status_widget = QWidget(central)
            status_layout = QHBoxLayout(status_widget)
            status_layout.setContentsMargins(0, 0, 0, 0)
            self.status_label = QLabel(self._default_status, status_widget)
            self.status_label.setWordWrap(True)
            self.status_label.setStyleSheet("color: white;")
            status_layout.addWidget(self.status_label)
            main_layout.addWidget(status_widget)

            self.register_shortcut("Space", self.handle_draw, "Draw from stock")
            self.register_shortcut("A", self.handle_auto, "Auto move to foundations")
            self.register_shortcut("R", self.handle_reset, "Recycle waste onto stock")

        def update_display(self) -> None:
            """Refresh scoreboard, pile canvases, and highlight states."""

            summary = self.game.get_state_summary()

            if self.score_value:
                self.score_value.setText(str(summary["score"]))
            if self.moves_value:
                self.moves_value.setText(f"{summary['moves_made']} (auto: {summary['auto_moves']})")
            if self.recycle_value:
                if summary["recycles_remaining"] is None:
                    recycle_text = f"{summary['recycles_used']} used"
                else:
                    recycle_text = f"{summary['recycles_used']} / {summary['recycles_remaining']}"
                self.recycle_value.setText(recycle_text)
            if self.draw_mode_value:
                self.draw_mode_value.setText(f"Draw {summary['draw_count']}")

            if self.stock_canvas:
                self.stock_canvas.update()
            if self.waste_canvas:
                self.waste_canvas.update()
            for canvas in self.foundation_canvases:
                canvas.update()
            for canvas in self.tableau_canvases:
                canvas.update()

            self._apply_highlights()

            if self.game.is_won():
                self._set_status(
                    "🎉 You won! Move cards to foundations to play again or start a new game.",
                    persist=True,
                )

        # ------------------------------------------------------------------
        # Painting helpers
        # ------------------------------------------------------------------
        def paint_pile(self, canvas: PileCanvas, painter: QPainter) -> list[Tuple[float, float, int]]:
            """Delegate pile rendering based on the canvas type."""

            painter.fillRect(canvas.rect(), QColor(self._canvas_bg))

            state = self._pile_state(canvas.pile_type, canvas.index)
            if state != "default":
                overlay = QColor(self._selection_border if state == "selected" else self._target_border)
                overlay.setAlpha(45)
                painter.fillRect(canvas.rect(), overlay)

            if canvas.pile_type == "stock":
                self._paint_stock(painter)
                return []
            if canvas.pile_type == "waste":
                self._paint_waste(painter)
                return []
            if canvas.pile_type == "foundation":
                self._paint_foundation(painter, canvas.index)
                return []
            if canvas.pile_type == "tableau":
                return self._paint_tableau(painter, canvas.index)
            return []

        def _paint_stock(self, painter: QPainter) -> None:
            pile_rect = QRectF(10, 10, CARD_WIDTH, CARD_HEIGHT)
            if self.game.stock.cards:
                painter.setBrush(QColor(self._card_back_color))
                painter.setPen(QPen(QColor(self._card_back_accent), 3))
                painter.drawRoundedRect(pile_rect, 8, 8)

                painter.setPen(QPen(QColor("white")))
                font = QFont(self.config.font_family, self.config.font_size + 8, QFont.Weight.Bold)
                painter.setFont(font)
                painter.drawText(
                    pile_rect,
                    Qt.AlignmentFlag.AlignCenter,
                    str(len(self.game.stock.cards)),
                )
            else:
                pen = QPen(QColor(self._card_back_accent), 2, Qt.PenStyle.DashLine)
                painter.setPen(pen)
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawRoundedRect(pile_rect, 8, 8)
                font = QFont(self.config.font_family, self.config.font_size)
                painter.setFont(font)
                painter.setPen(QPen(QColor("white")))
                painter.drawText(pile_rect, Qt.AlignmentFlag.AlignCenter, "Empty")

        def _paint_waste(self, painter: QPainter) -> None:
            pile_rect = QRectF(10, 10, CARD_WIDTH, CARD_HEIGHT)
            if not self.game.waste.cards:
                pen = QPen(QColor(self._card_back_accent), 2, Qt.PenStyle.DashLine)
                painter.setPen(pen)
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawRoundedRect(pile_rect, 8, 8)
                font = QFont(self.config.font_family, self.config.font_size)
                painter.setFont(font)
                painter.setPen(QPen(QColor("white")))
                painter.drawText(pile_rect, Qt.AlignmentFlag.AlignCenter, "Waste")
                return

            card = self.game.waste.cards[-1]
            self._draw_face_up_card(painter, card, top=10, height=CARD_HEIGHT)

        def _paint_foundation(self, painter: QPainter, index: int) -> None:
            pile = self.game.foundations[index]
            pile_rect = QRectF(10, 10, CARD_WIDTH, CARD_HEIGHT)
            top_card = pile.top_card()
            if top_card:
                self._draw_face_up_card(painter, top_card, top=10, height=CARD_HEIGHT)
                font = QFont(self.config.font_family, self.config.font_size - 1)
                painter.setFont(font)
                painter.setPen(QPen(QColor("white")))
                painter.drawText(
                    QRectF(10, 10 + CARD_HEIGHT + 6, CARD_WIDTH, 18),
                    Qt.AlignmentFlag.AlignCenter,
                    f"{len(pile.cards)} cards",
                )
                return

            pen = QPen(QColor(self._card_back_accent), 2, Qt.PenStyle.DashLine)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(pile_rect, 8, 8)
            font = QFont(self.config.font_family, self.config.font_size - 1)
            painter.setFont(font)
            painter.setPen(QPen(QColor("white")))
            painter.drawText(pile_rect, Qt.AlignmentFlag.AlignCenter, "Foundation")

        def _paint_tableau(self, painter: QPainter, index: int) -> list[Tuple[float, float, int]]:
            pile = self.game.tableau[index]
            positions: list[Tuple[float, float, int]] = []
            y = 12.0
            face_up_start = len(pile.cards) - pile.face_up_count
            if face_up_start < 0:
                face_up_start = 0

            for card_index, card in enumerate(pile.cards):
                is_face_up = card_index >= face_up_start
                height = CARD_HEIGHT if is_face_up else FACE_DOWN_HEIGHT
                if is_face_up:
                    self._draw_face_up_card(painter, card, top=y, height=height)
                else:
                    rect = QRectF(10, y, CARD_WIDTH, height)
                    painter.setBrush(QColor(self._card_back_color))
                    painter.setPen(QPen(QColor(self._card_back_accent), 2))
                    painter.drawRoundedRect(rect, 6, 6)
                positions.append((y, y + height, card_index))
                y += FACE_UP_SPACING if is_face_up else FACE_DOWN_SPACING

            if not pile.cards:
                pen = QPen(QColor(self._card_back_accent), 2, Qt.PenStyle.DashLine)
                painter.setPen(pen)
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawRoundedRect(QRectF(10, y, CARD_WIDTH, CARD_HEIGHT), 8, 8)
                positions.clear()

            return positions

        def _draw_face_up_card(self, painter: QPainter, card: Card, *, top: float, height: float) -> None:
            rect = QRectF(10, top, CARD_WIDTH, height)
            painter.setBrush(QColor(self._card_face_color))
            painter.setPen(QPen(QColor(self._card_back_accent), 2))
            painter.drawRoundedRect(rect, 6, 6)

            font = QFont(self.config.font_family, self.config.font_size + 6, QFont.Weight.Bold)
            painter.setFont(font)
            color = QColor("#D32F2F") if card.suit.name in {"HEARTS", "DIAMONDS"} else QColor("#1B1B1B")
            painter.setPen(color)
            text_rect = rect.adjusted(12, 12, -12, -12)
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop, str(card))

        # ------------------------------------------------------------------
        # Event handling & move logic
        # ------------------------------------------------------------------
        def handle_draw(self) -> None:
            """Draw cards from the stock, updating the status label."""

            if self.game.draw_from_stock():
                self._set_status("Drew from the stock pile.")
            else:
                if self.game.can_reset_stock():
                    self._set_status("Stock is empty—use Reset to recycle the waste.")
                else:
                    self._set_status("No cards left to draw.")
            self.clear_selection()
            self.update_display()

        def handle_reset(self) -> None:
            """Recycle the waste pile back into the stock."""

            if self.game.reset_stock():
                self._set_status("Recycled the waste pile onto the stock.")
            else:
                self._set_status("Cannot reset the stock right now.")
            self.clear_selection()
            self.update_display()

        def handle_auto(self) -> None:
            """Trigger automatic moves to the foundations."""

            if self.game.auto_move_to_foundation():
                self._set_status("Moved all available cards to the foundations.")
            else:
                self._set_status("No automatic foundation moves available.")
            self.clear_selection()
            self.update_display()

        def handle_new_game(self) -> None:
            """Deal a fresh game via the new-game factory."""

            if not self._new_game_factory:
                if QMessageBox:
                    QMessageBox.warning(self, "New Game", "New game factory not provided.")
                self._set_status("New game factory not provided.")
                return
            self.game = self._new_game_factory()
            self.clear_selection()
            self._set_status("Dealt a new game. Good luck!")
            self.update_display()

        def _on_pile_clicked(self, pile_type: str, index: int, y: float) -> None:
            if pile_type == "stock":
                self.handle_draw()
                return
            if pile_type == "waste":
                self._on_waste_click()
                return
            if pile_type == "foundation":
                self._on_foundation_click(index)
                return
            if pile_type == "tableau":
                self._on_tableau_click(index, y)

        def _on_waste_click(self) -> None:
            if self.selected_source and self.selected_source[0] == "waste":
                self.clear_selection()
                self.update_display()
                return
            if not self.game.waste.cards:
                self._set_status("Waste pile is empty.")
                self.clear_selection()
                self.update_display()
                return
            self._set_selection(("waste", 0, 1))

        def _on_foundation_click(self, index: int) -> None:
            target_key = ("foundation", index)
            if self.selected_source and target_key in self.legal_targets:
                if self._execute_move(target_key):
                    return

            pile = self.game.foundations[index]
            if not pile.cards:
                self._set_status("Foundation is empty.")
                return
            if self.game.scoring_mode == "vegas":
                self._set_status("Vegas scoring does not allow moving cards off foundations.")
                return
            self._set_selection(("foundation", index, 1))

        def _on_tableau_click(self, index: int, y: float) -> None:
            target_key = ("tableau", index)
            if self.selected_source and target_key in self.legal_targets:
                if self._execute_move(target_key):
                    return

            pile = self.game.tableau[index]
            if not pile.cards:
                message = "Empty column selected." if not self.selected_source else ""
                if message:
                    self._set_status(message)
                if self.selected_source and target_key in self.legal_targets:
                    self._execute_move(target_key)
                return

            canvas = self.tableau_canvases[index]
            clicked_index = canvas.card_index_at(y)
            if clicked_index is None:
                clicked_index = len(pile.cards) - 1

            face_up_start = len(pile.cards) - pile.face_up_count
            if clicked_index < face_up_start:
                self._set_status("You can only move face-up cards.")
                self.clear_selection()
                self.update_display()
                return

            num_cards = len(pile.cards) - clicked_index
            self._set_selection(("tableau", index, num_cards))

        def _execute_move(self, target: TargetKey) -> bool:
            if not self.selected_source:
                return False

            source_type, source_index, num_cards = self.selected_source
            source_pile = self._get_pile(source_type, source_index)
            if source_pile is None:
                return False

            target_type, target_index = target
            moved = False
            if target_type == "foundation":
                moved = self.game.move_to_foundation(source_pile, target_index)
                if moved:
                    self._set_status("Moved card to the foundation.")
            elif target_type == "tableau":
                moved = self.game.move_to_tableau(source_pile, target_index, num_cards)
                if moved:
                    self._set_status(f"Moved {num_cards} card(s) to tableau column {target_index}.")

            if moved:
                self.clear_selection()
                self.update_display()
            else:
                self._set_status("That move isn't allowed.")
                self.update_display()
            return moved

        def _get_pile(self, source_type: str, index: int) -> Optional[Pile]:
            if source_type == "waste":
                return self.game.waste
            if source_type == "foundation":
                return self.game.foundations[index]
            if source_type == "tableau":
                return self.game.tableau[index]
            return None

        def _set_selection(self, selection: SelectedSource) -> None:
            if self.selected_source == selection:
                self.clear_selection()
                self.update_display()
                return
            self.selected_source = selection
            self.legal_targets = self._compute_legal_targets(selection)
            self.update_display()

        def clear_selection(self) -> None:
            """Clear the current selection and target highlights."""

            self.selected_source = None
            self.legal_targets.clear()

        def _compute_legal_targets(self, selection: SelectedSource) -> set[TargetKey]:
            source_type, index, num_cards = selection
            source_pile = self._get_pile(source_type, index)
            if not source_pile:
                return set()

            targets: set[TargetKey] = set()
            top_card = source_pile.top_card()

            if source_type == "tableau":
                cards_to_move = source_pile.cards[-num_cards:]
                if not cards_to_move:
                    return set()
                top_card = cards_to_move[-1]
                bottom_card = cards_to_move[0]
                for t_index, tableau_pile in enumerate(self.game.tableau):
                    if t_index == index:
                        continue
                    if tableau_pile.can_add_to_tableau(bottom_card):
                        targets.add(("tableau", t_index))
                if num_cards == 1 and top_card:
                    for f_index, foundation in enumerate(self.game.foundations):
                        if foundation.can_add_to_foundation(top_card):
                            targets.add(("foundation", f_index))

            elif source_type == "waste":
                if top_card:
                    for f_index, foundation in enumerate(self.game.foundations):
                        if foundation.can_add_to_foundation(top_card):
                            targets.add(("foundation", f_index))
                    for t_index, tableau_pile in enumerate(self.game.tableau):
                        if tableau_pile.can_add_to_tableau(top_card):
                            targets.add(("tableau", t_index))

            elif source_type == "foundation":
                if top_card:
                    for t_index, tableau_pile in enumerate(self.game.tableau):
                        if tableau_pile.can_add_to_tableau(top_card):
                            targets.add(("tableau", t_index))

            return targets

        def _apply_highlights(self) -> None:
            mapping: dict[Tuple[str, int], PileContainer] = {}
            if self.stock_container:
                mapping[("stock", 0)] = self.stock_container
            if self.waste_container:
                mapping[("waste", 0)] = self.waste_container
            for idx, container in enumerate(self.foundation_containers):
                mapping[("foundation", idx)] = container
            for idx, container in enumerate(self.tableau_containers):
                mapping[("tableau", idx)] = container

            for key, container in mapping.items():
                container.set_highlight("default")

            if self.selected_source:
                source_key = (self.selected_source[0], self.selected_source[1])
                if source_key in mapping:
                    mapping[source_key].set_highlight("selected")

            for target in self.legal_targets:
                if target in mapping:
                    mapping[target].set_highlight("target")

        def _pile_state(self, pile_type: str, index: int) -> str:
            if self.selected_source and (self.selected_source[0], self.selected_source[1]) == (pile_type, index):
                return "selected"
            if (pile_type, index) in self.legal_targets:
                return "target"
            return "default"

        def _set_status(self, message: str, *, persist: bool = False) -> None:
            if not self.status_label or not message:
                return
            self.status_label.setText(message)
            if persist:
                self.status_timer.stop()
            else:
                self.status_timer.start(4000)

        def _restore_default_status(self) -> None:
            if self.status_label:
                self.status_label.setText(self._default_status)

else:

    class SolitaireWindow:  # type: ignore[misc]
        """Placeholder when PyQt5 is unavailable."""

        def __init__(self, *_, **__) -> None:
            raise RuntimeError("PyQt5 is not available on this system.")


def run_app(
    *,
    draw_count: int = 3,
    max_recycles: Optional[int] = None,
    scoring_mode: str = "standard",
    seed: Optional[int] = None,
) -> None:
    """Launch the Solitaire PyQt5 application."""

    if not PYQT5_AVAILABLE:
        raise RuntimeError("PyQt5 is not available; install it to use the GUI.")

    def make_game() -> SolitaireGame:
        rng = random.Random(seed) if seed is not None else None
        return SolitaireGame(
            draw_count=draw_count,
            max_recycles=max_recycles,
            scoring_mode=scoring_mode,
            rng=rng,
        )

    app = QApplication.instance() or QApplication([])
    window = SolitaireWindow(make_game(), new_game_factory=make_game)
    window.show()
    app.exec_()
