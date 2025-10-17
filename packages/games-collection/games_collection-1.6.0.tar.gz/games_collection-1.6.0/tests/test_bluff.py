"""Tests for the Bluff card game implementation."""

import pathlib
import sys

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from card_games.bluff.bluff import DECK_TYPES, DIFFICULTIES, BluffGame, BluffTournament, PlayerPattern


def test_deck_types_exist():
    """Test that all deck types are defined."""
    assert "Standard" in DECK_TYPES
    assert "FaceCardsOnly" in DECK_TYPES
    assert "NumbersOnly" in DECK_TYPES
    assert "DoubleDown" in DECK_TYPES
    assert "HighLow" in DECK_TYPES


def test_deck_type_generates_cards():
    """Test that deck types can generate cards."""
    standard_deck = DECK_TYPES["Standard"]
    cards = standard_deck.generate_cards(deck_count=1)
    assert len(cards) == 52  # Standard deck has 52 cards

    face_cards_deck = DECK_TYPES["FaceCardsOnly"]
    cards = face_cards_deck.generate_cards(deck_count=1)
    assert len(cards) == 16  # 4 ranks * 4 suits

    double_down_deck = DECK_TYPES["DoubleDown"]
    cards = double_down_deck.generate_cards(deck_count=1)
    assert len(cards) == 104  # 2 copies of each card


def test_game_initialization():
    """Test that a game can be initialized."""
    difficulty = DIFFICULTIES["Noob"]
    game = BluffGame(difficulty, rounds=3)

    assert game.difficulty == difficulty
    assert len(game.players) == 2  # User + 1 bot for Noob
    assert game.phase.name == "TURN"
    assert not game.finished


def test_game_with_deck_type():
    """Test that a game can be initialized with a specific deck type."""
    difficulty = DIFFICULTIES["Easy"]
    deck_type = DECK_TYPES["FaceCardsOnly"]
    game = BluffGame(difficulty, rounds=2, deck_type=deck_type)

    assert game.deck_type == deck_type
    assert game.deck_type.name == "Face Cards Only"


def test_replay_recording():
    """Test that replay recording can be enabled."""
    difficulty = DIFFICULTIES["Noob"]
    game = BluffGame(difficulty, rounds=2, record_replay=True, seed=42)

    assert game._record_replay is True
    assert game._seed == 42
    assert isinstance(game._replay_actions, list)


def test_team_play_setup():
    """Test that team play mode sets up teams correctly."""
    difficulty = DIFFICULTIES["Easy"]
    game = BluffGame(difficulty, rounds=2, team_play=True)

    assert game.team_play is True
    assert len(game.teams) == 2
    assert game.teams[0].name == "Team Alpha"
    assert game.teams[1].name == "Team Bravo"

    # Check that players are distributed
    total_members = sum(len(team.members) for team in game.teams)
    assert total_members == len(game.players)


def test_tournament_initialization():
    """Test that a tournament can be initialized."""
    difficulty = DIFFICULTIES["Medium"]
    tournament = BluffTournament(difficulty, rounds_per_match=2)

    assert len(tournament.players) == 8  # 8-player tournament
    assert tournament.current_round == 0
    assert not tournament.is_complete()


def test_tournament_round_creation():
    """Test that tournament rounds are created correctly."""
    difficulty = DIFFICULTIES["Noob"]
    tournament = BluffTournament(difficulty, rounds_per_match=1)

    round_obj = tournament.create_round()
    assert round_obj is not None
    assert round_obj.round_number == 1
    assert len(round_obj.matches) == 4  # 8 players = 4 matches


def test_player_pattern_learning():
    """Test that player patterns track behavior."""
    pattern = PlayerPattern()

    # Simulate some claims
    pattern.update_bluff_pattern(was_truthful=False, pile_size=5, card_count=10, rank="A")
    pattern.update_bluff_pattern(was_truthful=False, pile_size=6, card_count=9, rank="K")
    pattern.update_bluff_pattern(was_truthful=True, pile_size=3, card_count=11, rank="Q")

    assert len(pattern.recent_behavior) == 3
    assert pattern.recent_behavior == [False, False, True]

    # Check that patterns are being tracked
    assert len(pattern.bluff_rate_by_pile_size) > 0
    assert len(pattern.bluff_rate_by_card_count) > 0

    # Test probability estimation
    prob = pattern.get_suspected_bluff_probability(5, 10, "A")
    assert 0 <= prob <= 1  # Probability should be between 0 and 1


def test_team_card_counting():
    """Test that teams correctly count total cards."""
    difficulty = DIFFICULTIES["Easy"]
    game = BluffGame(difficulty, rounds=2, team_play=True)

    for team in game.teams:
        total = team.total_cards()
        assert total > 0
        # Should equal sum of member hands
        expected = sum(len(member.hand) for member in team.members)
        assert total == expected


def test_public_state_includes_deck_type():
    """Test that public state includes deck type information."""
    difficulty = DIFFICULTIES["Noob"]
    deck_type = DECK_TYPES["HighLow"]
    game = BluffGame(difficulty, deck_type=deck_type)

    state = game.public_state()
    assert "deck_type" in state
    assert state["deck_type"] == "High-Low"
    assert "valid_ranks" in state
    assert isinstance(state["valid_ranks"], list)


if __name__ == "__main__":
    # Run all tests

    test_functions = [obj for name, obj in globals().items() if name.startswith("test_") and callable(obj)]

    passed = 0
    failed = 0

    for test_func in test_functions:
        try:
            test_func()
            print(f"✓ {test_func.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"✗ {test_func.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {test_func.__name__}: {type(e).__name__}: {e}")
            failed += 1

    print(f"\n{passed} passed, {failed} failed")
    sys.exit(0 if failed == 0 else 1)
