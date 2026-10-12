"""
Tests: simplicial pushout (concept gluing) and the Mayer-Vietoris prediction.
"""

import numpy as np
import pytest

from nhcs.layer1_genesis.invariants import betti_at_scale, compute_betti
from nhcs.layer1_genesis.pushout import (
    PushoutError,
    SimplicialComplex,
    complex_from_points,
    glue,
)


def cycle(n: int, prefix: str = "v") -> SimplicialComplex:
    """Boundary of an n-gon: a simplicial circle (needs n >= 3)."""
    vs = [f"{prefix}{i}" for i in range(n)]
    return SimplicialComplex.from_simplices([(vs[i], vs[(i + 1) % n]) for i in range(n)])


class TestSimplicialComplex:
    def test_circle_betti(self):
        assert cycle(5).betti() == [1, 1, 0]

    def test_euler_from_simplex_counts(self):
        assert cycle(6).euler_characteristic() == 0

    def test_filled_triangle_is_contractible(self):
        k = SimplicialComplex.from_simplices([("a", "b", "c")])
        assert k.betti() == [1, 0, 0]
        assert len(k.simplices) == 7  # 3 vertices, 3 edges, 1 face

    def test_hollow_tetrahedron_is_a_sphere(self):
        faces = [("a", "b", "c"), ("a", "b", "d"), ("a", "c", "d"), ("b", "c", "d")]
        assert SimplicialComplex.from_simplices(faces).betti() == [1, 0, 1]


class TestPushout:
    def test_two_circles_glued_at_two_points(self):
        """The worked example: β(K_A) = β(K_B) = (1,1,0), K_I = {E1, E2} -> (1,3,0)."""
        k_a, k_b = cycle(4, "a"), cycle(4, "b")   # E1, E2 opposite, so not adjacent
        res = glue(k_a, k_b, [("a0", "b0"), ("a2", "b2")], strict=True)
        assert res.betti == [1, 3, 0]
        assert res.kernel_phi0 == 1
        assert res.predicted_betti == [1, 3]
        assert res.is_homotopy_pushout

    def test_euler_characteristic_matches(self):
        res = glue(cycle(4, "a"), cycle(4, "b"), [("a0", "b0"), ("a2", "b2")])
        # V = 4 + 4 - 2 = 6, E = 8 -> χ = -2 = β0 - β1
        assert res.complex.euler_characteristic() == -2

    def test_shared_edge_collapses_and_drops_a_cycle(self):
        """If E1E2 is an edge in both circles, SimpComp merges the edges: β1 = 2, not 3."""
        k_a, k_b = cycle(3, "a"), cycle(3, "b")  # every vertex pair is adjacent in a triangle
        res = glue(k_a, k_b, [("a0", "b0"), ("a1", "b1")])
        assert res.betti == [1, 2, 0]
        assert not res.is_homotopy_pushout
        assert res.predicted_betti is None
        assert frozenset({("I", 0), ("I", 1)}) in res.collapsed

    def test_shared_edge_raises_when_strict(self):
        with pytest.raises(PushoutError, match="Mayer-Vietoris"):
            glue(cycle(3, "a"), cycle(3, "b"), [("a0", "b0"), ("a1", "b1")], strict=True)

    def test_declaring_the_shared_edge_in_k_i_restores_mayer_vietoris(self):
        """Gluing along an arc (K_I contractible) instead: β1 = 1 + 1 + 0 = 2."""
        res = glue(cycle(3, "a"), cycle(3, "b"), [("a0", "b0"), ("a1", "b1")],
                   shared_simplices=[(0, 1)], strict=True)
        assert res.betti == [1, 2, 0]
        assert res.kernel_phi0 == 0
        assert res.predicted_betti == [1, 2]

    def test_single_point_wedge(self):
        """Wedge of two circles: K_I = one point, ker φ0 = 0, β = (1, 2, 0)."""
        res = glue(cycle(4, "a"), cycle(4, "b"), [("a0", "b0")], strict=True)
        assert res.betti == [1, 2, 0]
        assert res.predicted_betti == [1, 2]

    def test_three_points_gives_four_cycles(self):
        res = glue(cycle(6, "a"), cycle(6, "b"), [("a0", "b0"), ("a2", "b2"), ("a4", "b4")],
                   strict=True)
        assert res.kernel_phi0 == 2
        assert res.betti == [1, 4, 0]

    def test_disjoint_components_on_one_side(self):
        """K_B = two separate circles, one shared point in each: everything connects."""
        k_b = SimplicialComplex(cycle(4, "b").simplices | cycle(4, "c").simplices)
        assert k_b.betti() == [2, 2, 0]
        res = glue(cycle(4, "a"), k_b, [("a0", "b0"), ("a2", "c0")], strict=True)
        assert res.kernel_phi0 == 0
        assert res.betti == [1, 3, 0]
        assert res.predicted_betti == [1, 3]

    def test_structure_maps_send_shared_vertices_to_the_same_place(self):
        res = glue(cycle(4, "a"), cycle(4, "b"), [("a0", "b0"), ("a2", "b2")])
        assert res.j_a["a0"] == res.j_b["b0"]
        assert res.j_a["a1"] != res.j_b["b1"]

    def test_rejects_non_injective_map(self):
        with pytest.raises(PushoutError, match="injective"):
            glue(cycle(4, "a"), cycle(4, "b"), [("a0", "b0"), ("a0", "b2")])

    def test_rejects_unknown_vertex(self):
        with pytest.raises(PushoutError, match="not present"):
            glue(cycle(4, "a"), cycle(4, "b"), [("a9", "b0")])

    def test_rejects_k_i_simplex_missing_from_one_side(self):
        with pytest.raises(PushoutError, match="not a simplex of K_A"):
            glue(cycle(4, "a"), cycle(4, "b"), [("a0", "b0"), ("a2", "b1")],
                 shared_simplices=[(0, 1)])


class TestPointCloudBridge:
    def _circle(self, n=24):
        t = np.linspace(0, 2 * np.pi, n, endpoint=False)
        return np.stack([np.cos(t), np.sin(t)], axis=1)

    def test_rips_complex_reproduces_compute_betti(self):
        pts = self._circle()
        profile = compute_betti(pts, max_dimension=2, max_edge_length=0.5)
        k = complex_from_points(pts, profile.max_edge_length)
        assert k.betti() == profile.betti == [1, 1, 0]

    def test_glue_two_point_cloud_concepts(self):
        a, b = self._circle(), self._circle() * 2.0
        k_a = complex_from_points(a, 0.5)
        k_b = complex_from_points(b, 1.0)
        res = glue(k_a, k_b, [(0, 0), (12, 12)], strict=True)  # antipodal points
        assert res.betti == [1, 3, 0]

    def test_profile_records_cutoff_and_betti_at_scale_matches(self):
        profile = compute_betti(self._circle(), max_dimension=2, max_edge_length=0.5)
        assert profile.max_edge_length == 0.5
        assert betti_at_scale(profile.persistence_pairs, 0.5, 2) == profile.betti
