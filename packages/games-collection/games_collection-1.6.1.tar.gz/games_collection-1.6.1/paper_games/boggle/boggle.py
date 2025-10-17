"""Boggle game engine, dictionary integration, and command-line interface.

This module provides a complete implementation of the Boggle game, including:
- A `BoggleGame` engine that adheres to the official rules, supporting
  various board sizes, dice layouts, and timed rounds.
- Integration with a `BoggleDictionary` for word validation.
- A `BoggleCLI` for playing the game in a terminal.

The game engine manages the board generation, word submission, scoring,
and multiplayer logic, while the CLI provides a user-friendly interface
for interacting with the game.
"""

from __future__ import annotations

import random
import time
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Set, Tuple

from common.game_engine import GameEngine, GameState

from .dictionary import BoggleDictionary


@dataclass(frozen=True)
class BoggleMove:
    """Represents a submitted word in a Boggle game.

    This dataclass is used to encapsulate a player's move, which consists of
    the word they are submitting and their player ID.

    Args:
        word (str): The candidate word submitted by the player.
        player_id (int): The zero-based index of the submitting player.
    """

    word: str
    player_id: int = 0


@dataclass
class SubmissionFeedback:
    """Provides feedback on the outcome of a word submission.

    This class is used to communicate the result of a word submission back
    to the user interface, indicating whether the word was accepted, how many
    points it was worth, and why it might have been rejected.

    Attributes:
        word (str): The word that was evaluated.
        player_id (int): The index of the submitting player.
        accepted (bool): True if the submission was accepted as a valid word.
        points (int): The number of points awarded for the submission.
        reason (Optional[str]): An explanation for rejected or zero-point submissions.
    """

    word: str
    player_id: int
    accepted: bool
    points: int
    reason: Optional[str] = None


class BoggleGame(GameEngine[BoggleMove, int]):
    """An engine that implements the official rules of Boggle.

    This engine manages the entire game lifecycle, including board generation
    using official dice layouts, word validation against a dictionary,
    scoring, and handling multiplayer interactions like duplicate word detection.
    """

    # Scoring table based on official Boggle rules.
    SCORE_TABLE = {3: 1, 4: 1, 5: 2, 6: 3, 7: 5}
    # Official dice layouts for 4x4 and 5x5 Boggle.
    DICE_LAYOUTS = {
        4: [
            "AAEEGN",
            "ABBJOO",
            "ACHOPS",
            "AFFKPS",
            "AOOTTW",
            "CIMOTU",
            "DEILRX",
            "DELRVY",
            "DISTTY",
            "EEGHNW",
            "EEINSU",
            "EHRTVW",
            "EIOSST",
            "ELRTTY",
            "HIMNQU",
            "HLNNRZ",
        ],
        5: [
            "AAAFRS",
            "AAEEEE",
            "AAFIRS",
            "ADENNN",
            "AEEEEM",
            "AEEGMU",
            "AEGMNN",
            "AEILMN",
            "AEINOU",
            "AFIRSY",
            "AEJLRS",
            "AFRTTY",
            "BJKQXZ",
            "CCNSTW",
            "CEIILT",
            "CEILPT",
            "CEIPST",
            "DDHNOT",
            "DHHLOR",
            "DHLNOR",
            "DHLNOR",
            "EIIITT",
            "EMOTTT",
            "ENSSSU",
            "FIPRSY",
        ],
    }

    def __init__(
        self,
        size: int = 4,
        time_limit: int = 180,
        *,
        dictionary: Optional[BoggleDictionary] = None,
        language: str = "en",
        lexicon: str = "enable",
        player_names: Optional[Iterable[str]] = None,
        seed: Optional[int] = None,
    ) -> None:
        """Initializes the Boggle game engine.

        Args:
            size (int): The dimension of the game board (e.g., 4 for 4x4).
            time_limit (int): The duration of the round in seconds.
            dictionary (Optional[BoggleDictionary]): A pre-loaded dictionary instance.
                                                    If not provided, one will be created.
            language (str): The language code for the dictionary (e.g., "en").
            lexicon (str): The lexicon identifier for the dictionary.
            player_names (Optional[Iterable[str]]): An iterable of player display names.
            seed (Optional[int]): An optional seed for deterministic board generation.
        """
        self.size = size
        self.time_limit = time_limit
        self._dictionary = dictionary or BoggleDictionary(language=language, lexicon=lexicon)
        self._rng = random.Random(seed)
        self._players = list(player_names or ["Player 1"])
        self._grid: List[List[str]] = []
        self._start_time: Optional[float] = None
        self._end_time: Optional[float] = None
        self._state = GameState.NOT_STARTED
        self._scores: Dict[int, int] = {}
        self._player_words: Dict[int, Set[str]] = {}
        self._word_claims: Dict[str, Set[int]] = {}
        self._word_points: Dict[str, int] = {}
        self._word_owners: Dict[str, Optional[int]] = {}
        self._last_feedback: Optional[SubmissionFeedback] = None
        self.reset()

    def reset(self) -> None:
        """Resets the game to a new round, generating a new board and starting the timer."""
        self._grid = self._generate_board()
        self._scores = {index: 0 for index in range(len(self._players))}
        self._player_words = {index: set() for index in range(len(self._players))}
        self._word_claims = {}
        self._word_points = {}
        self._word_owners = {}
        self._start_time = time.monotonic()
        self._end_time = None
        self._state = GameState.IN_PROGRESS
        self._last_feedback = None

    def _generate_board(self) -> List[List[str]]:
        """Generates a new Boggle board, using official dice layouts if available.

        Returns:
            List[List[str]]: A 2D list representing the generated board.
        """
        layout = self.DICE_LAYOUTS.get(self.size)
        cells: List[str]
        if layout:
            # If an official layout exists, shuffle the dice and roll them.
            dice = layout.copy()
            self._rng.shuffle(dice)
            rolls = [self._rng.choice(die) for die in dice]
            cells = rolls[: self.size * self.size]
        else:
            # Otherwise, create a board with random letters.
            alphabet = "EERTTYLNSAOIUHDCPMGFKWVBXZJQ"
            cells = [self._rng.choice(alphabet) for _ in range(self.size * self.size)]
        grid = [[self._format_tile(cells[row * self.size + col]) for col in range(self.size)] for row in range(self.size)]
        return grid

    @staticmethod
    def _format_tile(letter: str) -> str:
        """Formats a die roll for display, handling the "Qu" tile.

        Args:
            letter (str): The letter rolled from a die.

        Returns:
            str: The formatted letter, with "Q" becoming "Qu".
        """
        if letter.upper() == "Q":
            return "Qu"
        return letter.upper()

    def is_game_over(self) -> bool:
        """Determines if the game round has ended.

        Returns:
            bool: True if the round is finished, False otherwise.
        """
        self._update_state()
        return self._state == GameState.FINISHED

    def _update_state(self) -> None:
        """Transitions the game state to `FINISHED` if the timer has expired."""
        if self._state != GameState.IN_PROGRESS or self._start_time is None:
            return
        if self.time_limit <= 0:
            return
        if time.monotonic() - self._start_time >= self.time_limit:
            self._state = GameState.FINISHED
            self._end_time = time.monotonic()

    def get_current_player(self) -> int:
        """Returns the active player index. In Boggle, turns are not sequential,
        so this always returns 0.
        """
        return 0

    def get_valid_moves(self) -> List[BoggleMove]:
        """Returns an empty list, as enumerating all possible words is impractical."""
        return []

    def make_move(self, move: BoggleMove) -> bool:
        """Validates and registers a player's word submission.

        This method checks if the word is valid (in the dictionary, on the
        board, etc.) and updates the game state accordingly.

        Args:
            move (BoggleMove): The move containing the submitted word and player ID.

        Returns:
            bool: True if the submission is accepted (even if worth zero points),
                  False otherwise.
        """
        self._update_state()
        if self.is_game_over():
            self._last_feedback = SubmissionFeedback(word=move.word, player_id=move.player_id, accepted=False, points=0, reason="Round has already finished.")
            return False
        if move.player_id not in self._scores:
            self._last_feedback = SubmissionFeedback(word=move.word, player_id=move.player_id, accepted=False, points=0, reason="Unknown player.")
            return False
        normalized = move.word.strip().upper()
        if len(normalized) < 3:
            self._last_feedback = SubmissionFeedback(
                word=normalized, player_id=move.player_id, accepted=False, points=0, reason="Words must be at least three letters."
            )
            return False
        if normalized in self._player_words[move.player_id]:
            self._last_feedback = SubmissionFeedback(
                word=normalized, player_id=move.player_id, accepted=False, points=0, reason="Word already submitted by this player."
            )
            return False
        if not self._dictionary.contains(normalized):
            self._last_feedback = SubmissionFeedback(
                word=normalized, player_id=move.player_id, accepted=False, points=0, reason="Word not found in dictionary."
            )
            return False
        if not self.is_word_in_grid(normalized):
            self._last_feedback = SubmissionFeedback(
                word=normalized, player_id=move.player_id, accepted=False, points=0, reason="Word cannot be formed on the board."
            )
            return False
        # If all checks pass, record the word and evaluate its score.
        self._player_words[move.player_id].add(normalized)
        claims = self._word_claims.setdefault(normalized, set())
        claims.add(move.player_id)
        accepted, points, reason = self._evaluate_word(normalized, move.player_id)
        self._last_feedback = SubmissionFeedback(word=normalized, player_id=move.player_id, accepted=accepted, points=points, reason=reason)
        return accepted

    def _evaluate_word(self, word: str, player_id: int) -> Tuple[bool, int, Optional[str]]:
        """Updates scores based on a newly claimed word and returns feedback.

        This method handles the logic for awarding and revoking points when
        words are claimed by multiple players.

        Args:
            word (str): The word that has just been claimed.
            player_id (int): The ID of the player submitting the word.

        Returns:
            Tuple[bool, int, Optional[str]]: A tuple containing whether the
                submission counts, the points awarded, and an optional message.
        """
        points = self._score_for_word(word)
        self._word_points.setdefault(word, points)
        claims = self._word_claims[word]
        previous_owner = self._word_owners.get(word)
        if len(claims) == 1:
            # First player to claim the word gets the points.
            if previous_owner != player_id:
                if previous_owner is not None:
                    self._scores[previous_owner] -= self._word_points[word]
                self._scores[player_id] += self._word_points[word]
                self._word_owners[word] = player_id
            return True, self._word_points[word], None
        if previous_owner is not None:
            # If another player claims a word, the original owner loses the points.
            self._scores[previous_owner] -= self._word_points[word]
            self._word_owners.pop(word, None)
        return True, 0, "Duplicate word - no points awarded."

    def _score_for_word(self, word: str) -> int:
        """Returns the official Boggle score for a given word based on its length.

        Args:
            word (str): The word to evaluate.

        Returns:
            int: The number of points the word is worth.
        """
        length = len(word)
        if length <= 2:
            return 0
        if length >= 8:
            return 11
        return self.SCORE_TABLE.get(length, 0)

    def is_word_in_grid(self, word: str) -> bool:
        """Determines if a word can be formed from adjacent tiles on the board.

        Args:
            word (str): The candidate word to search for.

        Returns:
            bool: True if the word can be constructed, False otherwise.
        """
        target = word.upper()
        for row in range(self.size):
            for col in range(self.size):
                if self._search_from(target, 0, row, col, set()):
                    return True
        return False

    def _search_from(
        self,
        word: str,
        index: int,
        row: int,
        col: int,
        visited: Set[Tuple[int, int]],
    ) -> bool:
        """A recursive depth-first search to find a word on the board.

        Args:
            word (str): The word being matched.
            index (int): The current position within the word being checked.
            row (int): The row of the tile under consideration.
            col (int): The column of the tile under consideration.
            visited (Set[Tuple[int, int]]): The coordinates already used in the search path.

        Returns:
            bool: True if a valid path for the word is found, False otherwise.
        """
        if index >= len(word):
            return True
        if not (0 <= row < self.size and 0 <= col < self.size):
            return False
        position = (row, col)
        if position in visited:
            return False
        tile = self._grid[row][col].upper()
        if not word.startswith(tile, index):
            return False
        updated_visited = set(visited)
        updated_visited.add(position)
        next_index = index + len(tile)
        # Explore all 8 neighboring cells.
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                if self._search_from(word, next_index, row + dr, col + dc, updated_visited):
                    return True
        return False

    def end_game(self) -> None:
        """Forces the round to end immediately."""
        self._state = GameState.FINISHED
        self._end_time = time.monotonic()

    def get_winner(self) -> Optional[int]:
        """Returns the index of the winning player, or None for a tie.

        Returns:
            Optional[int]: The index of the winning player, or None if there is a tie.
        """
        if not self.is_game_over() or not self._scores:
            return None
        top_score = max(self._scores.values())
        leaders = [player_id for player_id, score in self._scores.items() if score == top_score]
        return leaders[0] if len(leaders) == 1 else None

    def get_game_state(self) -> GameState:
        """Returns the current state of the game round.

        Returns:
            GameState: The current status of the round (e.g., IN_PROGRESS, FINISHED).
        """
        self._update_state()
        return self._state

    def get_state_representation(self) -> dict:
        """Returns a serializable snapshot of the current game state.

        Returns:
            dict: A dictionary containing the board, scores, word claims, and timer data.
        """
        return {
            "grid": [row.copy() for row in self._grid],
            "scores": self.get_scores(),
            "word_claims": self.get_word_claims(),
            "time_remaining": self.get_remaining_time(),
        }

    def get_grid(self) -> List[List[str]]:
        """Returns a copy of the current game board.

        Returns:
            List[List[str]]: A 2D list representing the grid.
        """
        return [row.copy() for row in self._grid]

    def get_score(self) -> int:
        """Returns the combined score across all players.

        Returns:
            int: The sum of all player scores.
        """
        return sum(self._scores.values())

    def get_scores(self) -> Dict[str, int]:
        """Returns the scoreboard, keyed by player name.

        Returns:
            Dict[str, int]: A mapping of player display names to their scores.
        """
        return {self._players[player_id]: self._scores[player_id] for player_id in range(len(self._players))}

    def get_found_words(self) -> Dict[str, Set[str]]:
        """Returns the set of words submitted by each player.

        Returns:
            Dict[str, Set[str]]: A mapping of player names to the set of words they entered.
        """
        return {self._players[player_id]: set(words) for player_id, words in self._player_words.items()}

    def get_unique_words(self, player_id: int) -> Set[str]:
        """Returns the set of words found uniquely by the specified player.

        Args:
            player_id (int): The index of the player.

        Returns:
            Set[str]: A set of words credited solely to the specified player.
        """
        return {word for word in self._player_words.get(player_id, set()) if len(self._word_claims.get(word, set())) == 1}

    def get_word_claims(self) -> Dict[str, Set[str]]:
        """Returns which players claimed each submitted word.

        Returns:
            Dict[str, Set[str]]: A mapping from each word to the set of player names
                                 who submitted it.
        """
        return {word: {self._players[player_id] for player_id in claimants} for word, claimants in self._word_claims.items()}

    def get_remaining_time(self) -> Optional[int]:
        """Returns the number of seconds left in the round.

        Returns:
            Optional[int]: The integer number of seconds remaining, or None if the
                           timer is disabled.
        """
        if self.time_limit <= 0 or self._start_time is None:
            return None
        elapsed = time.monotonic() - self._start_time
        return max(int(self.time_limit - elapsed), 0)

    def get_last_feedback(self) -> Optional[SubmissionFeedback]:
        """Returns feedback for the most recent word submission.

        Returns:
            Optional[SubmissionFeedback]: A feedback instance, or None if no
                                          submission has been made yet.
        """
        return self._last_feedback

    def get_players(self) -> List[str]:
        """Returns a copy of the registered player names.

        Returns:
            List[str]: A list of player display names.
        """
        return list(self._players)


class BoggleCLI:
    """An interactive command-line interface for playing Boggle."""

    def __init__(self) -> None:
        """Initializes the CLI wrapper."""
        self.game: Optional[BoggleGame] = None

    def run(self) -> None:
        """Starts a new Boggle round in the terminal."""
        print("Welcome to Boggle!")
        size = self._prompt_int("Enter board size (4 or 5 recommended) [4]: ", default=4)
        time_limit = self._prompt_int("Enter round length in seconds [180]: ", default=180)
        player_names = self._prompt_players()
        self.game = BoggleGame(size=size, time_limit=time_limit, player_names=player_names)
        self._print_board()
        print("Enter words as '<player> word'. Type 'done' to finish early.")
        while self.game and not self.game.is_game_over():
            self._print_timer()
            entry = input("Submission: ").strip()
            if entry.lower() == "done":
                self.game.end_game()
                break
            if not entry:
                continue
            player_id, word = self._parse_submission(entry)
            if player_id is None or not word:
                continue
            if not self.game.make_move(BoggleMove(word=word, player_id=player_id)):
                feedback = self.game.get_last_feedback()
                if feedback:
                    print(f"✗ {feedback.word}: {feedback.reason}")
                continue
            feedback = self.game.get_last_feedback()
            if feedback:
                if feedback.points > 0:
                    player = self.game.get_players()[player_id]
                    print(f"✓ {player} earns {feedback.points} points for {feedback.word}.")
                else:
                    print(f"• {feedback.word}: {feedback.reason}")
            self._print_scores()
        if self.game:
            self.game.end_game()
            self._print_summary()

    def _prompt_int(self, prompt: str, *, default: int) -> int:
        """Prompts the user for an integer, with a default fallback value.

        Args:
            prompt (str): The message to display to the player.
            default (int): The value to return if the user provides no or invalid input.

        Returns:
            int: The integer entered by the user, or the default value.
        """
        try:
            response = input(prompt).strip()
            return int(response) if response else default
        except ValueError:
            print("Invalid number, using default value.")
            return default

    def _prompt_players(self) -> List[str]:
        """Collects player names from standard input.

        Returns:
            List[str]: A list of player display names.
        """
        count = max(self._prompt_int("Number of players [1]: ", default=1), 1)
        players: List[str] = []
        for index in range(count):
            default_name = f"Player {index + 1}"
            name = input(f"Player {index + 1} name [{default_name}]: ").strip()
            players.append(name or default_name)
        return players

    def _print_board(self) -> None:
        """Displays the current game board to the terminal."""
        if not self.game:
            return
        print("\nYour Boggle Board:")
        print("-" * (self.game.size * 4))
        for row in self.game.get_grid():
            print("  " + "  ".join(row))
        print("-" * (self.game.size * 4))

    def _print_timer(self) -> None:
        """Displays the countdown timer if it is enabled."""
        if not self.game:
            return
        remaining = self.game.get_remaining_time()
        if remaining is not None:
            print(f"Time remaining: {remaining} seconds")

    def _parse_submission(self, entry: str) -> Tuple[Optional[int], str]:
        """Parses user input into a player index and a word.

        Args:
            entry (str): The raw submission string entered by the user.

        Returns:
            Tuple[Optional[int], str]: A tuple containing the player index and the word.
                                       The player index is `None` if parsing fails.
        """
        if not self.game:
            return None, ""
        players = self.game.get_players()
        if len(players) == 1:
            return 0, entry
        try:
            player_token, word = entry.split(maxsplit=1)
        except ValueError:
            print("Format should be '<player> word'.")
            return None, ""
        for index, name in enumerate(players):
            if name.lower() == player_token.lower():
                return index, word
        print(f"Unknown player '{player_token}'.")
        return None, ""

    def _print_scores(self) -> None:
        """Prints the current scoreboard."""
        if not self.game:
            return
        print("Scores:")
        for player, score in self.game.get_scores().items():
            print(f"  {player}: {score}")

    def _print_summary(self) -> None:
        """Presents the final results of the round, including unique words,
        duplicates, and the winner.
        """
        if not self.game:
            return
        print("\nRound complete!")
        scores = self.game.get_scores()
        for player, score in scores.items():
            unique_words = sorted(self.game.get_unique_words(self.game.get_players().index(player)))
            duplicates = sorted(word for word in self.game.get_found_words()[player] if word not in unique_words)
            print(f"{player}: {score} points")
            if unique_words:
                print(f"  Unique words ({len(unique_words)}): {', '.join(unique_words)}")
            if duplicates:
                print(f"  Duplicates ({len(duplicates)}): {', '.join(duplicates)}")
        winner = self.game.get_winner()
        if winner is not None:
            print(f"Winner: {self.game.get_players()[winner]}")
        else:
            print("The round ended in a tie!")
