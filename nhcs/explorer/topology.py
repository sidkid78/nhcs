"""Betti numbers of a point sample at a fixed Rips scale (shared by objects and probes)."""

from __future__ import annotations

import numpy as np

import gudhi  # type: ignore


def voxel_downsample(points: np.ndarray, cell: float) -> np.ndarray:
    """Keep one point per cubic cell of side ``cell`` (the first one seen)."""
    if len(points) == 0 or cell <= 0:
        return points
    keys = np.floor(points / cell).astype(np.int64)
    _, idx = np.unique(keys, axis=0, return_index=True)
    return points[np.sort(idx)]


def betti_at_scale(points: np.ndarray, scale: float, max_dim: int = 2) -> list[int]:
    """
    Betti numbers b_0..b_max_dim of the Rips complex at ``scale``, over Z/11
    (GUDHI's default field, so these are the rational Betti numbers: torsion
    such as RP^2's is invisible).

    The 1-skeleton is edge-collapsed before expansion; that preserves homology
    and keeps dense samples tractable.
    """
    if len(points) == 0:
        return [0] * (max_dim + 1)
    if len(points) == 1:
        return [1] + [0] * max_dim
    st = gudhi.RipsComplex(points=np.asarray(points).tolist(), max_edge_length=scale).create_simplex_tree(max_dimension=1)
    flat = gudhi.SimplexTree()
    for s, _ in st.get_simplices():
        flat.insert(s, 0.0)
    flat.collapse_edges(100)
    flat.expansion(max_dim + 1)
    flat.compute_persistence(persistence_dim_max=True)
    b = list(flat.betti_numbers())
    return (b + [0] * (max_dim + 1))[: max_dim + 1]
