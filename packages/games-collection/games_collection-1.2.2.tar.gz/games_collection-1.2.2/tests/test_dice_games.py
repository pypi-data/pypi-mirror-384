"""Tests for dice games."""

from __future__ import annotations

from dice_games import BuncoGame, CrapsGame, FarkleGame, LiarsDiceGame


class TestFarkle:
    """Test Farkle game."""

    def test_initialization(self) -> None:
        """Test game initializes correctly."""
        game = FarkleGame(num_players=2)
        assert game.num_players == 2
        assert game.winning_score == 10000
        assert len(game.scores) == 2
        assert all(s == 0 for s in game.scores)

    def test_scoring_single_ones(self) -> None:
        """Test scoring for single 1s."""
        game = FarkleGame()
        score = game._calculate_score([1])
        assert score == 100

    def test_scoring_single_fives(self) -> None:
        """Test scoring for single 5s."""
        game = FarkleGame()
        score = game._calculate_score([5])
        assert score == 50

    def test_scoring_three_of_kind(self) -> None:
        """Test scoring for three of a kind."""
        game = FarkleGame()
        score = game._calculate_score([2, 2, 2])
        assert score == 200

    def test_scoring_three_ones(self) -> None:
        """Test scoring for three 1s."""
        game = FarkleGame()
        score = game._calculate_score([1, 1, 1])
        assert score == 1000

    def test_scoring_straight(self) -> None:
        """Test scoring for straight."""
        game = FarkleGame()
        score = game._calculate_score([1, 2, 3, 4, 5, 6])
        assert score == 1500

    def test_no_scoring_dice(self) -> None:
        """Test detecting no scoring dice."""
        game = FarkleGame()
        score = game._calculate_score([2, 3, 4])
        assert score == 0


class TestCraps:
    """Test Craps game."""

    def test_initialization(self) -> None:
        """Test game initializes correctly."""
        game = CrapsGame()
        assert game.bankroll == 1000
        assert game.point is None

    def test_valid_moves(self) -> None:
        """Test valid moves."""
        game = CrapsGame()
        moves = game.get_valid_moves()
        assert "roll" in moves
        assert "bet_pass" in moves


class TestLiarsDice:
    """Test Liar's Dice game."""

    def test_initialization(self) -> None:
        """Test game initializes correctly."""
        game = LiarsDiceGame(num_players=2, dice_per_player=5)
        assert game.num_players == 2
        assert len(game.player_dice) == 2
        assert all(len(dice) == 5 for dice in game.player_dice)

    def test_dice_values(self) -> None:
        """Test dice have valid values."""
        game = LiarsDiceGame()
        for player_dice in game.player_dice:
            for die in player_dice:
                assert 1 <= die <= 6


class TestBunco:
    """Test Bunco game."""

    def test_initialization(self) -> None:
        """Test game initializes correctly."""
        game = BuncoGame(num_players=2)
        assert game.num_players == 2
        assert game.round_num == 1
        assert len(game.scores) == 2

    def test_game_progression(self) -> None:
        """Test game progresses through rounds."""
        game = BuncoGame(num_players=2)
        initial_round = game.round_num
        assert initial_round == 1
        assert not game.is_game_over()
