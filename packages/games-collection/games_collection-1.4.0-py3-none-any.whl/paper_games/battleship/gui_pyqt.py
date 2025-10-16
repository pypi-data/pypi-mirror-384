"""PyQt5-powered graphical interface for Battleship.

This module provides an interactive Battleship GUI with ship placement,
AI opponent turns, salvo mode support, and visual feedback for hits and misses.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import Optional, Set

from PyQt5.QtCore import QPointF, Qt, QTimer
from PyQt5.QtGui import QBrush, QColor, QFont, QPainter, QPen
from PyQt5.QtWidgets import QApplication, QGraphicsScene, QGraphicsView, QHBoxLayout, QLabel, QMessageBox, QPushButton, QVBoxLayout, QWidget

from .battleship import DEFAULT_FLEET, EXTENDED_FLEET, SMALL_FLEET, BattleshipGame, Board, Coordinate


@dataclass
class BoardTheme:
    """Color palette for a Battleship board."""

    background: QColor
    grid: QColor
    hover: QColor
    ship: QColor
    preview: QColor
    miss: QColor
    hit: QColor
    sunk: QColor


class BoardCanvas(QGraphicsView):
    """Custom view for rendering the Battleship board using QGraphicsScene."""

    CELL_SIZE = 36
    MARGIN = 24

    PLAYER_THEME = BoardTheme(
        background=QColor("#e3f2fd"),
        grid=QColor("#0d47a1"),
        hover=QColor("#1e88e5"),
        ship=QColor("#546e7a"),
        preview=QColor(46, 204, 113, 160),
        miss=QColor("#bbdefb"),
        hit=QColor("#ef5350"),
        sunk=QColor("#c62828"),
    )
    OPPONENT_THEME = BoardTheme(
        background=QColor("#bbdefb"),
        grid=QColor("#0d47a1"),
        hover=QColor("#3949ab"),
        ship=QColor("#1a237e"),
        preview=QColor(255, 255, 255, 0),
        miss=QColor("#e3f2fd"),
        hit=QColor("#e53935"),
        sunk=QColor("#b71c1c"),
    )

    def __init__(self, gui: "BattleshipGUI", size: int, is_player: bool) -> None:
        super().__init__()
        self.gui = gui
        self.size = size
        self.is_player = is_player
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.setRenderHints(self.renderHints() | QPainter.RenderHint.Antialiasing)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setMouseTracking(True)
        self.hover_coord: Optional[Coordinate] = None
        self.theme = self.PLAYER_THEME if is_player else self.OPPONENT_THEME
        self.label_font = QFont("Arial", 10)

        view_size = self.MARGIN * 2 + self.CELL_SIZE * self.size
        self.setFixedSize(view_size + 2, view_size + 2)
        self.draw_board()

    # ------------------------------------------------------------------
    # Coordinate helpers
    # ------------------------------------------------------------------
    def _scene_to_coord(self, point: QPointF) -> Optional[Coordinate]:
        """Convert a scene position to a board coordinate."""

        x = point.x() - self.MARGIN
        y = point.y() - self.MARGIN
        if x < 0 or y < 0:
            return None
        col = int(x // self.CELL_SIZE)
        row = int(y // self.CELL_SIZE)
        if 0 <= row < self.size and 0 <= col < self.size:
            return row, col
        return None

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------
    def mouseMoveEvent(self, event) -> None:  # type: ignore[override]
        point = self.mapToScene(event.pos())
        coord = self._scene_to_coord(point)
        if coord != self.hover_coord:
            self.hover_coord = coord
            self.gui.handle_board_hover(self, coord)
        super().mouseMoveEvent(event)

    def leaveEvent(self, event) -> None:  # type: ignore[override]
        if self.hover_coord is not None:
            self.hover_coord = None
            self.gui.handle_board_leave(self)
        super().leaveEvent(event)

    def mousePressEvent(self, event) -> None:  # type: ignore[override]
        if event.button() == Qt.MouseButton.LeftButton:
            point = self.mapToScene(event.pos())
            coord = self._scene_to_coord(point)
            self.gui.handle_board_click(self, coord)
        super().mousePressEvent(event)

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------
    def draw_board(self) -> None:
        """Render the current state of the board."""

        self.scene.clear()
        view_size = self.MARGIN * 2 + self.CELL_SIZE * self.size
        self.scene.setSceneRect(0, 0, view_size, view_size)
        board = self.gui._board_for_canvas(self)
        show_ships = self.gui._should_show_ships(self)

        # Draw background
        self.scene.addRect(
            0,
            0,
            view_size,
            view_size,
            QPen(Qt.PenStyle.NoPen),
            QBrush(self.theme.background),
        )

        # Grid cells
        for row in range(self.size):
            for col in range(self.size):
                x = self.MARGIN + col * self.CELL_SIZE
                y = self.MARGIN + row * self.CELL_SIZE
                rect = (x, y, self.CELL_SIZE, self.CELL_SIZE)

                fill_color = self.theme.background
                shot = None
                if board is not None:
                    coord = (row, col)
                    shot = board.shots.get(coord)
                    is_preview = self.gui._is_preview_cell(self, coord)
                    if show_ships and coord in board.occupied:
                        fill_color = self.theme.ship
                    if is_preview:
                        fill_color = self.theme.preview
                    if shot == "miss":
                        fill_color = self.theme.miss
                    elif shot in {"hit", "sunk"}:
                        fill_color = self.theme.hit if shot == "hit" else self.theme.sunk

                hover_pen = QPen(self.theme.grid, 1)
                if self.hover_coord == (row, col):
                    hover_pen = QPen(self.theme.hover, 2)
                self.scene.addRect(*rect, hover_pen, QBrush(fill_color))

                if board is not None:
                    coord = (row, col)
                    shot = board.shots.get(coord)
                    if shot == "miss":
                        center_x = x + self.CELL_SIZE / 2
                        center_y = y + self.CELL_SIZE / 2
                        radius = self.CELL_SIZE * 0.18
                        self.scene.addEllipse(
                            center_x - radius,
                            center_y - radius,
                            radius * 2,
                            radius * 2,
                            QPen(self.theme.grid, 1),
                            QBrush(QColor("white")),
                        )
                    elif shot in {"hit", "sunk"}:
                        pen = QPen(QColor("#fafafa"), 2)
                        self.scene.addLine(x + 6, y + 6, x + self.CELL_SIZE - 6, y + self.CELL_SIZE - 6, pen)
                        self.scene.addLine(x + self.CELL_SIZE - 6, y + 6, x + 6, y + self.CELL_SIZE - 6, pen)

        # Border
        board_rect = (
            self.MARGIN,
            self.MARGIN,
            self.CELL_SIZE * self.size,
            self.CELL_SIZE * self.size,
        )
        self.scene.addRect(*board_rect, QPen(self.theme.grid, 2))

        # Labels
        if self.size <= 12:
            for col in range(self.size):
                x = self.MARGIN + col * self.CELL_SIZE + self.CELL_SIZE / 2 - 6
                text = self.scene.addText(str(col), self.label_font)
                text.setDefaultTextColor(self.theme.grid)
                text.setPos(x, self.MARGIN - 22)
            for row in range(self.size):
                y = self.MARGIN + row * self.CELL_SIZE + self.CELL_SIZE / 2 - 10
                text = self.scene.addText(str(row), self.label_font)
                text.setDefaultTextColor(self.theme.grid)
                text.setPos(self.MARGIN - 24, y)


class BattleshipGUI(QWidget):
    """Main Battleship GUI window."""

    def __init__(
        self,
        *,
        size: int = 10,
        fleet_type: str = "default",
        difficulty: str = "medium",
        two_player: bool = False,
        salvo_mode: bool = False,
        seed: Optional[int] = None,
    ) -> None:
        super().__init__()
        self.size = size
        self.fleet_type = fleet_type
        self.difficulty = difficulty
        self.two_player = two_player
        self.salvo_mode = salvo_mode
        self.seed = seed

        self.fleet_map = {
            "small": SMALL_FLEET,
            "default": DEFAULT_FLEET,
            "extended": EXTENDED_FLEET,
        }
        if fleet_type not in self.fleet_map:
            raise ValueError("Fleet type must be 'small', 'default', or 'extended'.")
        self.fleet = self.fleet_map[fleet_type]

        self.game: Optional[BattleshipGame] = None
        self.setup_phase = True
        self.setup_player = 1
        self.current_player = 1
        self.placing_ship_index = 0
        self.ship_orientation = "h"
        self.preview_coords: Set[Coordinate] = set()
        self.shots_remaining = 0
        self.ai_shots_pending = 0

        self.ai_timer = QTimer(self)
        self.ai_timer.setSingleShot(True)
        self.ai_timer.timeout.connect(self._process_ai_shot)

        self._build_layout()
        self._new_game()

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------
    def _build_layout(self) -> None:
        """Build the window layout."""

        self.setWindowTitle(self._window_title())
        main_layout = QVBoxLayout(self)
        boards_layout = QHBoxLayout()

        player_layout = QVBoxLayout()
        player_label = QLabel("Your Fleet")
        player_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        player_layout.addWidget(player_label)
        self.player_canvas = BoardCanvas(self, self.size, is_player=True)
        player_layout.addWidget(self.player_canvas)
        boards_layout.addLayout(player_layout)

        opponent_layout = QVBoxLayout()
        opponent_label = QLabel("Enemy Waters")
        opponent_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        opponent_layout.addWidget(opponent_label)
        self.opponent_canvas = BoardCanvas(self, self.size, is_player=False)
        opponent_layout.addWidget(self.opponent_canvas)
        boards_layout.addLayout(opponent_layout)

        main_layout.addLayout(boards_layout)

        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)
        main_layout.addWidget(self.status_label)

        self.salvo_label = QLabel("")
        main_layout.addWidget(self.salvo_label)

        # Ship placement controls
        self.setup_controls = QWidget()
        setup_layout = QHBoxLayout(self.setup_controls)
        setup_layout.setContentsMargins(0, 0, 0, 0)
        setup_layout.addWidget(QLabel("Ship Placement:"))

        self.orientation_button = QPushButton("Orientation: Horizontal")
        self.orientation_button.clicked.connect(self._toggle_orientation)
        setup_layout.addWidget(self.orientation_button)

        self.random_button = QPushButton("Place Randomly")
        self.random_button.clicked.connect(self._place_ships_randomly)
        setup_layout.addWidget(self.random_button)

        main_layout.addWidget(self.setup_controls)

        # General controls
        controls = QWidget()
        controls_layout = QHBoxLayout(controls)
        controls_layout.setContentsMargins(0, 0, 0, 0)

        self.new_game_button = QPushButton("New Game")
        self.new_game_button.clicked.connect(self._new_game)
        controls_layout.addWidget(self.new_game_button)

        quit_button = QPushButton("Quit")
        quit_button.clicked.connect(self.close)
        controls_layout.addWidget(quit_button)

        main_layout.addWidget(controls)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _is_setup_canvas(self, canvas: BoardCanvas) -> bool:
        """Return whether the given canvas is currently used for ship placement."""

        if not self.setup_phase:
            return False
        if not self.two_player:
            return canvas.is_player
        if self.setup_player == 1:
            return canvas.is_player
        return not canvas.is_player

    def _current_setup_board(self) -> Optional[Board]:
        """Return the board that is currently being configured during setup."""

        if self.game is None:
            return None
        return self.game.player_board if self.setup_player == 1 else self.game.opponent_board

    def _board_for_canvas(self, canvas: BoardCanvas) -> Optional[Board]:
        """Return the Battleship board associated with the provided canvas."""

        if self.game is None:
            return None
        return self.game.player_board if canvas.is_player else self.game.opponent_board

    def _should_show_ships(self, canvas: BoardCanvas) -> bool:
        """Determine whether ship locations should be shown on the canvas."""

        if self.game is None:
            return False
        if not self.two_player:
            return canvas.is_player
        if self.setup_phase:
            return (self.setup_player == 1 and canvas.is_player) or (self.setup_player == 2 and not canvas.is_player)
        return canvas.is_player

    def _is_preview_cell(self, canvas: BoardCanvas, coord: Coordinate) -> bool:
        """Return whether the coordinate should display the placement preview."""

        return self.setup_phase and self._is_setup_canvas(canvas) and coord in self.preview_coords

    def _update_canvas_interactivity(self) -> None:
        """Enable or disable canvases based on the current setup phase."""

        if not self.setup_phase:
            self.player_canvas.setEnabled(True)
            self.opponent_canvas.setEnabled(True)
            return

        self.player_canvas.setEnabled(self._is_setup_canvas(self.player_canvas))
        self.opponent_canvas.setEnabled(self._is_setup_canvas(self.opponent_canvas))

    # ------------------------------------------------------------------
    # Event handlers from BoardCanvas
    # ------------------------------------------------------------------
    def handle_board_hover(self, canvas: BoardCanvas, coord: Optional[Coordinate]) -> None:
        """Handle hover events from the board."""

        if not self.setup_phase or self.game is None:
            canvas.draw_board()
            return
        if not self._is_setup_canvas(canvas):
            canvas.draw_board()
            return

        if coord is None or self.placing_ship_index >= len(self.fleet):
            if self.preview_coords:
                self.preview_coords.clear()
                self.player_canvas.draw_board()
                self.opponent_canvas.draw_board()
            else:
                canvas.draw_board()
            return

        board = self._current_setup_board()
        if board is None:
            return

        ship_length = self.fleet[self.placing_ship_index][1]
        row, col = coord
        preview: Set[Coordinate] = set()
        if self.ship_orientation == "h":
            preview = {(row, col + i) for i in range(ship_length)}
        else:
            preview = {(row + i, col) for i in range(ship_length)}

        if all(board.in_bounds(c) and c not in board.occupied for c in preview):
            self.preview_coords = preview
        else:
            self.preview_coords.clear()

        self.player_canvas.draw_board()
        self.opponent_canvas.draw_board()

    def handle_board_leave(self, canvas: BoardCanvas) -> None:
        """Handle cursor leaving a board."""

        if self.setup_phase and self._is_setup_canvas(canvas) and self.preview_coords:
            self.preview_coords.clear()
            self.player_canvas.draw_board()
            self.opponent_canvas.draw_board()
            return
        canvas.draw_board()

    def handle_board_click(self, canvas: BoardCanvas, coord: Optional[Coordinate]) -> None:
        """Handle click events from the boards."""

        if self.game is None or coord is None:
            return

        if self.setup_phase and self._is_setup_canvas(canvas):
            if self.placing_ship_index >= len(self.fleet):
                return
            board = self._current_setup_board()
            if board is None:
                return
            ship_name, ship_length = self.fleet[self.placing_ship_index]
            try:
                board.place_ship(ship_name, ship_length, coord, self.ship_orientation)
            except ValueError as exc:
                QMessageBox.warning(self, "Invalid Placement", str(exc))
                return
            self.placing_ship_index += 1
            self.preview_coords.clear()
            self.player_canvas.draw_board()
            self.opponent_canvas.draw_board()
            if self.placing_ship_index >= len(self.fleet):
                self._finish_player_setup()
            self._update_status()
            return

        # Opponent board click
        if self.setup_phase or self.current_player != 1:
            return
        if coord in self.game.opponent_board.shots:
            QMessageBox.information(self, "Already Targeted", "You already fired at this location.")
            return
        try:
            result, ship_name = self.game.player_shoot(coord)
        except ValueError as exc:
            QMessageBox.warning(self, "Invalid Shot", str(exc))
            return

        self.opponent_canvas.draw_board()
        message = {
            "miss": "Miss!",
            "hit": "Hit!",
            "sunk": f"Sunk enemy {ship_name}!" if ship_name else "Sunk!",
        }[result]
        self.status_label.setText(message)

        if self.salvo_mode:
            self.shots_remaining -= 1
            self.salvo_label.setText(f"Shots remaining: {self.shots_remaining}")

        if self.game.opponent_has_lost():
            QMessageBox.information(self, "Victory", "You sank all enemy ships!")
            self._new_game()
            return

        if self.salvo_mode and self.shots_remaining > 0:
            self._update_status()
            return

        self.current_player = 2
        self._update_status()
        self._begin_ai_turn()

    # ------------------------------------------------------------------
    # Game management
    # ------------------------------------------------------------------
    def _window_title(self) -> str:
        mode = "2-Player" if self.two_player else f"vs AI ({self.difficulty.title()})"
        salvo = " [Salvo]" if self.salvo_mode else ""
        return f"Battleship {self.size}x{self.size} - {mode}{salvo}"

    def _toggle_orientation(self) -> None:
        self.ship_orientation = "v" if self.ship_orientation == "h" else "h"
        text = "Orientation: Vertical" if self.ship_orientation == "v" else "Orientation: Horizontal"
        self.orientation_button.setText(text)
        self.preview_coords.clear()
        self.player_canvas.draw_board()
        self.opponent_canvas.draw_board()
        self._update_status()

    def _place_ships_randomly(self) -> None:
        if self.game is None or not self.setup_phase:
            return
        board = self._current_setup_board()
        if board is None:
            return
        board.occupied.clear()
        board.ships.clear()
        board.shots.clear()
        board.randomly_place_ships(self.fleet, self.game.rng)
        self.placing_ship_index = len(self.fleet)
        self.preview_coords.clear()
        self.player_canvas.draw_board()
        self.opponent_canvas.draw_board()
        self._finish_player_setup()
        self._update_status()

    def _finish_player_setup(self) -> None:
        if self.game is None:
            return
        if self.two_player and self.setup_player == 1:
            self.setup_player = 2
            self.placing_ship_index = 0
            self.ship_orientation = "h"
            self.orientation_button.setText("Orientation: Horizontal")
            self.preview_coords.clear()
            self._update_canvas_interactivity()
            self.player_canvas.draw_board()
            self.opponent_canvas.draw_board()
            return

        self.setup_phase = False
        self.setup_controls.setVisible(False)
        if not self.two_player:
            self.game.opponent_board.randomly_place_ships(self.fleet, self.game.rng)
        self.preview_coords.clear()
        self._update_canvas_interactivity()
        self.player_canvas.draw_board()
        self.opponent_canvas.draw_board()
        self._start_player_turn()

    def _start_player_turn(self) -> None:
        if self.game is None:
            return
        self.current_player = 1
        self.shots_remaining = self.game.get_salvo_count("player") if self.salvo_mode else 1
        self.salvo_label.setText(f"Shots remaining: {self.shots_remaining}" if self.salvo_mode else "")
        self._update_status()

    def _begin_ai_turn(self) -> None:
        if self.game is None or self.two_player:
            return
        self.ai_shots_pending = self.game.get_salvo_count("opponent") if self.salvo_mode else 1
        self.ai_timer.start(600)

    def _process_ai_shot(self) -> None:
        if self.game is None or self.two_player:
            return
        coord, result, ship_name = self.game.ai_shoot()
        self.player_canvas.draw_board()
        row, col = coord
        if result == "miss":
            message = f"AI fired at ({row}, {col}) — Miss!"
        elif result == "hit":
            message = f"AI hit a ship at ({row}, {col})!"
        else:
            message = f"AI sank your {ship_name} at ({row}, {col})!"
        self.status_label.setText(message)

        if self.game.player_has_lost():
            QMessageBox.information(self, "Defeat", "All of your ships were sunk.")
            self._new_game()
            return

        self.ai_shots_pending -= 1
        if self.salvo_mode and self.ai_shots_pending > 0:
            self.ai_timer.start(600)
            return

        self._start_player_turn()

    def _new_game(self) -> None:
        import random

        rng = random.Random(self.seed) if self.seed is not None else None
        self.game = BattleshipGame(
            size=self.size,
            fleet=self.fleet,
            rng=rng,
            difficulty=self.difficulty,
            two_player=self.two_player,
            salvo_mode=self.salvo_mode,
        )
        self.setup_phase = True
        self.setup_player = 1
        self.current_player = 1
        self.placing_ship_index = 0
        self.ship_orientation = "h"
        self.preview_coords.clear()
        self.shots_remaining = 0
        self.ai_shots_pending = 0
        self.ai_timer.stop()
        self.setWindowTitle(self._window_title())
        self.setup_controls.setVisible(True)
        self.orientation_button.setText("Orientation: Horizontal")
        self._update_canvas_interactivity()
        self.player_canvas.draw_board()
        self.opponent_canvas.draw_board()
        self._update_status()

    def _update_status(self) -> None:
        if self.setup_phase:
            if self.placing_ship_index < len(self.fleet):
                ship_name, ship_length = self.fleet[self.placing_ship_index]
                orientation = "Horizontal" if self.ship_orientation == "h" else "Vertical"
                if self.two_player:
                    prompt = f"Player {self.setup_player}: place your {ship_name}"
                else:
                    prompt = f"Place your {ship_name}"
                self.status_label.setText(f"{prompt} (length {ship_length}) — {orientation}")
            else:
                if self.two_player and self.setup_player == 1:
                    self.status_label.setText("Player 1 ready — Pass to Player 2 for placement.")
                else:
                    self.status_label.setText("Ready to start! Click to begin.")
            return

        if self.current_player == 1:
            if self.salvo_mode:
                self.status_label.setText(f"Your turn — {self.shots_remaining} shot(s) remaining")
            else:
                self.status_label.setText("Your turn — Select a target square")
        else:
            if self.two_player:
                self.status_label.setText("Player 2's turn")
            else:
                turn_msg = f"AI firing {self.ai_shots_pending} shot(s)..." if self.salvo_mode else "AI is thinking..."
                self.status_label.setText(turn_msg)

    # ------------------------------------------------------------------
    # Qt lifecycle
    # ------------------------------------------------------------------
    def closeEvent(self, event) -> None:  # type: ignore[override]
        self.ai_timer.stop()
        super().closeEvent(event)


def run_gui(
    *,
    size: int = 10,
    fleet: str = "default",
    difficulty: str = "medium",
    two_player: bool = False,
    salvo: bool = False,
    seed: Optional[int] = None,
) -> None:
    """Launch the Battleship PyQt5 GUI."""

    app = QApplication.instance() or QApplication(sys.argv)
    window = BattleshipGUI(
        size=size,
        fleet_type=fleet,
        difficulty=difficulty,
        two_player=two_player,
        salvo_mode=salvo,
        seed=seed,
    )
    window.show()
    app.exec()


__all__ = ["BattleshipGUI", "run_gui"]
