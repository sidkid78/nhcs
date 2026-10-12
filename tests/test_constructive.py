"""
Tests: pushout-based constructive generator (RSE mode="pushout").
"""

import numpy as np
import pytest

from nhcs.layer1_genesis.constructive import PushoutGenerator
from nhcs.layer1_genesis.invariants import compute_betti
from nhcs.layer1_genesis.merit import MeritEvaluator
from nhcs.layer1_genesis.rse import RecursiveSynthesisEngine


def _gen(seed=0, **kw):
    return PushoutGenerator(rng=np.random.default_rng(seed), **kw)


class TestCompose:
    @pytest.mark.parametrize("seed", range(8))
    def test_betti_follow_mayer_vietoris_bookkeeping(self, seed):
        """First circle gives one cycle; a circle glued at k points adds k cycles
        (1 of its own + k-1 from ker φ0); each sphere adds one void."""
        k, edges, spheres, cons = _gen(seed, sphere_prob=0.3).compose()
        circles = [s for s in cons.steps if s["primitive"] == "circle"]
        expected_b1 = 1 + sum(s["glue_points"] for s in circles[1:])
        assert cons.predicted_betti == [1, expected_b1, len(spheres)]
        assert k.betti(2) == cons.predicted_betti

    def test_circle_graph_homology_matches(self):
        """The circle edges alone carry all of β1 (spheres are wedged at one point)."""
        from nhcs.layer1_genesis.pushout import SimplicialComplex
        k, edges, spheres, cons = _gen(3, sphere_prob=0.5).compose()
        graph = SimplicialComplex.from_simplices(edges)
        assert graph.betti(2)[:2] == [1, cons.predicted_betti[1]]

    def test_kernel_dimension_recorded(self):
        _, _, _, cons = _gen(1, sphere_prob=0.0, max_glue_points=3).compose()
        for s in cons.steps[1:]:
            assert s["kernel_phi0"] == s["glue_points"] - 1


class TestGenerate:
    def test_emitted_concepts_have_verified_betti(self):
        g = _gen(0)
        concepts = g.run(10)
        assert len(concepts) >= 5
        for c in concepts:
            assert c.invariant.betti == c.construction["predicted_betti"]
            assert c.invariant.max_edge_length == pytest.approx(g.cutoff)
            again = compute_betti(c.point_cloud, max_dimension=2, max_edge_length=g.cutoff)
            assert again.betti == c.invariant.betti
            assert c.construction["n_points"] == len(c.point_cloud)
            assert c.store.n_nodes() == len(c.point_cloud)

    def test_stats_add_up(self):
        g = _gen(2)
        out = g.run(6)
        assert g.stats["emitted"] == len(out)
        assert g.stats["emitted"] + g.stats["dropped_geometry"] == g.stats["constructed"] == 6

    def test_constructed_loops_are_persistent(self):
        """The point of the generator: every loop clears the P >= 0.5 gate."""
        ev = MeritEvaluator("blocking")
        for c in _gen(4).run(6):
            m = ev.evaluate(c)
            assert m.topo_robustness == 1.0
            assert m.persistence_ratio_min >= 0.5
            assert m.epistemic_truth >= 0.5

    def test_deterministic_for_a_seed(self):
        a = [c.invariant.betti for c in _gen(5).run(4)]
        b = [c.invariant.betti for c in _gen(5).run(4)]
        assert a == b

    def test_clearance_must_exceed_cutoff(self):
        with pytest.raises(ValueError, match="clearance"):
            PushoutGenerator(spacing=0.2, cutoff_factor=2.0, clearance=0.3)


class TestRSEMode:
    def test_pushout_mode(self):
        rse = RecursiveSynthesisEngine(n_seed_complexes=4, rng_seed=1, mode="pushout",
                                       pushout_config={"sphere_prob": 0.0})
        out = rse.run()
        assert out and all(c.construction["generator"] == "pushout" for c in out)
        assert all(c.invariant.betti[2] == 0 for c in out)

    def test_yaml_lists_are_accepted(self):
        rse = RecursiveSynthesisEngine(n_seed_complexes=2, rng_seed=2, mode="pushout",
                                       pushout_config={"n_primitives": [2, 2], "ambient_dim": [4, 4]})
        for c in rse.run():
            assert c.point_cloud.shape[1] == 4
            assert len(c.construction["steps"]) <= 2

    def test_mro_mode_unchanged_and_unlabelled(self):
        out = RecursiveSynthesisEngine(n_seed_complexes=2, max_iterations=20, rng_seed=3).run()
        assert all(c.construction is None for c in out)

    def test_unknown_mode_rejected(self):
        with pytest.raises(ValueError, match="mode"):
            RecursiveSynthesisEngine(mode="random")
