"""Analytics and metrics system for game statistics tracking.

This module provides comprehensive analytics capabilities including:
- Game statistics tracking (wins, losses, streaks)
- Performance metrics (average game time, decision time)
- Data visualization dashboards
- AI opponent difficulty rating system
- Skill rating systems (ELO, Glicko-2)
- Game replay analysis tools
- Heatmaps for strategy analysis
"""

from __future__ import annotations

from .game_stats import GameStatistics, PlayerStats
from .performance_metrics import DecisionMetrics, PerformanceMetrics
from .rating_systems import EloRating, GlickoRating
from .replay_analyzer import MovePattern, ReplayAnalyzer
from .visualization import Dashboard, Heatmap

__all__ = [
    "GameStatistics",
    "PlayerStats",
    "PerformanceMetrics",
    "DecisionMetrics",
    "EloRating",
    "GlickoRating",
    "ReplayAnalyzer",
    "MovePattern",
    "Dashboard",
    "Heatmap",
]
