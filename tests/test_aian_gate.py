"""
Tests: AIAN gate — blocking drops low-novelty candidates, log_only scores
them but lets every candidate through.
"""

from types import SimpleNamespace

import numpy as np
import pytest

from nhcs.layer1_genesis.aian import AIAN


def _candidates(n=4):
    rng = np.random.default_rng(0)
    return [SimpleNamespace(
        invariant=SimpleNamespace(betti=[1, k + 1, 0], euler_characteristic=-k,
                                  complexity_score=1.0),
        point_cloud=rng.standard_normal((30, 3)),
    ) for k in range(n)]


@pytest.fixture(scope="module")
def aian_cls():
    return AIAN


def test_blocking_drops_everything_below_an_unreachable_threshold(aian_cls):
    assert aian_cls(novelty_threshold=1.01).filter(_candidates()) == []


def test_log_only_passes_all_and_still_scores(aian_cls):
    cs = _candidates()
    out = aian_cls(novelty_threshold=1.01, gate="log_only").filter(cs)
    assert out == cs
    assert all(0.0 <= c._novelty_score <= 1.0 for c in out)


def test_log_only_scores_match_blocking_scores(aian_cls):
    a, b = _candidates(), _candidates()
    aian_cls(gate="blocking").filter(a)
    aian_cls(gate="log_only").filter(b)
    assert [c._novelty_score for c in a] == pytest.approx([c._novelty_score for c in b])


def test_unknown_gate_rejected(aian_cls):
    with pytest.raises(ValueError, match="gate"):
        aian_cls(gate="off")
