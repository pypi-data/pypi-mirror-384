"""Tests for logic and puzzle games."""

from __future__ import annotations

from common.game_engine import GameState
from logic_games import LightsOutGame, MinesweeperGame, PicrossGame, SlidingPuzzleGame, SokobanGame
from logic_games.lights_out.lights_out import LightBulb
from logic_games.minesweeper.minesweeper import CellState, Difficulty


class TestMinesweeper:
    """Test Minesweeper game."""

    def test_initialization_beginner(self) -> None:
        """Test beginner difficulty initialization."""
        game = MinesweeperGame(Difficulty.BEGINNER)
        assert game.rows == 9
        assert game.cols == 9
        assert game.num_mines == 10

    def test_initialization_intermediate(self) -> None:
        """Test intermediate difficulty initialization."""
        game = MinesweeperGame(Difficulty.INTERMEDIATE)
        assert game.rows == 16
        assert game.cols == 16
        assert game.num_mines == 40

    def test_first_click_safe(self) -> None:
        """Test first click is always safe."""
        game = MinesweeperGame()
        game.state = GameState.IN_PROGRESS
        # First click should place mines
        result = game.make_move((0, 0, "reveal"))
        assert result
        # Should not have hit mine
        assert not game.game_lost

    def test_flag_cell(self) -> None:
        """Test flagging a cell."""
        game = MinesweeperGame()
        game.state = GameState.IN_PROGRESS
        result = game.make_move((0, 0, "flag"))
        assert result
        assert (0, 0) in game.flagged_positions

    def test_question_mark_cycle(self) -> None:
        """Test cycling through mark states."""
        game = MinesweeperGame()
        game.state = GameState.IN_PROGRESS

        assert game.make_move((0, 0, "question"))
        assert game.cell_states[0][0] == CellState.QUESTION

        assert game.make_move((0, 0, "flag"))
        assert game.cell_states[0][0] == CellState.FLAGGED
        assert (0, 0) in game.flagged_positions

        assert game.make_move((0, 0, "question"))
        assert game.cell_states[0][0] == CellState.QUESTION
        assert (0, 0) not in game.flagged_positions

        assert game.make_move((0, 0, "unflag"))
        assert game.cell_states[0][0] == CellState.HIDDEN

    def test_chord_reveals_neighbors(self) -> None:
        """Chord action should reveal adjacent hidden cells when flags match numbers."""

        game = MinesweeperGame()
        game.state = GameState.IN_PROGRESS
        game.board = [[False] * game.cols for _ in range(game.rows)]
        game.cell_states = [[CellState.HIDDEN] * game.cols for _ in range(game.rows)]
        game.numbers = [[0] * game.cols for _ in range(game.rows)]

        game.board[0][0] = True
        for row in range(3):
            for col in range(3):
                if not game.board[row][col]:
                    game.numbers[row][col] = game._count_adjacent_mines(row, col)

        assert game.make_move((1, 1, "reveal"))
        assert game.numbers[1][1] == 1
        assert game.cell_states[1][1] == CellState.REVEALED

        assert game.make_move((0, 0, "flag"))
        assert game.make_move((1, 1, "chord"))
        assert game.cell_states[2][2] == CellState.REVEALED

    def test_misflag_display_after_loss(self) -> None:
        """Misflagged cells should be indicated when the player loses."""

        game = MinesweeperGame()
        game.state = GameState.IN_PROGRESS
        game.board = [[False] * game.cols for _ in range(game.rows)]
        game.cell_states = [[CellState.HIDDEN] * game.cols for _ in range(game.rows)]
        game.numbers = [[0] * game.cols for _ in range(game.rows)]

        game.board[0][0] = True
        for row in range(2):
            for col in range(2):
                if not game.board[row][col]:
                    game.numbers[row][col] = game._count_adjacent_mines(row, col)

        assert game.make_move((0, 1, "flag"))
        assert game.make_move((0, 0, "reveal"))
        assert game.game_lost
        assert game.get_cell_display(0, 0) == "*"
        assert game.get_cell_display(0, 1) == "✗"


class TestSokoban:
    """Test Sokoban game."""

    def test_initialization(self) -> None:
        """Test game initializes correctly."""
        game = SokobanGame()
        assert len(game.grid) > 0
        assert game.moves == 0

    def test_find_player(self) -> None:
        """Test finding player position."""
        game = SokobanGame()
        pos = game._find_player()
        assert isinstance(pos, tuple)
        assert len(pos) == 2


class TestSlidingPuzzle:
    """Test Sliding Puzzle game."""

    def test_initialization(self) -> None:
        """Test game initializes correctly."""
        game = SlidingPuzzleGame(size=4)
        assert len(game.board) == 16
        assert 0 in game.board  # Empty space
        assert game.size == 4
        assert not game.is_game_over()

    def test_valid_moves(self) -> None:
        """Test getting valid moves."""
        game = SlidingPuzzleGame(size=4)
        moves = game.get_valid_moves()
        assert len(moves) > 0
        assert all(m in ["u", "d", "l", "r"] for m in moves)

    def test_move_execution(self) -> None:
        """Test executing moves by direction and tile number."""
        game = SlidingPuzzleGame(size=4)
        moves = game.get_valid_moves()
        assert moves
        initial_moves = game.moves
        assert game.make_move(moves[0])
        assert game.moves == initial_moves + 1

        zero_idx = game.board.index(0)
        row, col = divmod(zero_idx, game.size)
        neighbor_indices = []
        if row > 0:
            neighbor_indices.append(zero_idx - game.size)
        if row < game.size - 1:
            neighbor_indices.append(zero_idx + game.size)
        if col > 0:
            neighbor_indices.append(zero_idx - 1)
        if col < game.size - 1:
            neighbor_indices.append(zero_idx + 1)
        tile_to_slide = next(game.board[idx] for idx in neighbor_indices if game.board[idx] != 0)
        assert tile_to_slide != 0
        assert game.make_move(str(tile_to_slide))


class TestLightsOut:
    """Test Lights Out game."""

    def test_initialization(self) -> None:
        """Test game initializes correctly."""
        game = LightsOutGame(size=5)
        assert len(game.grid) == 5
        assert all(len(row) == 5 for row in game.grid)
        assert all(isinstance(cell, LightBulb) for row in game.grid for cell in row)

    def test_toggle_cell(self) -> None:
        """Test toggling a cell."""
        game = LightsOutGame(size=3)
        positions = [
            (1, 1),
            (0, 1),
            (2, 1),
            (1, 0),
            (1, 2),
        ]
        before = {(r, c): game.grid[r][c].is_on for r, c in positions if 0 <= r < game.size and 0 <= c < game.size}

        result = game.make_move((1, 1))
        assert result

        for (r, c), state in before.items():
            assert game.grid[r][c].is_on != state

    def test_win_condition(self) -> None:
        """Test win condition detection."""
        game = LightsOutGame(size=3)
        # Set all lights off
        for row in game.grid:
            for bulb in row:
                bulb.is_on = False
                bulb.brightness = 0.0
        assert game.is_game_over()

    def test_brightness_reflects_neighbors(self) -> None:
        """Bulb brightness should respond to neighbours."""
        game = LightsOutGame(size=3)
        for row in game.grid:
            for bulb in row:
                bulb.is_on = False
                bulb.brightness = 0.0

        game.grid[1][1].is_on = True
        game._recalculate_brightness()

        assert game.grid[1][1].brightness == game.on_brightness
        assert game.grid[0][1].brightness > 0

    def test_energy_tracking(self) -> None:
        """Energy tracking should increase with moves."""
        game = LightsOutGame(size=3)
        initial_energy = game.total_energy_kwh
        initial_time = game.total_time_seconds

        assert game.make_move((0, 0))

        assert game.total_energy_kwh > initial_energy
        assert game.total_time_seconds > initial_time

    def test_state_representation_contains_metrics(self) -> None:
        """Structured state representation should expose telemetry."""
        game = LightsOutGame(size=3)
        state = game.get_state_representation()

        assert "brightness" in state
        assert "power_draw_w" in state
        assert "total_energy_kwh" in state


class TestPicross:
    """Test Picross game."""

    def test_initialization(self) -> None:
        """Test game initializes correctly."""
        game = PicrossGame()
        assert game.size == 10
        assert len(game.row_hints) == 10
        assert len(game.col_hints) == 10
        assert all(cell == CellState.UNKNOWN for row in game.grid for cell in row)
        assert game.total_mistakes == 0

    def test_hints_generation(self) -> None:
        """Test hint generation."""
        # Row with no filled cells should have hint [0]
        hints = PicrossGame._get_hints([0, 0, 0])
        assert hints == [0]
        # Row with consecutive filled cells
        hints = PicrossGame._get_hints([1, 1, 0, 1])
        assert hints == [2, 1]

    def test_move_cycle_and_validation(self) -> None:
        """Test filling, toggling and clearing cells."""
        game = PicrossGame()
        assert game.make_move((0, 2, "fill"))
        assert game.grid[0][2] == CellState.FILLED
        assert game.is_cell_correct(0, 2)

        assert game.make_move((0, 2, "toggle"))
        assert game.grid[0][2] == CellState.EMPTY
        assert not game.is_cell_correct(0, 2)
        assert game.total_mistakes == 1
        assert (0, 2) in game.incorrect_cells

        assert game.make_move((0, 2, "clear"))
        assert game.grid[0][2] == CellState.UNKNOWN
        assert (0, 2) not in game.incorrect_cells

    def test_line_progress_tracks_segments(self) -> None:
        """Ensure line progress reflects placed groups."""
        game = PicrossGame()
        game.make_move((0, 2, "fill"))
        game.make_move((0, 3, "fill"))
        progress = game.get_line_progress(0, is_row=True)
        assert list(progress.segments) == [2]
        assert progress.expected_filled == sum(game.row_hints[0])
        assert not progress.is_satisfied

        game.make_move((0, 2, "clear"))
        progress_after_clear = game.get_line_progress(0, is_row=True)
        assert list(progress_after_clear.segments) == [1]

        game.make_move((0, 3, "clear"))
        progress_all_cleared = game.get_line_progress(0, is_row=True)
        assert list(progress_all_cleared.segments) == [0]

    def test_mistake_tracking(self) -> None:
        """Incorrect placements are counted once until cleared."""
        game = PicrossGame()
        assert game.make_move((0, 0, "fill"))  # incorrect cell
        assert (0, 0) in game.incorrect_cells
        assert game.total_mistakes == 1

        # Repeating the same incorrect action should not double count
        assert game.make_move((0, 0, "fill"))
        assert game.total_mistakes == 1

        # Clearing removes the mistake marker
        assert game.make_move((0, 0, "clear"))
        assert (0, 0) not in game.incorrect_cells
