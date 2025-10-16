"""Tkinter-powered graphical interface for the Bluff card game.

The GUI is intentionally verbose in both code and documentation so that it can
double as a tutorial for how the engine communicates with a presentation layer.
Key features include:

* A scrolling log that mirrors the CLI output, keeping human players informed
  about every decision made at the table.
* A scoreboard summarising player statistics such as cards remaining, number of
  successful bluffs, and challenge history.
* Interactive controls for selecting cards, declaring claims, and issuing
  challenges. These widgets are coordinated through well-documented helper
  methods whose docstrings explain the reasoning behind each state change.
"""

from __future__ import annotations

import random
import tkinter as tk
from tkinter import ttk
from typing import Optional

from card_games.common.soundscapes import initialize_game_soundscape
from common.gui_base import BaseGUI, GUIConfig

from .bluff import BluffGame, DeckType, DifficultyLevel, Phase


class BluffGUI(BaseGUI):
    """Manages the interactive Tkinter interface for a Bluff card game.

    This class is responsible for building the UI, rendering the game state,
    and handling user interactions like card selection, claims, and challenges.
    """

    def __init__(
        self,
        root: tk.Tk,
        game: BluffGame,
        *,
        enable_sounds: bool = True,
        config: Optional[GUIConfig] = None,
    ) -> None:
        """Initialize the Bluff GUI.

        Args:
            root (tk.Tk): The root Tkinter window.
            game (BluffGame): The instance of the Bluff game engine.
        """
        gui_config = config or GUIConfig(
            window_title="Bluff - Card Game",
            window_width=1200,
            window_height=780,
            enable_sounds=enable_sounds,
            enable_animations=True,
            theme_name="dark",
        )
        super().__init__(root, gui_config)
        self.sound_manager = initialize_game_soundscape(
            "bluff",
            module_file=__file__,
            enable_sounds=gui_config.enable_sounds,
            existing_manager=self.sound_manager,
        )
        self.theme_manager.set_current_theme(gui_config.theme_name)
        self.current_theme = self.theme_manager.get_current_theme()
        self.game = game

        # Mirror the CLI welcome text so both interfaces narrate the same story
        # and players can switch between them without confusion.

        self.root.title("Card Games - Bluff")
        self.root.geometry("960x640")

        # UI state variables
        self.status_var = tk.StringVar(value="Welcome to Bluff! Shed every card to win.")
        self.pile_var = tk.StringVar(value="Pile: 0 cards")
        self.turn_var = tk.StringVar(value="Turn 1")
        self._selected_card: Optional[int] = None
        self._last_claim_text = tk.StringVar(value="No claim yet.")

        # Configure styles for widgets
        style = ttk.Style()
        style.configure("Card.TButton", font=("Consolas", 14), padding=8)
        style.configure(
            "SelectedCard.TButton",
            font=("Consolas", 14, "bold"),
            padding=8,
            background="#1f6aa5",
            foreground="#ffffff",
        )

        # Build the layout and start the game loop
        self._build_layout()
        self._update_scoreboard()
        self._update_user_hand()
        self._set_user_controls_state(enabled=False)
        self._set_challenge_controls_state(enabled=False)
        self.root.after(300, self.advance_game)

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------
    def _build_layout(self) -> None:
        """Construct the main layout of the application window."""
        root = self.root
        root.columnconfigure(0, weight=1)
        root.rowconfigure(1, weight=1)
        root.rowconfigure(2, weight=1)

        # Header with status and game info
        header = ttk.Frame(root, padding=12)
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(0, weight=2)
        header.columnconfigure(1, weight=1)
        header.columnconfigure(2, weight=1)
        self.status_label = ttk.Label(header, textvariable=self.status_var, font=("Segoe UI", 14, "bold"))
        self.status_label.grid(row=0, column=0, sticky="w")
        ttk.Label(header, textvariable=self.turn_var).grid(row=0, column=1, sticky="e")
        ttk.Label(header, textvariable=self.pile_var).grid(row=0, column=2, sticky="e")

        # Main board with game log and summary sidebar
        board = ttk.Frame(root, padding=10)
        board.grid(row=1, column=0, sticky="nsew")
        board.columnconfigure(0, weight=2)
        board.columnconfigure(1, weight=1)

        # Game log
        self.log = tk.Text(
            board,
            height=18,
            state="disabled",
            wrap="word",
            background="#101820",
            foreground="#E0E6ED",
        )
        self.log.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        # Sidebar with player summary and last claim
        sidebar = ttk.Frame(board, padding=10)
        sidebar.grid(row=0, column=1, sticky="nsew")
        sidebar.columnconfigure(0, weight=1)
        ttk.Label(sidebar, text="Table summary", font=("Segoe UI", 12, "bold")).grid(row=0, column=0, sticky="w")
        self.summary = tk.Text(sidebar, height=12, state="disabled", wrap="word")
        self.summary.grid(row=1, column=0, sticky="nsew", pady=(4, 10))
        ttk.Label(sidebar, textvariable=self._last_claim_text, wraplength=220).grid(row=2, column=0, sticky="w")

        # Player controls area
        controls = ttk.Frame(root, padding=12)
        controls.grid(row=2, column=0, sticky="nsew")
        controls.columnconfigure(0, weight=1)
        controls.columnconfigure(1, weight=1)
        controls.columnconfigure(2, weight=1)

        # User's hand display
        hand_frame = ttk.LabelFrame(controls, text="Your hand", padding=10)
        hand_frame.grid(row=0, column=0, columnspan=3, sticky="ew")
        hand_frame.columnconfigure(tuple(range(10)), weight=1)
        self.hand_frame = hand_frame

        # Claim controls
        claim_frame = ttk.Frame(controls, padding=(0, 10))
        claim_frame.grid(row=1, column=0, columnspan=3, sticky="ew")
        claim_frame.columnconfigure(1, weight=1)
        ttk.Label(claim_frame, text="Declare rank:").grid(row=0, column=0, sticky="w")
        # Get valid ranks from the game's deck type
        valid_ranks = self.game.deck_type.ranks
        self.claim_rank_var = tk.StringVar(value=valid_ranks[0])
        self.claim_combo = ttk.Combobox(
            claim_frame,
            textvariable=self.claim_rank_var,
            values=valid_ranks,
            state="readonly",
        )
        self.claim_combo.grid(row=0, column=1, sticky="ew", padx=6)
        self.submit_btn = ttk.Button(claim_frame, text="Play selected card", command=self.submit_claim)
        self.submit_btn.grid(row=0, column=2, sticky="ew")

        # Challenge controls
        challenge_frame = ttk.Frame(controls)
        challenge_frame.grid(row=2, column=0, columnspan=3, sticky="ew")
        challenge_frame.columnconfigure(0, weight=1)
        challenge_frame.columnconfigure(1, weight=1)
        self.call_btn = ttk.Button(
            challenge_frame,
            text="Call Bluff",
            command=lambda: self.resolve_user_challenge(True),
        )
        self.trust_btn = ttk.Button(
            challenge_frame,
            text="Trust Claim",
            command=lambda: self.resolve_user_challenge(False),
        )
        self.call_btn.grid(row=0, column=0, sticky="ew", padx=(0, 6))
        self.trust_btn.grid(row=0, column=1, sticky="ew")

    # ------------------------------------------------------------------
    # UI state updates
    # ------------------------------------------------------------------
    def _update_scoreboard(self) -> None:
        """Refresh the scoreboard with the latest game statistics."""
        state = self.game.public_state()
        self.turn_var.set(f"Turn {state['turns_played'] + 1} / {state['max_turns']}")
        self.pile_var.set(f"Pile: {state['pile_size']} cards")

        # Format player stats for display
        text_lines = []
        for player in state["players"]:
            calls = player["calls"]
            correct = player["correct_calls"]
            call_text = f"Calls: {correct}/{calls}" if calls else "Calls: 0"
            line = f"{player['name']}: {player['card_count']} cards | Truths: {player['truths']} | Lies: {player['lies']} | {call_text}"
            text_lines.append(line)

        # Update the summary text widget
        self.summary.configure(state="normal")
        self.summary.delete("1.0", tk.END)
        self.summary.insert(tk.END, "\n".join(text_lines))
        self.summary.configure(state="disabled")
        self.animate_highlight(self.summary)

    def _set_status(self, text: str, *, highlight_color: str = "#1f6aa5") -> None:
        """Update the status label text with an optional highlight animation."""

        self.status_var.set(text)
        self.animate_highlight(self.status_label, highlight_color=highlight_color)

    def _update_user_hand(self) -> None:
        """Clear and re-render the buttons for the user's hand."""
        for widget in self.hand_frame.winfo_children():
            widget.destroy()

        user = self.game.players[0]
        for idx, card in enumerate(user.hand):
            style = "SelectedCard.TButton" if idx == self._selected_card else "Card.TButton"
            button = ttk.Button(
                self.hand_frame,
                text=str(card),
                style=style,
                command=lambda i=idx: self._select_card(i),
            )
            button.grid(row=0, column=idx, padx=4, pady=4, sticky="ew")

        # Deselect if the card is no longer in hand
        if self._selected_card is not None and self._selected_card >= len(user.hand):
            self._selected_card = None

        if user.hand:
            self.animate_highlight(self.hand_frame)

    def _select_card(self, index: int) -> None:
        """Handle the user selecting a card from their hand."""
        self._selected_card = index
        user = self.game.players[0]
        if 0 <= index < len(user.hand):
            self.claim_rank_var.set(user.hand[index].rank)
        self._update_user_hand()

    def _set_user_controls_state(self, *, enabled: bool) -> None:
        """Enable or disable the user's turn controls."""
        state = "normal" if enabled else "disabled"
        for widget in self.hand_frame.winfo_children():
            widget.configure(state=state)
        self.claim_combo.configure(state="readonly" if enabled else "disabled")
        self.submit_btn.configure(state=state)

    def _set_challenge_controls_state(self, *, enabled: bool) -> None:
        """Enable or disable the challenge buttons."""
        state = "normal" if enabled else "disabled"
        self.call_btn.configure(state=state)
        self.trust_btn.configure(state=state)

    def _log(self, message: str) -> None:
        """Append a message to the game log."""
        self.log.configure(state="normal")
        self.log.insert(tk.END, message + "\n")
        self.log.configure(state="disabled")
        self.log.see(tk.END)

    # ------------------------------------------------------------------
    # Game progression
    # ------------------------------------------------------------------
    def advance_game(self) -> None:
        """Advance the game to the next state, handling both user and bot turns."""
        self._update_scoreboard()
        self._update_user_hand()
        if self.game.finished:
            self._handle_game_end()
            return

        current = self.game.current_player
        if current.is_user:
            # It's the user's turn
            self._set_status("Your turn: choose a card and declare its rank.")
            self._last_claim_text.set("Awaiting your play.")
            self._set_user_controls_state(enabled=True)
            self._set_challenge_controls_state(enabled=False)
        else:
            # It's a bot's turn
            self._set_user_controls_state(enabled=False)
            claim, messages = self.game.play_bot_turn()
            for msg in messages:
                self._log(msg)
            self._log(f"{current.name} claims their card is a {claim.claimed_rank}.")
            self._last_claim_text.set(f"Latest claim: {current.name} says {claim.claimed_rank}.")
            self._update_scoreboard()
            self.root.after(450, self._resolve_challenges)

    def submit_claim(self) -> None:
        """Handle the user's submission of a card claim."""
        if self.game.finished or self.game.current_player is not self.game.players[0]:
            return
        if self._selected_card is None:
            self._set_status("Select a card from your hand first.", highlight_color="#bf3f5f")
            return

        rank = self.claim_rank_var.get().upper()
        try:
            claim = self.game.play_user_turn(self._selected_card, rank)
        except (ValueError, RuntimeError) as exc:
            self._set_status(str(exc), highlight_color="#bf3f5f")
            return

        self._log(f"You play {claim.card} while stating it's a {claim.claimed_rank}.")
        self._last_claim_text.set(f"Latest claim: You said {claim.claimed_rank}.")
        self._selected_card = None
        self._set_user_controls_state(enabled=False)
        self._update_scoreboard()
        self.root.after(200, self._resolve_challenges)

    def _resolve_challenges(self) -> None:
        """Automatically resolve challenges for bots or prompt the user."""
        if self.game.finished:
            self.advance_game()
            return

        while self.game.phase == Phase.CHALLENGE and not self.game.finished:
            challenger = self.game.current_challenger
            if not challenger:
                break

            if challenger.is_user:
                # Prompt the user to challenge or trust
                claimant = self.game.claim_in_progress.claimant
                self._set_status(f"{claimant.name} claims a {self.game.claim_in_progress.claimed_rank}. Challenge?", highlight_color="#1f6aa5")
                self._set_challenge_controls_state(enabled=True)
                return

            # Bot decides whether to challenge
            decision = self.game.bot_should_challenge(challenger)
            self._log(f"{challenger.name} {'challenges the claim!' if decision else 'decides to wait.'}")
            outcome = self.game.evaluate_challenge(decision)
            for line in outcome.messages:
                self._log(line)
            self._update_scoreboard()

        if self.game.phase != Phase.CHALLENGE:
            self.root.after(450, self.advance_game)

    def resolve_user_challenge(self, decision: bool) -> None:
        """Handle the user's decision to challenge or trust a claim."""
        if self.game.phase != Phase.CHALLENGE:
            return
        challenger = self.game.current_challenger
        if not challenger or not challenger.is_user:
            return

        self._set_challenge_controls_state(enabled=False)

        # If challenging, show animation before resolving
        if decision:
            claim = self.game.claim_in_progress
            self._animate_challenge_reveal(claim.truthful, lambda: self._finish_resolve_challenge(decision))
        else:
            self._finish_resolve_challenge(decision)

    def _finish_resolve_challenge(self, decision: bool) -> None:
        """Complete the challenge resolution after any animation."""
        outcome = self.game.evaluate_challenge(decision)
        for line in outcome.messages:
            self._log(line)
        self._update_scoreboard()

        if self.game.phase == Phase.CHALLENGE:
            self.root.after(350, self._resolve_challenges)
        else:
            self.root.after(450, self.advance_game)

    def _handle_game_end(self) -> None:
        """Display the final game outcome."""
        self._set_user_controls_state(enabled=False)
        self._set_challenge_controls_state(enabled=False)

        if self.game.winner is None:
            self._set_status("The match ends in a tie.")
            self._log("The table shares the honours—no single winner.")
        elif self.game.winner.is_user:
            self._set_status("You emptied your hand! Victory is yours.")
            self._log("Congratulations, you outfoxed every bluff.")
        else:
            self._set_status(f"{self.game.winner.name} wins the match.")
            self._log(f"{self.game.winner.name} finishes with the fewest cards.")

        # Save replay if recording was enabled
        if self.game._record_replay:
            replay = self.game.get_replay()
            if replay:
                import datetime
                from pathlib import Path

                replay_dir = Path.home() / ".bluff_replays"
                replay_dir.mkdir(exist_ok=True)
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                replay_file = replay_dir / f"bluff_replay_{timestamp}.json"
                replay.save_to_file(replay_file)
                self._log(f"\nReplay saved to: {replay_file}")

    def _animate_challenge_reveal(self, truthful: bool, callback) -> None:
        """Animate the reveal of a challenge outcome.

        Args:
            truthful: Whether the claim was truthful.
            callback: Function to call after animation completes.
        """
        reveal_label = tk.Label(
            self.root,
            text="REVEALING..." if truthful else "CAUGHT!",
            font=("Segoe UI", 24, "bold"),
            fg="#2ecc71" if truthful else "#e74c3c",
            bg="white",
            padx=24,
            pady=12,
        )
        reveal_label.place(relx=0.5, rely=0.5, anchor="center")

        def finish() -> None:
            reveal_label.destroy()
            callback()

        if not self.config.enable_animations:
            self.root.after(600, finish)
            return

        self.animate_highlight(reveal_label, highlight_color="#2ecc71" if truthful else "#e74c3c", duration=900)
        self.root.after(900, finish)


def run_gui(
    difficulty: DifficultyLevel,
    *,
    rounds: int,
    seed: int | None = None,
    deck_type: DeckType | None = None,
    record_replay: bool = False,
) -> None:
    """Launch the Bluff GUI application.

    Args:
        difficulty (DifficultyLevel): The selected difficulty for the game.
        rounds (int): The number of rounds to play before judging by card count.
        seed (int | None): An optional seed for the random number generator.
        deck_type (DeckType | None): The deck type to use, defaults to Standard.
        record_replay (bool): Whether to record the game for replay.
    """
    rng = random.Random(seed) if seed is not None else random.Random()
    game = BluffGame(
        difficulty,
        rounds=rounds,
        rng=rng,
        record_replay=record_replay,
        seed=seed,
        deck_type=deck_type,
    )
    root = tk.Tk()
    BluffGUI(root, game)
    root.mainloop()
