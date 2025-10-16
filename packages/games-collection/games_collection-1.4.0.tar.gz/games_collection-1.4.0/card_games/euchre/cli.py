"""Command-line interface for the Euchre card game."""

from __future__ import annotations

from typing import Dict, Iterable, List

from card_games.common.cards import Card, Suit
from card_games.euchre.ai import BasicEuchreAI
from card_games.euchre.game import EuchreGame, GamePhase


def display_game_state(game: EuchreGame) -> None:
    """Display the current high-level game state.

    Args:
        game: The active Euchre game instance.

    Returns:
        None.

    Raises:
        None.
    """

    state = game.get_state_summary()
    print("\n" + "=" * 60)
    print(f"EUCHRE - {state['phase']}")
    print("=" * 60)
    print(f"Team 1 (Players 0 & 2): {state['team1_score']} points")
    print(f"Team 2 (Players 1 & 3): {state['team2_score']} points")
    print(f"Dealer: Player {state['dealer']}")
    if state["up_card"]:
        print(f"Up card: {state['up_card']}")
    if state["trump"]:
        print(f"Trump: {state['trump']} (Team {state['maker']} is the maker)")
    if state["going_alone"]:
        print(f"Player {game.alone_player} is going alone!")
    if state["defending_alone_player"] is not None:
        print(f"Defender {state['defending_alone_player']} is defending alone.")
    print("=" * 60)


def prompt_yes_no(prompt: str) -> bool:
    """Return ``True`` if the user confirms with yes.

    Args:
        prompt: Prompt text to present to the user.

    Returns:
        bool: ``True`` when the user confirms with yes, ``False`` otherwise.

    Raises:
        None.
    """

    while True:
        answer = input(f"{prompt} [y/n]: ").strip().lower()
        if answer in {"y", "yes"}:
            return True
        if answer in {"n", "no"}:
            return False
        print("Please respond with 'y' or 'n'.")


def format_cards(cards: Iterable[Card]) -> str:
    """Return a human readable representation of the provided cards.

    Args:
        cards: Collection of cards to render.

    Returns:
        str: Comma separated string of card faces.

    Raises:
        None.
    """

    return ", ".join(str(card) for card in cards)


def prompt_for_card(cards: List[Card], legal_cards: List[Card], action: str) -> Card:
    """Prompt the human player to select a card from the legal options.

    Args:
        cards: Cards available to the player.
        legal_cards: Subset of playable cards obeying follow-suit.
        action: Description of the requested action (play/discard).

    Returns:
        Card: The selected card.

    Raises:
        None.
    """

    legal_set = set(legal_cards)
    print(f"Available cards: {format_cards(cards)}")
    print(f"Legal options: {format_cards(legal_cards)}")
    while True:
        choice = input(f"Select a card to {action} (enter index 1-{len(cards)}): ")
        if not choice.isdigit():
            print("Please enter a number corresponding to your card selection.")
            continue
        index = int(choice) - 1
        if index < 0 or index >= len(cards):
            print("That selection is out of range.")
            continue
        selected = cards[index]
        if selected not in legal_set:
            print("You must follow suit when possible. Choose a legal card.")
            continue
        return selected


def handle_defender_alone(game: EuchreGame, ai_players: Dict[int, BasicEuchreAI]) -> None:
    """Offer the defending team the option to defend alone.

    Args:
        game: The active Euchre game instance.
        ai_players: Mapping of seat index to AI helper for non-human players.

    Returns:
        None.

    Raises:
        None.
    """

    if game.maker is None or game.trump is None:
        return

    defending_players = [p for p in range(4) if (1 if p in {0, 2} else 2) != game.maker]
    for player in defending_players:
        if game.defending_alone_player is not None:
            break
        if player == 0:
            if prompt_yes_no("Would you like to defend alone?"):
                game.set_defending_alone(player)
                print("Player 0's partner will sit out on defence!")
                break
        else:
            ai = ai_players[player]
            if game.trump and ai.evaluate_hand_strength(game.hands[player], game.trump) >= 18.5:
                game.set_defending_alone(player)
                print(f"Player {player} defends alone.")
                break


def bidding_phase(game: EuchreGame, ai_players: Dict[int, BasicEuchreAI]) -> None:
    """Resolve the two-round euchre bidding process.

    Args:
        game: The active Euchre game instance.
        ai_players: Mapping of AI helpers controlling non-human seats.

    Returns:
        None.

    Raises:
        None.
    """

    up_card = game.up_card
    if up_card is None:
        return

    order = [((game.dealer + offset) % 4) for offset in range(1, 5)]

    # Round one: ordering up the turned card
    for player in order:
        if game.phase != GamePhase.BIDDING:
            break
        if player == 0:
            print(f"Your hand: {format_cards(game.hands[player])}")
            if prompt_yes_no(f"Order up {up_card} as trump?"):
                go_alone = prompt_yes_no("Go alone and sit partner out?")
                game.select_trump(up_card.suit, player, go_alone=go_alone, require_dealer_pickup=True)
                print(f"Player {player} orders up {up_card.suit}.")
        else:
            ai = ai_players[player]
            if ai.should_order_up(game.hands[player], up_card, game.dealer, player):
                go_alone = False
                if ai.evaluate_hand_strength(game.hands[player], up_card.suit) >= 21.0:
                    go_alone = True
                game.select_trump(up_card.suit, player, go_alone=go_alone, require_dealer_pickup=True)
                print(f"Player {player} orders up {up_card.suit}.")
        if game.phase != GamePhase.BIDDING:
            break

    if game.phase != GamePhase.BIDDING:
        return

    # Round two: naming trump
    forbidden = up_card.suit
    for player in order:
        is_dealer = player == game.dealer
        if game.phase != GamePhase.BIDDING:
            break
        if player == 0:
            print(f"Your hand: {format_cards(game.hands[player])}")
            print("Suits available to call:")
            options = [suit for suit in Suit if suit != forbidden]
            for idx, suit in enumerate(options, start=1):
                print(f"  {idx}. {suit.value}")
            choice = input("Choose a suit number or press Enter to pass: ").strip()
            if not choice:
                if is_dealer:
                    print("As dealer you must choose a trump suit.")
                else:
                    continue
            suit_choice: Suit | None = None
            if choice.isdigit() and 1 <= int(choice) <= len(options):
                suit_choice = options[int(choice) - 1]
            if suit_choice is None:
                if is_dealer:
                    suit_choice = options[0]
                else:
                    print("Passing.")
                    continue
            go_alone = prompt_yes_no("Go alone and sit partner out?")
            game.select_trump(suit_choice, player, go_alone=go_alone)
            print(f"Player {player} names {suit_choice} as trump.")
        else:
            ai = ai_players[player]
            trump_choice = ai.choose_trump(game.hands[player], forbidden)
            if trump_choice is None and is_dealer:
                trump_choice = next(suit for suit in Suit if suit != forbidden)
            if trump_choice is None:
                continue
            go_alone = ai.evaluate_hand_strength(game.hands[player], trump_choice) >= 21.0
            game.select_trump(trump_choice, player, go_alone=go_alone)
            print(f"Player {player} names {trump_choice} as trump.")

    if game.phase == GamePhase.BIDDING:
        print("Everyone passed twice. Redealing...")
        game.redeal()
        for ai in ai_players.values():
            ai.reset_for_new_hand()


def handle_dealer_pickup(game: EuchreGame, ai_players: Dict[int, BasicEuchreAI]) -> None:
    """Assist the dealer in discarding after being ordered up.

    Args:
        game: The active Euchre game instance.
        ai_players: Mapping of seat index to AI helpers.

    Returns:
        None.

    Raises:
        None.
    """

    dealer = game.dealer
    up_card = game.up_card
    if up_card is None or game.trump is None:
        return

    if dealer == 0:
        print(f"Dealer pickup required. Up card: {up_card}")
        extended = game.hands[dealer] + [up_card]
        discard = prompt_for_card(extended, extended, "discard")
        game.dealer_pickup(discard)
        print(f"You discard {discard} and pick up {up_card}.")
    else:
        ai = ai_players[dealer]
        discard = ai.choose_discard(game.hands[dealer][:], up_card, game.trump)
        game.dealer_pickup(discard)
        print(f"Dealer {dealer} discards {discard} and picks up {up_card}.")


def play_phase(game: EuchreGame, ai_players: Dict[int, BasicEuchreAI]) -> None:
    """Run the trick-taking play loop for a single trick/card.

    Args:
        game: The active Euchre game instance.
        ai_players: Mapping of seat index to AI helpers.

    Returns:
        None.

    Raises:
        AssertionError: If the play phase starts without a trump suit.
    """

    player = game.current_player
    hand = game.hands[player]
    legal_cards = game.get_legal_cards(player)

    assert game.trump is not None

    if player == 0:
        print(f"Your hand: {format_cards(hand)}")
        card_to_play = prompt_for_card(hand, legal_cards, "play")
    else:
        lead_card = game.current_trick[0][1] if game.current_trick else None
        card_to_play = ai_players[player].choose_card(hand, lead_card, game.trump)
    result = game.play_card(player, card_to_play)
    for ai in ai_players.values():
        ai.record_card(card_to_play)
    if result["success"]:
        print(f"Player {player} plays {card_to_play}.")
    if result.get("trick_complete"):
        winner = result.get("trick_winner")
        if winner is not None:
            print(f"Player {winner} wins the trick.")
    input("Press Enter to continue...")


def game_loop(game: EuchreGame) -> None:
    """Main game loop for the Euchre CLI.

    Args:
        game: The Euchre game engine to drive.

    Returns:
        None.

    Raises:
        None.
    """

    print("\n🂡 Welcome to Euchre! 🂡")
    print("Four players in partnerships: Team 1 (0 & 2) vs Team 2 (1 & 3)")
    print("First partnership to 10 points wins!\n")

    ai_players: Dict[int, BasicEuchreAI] = {1: BasicEuchreAI(), 2: BasicEuchreAI(), 3: BasicEuchreAI()}

    while game.phase != GamePhase.GAME_OVER:
        display_game_state(game)

        if game.phase == GamePhase.BIDDING:
            for ai in ai_players.values():
                ai.reset_for_new_hand()
            bidding_phase(game, ai_players)
            if game.phase == GamePhase.PLAY:
                handle_defender_alone(game, ai_players)
        elif game.phase == GamePhase.DEALER_DISCARD:
            handle_dealer_pickup(game, ai_players)
            if game.phase == GamePhase.PLAY:
                handle_defender_alone(game, ai_players)
        elif game.phase == GamePhase.PLAY:
            play_phase(game, ai_players)

    state = game.get_state_summary()
    print("\n" + "=" * 60)
    print("GAME OVER")
    print("=" * 60)
    print(f"🎉 Team {state['winner']} wins!")
    print(f"Final Score: Team 1: {state['team1_score']}, Team 2: {state['team2_score']}")
    print("=" * 60)
