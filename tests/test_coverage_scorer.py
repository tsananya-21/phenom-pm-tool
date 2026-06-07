import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.evidence import Dimension, Signal
from pipeline.stage5_coverage import score_coverage


def _sig(dim: Dimension, confidence: float) -> Signal:
    return Signal(
        source_url="https://example.com",
        source_type="job_posting",
        dimension=dim,
        signal_type="test",
        content="test signal",
        raw_snippet="test",
        confidence=confidence,
    )


def test_empty_signals_all_thin():
    scores = score_coverage([])
    for s in scores:
        assert s.is_thin
        assert s.score == 0.0
        assert s.signal_count == 0


def test_single_high_confidence_not_thin():
    signals = [_sig(Dimension.HIRING, 0.9), _sig(Dimension.HIRING, 0.9), _sig(Dimension.HIRING, 0.9)]
    scores = {s.dimension: s for s in score_coverage(signals)}
    assert not scores[Dimension.HIRING].is_thin
    assert scores[Dimension.HIRING].score == 0.9  # 3 * 0.9 / 3.0 ceiling


def test_single_low_confidence_is_thin():
    signals = [_sig(Dimension.RETENTION, 0.2)]
    scores = {s.dimension: s for s in score_coverage(signals)}
    assert scores[Dimension.RETENTION].is_thin
    assert scores[Dimension.RETENTION].score < 0.3


def test_all_dimensions_present():
    signals = [_sig(d, 0.5) for d in Dimension]
    scores = score_coverage(signals)
    assert len(scores) == len(Dimension)
    dims_in_output = {s.dimension for s in scores}
    assert dims_in_output == set(Dimension)


def test_score_capped_at_one():
    signals = [_sig(Dimension.HIRING, 1.0) for _ in range(10)]
    scores = {s.dimension: s for s in score_coverage(signals)}
    assert scores[Dimension.HIRING].score == 1.0
