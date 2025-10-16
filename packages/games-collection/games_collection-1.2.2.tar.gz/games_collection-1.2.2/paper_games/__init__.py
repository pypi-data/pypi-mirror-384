"""
A collection of interactive implementations of classic paper-and-pencil games.

This package provides classes for various games that can be played in the terminal.
Each game is contained in its own submodule.
"""

# Import the main game classes from their respective submodules.
from .backgammon import BackgammonGame
from .battleship import BattleshipGame
from .boggle import BoggleGame
from .checkers import CheckersGame
from .chess import ChessGame
from .connect_four import ConnectFourGame
from .dots_and_boxes import DotsAndBoxes
from .four_square_writing import FourSquareWritingGame
from .hangman import HangmanGame
from .mancala import MancalaGame
from .mastermind import MastermindGame
from .nim import NimGame
from .othello import OthelloGame
from .pentago import PentagoGame
from .snakes_and_ladders import SnakesAndLaddersGame
from .sprouts import SproutsGame
from .sudoku import SudokuGenerator, SudokuPuzzle
from .tic_tac_toe import TicTacToeGame
from .twenty_questions import TwentyQuestionsGame
from .unscramble import UnscrambleGame
from .yahtzee import YahtzeeGame

# The __all__ variable defines the public API of the package.
# When a user writes `from paper_games import *`, only these names will be imported.
__all__ = [
    "BackgammonGame",
    "BattleshipGame",
    "BoggleGame",
    "CheckersGame",
    "ChessGame",
    "ConnectFourGame",
    "DotsAndBoxes",
    "FourSquareWritingGame",
    "HangmanGame",
    "MancalaGame",
    "MastermindGame",
    "NimGame",
    "OthelloGame",
    "PentagoGame",
    "SnakesAndLaddersGame",
    "SproutsGame",
    "SudokuGenerator",
    "SudokuPuzzle",
    "TicTacToeGame",
    "TwentyQuestionsGame",
    "UnscrambleGame",
    "YahtzeeGame",
]
