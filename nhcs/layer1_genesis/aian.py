"""
Anti-Imitation Adversarial Network (AIAN).

Four detection heads scoring candidate concepts for non-human-likeness:
  1. Semantic    — Betti distance from known human shapes
  2. Heuristic   — geometric regularity (symmetry, PCA hierarchy)
  3. Aesthetic   — coefficient of variation of pairwise distances
  4. Embedding   — sentence-transformer distance from human-corpus probes

Head 3 change (run_002): switched from zlib compression ratio to CV of pairwise
distances. Raw float32 Gaussian coordinates are incompressible by construction
(ratio ≥ 1.0 always), making the head a constant that contributes no signal.
CV of pairwise distances measures actual geometric irregularity:
  - Low CV: near-uniform distances (sphere-like, human aesthetic) → low novelty
  - High CV: wildly varying distances (alien geometry) → high novelty
"""

from __future__ import annotations

import logging
from typing import Protocol, Sequence, runtime_checkable

import numpy as np
from scipy.spatial.distance import pdist

logger = logging.getLogger(__name__)


@runtime_checkable
class _Invariant(Protocol):
    """Structural contract for the topological invariant a candidate carries."""
    betti: list[int]
    euler_characteristic: int
    complexity_score: float


@runtime_checkable
class CandidateLike(Protocol):
    """Structural contract for objects accepted by ``AIAN.filter``."""
    invariant: _Invariant
    point_cloud: np.ndarray

try:
    from sentence_transformers import SentenceTransformer  # type: ignore
    _ST_AVAILABLE = True
except ImportError:
    logger.warning("sentence-transformers not available — AIAN using geometric stub.")
    _ST_AVAILABLE = False


_HUMAN_CORPUS_PROBES: list[str] = [
    "cause and effect",
    "beginning middle end",
    "symmetry and beauty",
    "hierarchy and order",
    "near and far",
    "before and after",
    "self and other",
    "good and evil",
    "pattern and noise",
    "up and down",
    "more is better",
    "simple is elegant",
    "narrative arc",
    "categorical boundary",
    "spatial proximity",
    "temporal sequence",
    "subject predicate object",
    "agent action goal",
]


class AIAN:
    """
    Anti-Imitation Adversarial Network.

    Parameters
    ----------
    novelty_threshold : float
        Minimum novelty score to pass (0–1). Below = rejected as too human-like.
    encoder_model : str
        SentenceTransformer model for the frozen reference encoder.
    head_weights : Sequence[float], optional
        Aggregation weights for the four heads
        (semantic, heuristic, aesthetic, embedding). Defaults to
        ``(0.15, 0.25, 0.20, 0.40)``. Need not be normalised — they are
        rescaled to sum to 1.0 so w1..w4 can be tuned independently.
    gate : "blocking" | "log_only"
        blocking (default): ``filter`` drops candidates below the threshold.
        log_only: every candidate passes; novelty is still scored and attached
        as ``_novelty_score`` so it stays in the ledger/CSV. Use while the heads
        are uncalibrated for pushout-mode concepts (they reward high-b0 blobs
        and irregular point clouds, so persistent constructed topology scores
        ~0.52 vs the 0.6 threshold).
    """

    GATES = ("blocking", "log_only")

    DEFAULT_HEAD_WEIGHTS: tuple[float, float, float, float] = (0.15, 0.25, 0.20, 0.40)

    def __init__(
        self,
        novelty_threshold: float = 0.6,
        encoder_model: str = "all-MiniLM-L6-v2",
        head_weights: Sequence[float] | None = None,
        gate: str = "blocking",
    ) -> None:
        if gate not in self.GATES:
            raise ValueError(f"gate must be one of {self.GATES}, got {gate!r}")
        self.gate = gate
        self.novelty_threshold = novelty_threshold

        w = np.asarray(head_weights if head_weights is not None
                       else self.DEFAULT_HEAD_WEIGHTS, dtype=float)
        if w.shape != (4,):
            raise ValueError(f"head_weights must have 4 elements, got {w.shape}")
        total = w.sum()
        self.head_weights = w / total if total > 0 else w

        # Cache embedding-head results keyed by (betti0, betti1, betti2, euler);
        # the description string and similarity are fully determined by these.
        self._embedding_cache: dict[tuple[int, int, int, int], float] = {}
        self._encoder: SentenceTransformer | None = None

        if _ST_AVAILABLE:
            try:
                self._encoder = SentenceTransformer(encoder_model)
                self._human_embeddings = self._encoder.encode(
                    _HUMAN_CORPUS_PROBES, normalize_embeddings=True
                )
                logger.info("AIAN loaded encoder '%s'.", encoder_model)
            except Exception as exc:
                logger.warning("AIAN could not load encoder: %s. Using stub.", exc)
                self._encoder = None

    # ── Detection heads ───────────────────────────────────────────────

    def _semantic_head(self, betti: list[int], complexity: float) -> float:
        """Head 1: distance of Betti profile from known human-meaningful shapes.

        NOTE (bias caveat): raw L2 distance rewards large beta_0 monotonically,
        so high-component blobs ([8,1,0], [9,1,0]) saturate at 1.0 regardless
        of cycle/void structure. This biases the pipeline toward high-b0 /
        low-b1 concepts. A per-dimension saturating variant was trialled to
        debias it, but calibration showed this head's saturated ~1.0 output is
        load-bearing: the other three heads average only ~0.56, below the 0.6
        threshold, so deflating this head to realistic mid-range values makes
        AIAN keep nothing. Debiasing therefore requires re-calibrating the
        threshold (and/or head weights) in the same change -- not this head in
        isolation. Left as original pending that combined, separately-tested
        fix. See DivergentBeamSearch dedup for the diversity issue this was
        conflated with.
        """
        b = (betti + [0, 0, 0])[:3]
        human_shapes = [
            [1, 0, 0], [1, 1, 0], [1, 0, 1], [1, 2, 1], [1, 0, 0],
        ]
        min_dist = min(
            np.linalg.norm(np.array(b, float) - np.array(h, float))
            for h in human_shapes
        )
        return float(np.clip(min_dist / 5.0, 0.0, 1.0))

    def _heuristic_head(self, point_cloud: np.ndarray) -> float:
        """Head 2: geometric regularity via centroid-distance CV and PCA dominance."""
        if point_cloud.shape[0] < 3:
            return 0.5

        centroid = point_cloud.mean(axis=0)
        dists = np.linalg.norm(point_cloud - centroid, axis=1)
        cv = dists.std() / (dists.mean() + 1e-8)

        cov = np.cov(point_cloud.T)
        if cov.ndim == 0:
            eigenvalues = np.array([float(cov)])
        else:
            eigenvalues = np.linalg.eigvalsh(cov)
        eigenvalues = np.abs(eigenvalues)
        total = eigenvalues.sum()
        dominant = eigenvalues.max() / (total + 1e-8)

        novelty = 0.5 * cv + 0.5 * (1.0 - dominant)
        return float(np.clip(novelty, 0.0, 1.0))

    def _aesthetic_head(self, point_cloud: np.ndarray) -> float:
        """
        Head 3 — Aesthetic Symmetry via pairwise distance CV.

        Human aesthetics correlate with regularity — distances between points
        cluster tightly (sphere, torus, grid). Alien structures have highly
        irregular inter-point distances.

        Metric: coefficient of variation of all pairwise distances.
          Low CV  → uniform distances → symmetric/structured → low novelty
          High CV → irregular distances → alien geometry → high novelty

        CV is scale-invariant (std/mean), so it's unaffected by the MRO's
        cumulative stretch. Capped at CV=2.0 → novelty=1.0.

        Replaces zlib compression of raw float32 coordinates, which always
        returned ratio ≥ 1.0 (incompressible Gaussian noise → no signal).
        """
        n = point_cloud.shape[0]
        if n < 3:
            return 0.5

        # Condensed pairwise distances: N*(N-1)/2 values, no (N,N,d) temporary.
        upper = pdist(point_cloud)

        if upper.size == 0 or upper.mean() < 1e-12:
            return 0.5

        cv = upper.std() / upper.mean()
        # Cap at 2.0: CV=2 → fully novel, CV=0 → perfectly uniform (maximally human)
        return float(np.clip(cv / 2.0, 0.0, 1.0))

    def _embedding_head(self, betti: list[int], euler: int) -> float:
        """Head 4: max cosine similarity to human-corpus probes. Low sim → high novelty."""
        if self._encoder is None:
            return 0.7

        b = (betti + [0, 0, 0])[:3]
        key = (b[0], b[1], b[2], euler)
        cached = self._embedding_cache.get(key)
        if cached is not None:
            return cached

        desc = (
            f"topology with {b[0]} components, "
            f"{b[1]} one-cycles, {b[2]} two-voids, "
            f"euler characteristic {euler}"
        )
        emb = self._encoder.encode([desc], normalize_embeddings=True)[0]
        sims = self._human_embeddings @ emb
        max_sim = float(np.max(sims))
        novelty = float(np.clip(1.0 - max_sim, 0.0, 1.0))
        self._embedding_cache[key] = novelty
        return novelty

    # ── Public API ────────────────────────────────────────────────────

    def score(
        self,
        betti: list[int],
        euler: int,
        complexity: float,
        point_cloud: np.ndarray,
    ) -> float:
        """Aggregate novelty score ∈ [0, 1]. 1.0 = maximally non-human."""
        s1 = self._semantic_head(betti, complexity)
        s2 = self._heuristic_head(point_cloud)
        s3 = self._aesthetic_head(point_cloud)
        s4 = self._embedding_head(betti, euler)

        score = float(np.dot(self.head_weights, [s1, s2, s3, s4]))
        return float(np.clip(score, 0.0, 1.0))

    def filter(self, candidates: list[CandidateLike]) -> list[CandidateLike]:
        """Filter CandidateConcepts to those passing novelty_threshold.

        In ``log_only`` mode every candidate is returned (still scored)."""
        passed = []
        for c in candidates:
            novelty = self.score(
                c.invariant.betti,
                c.invariant.euler_characteristic,
                c.invariant.complexity_score,
                c.point_cloud,
            )
            setattr(c, "_novelty_score", novelty)
            if novelty >= self.novelty_threshold or self.gate == "log_only":
                passed.append(c)
            else:
                logger.debug(
                    "AIAN rejected (novelty=%.3f < threshold=%.3f).",
                    novelty, self.novelty_threshold,
                )
        logger.info("AIAN kept %d/%d candidates (gate=%s).", len(passed), len(candidates), self.gate)
        return passed
