"""Data visualization tools for analytics dashboards.

This module provides tools for creating dashboards, charts, and heatmaps
to visualize game statistics and analytics data.
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple


class Heatmap:
    """Heatmap generator for strategy analysis.

    Creates ASCII/text-based heatmaps showing position frequency,
    move quality, or other spatial data.
    """

    def __init__(self, width: int, height: int) -> None:
        """Initialize heatmap.

        Args:
            width: Width of the heatmap grid.
            height: Height of the heatmap grid.
        """
        self.width = width
        self.height = height
        self.data: Dict[Tuple[int, int], float] = {}

    def set_value(self, x: int, y: int, value: float) -> None:
        """Set value at position.

        Args:
            x: X coordinate.
            y: Y coordinate.
            value: Value to set.
        """
        if 0 <= x < self.width and 0 <= y < self.height:
            self.data[(x, y)] = value

    def get_value(self, x: int, y: int) -> float:
        """Get value at position.

        Args:
            x: X coordinate.
            y: Y coordinate.

        Returns:
            Value at position, or 0.0 if not set.
        """
        return self.data.get((x, y), 0.0)

    def increment(self, x: int, y: int, amount: float = 1.0) -> None:
        """Increment value at position.

        Args:
            x: X coordinate.
            y: Y coordinate.
            amount: Amount to increment by.
        """
        current = self.get_value(x, y)
        self.set_value(x, y, current + amount)

    def normalize(self) -> None:
        """Normalize all values to 0-1 range."""
        if not self.data:
            return

        max_val = max(self.data.values())
        if max_val > 0:
            for key in self.data:
                self.data[key] = self.data[key] / max_val

    def render_ascii(self, chars: str = " .:-=+*#%@") -> str:
        """Render heatmap as ASCII art.

        Args:
            chars: Characters to use for intensity (lowest to highest).

        Returns:
            ASCII representation of heatmap.
        """
        lines = []

        for y in range(self.height):
            row = []
            for x in range(self.width):
                value = self.get_value(x, y)
                # Map value to character index
                char_idx = int(value * (len(chars) - 1))
                char_idx = min(max(char_idx, 0), len(chars) - 1)
                row.append(chars[char_idx])
            lines.append(" ".join(row))

        return "\n".join(lines)

    def render_numeric(self, precision: int = 2) -> str:
        """Render heatmap with numeric values.

        Args:
            precision: Number of decimal places.

        Returns:
            Numeric representation of heatmap.
        """
        lines = []

        for y in range(self.height):
            row = []
            for x in range(self.width):
                value = self.get_value(x, y)
                row.append(f"{value:.{precision}f}")
            lines.append(" | ".join(row))

        return "\n".join(lines)

    def get_hotspots(self, threshold: float = 0.7) -> List[Tuple[int, int, float]]:
        """Identify hotspots (high-value positions).

        Args:
            threshold: Minimum value to be considered a hotspot.

        Returns:
            List of (x, y, value) tuples for hotspots.
        """
        hotspots = []

        for (x, y), value in self.data.items():
            if value >= threshold:
                hotspots.append((x, y, value))

        return sorted(hotspots, key=lambda item: item[2], reverse=True)


class Dashboard:
    """Analytics dashboard for displaying statistics.

    Creates formatted text-based dashboards for displaying
    various game statistics and metrics.
    """

    def __init__(self, title: str, width: int = 80) -> None:
        """Initialize dashboard.

        Args:
            title: Dashboard title.
            width: Width of the dashboard in characters.
        """
        self.title = title
        self.width = width
        self.sections: List[Dict[str, Any]] = []

    def add_section(
        self,
        title: str,
        content: List[str],
        style: str = "default",
    ) -> None:
        """Add a section to the dashboard.

        Args:
            title: Section title.
            content: List of content lines.
            style: Display style ('default', 'boxed', 'minimal').
        """
        self.sections.append(
            {
                "title": title,
                "content": content,
                "style": style,
            }
        )

    def add_stat(
        self,
        section_title: str,
        stat_name: str,
        stat_value: Any,
        format_spec: str = "",
    ) -> None:
        """Add a statistic to a section.

        Args:
            section_title: Title of section to add to.
            stat_name: Name of the statistic.
            stat_value: Value of the statistic.
            format_spec: Optional format specification.
        """
        # Find or create section
        section = None
        for s in self.sections:
            if s["title"] == section_title:
                section = s
                break

        if section is None:
            section = {
                "title": section_title,
                "content": [],
                "style": "default",
            }
            self.sections.append(section)

        # Format the value
        if format_spec:
            formatted_value = f"{stat_value:{format_spec}}"
        else:
            formatted_value = str(stat_value)

        section["content"].append(f"{stat_name}: {formatted_value}")

    def add_chart(
        self,
        section_title: str,
        data: Dict[str, float],
        max_width: int = 40,
    ) -> None:
        """Add a simple bar chart to a section.

        Args:
            section_title: Title of section to add to.
            data: Dictionary mapping labels to values.
            max_width: Maximum width of bars in characters.
        """
        if not data:
            return

        max_value = max(data.values())

        chart_lines = []
        for label, value in data.items():
            if max_value > 0:
                bar_width = int((value / max_value) * max_width)
            else:
                bar_width = 0

            bar = "█" * bar_width
            chart_lines.append(f"{label:15s} {bar} {value}")

        # Find or create section
        section = None
        for s in self.sections:
            if s["title"] == section_title:
                section = s
                break

        if section is None:
            section = {
                "title": section_title,
                "content": [],
                "style": "default",
            }
            self.sections.append(section)

        section["content"].extend(chart_lines)

    def render(self) -> str:
        """Render the complete dashboard.

        Returns:
            Formatted dashboard string.
        """
        lines = []

        # Title
        lines.append("=" * self.width)
        lines.append(self.title.center(self.width))
        lines.append("=" * self.width)
        lines.append("")

        # Sections
        for section in self.sections:
            if section["style"] == "boxed":
                lines.append("+" + "-" * (self.width - 2) + "+")
                lines.append("| " + section["title"].ljust(self.width - 4) + " |")
                lines.append("+" + "-" * (self.width - 2) + "+")
                for line in section["content"]:
                    lines.append("| " + line.ljust(self.width - 4) + " |")
                lines.append("+" + "-" * (self.width - 2) + "+")
            elif section["style"] == "minimal":
                lines.append(section["title"])
                lines.extend(section["content"])
            else:  # default
                lines.append("")
                lines.append(f"--- {section['title']} ---")
                lines.extend(section["content"])

            lines.append("")

        lines.append("=" * self.width)

        return "\n".join(lines)

    def clear(self) -> None:
        """Clear all sections from the dashboard."""
        self.sections.clear()


def create_leaderboard_display(
    players: List[Tuple[str, Any]],
    title: str = "Leaderboard",
    max_entries: int = 10,
) -> str:
    """Create a formatted leaderboard display.

    Args:
        players: List of (player_id, score/rating) tuples.
        title: Leaderboard title.
        max_entries: Maximum number of entries to display.

    Returns:
        Formatted leaderboard string.
    """
    lines = [
        "=" * 60,
        title.center(60),
        "=" * 60,
        "",
    ]

    for i, (player_id, score) in enumerate(players[:max_entries], 1):
        # Add medal emoji for top 3
        if i == 1:
            prefix = "🥇"
        elif i == 2:
            prefix = "🥈"
        elif i == 3:
            prefix = "🥉"
        else:
            prefix = f"{i:2d}."

        # Format score
        if isinstance(score, float):
            score_str = f"{score:.2f}"
        else:
            score_str = str(score)

        lines.append(f"  {prefix} {player_id:30s} {score_str:>10s}")

    lines.append("")
    lines.append("=" * 60)

    return "\n".join(lines)


def create_comparison_chart(
    categories: List[str],
    player_a_data: List[float],
    player_b_data: List[float],
    player_a_name: str = "Player A",
    player_b_name: str = "Player B",
) -> str:
    """Create a comparison chart between two players.

    Args:
        categories: List of category names.
        player_a_data: Data for player A.
        player_b_data: Data for player B.
        player_a_name: Name of player A.
        player_b_name: Name of player B.

    Returns:
        Formatted comparison chart.
    """
    lines = [
        "=" * 80,
        f"Comparison: {player_a_name} vs {player_b_name}".center(80),
        "=" * 80,
        "",
    ]

    max_value = max(max(player_a_data), max(player_b_data))
    bar_width = 30

    for category, val_a, val_b in zip(categories, player_a_data, player_b_data):
        # Normalize values
        if max_value > 0:
            width_a = int((val_a / max_value) * bar_width)
            width_b = int((val_b / max_value) * bar_width)
        else:
            width_a = width_b = 0

        bar_a = "█" * width_a
        bar_b = "█" * width_b

        lines.append(f"{category:20s}")
        lines.append(f"  {player_a_name:15s} {bar_a} {val_a:.2f}")
        lines.append(f"  {player_b_name:15s} {bar_b} {val_b:.2f}")
        lines.append("")

    lines.append("=" * 80)

    return "\n".join(lines)
