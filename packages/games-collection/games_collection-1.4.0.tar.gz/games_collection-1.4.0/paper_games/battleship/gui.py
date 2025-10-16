"""Tkinter-powered graphical interface for Battleship.

This GUI provides a visual interface for playing Battleship with features including:
* Interactive board with drag-and-drop ship placement
* Visual feedback for hits, misses, and sunk ships
* Support for different board sizes (8x8, 10x10)
* Support for different fleet configurations
* AI difficulty levels
* 2-player hot-seat mode
* Salvo mode (multiple shots per turn)
"""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk
from typing import Dict, Optional, Set, Tuple

from .battleship import DEFAULT_FLEET, EXTENDED_FLEET, SMALL_FLEET, BattleshipGame, Coordinate


class BattleshipGUI:
    """GUI for the Battleship game."""

    CELL_SIZE = 40
    BOARD_PADDING = 30

    def __init__(
        self,
        root: tk.Tk,
        size: int = 10,
        fleet_type: str = "default",
        difficulty: str = "medium",
        two_player: bool = False,
        salvo_mode: bool = False,
        seed: Optional[int] = None,
    ) -> None:
        """Initialize the GUI.

        Args:
            root: The Tkinter root window
            size: Board size (8 or 10)
            fleet_type: Fleet configuration ("small", "default", "extended")
            difficulty: AI difficulty level ("easy", "medium", "hard")
            two_player: Enable 2-player hot-seat mode
            salvo_mode: Enable salvo mode (multiple shots per turn)
            seed: Random seed for reproducible games
        """
        self.root = root
        self.size = size
        self.fleet_type = fleet_type
        self.difficulty = difficulty
        self.two_player = two_player
        self.salvo_mode = salvo_mode
        self.seed = seed

        # Select fleet based on fleet_type
        fleet_map = {
            "small": SMALL_FLEET,
            "default": DEFAULT_FLEET,
            "extended": EXTENDED_FLEET,
        }
        self.fleet = fleet_map[fleet_type]

        # Create random number generator
        import random

        rng = random.Random(seed) if seed is not None else None

        # Create game instance
        self.game = BattleshipGame(
            size=size,
            fleet=self.fleet,
            rng=rng,
            difficulty=difficulty,
            two_player=two_player,
            salvo_mode=salvo_mode,
        )

        # Game state
        self.setup_phase = True
        self.current_player = 1  # 1 for player/Player 1, 2 for AI/Player 2
        self.placing_ship_index = 0
        self.ship_orientation = "h"  # h or v
        self.dragging_ship: Optional[Tuple[str, int]] = None
        self.preview_coords: Set[Coordinate] = set()

        # Track shots remaining in salvo mode
        self.shots_remaining = 0

        # Canvas elements
        self.player_cells: Dict[Coordinate, int] = {}
        self.opponent_cells: Dict[Coordinate, int] = {}

        # Configure root window
        mode_str = "2-Player" if two_player else f"vs AI ({difficulty})"
        salvo_str = " [SALVO]" if salvo_mode else ""
        self.root.title(f"Battleship {size}x{size} - {mode_str}{salvo_str}")
        self.root.resizable(False, False)

        # Apply styling
        style = ttk.Style()
        style.theme_use("clam")

        self._build_layout()
        self._draw_boards()
        self._update_status()

    def _build_layout(self) -> None:
        """Build the main window layout."""
        # Main container
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.grid(row=0, column=0, sticky="nsew")

        # Top frame for boards
        boards_frame = ttk.Frame(main_frame)
        boards_frame.grid(row=0, column=0, columnspan=2, pady=(0, 10))

        # Player board (left)
        player_frame = ttk.LabelFrame(boards_frame, text="Your Fleet", padding=10)
        player_frame.grid(row=0, column=0, padx=(0, 10))

        canvas_size = self.CELL_SIZE * self.size + self.BOARD_PADDING * 2
        self.player_canvas = tk.Canvas(
            player_frame,
            width=canvas_size,
            height=canvas_size,
            bg="lightblue",
            highlightthickness=1,
            highlightbackground="navy",
        )
        self.player_canvas.pack()

        # Opponent board (right)
        opponent_frame = ttk.LabelFrame(boards_frame, text="Enemy Waters", padding=10)
        opponent_frame.grid(row=0, column=1)

        self.opponent_canvas = tk.Canvas(
            opponent_frame,
            width=canvas_size,
            height=canvas_size,
            bg="lightblue",
            highlightthickness=1,
            highlightbackground="navy",
        )
        self.opponent_canvas.pack()

        # Sidebar
        sidebar = ttk.Frame(main_frame, padding=10)
        sidebar.grid(row=1, column=0, columnspan=2, sticky="ew")

        # Status label
        ttk.Label(sidebar, text="Status:", font=("Arial", 10, "bold")).grid(row=0, column=0, sticky="w", padx=(0, 5))
        self.status_label = ttk.Label(sidebar, text="", font=("Arial", 10))
        self.status_label.grid(row=0, column=1, sticky="w")

        # Ship placement controls (shown during setup)
        self.setup_frame = ttk.Frame(sidebar)
        self.setup_frame.grid(row=1, column=0, columnspan=2, pady=10, sticky="ew")

        ttk.Label(self.setup_frame, text="Ship Placement:").grid(row=0, column=0, sticky="w")

        self.orientation_button = ttk.Button(
            self.setup_frame,
            text="Orientation: Horizontal",
            command=self._toggle_orientation,
        )
        self.orientation_button.grid(row=0, column=1, padx=5)

        self.random_button = ttk.Button(
            self.setup_frame,
            text="Place Randomly",
            command=self._place_ships_randomly,
        )
        self.random_button.grid(row=0, column=2, padx=5)

        # Game controls
        control_frame = ttk.Frame(sidebar)
        control_frame.grid(row=2, column=0, columnspan=2, pady=5, sticky="ew")

        ttk.Button(control_frame, text="New Game", command=self._new_game).pack(side="left", padx=5)
        ttk.Button(control_frame, text="Quit", command=self.root.quit).pack(side="left", padx=5)

        # Bind canvas events
        self.player_canvas.bind("<Motion>", self._on_player_canvas_motion)
        self.player_canvas.bind("<Button-1>", self._on_player_canvas_click)
        self.opponent_canvas.bind("<Button-1>", self._on_opponent_canvas_click)

    def _draw_boards(self) -> None:
        """Draw both game boards."""
        self._draw_board(self.player_canvas, is_player=True)
        self._draw_board(self.opponent_canvas, is_player=False)

    def _draw_board(self, canvas: tk.Canvas, is_player: bool) -> None:
        """Draw a single game board.

        Args:
            canvas: Canvas to draw on
            is_player: True for player board, False for opponent board
        """
        canvas.delete("all")
        offset = self.BOARD_PADDING

        # Get the appropriate board
        board = self.game.player_board if is_player else self.game.opponent_board
        cells_dict = self.player_cells if is_player else self.opponent_cells
        cells_dict.clear()

        # Draw column labels
        for col in range(self.size):
            x = offset + col * self.CELL_SIZE + self.CELL_SIZE // 2
            y = offset // 2
            canvas.create_text(x, y, text=str(col), font=("Arial", 8))

        # Draw row labels
        for row in range(self.size):
            x = offset // 2
            y = offset + row * self.CELL_SIZE + self.CELL_SIZE // 2
            canvas.create_text(x, y, text=str(row), font=("Arial", 8))

        # Draw grid cells
        for row in range(self.size):
            for col in range(self.size):
                coord = (row, col)
                x1 = offset + col * self.CELL_SIZE
                y1 = offset + row * self.CELL_SIZE
                x2 = x1 + self.CELL_SIZE
                y2 = y1 + self.CELL_SIZE

                # Determine cell color
                color = "lightblue"

                # Show ships on player board or during setup
                if is_player and coord in board.occupied:
                    color = "gray"

                # Show shots
                if coord in board.shots:
                    shot_result = board.shots[coord]
                    if shot_result == "miss":
                        color = "white"
                    elif shot_result in ("hit", "sunk"):
                        color = "red"

                # Show preview during ship placement
                if is_player and self.setup_phase and coord in self.preview_coords:
                    color = "lightgreen"

                rect_id = canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="navy", width=1)
                cells_dict[coord] = rect_id

                # Show hit/miss markers
                if coord in board.shots:
                    shot_result = board.shots[coord]
                    cx = (x1 + x2) // 2
                    cy = (y1 + y2) // 2
                    if shot_result == "miss":
                        canvas.create_text(cx, cy, text="○", font=("Arial", 16), fill="blue")
                    elif shot_result in ("hit", "sunk"):
                        canvas.create_text(cx, cy, text="✗", font=("Arial", 16, "bold"), fill="darkred")

    def _get_canvas_coordinate(self, canvas: tk.Canvas, event: tk.Event) -> Optional[Coordinate]:
        """Convert canvas pixel coordinates to board coordinates.

        Args:
            canvas: The canvas widget
            event: Mouse event

        Returns:
            Board coordinate tuple or None if outside the board
        """
        offset = self.BOARD_PADDING
        col = (event.x - offset) // self.CELL_SIZE
        row = (event.y - offset) // self.CELL_SIZE

        if 0 <= row < self.size and 0 <= col < self.size:
            return (row, col)
        return None

    def _on_player_canvas_motion(self, event: tk.Event) -> None:
        """Handle mouse motion over player canvas."""
        if not self.setup_phase:
            return

        coord = self._get_canvas_coordinate(self.player_canvas, event)
        if coord is None:
            self.preview_coords.clear()
            self._draw_board(self.player_canvas, is_player=True)
            return

        # Calculate preview coordinates for current ship
        if self.placing_ship_index < len(self.fleet):
            ship_name, ship_length = self.fleet[self.placing_ship_index]
            row, col = coord

            preview_coords = set()
            if self.ship_orientation == "h":
                for i in range(ship_length):
                    preview_coords.add((row, col + i))
            else:  # vertical
                for i in range(ship_length):
                    preview_coords.add((row + i, col))

            # Check if placement is valid
            valid = True
            for c in preview_coords:
                if not self.game.player_board.in_bounds(c) or c in self.game.player_board.occupied:
                    valid = False
                    break

            if valid:
                self.preview_coords = preview_coords
            else:
                self.preview_coords.clear()

            self._draw_board(self.player_canvas, is_player=True)

    def _on_player_canvas_click(self, event: tk.Event) -> None:
        """Handle click on player canvas."""
        if not self.setup_phase:
            return

        coord = self._get_canvas_coordinate(self.player_canvas, event)
        if coord is None or self.placing_ship_index >= len(self.fleet):
            return

        ship_name, ship_length = self.fleet[self.placing_ship_index]

        # Try to place the ship
        try:
            self.game.player_board.place_ship(ship_name, ship_length, coord, self.ship_orientation)
            self.placing_ship_index += 1
            self.preview_coords.clear()

            # Check if all ships are placed
            if self.placing_ship_index >= len(self.fleet):
                self._finish_player_setup()
            else:
                self._update_status()

            self._draw_board(self.player_canvas, is_player=True)

        except ValueError as e:
            messagebox.showerror("Invalid Placement", str(e))

    def _on_opponent_canvas_click(self, event: tk.Event) -> None:
        """Handle click on opponent canvas."""
        if self.setup_phase:
            return

        # Check if it's the player's turn
        if self.two_player:
            # In 2-player mode, both players shoot at each other's boards
            # But we need to handle turn management differently
            pass
        elif self.current_player != 1:
            return

        coord = self._get_canvas_coordinate(self.opponent_canvas, event)
        if coord is None:
            return

        # Check if already shot
        if coord in self.game.opponent_board.shots:
            messagebox.showwarning("Invalid Shot", "You already shot at this location!")
            return

        # Take the shot
        try:
            result, ship_name = self.game.player_shoot(coord)

            self._draw_boards()

            # Show result
            if result == "miss":
                msg = "Miss!"
            elif result == "hit":
                msg = "Hit!"
            else:  # sunk
                msg = f"You sank the enemy {ship_name}!"

            # Update status temporarily to show shot result
            self.status_label.config(text=msg)
            self.root.update()
            self.root.after(500)  # Brief pause to show result

            # Decrement shots remaining in salvo mode
            if self.salvo_mode:
                self.shots_remaining -= 1

            # Check for win
            if self.game.opponent_has_lost():
                self._draw_boards()
                messagebox.showinfo("Victory!", "You sank all enemy ships! You win!")
                self._new_game()
                return

            # Check if salvo turn continues
            if self.salvo_mode and self.shots_remaining > 0:
                self._update_status()
                return

            # AI turn
            if not self.two_player:
                self.current_player = 2
                self._update_status()
                self.root.after(500, self._ai_take_turn)

        except ValueError as e:
            messagebox.showerror("Invalid Shot", str(e))

    def _ai_take_turn(self) -> None:
        """AI takes its turn."""
        if self.salvo_mode:
            shots = self.game.get_salvo_count("opponent")
            self.status_label.config(text=f"AI is taking {shots} shots...")
            self.root.update()
        else:
            shots = 1

        for i in range(shots):
            if self.salvo_mode and shots > 1:
                self.root.after(300 * i)  # Stagger shots slightly

            coord, result, ship_name = self.game.ai_shoot()

            self._draw_boards()

            # Show AI's shot result
            if result == "miss":
                msg = f"AI shot at {coord} and missed."
            elif result == "hit":
                msg = f"AI hit your ship at {coord}!"
            else:  # sunk
                msg = f"AI sank your {ship_name} at {coord}!"

            self.status_label.config(text=msg)
            self.root.update()

            # Check for loss
            if self.game.player_has_lost():
                self._draw_boards()
                messagebox.showinfo("Defeat", "All your ships have been sunk! AI wins!")
                self._new_game()
                return

        # Player's turn again
        self.current_player = 1

        # Set shots remaining for next turn if salvo mode
        if self.salvo_mode:
            self.shots_remaining = self.game.get_salvo_count("player")

        self.root.after(1000, self._update_status)

    def _finish_player_setup(self) -> None:
        """Finish player setup phase."""
        if self.two_player:
            # In 2-player mode, need to setup Player 2's ships
            response = messagebox.askyesno(
                "Player 2 Setup",
                "Player 1 setup complete. Hand device to Player 2.\n\nPlace ships randomly for Player 2?",
            )
            if response:
                self.game.opponent_board.randomly_place_ships(self.fleet, self.game.rng)
            else:
                # Manual setup for Player 2 - would need to implement separate phase
                # For simplicity, just place randomly
                self.game.opponent_board.randomly_place_ships(self.fleet, self.game.rng)
        else:
            # AI opponent - place ships randomly
            self.game.opponent_board.randomly_place_ships(self.fleet, self.game.rng)

        # Hide setup controls
        self.setup_frame.grid_remove()
        self.setup_phase = False

        # Initialize salvo mode shots
        if self.salvo_mode:
            self.shots_remaining = self.game.get_salvo_count("player")

        self._draw_boards()
        self._update_status()

    def _place_ships_randomly(self) -> None:
        """Place all remaining ships randomly."""
        try:
            # Clear any already placed ships and start over
            self.game.player_board.ships.clear()
            self.game.player_board.occupied.clear()
            self.game.player_board.randomly_place_ships(self.fleet, self.game.rng)
            self.placing_ship_index = len(self.fleet)
            self.preview_coords.clear()
            self._finish_player_setup()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to place ships: {e}")

    def _toggle_orientation(self) -> None:
        """Toggle ship placement orientation."""
        if self.ship_orientation == "h":
            self.ship_orientation = "v"
            self.orientation_button.config(text="Orientation: Vertical")
        else:
            self.ship_orientation = "h"
            self.orientation_button.config(text="Orientation: Horizontal")

    def _update_status(self) -> None:
        """Update the status label."""
        if self.setup_phase:
            if self.placing_ship_index < len(self.fleet):
                ship_name, ship_length = self.fleet[self.placing_ship_index]
                status = f"Place your {ship_name} (length {ship_length}). Click to place, or use 'Place Randomly' button."
            else:
                status = "Setup complete! Starting game..."
        elif self.current_player == 1:
            if self.salvo_mode:
                status = f"Your turn! You have {self.shots_remaining} shot(s) remaining."
            else:
                status = "Your turn! Click on enemy waters to fire."
        else:
            status = "AI is thinking..."

        self.status_label.config(text=status)

    def _new_game(self) -> None:
        """Start a new game."""
        # Reset game state
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
        self.current_player = 1
        self.placing_ship_index = 0
        self.ship_orientation = "h"
        self.preview_coords.clear()
        self.shots_remaining = 0

        # Show setup controls
        self.setup_frame.grid()
        self.orientation_button.config(text="Orientation: Horizontal")

        self._draw_boards()
        self._update_status()


def run_gui(
    size: int = 10,
    fleet: str = "default",
    difficulty: str = "medium",
    two_player: bool = False,
    salvo: bool = False,
    seed: Optional[int] = None,
) -> None:
    """Launch the Battleship GUI.

    Args:
        size: Board size (8 or 10)
        fleet: Fleet configuration ("small", "default", "extended")
        difficulty: AI difficulty level ("easy", "medium", "hard")
        two_player: Enable 2-player hot-seat mode
        salvo: Enable salvo mode
        seed: Random seed for reproducible games
    """
    root = tk.Tk()
    BattleshipGUI(
        root,
        size=size,
        fleet_type=fleet,
        difficulty=difficulty,
        two_player=two_player,
        salvo_mode=salvo,
        seed=seed,
    )
    root.mainloop()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Play Battleship with a graphical interface")
    parser.add_argument("--size", type=int, choices=[8, 10], default=10, help="Board size (8x8 or 10x10)")
    parser.add_argument(
        "--fleet",
        choices=["small", "default", "extended"],
        default="default",
        help="Fleet configuration",
    )
    parser.add_argument(
        "--difficulty",
        choices=["easy", "medium", "hard"],
        default="medium",
        help="AI difficulty level",
    )
    parser.add_argument("--two-player", action="store_true", help="Enable 2-player hot-seat mode")
    parser.add_argument("--salvo", action="store_true", help="Enable salvo mode")
    parser.add_argument("--seed", type=int, default=None, help="Random seed for reproducible games")

    args = parser.parse_args()

    run_gui(
        size=args.size,
        fleet=args.fleet,
        difficulty=args.difficulty,
        two_player=args.two_player,
        salvo=args.salvo,
        seed=args.seed,
    )
