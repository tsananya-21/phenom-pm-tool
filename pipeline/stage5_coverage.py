"""
Stage 5 — Coverage Scoring

Per dimension: sum of signal confidences, normalized against an expected
ceiling of 3.0 total confidence (3 medium-confidence signals = full coverage).
is_thin = True if score < 0.3.

Coverage scores flow into both the UI and the synthesis prompt,
where thin dimensions trigger hedge language in the model output.
"""
from __future__ import annotations

from models.evidence import CoverageScore, Dimension, Signal

_EXPECTED_MAX = 3.0  # ceiling total confidence per dimension


def score_coverage(signals: list[Signal]) -> list[CoverageScore]:
    scores: list[CoverageScore] = []
    for dim in Dimension:
        dim_signals = [s for s in signals if s.dimension == dim]
        if not dim_signals:
            scores.append(CoverageScore(
                dimension=dim,
                score=0.0,
                signal_count=0,
                is_thin=True,
                thin_reason="No signals found",
            ))
            continue

        raw = sum(s.confidence for s in dim_signals)
        score = min(raw / _EXPECTED_MAX, 1.0)
        is_thin = score < 0.3

        scores.append(CoverageScore(
            dimension=dim,
            score=round(score, 2),
            signal_count=len(dim_signals),
            is_thin=is_thin,
            thin_reason=(
                f"Only {len(dim_signals)} signal(s) with low total confidence ({raw:.1f})"
                if is_thin else None
            ),
        ))

    return scores
