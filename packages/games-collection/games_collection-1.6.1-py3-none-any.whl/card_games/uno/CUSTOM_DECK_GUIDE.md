# Uno Custom Deck Designer Guide

## Overview

This guide explains how to create and use custom Uno decks with additional cards, colors, and special effects. The
custom deck system allows for creative variations of the classic game.

## Custom Deck Format

Custom decks are defined using JSON or Python dictionaries with the following structure:

```json
{
  "name": "My Custom Deck",
  "description": "A fun variant with extra cards",
  "colors": ["red", "yellow", "green", "blue", "purple", "orange"],
  "cards": [
    {
      "color": "red",
      "value": "0",
      "count": 1
    },
    {
      "color": "red",
      "value": "1",
      "count": 2
    },
    {
      "color": null,
      "value": "wild",
      "count": 4
    },
    {
      "color": "purple",
      "value": "swap",
      "count": 2,
      "effect": "swap_with_any"
    }
  ],
  "special_rules": {
    "custom_actions": {
      "swap": "Player chooses any other player to swap hands with"
    }
  }
}
```

## Implementation

### 1. Custom Card Definition

Extend the `UnoCard` class to support custom effects:

```python
@dataclass(frozen=True)
class CustomUnoCard(UnoCard):
    """Extended Uno card with custom effects."""
    effect: Optional[str] = None
    effect_params: Optional[Dict[str, Any]] = None

    def has_custom_effect(self) -> bool:
        return self.effect is not None
```

### 2. Custom Deck Loader

```python
class CustomDeckLoader:
    """Loads and validates custom Uno deck definitions."""

    @staticmethod
    def load_from_file(filepath: str) -> Dict:
        """Load a custom deck from a JSON file."""
        with open(filepath, 'r') as f:
            deck_def = json.load(f)
        CustomDeckLoader.validate(deck_def)
        return deck_def

    @staticmethod
    def validate(deck_def: Dict) -> None:
        """Validate deck definition structure."""
        required_keys = ['name', 'colors', 'cards']
        for key in required_keys:
            if key not in deck_def:
                raise ValueError(f"Missing required key: {key}")

        # Validate colors
        if len(deck_def['colors']) < 2:
            raise ValueError("Deck must have at least 2 colors")

        # Validate cards
        if len(deck_def['cards']) < 20:
            raise ValueError("Deck must have at least 20 cards")

        # Validate card structure
        for card in deck_def['cards']:
            if 'value' not in card or 'count' not in card:
                raise ValueError("Each card must have 'value' and 'count'")

    @staticmethod
    def create_deck(deck_def: Dict, rng: Optional[random.Random] = None) -> UnoDeck:
        """Create a UnoDeck from a deck definition."""
        deck = UnoDeck(rng=rng)
        deck.cards.clear()

        for card_def in deck_def['cards']:
            color = card_def.get('color')
            value = card_def['value']
            count = card_def['count']

            for _ in range(count):
                if 'effect' in card_def:
                    # Custom card with effect
                    deck.cards.append(CustomUnoCard(
                        color=color,
                        value=value,
                        effect=card_def['effect'],
                        effect_params=card_def.get('effect_params')
                    ))
                else:
                    # Standard card
                    deck.cards.append(UnoCard(color=color, value=value))

        deck.shuffle()
        return deck
```

### 3. Custom Effect Handler

```python
class CustomEffectHandler:
    """Handles custom card effects in the game."""

    def __init__(self, game: UnoGame):
        self.game = game
        self.handlers = {
            'swap_with_any': self._handle_swap_with_any,
            'steal_card': self._handle_steal_card,
            'gift_card': self._handle_gift_card,
            'peek_hand': self._handle_peek_hand,
            'block': self._handle_block,
        }

    def apply_effect(self, card: CustomUnoCard, player: UnoPlayer) -> None:
        """Apply the custom effect of a card."""
        if card.effect in self.handlers:
            self.handlers[card.effect](card, player)
        else:
            raise ValueError(f"Unknown effect: {card.effect}")

    def _handle_swap_with_any(self, card: CustomUnoCard, player: UnoPlayer) -> None:
        """Allow player to swap hands with any other player."""
        target_idx = self.game.interface.choose_swap_target(player, self.game.players)
        if target_idx is not None:
            target = self.game.players[target_idx]
            self.game._swap_hands(player, target)

    def _handle_steal_card(self, card: CustomUnoCard, player: UnoPlayer) -> None:
        """Steal a random card from another player."""
        target_idx = self.game.interface.choose_swap_target(player, self.game.players)
        if target_idx is not None:
            target = self.game.players[target_idx]
            if target.hand:
                stolen_idx = self.game.rng.randint(0, len(target.hand) - 1)
                stolen_card = target.hand.pop(stolen_idx)
                player.hand.append(stolen_card)
                self.game._log(
                    f"{player.name} steals a card from {target.name}!",
                    Fore.MAGENTA
                )

    def _handle_gift_card(self, card: CustomUnoCard, player: UnoPlayer) -> None:
        """Give a card to another player."""
        if len(player.hand) > 1:
            card_idx = self.game.interface.choose_card_to_give(player)
            target_idx = self.game.interface.choose_swap_target(player, self.game.players)
            if card_idx is not None and target_idx is not None:
                given_card = player.hand.pop(card_idx)
                self.game.players[target_idx].hand.append(given_card)

    def _handle_peek_hand(self, card: CustomUnoCard, player: UnoPlayer) -> None:
        """Peek at another player's hand."""
        target_idx = self.game.interface.choose_swap_target(player, self.game.players)
        if target_idx is not None:
            target = self.game.players[target_idx]
            self.game.interface.show_peek_result(target.hand)

    def _handle_block(self, card: CustomUnoCard, player: UnoPlayer) -> None:
        """Block the next player's turn (like skip but with special visual)."""
        self.game._log(f"{player.name} blocks the next player!", Fore.RED)
        # Similar to skip effect
```

### 4. Integration with UnoGame

Modify `UnoGame` to support custom decks:

```python
class UnoGame:
    def __init__(
        self,
        *,
        players: Sequence[UnoPlayer],
        rng: Optional[random.Random] = None,
        interface: Optional[UnoInterface] = None,
        house_rules: Optional[HouseRules] = None,
        team_mode: bool = False,
        custom_deck: Optional[Dict] = None,  # New parameter
    ) -> None:
        # ... existing initialization ...

        if custom_deck:
            self.deck = CustomDeckLoader.create_deck(custom_deck, rng=self.rng)
            self.custom_effect_handler = CustomEffectHandler(self)
        else:
            self.deck = UnoDeck(rng=self.rng)
            self.custom_effect_handler = None
```

## Example Custom Decks

### 1. Rainbow Deck

```json
{
  "name": "Rainbow Deck",
  "description": "Uno with 6 colors and extra wildcards",
  "colors": ["red", "yellow", "green", "blue", "purple", "orange"],
  "cards": [
    { "color": "red", "value": "0", "count": 1 },
    { "color": "red", "value": "1", "count": 2 },
    { "color": "red", "value": "2", "count": 2 },
    { "color": "red", "value": "3", "count": 2 },
    { "color": "red", "value": "4", "count": 2 },
    { "color": "red", "value": "5", "count": 2 },
    { "color": "red", "value": "6", "count": 2 },
    { "color": "red", "value": "7", "count": 2 },
    { "color": "red", "value": "8", "count": 2 },
    { "color": "red", "value": "9", "count": 2 },
    { "color": "red", "value": "skip", "count": 2 },
    { "color": "red", "value": "reverse", "count": 2 },
    { "color": "red", "value": "+2", "count": 2 }
  ]
}
```

### 2. Extreme Uno

```json
{
  "name": "Extreme Uno",
  "description": "High-stakes Uno with powerful special cards",
  "colors": ["red", "yellow", "green", "blue"],
  "cards": [
    { "color": null, "value": "mega-wild", "count": 2, "effect": "swap_with_any" },
    { "color": null, "value": "steal", "count": 4, "effect": "steal_card" },
    { "color": null, "value": "gift", "count": 2, "effect": "gift_card" },
    { "color": null, "value": "+6", "count": 2 }
  ]
}
```

### 3. Speed Uno

```json
{
  "name": "Speed Uno",
  "description": "Faster gameplay with fewer numbers",
  "colors": ["red", "yellow", "green", "blue"],
  "cards": [
    { "color": "red", "value": "1", "count": 3 },
    { "color": "red", "value": "2", "count": 3 },
    { "color": "red", "value": "3", "count": 3 },
    { "color": "red", "value": "skip", "count": 3 },
    { "color": "red", "value": "reverse", "count": 3 }
  ]
}
```

## Deck Designer Tool

Create a visual deck designer tool:

```python
class DeckDesignerGUI:
    """GUI application for designing custom Uno decks."""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Uno Custom Deck Designer")
        self.deck_def = {
            "name": "New Deck",
            "colors": list(COLORS),
            "cards": []
        }
        self._build_ui()

    def _build_ui(self):
        # Deck properties
        tk.Label(self.root, text="Deck Name:").pack()
        self.name_entry = tk.Entry(self.root)
        self.name_entry.pack()

        # Color selector
        tk.Label(self.root, text="Colors:").pack()
        self.color_frame = tk.Frame(self.root)
        self.color_frame.pack()

        # Card list
        tk.Label(self.root, text="Cards:").pack()
        self.card_list = tk.Listbox(self.root, height=10)
        self.card_list.pack()

        # Add card controls
        tk.Button(self.root, text="Add Card", command=self.add_card).pack()
        tk.Button(self.root, text="Remove Card", command=self.remove_card).pack()

        # Export buttons
        tk.Button(self.root, text="Export JSON", command=self.export_json).pack()
        tk.Button(self.root, text="Test Deck", command=self.test_deck).pack()

    def add_card(self):
        # Open dialog to configure new card
        pass

    def export_json(self):
        filepath = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")]
        )
        if filepath:
            with open(filepath, 'w') as f:
                json.dump(self.deck_def, f, indent=2)
```

## Command-Line Usage

```bash
# Play with a custom deck
python -m card_games.uno --custom-deck decks/rainbow.json

# Create a new deck
python -m card_games.uno.deck_designer

# Validate a deck file
python -m card_games.uno.validate_deck decks/extreme.json
```

## Best Practices

1. **Balance**: Ensure no single card is too powerful
1. **Testing**: Playtest custom decks thoroughly
1. **Clarity**: Clearly document custom effects
1. **Compatibility**: Make sure custom cards work with house rules
1. **Validation**: Always validate deck files before use

## Advanced Features

### Dynamic Card Effects

```python
class DynamicEffect:
    """Card effect that can be modified during runtime."""

    def __init__(self, effect_type: str, params: Dict[str, Any]):
        self.effect_type = effect_type
        self.params = params

    def execute(self, game: UnoGame, player: UnoPlayer) -> None:
        # Execute effect with parameters
        if self.effect_type == "conditional_draw":
            # Draw X cards if condition is met
            condition = self.params.get("condition")
            amount = self.params.get("amount", 2)
            if self._check_condition(game, condition):
                game._draw_cards(player, amount)
```

### Card Rarity System

```json
{
  "card": {
    "color": "gold",
    "value": "ultimate",
    "count": 1,
    "rarity": "legendary",
    "effect": "win_game",
    "condition": "can_only_play_if_hand_size_1"
  }
}
```

## Future Enhancements

- Visual card designer with drag-and-drop
- Card artwork customization
- Effect scripting language
- Online deck sharing
- Deck rating and reviews
- Tournament-legal deck validation
- Deck statistics and balance analysis
