"""Command-line interface for Hearts."""

from __future__ import annotations

from card_games.common.cards import Card, format_cards, parse_card
from card_games.hearts.game import HeartsGame, HeartsPlayer


def display_hand(player: HeartsPlayer) -> None:
    """Display a player's hand.

    Args:
        player: The player whose hand to display
    """
    print(f"\n{player.name}'s hand:")
    print(f"  {format_cards(player.hand)}")


def display_scores(game: HeartsGame) -> None:
    """Display current scores.

    Args:
        game: The Hearts game instance
    """
    print("\n" + "=" * 60)
    print("SCORES")
    print("=" * 60)
    for player in game.players:
        print(f"  {player.name:20} {player.score:3} points")
    print("=" * 60)


def display_trick(game: HeartsGame) -> None:
    """Display the current trick.

    Args:
        game: The Hearts game instance
    """
    if not game.current_trick:
        return

    print("\nCurrent trick:")
    for player, card in game.current_trick:
        print(f"  {player.name:20} played {card}")


def get_cards_to_pass(player: HeartsPlayer, game: HeartsGame) -> list[Card]:
    """Get 3 cards from player to pass.

    Args:
        player: The player passing cards
        game: The Hearts game instance

    Returns:
        List of 3 cards to pass
    """
    if player.is_ai:
        return game.select_cards_to_pass(player)

    display_hand(player)
    print("\nSelect 3 cards to pass (e.g., 'AS KH QD'):")

    while True:
        try:
            card_input = input("Cards: ").strip().upper()
            card_codes = card_input.split()

            if len(card_codes) != 3:
                print("You must select exactly 3 cards.")
                continue

            cards = [parse_card(code) for code in card_codes]

            # Validate cards are in hand
            if all(card in player.hand for card in cards):
                return cards
            else:
                print("One or more cards are not in your hand.")
        except (ValueError, KeyError) as e:
            print(f"Invalid input: {e}")


def get_card_to_play(player: HeartsPlayer, game: HeartsGame) -> Card:
    """Get a card from player to play.

    Args:
        player: The player playing a card
        game: The Hearts game instance

    Returns:
        The card to play
    """
    if player.is_ai:
        return game.select_card_to_play(player)

    valid_plays = game.get_valid_plays(player)
    display_hand(player)
    display_trick(game)
    print(f"\nValid cards to play: {format_cards(valid_plays)}")
    print("Enter card to play (e.g., 'AS'):")

    while True:
        try:
            card_code = input("Card: ").strip().upper()
            card = parse_card(card_code)

            if card in valid_plays:
                return card
            else:
                print("Invalid play. Try again.")
        except (ValueError, KeyError) as e:
            print(f"Invalid input: {e}")


def play_round(game: HeartsGame) -> None:
    """Play one round of Hearts.

    Args:
        game: The Hearts game instance
    """
    # Deal cards
    game.deal_cards()
    game.hearts_broken = False

    print("\n" + "=" * 60)
    print(f"ROUND {game.round_number + 1}")
    print("=" * 60)

    # Passing phase
    pass_direction = game.get_pass_direction()
    print(f"\nPassing direction: {pass_direction.name}")

    if pass_direction.name != "NONE":
        passes = {}
        for player in game.players:
            cards = get_cards_to_pass(player, game)
            passes[player] = cards
            if not player.is_ai:
                print(f"{player.name} is passing: {format_cards(cards)}")

        game.pass_cards(passes)
        print("\nCards have been passed!")

    # Play 13 tricks
    current_player = game.find_starting_player()
    print(f"\n{current_player.name} has the 2♣ and leads the first trick.")

    for trick_num in range(13):
        print(f"\n--- Trick {trick_num + 1} ---")

        # Get the player order starting with current player
        player_idx = game.players.index(current_player)
        play_order = [game.players[(player_idx + i) % 4] for i in range(4)]

        for player in play_order:
            card = get_card_to_play(player, game)
            game.play_card(player, card)
            print(f"{player.name} plays {card}")

        winner = game.complete_trick()
        print(f"\n{winner.name} wins the trick!")
        current_player = winner

    # Calculate scores for this round
    print("\n" + "=" * 60)
    print("ROUND RESULTS")
    print("=" * 60)
    round_scores = game.calculate_scores()

    for player in game.players:
        points = round_scores[player.name]
        if points == 26:
            print(f"  {player.name:20} {points:3} points (others shot the moon)")
        elif points == 0:
            # Check if this player shot the moon
            actual_points = player.calculate_round_points()
            if actual_points == 26:
                print(f"  {player.name:20} SHOT THE MOON! (0 points)")
            else:
                print(f"  {player.name:20} {points:3} points")
        else:
            print(f"  {player.name:20} {points:3} points")

    game.round_number += 1


def game_loop() -> None:
    """Main game loop for Hearts."""
    print("\n" + "=" * 60)
    print("WELCOME TO HEARTS")
    print("=" * 60)
    print("\nGoal: Avoid taking hearts (1 point each) and the Queen of Spades (13 points).")
    print("Or shoot the moon by taking ALL hearts and the Queen!")
    print("First player to reach 100 points loses.\n")

    # Create players
    player_name = input("Enter your name: ").strip() or "Player"
    players = [
        HeartsPlayer(name=player_name, is_ai=False),
        HeartsPlayer(name="AI 1", is_ai=True),
        HeartsPlayer(name="AI 2", is_ai=True),
        HeartsPlayer(name="AI 3", is_ai=True),
    ]

    game = HeartsGame(players)

    # Play rounds until someone reaches 100 points
    while not game.is_game_over():
        play_round(game)
        display_scores(game)

        if not game.is_game_over():
            input("\nPress Enter to continue to next round...")

    # Game over
    winner = game.get_winner()
    print("\n" + "=" * 60)
    print("GAME OVER!")
    print("=" * 60)
    print(f"\nWinner: {winner.name} with {winner.score} points!")
    print("(In Hearts, lowest score wins)")
    display_scores(game)
