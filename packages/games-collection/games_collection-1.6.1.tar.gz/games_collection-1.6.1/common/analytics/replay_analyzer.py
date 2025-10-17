"""Replay analysis tools for game strategy analysis.

This module provides tools for analyzing game replays to detect patterns,
evaluate strategies, and provide insights into gameplay.
"""

from __future__ import annotations

import json
import pathlib
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional


@dataclass
class MovePattern:
    """Represents a detected pattern in game moves.

    A pattern is a sequence of moves that occurs repeatedly
    or has strategic significance.
    """

    pattern_id: str
    description: str
    occurrences: int = 0
    positions: List[int] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_occurrence(self, position: int, meta: Optional[Dict] = None) -> None:
        """Record an occurrence of this pattern.

        Args:
            position: Position in the move sequence.
            meta: Optional metadata about this occurrence.
        """
        self.occurrences += 1
        self.positions.append(position)
        if meta:
            self.metadata[f"occurrence_{position}"] = meta


@dataclass
class ReplayAnalyzer:
    """Analyzer for game replays.

    Provides tools for analyzing game replays to extract insights,
    detect patterns, and evaluate strategy quality.
    """

    game_name: str
    move_history: List[Dict[str, Any]] = field(default_factory=list)
    patterns: Dict[str, MovePattern] = field(default_factory=dict)
    analysis_results: Dict[str, Any] = field(default_factory=dict)

    def load_replay(self, filepath: pathlib.Path) -> None:
        """Load replay data from file.

        Args:
            filepath: Path to replay file.
        """
        with open(filepath) as f:
            data = json.load(f)

        self.move_history = data.get("moves", [])
        if "game_name" in data:
            self.game_name = data["game_name"]

    def add_move(self, move_data: Dict[str, Any]) -> None:
        """Add a move to the history.

        Args:
            move_data: Dictionary containing move information.
        """
        self.move_history.append(move_data)

    def detect_pattern(
        self,
        pattern_id: str,
        description: str,
        detector: Callable[[List[Dict[str, Any]]], List[int]],
    ) -> MovePattern:
        """Detect a pattern in the move history.

        Args:
            pattern_id: Unique identifier for the pattern.
            description: Human-readable pattern description.
            detector: Function that returns positions where pattern occurs.

        Returns:
            MovePattern with detected occurrences.
        """
        if pattern_id not in self.patterns:
            self.patterns[pattern_id] = MovePattern(
                pattern_id=pattern_id,
                description=description,
            )

        pattern = self.patterns[pattern_id]
        positions = detector(self.move_history)

        for pos in positions:
            pattern.add_occurrence(pos)

        return pattern

    def analyze_opening(self, num_moves: int = 5) -> Dict[str, Any]:
        """Analyze opening moves.

        Args:
            num_moves: Number of opening moves to analyze.

        Returns:
            Dictionary with opening analysis results.
        """
        opening_moves = self.move_history[:num_moves]

        analysis = {
            "num_moves": len(opening_moves),
            "moves": opening_moves,
            "common_patterns": [],
        }

        self.analysis_results["opening"] = analysis
        return analysis

    def analyze_endgame(self, num_moves: int = 5) -> Dict[str, Any]:
        """Analyze endgame moves.

        Args:
            num_moves: Number of endgame moves to analyze.

        Returns:
            Dictionary with endgame analysis results.
        """
        endgame_moves = self.move_history[-num_moves:] if len(self.move_history) >= num_moves else self.move_history

        analysis = {
            "num_moves": len(endgame_moves),
            "moves": endgame_moves,
            "efficiency": self._calculate_efficiency(endgame_moves),
        }

        self.analysis_results["endgame"] = analysis
        return analysis

    def _calculate_efficiency(self, moves: List[Dict[str, Any]]) -> float:
        """Calculate move efficiency.

        Args:
            moves: List of moves to analyze.

        Returns:
            Efficiency score (0-1).
        """
        if not moves:
            return 0.0

        # Simple efficiency based on move quality if available
        total_quality = 0.0
        count = 0

        for move in moves:
            if "quality" in move:
                total_quality += move["quality"]
                count += 1

        if count == 0:
            return 0.5  # Default neutral efficiency

        return total_quality / count

    def get_move_frequency(self, player_id: Optional[str] = None) -> Dict[str, int]:
        """Calculate move frequency distribution.

        Args:
            player_id: Optional player to filter by.

        Returns:
            Dictionary mapping move types to frequencies.
        """
        frequency: Dict[str, int] = {}

        for move in self.move_history:
            if player_id and move.get("player_id") != player_id:
                continue

            move_type = move.get("type", "unknown")
            frequency[move_type] = frequency.get(move_type, 0) + 1

        return frequency

    def get_position_heatmap_data(self) -> Dict[str, int]:
        """Generate data for position heatmap.

        Returns:
            Dictionary mapping positions to frequency of play.
        """
        heatmap: Dict[str, int] = {}

        for move in self.move_history:
            position = move.get("position")
            if position:
                # Convert position to string key
                pos_key = str(position)
                heatmap[pos_key] = heatmap.get(pos_key, 0) + 1

        return heatmap

    def calculate_critical_moments(self, threshold: float = 0.7) -> List[Dict[str, Any]]:
        """Identify critical moments in the game.

        Args:
            threshold: Threshold for determining criticality.

        Returns:
            List of critical moments with context.
        """
        critical_moments = []

        for i, move in enumerate(self.move_history):
            criticality = move.get("criticality", 0.5)

            if criticality >= threshold:
                critical_moments.append(
                    {
                        "position": i,
                        "move": move,
                        "criticality": criticality,
                    }
                )

        return critical_moments

    def get_summary(self) -> str:
        """Generate analysis summary.

        Returns:
            Formatted summary string.
        """
        lines = [
            f"=== Replay Analysis: {self.game_name} ===",
            f"Total Moves: {len(self.move_history)}",
            "",
        ]

        if self.patterns:
            lines.append("Detected Patterns:")
            for pattern in self.patterns.values():
                lines.append(f"  {pattern.description}: {pattern.occurrences} occurrences")
            lines.append("")

        if "opening" in self.analysis_results:
            opening = self.analysis_results["opening"]
            lines.append(f"Opening Analysis: {opening['num_moves']} moves analyzed")

        if "endgame" in self.analysis_results:
            endgame = self.analysis_results["endgame"]
            lines.append(f"Endgame Analysis: Efficiency {endgame['efficiency']:.2%}")

        return "\n".join(lines)

    def save_analysis(self, filepath: pathlib.Path) -> None:
        """Save analysis results to file.

        Args:
            filepath: Path to save file.
        """
        data = {
            "game_name": self.game_name,
            "move_history": self.move_history,
            "patterns": {
                pid: {
                    "pattern_id": p.pattern_id,
                    "description": p.description,
                    "occurrences": p.occurrences,
                    "positions": p.positions,
                    "metadata": p.metadata,
                }
                for pid, p in self.patterns.items()
            },
            "analysis_results": self.analysis_results,
        }

        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)

    @classmethod
    def load_analysis(cls, filepath: pathlib.Path) -> ReplayAnalyzer:
        """Load analysis from file.

        Args:
            filepath: Path to load from.

        Returns:
            ReplayAnalyzer instance.
        """
        with open(filepath) as f:
            data = json.load(f)

        analyzer = cls(game_name=data.get("game_name", "Unknown"))
        analyzer.move_history = data.get("move_history", [])

        # Reconstruct patterns
        for pid, pdata in data.get("patterns", {}).items():
            pattern = MovePattern(
                pattern_id=pdata["pattern_id"],
                description=pdata["description"],
                occurrences=pdata["occurrences"],
                positions=pdata["positions"],
                metadata=pdata["metadata"],
            )
            analyzer.patterns[pid] = pattern

        analyzer.analysis_results = data.get("analysis_results", {})

        return analyzer
