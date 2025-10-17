"""Four Square Writing Method - educational template.

This is an educational tool, not a game. It provides a template for
the four-square writing method used to teach essay structure.
"""

from __future__ import annotations

from typing import Dict, List, Optional

from common.game_engine import GameEngine, GameState


class FourSquareWritingGame(GameEngine[str, int]):
    def __init__(self) -> None:
        self._quadrants: Dict[str, str] = {
            "center": "",  # Main idea
            "top_left": "",  # Reason 1
            "top_right": "",  # Reason 2
            "bottom_left": "",  # Reason 3
            "bottom_right": "",  # Conclusion
        }
        self._state = GameState.IN_PROGRESS

    def reset(self) -> None:
        self._quadrants = {k: "" for k in self._quadrants}
        self._state = GameState.IN_PROGRESS

    def is_game_over(self) -> bool:
        return all(v != "" for v in self._quadrants.values())

    def get_current_player(self) -> int:
        return 0

    def get_valid_moves(self) -> List[str]:
        return [k for k, v in self._quadrants.items() if v == ""]

    def make_move(self, move: str) -> bool:
        # Move is just filling in a quadrant
        return True

    def set_quadrant(self, quadrant: str, text: str) -> None:
        if quadrant in self._quadrants:
            self._quadrants[quadrant] = text

    def get_quadrant(self, quadrant: str) -> str:
        return self._quadrants.get(quadrant, "")

    def get_winner(self) -> Optional[int]:
        return 0 if self.is_game_over() else None

    def get_game_state(self) -> GameState:
        return GameState.FINISHED if self.is_game_over() else GameState.IN_PROGRESS

    def get_state_representation(self) -> dict:
        return self._quadrants.copy()


class FourSquareWritingCLI:
    def __init__(self) -> None:
        self.game = FourSquareWritingGame()

    def run(self) -> None:
        print("Four Square Writing Method")
        print("=" * 60)
        print("This educational template helps structure your essay.")
        print()
        print("Fill in each quadrant:")
        print("1. Center: Main idea/thesis")
        print("2. Top Left: Reason/Point 1")
        print("3. Top Right: Reason/Point 2")
        print("4. Bottom Left: Reason/Point 3")
        print("5. Bottom Right: Conclusion")
        print()

        quadrants = ["center", "top_left", "top_right", "bottom_left", "bottom_right"]
        labels = ["Main Idea", "Reason 1", "Reason 2", "Reason 3", "Conclusion"]

        for quad, label in zip(quadrants, labels):
            text = input(f"{label}: ")
            self.game.set_quadrant(quad, text)

        print("\n" + "=" * 60)
        print("Your Four Square Writing Template:")
        print("=" * 60)
        print(f"Center (Main Idea): {self.game.get_quadrant('center')}")
        print(f"Top Left (Reason 1): {self.game.get_quadrant('top_left')}")
        print(f"Top Right (Reason 2): {self.game.get_quadrant('top_right')}")
        print(f"Bottom Left (Reason 3): {self.game.get_quadrant('bottom_left')}")
        print(f"Bottom Right (Conclusion): {self.game.get_quadrant('bottom_right')}")
        print("=" * 60)
