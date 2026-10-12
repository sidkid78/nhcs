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

    Score = complexity_norm + λ * min_distance_to_already_selected_norm
    where distance is L2 in Betti-vector space, and BOTH terms are min-max
    normalised to [0, 1] within the pool so λ has a meaningful, scale-free
    interpretation (λ=1 => diversity and complexity weigh equally). Without
    normalisation, raw complexity scores (~2-4) dwarf raw Betti distances
    (~1-3), so the diversity term never affects selection and the search
    collapses to pure complexity ranking.

    Candidates are DEDUPLICATED by Betti signature first (keeping the
    highest-complexity representative of each). The RSE routinely produces
    many seeds that converge to the same topology; without dedup the top-k
    can be k identical concepts (diversity distance 0 between duplicates
    does not prevent their selection, it only removes the bonus), which is
    the opposite of the intended behaviour.

    Parameters
    ----------
    beam_width : int
    diversity_weight : float  (λ); default 1.0 (equal weight after norm)
    """

    def __init__(self, beam_width: int = 5, diversity_weight: float = 1.0) -> None:
        self.beam_width = beam_width
        self.diversity_weight = diversity_weight

    def _betti_vec(self, c: CandidateConcept) -> np.ndarray:
        b = (c.invariant.betti + [0, 0, 0])[:3]
        return np.array(b, dtype=float)

    def _betti_sig(self, c: CandidateConcept) -> tuple[int, int, int]:
        b = (c.invariant.betti + [0, 0, 0])[:3]
        return (int(b[0]), int(b[1]), int(b[2]))

    def _dedupe(self, pool: list[CandidateConcept]) -> list[CandidateConcept]:
        """One representative per Betti signature: the highest-complexity one."""
        best: dict[tuple[int, int, int], CandidateConcept] = {}
        for c in pool:
            sig = self._betti_sig(c)
            cur = best.get(sig)
            if cur is None or c.invariant.complexity_score > cur.invariant.complexity_score:
                best[sig] = c
        return list(best.values())

    def _min_dist_to_selected(
        self,
        candidate: CandidateConcept,
        selected: list[CandidateConcept],
    ) -> float:
        if not selected:
            return 1.0
        bv = self._betti_vec(candidate)
        return float(min(np.linalg.norm(bv - self._betti_vec(s)) for s in selected))

    def select(self, pool: list[CandidateConcept]) -> list[CandidateConcept]:
        """Greedy diverse-and-complex selection over the deduplicated pool."""
        if not pool:
            return []

        pool = self._dedupe(pool)
        n_unique = len(pool)
        if n_unique == 1:
            logger.info(
                "DivergentBeamSearch: pool collapsed to 1 unique signature "
                "(RSE produced no topological diversity this round)."
            )
            return pool

        # Min-max normalise complexity across the (deduped) pool.
        cx = np.array([c.invariant.complexity_score for c in pool], dtype=float)
        cx_range = float(np.ptp(cx))
        cx_norm = (cx - cx.min()) / (cx_range + 1e-9)

        # Normalise diversity by the max pairwise Betti distance in the pool,
        # so both terms live on [0, 1].
        bvs = [self._betti_vec(c) for c in pool]
        d_max = max(
            (float(np.linalg.norm(a - b)) for a in bvs for b in bvs),
            default=1.0,
        ) or 1.0

        cx_by_id = {id(c): cx_norm[i] for i, c in enumerate(pool)}

        selected: list[CandidateConcept] = []
        remaining = list(pool)
        while remaining and len(selected) < self.beam_width:
            def _score(c: CandidateConcept) -> float:
                base = float(cx_by_id[id(c)])
                if not selected:
                    return base
                div = self._min_dist_to_selected(c, selected) / d_max
                return base + self.diversity_weight * div

            best = max(remaining, key=_score)
            selected.append(best)
            remaining.remove(best)

        logger.info(
            "DivergentBeamSearch selected %d/%d (%d unique signatures).",
            len(selected), len(pool), n_unique,
        )
        return selected
