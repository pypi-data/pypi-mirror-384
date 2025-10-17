"""Tests for dice games."""

from __future__ import annotations

import random

from common.game_engine import GameState
from dice_games import (
    BuncoGame,
    BuncoMatchResult,
    BuncoTournament,
    CrapsGame,
    FarkleGame,
    LiarsDiceGame,
)


class FixedRNG:
    """Deterministic RNG for tests."""

    def __init__(self, values: list[int]) -> None:
        self._values = iter(values)

    def randint(self, _a: int, _b: int) -> int:
        return next(self._values)


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

    def test_ai_banks_high_turn_score(self) -> None:
        """Adaptive AI should bank when a turn already has high points."""
        game = FarkleGame()
        game.state = GameState.IN_PROGRESS
        game.turn_score = 900
        game.last_roll = [1, 5]
        game.dice_in_hand = 2
        strategy = game.create_adaptive_ai()
        move = strategy.select_move(game.get_valid_moves(), game)
        assert move[1] is False


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

    def test_pass_line_and_odds_payout(self) -> None:
        """Pass line with odds should pay correct amount on a point win."""
        rng = FixedRNG([3, 3, 3, 3])
        game = CrapsGame(rng=rng)
        assert game.make_move("bet_pass 50")
        assert game.make_move("roll")
        assert game.point == 6
        assert game.make_move("bet_odds 30")
        assert game.odds_bet == 30
        assert game.make_move("roll")
        assert game.point is None
        assert game.current_bet == 0
        assert game.odds_bet == 0
        assert game.bankroll == 1086

    def test_place_bet_management(self) -> None:
        """Place bets should pay out and be removable."""
        rng = FixedRNG([2, 2])
        game = CrapsGame(rng=rng)
        assert game.make_move("bet_place_4 10")
        assert game.place_bets[4] == 10
        game.make_move("roll")
        assert game.bankroll == 1008
        assert game.make_move("remove_place_4")
        assert game.place_bets[4] == 0
        assert game.bankroll == 1018


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

    def test_ai_calls_unlikely_bid(self) -> None:
        """Adaptive AI should challenge improbable bids."""
        game = LiarsDiceGame(num_players=3, dice_per_player=3)
        game.state = GameState.IN_PROGRESS
        game.player_dice = [[2, 2, 3], [4, 5, 6], [6, 6, 6]]
        game.current_player_idx = 0
        game.current_bid = (7, 6)
        strategy = game.create_adaptive_ai()
        move = strategy.select_move(game.get_valid_moves(), game)
        assert move == (-1, -1)


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

    def test_tournament_bracket_creation(self) -> None:
        """Tournament should produce bracket and summaries."""
        tournament = BuncoTournament(["Alice", "Bob", "Cara", "Dan"], rng=random.Random(1))
        champion = tournament.run()
        bracket = tournament.get_bracket()
        assert len(bracket) == 2
        assert all(isinstance(match, BuncoMatchResult) for match in bracket[0])
        summary = tournament.get_score_summary()
        assert summary[0].matches_played >= 1
        assert champion in {"Alice", "Bob", "Cara", "Dan"}
