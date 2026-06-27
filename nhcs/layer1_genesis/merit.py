"""
Merit heuristics for concept evaluation.

Implements: MDL/Kolmogorov proxy, topological consistency,
Schmidhuber compression progress, fractal dimension, edge-of-chaos ratio.
"""

from __future__ import annotations

import logging
import math
import zlib
from dataclasses import dataclass

import numpy as np

from nhcs.layer1_genesis.invariants import InvariantProfile
from nhcs.layer1_genesis.rse import CandidateConcept
from nhcs.schemas import MeritScores

logger = logging.getLogger(__name__)


class MeritEvaluator:
    """Scores a CandidateConcept on all merit axes."""

    def evaluate(self, concept: CandidateConcept, novelty_score: float = 0.0) -> MeritScores:
        profile = concept.invariant
        pc = concept.point_cloud

        mdl = self._mdl_score(pc)
        topo = self._topo_consistency(profile)
        delta_compress = self._schmidhuber_progress(pc)
        frac_dim = self._fractal_dimension(pc)
        eoc = self._edge_of_chaos(pc)

        # Epistemic truth: combination of topo consistency + MDL
        et = float(np.clip(0.6 * topo + 0.4 * mdl, 0.0, 1.0))
        # Algorithmic parsimony: MDL is the primary proxy
        ap = float(np.clip(mdl, 0.0, 1.0))

        return MeritScores(
            epistemic_truth=et,
            algorithmic_parsimony=ap,
            mdl_score=mdl,
            compression_progress=delta_compress,
            fractal_dimension=frac_dim,
            edge_of_chaos_ratio=eoc,
            novelty_score=novelty_score,
        )

    # ------------------------------------------------------------------
    # Individual heuristics
    # ------------------------------------------------------------------

    def _mdl_score(self, points: np.ndarray) -> float:
        """
        Kolmogorov approximation via zlib compression ratio.
        High compression of the raw bytes → low MDL → high parsimony.
        Score: 1.0 = maximally compressible, 0.0 = incompressible noise.
        """
        if points.size == 0:
            return 0.0
        raw = points.astype(np.float32).tobytes()
        compressed = zlib.compress(raw, level=9)
        ratio = len(compressed) / len(raw)
        # Invert: lower ratio → more parsimonious → higher score
        return float(np.clip(1.0 - ratio, 0.0, 1.0))

    def _topo_consistency(self, profile: InvariantProfile) -> float:
        """
        Euler characteristic consistency:
        χ = β0 - β1 + β2 should match the computed value.
        Full consistency → 1.0; mismatch → penalised.
        """
        betti = (profile.betti + [0, 0, 0])[:3]
        expected_euler = betti[0] - betti[1] + betti[2]
        error = abs(expected_euler - profile.euler_characteristic)
        return float(np.clip(1.0 / (1.0 + error), 0.0, 1.0))

    def _schmidhuber_progress(self, points: np.ndarray) -> float:
        """
        Compression progress: Δ between 25th and 75th percentile subsets.
        """
        if points.shape[0] < 4:
            return 0.0
        n = points.shape[0]
        half = n // 2
        raw_early = points[:half].astype(np.float32).tobytes()
        raw_late = points[half:].astype(np.float32).tobytes()
        r_e = len(zlib.compress(raw_early, 9)) / (len(raw_early) + 1)
        r_l = len(zlib.compress(raw_late, 9)) / (len(raw_late) + 1)
        return float(np.clip(r_e - r_l, 0.0, 1.0))  # positive → improvement

    def _fractal_dimension(self, points: np.ndarray) -> float:
        """
        Box-counting fractal dimension estimate (normalised to [0,1]).
        """
        if points.shape[0] < 8:
            return 0.0
        pts = points - points.min(axis=0)
        scale = pts.max()
        if scale == 0:
            return 0.0
        pts /= scale

        counts = []
        box_sizes = [0.5, 0.25, 0.125, 0.0625]
        for eps in box_sizes:
            indices = (pts / eps).astype(int)
            n_boxes = len(set(map(tuple, indices.tolist())))
            counts.append(n_boxes)

        if len(counts) < 2 or counts[0] == 0:
            return 0.0
        log_n = np.log(counts)
        log_r = np.log([1.0 / eps for eps in box_sizes])
        slope = float(np.polyfit(log_r, log_n, 1)[0])
        # Normalise: typical fractal dims are 1–3 for 2-3D point clouds
        return float(np.clip(slope / 3.0, 0.0, 1.0))

    def _edge_of_chaos(self, points: np.ndarray) -> float:
        """
        Edge-of-chaos proxy: variance of singular values of the point cloud.
        Deep chaos → all singular values equal. Deep order → one dominant.
        Edge-of-chaos → intermediate.
        """
        if points.shape[0] < 2:
            return 0.0
        try:
            sv = np.linalg.svd(points - points.mean(axis=0), compute_uv=False)
            sv_norm = sv / (sv.sum() + 1e-8)
            entropy = -float(np.sum(sv_norm * np.log(sv_norm + 1e-12)))
            max_entropy = math.log(len(sv))
            return float(np.clip(entropy / (max_entropy + 1e-8), 0.0, 1.0))
        except np.linalg.LinAlgError:
            return 0.0
