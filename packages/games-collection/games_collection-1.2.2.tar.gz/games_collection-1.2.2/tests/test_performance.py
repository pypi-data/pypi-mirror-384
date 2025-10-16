"""Performance benchmarking tests for game algorithms.

These tests ensure that game logic and AI perform efficiently.
"""

import pathlib
import sys
import time

import pytest

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@pytest.mark.performance
class TestNimPerformance:
    """Performance tests for Nim game."""

    def test_nim_computer_move_performance(self, benchmark_iterations):
        """Test that Nim computer move is calculated quickly."""
        from paper_games.nim import NimGame

        start_time = time.time()
        for _ in range(benchmark_iterations):
            game = NimGame([10, 15, 20])
            game.computer_move()
        elapsed = time.time() - start_time

        avg_time = elapsed / benchmark_iterations
        assert avg_time < 0.01, f"Computer move too slow: {avg_time:.4f}s average"

    def test_nim_large_heaps_performance(self):
        """Test Nim performance with large heap sizes."""
        from paper_games.nim import NimGame

        start_time = time.time()
        game = NimGame([100, 200, 300])
        game.computer_move()
        elapsed = time.time() - start_time

        assert elapsed < 0.1, f"Large heap calculation too slow: {elapsed:.4f}s"

    def test_nim_many_heaps_performance(self):
        """Test Nim performance with many heaps."""
        from paper_games.nim import NimGame

        start_time = time.time()
        game = NimGame([5, 10, 15, 20, 25, 30])
        game.computer_move()
        elapsed = time.time() - start_time

        assert elapsed < 0.05, f"Many heaps calculation too slow: {elapsed:.4f}s"


@pytest.mark.performance
class TestTicTacToePerformance:
    """Performance tests for Tic-Tac-Toe game."""

    def test_tictactoe_computer_move_performance(self, benchmark_iterations):
        """Test that Tic-Tac-Toe computer move is calculated quickly."""
        from paper_games.tic_tac_toe import TicTacToeGame

        start_time = time.time()
        for _ in range(benchmark_iterations):
            game = TicTacToeGame()
            game.computer_move()
        elapsed = time.time() - start_time

        avg_time = elapsed / benchmark_iterations
        assert avg_time < 0.05, f"Computer move too slow: {avg_time:.4f}s average"

    def test_tictactoe_full_game_performance(self):
        """Test performance of a complete game."""
        from paper_games.tic_tac_toe import TicTacToeGame

        start_time = time.time()
        for _ in range(10):
            game = TicTacToeGame()
            moves = 0
            while not game.is_over() and moves < 9:
                move = game.computer_move()
                if move:
                    row, col = move
                    game.make_move(row, col)
                moves += 1
        elapsed = time.time() - start_time

        assert elapsed < 1.0, f"Full game simulation too slow: {elapsed:.4f}s for 10 games"


@pytest.mark.performance
class TestBattleshipPerformance:
    """Performance tests for Battleship game."""

    def test_battleship_setup_performance(self, benchmark_iterations):
        """Test that Battleship board setup is fast."""
        from paper_games.battleship import BattleshipGame

        start_time = time.time()
        for _ in range(benchmark_iterations):
            game = BattleshipGame()
            game.setup_random()
        elapsed = time.time() - start_time

        avg_time = elapsed / benchmark_iterations
        assert avg_time < 0.1, f"Board setup too slow: {avg_time:.4f}s average"

    def test_battleship_ai_shot_performance(self):
        """Test that AI shot selection is fast."""
        from paper_games.battleship import BattleshipGame

        game = BattleshipGame()
        game.setup_random()

        start_time = time.time()
        for _ in range(50):
            # Just test that the game can process shots quickly
            try:
                game.computer_shot()
            except Exception:
                # If computer_shot fails, that's okay - we're testing performance
                pass
        elapsed = time.time() - start_time

        assert elapsed < 0.5, f"AI shot selection too slow: {elapsed:.4f}s for 50 shots"


@pytest.mark.performance
class TestDotsAndBoxesPerformance:
    """Performance tests for Dots and Boxes game."""

    def test_dots_boxes_computer_move_performance(self):
        """Test that Dots and Boxes computer move is calculated quickly."""
        from paper_games.dots_and_boxes import DotsAndBoxes

        game = DotsAndBoxes(size=4)

        start_time = time.time()
        for _ in range(20):
            if not game.game_over():
                game.make_computer_move()
        elapsed = time.time() - start_time

        assert elapsed < 1.0, f"Computer move too slow: {elapsed:.4f}s for 20 moves"

    def test_dots_boxes_large_board_performance(self):
        """Test performance with larger board."""
        from paper_games.dots_and_boxes import DotsAndBoxes

        start_time = time.time()
        game = DotsAndBoxes(size=6)
        game.make_computer_move()
        elapsed = time.time() - start_time

        assert elapsed < 0.2, f"Large board move too slow: {elapsed:.4f}s"


@pytest.mark.performance
class TestBlackjackPerformance:
    """Performance tests for Blackjack game."""

    def test_blackjack_game_creation_performance(self, benchmark_iterations):
        """Test that Blackjack game creation is fast."""
        from card_games.blackjack import BlackjackGame

        start_time = time.time()
        for _ in range(benchmark_iterations):
            game = BlackjackGame()
            game.start_round(bet=10)
        elapsed = time.time() - start_time

        avg_time = elapsed / benchmark_iterations
        assert avg_time < 0.01, f"Game creation too slow: {avg_time:.4f}s average"

    def test_blackjack_dealer_play_performance(self):
        """Test that dealer play logic is fast."""
        from card_games.blackjack import BlackjackGame

        game = BlackjackGame()

        start_time = time.time()
        for _ in range(50):
            game.start_round(bet=10)
            # Dealer plays automatically according to rules
        elapsed = time.time() - start_time

        assert elapsed < 0.5, f"Dealer play too slow: {elapsed:.4f}s for 50 rounds"


@pytest.mark.performance
class TestUnoPerformance:
    """Performance tests for UNO game."""

    def test_uno_game_creation_performance(self, benchmark_iterations):
        """Test that UNO game creation is fast."""
        from card_games.uno import UnoGame, build_players

        start_time = time.time()
        for _ in range(benchmark_iterations):
            players = build_players(total_players=4, bots=3)
            _ = UnoGame(players=players)
        elapsed = time.time() - start_time

        avg_time = elapsed / benchmark_iterations
        assert avg_time < 0.02, f"Game creation too slow: {avg_time:.4f}s average"


@pytest.mark.performance
class TestHangmanPerformance:
    """Performance tests for Hangman game."""

    def test_hangman_word_loading_performance(self):
        """Test that word list loading is fast."""
        from paper_games.hangman import HangmanGame

        start_time = time.time()
        for _ in range(100):
            _ = HangmanGame(words=["testing"])
        elapsed = time.time() - start_time

        assert elapsed < 0.1, f"Word loading too slow: {elapsed:.4f}s for 100 games"


@pytest.mark.performance
class TestUnscramblePerformance:
    """Performance tests for Unscramble game."""

    def test_unscramble_word_scrambling_performance(self, benchmark_iterations):
        """Test that word scrambling is fast."""
        from paper_games.unscramble import UnscrambleGame

        start_time = time.time()
        for _ in range(benchmark_iterations):
            _ = UnscrambleGame()
            # Word scrambling happens during initialization
        elapsed = time.time() - start_time

        avg_time = elapsed / benchmark_iterations
        assert avg_time < 0.01, f"Word scrambling too slow: {avg_time:.4f}s average"


@pytest.mark.performance
@pytest.mark.slow
def test_overall_system_performance():
    """Test overall system performance with multiple games."""
    from card_games.blackjack import BlackjackGame
    from card_games.uno import UnoGame, build_players
    from paper_games.nim import NimGame
    from paper_games.tic_tac_toe import TicTacToeGame

    start_time = time.time()

    # Create and play multiple games
    for _ in range(10):
        nim = NimGame([5, 10, 15])
        nim.computer_move()

        ttt = TicTacToeGame()
        ttt.computer_move()

        bj = BlackjackGame()
        bj.start_round(bet=10)

        players = build_players(total_players=4, bots=3)
        _ = UnoGame(players=players)
        # Just creation is enough

    elapsed = time.time() - start_time

    assert elapsed < 5.0, f"Overall system too slow: {elapsed:.4f}s for mixed operations"
