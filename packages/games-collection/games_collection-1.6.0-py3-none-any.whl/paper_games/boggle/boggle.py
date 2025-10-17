"""Boggle game engine, dictionary integration, and command line interface."""

from __future__ import annotations

import random
import time
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Set, Tuple

from common.game_engine import GameEngine, GameState

from .dictionary import BoggleDictionary


@dataclass(frozen=True)
class BoggleMove:
    """Move representing a submitted word in Boggle.

    Args:
        word: Candidate word submitted by the player.
        player_id: Zero-based index of the submitting player.
    """

    word: str
    player_id: int = 0


@dataclass
class SubmissionFeedback:
    """Feedback describing the outcome of a submission.

    Attributes:
        word: Word that was evaluated.
        player_id: Index of the submitting player.
        accepted: Whether the submission counted as a valid word.
        points: Number of points awarded for this submission.
        reason: Additional information for rejected or zero-point submissions.
    """

    word: str
    player_id: int
    accepted: bool
    points: int
    reason: Optional[str] = None


class BoggleGame(GameEngine[BoggleMove, int]):
    """Engine implementing the official Boggle rules.

    The engine supports lexicon-backed dictionary lookups, official dice layouts,
    multiplayer duplicate detection, and timer-based rounds.
    """

    SCORE_TABLE = {3: 1, 4: 1, 5: 2, 6: 3, 7: 5}
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
        """Initialize the Boggle game engine.

        Args:
            size: Board dimension (4 for classic, 5 for Big Boggle, etc.).
            time_limit: Duration of the round in seconds.
            dictionary: Pre-loaded dictionary instance to use.
            language: Language code for dictionary lookup when ``dictionary`` is not provided.
            lexicon: Lexicon identifier for the selected language.
            player_names: Iterable of player display names.
            seed: Optional seed for deterministic board generation.
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
        """Reset the round, generate a new board, and start the timer."""

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
        """Generate a board using official dice layouts when available."""

        layout = self.DICE_LAYOUTS.get(self.size)
        cells: List[str]
        if layout:
            dice = layout.copy()
            self._rng.shuffle(dice)
            rolls = [self._rng.choice(die) for die in dice]
            cells = rolls[: self.size * self.size]
        else:
            alphabet = "EERTTYLNSAOIUHDCPMGFKWVBXZJQ"
            cells = [self._rng.choice(alphabet) for _ in range(self.size * self.size)]
        grid = [[self._format_tile(cells[row * self.size + col]) for col in range(self.size)] for row in range(self.size)]
        return grid

    @staticmethod
    def _format_tile(letter: str) -> str:
        """Format a die roll for board presentation.

        Args:
            letter: Letter rolled from a die.

        Returns:
            Formatted representation suitable for display and traversal.
        """

        if letter.upper() == "Q":
            return "Qu"
        return letter.upper()

    def is_game_over(self) -> bool:
        """Determine whether the round has ended.

        Returns:
            True when the round is finished, otherwise False.
        """

        self._update_state()
        return self._state == GameState.FINISHED

    def _update_state(self) -> None:
        """Transition to ``FINISHED`` when the timer expires."""

        if self._state != GameState.IN_PROGRESS or self._start_time is None:
            return
        if self.time_limit <= 0:
            return
        if time.monotonic() - self._start_time >= self.time_limit:
            self._state = GameState.FINISHED
            self._end_time = time.monotonic()

    def get_current_player(self) -> int:
        """Return the active player index (unused in free-form submission).

        Returns:
            Always returns ``0`` because turns are not sequential in Boggle.
        """

        return 0

    def get_valid_moves(self) -> List[BoggleMove]:
        """Return an empty list because the search space is too large.

        Returns:
            Empty list (valid moves are not enumerated).
        """

        return []

    def make_move(self, move: BoggleMove) -> bool:
        """Validate and register a player's word submission.

        Args:
            move: Submitted move containing the word and player index.

        Returns:
            ``True`` when the submission is accepted (even if worth zero points) and ``False`` otherwise.
        """

        self._update_state()
        if self.is_game_over():
            self._last_feedback = SubmissionFeedback(
                word=move.word,
                player_id=move.player_id,
                accepted=False,
                points=0,
                reason="Round has already finished.",
            )
            return False
        if move.player_id not in self._scores:
            self._last_feedback = SubmissionFeedback(
                word=move.word,
                player_id=move.player_id,
                accepted=False,
                points=0,
                reason="Unknown player.",
            )
            return False
        normalized = move.word.strip().upper()
        if len(normalized) < 3:
            self._last_feedback = SubmissionFeedback(
                word=normalized,
                player_id=move.player_id,
                accepted=False,
                points=0,
                reason="Words must be at least three letters.",
            )
            return False
        if normalized in self._player_words[move.player_id]:
            self._last_feedback = SubmissionFeedback(
                word=normalized,
                player_id=move.player_id,
                accepted=False,
                points=0,
                reason="Word already submitted by this player.",
            )
            return False
        if not self._dictionary.contains(normalized):
            self._last_feedback = SubmissionFeedback(
                word=normalized,
                player_id=move.player_id,
                accepted=False,
                points=0,
                reason="Word not found in dictionary.",
            )
            return False
        if not self.is_word_in_grid(normalized):
            self._last_feedback = SubmissionFeedback(
                word=normalized,
                player_id=move.player_id,
                accepted=False,
                points=0,
                reason="Word cannot be formed on the board.",
            )
            return False
        self._player_words[move.player_id].add(normalized)
        claims = self._word_claims.setdefault(normalized, set())
        claims.add(move.player_id)
        accepted, points, reason = self._evaluate_word(normalized, move.player_id)
        self._last_feedback = SubmissionFeedback(
            word=normalized,
            player_id=move.player_id,
            accepted=accepted,
            points=points,
            reason=reason,
        )
        return accepted

    def _evaluate_word(self, word: str, player_id: int) -> Tuple[bool, int, Optional[str]]:
        """Update scores for ``word`` and return feedback information.

        Args:
            word: Word that has just been claimed.
            player_id: Player submitting the word.

        Returns:
            Tuple where the first item is whether the submission counts, the second is the
            awarded points, and the third is an optional explanatory message.
        """

        points = self._score_for_word(word)
        self._word_points.setdefault(word, points)
        claims = self._word_claims[word]
        previous_owner = self._word_owners.get(word)
        if len(claims) == 1:
            if previous_owner != player_id:
                if previous_owner is not None:
                    self._scores[previous_owner] -= self._word_points[word]
                self._scores[player_id] += self._word_points[word]
                self._word_owners[word] = player_id
            return True, self._word_points[word], None
        if previous_owner is not None:
            self._scores[previous_owner] -= self._word_points[word]
            self._word_owners.pop(word, None)
        return True, 0, "Duplicate word - no points awarded."

    def _score_for_word(self, word: str) -> int:
        """Return the official Boggle score for ``word``.

        Args:
            word: Word to evaluate.

        Returns:
            Integer number of points granted for the word.
        """

        length = len(word)
        if length <= 2:
            return 0
        if length >= 8:
            return 11
        return self.SCORE_TABLE.get(length, 0)

    def is_word_in_grid(self, word: str) -> bool:
        """Determine whether ``word`` can be formed from adjacent tiles.

        Args:
            word: Candidate word to search for.

        Returns:
            True if the word can be constructed on the current board, otherwise False.
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
        """Depth-first search helper to determine if the word exists.

        Args:
            word: Word being matched.
            index: Position within ``word`` currently being checked.
            row: Row of the tile under consideration.
            col: Column of the tile under consideration.
            visited: Coordinates already used in the search path.

        Returns:
            True if the path yields the word, otherwise False.
        """

        if index >= len(word):
            return True
        if row < 0 or row >= self.size or col < 0 or col >= self.size:
            return False
        position = (row, col)
        if position in visited:
            return False
        tile = self._grid[row][col].upper()
        if not word.startswith(tile, index):
            return False
        updated = set(visited)
        updated.add(position)
        next_index = index + len(tile)
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                if self._search_from(word, next_index, row + dr, col + dc, updated):
                    return True
        return False

    def end_game(self) -> None:
        """Force the round to end immediately."""

        self._state = GameState.FINISHED
        self._end_time = time.monotonic()

    def get_winner(self) -> Optional[int]:
        """Return the index of the winning player or ``None`` for a tie.

        Returns:
            Index of the winning player or ``None`` when there is a tie/no winner.
        """

        if not self.is_game_over():
            return None
        if not self._scores:
            return None
        top_score = max(self._scores.values())
        leaders = [player_id for player_id, score in self._scores.items() if score == top_score]
        if len(leaders) == 1:
            return leaders[0]
        return None

    def get_game_state(self) -> GameState:
        """Return the current state of the round.

        Returns:
            Game state enumeration describing the round status.
        """

        self._update_state()
        return self._state

    def get_state_representation(self) -> dict:
        """Return a serialisable snapshot of the current game state.

        Returns:
            Dictionary containing the board, scores, word claims, and timer data.
        """

        return {
            "grid": [row.copy() for row in self._grid],
            "scores": self.get_scores(),
            "word_claims": self.get_word_claims(),
            "time_remaining": self.get_remaining_time(),
        }

    def get_grid(self) -> List[List[str]]:
        """Return a copy of the current board.

        Returns:
            Two-dimensional list representing the grid.
        """

        return [row.copy() for row in self._grid]

    def get_score(self) -> int:
        """Return the combined score across all players.

        Returns:
            Sum of all player scores.
        """

        return sum(self._scores.values())

    def get_scores(self) -> Dict[str, int]:
        """Return the scoreboard keyed by player name.

        Returns:
            Mapping of player display name to score.
        """

        return {self._players[player_id]: self._scores[player_id] for player_id in range(len(self._players))}

    def get_found_words(self) -> Dict[str, Set[str]]:
        """Return the set of words submitted by each player.

        Returns:
            Mapping of player names to the set of words they entered.
        """

        return {self._players[player_id]: set(words) for player_id, words in self._player_words.items()}

    def get_unique_words(self, player_id: int) -> Set[str]:
        """Return words uniquely found by the specified player.

        Args:
            player_id: Index of the player.

        Returns:
            Set of words credited solely to the specified player.
        """

        return {word for word in self._player_words.get(player_id, set()) if len(self._word_claims.get(word, set())) == 1}

    def get_word_claims(self) -> Dict[str, Set[str]]:
        """Return which players claimed each word.

        Returns:
            Mapping from word to the set of player names who submitted it.
        """

        return {word: {self._players[player_id] for player_id in claimants} for word, claimants in self._word_claims.items()}

    def get_remaining_time(self) -> Optional[int]:
        """Return the number of seconds left in the round.

        Returns:
            Integer seconds remaining or ``None`` if the timer is disabled.
        """

        if self.time_limit <= 0 or self._start_time is None:
            return None
        elapsed = time.monotonic() - self._start_time
        remaining = max(int(self.time_limit - elapsed), 0)
        return remaining

    def get_last_feedback(self) -> Optional[SubmissionFeedback]:
        """Return feedback for the most recent submission.

        Returns:
            Submission feedback instance or ``None`` if no submission has been made.
        """

        return self._last_feedback

    def get_players(self) -> List[str]:
        """Return a copy of the registered player names.

        Returns:
            List of player display names.
        """

        return list(self._players)


class BoggleCLI:
    """Interactive command-line interface for Boggle."""

    def __init__(self) -> None:
        """Initialise the CLI wrapper."""

        self.game: Optional[BoggleGame] = None

    def run(self) -> None:
        """Start a Boggle round in the terminal."""

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
        """Prompt the user for an integer with a default fallback.

        Args:
            prompt: Message displayed to the player.
            default: Value returned when the user supplies no or invalid input.

        Returns:
            Integer entered by the user or the default value.
        """

        try:
            response = input(prompt).strip()
            return int(response) if response else default
        except ValueError:
            print("Invalid number, using default value.")
            return default

    def _prompt_players(self) -> List[str]:
        """Collect player names from stdin.

        Returns:
            List of player display names.
        """

        count = max(self._prompt_int("Number of players [1]: ", default=1), 1)
        players: List[str] = []
        for index in range(count):
            default_name = f"Player {index + 1}"
            name = input(f"Player {index + 1} name [{default_name}]: ").strip()
            players.append(name or default_name)
        return players

    def _print_board(self) -> None:
        """Display the current board to the terminal."""

        if not self.game:
            return
        print("\nYour Boggle Board:")
        print("-" * (self.game.size * 4))
        for row in self.game.get_grid():
            print("  " + "  ".join(row))
        print("-" * (self.game.size * 4))

    def _print_timer(self) -> None:
        """Display the countdown timer if enabled."""

        if not self.game:
            return
        remaining = self.game.get_remaining_time()
        if remaining is not None:
            print(f"Time remaining: {remaining} seconds")

    def _parse_submission(self, entry: str) -> Tuple[Optional[int], str]:
        """Parse user input into a player index and word.

        Args:
            entry: Raw submission string entered by the user.

        Returns:
            Tuple of (player index, word). Player index is ``None`` when parsing fails.
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
        """Print the scoreboard."""

        if not self.game:
            return
        print("Scores:")
        for player, score in self.game.get_scores().items():
            print(f"  {player}: {score}")

    def _print_summary(self) -> None:
        """Present round results including duplicates and winners."""

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
