"""
Tests: merit v2 — topological robustness, persistence telemetry, collapse MDL,
and the log_only / blocking persistence gate.
"""

import numpy as np
import pytest

from nhcs.layer1_genesis.icvp.node import ValidatorNode
from nhcs.layer1_genesis.invariants import compute_betti
from nhcs.layer1_genesis.merit import MERIT_VERSION, MeritEvaluator
from nhcs.layer1_genesis.prt import HypergraphStore
from nhcs.layer1_genesis.rse import CandidateConcept


def _circle(n: int, r: float = 1.0) -> np.ndarray:
    t = np.linspace(0, 2 * np.pi, n, endpoint=False)
    return np.stack([r * np.cos(t), r * np.sin(t)], axis=1)


def _concept(points: np.ndarray, mel: float) -> CandidateConcept:
    profile = compute_betti(points, max_dimension=2, max_edge_length=mel)
    return CandidateConcept(HypergraphStore(), points, profile, iteration=0, rng_seed=0)


def _square(side: float = 1.0) -> np.ndarray:
    """4 points: the loop is born at `side` and dies at the diagonal side*sqrt(2)."""
    return np.array([[0, 0], [side, 0], [side, side], [0, side]], dtype=float)


class TestTopologicalRobustness:
    def test_all_persistent(self):
        assert MeritEvaluator()._topo_consistency([2.0, 0.9]) == 1.0

    def test_all_fragile(self):
        assert MeritEvaluator()._topo_consistency([0.1, 0.3]) == 0.0

    def test_mixed_features_score_as_a_fraction(self):
        assert MeritEvaluator()._topo_consistency([0.1, 0.6]) == 0.5

    def test_threshold_is_configurable(self):
        assert MeritEvaluator(min_persistence_ratio=0.05)._topo_consistency([0.1, 0.3]) == 1.0

    def test_no_higher_features_is_trivially_robust(self):
        assert MeritEvaluator()._topo_consistency([]) == 1.0

    def test_loop_born_near_the_cutoff_can_still_be_robust(self):
        """Birth position alone is misleading: this loop is born at 87% of the
        cutoff but lives ~2x the cutoff beyond it."""
        m = MeritEvaluator().evaluate(_concept(_circle(24), 0.3))
        assert m.topo_robustness == 1.0

class TestPersistenceRatio:
    def test_clean_circle_loop_persists_far_past_the_cutoff(self):
        pts = _circle(24)                      # nearest-neighbour spacing ~0.26
        ratios, factor = MeritEvaluator()._persistence_ratios(pts, 0.3, 2)
        assert factor == 2.0
        assert len(ratios) == 1
        assert ratios[0] > 1.0                 # dies near √3, censored at 2 x 0.3

    def test_count_matches_reported_betti(self):
        rng = np.random.default_rng(0)
        pts = rng.standard_normal((30, 3))
        c = _concept(pts, 0.9)
        ratios, _ = MeritEvaluator()._persistence_ratios(pts, 0.9, 2)
        assert len(ratios) == sum(c.invariant.betti[1:])


class TestCollapseMDL:
    def test_bare_cycle_has_nothing_to_collapse(self):
        # 6 points at spacing 1.0 with cutoff 1.1: a hexagon, every edge load-bearing
        assert MeritEvaluator()._mdl_score(_circle(6), 1.1) == 0.0

    def test_dense_circle_is_mostly_redundant(self):
        assert MeritEvaluator()._mdl_score(_circle(60), 0.5) > 0.5

    def test_bounded_and_varies_across_random_clouds(self):
        rng = np.random.default_rng(1)
        scores = []
        for _ in range(6):
            pts = rng.standard_normal((30, 3))
            c = _concept(pts, 1.0)
            scores.append(MeritEvaluator()._mdl_score(pts, c.invariant.max_edge_length))
        assert all(0.0 <= s <= 1.0 for s in scores)
        assert max(scores) - min(scores) > 0.01   # v1 zlib MDL was a constant 0.0


class TestPersistenceGate:
    def _fragile_concept(self):
        # Square at cutoff 1.05: loop born 1.0, dies 1.414 -> P = 0.39 < 0.5
        return _concept(_square(), 1.05)

    def test_log_only_keeps_robustness_out_of_et(self):
        m = MeritEvaluator("log_only").evaluate(self._fragile_concept())
        assert m.n_reported_features == 1
        assert m.persistence_ratio_median == pytest.approx((2 ** 0.5 - 1) / 1.05)
        assert m.topo_robustness == 0.0
        assert m.epistemic_truth == pytest.approx(0.6 + 0.4 * m.mdl_score)
        assert m.persistence_gate == "log_only"
        assert m.merit_version == MERIT_VERSION

    def test_blocking_lets_robustness_drive_et(self):
        m = MeritEvaluator("blocking").evaluate(self._fragile_concept())
        assert m.epistemic_truth == pytest.approx(0.4 * m.mdl_score)
        assert m.epistemic_truth < 0.5

    def test_validator_rejects_fragile_concept_only_when_blocking(self):
        c = self._fragile_concept()
        assert ValidatorNode(persistence_gate="log_only", noise_std=0.0).evaluate(c, "x").approve
        assert not ValidatorNode(persistence_gate="blocking", noise_std=0.0).evaluate(c, "x").approve

    def test_rejects_unknown_gate(self):
        with pytest.raises(ValueError):
            MeritEvaluator("strict")

    def test_telemetry_fields_populated(self):
        m = MeritEvaluator().evaluate(_concept(_circle(24), 0.3))
        assert m.n_reported_features == 1
        assert m.persistence_ratio_median is not None and m.persistence_ratio_median > 1.0
