"""Tkinter-powered graphical interface for Dots and Boxes.

This GUI provides a visual interface for playing Dots and Boxes with features including:
* Interactive board with clickable edges
* Chain identification highlighting
* Move hints/suggestions for learning
* Tournament mode support
"""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk
from typing import List, Optional, Tuple

from .dots_and_boxes import DotsAndBoxes, EdgeKey


class DotsAndBoxesGUI:
    """GUI for the Dots and Boxes game."""

    DOT_SIZE = 8
    CELL_SIZE = 60
    EDGE_WIDTH = 4
    EDGE_HOVER_WIDTH = 6

    def __init__(self, root: tk.Tk, size: int = 2, show_hints: bool = False) -> None:
        """Initialize the GUI.

        Args:
            root: The Tkinter root window
            size: Board size (2-6)
            show_hints: Whether to show move hints
        """
        self.root = root
        self.size = size
        self.show_hints = show_hints
        self.game = DotsAndBoxes(size=size)
        self.player_turn = True
        self.hovered_edge: Optional[EdgeKey] = None
        self.chain_edges: List[EdgeKey] = []

        # Edge line IDs for rendering
        self.horizontal_lines: dict[Tuple[int, int], int] = {}
        self.vertical_lines: dict[Tuple[int, int], int] = {}
        self.box_labels: dict[Tuple[int, int], int] = {}

        # Configure root window
        self.root.title(f"Dots and Boxes ({size}x{size})")
        self.root.resizable(False, False)

        # Apply styling
        style = ttk.Style()
        style.theme_use("clam")

        self._build_layout()
        self._draw_board()
        self._update_status()

    def _build_layout(self) -> None:
        """Build the main window layout."""
        # Main container
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.grid(row=0, column=0, sticky="nsew")

        # Canvas for the board
        canvas_size = self.CELL_SIZE * self.size + 40
        self.canvas = tk.Canvas(
            main_frame,
            width=canvas_size,
            height=canvas_size,
            bg="white",
            highlightthickness=1,
            highlightbackground="gray",
        )
        self.canvas.grid(row=0, column=0, padx=10, pady=10)

        # Sidebar
        sidebar = ttk.Frame(main_frame, padding=10)
        sidebar.grid(row=0, column=1, sticky="nsew", padx=10)

        # Status label
        ttk.Label(sidebar, text="Game Status", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(0, 5))
        self.status_label = ttk.Label(sidebar, text="Your turn!", wraplength=200)
        self.status_label.pack(anchor="w", pady=(0, 10))

        # Score display
        ttk.Label(sidebar, text="Score", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(0, 5))
        self.score_label = ttk.Label(sidebar, text="", wraplength=200)
        self.score_label.pack(anchor="w", pady=(0, 10))

        # Hint button (if enabled)
        if self.show_hints:
            self.hint_button = ttk.Button(sidebar, text="Show Hint", command=self._show_hint)
            self.hint_button.pack(fill="x", pady=5)

        # Chain info
        ttk.Label(sidebar, text="Chain Info", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(10, 5))
        self.chain_label = ttk.Label(sidebar, text="Hover over edges to see chain info", wraplength=200)
        self.chain_label.pack(anchor="w")

        # Control buttons
        ttk.Button(sidebar, text="New Game", command=self._new_game).pack(fill="x", pady=(20, 5))
        ttk.Button(sidebar, text="Quit", command=self.root.quit).pack(fill="x", pady=5)

        # Bind canvas events
        self.canvas.bind("<Motion>", self._on_mouse_move)
        self.canvas.bind("<Button-1>", self._on_click)
        self.canvas.bind("<Leave>", self._on_mouse_leave)

    def _draw_board(self) -> None:
        """Draw the initial board state."""
        self.canvas.delete("all")
        offset = 20

        # Draw dots
        for row in range(self.size + 1):
            for col in range(self.size + 1):
                x = offset + col * self.CELL_SIZE
                y = offset + row * self.CELL_SIZE
                self.canvas.create_oval(
                    x - self.DOT_SIZE // 2,
                    y - self.DOT_SIZE // 2,
                    x + self.DOT_SIZE // 2,
                    y + self.DOT_SIZE // 2,
                    fill="black",
                    outline="black",
                )

        # Draw horizontal edges
        for row in range(self.size + 1):
            for col in range(self.size):
                x1 = offset + col * self.CELL_SIZE
                y1 = offset + row * self.CELL_SIZE
                x2 = offset + (col + 1) * self.CELL_SIZE
                y2 = y1
                line_id = self.canvas.create_line(x1, y1, x2, y2, width=self.EDGE_WIDTH, fill="lightgray", tags="edge")
                self.horizontal_lines[(row, col)] = line_id

        # Draw vertical edges
        for row in range(self.size):
            for col in range(self.size + 1):
                x1 = offset + col * self.CELL_SIZE
                y1 = offset + row * self.CELL_SIZE
                x2 = x1
                y2 = offset + (row + 1) * self.CELL_SIZE
                line_id = self.canvas.create_line(x1, y1, x2, y2, width=self.EDGE_WIDTH, fill="lightgray", tags="edge")
                self.vertical_lines[(row, col)] = line_id

        # Initialize box labels (will be filled when boxes are claimed)
        for row in range(self.size):
            for col in range(self.size):
                x = offset + col * self.CELL_SIZE + self.CELL_SIZE // 2
                y = offset + row * self.CELL_SIZE + self.CELL_SIZE // 2
                label_id = self.canvas.create_text(x, y, text="", font=("Arial", 20, "bold"), fill="")
                self.box_labels[(row, col)] = label_id

        self._update_board()

    def _update_board(self) -> None:
        """Update the board display to match the game state."""
        # Update horizontal edges
        for (row, col), owner in self.game.horizontal_edges.items():
            line_id = self.horizontal_lines[(row, col)]
            if owner:
                color = "blue" if owner == self.game.human_name else "red"
                self.canvas.itemconfig(line_id, fill=color, width=self.EDGE_WIDTH)

        # Update vertical edges
        for (row, col), owner in self.game.vertical_edges.items():
            line_id = self.vertical_lines[(row, col)]
            if owner:
                color = "blue" if owner == self.game.human_name else "red"
                self.canvas.itemconfig(line_id, fill=color, width=self.EDGE_WIDTH)

        # Update boxes
        for (row, col), owner in self.game.boxes.items():
            label_id = self.box_labels[(row, col)]
            if owner:
                text = "H" if owner == self.game.human_name else "C"
                color = "blue" if owner == self.game.human_name else "red"
                self.canvas.itemconfig(label_id, text=text, fill=color)

    def _get_edge_from_position(self, x: int, y: int) -> Optional[EdgeKey]:
        """Determine which edge is at the given canvas position.

        Returns:
            EdgeKey if an edge is found, None otherwise
        """
        offset = 20
        threshold = 10

        # Check horizontal edges
        for row in range(self.size + 1):
            for col in range(self.size):
                x1 = offset + col * self.CELL_SIZE
                y1 = offset + row * self.CELL_SIZE
                x2 = offset + (col + 1) * self.CELL_SIZE
                y2 = y1

                # Check if click is near this horizontal edge
                if abs(y - y1) < threshold and x1 - threshold <= x <= x2 + threshold:
                    if self.game.horizontal_edges[(row, col)] is None:
                        return ("h", row, col)

        # Check vertical edges
        for row in range(self.size):
            for col in range(self.size + 1):
                x1 = offset + col * self.CELL_SIZE
                y1 = offset + row * self.CELL_SIZE
                x2 = x1
                y2 = offset + (row + 1) * self.CELL_SIZE

                # Check if click is near this vertical edge
                if abs(x - x1) < threshold and y1 - threshold <= y <= y2 + threshold:
                    if self.game.vertical_edges[(row, col)] is None:
                        return ("v", row, col)

        return None

    def _on_mouse_move(self, event: tk.Event) -> None:
        """Handle mouse movement over the canvas."""
        if not self.player_turn or self.game.is_finished():
            return

        edge = self._get_edge_from_position(event.x, event.y)

        # Clear previous hover
        if self.hovered_edge and self.hovered_edge != edge:
            orient, row, col = self.hovered_edge
            line_id = self.horizontal_lines[(row, col)] if orient == "h" else self.vertical_lines[(row, col)]
            self.canvas.itemconfig(line_id, width=self.EDGE_WIDTH, fill="lightgray")

        # Apply new hover
        self.hovered_edge = edge
        if edge:
            orient, row, col = edge
            line_id = self.horizontal_lines[(row, col)] if orient == "h" else self.vertical_lines[(row, col)]
            self.canvas.itemconfig(line_id, width=self.EDGE_HOVER_WIDTH, fill="green")

            # Show chain information
            self._update_chain_info(edge)

    def _on_mouse_leave(self, event: tk.Event) -> None:
        """Handle mouse leaving the canvas."""
        if self.hovered_edge:
            orient, row, col = self.hovered_edge
            line_id = self.horizontal_lines[(row, col)] if orient == "h" else self.vertical_lines[(row, col)]
            if self.game._edge_map(orient)[(row, col)] is None:
                self.canvas.itemconfig(line_id, width=self.EDGE_WIDTH, fill="lightgray")
        self.hovered_edge = None
        self.chain_label.config(text="Hover over edges to see chain info")

    def _update_chain_info(self, edge: EdgeKey) -> None:
        """Update the chain information label based on the hovered edge."""
        if self.game._would_complete_box(edge):
            self.chain_label.config(text="⭐ This move completes a box!")
        elif self.game._creates_third_edge(edge):
            chain_length = self.game._chain_length_if_opened(edge)
            self.chain_label.config(text=f"⚠️ Warning: This creates a chain!\n" f"Opponent could capture {chain_length} box{'es' if chain_length != 1 else ''}.")
        else:
            self.chain_label.config(text="✅ Safe move - no chain created")

    def _on_click(self, event: tk.Event) -> None:
        """Handle mouse click on the canvas."""
        if not self.player_turn or self.game.is_finished():
            return

        edge = self._get_edge_from_position(event.x, event.y)
        if edge:
            self._make_move(edge)

    def _make_move(self, edge: EdgeKey) -> None:
        """Make a move at the specified edge."""
        orient, row, col = edge
        try:
            completed = self.game.claim_edge(orient, row, col, player=self.game.human_name)
            self._update_board()

            if not self.game.is_finished():
                if not completed:
                    # Computer's turn
                    self.player_turn = False
                    self._update_status()
                    self.root.after(500, self._computer_turn)
                else:
                    self._update_status()
            else:
                self._game_over()

        except (ValueError, KeyError) as e:
            messagebox.showerror("Invalid Move", str(e))

    def _computer_turn(self) -> None:
        """Execute the computer's turn."""
        self.game.computer_turn()
        self._update_board()

        if not self.game.is_finished():
            self.player_turn = True
            self._update_status()
        else:
            self._game_over()

    def _update_status(self) -> None:
        """Update the status and score labels."""
        human_score = self.game.scores[self.game.human_name]
        computer_score = self.game.scores[self.game.computer_name]

        self.score_label.config(text=f"You: {human_score}\nComputer: {computer_score}")

        if self.game.is_finished():
            self.status_label.config(text="Game Over!")
        elif self.player_turn:
            self.status_label.config(text="Your turn!")
        else:
            self.status_label.config(text="Computer's turn...")

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

        messagebox.showinfo("Game Over", f"{result}\n\nYou: {human_score}\nComputer: {computer_score}")

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

        messagebox.showinfo("Hint", hint_text)

    def _new_game(self) -> None:
        """Start a new game."""
        self.game = DotsAndBoxes(size=self.size)
        self.player_turn = True
        self.hovered_edge = None
        self._draw_board()
        self._update_status()


def run_gui(size: int = 2, show_hints: bool = False) -> None:
    """Launch the Dots and Boxes GUI.

    Args:
        size: Board size (2-6)
        show_hints: Whether to enable move hints
    """
    root = tk.Tk()
    DotsAndBoxesGUI(root, size=size, show_hints=show_hints)
    root.mainloop()


if __name__ == "__main__":
    run_gui(size=3, show_hints=True)
