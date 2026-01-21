from __future__ import annotations

import math


def expected_score(rating_a: float, rating_b: float) -> float:
    """
    Standard Elo expected score.
    """

    return 1.0 / (1.0 + math.pow(10.0, (rating_b - rating_a) / 400.0))


def _distribute(total: int, n: int) -> list[int]:
    """
    Distribute an integer `total` into `n` integers as evenly as possible.

    - sum(deltas) == total
    - deltas differ by at most 1
    - deterministic
    """

    if n <= 0:
        raise ValueError("n must be positive")

    sign = -1 if total < 0 else 1
    total_abs = abs(total)

    base, rem = divmod(total_abs, n)
    deltas = [base] * n
    for i in range(rem):
        deltas[i] += 1

    if sign < 0:
        deltas = [-d for d in deltas]
    return deltas


def team_elo_deltas(
    team1_ratings: list[int],
    team2_ratings: list[int],
    score_team1: float,
    *,
    k: int = 32,
) -> tuple[list[int], list[int], float]:
    """
    Elo-like rating update for **two teams** (team-vs-team).

    - Team strength is estimated by average rating.
    - Rating change is computed for the match, then distributed across members.
    - Total rating change across all players is kept at 0 (except rounding effects are contained).
    """

    if not team1_ratings or not team2_ratings:
        raise ValueError("Both teams must be non-empty")
    if score_team1 < 0.0 or score_team1 > 1.0:
        raise ValueError("score_team1 must be in [0, 1]")

    avg1 = sum(team1_ratings) / len(team1_ratings)
    avg2 = sum(team2_ratings) / len(team2_ratings)
    exp1 = expected_score(avg1, avg2)

    total1 = int(round(k * (score_team1 - exp1)))
    total2 = -total1

    deltas1 = _distribute(total1, len(team1_ratings))
    deltas2 = _distribute(total2, len(team2_ratings))
    return deltas1, deltas2, exp1

