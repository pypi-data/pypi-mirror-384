import itertools
import pathlib
import sys

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from paper_games.nim import NimGame


def nim_sum(heaps):
    result = 0
    for heap in heaps:
        result ^= heap
    return result


def has_winning_move(heaps):
    for heap_index, heap in enumerate(heaps):
        for take in range(1, heap + 1):
            new_heaps = list(heaps)
            new_heaps[heap_index] -= take
            if nim_sum(new_heaps) == 0:
                return True
    return False


def test_computer_move_leaves_zero_nim_sum_when_possible():
    for heaps in itertools.product(range(1, 6), repeat=3):
        original = list(heaps)
        game = NimGame(list(original))
        starting_sum = game.nim_sum()
        heap_index, remove = game.computer_move()
        assert 1 <= remove <= original[heap_index]
        resulting_sum = game.nim_sum()
        if starting_sum != 0:
            assert resulting_sum == 0
        else:
            assert not has_winning_move(original)


def test_computer_move_handles_single_heap():
    game = NimGame([7])
    heap_index, remove = game.computer_move()
    assert heap_index == 0
    assert remove == 7
    assert game.is_over()


def test_misere_all_singletons_leaves_opponent_bad_position():
    game = NimGame([1, 1, 1, 1], misere=True)
    heap_index, remove = game.computer_move()
    assert remove == 1
    assert game.heaps[heap_index] == 0
    remaining = sum(1 for heap in game.heaps if heap > 0)
    # Opponent faces an odd number of singletons and is in the losing seat.
    assert remaining % 2 == 1
