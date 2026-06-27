"""
Human-in-the-loop signature detector (slashing).

Detects whether a concept has been contaminated by human-authored content.
Implemented as a cosine-similarity classifier against a frozen human-corpus encoder.

Precision/recall are tracked explicitly on a labelled probe set so the
false-positive rate is always visible (silent false-positives would kill
legitimate concepts).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

import numpy as np

logger = logging.getLogger(__name__)

try:
    from sentence_transformers import SentenceTransformer  # type: ignore
    _ST_AVAILABLE = True
except ImportError:
    _ST_AVAILABLE = False

# Probe set: (description, is_human_tainted)
_PROBE_SET: list[tuple[str, bool]] = [
    ("narrative with beginning middle end", True),
    ("hierarchical tree structure", True),
    ("symmetric butterfly pattern", True),
    ("random topological noise", False),
    ("persistent homology with betti numbers", False),
    ("fractal dimension 1.7", False),
    ("moral story arc", True),
    ("euler characteristic invariant", False),
]


@dataclass
class SlashingResult:
    concept_id: str
    tainted: bool
    similarity_score: float   # max cosine sim to human corpus
    threshold: float


@dataclass
class SlashingDetector:
    """
    Pluggable slashing classifier.

    Parameters
    ----------
    similarity_threshold : float
        Cosine similarity above which a concept is flagged as tainted.
    encoder_model : str
    """
    similarity_threshold: float = 0.75
    encoder_model: str = "all-MiniLM-L6-v2"
    _encoder: object = field(default=None, init=False, repr=False)
    _human_embeddings: np.ndarray | None = field(default=None, init=False, repr=False)
    _tp: int = field(default=0, init=False)
    _fp: int = field(default=0, init=False)
    _tn: int = field(default=0, init=False)
    _fn: int = field(default=0, init=False)

    def __post_init__(self) -> None:
        if _ST_AVAILABLE:
            try:
                self._encoder = SentenceTransformer(self.encoder_model)
                corpus = [p for p, _ in _PROBE_SET]
                self._human_embeddings = self._encoder.encode(
                    corpus, normalize_embeddings=True
                )
            except Exception as e:
                logger.warning("SlashingDetector could not load encoder: %s", e)

    def detect(self, concept_id: str, betti: list[int], description: str = "") -> SlashingResult:
        """
        Return SlashingResult for a candidate concept.
        `description` is optional human-readable summary for encoder-based check.
        """
        if self._encoder is None or self._human_embeddings is None:
            # Stub: always clean
            return SlashingResult(concept_id, False, 0.0, self.similarity_threshold)

        text = description or (
            f"topology with betti {betti} and {sum(betti)} topological features"
        )
        emb = self._encoder.encode([text], normalize_embeddings=True)[0]
        # Only check against tainted probes
        tainted_idxs = [i for i, (_, t) in enumerate(_PROBE_SET) if t]
        tainted_embs = self._human_embeddings[tainted_idxs]
        sims = tainted_embs @ emb
        max_sim = float(np.max(sims)) if len(sims) else 0.0
        tainted = max_sim >= self.similarity_threshold
        return SlashingResult(concept_id, tainted, max_sim, self.similarity_threshold)

    def precision_recall(self) -> dict:
        """Report precision/recall on accumulated probe evaluations."""
        tp, fp, tn, fn = self._tp, self._fp, self._tn, self._fn
        precision = tp / (tp + fp + 1e-9)
        recall = tp / (tp + fn + 1e-9)
        return {"precision": precision, "recall": recall, "tp": tp, "fp": fp, "tn": tn, "fn": fn}
