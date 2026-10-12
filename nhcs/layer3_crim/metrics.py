"""
CRIM metrics: BHI (Biometric Homeostasis Index) and SDR (Semantic Distance Reduction).

Thread A (spectral-v2) SDR rewrite:
  The previous SDR computed 1 - cos(initial, final): DISPLACEMENT from the start,
  not REDUCTION toward a target — the exact opposite of what the name and
  docstring promise, and it never referenced its own `target_primes` argument.

  New SDR measures genuine convergence toward the concept's intended NSM
  encoding (from prime_map.concept_to_primes):

      d_init  = 1 - cos(v_initial, v_target)
      d_final = 1 - cos(v_final,   v_target)
      SDR     = clip( (d_init - d_final) / (d_init + eps), 0, 1 )

  SDR = 1 → final landed exactly on target; SDR = 0 → no closer (or drifted
  away). Confidence is gated by d_init: if the initial state already sits on the
  target there is nothing to reduce and any motion is noise, so confidence → 0.
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

    High BHI = low variance in all three streams = subject in stable state.
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


def _normalize_target(target_primes):
    """Accept list[(prime,weight)] or list[str] (weight 1.0) or None."""
    if not target_primes:
        return None
    if isinstance(target_primes[0], str):
        return [(p, 1.0) for p in target_primes]
    return [(p, float(w)) for p, w in target_primes]


def semantic_distance_reduction(
    initial_prime_weights: list[tuple[str, float]],
    final_prime_weights: list[tuple[str, float]],
    target_primes=None,
) -> tuple[float, float]:
    """
    SDR ∈ [0,1]: how much the prime activation moved TOWARD the target.

    Parameters
    ----------
    initial_prime_weights : [(prime, weight), ...]  — state at loop start
    final_prime_weights   : [(prime, weight), ...]  — state at loop end
    target_primes         : [(prime, weight), ...] | [prime, ...] | None
                            The concept's intended NSM encoding. If None, falls
                            back to legacy displacement 1 - cos(init, final)
                            (kept only for back-compat; the runner always passes
                            a target).

    Returns
    -------
    (sdr_score, confidence)
    """
    target = _normalize_target(target_primes)

    # ---- Legacy fallback: displacement (no target provided) ----
    if target is None:
        basis = list({p for p, _ in initial_prime_weights + final_prime_weights})
        if not basis:
            return 0.0, 0.0
        vi = _vec(initial_prime_weights, basis)
        vf = _vec(final_prime_weights, basis)
        sdr = float(np.clip(1.0 - float(np.dot(vi, vf)), 0.0, 1.0))
        conf = float(np.clip(sum(w for _, w in final_prime_weights) / 5.0, 0.0, 1.0))
        return sdr, conf

    # ---- Target-convergence SDR ----
    basis = list({
        p for p, _ in
        (initial_prime_weights + final_prime_weights + target)
    })
    if not basis:
        return 0.0, 0.0

    v_init = _vec(initial_prime_weights, basis)
    v_final = _vec(final_prime_weights, basis)
    v_tgt = _vec(target, basis)

    if np.linalg.norm(v_tgt) < 1e-8:
        return 0.0, 0.0

    d_init = 1.0 - float(np.dot(v_init, v_tgt))
    d_final = 1.0 - float(np.dot(v_final, v_tgt))

    sdr = float(np.clip((d_init - d_final) / (d_init + 1e-6), 0.0, 1.0))

    # Confidence: need meaningful room to move (d_init) AND real final signal.
    weight_conf = float(np.clip(sum(w for _, w in final_prime_weights) / 5.0, 0.0, 1.0))
    room_conf = float(np.clip(d_init, 0.0, 1.0))
    confidence = float(np.clip(weight_conf * room_conf, 0.0, 1.0))

    return sdr, confidence


def _vec(weights: list[tuple[str, float]], basis: list[str]) -> np.ndarray:
    d: dict[str, float] = {}
    for p, w in weights:
        d[p] = max(d.get(p, 0.0), float(w))  # max-pool duplicates
    v = np.array([d.get(p, 0.0) for p in basis], dtype=float)
    n = np.linalg.norm(v)
    return v / (n + 1e-8)
