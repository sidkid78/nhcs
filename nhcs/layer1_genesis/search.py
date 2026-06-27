"""
Divergent Beam Search.

Standard beam search modified with a structural-distance penalty term
to promote diverse topological outputs from the RSE.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

import numpy as np

from nhcs.layer1_genesis.rse import CandidateConcept

logger = logging.getLogger(__name__)


class DivergentBeamSearch:
    """
    Greedily selects the top-k most novel AND diverse candidates from a pool.

    Score = complexity_score + λ * min_distance_to_already_selected
    where distance is L2 in Betti-vector space.

    Parameters
    ----------
    beam_width : int
    diversity_weight : float  (λ)
    """

    def __init__(self, beam_width: int = 5, diversity_weight: float = 0.3) -> None:
        self.beam_width = beam_width
        self.diversity_weight = diversity_weight

    def _betti_vec(self, c: CandidateConcept) -> np.ndarray:
        b = (c.invariant.betti + [0, 0, 0])[:3]
        logger.info(b)
        return np.array(b, dtype=float)

    def _min_dist_to_selected(
        self,
        candidate: CandidateConcept,
        selected: list[CandidateConcept],
    ) -> float:
        if not selected:
            return 1.0
        bv = self._betti_vec(candidate)
        logger.info(bv)
        return float(min(np.linalg.norm(bv - self._betti_vec(s)) for s in selected))

    def select(self, pool: list[CandidateConcept]) -> list[CandidateConcept]:
        """Greedy diverse-and-complex selection."""
        if not pool:
            return []
        selected: list[CandidateConcept] = []
        remaining = list(pool)

        while remaining and len(selected) < self.beam_width:
            scored = [
                (c.invariant.complexity_score + self.diversity_weight *
                 self._min_dist_to_selected(c, selected), c)
                for c in remaining
            ]
            scored.sort(key=lambda x: -x[0])
            best = scored[0][1]
            selected.append(best)
            remaining.remove(best)

        logger.info("DivergentBeamSearch selected %d/%d.", len(selected), len(pool))
        return selected
