"""
Topological invariant computation using GUDHI persistent homology.

Best practices (GUDHI 3.12):
- Adaptive max_edge_length: set to a percentile of pairwise distances so the
  filtration captures meaningful local topology regardless of point cloud scale.
- For N ≤ 80 points: plain RipsComplex is optimal.
- Pass points as list[list[float]] — GUDHI's C++ backend is faster.
- complexity_score is normalised by mel to be scale-invariant. Without
  normalisation, MRO stretch accumulates exponentially over 500 iterations,
  making the score measure cloud scale rather than topological richness.

Falls back to a networkx stub if GUDHI is unavailable.
"""

from __future__ import annotations

import logging
import math
from typing import NamedTuple

import numpy as np

logger = logging.getLogger(__name__)

try:
    import gudhi  # type: ignore
    _GUDHI_AVAILABLE = True
    logger.debug("GUDHI %s available.", gudhi.__version__)
except ImportError:
    logger.warning("GUDHI not available — using stub invariant computation.")
    _GUDHI_AVAILABLE = False


class PersistencePair(NamedTuple):
    dimension: int
    birth: float
    death: float

    @property
    def lifetime(self) -> float:
        return (self.death - self.birth) if not math.isinf(self.death) else 1.0


class InvariantProfile(NamedTuple):
    betti: list[int]
    euler_characteristic: int
    dimension: int
    persistence_pairs: list[PersistencePair]
    persistence_entropy: float
    complexity_score: float


def _adaptive_max_edge_length(points: np.ndarray, percentile: float = 20.0) -> float:
    """
    Set filtration threshold adaptively from the pairwise distance distribution.

    percentile=20 connects the nearest 20% of point pairs — enough to reveal
    1-cycles and 2-voids without drowning in noise from distant connections.
    Scale-adaptive: works regardless of how stretched the cloud is after MRO.
    """
    n = len(points)
    if n < 2:
        return 1.0
    if n > 60:
        idx = np.random.choice(n, 60, replace=False)
        pts = points[idx]
    else:
        pts = points
    diffs = pts[:, None] - pts[None, :]
    dists = np.linalg.norm(diffs, axis=-1)
    upper = dists[np.triu_indices(len(pts), k=1)]
    return float(np.percentile(upper, percentile)) if len(upper) > 0 else 1.0


def compute_betti(
    points: np.ndarray,
    max_dimension: int = 2,
    max_edge_length: float | None = None,
) -> InvariantProfile:
    if _GUDHI_AVAILABLE:
        return _compute_betti_gudhi(points, max_dimension, max_edge_length)
    else:
        return _compute_betti_stub(points, max_dimension)


def _compute_betti_gudhi(
    points: np.ndarray,
    max_dimension: int,
    max_edge_length: float | None,
) -> InvariantProfile:
    mel = max_edge_length if max_edge_length is not None else _adaptive_max_edge_length(points)

    rips = gudhi.RipsComplex(points=points.tolist(), max_edge_length=mel)
    simplex_tree = rips.create_simplex_tree(max_dimension=max_dimension + 1)
    simplex_tree.compute_persistence()

    pairs: list[PersistencePair] = []
    for dim, (birth, death) in simplex_tree.persistence():
        pairs.append(PersistencePair(dim, birth, death))

    raw_betti = list(simplex_tree.betti_numbers())

    # GUDHI returns [] for a trivially simple complex (single isolated point).
    # A non-empty cloud always has β0 ≥ 1.
    if len(raw_betti) == 0 and len(points) > 0:
        raw_betti = [1]

    betti = list(raw_betti) + [0] * max(0, max_dimension + 1 - len(raw_betti))
    betti = betti[: max_dimension + 1]

    dimension = max_dimension
    euler = sum((-1) ** k * b for k, b in enumerate(betti))
    entropy = _persistence_entropy(pairs)
    # Pass mel so score is normalised and scale-invariant
    score = topological_complexity_score(betti, pairs, mel=mel)

    logger.debug(
        "GUDHI: N=%d d=%d mel=%.3e betti=%s score=%.3f",
        len(points), points.shape[1] if points.ndim > 1 else 1, mel, betti, score,
    )
    return InvariantProfile(betti, euler, dimension, pairs, entropy, score)


def _compute_betti_stub(points: np.ndarray, max_dimension: int) -> InvariantProfile:
    """Fallback stub — install GUDHI for real topology."""
    import networkx as nx

    n = len(points)
    if n == 0:
        betti = [0] * (max_dimension + 1)
        return InvariantProfile(betti, 0, 0, [], 0.0, 0.0)

    dists = np.linalg.norm(points[:, None] - points[None, :], axis=-1)
    eps = float(np.percentile(dists[dists > 0], 20))

    g = nx.Graph()
    g.add_nodes_from(range(n))
    rows, cols = np.where((dists < eps) & (dists > 0))
    g.add_edges_from(zip(rows.tolist(), cols.tolist()))

    b0 = nx.number_connected_components(g)
    b1 = max(0, g.number_of_edges() - g.number_of_nodes() + b0)
    betti = [b0, b1] + [0] * max(0, max_dimension - 1)
    betti = betti[: max_dimension + 1]

    euler = sum((-1) ** k * b for k, b in enumerate(betti))
    return InvariantProfile(betti, euler, max_dimension, [], 0.0,
                            topological_complexity_score(betti, [], mel=1.0))


def _persistence_entropy(pairs: list[PersistencePair]) -> float:
    """Shannon entropy of the normalised persistence lifetime distribution."""
    lifetimes = np.array([p.lifetime for p in pairs if not math.isinf(p.death)])
    if lifetimes.sum() == 0:
        return 0.0
    p = lifetimes / lifetimes.sum()
    return float(-np.sum(p * np.log(p + 1e-12)))


def topological_complexity_score(
    betti: list[int],
    pairs: list[PersistencePair],
    mel: float = 1.0,
) -> float:
    """
    Scale-invariant fitness metric combining Betti richness and persistence.

    persistence_score is normalised by mel so it stays in [0, 1] regardless
    of the cloud's absolute scale after MRO transformations. Without this,
    the score grows exponentially with iteration count (scale explosion bug).

    betti_score is dimensionless by construction.
    Total range: approximately [0, 10] for typical Betti profiles.
    """
    betti_score = sum((k + 1) * b for k, b in enumerate(betti))
    if pairs and mel > 0:
        finite_lifetimes = [p.lifetime for p in pairs if not math.isinf(p.death)]
        if finite_lifetimes:
            # Normalise by mel: lifetime / mel ∈ [0, 1]
            persistence_score = float(np.mean(finite_lifetimes) / mel)
        else:
            persistence_score = 0.0
    else:
        persistence_score = 0.0
    return betti_score + persistence_score
