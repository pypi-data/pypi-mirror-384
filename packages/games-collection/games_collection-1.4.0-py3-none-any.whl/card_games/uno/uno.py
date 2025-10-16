"""A comprehensive implementation of the card game Uno.

This module provides the core logic for a game of Uno, designed to be versatile
enough to support both a command-line interface (CLI) and a graphical user
interface (GUI). It includes classes for cards, decks, players, and the main
game engine, as well as a protocol for abstracting the user interface.

Key Components:
- **UnoCard**: Represents a single Uno card with a color and value.
- **UnoDeck**: Manages the deck of cards, including shuffling and drawing.
- **UnoPlayer**: Represents a player, holding a hand of cards and making decisions.
- **UnoGame**: The main game engine that orchestrates the game flow, rules, and
  player interactions.
- **UnoInterface**: A protocol defining the methods required for a user interface,
  allowing for different front-ends to be swapped in.
- **ConsoleUnoInterface**: A concrete implementation of the `UnoInterface` for
  playing the game in the console.
"""

from __future__ import annotations

import argparse
import random
from dataclasses import dataclass
from typing import Iterable, List, Optional, Protocol, Sequence

from colorama import Fore, Style
from colorama import init as colorama_init

# Initialize colorama for cross-platform colored terminal text.
colorama_init(autoreset=True)

# Define the standard colors, numbers, and special values for Uno cards.
COLORS = ("red", "yellow", "green", "blue")
NUMBER_VALUES = tuple(str(n) for n in range(10))
ACTION_VALUES = ("skip", "reverse", "+2")
WILD_VALUES = ("wild", "+4")
BOT_PERSONALITIES = ("easy", "balanced", "aggressive")

# Map colors to their colorama styles for terminal output.
COLOR_STYLE_MAP = {
    "red": Fore.RED,
    "yellow": Fore.YELLOW,
    "green": Fore.GREEN,
    "blue": Fore.BLUE,
}


def colorize_color(color: str) -> str:
    """Return a colorized string for a given color name."""
    style = COLOR_STYLE_MAP.get(color.lower(), Fore.WHITE)
    return f"{style}{color.capitalize()}{Style.RESET_ALL}"


def format_card(card: "UnoCard", *, emphasize: bool = False) -> str:
    """Return a formatted, colorized string representation of a card."""
    base = card.label()
    style = COLOR_STYLE_MAP.get(card.color, Fore.WHITE) if card.color else Fore.MAGENTA
    weight = Style.BRIGHT if emphasize else ""
    return f"{weight}{style}{base}{Style.RESET_ALL}"


def format_highlight(message: str, color: str, *, style: str = "") -> str:
    """Return a highlighted message string."""
    return f"{style}{color}{message}{Style.RESET_ALL}"


def format_section_heading(message: str) -> str:
    """Return a formatted section heading."""
    return format_highlight(message, Fore.CYAN, style=Style.BRIGHT)


@dataclass(frozen=True)
class UnoCard:
    """Represents a single, immutable Uno card.

    Attributes:
        color: The color of the card (e.g., "red"), or None for wild cards.
        value: The value of the card (e.g., "7", "skip", "+4").
    """

    color: Optional[str]
    value: str

    def is_wild(self) -> bool:
        """Return True if the card is a wild card."""
        return self.color is None

    def is_action(self) -> bool:
        """Return True if the card is an action card (e.g., skip, +2)."""
        return self.value in ACTION_VALUES or self.value in WILD_VALUES

    def matches(self, active_color: str, active_value: str) -> bool:
        """Check if this card can be played on the given active card."""
        return self.is_wild() or self.color == active_color or self.value == active_value

    def label(self) -> str:
        """Return a human-friendly label for the card."""
        if self.color is None:
            return "Wild +4" if self.value == "+4" else "Wild"
        color_name = self.color.capitalize()
        return f"{color_name} {self.value.capitalize()}" if self.value in {"skip", "reverse"} else f"{color_name} {self.value}"

    def __str__(self) -> str:
        """Return a compact string representation of the card."""
        if self.color is None:
            return self.label()
        return f"{self.color[0].upper()}-{self.value.upper()}"


class UnoDeck:
    """A mutable deck of Uno cards that can be shuffled and drawn from."""

    def __init__(self, *, rng: Optional[random.Random] = None) -> None:
        self._rng = rng or random.Random()
        self.cards: List[UnoCard] = []
        self.populate()
        self.shuffle()

    def populate(self) -> None:
        """Fill the deck with a standard set of 108 Uno cards."""
        self.cards.clear()
        for color in COLORS:
            # Every colour has a single zero card and two of every other
            # number/action card, mirroring the physical Uno deck.
            self.cards.append(UnoCard(color, "0"))
            for value in NUMBER_VALUES[1:] + ACTION_VALUES:
                self.cards.extend([UnoCard(color, value), UnoCard(color, value)])
        for _ in range(4):
            # Wilds do not have a colour and appear four times each.
            self.cards.extend([UnoCard(None, "wild"), UnoCard(None, "+4")])

    def shuffle(self) -> None:
        """Shuffle the deck in place."""
        self._rng.shuffle(self.cards)

    def draw(self) -> UnoCard:
        """Draw a single card from the top of the deck."""
        if not self.cards:
            raise RuntimeError("The deck is empty")
        # ``pop`` models drawing the top-most card from the pile.
        return self.cards.pop()

    def extend(self, cards: Iterable[UnoCard]) -> None:
        """Add cards to the deck and reshuffle."""
        self.cards.extend(cards)
        self.shuffle()

    def __len__(self) -> int:
        return len(self.cards)


class UnoPlayer:
    """Represents a human or bot player in an Uno game.

    Attributes:
        name (str): The player's name.
        is_human (bool): True if the player is controlled by a human.
        personality (str): A string defining the bot's play style.
        hand (List[UnoCard]): The cards currently held by the player.
        pending_uno (bool): True if the player has one card but has not yet declared "Uno!".
        team (Optional[int]): Team number for team play mode (None for no teams).
    """

    def __init__(self, name: str, *, is_human: bool = False, personality: str = "balanced", team: Optional[int] = None) -> None:
        self.name = name
        self.is_human = is_human
        self.personality = personality
        self.hand: List[UnoCard] = []
        self.pending_uno = False
        self.team = team

    def draw_cards(self, deck: UnoDeck, count: int) -> List[UnoCard]:
        """Draw a specified number of cards from the deck."""
        drawn = [deck.draw() for _ in range(count)]
        self.hand.extend(drawn)
        self.pending_uno = False
        return drawn

    def take_card(self, card: UnoCard) -> None:
        """Add a single card to the player's hand."""
        self.hand.append(card)
        self.pending_uno = False

    def pop_card(self, index: int) -> UnoCard:
        """Remove and return a card from the hand at the given index."""
        card = self.hand.pop(index)
        if len(self.hand) != 1:
            self.pending_uno = False
        return card

    def has_cards(self) -> bool:
        """Return True if the player has any cards in their hand."""
        return bool(self.hand)

    def playable_cards(
        self,
        active_color: str,
        active_value: str,
        *,
        penalty_value: Optional[str] = None,
    ) -> List[int]:
        """Return a list of indices of playable cards in the hand."""
        if penalty_value:
            return [i for i, card in enumerate(self.hand) if card.value == penalty_value]
        return [i for i, card in enumerate(self.hand) if card.matches(active_color, active_value)]

    def choose_card(self, playable: Sequence[int], active_color: str) -> Optional[int]:
        """AI logic for a bot to choose the best card to play."""
        if not playable:
            return None

        def score(card: UnoCard) -> float:
            # A simple scoring heuristic for card selection.
            base = 0.0
            if card.color == active_color:
                base += 2.0
            if card.is_action():
                base += 2.0 if self.personality == "aggressive" else 1.0
            if card.is_wild():
                base += 1.5
            if card.color:
                base += sum(1 for c in self.hand if c.color == card.color) / 10.0
            return base

        return max(playable, key=lambda idx: score(self.hand[idx]))

    def preferred_color(self) -> str:
        """Determine the bot's preferred color to switch to after playing a wild."""
        color_counts = {color: sum(1 for card in self.hand if card.color == color) for color in COLORS}
        max_count = max(color_counts.values()) if color_counts else 0
        top_colors = [color for color, count in color_counts.items() if count == max_count]
        # Break ties randomly so the bots do not behave identically.
        return random.choice(top_colors) if top_colors else random.choice(COLORS)

    def __str__(self) -> str:
        return self.name


@dataclass
class HouseRules:
    """Configuration for house rules variants.

    Attributes:
        stacking: Allow stacking +2 and +4 cards to increase penalty.
        jump_in: Allow players to play identical cards (same color AND value) out of turn,
                 interrupting the normal turn order. Players are checked clockwise from
                 the current player, and the first to accept jumps in.
        seven_zero_swap: Playing 7 swaps hands with another player, playing 0 rotates all hands.
    """

    stacking: bool = False
    jump_in: bool = False
    seven_zero_swap: bool = False


@dataclass
class PlayerDecision:
    """Represents a decision made by a player during their turn."""

    action: str
    card_index: Optional[int] = None
    declare_uno: bool = False
    chosen_color: Optional[str] = None
    swap_target: Optional[int] = None  # For 7-0 swapping rule


class UnoInterface(Protocol):
    """A protocol defining the interface between the game engine and a UI.

    This abstraction allows the `UnoGame` to be independent of the presentation
    layer, whether it's a console, a GUI, or another interface.
    """

    def show_heading(self, message: str) -> None: ...
    def show_message(self, message: str, *, color: str = Fore.WHITE, style: str = "") -> None: ...
    def show_hand(self, player: UnoPlayer, formatted_cards: Sequence[str]) -> None: ...
    def choose_action(
        self,
        game: "UnoGame",
        player: UnoPlayer,
        playable: Sequence[int],
        penalty_active: bool,
    ) -> PlayerDecision: ...
    def handle_drawn_card(self, game: "UnoGame", player: UnoPlayer, card: UnoCard) -> PlayerDecision: ...
    def choose_color(self, player: UnoPlayer) -> str: ...
    def choose_swap_target(self, player: UnoPlayer, players: Sequence[UnoPlayer]) -> int: ...
    def prompt_challenge(self, challenger: UnoPlayer, target: UnoPlayer, *, bluff_possible: bool) -> bool: ...
    def notify_uno_called(self, player: UnoPlayer) -> None: ...
    def notify_uno_penalty(self, player: UnoPlayer) -> None: ...
    def announce_winner(self, winner: UnoPlayer) -> None: ...
    def update_status(self, game: "UnoGame") -> None: ...
    def render_card(self, card: UnoCard, *, emphasize: bool = False) -> str: ...
    def render_color(self, color: str) -> str: ...
    def play_sound(self, sound_type: str) -> None: ...  # Hook for sound effects
    def prompt_jump_in(self, player: UnoPlayer, card: UnoCard) -> bool: ...  # Ask if player wants to jump in


class ConsoleUnoInterface(UnoInterface):
    """An implementation of `UnoInterface` for playing the game in the console."""

    def show_heading(self, message: str) -> None:
        print(format_section_heading(message))

    def show_message(self, message: str, *, color: str = Fore.WHITE, style: str = "") -> None:
        print(format_highlight(message, color, style=style))

    def show_hand(self, player: UnoPlayer, formatted_cards: Sequence[str]) -> None:
        print(format_section_heading("Your hand:"))
        for i, card_str in enumerate(formatted_cards, 1):
            print(f"  {i}) {card_str}")

    def choose_action(
        self,
        game: "UnoGame",
        player: UnoPlayer,
        playable: Sequence[int],
        penalty_active: bool,
    ) -> PlayerDecision:
        """Prompt the human player for their action."""
        while True:
            prompt = "Choose card to play or type 'draw': "
            if penalty_active:
                prompt = "Stack a penalty card or type 'accept': "
            elif not playable:
                prompt = "No playable cards, type 'draw': "

            choice = input(prompt).strip().lower()
            tokens = choice.replace("-", " ").split()
            declare_uno = "uno" in tokens
            tokens = [t for t in tokens if t != "uno"]

            if not tokens:
                if declare_uno:
                    print("Declare UNO with the card you wish to play.")
                continue

            action = tokens[0]
            if penalty_active and action in {"accept", "draw"}:
                return PlayerDecision(action="accept_penalty")
            if action in {"draw", "d"}:
                return PlayerDecision(action="draw")
            if action.isdigit():
                card_idx = int(action) - 1
                swap_target = None
                # Check if playing a 7 with seven_zero_swap rule
                if game.house_rules.seven_zero_swap and 0 <= card_idx < len(player.hand) and player.hand[card_idx].value == "7":
                    swap_target = self.choose_swap_target(player, game.players)
                return PlayerDecision(action="play", card_index=card_idx, declare_uno=declare_uno, swap_target=swap_target)

            self.show_message("Invalid selection. Try again.", color=Fore.RED)

    def handle_drawn_card(self, game: "UnoGame", player: UnoPlayer, card: UnoCard) -> PlayerDecision:
        """Ask the player if they want to play the card they just drew."""
        if card.matches(game.active_color, game.active_value):
            while True:
                response = input("Play the drawn card? (y/n): ").strip().lower()
                if response in {"y", "yes"}:
                    declare = len(player.hand) == 2 and input("Declare UNO? (y/n): ").strip().lower() == "y"
                    return PlayerDecision(
                        action="play",
                        card_index=len(player.hand) - 1,
                        declare_uno=declare,
                    )
                if response in {"n", "no", ""}:
                    break
                self.show_message("Please answer 'y' or 'n'.", color=Fore.RED)
        return PlayerDecision(action="skip")

    def choose_color(self, player: UnoPlayer) -> str:
        """Prompt the player to choose a color after playing a wild card."""
        while True:
            choice = input("Choose a color (red, yellow, green, blue): ").strip().lower()
            if choice in COLORS:
                return choice
            self.show_message("Invalid color. Please choose one of the four.", color=Fore.RED)

    def choose_swap_target(self, player: UnoPlayer, players: Sequence[UnoPlayer]) -> int:
        """Prompt the player to choose another player to swap hands with."""
        print(format_section_heading("Choose a player to swap hands with:"))
        valid_targets = [i for i, p in enumerate(players) if p != player]
        for i in valid_targets:
            print(f"  {i + 1}) {players[i].name} ({len(players[i].hand)} cards)")

        while True:
            choice = input("Enter player number: ").strip()
            if choice.isdigit():
                idx = int(choice) - 1
                if idx in valid_targets:
                    return idx
            self.show_message("Invalid selection. Try again.", color=Fore.RED)

    def prompt_challenge(self, challenger: UnoPlayer, target: UnoPlayer, *, bluff_possible: bool) -> bool:
        """Ask a player if they want to challenge a +4 card."""
        prompt = f"{challenger.name}, challenge {target.name}'s +4? [y/N]: "
        if not bluff_possible:
            prompt = f"{challenger.name}, challenge {target.name}'s +4? (unlikely to help) [y/N]: "
        return input(prompt).strip().lower() in {"y", "yes"}

    def notify_uno_called(self, player: UnoPlayer) -> None:
        self.show_message(f"{player.name} calls UNO!", color=Fore.CYAN, style=Style.BRIGHT)

    def notify_uno_penalty(self, player: UnoPlayer) -> None:
        self.show_message(
            f"{player.name} failed to call UNO and must draw two cards!",
            color=Fore.RED,
            style=Style.BRIGHT,
        )

    def announce_winner(self, winner: UnoPlayer) -> None:
        msg = f"\n{winner.name} wins the game! {'Congratulations!' if winner.is_human else 'Better luck next time.'}"
        self.show_message(msg, color=Fore.CYAN, style=Style.BRIGHT)

    def update_status(self, game: "UnoGame") -> None:
        pass  # The console interface updates reactively.

    def render_card(self, card: UnoCard, *, emphasize: bool = False) -> str:
        return format_card(card, emphasize=emphasize)

    def render_color(self, color: str) -> str:
        return colorize_color(color)

    def play_sound(self, sound_type: str) -> None:
        """Play a sound effect (no-op for console interface)."""
        pass  # Console doesn't play sounds

    def prompt_jump_in(self, player: UnoPlayer, card: UnoCard) -> bool:
        """Ask if player wants to jump in with an identical card.

        Args:
            player: The player being asked.
            card: The card that was just played.

        Returns:
            True if player wants to jump in, False otherwise.
        """
        print(format_highlight(f"\n{player.name}, someone played {self.render_card(card)}!", Fore.MAGENTA, style=Style.BRIGHT))
        response = input("Do you want to JUMP IN with an identical card? (y/n): ").strip().lower()
        return response in ("y", "yes")


class UnoGame:
    """The main engine for managing and playing a game of Uno.

    This class orchestrates the game flow, including setting up the game,
    handling player turns, enforcing rules, and determining the winner.
    """

    def __init__(
        self,
        *,
        players: Sequence[UnoPlayer],
        rng: Optional[random.Random] = None,
        interface: Optional[UnoInterface] = None,
        house_rules: Optional[HouseRules] = None,
        team_mode: bool = False,
    ) -> None:
        if len(players) < 2:
            raise ValueError("Uno requires at least two players")
        self.players = list(players)
        self.rng = rng or random.Random()
        self.deck = UnoDeck(rng=self.rng)
        self.discard_pile: List[UnoCard] = []
        self.current_index = 0
        self.direction = 1  # 1 for clockwise, -1 for counter-clockwise
        self.active_color = ""
        self.active_value = ""
        self.penalty_value: Optional[str] = None
        self.penalty_amount = 0
        self.plus4_challenge: Optional[dict] = None
        self.interface = interface or ConsoleUnoInterface()
        self.event_log: List[tuple[str, str, str]] = []
        self.house_rules = house_rules or HouseRules()
        self.team_mode = team_mode
        # Validate team assignments if in team mode
        if self.team_mode:
            teams = set(p.team for p in self.players if p.team is not None)
            if len(teams) < 2:
                raise ValueError("Team mode requires at least 2 teams")

    def setup(self, *, starting_hand: int = 7) -> None:
        """Initializes the game state for a new round."""
        for player in self.players:
            # Deal a fresh starting hand to everyone and reset UNO state flags.
            player.hand.clear()
            player.pending_uno = False
            player.draw_cards(self.deck, starting_hand)

        first_card = self._draw_start_card()
        self.discard_pile.append(first_card)
        self.active_color = first_card.color or self.rng.choice(COLORS)
        self.active_value = first_card.value

        # Some action cards (e.g., Skip) immediately affect turn order.
        skip_next = self._apply_action_card(first_card, initializing=True)
        if skip_next:
            self.current_index = self._next_index(1)
        self.interface.update_status(self)

    def _draw_start_card(self) -> UnoCard:
        """Draws the first card for the discard pile, ensuring it's not a wild."""
        while True:
            card = self.deck.draw()
            if card.value not in WILD_VALUES:
                return card
            # Wilds are unsuitable as a starting card; cycle them back in and
            # reshuffle to preserve randomness.
            self.deck.cards.insert(0, card)
            self.deck.shuffle()

    def _reshuffle_if_needed(self) -> None:
        """Reshuffles the discard pile into the deck if the deck is empty."""
        if self.deck.cards:
            return
        if len(self.discard_pile) <= 1:
            raise RuntimeError("No cards left to reshuffle")

        top_card = self.discard_pile.pop()
        # Everything except the top card of the discard pile is shuffled back
        # into the deck so the active card remains visible on the table.
        self.deck.extend(self.discard_pile)
        self.discard_pile = [top_card]

    def _next_index(self, steps: int = 1) -> int:
        """Calculates the index of the next player in turn order."""
        return (self.current_index + steps * self.direction) % len(self.players)

    def _advance_turn(self, *, skip_next: bool = False) -> None:
        """Advances the turn to the next player."""
        self.current_index = self._next_index(1 + (1 if skip_next else 0))

    def _apply_action_card(
        self,
        card: UnoCard,
        *,
        player: Optional[UnoPlayer] = None,
        initializing: bool = False,
        illegal_plus4: bool = False,
    ) -> bool:
        """Applies the effect of an action card (skip, reverse, +2, +4)."""
        skip_next = False

        # Only reset penalties if stacking is disabled or this isn't a stackable card
        if not self.house_rules.stacking or card.value not in ("+2", "+4"):
            self.penalty_value = None
            self.penalty_amount = 0
            self.plus4_challenge = None

        if card.value == "skip" and not initializing:
            self._log(
                f"{player.name if player else 'A player'} skips the next player!",
                Fore.MAGENTA,
            )
            skip_next = True
        elif card.value == "reverse":
            self.direction *= -1
            direction_label = "clockwise" if self.direction == 1 else "counter-clockwise"
            self._log(f"Play order reverses to {direction_label}!", Fore.MAGENTA)
            if len(self.players) == 2 and not initializing:
                skip_next = True
        elif card.value == "+2":
            if self.house_rules.stacking and self.penalty_value in ("+2", "+4"):
                # Stack on existing penalty
                self.penalty_amount += 2
                self._log(f"Penalty stacked! Now at +{self.penalty_amount}!", Fore.RED, style=Style.BRIGHT)
            else:
                self.penalty_value = "+2"
                self.penalty_amount = 2
        elif card.value == "+4":
            if self.house_rules.stacking and self.penalty_value in ("+2", "+4"):
                # Stack on existing penalty
                self.penalty_amount += 4
                self._log(f"Penalty stacked! Now at +{self.penalty_amount}!", Fore.RED, style=Style.BRIGHT)
            else:
                self.penalty_value = "+4"
                self.penalty_amount = 4
            self.plus4_challenge = {"player": player, "illegal": illegal_plus4}

        return skip_next

    def _draw_cards(self, player: UnoPlayer, count: int) -> List[UnoCard]:
        """Makes a player draw a specified number of cards."""
        drawn: List[UnoCard] = []
        for _ in range(count):
            self._reshuffle_if_needed()
            drawn.append(player.draw_cards(self.deck, 1)[0])
        self.interface.update_status(self)
        return drawn

    def _log(self, message: str, color: str = Fore.WHITE, *, style: str = "") -> None:
        """Logs a game event to the event log and the interface."""
        self.event_log.append((message, color, style))
        self.interface.show_message(message, color=color, style=style)

    def _render_hand(self, player: UnoPlayer) -> List[str]:
        """Renders a player's hand to a list of formatted strings."""
        return [self.interface.render_card(card) for card in player.hand]

    def _has_color_match(self, player: UnoPlayer, color: str, *, ignore_index: Optional[int] = None) -> bool:
        """Checks if a player has a card of the specified color."""
        return any(c.color == color for i, c in enumerate(player.hand) if i != ignore_index)

    def _check_uno_penalties(self, current_player: UnoPlayer) -> None:
        """Checks if any player failed to call Uno and applies a penalty."""
        for p in self.players:
            if p is not current_player and p.pending_uno and len(p.hand) == 1:
                self.interface.notify_uno_penalty(p)
                self._draw_cards(p, 2)
                p.pending_uno = False

    def _resolve_plus4_challenge(self, challenger: UnoPlayer) -> bool:
        """Resolves a challenge to a +4 card play."""
        if not self.plus4_challenge or self.penalty_value != "+4":
            return False

        target = self.plus4_challenge["player"]
        if not target:
            return False  # Cannot challenge the opening card.

        illegal_play = self.plus4_challenge["illegal"]
        if not (challenger.is_human or self._bot_should_challenge(challenger)):
            return False

        if illegal_play:
            self._log(
                f"{challenger.name} challenges successfully! {target.name} draws 4.",
                Fore.MAGENTA,
                style=Style.BRIGHT,
            )
            self._draw_cards(target, 4)
            self.penalty_amount = 0
            self.penalty_value = None
        else:
            self._log(
                f"{challenger.name} challenges incorrectly and must draw 6!",
                Fore.RED,
                style=Style.BRIGHT,
            )
            self._draw_cards(challenger, 6)
            self._advance_turn()

        self.plus4_challenge = None
        self.interface.update_status(self)
        return True

    def _bot_should_challenge(self, challenger: UnoPlayer) -> bool:
        """Determines if a bot should challenge a +4 play."""
        if not self.plus4_challenge:
            return False

        base_threshold = {"aggressive": 0.4, "easy": 0.15}.get(challenger.personality, 0.25)
        modifier = 0.3 if self.plus4_challenge["illegal"] else -0.05
        return self.rng.random() < max(0.0, min(0.95, base_threshold + modifier))

    def _accept_penalty(self, player: UnoPlayer) -> None:
        """Makes a player accept a pending +2 or +4 penalty."""
        if self.penalty_amount == 0:
            return

        penalty_desc = "+4" if self.penalty_value == "+4" else "+2"
        self._log(
            f"{player.name} draws {self.penalty_amount} cards from a {penalty_desc} stack.",
            Fore.YELLOW,
        )
        self._draw_cards(player, self.penalty_amount)
        self.penalty_amount = 0
        self.penalty_value = None
        self.plus4_challenge = None
        self._advance_turn()

    def _swap_hands(self, player1: UnoPlayer, player2: UnoPlayer) -> None:
        """Swap hands between two players (for 7 card rule)."""
        player1.hand, player2.hand = player2.hand, player1.hand
        player1.pending_uno = len(player1.hand) == 1
        player2.pending_uno = len(player2.hand) == 1
        self._log(
            f"{player1.name} swaps hands with {player2.name}!",
            Fore.MAGENTA,
            style=Style.BRIGHT,
        )

    def _rotate_hands(self) -> None:
        """Rotate all hands in the direction of play (for 0 card rule)."""
        if len(self.players) < 2:
            return

        if self.direction == 1:
            # Clockwise: each player gets the hand from the player before them
            hands = [p.hand for p in self.players]
            for i, player in enumerate(self.players):
                player.hand = hands[i - 1]
                player.pending_uno = len(player.hand) == 1
            self._log("All hands rotate clockwise!", Fore.MAGENTA, style=Style.BRIGHT)
        else:
            # Counter-clockwise: each player gets the hand from the player after them
            hands = [p.hand for p in self.players]
            for i, player in enumerate(self.players):
                player.hand = hands[(i + 1) % len(self.players)]
                player.pending_uno = len(player.hand) == 1
            self._log("All hands rotate counter-clockwise!", Fore.MAGENTA, style=Style.BRIGHT)

    def _check_jump_in(self, played_card: UnoCard, current_player: UnoPlayer) -> Optional[tuple[UnoPlayer, int]]:
        """Check if any other player wants to jump in with an identical card.

        Jump-in rule: Players can play an identical card (same color AND value)
        out of turn, interrupting the normal turn order.

        Args:
            played_card: The card that was just played.
            current_player: The player who just played the card.

        Returns:
            Tuple of (player, card_index) who jumps in, or None if no one jumps in.
        """
        if played_card.is_wild():
            # Cannot jump in on wild cards (no fixed color)
            return None

        # Check players in clockwise order from current player
        # This ensures fairness - closest player gets priority
        start_idx = (self.players.index(current_player) + 1) % len(self.players)
        for offset in range(len(self.players) - 1):
            check_idx = (start_idx + offset) % len(self.players)
            player = self.players[check_idx]

            if player == current_player:
                continue

            # Check if player has an identical card
            identical_cards = [i for i, card in enumerate(player.hand) if card.color == played_card.color and card.value == played_card.value]

            if not identical_cards:
                continue

            # Human player: ask if they want to jump in
            if player.is_human:
                if self.interface.prompt_jump_in(player, played_card):
                    # Use first identical card
                    return (player, identical_cards[0])
            else:
                # Bot decision: jump in based on personality
                if self._bot_should_jump_in(player, played_card, identical_cards):
                    # Use first identical card
                    return (player, identical_cards[0])

        return None

    def _bot_should_jump_in(self, bot: UnoPlayer, played_card: UnoCard, identical_card_indices: List[int]) -> bool:
        """Determine if a bot should jump in with an identical card.

        Args:
            bot: The bot player.
            played_card: The card that was just played.
            identical_card_indices: Indices of identical cards in bot's hand.

        Returns:
            True if the bot should jump in, False otherwise.
        """
        if not identical_card_indices:
            return False

        # More likely to jump in if they have few cards or it's an action card
        hand_size = len(bot.hand)
        is_action = played_card.is_action()

        # Personality-based probability
        base_prob = {"aggressive": 0.7, "balanced": 0.5, "easy": 0.3}.get(bot.personality, 0.5)

        # Adjust for hand size (more likely with fewer cards)
        if hand_size <= 3:
            base_prob += 0.2
        elif hand_size <= 5:
            base_prob += 0.1

        # Adjust for action cards (more likely to jump in on action cards)
        if is_action:
            base_prob += 0.15

        return self.rng.random() < min(0.95, base_prob)

    def _execute_play(
        self,
        player: UnoPlayer,
        card_index: int,
        *,
        declare_uno: bool = False,
        chosen_color: Optional[str] = None,
        swap_target: Optional[int] = None,
    ) -> Optional[UnoPlayer]:
        """Executes a card play, updating the game state and checking for a winner."""
        card = player.hand[card_index]
        illegal_plus4 = card.value == "+4" and self.active_color and self._has_color_match(player, self.active_color, ignore_index=card_index)

        # Remove the card from the player's hand and push it to the discard pile
        # before mutating active colour/value so the UI reflects the new top card.
        player.pop_card(card_index)
        self.discard_pile.append(card)
        self.active_value = card.value
        self.active_color = card.color or chosen_color or (self.interface.choose_color(player) if player.is_human else player.preferred_color())

        if card.is_wild():
            self._log(
                f"Active color is now {self.interface.render_color(self.active_color)}.",
                Fore.CYAN,
            )

        # Apply action-card effects (penalties, reverse, skip, etc.) prior to
        # checking for victory so follow-up turns use the updated state.
        skip_next = self._apply_action_card(card, player=player, illegal_plus4=illegal_plus4)
        self._log(f"{player.name} plays {self.interface.render_card(card)}.", Fore.GREEN)

        # Play sound effects for card plays
        if card.value == "skip":
            self.interface.play_sound("skip")
        elif card.value == "reverse":
            self.interface.play_sound("reverse")
        elif card.value in ("+2", "+4"):
            self.interface.play_sound("draw_penalty")
        elif card.is_wild():
            self.interface.play_sound("wild")
        else:
            self.interface.play_sound("card_play")

        # Handle jump-in rule: check if another player can play an identical card
        if self.house_rules.jump_in and not card.is_wild():
            jump_in_result = self._check_jump_in(card, player)
            if jump_in_result:
                jump_in_player, jump_in_card_idx = jump_in_result
                self._log(f"{jump_in_player.name} jumps in!", Fore.MAGENTA, style=Style.BRIGHT)
                self.interface.play_sound("jump_in")
                # Set current player to jump-in player so they take the next turn
                self.current_index = self.players.index(jump_in_player)
                # Play their card immediately (recursive call to execute_play)
                return self._execute_play(jump_in_player, jump_in_card_idx, declare_uno=len(jump_in_player.hand) == 2)

        # Handle 7-0 swapping house rule
        if self.house_rules.seven_zero_swap and card.value in ("7", "0"):
            if card.value == "7":
                # Swap hands with another player
                if swap_target is not None and 0 <= swap_target < len(self.players):
                    target_player = self.players[swap_target]
                    if target_player != player:
                        self._swap_hands(player, target_player)
                        self.interface.play_sound("swap")
                elif not player.is_human:
                    # Bot chooses a random opponent
                    opponents = [i for i, p in enumerate(self.players) if p != player]
                    if opponents:
                        target_idx = self.rng.choice(opponents)
                        self._swap_hands(player, self.players[target_idx])
                        self.interface.play_sound("swap")
            elif card.value == "0":
                # Rotate all hands
                self._rotate_hands()
                self.interface.play_sound("rotate")

        if not player.has_cards():
            # Check for team victory if in team mode
            if self.team_mode and player.team is not None:
                team_name = f"Team {player.team}"
                self._log(f"{team_name} wins the game!", Fore.CYAN, style=Style.BRIGHT)
                self.interface.play_sound("win")
                self.interface.announce_winner(player)
                return player
            else:
                self.interface.play_sound("win")
                self.interface.announce_winner(player)
                return player

        if len(player.hand) == 1 and (declare_uno or not player.is_human):
            # Bots auto-announce UNO, while humans must opt in via the prompt.
            self.interface.play_sound("uno")
            self.interface.notify_uno_called(player)
        elif len(player.hand) == 1:
            player.pending_uno = True

        self.interface.update_status(self)
        self._advance_turn(skip_next=skip_next)
        return None

    def _bot_take_turn(self, player: UnoPlayer, playable: Sequence[int], penalty_active: bool) -> Optional[UnoPlayer]:
        """Handles a bot's turn, including challenging, playing, or drawing."""
        if self.penalty_value == "+4" and self.plus4_challenge and self._resolve_plus4_challenge(player):
            return None
        if penalty_active and not playable:
            # Bots must accept the penalty when they cannot stack an additional
            # penalty card on top of the existing chain.
            self._accept_penalty(player)
            return None
        if playable:
            # Choose a card via the player's heuristic and immediately attempt
            # to play it; the helper returns the winner if the game ends.
            return self._execute_play(
                player,
                player.choose_card(playable, self.active_color),
                declare_uno=len(player.hand) == 2,
            )

        drawn_card = self._draw_cards(player, 1)[0]
        self._log(f"{player.name} draws a card.", Fore.YELLOW)
        if drawn_card.matches(self.active_color, self.active_value):
            if drawn_card.is_action() and player.personality == "easy":
                # Easy bots intentionally hold back action cards to feel more
                # human-like and prevent relentless stacking.
                pass
            else:
                return self._execute_play(player, len(player.hand) - 1, declare_uno=len(player.hand) == 1)

        self._advance_turn()
        return None

    def play(self) -> UnoPlayer:
        """Runs the main game loop until a winner is determined."""
        while True:
            player = self.players[self.current_index]
            self._check_uno_penalties(player)

            top_card = self.discard_pile[-1]
            heading = f"Top card: {self.interface.render_card(top_card, emphasize=True)} | Active color: {self.interface.render_color(self.active_color)}"
            self.interface.show_heading(heading)

            if self.penalty_amount:
                self._log(
                    f"Pending penalty: draw {self.penalty_amount} (must stack {self.penalty_value}).",
                    Fore.YELLOW,
                )

            playable = player.playable_cards(self.active_color, self.active_value, penalty_value=self.penalty_value)
            penalty_active = self.penalty_amount > 0

            if player.is_human:
                self.interface.show_hand(player, self._render_hand(player))
                if self.penalty_value == "+4" and self.plus4_challenge and self.penalty_amount and self._resolve_plus4_challenge(player):
                    continue

                decision = self.interface.choose_action(self, player, playable, penalty_active)
                if penalty_active and not playable and decision.action != "accept_penalty":
                    self._log("You must accept the penalty.", Fore.RED)
                    continue

                if decision.action == "accept_penalty":
                    self._accept_penalty(player)
                elif decision.action == "draw":
                    drawn_card = self._draw_cards(player, 1)[0]
                    self._log(
                        f"You drew {self.interface.render_card(drawn_card, emphasize=True)}.",
                        Fore.GREEN,
                    )
                    follow_up = self.interface.handle_drawn_card(self, player, drawn_card)
                    if follow_up.action == "play" and (
                        winner := self._execute_play(
                            player,
                            follow_up.card_index,
                            declare_uno=follow_up.declare_uno,
                            chosen_color=follow_up.chosen_color,
                            swap_target=follow_up.swap_target,
                        )
                    ):
                        return winner
                    else:
                        self._advance_turn()
                elif decision.action == "play" and decision.card_index is not None:
                    if not (0 <= decision.card_index < len(player.hand) and decision.card_index in playable):
                        self._log("Invalid card choice.", Fore.RED)
                        continue
                    if winner := self._execute_play(player, decision.card_index, declare_uno=decision.declare_uno, swap_target=decision.swap_target):
                        return winner
            else:  # Bot's turn
                if winner := self._bot_take_turn(player, playable, penalty_active):
                    return winner

            self.interface.update_status(self)


def build_players(
    total_players: int,
    *,
    bots: int,
    bot_skill: str = "balanced",
    team_mode: bool = False,
) -> List[UnoPlayer]:
    """Create a roster of Uno players for a new game session.

    Args:
        total_players: Total number of seats at the virtual table.
        bots: Number of AI-controlled opponents to include.
        bot_skill: Personality label that tunes the bot heuristics.
        team_mode: If True, assign players to teams (2v2 for 4 players).

    Returns:
        An ordered list of :class:`UnoPlayer` objects ready to hand to
        :class:`UnoGame`.

    Raises:
        ValueError: If the requested table configuration is invalid.
    """

    if total_players < 2:
        raise ValueError("Uno requires at least two total players.")
    if bots < 0:
        raise ValueError("Number of bot players cannot be negative.")
    if bot_skill not in BOT_PERSONALITIES:
        raise ValueError("Bot skill must be one of: " + ", ".join(sorted(BOT_PERSONALITIES)))
    if team_mode and total_players != 4:
        raise ValueError("Team mode currently requires exactly 4 players.")

    human_count = total_players - bots
    if human_count <= 0:
        raise ValueError("At least one human player is required to start Uno.")

    players: List[UnoPlayer] = []
    for index in range(human_count):
        name = "You" if index == 0 else f"Player {index + 1}"
        team = (index % 2) if team_mode else None
        players.append(UnoPlayer(name, is_human=True, team=team))

    for bot_index in range(bots):
        team = ((human_count + bot_index) % 2) if team_mode else None
        players.append(
            UnoPlayer(
                f"{bot_skill.capitalize()} Bot {bot_index + 1}",
                personality=bot_skill,
                team=team,
            )
        )

    return players


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Parse command-line arguments and launch either the CLI or GUI front-end."""

    parser = argparse.ArgumentParser(description="Play a game of Uno against configurable bot opponents.")
    parser.add_argument(
        "--players",
        type=int,
        default=4,
        help="Total number of seats at the table (minimum 2).",
    )
    parser.add_argument(
        "--bots",
        type=int,
        default=None,
        help="How many AI opponents to include (defaults to players - 1).",
    )
    parser.add_argument(
        "--bot-skill",
        choices=sorted(BOT_PERSONALITIES),
        default="balanced",
        help="Choose the personality for all bot opponents.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Optional random seed for reproducible shuffles.",
    )
    parser.add_argument(
        "--gui",
        nargs="?",
        const="tk",
        choices=("tk", "tkinter", "pyqt", "pyqt5"),
        help="Launch a graphical interface. Use 'tk' (default) or 'pyqt'.",
    )
    parser.add_argument(
        "--stacking",
        action="store_true",
        help="Enable stacking of +2 and +4 cards.",
    )
    parser.add_argument(
        "--jump-in",
        action="store_true",
        help="Enable jump-in rule (play identical cards out of turn).",
    )
    parser.add_argument(
        "--seven-zero",
        action="store_true",
        help="Enable 7-0 swapping rule (7 swaps hands, 0 rotates all hands).",
    )
    parser.add_argument(
        "--team-mode",
        action="store_true",
        help="Enable 2v2 team play mode (requires 4 players).",
    )

    args = parser.parse_args(argv)
    total_players = args.players
    bot_count = args.bots if args.bots is not None else max(total_players - 1, 1)

    house_rules = HouseRules(
        stacking=args.stacking,
        jump_in=args.jump_in,
        seven_zero_swap=args.seven_zero,
    )

    try:
        players = build_players(total_players, bots=bot_count, bot_skill=args.bot_skill, team_mode=args.team_mode)
    except ValueError as exc:  # pragma: no cover - defensive input validation
        parser.error(str(exc))

    rng = random.Random(args.seed)

    if args.gui:
        backend_map = {"tk": "tk", "tkinter": "tk", "pyqt": "pyqt", "pyqt5": "pyqt"}
        backend = backend_map[args.gui]
        if backend == "pyqt":
            try:
                from .gui_pyqt import launch_uno_gui_pyqt
            except ImportError as exc:  # pragma: no cover - PyQt optional dependency
                parser.error(f"PyQt5 backend requested but not available: {exc}")

            launch_uno_gui_pyqt(
                total_players,
                bots=bot_count,
                bot_skill=args.bot_skill,
                seed=args.seed,
                house_rules=house_rules,
                team_mode=args.team_mode,
            )
        else:
            from .gui import launch_uno_gui

            launch_uno_gui(
                total_players,
                bots=bot_count,
                bot_skill=args.bot_skill,
                seed=args.seed,
                house_rules=house_rules,
                team_mode=args.team_mode,
            )
        return 0

    game = UnoGame(players=players, rng=rng, interface=ConsoleUnoInterface(), house_rules=house_rules, team_mode=args.team_mode)
    game.setup()
    game.play()
    return 0


__all__ = [
    "UnoCard",
    "UnoDeck",
    "UnoGame",
    "UnoPlayer",
    "ConsoleUnoInterface",
    "PlayerDecision",
    "HouseRules",
    "build_players",
    "main",
]
