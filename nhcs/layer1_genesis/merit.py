"""
Merit heuristics for concept evaluation.

Implements: MDL proxy (homology-preserving edge collapse), topological
robustness, Schmidhuber compression progress, fractal dimension, edge-of-chaos
ratio, plus persistence telemetry.

merit_version "v2" (2026-10-12). Ledgers and CSVs from v1 are not comparable
on epistemic_truth / algorithmic_parsimony / mdl_score:
  - v1 MDL was zlib over raw float32 coordinates. Random floats do not
    compress, so it was 0.0 for every RSE concept (16-bit quantisation and
    compressing the adjacency matrix were also tried: both stay ~0, because
    zlib's fixed overhead exceeds any saving on <= 40 points).
  - v1 topological consistency compared chi with b0 - b1 + b2, but
    invariants.py computes chi from that same sum, so it was always 1.0.
  Net effect in v1: Et = 0.6 and Ap = 0.0 for every concept, and ICVP approved
  everything.

Persistence gate
----------------
``persistence_gate="log_only"`` (default) records topological robustness but
leaves it out of Et, so ICVP gating is unchanged apart from the MDL term.
``"blocking"`` puts robustness into Et. With current RSE output most concepts
fail in blocking mode -- most of their loops die soon after the Rips cutoff
(median persistence ratio ~0.15) -- so only switch once RSE produces
persistent features.
"""

from __future__ import annotations

import logging
import math
import statistics
import zlib

import numpy as np

from nhcs.layer1_genesis.invariants import _adaptive_max_edge_length
from nhcs.layer1_genesis.rse import CandidateConcept
from nhcs.schemas import MeritScores

logger = logging.getLogger(__name__)

try:
    import gudhi  # type: ignore
    _GUDHI_AVAILABLE = True
except ImportError:  # pragma: no cover
    _GUDHI_AVAILABLE = False

MERIT_VERSION = "v2"
PERSISTENCE_GATES = ("log_only", "blocking")


class MeritEvaluator:
    """Scores a CandidateConcept on all merit axes.

    Parameters
    ----------
    persistence_gate : "log_only" | "blocking"
        Whether topological robustness feeds into epistemic truth (and hence
        ICVP approval). See module docstring.
    min_persistence_ratio : float
        A b1/b2 feature counts as robust if (death - birth) / cutoff is at
        least this. Default 0.5.
    extend_factor : float
        For the persistence ratio, the filtration is recomputed out to
        ``extend_factor`` x cutoff so features alive at the cutoff get an
        observed death. Features still alive there are censored at that value.
        If the edge-collapsed complex at that scale exceeds ``max_collapsed_edges``
        the factor steps down to 1.5, which is always enough to decide
        P >= 0.5. The factor used is recorded as ``persistence_extend_factor``.
        Default 2.0: on constructed concepts 3.0 cost ~720 ms vs ~4 ms per
        evaluate with identical robustness verdicts; it only censors very
        long-lived loops lower (P <= 2).
    max_collapsed_edges : int
        Size budget for the extended filtration (see above).
    """

    def __init__(
        self,
        persistence_gate: str = "log_only",
        min_persistence_ratio: float = 0.5,
        extend_factor: float = 2.0,
        max_collapsed_edges: int = 2500,
    ) -> None:
        if persistence_gate not in PERSISTENCE_GATES:
            raise ValueError(f"persistence_gate must be one of {PERSISTENCE_GATES}")
        self.persistence_gate = persistence_gate
        self.min_persistence_ratio = min_persistence_ratio
        self.extend_factor = extend_factor
        self.max_collapsed_edges = max_collapsed_edges

    def evaluate(self, concept: CandidateConcept, novelty_score: float = 0.0) -> MeritScores:
        profile = concept.invariant
        pc = concept.point_cloud
        mel = profile.max_edge_length or _adaptive_max_edge_length(pc)

        mdl = self._mdl_score(pc, mel)
        ratios, ext_used = self._persistence_ratios(pc, mel, len(profile.betti) - 1)
        robustness = self._topo_consistency(ratios)
        delta_compress = self._schmidhuber_progress(pc)
        frac_dim = self._fractal_dimension(pc)
        eoc = self._edge_of_chaos(pc)

        # Epistemic truth: topological robustness + MDL. In log_only mode the
        # topology term is held at 1.0 (the v1 value) so gating is unchanged.
        topo_term = robustness if self.persistence_gate == "blocking" else 1.0
        et = float(np.clip(0.6 * topo_term + 0.4 * mdl, 0.0, 1.0))
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
            topo_robustness=robustness,
            persistence_ratio_median=statistics.median(ratios) if ratios else None,
            persistence_ratio_min=min(ratios) if ratios else None,
            n_reported_features=len(ratios),
            persistence_extend_factor=ext_used,
            persistence_gate=self.persistence_gate,
            merit_version=MERIT_VERSION,
        )

    # ------------------------------------------------------------------
    # Individual heuristics
    # ------------------------------------------------------------------

    def _mdl_score(self, points: np.ndarray, mel: float) -> float:
        """
        Parsimony as homology-preserving compressibility, in [0, 1].

        Take the concept's Rips complex at its cutoff, collapse edges (GUDHI's
        Boulanger-Glisse edge collapse, which provably preserves homology),
        re-expand, and report the fraction of simplices removed:
            1 - |collapsed| / |original|.
        High = much of the complex is redundant for its topology (short
        description); low = nearly every simplex is load-bearing.

        Known bias: larger clouds have more redundant simplices, so the score
        rises with point count (r ~ 0.8 on RSE output, N in 20-40).
        """
        if not _GUDHI_AVAILABLE or len(points) < 2 or mel <= 0:
            return 0.0
        rips = gudhi.RipsComplex(points=np.asarray(points).tolist(), max_edge_length=mel)
        graph = gudhi.SimplexTree()
        # Flatten the filtration so collapses are judged at the cutoff scale
        # only; collapsing the filtered graph must preserve every scale and
        # removes almost nothing.
        # Keep a reference: iterating get_simplices() on a temporary simplex
        # tree is a use-after-free in GUDHI (segfault).
        skeleton = rips.create_simplex_tree(max_dimension=1)
        for simplex, _ in skeleton.get_simplices():
            graph.insert(simplex, 0.0)
        full = gudhi.SimplexTree(graph)
        full.expansion(3)
        before = full.num_simplices()
        graph.collapse_edges(100)
        graph.expansion(3)
        after = graph.num_simplices()
        return float(np.clip(1.0 - after / before, 0.0, 1.0)) if before else 0.0

    def _topo_consistency(self, ratios: list[float]) -> float:
        """
        Topological robustness in [0, 1]: the share of the reported b1/b2
        features whose persistence ratio is at least ``min_persistence_ratio``.

        Judged on persistence, not on where a feature is born relative to the
        cutoff: a clean circle's loop can be born at 90% of the cutoff and
        still live 2x the cutoff past it.

        No higher features -> 1.0 (nothing to be fragile).
        """
        if not ratios:
            return 1.0
        return float(sum(r >= self.min_persistence_ratio for r in ratios) / len(ratios))

    def _persistence_ratios(
        self, points: np.ndarray, mel: float, max_dim: int,
    ) -> tuple[list[float], float | None]:
        """
        Persistence ratio P = (death - birth) / cutoff for every b1/b2 feature
        alive at the cutoff, with death read from a filtration extended past
        the cutoff (censored at the extension). Returns (ratios, factor used).

        At the cutoff itself every such feature has death = inf (it hasn't
        died yet), so P cannot be computed from the concept's own diagram.

        The 1-skeleton is edge-collapsed before expansion, which preserves the
        persistence diagram exactly (flag filtration). Without that, and
        without the step-down budget, a 3x extension of a ~240-point
        constructed concept expanded to ~36M simplices and ran out of memory.
        """
        if not _GUDHI_AVAILABLE or len(points) < 2 or mel <= 0 or max_dim < 1:
            return [], None
        pts = np.asarray(points).tolist()
        factors = sorted({self.extend_factor, 1.5} if self.extend_factor >= 1.5
                         else {self.extend_factor}, reverse=True)
        for i, factor in enumerate(factors):
            ext = factor * mel
            st = gudhi.RipsComplex(points=pts, max_edge_length=ext).create_simplex_tree(max_dimension=1)
            st.collapse_edges(100)
            n_edges = st.num_simplices() - st.num_vertices()
            if n_edges > self.max_collapsed_edges and i < len(factors) - 1:
                continue
            st.expansion(max_dim + 1)
            out = [(min(death, ext) - birth) / mel
                   for dim, (birth, death) in st.persistence(persistence_dim_max=True)
                   if 1 <= dim <= max_dim and birth <= mel < death]
            return out, factor
        return [], None  # pragma: no cover

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
