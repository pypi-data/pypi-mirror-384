"""Command-line interface for the Cribbage card game."""

from __future__ import annotations

from itertools import combinations
from typing import Sequence

from card_games.common.cards import RANK_TO_VALUE, Card, Deck
from card_games.cribbage.ai import choose_pegging_card, select_discards
from card_games.cribbage.game import CribbageGame, GamePhase


def format_cards(cards: Sequence[Card]) -> str:
    """Return a comma separated representation of ``cards``."""

    return ", ".join(str(card) for card in cards)


def print_scoreboard(game: CribbageGame) -> None:
    """Print the running scores and dealer."""

    state = game.get_state_summary()
    print(f"Scoreboard → Player 1: {state['player1_score']} pts | " f"Player 2: {state['player2_score']} pts (Dealer: Player {state['dealer']})")


def cut_for_first_deal() -> int:
    """Determine the first dealer by cutting cards."""

    print("\nCutting for the first deal...")
    while True:
        deck = Deck()
        deck.shuffle()
        p1_card, p2_card = deck.deal(2)
        print(f"Player 1 cuts {p1_card}, Player 2 cuts {p2_card}")
        v1 = RANK_TO_VALUE[p1_card.rank]
        v2 = RANK_TO_VALUE[p2_card.rank]
        if v1 == v2:
            print("Tie on the cut – cutting again!\n")
            continue
        dealer = 1 if v1 > v2 else 2  # high card loses the cut
        print(f"Player {dealer} deals first.\n")
        return dealer


def prompt_discard_choice(hand: list[Card]) -> list[Card]:
    """Prompt the player to choose two cards to discard to the crib."""

    options = list(combinations(range(len(hand)), 2))
    while True:
        print("\nChoose two cards to discard:")
        for idx, (i1, i2) in enumerate(options, 1):
            print(f"  {idx}. {hand[i1]} + {hand[i2]}")
        choice = input(f"Select option (1-{len(options)}): ").strip()
        if not choice.isdigit():
            print("Please enter a number.")
            continue
        selection = int(choice)
        if 1 <= selection <= len(options):
            i1, i2 = options[selection - 1]
            chosen = [hand[i1], hand[i2]]
            print(f"You discard {format_cards(chosen)} to the crib.")
            return chosen
        print("Invalid option. Try again.")


def display_pegging_history(game: CribbageGame) -> None:
    """Display the pegging history to date."""

    state = game.get_state_summary()
    history = state["pegging_history"]
    if not history:
        print("\nPegging begins. Count is 0.")
        return

    print("\nPegging history:")
    current_sequence = None
    for entry in history:
        if entry["sequence"] != current_sequence:
            current_sequence = entry["sequence"]
            print(f"  Sequence {current_sequence + 1}:")
        if entry["type"] == "starter":
            print("    Starter card: {card} → dealer scores 2.".format(card=entry["card"]))
        elif entry["type"] == "play":
            line = f"    Player {entry['player']} played {entry['card']} " f"(count {entry['count']})"
            if entry["events"]:
                line += " → " + ", ".join(entry["events"])
            if entry["points"]:
                line += f" [{entry['points']} pts]"
            print(line)
        elif entry["type"] == "go":
            msg = f"    Player {entry['player']} said Go."
            if entry["awarded_to"] is not None and entry["points"]:
                msg += f" Player {entry['awarded_to']} scores {entry['points']}."
            print(msg)


def check_skunk_line(previous: tuple[int, int], game: CribbageGame) -> None:
    """Report when a player crosses the 61/91 point skunk lines."""

    p1_before, p2_before = previous
    if p1_before < 61 <= game.player1_score:
        print("🎯 Player 1 crosses the double-skunk line (61 points).")
    if p2_before < 61 <= game.player2_score:
        print("🎯 Player 2 crosses the double-skunk line (61 points).")
    if p1_before < 91 <= game.player1_score:
        print("🎯 Player 1 crosses the skunk line (91 points).")
    if p2_before < 91 <= game.player2_score:
        print("🎯 Player 2 crosses the skunk line (91 points).")


def announce_play(game: CribbageGame, player: int, card: Card, result: dict[str, object]) -> None:
    """Announce a pegging play and update the scoreboard display."""

    print(f"\nPlayer {player} plays {card} → count {result['count']}")
    for event in result.get("events", []):
        print(f"  · {event}")
    if result.get("points", 0):
        print(f"  · Player {player} scores {result['points']} points.")
    if result.get("sequence_end"):
        print("  · Sequence complete – count resets to 0.")
    print_scoreboard(game)


def announce_go(game: CribbageGame, player: int, result: dict[str, object]) -> None:
    """Announce a go action."""

    print(f"\nPlayer {player} says 'Go'.")
    if result.get("awarded"):
        awarded_to = result.get("awarded_to")
        print(f"  · Player {awarded_to} scores {result['awarded']} point for go.")
    if result.get("sequence_end"):
        print("  · Sequence complete – count resets to 0.")
    next_player = result.get("next_player")
    if next_player:
        print(f"  · Next to play: Player {next_player}")
    print_scoreboard(game)


def summarize_hand(hand: Sequence[Card], starter: Card, is_crib: bool) -> list[str]:
    """Return human-readable scoring contributions for ``hand``."""

    cards = list(hand) + [starter]
    contributions = []
    fifteens = CribbageGame._score_fifteens(cards)
    if fifteens:
        contributions.append(f"Fifteens: {fifteens}")
    pairs = CribbageGame._score_pairs(cards)
    if pairs:
        contributions.append(f"Pairs: {pairs}")
    runs = CribbageGame._score_runs(cards)
    if runs:
        contributions.append(f"Runs: {runs}")
    flush = CribbageGame._score_flush(hand, starter, is_crib)
    if flush:
        contributions.append(f"Flush: {flush}")
    nobs = CribbageGame._score_nobs(hand, starter)
    if nobs:
        contributions.append(f"His nobs: {nobs}")
    return contributions


def handle_discard_phase(game: CribbageGame) -> tuple[list[Card], list[Card]]:
    """Run the discard phase and return snapshots of each hand."""

    print_scoreboard(game)
    print("\nPlayer 1 hand:")
    for idx, card in enumerate(game.player1_hand, 1):
        print(f"  {idx}. {card}")
    player_discards = prompt_discard_choice(game.player1_hand)
    game.discard_to_crib(1, player_discards)

    ai_discards = select_discards(
        game.player2_hand,
        is_dealer=game.dealer == 2,
        deck_cards=game.remaining_deck(),
    )
    game.discard_to_crib(2, ai_discards)
    print("Player 2 discards two cards to the crib.")

    display_pegging_history(game)
    print_scoreboard(game)

    return list(game.player1_hand), list(game.player2_hand)


def handle_pegging_phase(game: CribbageGame) -> bool:
    """Play the pegging phase. Return True if the game ends."""

    while game.phase == GamePhase.PLAY and game.phase != GamePhase.GAME_OVER:
        display_pegging_history(game)
        if game.current_player == 1:
            playable = game.legal_plays(1)
            if not playable:
                prev = (game.player1_score, game.player2_score)
                go_result = game.player_go(1)
                announce_go(game, 1, go_result)
                check_skunk_line(prev, game)
                if game.phase == GamePhase.GAME_OVER:
                    return True
                continue

            print("\nYour cards:")
            for idx, card in enumerate(game.player1_hand, 1):
                playable_marker = "(playable)" if card in playable else ""
                print(f"  {idx}. {card} {playable_marker}")
            choice = input("Choose a card to play or 'g' to say go: ").strip().lower()
            if choice == "g":
                prev = (game.player1_score, game.player2_score)
                go_result = game.player_go(1)
                announce_go(game, 1, go_result)
                check_skunk_line(prev, game)
                if game.phase == GamePhase.GAME_OVER:
                    return True
                continue
            if not choice.isdigit():
                print("Please enter a number or 'g'.")
                continue
            index = int(choice) - 1
            if index < 0 or index >= len(game.player1_hand):
                print("Invalid card selection.")
                continue
            card = game.player1_hand[index]
            if card not in playable:
                print("That card would exceed 31 – pick a different card or say go.")
                continue
            prev = (game.player1_score, game.player2_score)
            result = game.play_card(1, card)
            announce_play(game, 1, card, result)
            check_skunk_line(prev, game)
            if result.get("game_over"):
                return True
        else:
            card = choose_pegging_card(game, 2)
            if card is None:
                prev = (game.player1_score, game.player2_score)
                go_result = game.player_go(2)
                announce_go(game, 2, go_result)
                check_skunk_line(prev, game)
                if game.phase == GamePhase.GAME_OVER:
                    return True
                continue
            prev = (game.player1_score, game.player2_score)
            result = game.play_card(2, card)
            announce_play(game, 2, card, result)
            check_skunk_line(prev, game)
            if result.get("game_over"):
                return True

    return game.phase == GamePhase.GAME_OVER


def handle_show_phase(game: CribbageGame, player1_show: Sequence[Card], player2_show: Sequence[Card]) -> None:
    """Score hands and crib for the show phase."""

    starter = game.starter
    assert starter is not None

    print("\n" + "=" * 60)
    print("THE SHOW")
    print("=" * 60)

    prev = (game.player1_score, game.player2_score)
    p1_points = game.score_hand(list(player1_show))
    game._award_points(1, p1_points)
    print(f"Player 1 hand: {format_cards(player1_show)} + {starter} → {p1_points} points")
    for line in summarize_hand(player1_show, starter, is_crib=False):
        print(f"  · {line}")
    check_skunk_line(prev, game)
    print_scoreboard(game)

    prev = (game.player1_score, game.player2_score)
    p2_points = game.score_hand(list(player2_show))
    game._award_points(2, p2_points)
    print(f"Player 2 hand: {format_cards(player2_show)} + {starter} → {p2_points} points")
    for line in summarize_hand(player2_show, starter, is_crib=False):
        print(f"  · {line}")
    check_skunk_line(prev, game)
    print_scoreboard(game)

    prev = (game.player1_score, game.player2_score)
    crib_points = game.score_hand(list(game.crib), is_crib=True)
    crib_owner = game.dealer
    game._award_points(crib_owner, crib_points)
    owner_label = "Player 1" if crib_owner == 1 else "Player 2"
    print(f"Crib ({owner_label}): {format_cards(game.crib)} + {starter} → {crib_points} points")
    for line in summarize_hand(game.crib, starter, is_crib=True):
        print(f"  · {line}")
    check_skunk_line(prev, game)
    print_scoreboard(game)

    if game.phase == GamePhase.GAME_OVER:
        return

    next_dealer = 2 if game.dealer == 1 else 1
    print(f"\nDealer passes to Player {next_dealer}.")
    game.start_new_hand(dealer=next_dealer)


def describe_skunk(winner: int, game: CribbageGame) -> None:
    """Describe skunk results at the end of the match."""

    loser_score = game.player2_score if winner == 1 else game.player1_score
    if loser_score <= 60:
        print("💥 Double skunk! Winner earns two games.")
    elif loser_score <= 90:
        print("💥 Skunk! Winner earns an extra game.")


def game_loop(game: CribbageGame) -> None:
    """Play an interactive game of Cribbage in the terminal."""

    print("\n🎴 Welcome to Cribbage! 🎴")
    print("First to 121 points wins. Good luck!\n")

    dealer = cut_for_first_deal()
    game.start_new_hand(dealer=dealer)

    player1_show: list[Card] = []
    player2_show: list[Card] = []

    while game.phase != GamePhase.GAME_OVER:
        if game.phase == GamePhase.DISCARD:
            player1_show, player2_show = handle_discard_phase(game)
        if game.phase == GamePhase.PLAY and handle_pegging_phase(game):
            break
        if game.phase == GamePhase.SHOW:
            handle_show_phase(game, player1_show, player2_show)

    print("\n" + "=" * 60)
    print("GAME OVER")
    print("=" * 60)
    winner = game.winner or (1 if game.player1_score >= game.player2_score else 2)
    print(f"🎉 Player {winner} wins!")
    print(f"Final Score → Player 1: {game.player1_score} | Player 2: {game.player2_score}")
    describe_skunk(winner, game)
    print("=" * 60)
