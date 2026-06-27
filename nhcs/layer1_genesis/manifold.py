"""
Dynamic Embedding Manifold.

Embeds invariant signatures into a hyperbolic (Poincaré ball) manifold
for isomorphic distance computation between concepts.

Uses geoopt if available; falls back to euclidean stub.
"""

from __future__ import annotations

import logging

import numpy as np

logger = logging.getLogger(__name__)

try:
    import torch
    import geoopt  # type: ignore
    _GEOOPT_AVAILABLE = True
except ImportError:
    logger.warning("geoopt/torch not available — using Euclidean stub manifold.")
    _GEOOPT_AVAILABLE = False


class DynamicEmbeddingManifold:
    """
    Maps an InvariantProfile (Betti + persistence features) into a fixed-dim
    coordinate on a Poincaré ball manifold.

    The embedding dimension is `dim` (default 8).
    Distances in this space define the 'Relational Web' used by the RSE
    to identify novel vs. redundant concepts.
    """

    def __init__(self, dim: int = 8, curvature: float = 1.0) -> None:
        self.dim = dim
        self.curvature = curvature

        if _GEOOPT_AVAILABLE:
            self._ball = geoopt.PoincareBall(c=curvature)
            # Simple learnable linear projection from feature → manifold
            # Feature dim: max 3 Betti + euler + dim + entropy + complexity = 7
            self._proj = torch.nn.Linear(7, dim, bias=True)
            torch.nn.init.xavier_uniform_(self._proj.weight)
        self._embeddings: dict[str, np.ndarray] = {}

    def _feature_vector(self, betti: list[int], euler: int, dimension: int,
                        entropy: float, complexity: float) -> np.ndarray:
        b = (betti + [0, 0, 0])[:3]
        return np.array([*b, float(euler), float(dimension), entropy, complexity],
                        dtype=np.float32)

    def embed(
        self,
        concept_id: str,
        betti: list[int],
        euler: int,
        dimension: int,
        persistence_entropy: float,
        complexity_score: float,
    ) -> np.ndarray:
        """
        Map invariant signature → Poincaré ball coordinate.

        Returns
        -------
        coords : (dim,) float32 array  (cached by concept_id)
        """
        feat = self._feature_vector(betti, euler, dimension,
                                    persistence_entropy, complexity_score)

        if _GEOOPT_AVAILABLE:
            with torch.no_grad():
                t = torch.tensor(feat).unsqueeze(0)  # (1, 7)
                projected = self._proj(t).squeeze(0)  # (dim,)
                # Map onto Poincaré ball via expmap at origin
                origin = torch.zeros(self.dim)
                pt = self._ball.expmap0(projected)
                coords = pt.numpy().astype(np.float32)
        else:
            # Euclidean stub: pad / truncate feature to dim
            coords = np.zeros(self.dim, dtype=np.float32)
            n = min(len(feat), self.dim)
            coords[:n] = feat[:n]

        self._embeddings[concept_id] = coords
        return coords

    def distance(self, id_a: str, id_b: str) -> float:
        """Geodesic distance between two embedded concepts."""
        a = self._embeddings.get(id_a)
        b = self._embeddings.get(id_b)
        if a is None or b is None:
            raise KeyError("One or both concept IDs not embedded yet.")

        if _GEOOPT_AVAILABLE:
            ta = torch.tensor(a)
            tb = torch.tensor(b)
            return float(self._ball.dist(ta, tb).item())
        else:
            return float(np.linalg.norm(a - b))

    def nearest_neighbour(
        self, concept_id: str, n: int = 5
    ) -> list[tuple[str, float]]:
        """Return the n closest embedded concepts (excluding self)."""
        if concept_id not in self._embeddings:
            return []
        results = []
        for cid, coords in self._embeddings.items():
            if cid == concept_id:
                continue
            if _GEOOPT_AVAILABLE:
                d = self.distance(concept_id, cid)
            else:
                d = float(np.linalg.norm(self._embeddings[concept_id] - coords))
            results.append((cid, d))
        results.sort(key=lambda x: x[1])
        return results[:n]
