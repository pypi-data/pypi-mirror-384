"""Additional regression tests for paper-based games."""

from __future__ import annotations

import random

# Ensure deterministic SudokuGenerator seeding
from common.game_engine import GameState
from paper_games.boggle import BoggleGame, BoggleMove
from paper_games.checkers import CheckersAI, CheckersGame, CheckersMove, CheckersPiece
from paper_games.chess import ChessGame
from paper_games.connect_four import ConnectFourGame, ConnectFourMove
from paper_games.mancala import MancalaAI, MancalaGame, MancalaMove
from paper_games.mastermind import MastermindGame, MastermindMove
from paper_games.othello import OthelloAI, OthelloGame, OthelloMove
from paper_games.snakes_and_ladders import SnakesAndLaddersGame, SnakesAndLaddersMove
from paper_games.sudoku import SudokuGenerator
from paper_games.twenty_questions import TwentyQuestionsGame
from paper_games.yahtzee import YahtzeeCategory, YahtzeeGame


def test_connect_four_vertical_win() -> None:
    game = ConnectFourGame()
    for _ in range(3):
        assert game.make_move(ConnectFourMove(column=0))
        assert game.make_move(ConnectFourMove(column=1))
    assert game.make_move(ConnectFourMove(column=0))
    assert game.is_game_over()
    assert game.get_winner() == 1


def test_checkers_jump_and_promotion() -> None:
    game = CheckersGame()
    game._board = [[None for _ in range(game.board_size)] for _ in range(game.board_size)]
    game._board[2][1] = CheckersPiece("black")
    game._board[3][2] = CheckersPiece("white")
    game._board[5][4] = CheckersPiece("white")
    game._current_player = "black"
    game._state = GameState.IN_PROGRESS
    moves = game.get_valid_moves()
    assert len(moves) == 1
    move = moves[0]
    assert move.is_jump
    assert game.make_move(move)
    landing_row, landing_col = move.path[-1]
    landing_piece = game._board[landing_row][landing_col]
    assert landing_piece is not None
    assert landing_piece.color == "black"
    promotion_game = CheckersGame()
    promotion_game._board = [[None for _ in range(promotion_game.board_size)] for _ in range(promotion_game.board_size)]
    promotion_game._board[6][1] = CheckersPiece("black")
    promotion_game._current_player = "black"
    promotion_game._state = GameState.IN_PROGRESS
    promotion_move = CheckersMove(path=((6, 1), (7, 0)))
    assert promotion_game.make_move(promotion_move)
    promoted_piece = promotion_game._board[7][0]
    assert promoted_piece is not None and promoted_piece.king


def test_checkers_ai_prefers_capture() -> None:
    game = CheckersGame()
    game._board = [[None for _ in range(game.board_size)] for _ in range(game.board_size)]
    game._board[2][1] = CheckersPiece("black")
    game._board[3][2] = CheckersPiece("white")
    game._board[5][4] = CheckersPiece("white")
    game._current_player = "black"
    ai = CheckersAI(depth=2)
    move = ai.choose_move(game)
    assert move.is_jump


def test_mancala_capture_and_extra_turn() -> None:
    game = MancalaGame()
    assert game.make_move(MancalaMove(pit_index=2))
    assert game.get_current_player() == 0
    game._board = [0] * len(game._board)
    game._board[1] = 2
    game._board[9] = 4
    game._board[7] = 1
    game._current_player = 0
    assert game.make_move(MancalaMove(pit_index=1))
    assert game._board[game._store_index(0)] == 5


def test_mancala_ai_returns_valid_move() -> None:
    game = MancalaGame()
    ai = MancalaAI(depth=2)
    move = ai.choose_move(game)
    valid_pits = {valid_move.pit_index for valid_move in game.get_valid_moves()}
    assert move.pit_index in valid_pits


def test_othello_flipping_and_ai() -> None:
    game = OthelloGame()
    move = OthelloMove(row=2, column=3)
    assert move in game.get_valid_moves()
    assert game.make_move(move)
    assert game.get_state_representation()[3][3] == "black"
    ai = OthelloAI(depth=2)
    ai_move = ai.choose_move(game)
    assert ai_move in game.get_valid_moves()


def test_sudoku_generator_and_hint() -> None:
    generator = SudokuGenerator(rng=random.Random(12345))
    puzzle = generator.generate("medium")
    zeros = sum(cell == 0 for row in puzzle.starting_board for cell in row)
    assert zeros >= 40
    hint = puzzle.get_hint()
    assert hint is not None
    row, column, value = hint
    assert puzzle.solution[row][column] == value
    puzzle.get_hint(apply=True)
    assert puzzle.board[row][column] == value


def test_snakes_and_ladders_movement() -> None:
    game = SnakesAndLaddersGame(num_players=2)
    assert game.get_player_position(0) == 0
    assert game.get_player_position(1) == 0

    # Make a move
    move = SnakesAndLaddersMove(dice_roll=3)
    assert game.make_move(move)
    assert game.get_player_position(0) == 3

    # Next player's turn
    assert game.get_current_player() == 1


def test_yahtzee_scoring() -> None:
    game = YahtzeeGame(num_players=1)

    # Test scoring with specific dice
    game._dice = [1, 1, 1, 2, 3]
    score = game.calculate_score(YahtzeeCategory.ONES)
    assert score == 3  # Three ones

    score = game.calculate_score(YahtzeeCategory.THREE_OF_A_KIND)
    assert score == 8  # Sum of all dice

    # Test Yahtzee (all same)
    game._dice = [5, 5, 5, 5, 5]
    score = game.calculate_score(YahtzeeCategory.YAHTZEE)
    assert score == 50


def test_mastermind_feedback() -> None:
    game = MastermindGame(code_length=4)
    # Set a known secret code for testing
    game._secret_code = [0, 1, 2, 3]  # Red, Blue, Green, Yellow

    # Test exact match
    move = MastermindMove(guess=(0, 1, 2, 3))
    assert game.make_move(move)
    black, white = game.get_feedback()[0]
    assert black == 4  # All correct
    assert white == 0


def test_boggle_word_validation() -> None:
    game = BoggleGame(size=4)
    # Set a specific grid for testing
    game._grid = [
        ["C", "A", "T", "S"],
        ["O", "R", "E", "D"],
        ["D", "O", "G", "S"],
        ["R", "A", "T", "S"],
    ]

    # "CAT" should be findable
    # Note: may not be in simple dictionary, so just test structure
    assert game.is_word_in_grid("CAT")
    assert BoggleMove(word="cat").word.upper() == "CAT"


def test_twenty_questions_basic() -> None:
    game = TwentyQuestionsGame()
    assert not game.is_game_over()
    assert game.get_questions_remaining() == 20

    game.ask_question("Is it alive?", True)
    assert game.get_questions_remaining() == 19


def test_chess_basic_board() -> None:
    game = ChessGame()
    # Board should be initialized
    assert len(game._board) == 8
    assert len(game._board[0]) == 8
    # Should have some pieces
    assert game._board[1][0] == "wp"  # White pawn
