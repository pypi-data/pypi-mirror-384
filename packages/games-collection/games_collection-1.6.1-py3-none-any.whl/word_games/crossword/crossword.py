"""Crossword game engine with import/export pack utilities."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

from common.game_engine import GameEngine, GameState


@dataclass(frozen=True)
class CrosswordClue:
    """Single crossword clue definition."""

    row: int
    column: int
    direction: str
    answer: str
    clue: str

    def to_dict(self) -> Dict[str, str | int]:
        """Serialise the clue for JSON export."""

        return {
            "row": self.row,
            "column": self.column,
            "direction": self.direction,
            "answer": self.answer,
            "clue": self.clue,
        }

    @classmethod
    def from_dict(cls, payload: Dict[str, object]) -> "CrosswordClue":
        """Construct a ``CrosswordClue`` from dictionary data."""

        return cls(
            row=int(payload["row"]),
            column=int(payload["column"]),
            direction=str(payload["direction"]),
            answer=str(payload["answer"]),
            clue=str(payload["clue"]),
        )


class CrosswordPackManager:
    """Utility helpers for loading and exporting crossword packs."""

    @staticmethod
    def load(path: Path) -> Dict[int, CrosswordClue]:
        """Load a crossword pack from disk."""

        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        clues: Dict[int, CrosswordClue] = {}
        for item in payload:
            identifier = int(item["id"])
            clues[identifier] = CrosswordClue.from_dict(item)
        return clues

    @staticmethod
    def dump(clues: Dict[int, CrosswordClue], path: Path) -> None:
        """Persist a crossword pack to disk."""

        path.parent.mkdir(parents=True, exist_ok=True)
        payload = []
        for identifier, clue in clues.items():
            entry = clue.to_dict()
            entry["id"] = identifier
            payload.append(entry)
        with path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)


class CrosswordGame(GameEngine[Tuple[int, str], int]):
    """Simple crossword puzzle game."""

    DEFAULT_PUZZLE: Dict[int, CrosswordClue] = {
        1: CrosswordClue(0, 0, "across", "CAT", "Feline pet"),
        2: CrosswordClue(0, 0, "down", "CAN", "Container"),
        3: CrosswordClue(2, 0, "across", "NET", "Fishing tool"),
    }

    def __init__(self, clues: Dict[int, CrosswordClue] | None = None) -> None:
        """Initialize game."""

        self.clues = dict(clues or self.DEFAULT_PUZZLE)
        self.reset()

    def reset(self) -> None:
        """Reset game."""
        self.state = GameState.NOT_STARTED
        self.grid: Dict[Tuple[int, int], str] = {}
        self.solved: set[int] = set()

    def is_game_over(self) -> bool:
        """Check if game over."""
        return len(self.solved) == len(self.clues)

    def get_current_player(self) -> int:
        """Get current player."""
        return 0

    def get_valid_moves(self) -> List[Tuple[int, str]]:
        """Get valid moves: (clue_id, word_guess)."""
        unsolved = [cid for cid in self.clues if cid not in self.solved]
        return [(cid, "") for cid in unsolved]

    def make_move(self, move: Tuple[int, str]) -> bool:
        """Submit answer for a clue."""
        if self.state == GameState.NOT_STARTED:
            self.state = GameState.IN_PROGRESS

        clue_id, guess = move
        if clue_id not in self.clues or clue_id in self.solved:
            return False

        answer = self.clues[clue_id].answer
        if guess.upper() == answer.upper():
            self.solved.add(clue_id)
            if self.is_game_over():
                self.state = GameState.FINISHED
            return True
        return False

    def get_winner(self) -> int | None:
        """Get winner."""
        return 0 if self.is_game_over() else None

    def get_clues(self) -> Dict[int, CrosswordClue]:
        """Expose the currently loaded clues."""

        return dict(self.clues)

    def load_pack(self, clues: Dict[int, CrosswordClue]) -> None:
        """Load a new pack into the game and reset the state."""

        self.clues = dict(clues)
        self.reset()

    def export_pack(self, path: Path) -> None:
        """Export the current puzzle to disk."""

        CrosswordPackManager.dump(self.clues, path)

    def get_game_state(self) -> GameState:
        """Get current game state.

        Returns:
            Current state of the game
        """
        return self.state
