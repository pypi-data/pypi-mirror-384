"""WordBuilder game engine with dictionary validation and configurable tile bags."""

from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Dict, Iterable, List, MutableMapping, Optional

from common.game_engine import GameEngine, GameState

DEFAULT_DICTIONARY_PATH = Path(__file__).with_name("data").joinpath("dictionary.txt")


class DictionaryValidator:
    """Validate candidate words against an authoritative dictionary."""

    def __init__(self, *, words: Optional[Iterable[str]] = None, dictionary_path: Optional[Path] = None) -> None:
        self._words = set()
        if dictionary_path is not None and dictionary_path.exists():
            with dictionary_path.open("r", encoding="utf-8") as handle:
                for line in handle:
                    cleaned = line.strip().upper()
                    if cleaned:
                        self._words.add(cleaned)
        if words is not None:
            for entry in words:
                cleaned = entry.strip().upper()
                if cleaned:
                    self._words.add(cleaned)
        if not self._words:
            raise ValueError("DictionaryValidator requires at least one word entry")

    def is_valid(self, word: str) -> bool:
        """Return ``True`` when the supplied word exists in the dictionary."""

        return word.upper() in self._words


class TileBag:
    """Manage tile distribution using Scrabble-like configuration."""

    def __init__(self, config: MutableMapping[str, int]) -> None:
        tiles: List[str] = []
        for letter, count in config.items():
            if count < 0:
                raise ValueError("Tile counts must be non-negative")
            tiles.extend([letter.upper()] * count)
        if not tiles:
            raise ValueError("Tile bag cannot be empty")
        random.shuffle(tiles)
        self._tiles = tiles

    def draw(self, count: int) -> List[str]:
        """Draw up to ``count`` tiles from the bag."""

        drawn: List[str] = []
        for _ in range(count):
            if not self._tiles:
                break
            drawn.append(self._tiles.pop())
        return drawn

    def remaining(self) -> int:
        """Return the number of tiles still available."""

        return len(self._tiles)

    def to_json(self) -> str:
        """Serialise the remaining distribution for export or analytics."""

        counts: Dict[str, int] = {}
        for tile in self._tiles:
            counts[tile] = counts.get(tile, 0) + 1
        return json.dumps(counts, ensure_ascii=False, sort_keys=True)


DEFAULT_TILE_BAG: Dict[str, int] = {
    "A": 9,
    "B": 2,
    "C": 2,
    "D": 4,
    "E": 12,
    "F": 2,
    "G": 3,
    "H": 2,
    "I": 9,
    "J": 1,
    "K": 1,
    "L": 4,
    "M": 2,
    "N": 6,
    "O": 8,
    "P": 2,
    "Q": 1,
    "R": 6,
    "S": 4,
    "T": 6,
    "U": 4,
    "V": 2,
    "W": 2,
    "X": 1,
    "Y": 2,
    "Z": 1,
}


class WordBuilderGame(GameEngine[str, int]):
    """Tile-based word building game (Scrabble-like)."""

    TILE_VALUES = {
        "A": 1,
        "E": 1,
        "I": 1,
        "O": 1,
        "U": 1,
        "L": 1,
        "N": 1,
        "S": 1,
        "T": 1,
        "R": 1,
        "D": 2,
        "G": 2,
        "B": 3,
        "C": 3,
        "M": 3,
        "P": 3,
        "F": 4,
        "H": 4,
        "V": 4,
        "W": 4,
        "Y": 4,
        "K": 5,
        "J": 8,
        "X": 8,
        "Q": 10,
        "Z": 10,
    }

    def __init__(
        self,
        *,
        dictionary: Optional[DictionaryValidator] = None,
        dictionary_path: Optional[Path] = None,
        tile_bag_config: Optional[Dict[str, int]] = None,
    ) -> None:
        """Initialize game with dictionary validation and configurable tile bag."""

        self.dictionary = dictionary or DictionaryValidator(dictionary_path=dictionary_path or DEFAULT_DICTIONARY_PATH)
        self.tile_bag_config = dict(tile_bag_config or DEFAULT_TILE_BAG)
        self.tile_bag = TileBag(self.tile_bag_config)
        self.reset()

    def reset(self) -> None:
        """Reset game."""

        self.state = GameState.NOT_STARTED
        self.tile_bag = TileBag(self.tile_bag_config)
        self.hand = self._draw_tiles(7)
        self.score = 0
        self.turns = 0

    def _draw_tiles(self, count: int) -> List[str]:
        """Draw random tiles using the configured bag."""

        return self.tile_bag.draw(count)

    def is_game_over(self) -> bool:
        """Check if game over."""

        return self.turns >= 10 or (self.tile_bag.remaining() == 0 and not self.hand)

    def get_current_player(self) -> int:
        """Get current player."""

        return 0

    def get_valid_moves(self) -> List[str]:
        """Get valid moves (any dictionary word)."""

        return ["dictionary_word"]

    def make_move(self, move: str) -> bool:
        """Play a word."""

        if self.state == GameState.NOT_STARTED:
            self.state = GameState.IN_PROGRESS

        if self.is_game_over():
            return False

        word = move.upper().strip()
        if not word or not self.dictionary.is_valid(word):
            return False

        hand_copy = self.hand.copy()
        for letter in word:
            if letter in hand_copy:
                hand_copy.remove(letter)
            else:
                return False

        points = sum(self.TILE_VALUES.get(letter, 0) for letter in word)
        self.score += points

        for letter in word:
            self.hand.remove(letter)
        self.hand.extend(self._draw_tiles(len(word)))

        self.turns += 1

        if self.is_game_over():
            self.state = GameState.FINISHED

        return True

    def get_winner(self) -> int | None:
        """Get winner."""

        return 0 if self.is_game_over() else None

    def get_game_state(self) -> GameState:
        """Get current game state.

        Returns:
            Current state of the game
        """

        return self.state
