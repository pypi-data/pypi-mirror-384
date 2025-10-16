"""Farkle dice game implementation.

Farkle is a risk-based scoring game where players roll dice and can choose
to stop and bank their points or continue rolling to accumulate more points,
with the risk of "farkling" (getting no scoring dice) and losing all points
for that turn.
"""

from __future__ import annotations

__all__ = ["FarkleGame"]

from .farkle import FarkleGame
