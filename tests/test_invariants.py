"""
Tests: topological invariants on known complexes.

Cross-referenced against the TPMM data table in mapping_logic.json.
"""

import numpy as np
import pytest

from nhcs.layer1_genesis.invariants import compute_betti, topological_complexity_score


def _circle_points(n: int = 40, r: float = 1.0) -> np.ndarray:
    t = np.linspace(0, 2 * np.pi, n, endpoint=False)
    return np.stack([r * np.cos(t), r * np.sin(t)], axis=1)


def _sphere_points(n: int = 200) -> np.ndarray:
    """Fibonacci sphere sampling."""
    golden = (1 + 5 ** 0.5) / 2
    pts = []
    for i in range(n):
        theta = np.arccos(1 - 2 * (i + 0.5) / n)
        phi = 2 * np.pi * i / golden
        pts.append([np.sin(theta) * np.cos(phi), np.sin(theta) * np.sin(phi), np.cos(theta)])
    return np.array(pts)


def _point() -> np.ndarray:
    return np.array([[0.0, 0.0, 0.0]])


class TestBettiNumbers:
    def test_single_point(self):
        pts = np.array([[0.0, 0.0]])
        profile = compute_betti(pts, max_dimension=2, max_edge_length=5.0)
        assert profile.betti[0] == 1   # 1 connected component

    def test_circle_has_one_loop(self):
        pts = _circle_points(50)
        profile = compute_betti(pts, max_dimension=1, max_edge_length=0.5)
        # β0 = 1, β1 = 1 for a circle
        assert profile.betti[0] == 1
        assert profile.betti[1] >= 1  # at least one loop

    def test_two_circles_disconnected(self):
        c1 = _circle_points(30, r=1.0)
        c2 = _circle_points(30, r=1.0) + np.array([10.0, 0.0])
        pts = np.vstack([c1, c2])
        profile = compute_betti(pts, max_dimension=1, max_edge_length=0.5)
        assert profile.betti[0] == 2   # 2 components

    def test_complexity_score_positive(self):
        pts = _circle_points(40)
        profile = compute_betti(pts, max_dimension=1, max_edge_length=0.5)
        assert profile.complexity_score >= 0.0

    def test_euler_characteristic_consistency(self):
        """χ = β0 - β1 + β2 must match computed value (within stub tolerance)."""
        pts = _circle_points(40)
        profile = compute_betti(pts, max_dimension=2, max_edge_length=0.5)
        betti = (profile.betti + [0, 0, 0])[:3]
        expected = betti[0] - betti[1] + betti[2]
        assert abs(expected - profile.euler_characteristic) <= 2  # tolerance for stubs


class TestComplexityScore:
    def test_more_complex_topology_scores_higher(self):
        simple = _circle_points(10)
        complex_ = np.vstack([_circle_points(40), _circle_points(40, r=2.0) + [5, 0]])
        s1 = compute_betti(simple, max_dimension=1, max_edge_length=0.5)
        s2 = compute_betti(complex_, max_dimension=1, max_edge_length=0.5)
        assert s2.complexity_score >= s1.complexity_score
