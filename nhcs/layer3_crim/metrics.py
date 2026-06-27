"""
CRIM metrics: BHI (Biometric Homeostasis Index) and SDR (Semantic Distance Reduction).
"""

from __future__ import annotations

import numpy as np


def biometric_homeostasis_index(
    hrv_series: list[float],
    gsr_series: list[float],
    pupil_series: list[float],
) -> float:
    """
    BHI ∈ [0,1]: measures stability of the biometric signals.

    High BHI = low variance in all three streams = subject is in stable cognitive state.
    """
    if not hrv_series:
        return 0.0

    def _stability(series: list[float]) -> float:
        arr = np.array(series)
        if arr.std() == 0 or arr.mean() == 0:
            return 1.0
        cv = arr.std() / (arr.mean() + 1e-8)
        return float(np.clip(1.0 / (1.0 + cv), 0.0, 1.0))

    return float(np.mean([
        _stability(hrv_series),
        _stability(gsr_series),
        _stability(pupil_series),
    ]))


def semantic_distance_reduction(
    initial_prime_weights: list[tuple[str, float]],
    final_prime_weights: list[tuple[str, float]],
    target_primes: list[str] | None = None,
) -> tuple[float, float]:
    """
    SDR ∈ [0,1]: measures how much the prime activation moved toward target.

    Parameters
    ----------
    initial_prime_weights : [(prime, weight), ...]
    final_prime_weights   : [(prime, weight), ...]
    target_primes         : list of prime names considered 'target concepts'
                            (None → compare vector cosine similarity)

    Returns
    -------
    (sdr_score, confidence)
    """
    all_primes = list({p for p, _ in initial_prime_weights + final_prime_weights})
    if not all_primes:
        return 0.0, 0.0

    def _to_vec(weights: list[tuple[str, float]]) -> np.ndarray:
        d = dict(weights)
        v = np.array([d.get(p, 0.0) for p in all_primes], dtype=float)
        norm = np.linalg.norm(v)
        return v / (norm + 1e-8)

    v_init = _to_vec(initial_prime_weights)
    v_final = _to_vec(final_prime_weights)

    cos_sim = float(np.dot(v_init, v_final))
    # SDR = 1 - cosine similarity (moved away from initial = semantic drift)
    sdr = float(np.clip(1.0 - cos_sim, 0.0, 1.0))

    # Confidence: based on total weight magnitude
    total_weight = sum(w for _, w in final_prime_weights)
    confidence = float(np.clip(total_weight / 5.0, 0.0, 1.0))

    return sdr, confidence
