# Checkers

A complete and well-documented implementation of the classic game of Checkers, featuring a challenging AI opponent and a clean command-line interface.

## How to Play
The goal of Checkers is to capture all of your opponent's pieces or block them from making any legal moves.

1.  **Start the Game**: Run the game from your terminal:
    ```bash
    python -m paper_games.checkers
    ```
2.  **The Board**: The game is played on an 8x8 board. Pieces are placed on the dark squares.
3.  **Making Moves**:
    *   Pieces can only move diagonally forward.
    *   To make a move, enter the coordinates of the piece you want to move and the destination square, separated by a hyphen (e.g., `2,1-3,0`).
    *   If a jump is available, you **must** take it.
4.  **Capturing Pieces**:
    *   You can capture an opponent's piece by jumping over it to an empty square.
    *   Multiple jumps can be chained together in a single turn.
5.  **Kings**:
    *   When a piece reaches the farthest row from its starting position, it is "kinged" and can move both forwards and backward.
    *   Kings are represented by uppercase letters (`B` for black, `W` for white).

## Features
*   **Full Ruleset**: Implements all standard Checkers rules, including forced captures and multi-jump moves.
*   **Challenging AI**: The AI opponent is powered by the minimax algorithm with alpha-beta pruning, providing a formidable challenge.
*   **Interactive CLI**: A clean and simple command-line interface for playing the game.
*   **Clear Board Representation**: The board is displayed in the terminal with clear symbols for pieces and kings.

## Module Structure
The Checkers game is implemented in a single, well-documented module:
*   `checkers.py`: Contains the core game engine (`CheckersGame`), the AI (`CheckersAI`), and the command-line interface (`CheckersCLI`).