"""Tkinter-powered graphical user interface for the Uno game.

This module provides the `TkUnoInterface` class, which serves as a bridge
between the `UnoGame` engine and a `tkinter` GUI. It handles rendering the game
state, including player hands, the scoreboard, and the game log, and captures
user input through interactive widgets.
"""

from __future__ import annotations

import random
import re
import tkinter as tk
from tkinter import messagebox, scrolledtext
from typing import List, Optional, Sequence

from colorama import Fore, Style

from .sound_manager import create_sound_manager
from .uno import COLORS, HouseRules, PlayerDecision, UnoCard, UnoGame, UnoInterface, UnoPlayer, build_players

# Emojis for representing card colors in the GUI.
COLOR_EMOJI = {"red": "🟥", "yellow": "🟨", "green": "🟩", "blue": "🟦", None: "⬜"}

# Regex to strip ANSI escape codes from console-formatted text.
ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")

# Mapping from colorama colors to Tkinter-compatible hex codes and tags.
COLOR_TAGS = {
    Fore.WHITE: ("normal", "#f5f5f5"),
    Fore.RED: ("error", "#ef5350"),
    Fore.GREEN: ("success", "#66bb6a"),
    Fore.YELLOW: ("warning", "#fdd835"),
    Fore.CYAN: ("info", "#4dd0e1"),
    Fore.MAGENTA: ("accent", "#ba68c8"),
}


def strip_ansi(text: str) -> str:
    """Remove ANSI escape codes from a string."""
    # The console engine logs use ANSI colouring; the GUI strips them to
    # avoid showing raw escape sequences in Tkinter widgets.
    return ANSI_RE.sub("", text)


class TkUnoInterface(UnoInterface):
    """A graphical interface that bridges the Uno game engine with Tkinter.

    This class implements the `UnoInterface` protocol, providing a visual
    representation of the game and handling user interactions.
    """

    def __init__(
        self,
        root: tk.Tk,
        players: Sequence[UnoPlayer],
        *,
        enable_animations: bool = True,
        enable_sounds: bool = False,
    ) -> None:
        """Initialize the Tkinter Uno interface.

        Args:
            root: The root Tkinter window.
            players: The sequence of players in the game.
            enable_animations: Whether to enable card animations.
            enable_sounds: Whether to enable sound effects.
        """
        self.root = root
        self.root.title("Card Games - Uno")
        self.game: Optional[UnoGame] = None
        self.players = list(players)
        self.decision_ready = tk.BooleanVar(value=False)
        self.pending_decision: Optional[PlayerDecision] = None
        self.uno_var = tk.BooleanVar(value=False)
        self.enable_animations = enable_animations
        self.enable_sounds = enable_sounds
        self.sound_manager = create_sound_manager(enabled=enable_sounds)
        self._build_layout()
        self._build_scoreboard()

    def _build_layout(self) -> None:
        """Construct the main layout of the application window."""
        self.heading_var = tk.StringVar(value="Welcome to Uno!")
        heading = tk.Label(
            self.root,
            textvariable=self.heading_var,
            font=("Helvetica", 18, "bold"),
            pady=8,
        )
        heading.pack(fill=tk.X)

        content = tk.Frame(self.root)
        content.pack(fill=tk.BOTH, expand=True)

        self.status_frame = tk.LabelFrame(content, text="Players")
        self.status_frame.pack(side=tk.LEFT, fill=tk.Y, padx=8, pady=8)

        log_frame = tk.LabelFrame(content, text="Table Log")
        log_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=8, pady=8)
        self.log_widget = scrolledtext.ScrolledText(
            log_frame,
            width=60,
            height=18,
            state=tk.DISABLED,
            wrap=tk.WORD,
            font=("Courier New", 11),
        )
        self.log_widget.pack(fill=tk.BOTH, expand=True)

        action_area = tk.Frame(content)
        action_area.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=8, pady=8)

        self.action_frame = tk.LabelFrame(action_area, text="Actions")
        self.action_frame.pack(fill=tk.X, pady=6)

        self.hand_frame = tk.LabelFrame(action_area, text="Your Hand")
        self.hand_frame.pack(fill=tk.BOTH, expand=True)

        self.card_buttons: List[tk.Button] = []
        self.score_labels: List[tk.Label] = []

    def _build_scoreboard(self) -> None:
        """Create and populate the scoreboard with player names and card counts."""
        for widget in self.status_frame.winfo_children():
            widget.destroy()
        self.score_labels = []
        for player in self.players:
            frame = tk.Frame(self.status_frame)
            frame.pack(fill=tk.X, pady=2)
            tk.Label(frame, text=player.name, font=("Helvetica", 12, "bold")).pack(side=tk.LEFT)
            count_label = tk.Label(frame, text=f"{len(player.hand)} cards", font=("Helvetica", 11))
            count_label.pack(side=tk.RIGHT)
            self.score_labels.append(count_label)

    def set_game(self, game: UnoGame) -> None:
        """Set the game instance and update the status."""
        self.game = game
        self.update_status(game)

    def show_heading(self, message: str) -> None:
        """Display a heading message at the top of the window."""
        self.heading_var.set(strip_ansi(message))
        self.root.update_idletasks()

    def show_message(self, message: str, *, color: str = Fore.WHITE, style: str = "") -> None:
        """Display a message in the game log with appropriate color and style."""
        tag, hex_color = COLOR_TAGS.get(color, ("normal", "#f5f5f5"))
        font_weight = "bold" if style == Style.BRIGHT else "normal"
        self.log_widget.tag_configure(tag, foreground=hex_color, font=("Courier New", 11, font_weight))
        self.log_widget.configure(state=tk.NORMAL)
        self.log_widget.insert(tk.END, strip_ansi(message) + "\n", tag)
        self.log_widget.configure(state=tk.DISABLED)
        self.log_widget.see(tk.END)
        self.root.update_idletasks()

    def show_hand(self, player: UnoPlayer, formatted_cards: Sequence[str]) -> None:
        """Display the player's hand as a series of buttons."""
        for widget in self.hand_frame.winfo_children():
            widget.destroy()
        self.card_buttons.clear()

        info = tk.Label(self.hand_frame, text="Select a card or choose an action below.", anchor="w")
        info.pack(fill=tk.X, padx=8, pady=4)

        button_row = tk.Frame(self.hand_frame)
        button_row.pack(fill=tk.X, padx=4, pady=4)
        for i, label in enumerate(formatted_cards):
            btn = tk.Button(
                button_row,
                text=strip_ansi(label),
                width=16,
                state=tk.DISABLED,
                relief=tk.RIDGE,
                padx=6,
                pady=6,
            )
            btn.grid(row=0, column=i, padx=4, pady=4)
            self.card_buttons.append(btn)
        self.root.update_idletasks()

    def choose_action(
        self,
        game: UnoGame,
        player: UnoPlayer,
        playable: Sequence[int],
        penalty_active: bool,
    ) -> PlayerDecision:
        """Wait for the user to make a decision (play, draw, etc.)."""
        self._prepare_action_controls(playable, penalty_active, game)
        self.decision_ready.set(False)
        self.pending_decision = None
        self.root.wait_variable(self.decision_ready)
        self._teardown_action_controls()
        return self.pending_decision or PlayerDecision(action="draw")

    def handle_drawn_card(self, game: UnoGame, player: UnoPlayer, card: UnoCard) -> PlayerDecision:
        """Prompt the user to play or keep a card they just drew."""
        self.show_hand(player, [game.interface.render_card(c) for c in player.hand])
        if not card.matches(game.active_color, game.active_value):
            self.show_message("The drawn card cannot be played.", color=Fore.YELLOW)
            return PlayerDecision(action="skip")

        info = tk.Label(
            self.action_frame,
            text="Play the drawn card or keep it?",
            font=("Helvetica", 12),
        )
        info.pack(fill=tk.X, padx=6, pady=4)
        self.decision_ready.set(False)
        self.pending_decision = None

        def play_drawn() -> None:
            declare = self.uno_var.get() and len(player.hand) == 1
            self.pending_decision = PlayerDecision(action="play", card_index=len(player.hand) - 1, declare_uno=declare)
            self.decision_ready.set(True)

        def keep_drawn() -> None:
            self.pending_decision = PlayerDecision(action="skip")
            self.decision_ready.set(True)

        buttons = tk.Frame(self.action_frame)
        buttons.pack(fill=tk.X, padx=6, pady=4)
        tk.Button(buttons, text="Play Drawn Card", command=play_drawn).pack(side=tk.LEFT, padx=4)
        tk.Button(buttons, text="Keep Card", command=keep_drawn).pack(side=tk.LEFT, padx=4)
        self.root.wait_variable(self.decision_ready)
        info.destroy()
        buttons.destroy()
        return self.pending_decision or PlayerDecision(action="skip")

    def choose_color(self, player: UnoPlayer) -> str:
        """Open a dialog for the user to choose a color after playing a wild."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Choose a Color")
        tk.Label(dialog, text="Select the new active color:", font=("Helvetica", 12)).pack(padx=12, pady=8)
        color_var = tk.StringVar()

        def select_color(color: str) -> None:
            color_var.set(color)
            dialog.destroy()

        button_row = tk.Frame(dialog)
        button_row.pack(padx=12, pady=12)
        for color in COLORS:
            tk.Button(
                button_row,
                text=color.capitalize(),
                width=10,
                command=lambda c=color: select_color(c),
            ).pack(side=tk.LEFT, padx=6)

        dialog.transient(self.root)
        dialog.grab_set()
        self.root.wait_variable(color_var)
        return color_var.get()

    def choose_swap_target(self, player: UnoPlayer, players: Sequence[UnoPlayer]) -> int:
        """Open a dialog for the user to choose another player to swap hands with."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Choose Swap Target")
        tk.Label(dialog, text="Choose a player to swap hands with:", font=("Helvetica", 12)).pack(padx=12, pady=8)
        target_var = tk.IntVar(value=-1)

        def select_target(idx: int) -> None:
            target_var.set(idx)
            dialog.destroy()

        button_frame = tk.Frame(dialog)
        button_frame.pack(padx=12, pady=12)
        for i, p in enumerate(players):
            if p != player:
                tk.Button(
                    button_frame,
                    text=f"{p.name} ({len(p.hand)} cards)",
                    width=20,
                    command=lambda idx=i: select_target(idx),
                ).pack(pady=4)

        dialog.transient(self.root)
        dialog.grab_set()
        self.root.wait_variable(target_var)
        return target_var.get()

    def prompt_challenge(self, challenger: UnoPlayer, target: UnoPlayer, *, bluff_possible: bool) -> bool:
        """Ask the user if they want to challenge a +4 card."""
        message = f"Challenge {target.name}'s +4?" + (" It might be a bluff!" if bluff_possible else "")
        return messagebox.askyesno("Challenge?", message, parent=self.root)

    def notify_uno_called(self, player: UnoPlayer) -> None:
        """Display a message indicating a player has called "Uno!"."""
        self.show_message(f"{player.name} calls UNO!", color=Fore.CYAN, style=Style.BRIGHT)

    def notify_uno_penalty(self, player: UnoPlayer) -> None:
        """Display a message for a missed "Uno!" call."""
        self.show_message(
            f"{player.name} failed to call UNO and draws two cards!",
            color=Fore.RED,
            style=Style.BRIGHT,
        )

    def announce_winner(self, winner: UnoPlayer) -> None:
        """Announce the winner of the game."""
        self.show_message(f"{winner.name} wins the round!", color=Fore.CYAN, style=Style.BRIGHT)
        messagebox.showinfo("Uno", f"{winner.name} wins the game!")

    def update_status(self, game: UnoGame) -> None:
        """Update the scoreboard with the current card counts."""
        for label, player in zip(self.score_labels, self.players):
            label.configure(text=f"{len(player.hand)} cards")
        self.root.update_idletasks()

    def render_card(self, card: UnoCard, *, emphasize: bool = False) -> str:
        """Render a card to a string with an emoji prefix."""
        prefix = COLOR_EMOJI.get(card.color, "⬜")
        label = card.label().upper() if emphasize else card.label()
        return f"{prefix} {label}"

    def render_color(self, color: str) -> str:
        """Render a color name with its corresponding emoji."""
        return f"{COLOR_EMOJI.get(color, '⬜')} {color.capitalize()}"

    # Internal helpers -------------------------------------------------
    def _prepare_action_controls(self, playable: Sequence[int], penalty_active: bool, game: UnoGame) -> None:
        """Set up the action buttons for the user's turn."""
        for i, btn in enumerate(self.card_buttons):
            if i in playable:
                btn.configure(state=tk.NORMAL, command=lambda i=i: self._select_card(i))
            else:
                btn.configure(state=tk.DISABLED)

        for widget in self.action_frame.winfo_children():
            widget.destroy()

        uno_toggle = tk.Checkbutton(
            self.action_frame,
            text="Declare UNO",
            variable=self.uno_var,
            indicatoron=False,
            width=14,
            pady=4,
        )
        uno_toggle.pack(side=tk.LEFT, padx=4, pady=4)

        if penalty_active and not playable:
            tk.Label(
                self.action_frame,
                text=f"Accept the +{game.penalty_amount} penalty.",
                font=("Helvetica", 11),
            ).pack(side=tk.LEFT, padx=6)
            tk.Button(
                self.action_frame,
                text=f"Draw {game.penalty_amount}",
                command=self._accept_penalty,
                width=16,
            ).pack(side=tk.LEFT, padx=4)
        else:
            tk.Button(self.action_frame, text="Draw Card", command=self._draw_card, width=14).pack(side=tk.LEFT, padx=4)
            if penalty_active:
                tk.Button(
                    self.action_frame,
                    text=f"Accept +{game.penalty_amount}",
                    command=self._accept_penalty,
                    width=18,
                ).pack(side=tk.LEFT, padx=4)
        self.root.update_idletasks()

    def _teardown_action_controls(self) -> None:
        """Clear and disable the action controls after a turn."""
        for widget in self.action_frame.winfo_children():
            widget.destroy()
        for btn in self.card_buttons:
            btn.configure(state=tk.DISABLED)
        self.uno_var.set(False)
        self.root.update_idletasks()

    def _select_card(self, index: int) -> None:
        """Handle the user's card selection."""
        swap_target = None
        # Check if playing a 7 with seven_zero_swap rule enabled
        if self.game and self.game.house_rules.seven_zero_swap and 0 <= index < len(self.game.players[self.game.current_index].hand):
            current_player = self.game.players[self.game.current_index]
            card = current_player.hand[index]
            if card.value == "7":
                swap_target = self.choose_swap_target(current_player, self.game.players)

        self._animate_card_play(index)

        self.pending_decision = PlayerDecision(action="play", card_index=index, declare_uno=self.uno_var.get(), swap_target=swap_target)
        self.decision_ready.set(True)

    def _draw_card(self) -> None:
        """Set the pending decision to 'draw'."""
        self.pending_decision = PlayerDecision(action="draw")
        self.decision_ready.set(True)

    def _animate_card_play(self, card_index: int) -> None:
        """Animate a card being played with highlight and scale effects.

        This method shows a visual animation when a card is played:
        - Highlights the card with a bright color
        - Creates a pulsing effect
        - Can be extended with more sophisticated animations in the future
        """
        if not self.enable_animations:
            return

        # Animate the button to indicate the card being played
        if 0 <= card_index < len(self.card_buttons):
            btn = self.card_buttons[card_index]
            original_bg = btn.cget("background")
            original_relief = btn.cget("relief")

            def animate(step: int = 0) -> None:
                if step < 6:
                    # Alternate between highlighted and normal state
                    if step % 2 == 0:
                        btn.configure(bg="#FFD700", relief="raised")  # Gold highlight
                    else:
                        btn.configure(bg=original_bg, relief=original_relief)
                    # Schedule next animation step
                    self.root.after(80, lambda: animate(step + 1))
                else:
                    # Restore original appearance
                    btn.configure(bg=original_bg, relief=original_relief)

            animate()

    def play_sound(self, sound_type: str) -> None:
        """Play a sound effect using the sound manager.

        Args:
            sound_type: Type of sound to play ('card_play', 'draw', 'uno', 'win', etc.)

        Sound types:
        - 'card_play': When a card is played
        - 'draw': When drawing cards
        - 'uno': When UNO is called
        - 'win': When someone wins
        - 'reverse': When direction changes
        - 'skip': When a player is skipped
        - 'swap': When hands are swapped (7 card)
        - 'rotate': When hands rotate (0 card)
        - 'wild': When a wild card is played
        - 'draw_penalty': When +2 or +4 is played
        """
        if not self.enable_sounds or self.sound_manager is None:
            return

        self.sound_manager.play(sound_type)

    def prompt_jump_in(self, player: UnoPlayer, card: UnoCard) -> bool:
        """Ask if player wants to jump in with an identical card.

        Args:
            player: The player being asked.
            card: The card that was just played.

        Returns:
            True if player wants to jump in, False otherwise.
        """
        import tkinter.messagebox as messagebox

        if not player.is_human:
            return False

        # Show jump-in prompt
        result = messagebox.askyesno(
            "Jump In?", f"{player.name}, someone just played {card.color} {card.value}!\n\nDo you want to JUMP IN with an identical card?", icon="question"
        )

        return result

    def _accept_penalty(self) -> None:
        """Set the pending decision to 'accept_penalty'."""
        self.pending_decision = PlayerDecision(action="accept_penalty")
        self.decision_ready.set(True)


def launch_uno_gui(
    total_players: int,
    *,
    bots: int,
    bot_skill: str,
    seed: Optional[int] = None,
    house_rules: Optional[HouseRules] = None,
    team_mode: bool = False,
) -> None:
    """Launch the Uno GUI application.

    Args:
        total_players: The total number of players in the game.
        bots: The number of bot opponents.
        bot_skill: The personality/skill level of the bots.
        seed: An optional seed for the random number generator.
        house_rules: Optional house rules configuration.
        team_mode: Whether to enable team play mode.
    """
    rng = random.Random(seed)
    players = build_players(total_players, bots=bots, bot_skill=bot_skill, team_mode=team_mode)
    root = tk.Tk()
    interface = TkUnoInterface(root, players)
    game = UnoGame(
        players=players,
        rng=rng,
        interface=interface,
        house_rules=house_rules or HouseRules(),
        team_mode=team_mode,
    )
    interface.set_game(game)

    def run_game() -> None:
        # Run the game loop within the Tkinter event loop.
        game.setup()
        try:
            game.play()
        except Exception as exc:
            messagebox.showerror("Uno Error", f"An unexpected error occurred: {exc}")
            raise

    root.after(100, run_game)
    root.mainloop()


__all__ = ["launch_uno_gui", "TkUnoInterface"]
