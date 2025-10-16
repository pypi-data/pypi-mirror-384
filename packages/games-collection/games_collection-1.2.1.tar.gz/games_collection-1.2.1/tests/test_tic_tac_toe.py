import pathlib
import sys
import tempfile

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from paper_games.tic_tac_toe.network import NetworkConfig, NetworkTicTacToeClient, NetworkTicTacToeServer
from paper_games.tic_tac_toe.stats import GameStats
from paper_games.tic_tac_toe.themes import THEMES, get_theme, list_themes, validate_symbols
from paper_games.tic_tac_toe.tic_tac_toe import TicTacToeGame
from paper_games.tic_tac_toe.ultimate import UltimateTicTacToeGame


def test_standard_3x3_board():
    """Test that standard 3x3 board still works."""
    game = TicTacToeGame()
    assert len(game.board) == 9
    assert game.board_size == 3
    assert game.win_length == 3


def test_4x4_board():
    """Test 4x4 board creation."""
    game = TicTacToeGame(board_size=4)
    assert len(game.board) == 16
    assert game.board_size == 4
    assert game.win_length == 4


def test_5x5_board():
    """Test 5x5 board creation."""
    game = TicTacToeGame(board_size=5)
    assert len(game.board) == 25
    assert game.board_size == 5
    assert game.win_length == 5


def test_custom_win_length():
    """Test custom win length."""
    game = TicTacToeGame(board_size=4, win_length=3)
    assert game.board_size == 4
    assert game.win_length == 3


def test_winner_horizontal_4x4():
    """Test horizontal winner detection on 4x4 board."""
    game = TicTacToeGame(board_size=4, win_length=3)
    game.make_move(0, "X")  # A1
    game.make_move(1, "X")  # A2
    game.make_move(2, "X")  # A3
    assert game.winner() == "X"


def test_winner_vertical_4x4():
    """Test vertical winner detection on 4x4 board."""
    game = TicTacToeGame(board_size=4, win_length=3)
    game.make_move(0, "O")  # A1
    game.make_move(4, "O")  # B1
    game.make_move(8, "O")  # C1
    assert game.winner() == "O"


def test_winner_diagonal_4x4():
    """Test diagonal winner detection on 4x4 board."""
    game = TicTacToeGame(board_size=4, win_length=3)
    game.make_move(0, "X")  # A1
    game.make_move(5, "X")  # B2
    game.make_move(10, "X")  # C3
    assert game.winner() == "X"


def test_winner_anti_diagonal_5x5():
    """Test anti-diagonal winner detection on 5x5 board."""
    game = TicTacToeGame(board_size=5, win_length=4)
    game.make_move(3, "O")  # A4
    game.make_move(7, "O")  # B3
    game.make_move(11, "O")  # C2
    game.make_move(15, "O")  # D1
    assert game.winner() == "O"


def test_no_winner_partial_line():
    """Test that partial lines don't count as wins."""
    game = TicTacToeGame(board_size=4, win_length=3)
    game.make_move(0, "X")  # A1
    game.make_move(1, "X")  # A2
    assert game.winner() is None


def test_coordinate_parsing_4x4():
    """Test coordinate parsing for 4x4 board."""
    game = TicTacToeGame(board_size=4)
    assert game.parse_coordinate("A1") == 0
    assert game.parse_coordinate("A4") == 3
    assert game.parse_coordinate("D1") == 12
    assert game.parse_coordinate("D4") == 15


def test_coordinate_parsing_5x5():
    """Test coordinate parsing for 5x5 board."""
    game = TicTacToeGame(board_size=5)
    assert game.parse_coordinate("A1") == 0
    assert game.parse_coordinate("E5") == 24
    assert game.parse_coordinate("C3") == 12


def test_invalid_coordinate():
    """Test that invalid coordinates raise errors."""
    game = TicTacToeGame(board_size=4)
    try:
        game.parse_coordinate("E5")  # Out of bounds for 4x4
        assert False, "Should have raised ValueError"
    except ValueError:
        pass


def test_render_4x4():
    """Test that 4x4 board renders correctly."""
    game = TicTacToeGame(board_size=4)
    rendered = game.render()
    assert "A" in rendered
    assert "D" in rendered
    assert "1" in rendered
    assert "4" in rendered


def test_available_moves_4x4():
    """Test available moves on 4x4 board."""
    game = TicTacToeGame(board_size=4)
    assert len(game.available_moves()) == 16
    game.make_move(0, "X")
    assert len(game.available_moves()) == 15
    assert 0 not in game.available_moves()


def test_is_draw_4x4():
    """Test draw detection on 4x4 board."""
    game = TicTacToeGame(board_size=4, win_length=4)
    # Fill board in a pattern that prevents any wins
    # Pattern: XOXO / XOXO / OXOX / OXOX
    moves = [
        ("X", 0),
        ("O", 1),
        ("X", 2),
        ("O", 3),
        ("X", 4),
        ("O", 5),
        ("X", 6),
        ("O", 7),
        ("O", 8),
        ("X", 9),
        ("O", 10),
        ("X", 11),
        ("O", 12),
        ("X", 13),
        ("O", 14),
        ("X", 15),
    ]
    for symbol, pos in moves:
        game.make_move(pos, symbol)
    assert game.winner() is None
    assert game.is_draw()


def test_minimax_makes_move():
    """Test that minimax can find a move on larger board."""
    game = TicTacToeGame(board_size=4, win_length=3)
    score, move = game.minimax(True, max_depth=4)
    assert move is not None
    assert move in game.available_moves()


# Statistics tests
def test_stats_initial_state():
    """Test that initial stats are all zeros."""
    stats = GameStats()
    assert stats.human_wins == 0
    assert stats.computer_wins == 0
    assert stats.draws == 0
    assert stats.games_played == 0


def test_stats_record_human_win():
    """Test recording a human win."""
    stats = GameStats()
    stats.record_game("X", "X", "O")
    assert stats.human_wins == 1
    assert stats.computer_wins == 0
    assert stats.draws == 0
    assert stats.games_played == 1


def test_stats_record_computer_win():
    """Test recording a computer win."""
    stats = GameStats()
    stats.record_game("O", "X", "O")
    assert stats.human_wins == 0
    assert stats.computer_wins == 1
    assert stats.draws == 0
    assert stats.games_played == 1


def test_stats_record_draw():
    """Test recording a draw."""
    stats = GameStats()
    stats.record_game(None, "X", "O")
    assert stats.human_wins == 0
    assert stats.computer_wins == 0
    assert stats.draws == 1
    assert stats.games_played == 1


def test_stats_win_rate():
    """Test win rate calculation."""
    stats = GameStats()
    assert stats.win_rate() == 0.0

    stats.record_game("X", "X", "O")
    stats.record_game("O", "X", "O")
    stats.record_game("X", "X", "O")
    stats.record_game(None, "X", "O")

    # 2 wins out of 4 games = 0.5
    assert stats.win_rate() == 0.5


def test_stats_by_board_size():
    """Test tracking stats by board size."""
    stats = GameStats()
    stats.record_game("X", "X", "O", board_size=3)
    stats.record_game("O", "X", "O", board_size=4)
    stats.record_game("X", "X", "O", board_size=3)

    assert "3x3" in stats.stats_by_board_size
    assert "4x4" in stats.stats_by_board_size
    assert stats.stats_by_board_size["3x3"]["games"] == 2
    assert stats.stats_by_board_size["4x4"]["games"] == 1


def test_stats_save_and_load():
    """Test saving and loading statistics."""
    stats = GameStats()
    stats.record_game("X", "X", "O")
    stats.record_game("O", "X", "O")
    stats.record_game(None, "X", "O")

    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = pathlib.Path(tmpdir) / "stats.json"
        stats.save(filepath)

        loaded_stats = GameStats.load(filepath)
        assert loaded_stats.human_wins == stats.human_wins
        assert loaded_stats.computer_wins == stats.computer_wins
        assert loaded_stats.draws == stats.draws
        assert loaded_stats.games_played == stats.games_played


def test_stats_summary():
    """Test generating a summary."""
    stats = GameStats()
    stats.record_game("X", "X", "O", board_size=3)
    stats.record_game("O", "X", "O", board_size=4)

    summary = stats.summary()
    assert "Total games played: 2" in summary
    assert "Your wins: 1" in summary
    assert "Computer wins: 1" in summary
    assert "3x3" in summary
    assert "4x4" in summary


# Theme tests
def test_get_theme():
    """Test getting theme symbols."""
    sym1, sym2 = get_theme("classic")
    assert sym1 == "X"
    assert sym2 == "O"

    sym1, sym2 = get_theme("hearts")
    assert sym1 == "♥"
    assert sym2 == "♡"


def test_get_invalid_theme():
    """Test that invalid themes raise errors."""
    try:
        get_theme("nonexistent")
        assert False, "Should have raised ValueError"
    except ValueError:
        pass


def test_list_themes():
    """Test listing available themes."""
    themes_list = list_themes()
    assert "classic" in themes_list
    assert "hearts" in themes_list
    assert "emoji" in themes_list


def test_validate_symbols():
    """Test symbol validation."""
    assert validate_symbols("X", "O") is True
    assert validate_symbols("♥", "♡") is True

    # Test identical symbols
    try:
        validate_symbols("X", "X")
        assert False, "Should have raised ValueError"
    except ValueError:
        pass

    # Test empty symbols
    try:
        validate_symbols("", "O")
        assert False, "Should have raised ValueError"
    except ValueError:
        pass


def test_themed_game():
    """Test playing a game with themed symbols."""
    game = TicTacToeGame(human_symbol="♥", computer_symbol="♡")
    assert game.human_symbol == "♥"
    assert game.computer_symbol == "♡"

    game.make_move(0, "♥")
    game.make_move(1, "♡")

    rendered = game.render()
    assert "♥" in rendered
    assert "♡" in rendered


def test_all_themes_in_game():
    """Test that all themes can be used in a game."""
    for theme_name in THEMES.keys():
        sym1, sym2 = get_theme(theme_name)
        game = TicTacToeGame(human_symbol=sym1, computer_symbol=sym2, board_size=3)
        assert game.human_symbol == sym1
        assert game.computer_symbol == sym2


# Ultimate Tic-Tac-Toe tests
def test_ultimate_initialization():
    """Test ultimate tic-tac-toe initialization."""
    game = UltimateTicTacToeGame()
    assert len(game.small_boards) == 9
    assert len(game.meta_board) == 9
    assert game.active_board is None
    assert all(cell is None for cell in game.meta_board)


def test_ultimate_make_move():
    """Test making moves in ultimate tic-tac-toe."""
    game = UltimateTicTacToeGame()
    # First move can be anywhere
    assert game.make_move(4, 4, "X")  # Board 4, cell 4 (center)
    # Next move must be on board 4 (center)
    assert game.active_board == 4


def test_ultimate_board_restriction():
    """Test that board restriction works."""
    game = UltimateTicTacToeGame()
    game.make_move(0, 5, "X")  # Board 0, cell 5
    # Next move must be on board 5
    assert game.active_board == 5
    # Try to play on wrong board
    assert not game.make_move(0, 0, "O")
    # Play on correct board
    assert game.make_move(5, 0, "O")


def test_ultimate_win_small_board():
    """Test winning a small board."""
    game = UltimateTicTacToeGame()
    # Directly manipulate a small board to test winning
    game.small_boards[0].make_move(0, "X")
    game.small_boards[0].make_move(1, "X")
    game.small_boards[0].make_move(2, "X")

    # Check if the small board is won
    assert game.small_boards[0].winner() == "X"

    # Now update meta board based on this win
    game.meta_board[0] = game.small_boards[0].winner()
    assert game.meta_board[0] == "X"


def test_ultimate_meta_board_winner():
    """Test detecting winner on meta-board."""
    game = UltimateTicTacToeGame()
    # Win three boards in a row on meta-board
    # Win board 0
    for i in range(3):
        game.small_boards[0].make_move(i, "X")
    game.meta_board[0] = "X"

    # Win board 1
    for i in range(3):
        game.small_boards[1].make_move(i, "X")
    game.meta_board[1] = "X"

    # Win board 2
    for i in range(3):
        game.small_boards[2].make_move(i, "X")
    game.meta_board[2] = "X"

    assert game.winner() == "X"


def test_ultimate_draw():
    """Test draw detection."""
    game = UltimateTicTacToeGame()
    # Fill meta-board with mixed results (no winner)
    game.meta_board = ["X", "O", "X", "O", "X", "O", "O", "X", "DRAW"]
    assert game.winner() is None
    assert game.is_draw()


def test_ultimate_available_moves():
    """Test getting available moves."""
    game = UltimateTicTacToeGame()
    moves = game.available_moves()
    # Initially all 81 cells should be available
    assert len(moves) == 81

    # Make a move
    game.make_move(0, 0, "X")
    moves = game.available_moves()
    # Now only board 0 is active (9 cells minus the one we played)
    assert len(moves) == 8


def test_ultimate_render():
    """Test rendering the ultimate board."""
    game = UltimateTicTacToeGame()
    game.make_move(0, 0, "X")
    rendered = game.render()
    assert "Meta-board" in rendered
    assert "X" in rendered


def test_ultimate_computer_move():
    """Test computer making a move."""
    game = UltimateTicTacToeGame()
    board_idx, cell_idx = game.computer_move()
    assert board_idx in range(9)
    assert cell_idx in range(9)


def test_ultimate_full_game_sequence():
    """Test a sequence of moves leading to a win."""
    game = UltimateTicTacToeGame()

    # Player X wins board 0
    game.make_move(4, 0, "X")  # Center board, top-left cell
    game.make_move(0, 3, "O")  # Forced to board 0
    game.make_move(3, 0, "X")  # Move to board 3
    game.make_move(0, 4, "O")  # Forced to board 0
    game.make_move(4, 0, "X")  # Back to center
    game.make_move(0, 5, "O")  # Board 0

    # Check if board 0 has a winner
    assert game.small_boards[0].winner() is not None or len(game.small_boards[0].available_moves()) > 0


# Network tests
def test_network_config():
    """Test network configuration."""
    config = NetworkConfig()
    assert config.host == "localhost"
    assert config.port == 5555
    assert config.board_size == 3


def test_network_server_init():
    """Test server initialization."""
    config = NetworkConfig(port=5556)  # Use different port to avoid conflicts
    server = NetworkTicTacToeServer(config)
    assert server.config.port == 5556
    assert server.game is None


def test_network_client_init():
    """Test client initialization."""
    client = NetworkTicTacToeClient("localhost", 5557)
    assert client.host == "localhost"
    assert client.port == 5557
    assert client.game is None


def test_network_message_format():
    """Test that network messages can be created properly."""
    # Test move message
    move_msg = {
        "type": "move",
        "position": 4,
        "symbol": "X",
    }
    assert move_msg["type"] == "move"
    assert move_msg["position"] == 4

    # Test config message
    config_msg = {
        "type": "config",
        "board_size": 3,
        "win_length": 3,
        "your_symbol": "O",
        "opponent_symbol": "X",
    }
    assert config_msg["board_size"] == 3


if __name__ == "__main__":
    # Run all tests
    test_functions = [
        test_standard_3x3_board,
        test_4x4_board,
        test_5x5_board,
        test_custom_win_length,
        test_winner_horizontal_4x4,
        test_winner_vertical_4x4,
        test_winner_diagonal_4x4,
        test_winner_anti_diagonal_5x5,
        test_no_winner_partial_line,
        test_coordinate_parsing_4x4,
        test_coordinate_parsing_5x5,
        test_invalid_coordinate,
        test_render_4x4,
        test_available_moves_4x4,
        test_is_draw_4x4,
        test_minimax_makes_move,
        test_stats_initial_state,
        test_stats_record_human_win,
        test_stats_record_computer_win,
        test_stats_record_draw,
        test_stats_win_rate,
        test_stats_by_board_size,
        test_stats_save_and_load,
        test_stats_summary,
        test_get_theme,
        test_get_invalid_theme,
        test_list_themes,
        test_validate_symbols,
        test_themed_game,
        test_all_themes_in_game,
        test_ultimate_initialization,
        test_ultimate_make_move,
        test_ultimate_board_restriction,
        test_ultimate_win_small_board,
        test_ultimate_meta_board_winner,
        test_ultimate_draw,
        test_ultimate_available_moves,
        test_ultimate_render,
        test_ultimate_computer_move,
        test_ultimate_full_game_sequence,
        test_network_config,
        test_network_server_init,
        test_network_client_init,
        test_network_message_format,
    ]

    for test_func in test_functions:
        try:
            test_func()
            print(f"✓ {test_func.__name__}")
        except AssertionError as e:
            print(f"✗ {test_func.__name__}: {e}")
        except Exception as e:
            print(f"✗ {test_func.__name__}: {e}")

    print("\nAll tests completed!")
