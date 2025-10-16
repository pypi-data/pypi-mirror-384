# Recommendation System Overview

This document explains how the personalised recommendation pipeline is assembled and how to extend it.

## Architecture Summary

- **Service**: `common.recommendation_service.RecommendationService`
- **Inputs**:
  - `PlayerProfile` data (favourites, win rates, playtime)
  - Analytics from `common.analytics.game_stats`
  - Game metadata catalog (`GameDescriptor` instances)
- **Outputs**:
  - Ordered list of `RecommendationResult` objects for launcher/post-game surfaces
  - Explanatory text snippets (e.g., "You enjoy trick-taking games; try Spades")

### Scoring Pipeline

1. **Collaborative Signals** (`RecommendationWeights.collaborative`)
   - Popularity normalised by total community games played
1. **Challenge Signals** (`RecommendationWeights.challenge`)
   - Frequency of challenge completions recorded in analytics history
1. **Content Signals** (`RecommendationWeights.content`)
   - Mechanics overlap with favourites (Jaccard similarity)
   - Session length alignment and familiarity bonuses for lightly-played titles

The final score is `Σ component_score * weight`, adjusted by cached player feedback. Weights are configurable through `RecommendationWeights` when instantiating the service.

### Caching and Feedback

`PlayerProfile` now contains a `RecommendationCache` which stores:

- The last generated recommendations (with timestamps)
- Acceptance/ignore counts per game

The cache avoids recomputation until the configured TTL elapses. Feedback records tune the score via a multiplier so ignored games gradually fall down the list.

### Extending the System

- Add new metadata to `GameDescriptor` and incorporate it inside `_content_score`
- Update `RecommendationWeights` to include new components (ensure `.normalised()` reflects the change)
- When adding analytics fields, extend `_calculate_popularity` or `_calculate_challenge_completion`
- Keep functions below cyclomatic complexity 10 by splitting helpers as needed

## Launcher / Post-Game Integration

The recommendation service is UI-agnostic. Surfaces should:

1. Instantiate a `RecommendationService` with the shared metadata catalog
1. Call `service.recommend(profile, analytics)` when entering the launcher or after a game ends
1. Display `RecommendationResult.explanation` as the lead copy and list `reasons` for extra context
1. Report player choices with `service.record_feedback(profile, game_id, accepted)` to refine future suggestions

## Testing Guidance

- `tests/test_recommendation_service.py` illustrates how to create deterministic analytics fixtures
- When altering scoring, update or extend unit tests to cover new pathways
- Aim for >=90% coverage on new logic and keep test docstrings descriptive
