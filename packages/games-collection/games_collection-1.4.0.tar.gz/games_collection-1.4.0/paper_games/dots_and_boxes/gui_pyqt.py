"""PyQt5-powered graphical interface for Dots and Boxes.

This GUI provides a visual interface for playing Dots and Boxes with features including:
* Interactive board with clickable edges
* Chain identification highlighting
* Move hints/suggestions for learning
* Tournament mode support
"""

from __future__ import annotations

from typing import Optional

from PyQt5.QtCore import QPointF, QRectF, Qt, QTimer
from PyQt5.QtGui import QBrush, QColor, QFont, QPainter, QPen
from PyQt5.QtWidgets import QApplication, QHBoxLayout, QLabel, QMessageBox, QPushButton, QVBoxLayout, QWidget

from .dots_and_boxes import DotsAndBoxes, EdgeKey


class BoardCanvas(QWidget):
    """Custom widget for rendering the Dots and Boxes board."""

    DOT_SIZE = 8
    CELL_SIZE = 60
    EDGE_WIDTH = 4
    EDGE_HOVER_WIDTH = 6

    def __init__(self, gui: "DotsAndBoxesGUI", size: int) -> None:
        """Initialize the board canvas.

        Args:
            gui: Parent GUI instance
            size: Board size (2-6)
        """
        super().__init__()
        self.gui = gui
        self.size = size
        self.offset = 20
        self.hovered_edge: Optional[EdgeKey] = None

        canvas_size = self.CELL_SIZE * self.size + 40
        self.setFixedSize(canvas_size, canvas_size)
        self.setMouseTracking(True)
        self.setStyleSheet("background-color: white;")

    def paintEvent(self, event) -> None:
        """Paint the board."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw dots
        for row in range(self.size + 1):
            for col in range(self.size + 1):
                x = self.offset + col * self.CELL_SIZE
                y = self.offset + row * self.CELL_SIZE
                painter.setBrush(QBrush(QColor("black")))
                painter.setPen(QPen(QColor("black")))
                painter.drawEllipse(
                    QPointF(x, y),
                    self.DOT_SIZE // 2,
                    self.DOT_SIZE // 2,
                )

        # Draw horizontal edges
        for row in range(self.size + 1):
            for col in range(self.size):
                x1 = self.offset + col * self.CELL_SIZE
                y1 = self.offset + row * self.CELL_SIZE
                x2 = self.offset + (col + 1) * self.CELL_SIZE
                y2 = y1

                owner = self.gui.game.horizontal_edges[(row, col)]
                is_hovered = self.hovered_edge == ("h", row, col)

                if owner:
                    color = QColor("blue") if owner == self.gui.game.human_name else QColor("red")
                    width = self.EDGE_WIDTH
                elif is_hovered:
                    color = QColor("green")
                    width = self.EDGE_HOVER_WIDTH
                else:
                    color = QColor("lightgray")
                    width = self.EDGE_WIDTH

                painter.setPen(QPen(color, width))
                painter.drawLine(x1, y1, x2, y2)

        # Draw vertical edges
        for row in range(self.size):
            for col in range(self.size + 1):
                x1 = self.offset + col * self.CELL_SIZE
                y1 = self.offset + row * self.CELL_SIZE
                x2 = x1
                y2 = self.offset + (row + 1) * self.CELL_SIZE

                owner = self.gui.game.vertical_edges[(row, col)]
                is_hovered = self.hovered_edge == ("v", row, col)

                if owner:
                    color = QColor("blue") if owner == self.gui.game.human_name else QColor("red")
                    width = self.EDGE_WIDTH
                elif is_hovered:
                    color = QColor("green")
                    width = self.EDGE_HOVER_WIDTH
                else:
                    color = QColor("lightgray")
                    width = self.EDGE_WIDTH

                painter.setPen(QPen(color, width))
                painter.drawLine(x1, y1, x2, y2)

        # Draw box labels
        font = QFont("Arial", 20, QFont.Weight.Bold)
        painter.setFont(font)
        for row in range(self.size):
            for col in range(self.size):
                owner = self.gui.game.boxes[(row, col)]
                if owner:
                    x = self.offset + col * self.CELL_SIZE + self.CELL_SIZE // 2
                    y = self.offset + row * self.CELL_SIZE + self.CELL_SIZE // 2
                    text = "H" if owner == self.gui.game.human_name else "C"
                    color = QColor("blue") if owner == self.gui.game.human_name else QColor("red")
                    painter.setPen(color)
                    rect = QRectF(x - 20, y - 20, 40, 40)
                    painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, text)

    def mouseMoveEvent(self, event) -> None:
        """Handle mouse movement over the canvas."""
        if not self.gui.player_turn or self.gui.game.is_finished():
            return

        edge = self._get_edge_from_position(event.pos().x(), event.pos().y())
        if edge != self.hovered_edge:
            self.hovered_edge = edge
            self.update()

            if edge:
                self.gui._update_chain_info(edge)
            else:
                self.gui.chain_label.setText("Hover over edges to see chain info")

    def leaveEvent(self, event) -> None:
        """Handle mouse leaving the canvas."""
        if self.hovered_edge:
            self.hovered_edge = None
            self.update()
            self.gui.chain_label.setText("Hover over edges to see chain info")

    def mousePressEvent(self, event) -> None:
        """Handle mouse click on the canvas."""
        if not self.gui.player_turn or self.gui.game.is_finished():
            return

        if event.button() == Qt.MouseButton.LeftButton:
            edge = self._get_edge_from_position(event.pos().x(), event.pos().y())
            if edge:
                self.gui._make_move(edge)

    def _get_edge_from_position(self, x: int, y: int) -> Optional[EdgeKey]:
        """Determine which edge is at the given canvas position.

        Returns:
            EdgeKey if an edge is found, None otherwise
        """
        threshold = 10

        # Check horizontal edges
        for row in range(self.size + 1):
            for col in range(self.size):
                x1 = self.offset + col * self.CELL_SIZE
                y1 = self.offset + row * self.CELL_SIZE
                x2 = self.offset + (col + 1) * self.CELL_SIZE
                y2 = y1

                # Check if click is near this horizontal edge
                if abs(y - y1) < threshold and x1 - threshold <= x <= x2 + threshold:
                    if self.gui.game.horizontal_edges[(row, col)] is None:
                        return ("h", row, col)

        # Check vertical edges
        for row in range(self.size):
            for col in range(self.size + 1):
                x1 = self.offset + col * self.CELL_SIZE
                y1 = self.offset + row * self.CELL_SIZE
                x2 = x1
                y2 = self.offset + (row + 1) * self.CELL_SIZE

                # Check if click is near this vertical edge
                if abs(x - x1) < threshold and y1 - threshold <= y <= y2 + threshold:
                    if self.gui.game.vertical_edges[(row, col)] is None:
                        return ("v", row, col)

        return None


class DotsAndBoxesGUI(QWidget):
    """GUI for the Dots and Boxes game using PyQt5."""

    def __init__(self, size: int = 2, show_hints: bool = False) -> None:
        """Initialize the GUI.

        Args:
            size: Board size (2-6)
            show_hints: Whether to show move hints
        """
        super().__init__()
        self.size = size
        self.show_hints = show_hints
        self.game = DotsAndBoxes(size=size)
        self.player_turn = True

        self.setWindowTitle(f"Dots and Boxes ({size}x{size})")
        self._build_layout()
        self._update_status()

    def _build_layout(self) -> None:
        """Build the main window layout."""
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Canvas for the board
        self.canvas = BoardCanvas(self, self.size)
        main_layout.addWidget(self.canvas)

        # Sidebar
        sidebar = QVBoxLayout()
        sidebar.setContentsMargins(10, 10, 10, 10)

        # Status label
        status_header = QLabel("Game Status")
        status_header.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        sidebar.addWidget(status_header)

        self.status_label = QLabel("Your turn!")
        self.status_label.setWordWrap(True)
        self.status_label.setMaximumWidth(200)
        sidebar.addWidget(self.status_label)
        sidebar.addSpacing(10)

        # Score display
        score_header = QLabel("Score")
        score_header.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        sidebar.addWidget(score_header)

        self.score_label = QLabel("")
        self.score_label.setWordWrap(True)
        self.score_label.setMaximumWidth(200)
        sidebar.addWidget(self.score_label)
        sidebar.addSpacing(10)

        # Hint button (if enabled)
        if self.show_hints:
            self.hint_button = QPushButton("Show Hint")
            self.hint_button.clicked.connect(self._show_hint)
            sidebar.addWidget(self.hint_button)

        # Chain info
        sidebar.addSpacing(10)
        chain_header = QLabel("Chain Info")
        chain_header.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        sidebar.addWidget(chain_header)

        self.chain_label = QLabel("Hover over edges to see chain info")
        self.chain_label.setWordWrap(True)
        self.chain_label.setMaximumWidth(200)
        sidebar.addWidget(self.chain_label)

        # Control buttons
        sidebar.addSpacing(20)
        new_game_btn = QPushButton("New Game")
        new_game_btn.clicked.connect(self._new_game)
        sidebar.addWidget(new_game_btn)

        quit_btn = QPushButton("Quit")
        quit_btn.clicked.connect(self.close)
        sidebar.addWidget(quit_btn)

        sidebar.addStretch()

        # Add sidebar to main layout
        sidebar_widget = QWidget()
        sidebar_widget.setLayout(sidebar)
        main_layout.addWidget(sidebar_widget)

        self.setLayout(main_layout)

    def _update_chain_info(self, edge: EdgeKey) -> None:
        """Update the chain information label based on the hovered edge."""
        if self.game._would_complete_box(edge):
            self.chain_label.setText("⭐ This move completes a box!")
        elif self.game._creates_third_edge(edge):
            chain_length = self.game._chain_length_if_opened(edge)
            self.chain_label.setText(f"⚠️ Warning: This creates a chain!\nOpponent could capture {chain_length} box{'es' if chain_length != 1 else ''}.")
        else:
            self.chain_label.setText("✅ Safe move - no chain created")

    def _make_move(self, edge: EdgeKey) -> None:
        """Make a move at the specified edge."""
        orient, row, col = edge
        try:
            completed = self.game.claim_edge(orient, row, col, player=self.game.human_name)
            self.canvas.update()

            if not self.game.is_finished():
                if not completed:
                    # Computer's turn
                    self.player_turn = False
                    self._update_status()
                    QTimer.singleShot(500, self._computer_turn)
                else:
                    self._update_status()
            else:
                self._game_over()

        except (ValueError, KeyError) as e:
            QMessageBox.critical(self, "Invalid Move", str(e))

    def _computer_turn(self) -> None:
        """Execute the computer's turn."""
        self.game.computer_turn()
        self.canvas.update()

        if not self.game.is_finished():
            self.player_turn = True
            self._update_status()
        else:
            self._game_over()

    def _update_status(self) -> None:
        """Update the status and score labels."""
        human_score = self.game.scores[self.game.human_name]
        computer_score = self.game.scores[self.game.computer_name]

        self.score_label.setText(f"You: {human_score}\nComputer: {computer_score}")

        if self.game.is_finished():
            self.status_label.setText("Game Over!")
        elif self.player_turn:
            self.status_label.setText("Your turn!")
        else:
            self.status_label.setText("Computer's turn...")

    def _game_over(self) -> None:
        """Handle game over."""
        self._update_status()
        human_score = self.game.scores[self.game.human_name]
        computer_score = self.game.scores[self.game.computer_name]

        if human_score > computer_score:
            result = "You win! 🎉"
        elif human_score < computer_score:
            result = "Computer wins! 🤖"
        else:
            result = "It's a tie! 🤝"

        QMessageBox.information(self, "Game Over", f"{result}\n\nYou: {human_score}\nComputer: {computer_score}")

    def _show_hint(self) -> None:
        """Show a hint for the next move."""
        if self.game.is_finished() or not self.player_turn:
            return

        # Find a good move
        scoring_move = self.game._find_scoring_move()
        if scoring_move:
            hint_text = f"Complete a box with: {scoring_move[0]} {scoring_move[1]} {scoring_move[2]}"
        else:
            safe_moves = [move for move in self.game.available_edges() if not self.game._creates_third_edge(move)]
            if safe_moves:
                move = safe_moves[0]
                hint_text = f"Safe move: {move[0]} {move[1]} {move[2]}"
            else:
                move = self.game._choose_chain_starter()
                chain_length = self.game._chain_length_if_opened(move)
                hint_text = f"Best of bad options: {move[0]} {move[1]} {move[2]}\n(Opens chain of {chain_length})"

        QMessageBox.information(self, "Hint", hint_text)

    def _new_game(self) -> None:
        """Start a new game."""
        self.game = DotsAndBoxes(size=self.size)
        self.player_turn = True
        self.canvas.hovered_edge = None
        self.canvas.update()
        self._update_status()


def run_gui(size: int = 2, show_hints: bool = False) -> None:
    """Launch the Dots and Boxes GUI.

    Args:
        size: Board size (2-6)
        show_hints: Whether to enable move hints
    """
    app = QApplication.instance()
    if app is None:
        import sys

        app = QApplication(sys.argv)

    window = DotsAndBoxesGUI(size=size, show_hints=show_hints)
    window.show()
    app.exec()


if __name__ == "__main__":
    run_gui(size=3, show_hints=True)
