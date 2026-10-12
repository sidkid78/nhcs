"""
Topological-Physical Mapping Model (TPMM).

Translates Betti numbers + dimension to (frequency Hz, wavelength nm)
using hyperbolic saturation functions from the domain report.

  I_f = beta1 + 2*beta2     -> frequency  f(I_f) = 1 + 59*I_f / (5 + I_f)
  I_L = (beta0 - 1) + D     -> wavelength L(I_L) = 420 + 300*I_L / (5 + I_L)

Note: with K_f = 5, I_f = 1 -> f = 10.83 Hz (below RSR [15, 40] Hz).
Concepts with beta1 = 0 or 1 will be clamped in TopologyToField.translate().
Concepts with beta1 >= 2 or beta2 >= 1 (I_f >= 2) -> f >= 17.86 Hz (in RSR).

betti_to_physical() is a pure mathematical function — no clamping.
RSR clamping happens only in TopologyToField.translate().
"""

from __future__ import annotations

import logging
import math

import numpy as np

from nhcs.schemas import ConceptTarget, TopologicalSignature

logger = logging.getLogger(__name__)

# TPMM constants — from mapping_logic.json / domain report
_F_MIN, _F_MAX, _K_F = 1.0, 60.0, 5.0   # K_f = 5 (domain spec)
_L_MIN, _L_MAX, _K_L = 420.0, 720.0, 5.0

# Resonant Stability Regime
_RSR_MIN, _RSR_MAX = 15.0, 40.0


def _freq(I_f: float) -> float:
    """f(I_f) = 1 + 59 * I_f / (5 + I_f)  — hyperbolic saturation."""
    if I_f <= 0:
        return _F_MIN
    return _F_MIN + (_F_MAX - _F_MIN) * I_f / (_K_F + I_f)


def _wavelength(I_L: float) -> float:
    """L(I_L) = 420 + 300 * I_L / (5 + I_L)."""
    if I_L <= 0:
        return _L_MIN
    return _L_MIN + (_L_MAX - _L_MIN) * I_L / (_K_L + I_L)


def betti_to_physical(betti: list[int], dimension: int) -> tuple[float, float]:
    """
    Map Betti numbers + dimension to (frequency Hz, wavelength nm).

    Pure mathematical function — does NOT clamp to RSR.
    RSR enforcement happens in TopologyToField.translate().

    Returns
    -------
    (freq_hz, wavelength_nm)
    """
    b = (list(betti) + [0, 0, 0])[:3]
    I_f = b[1] + 2 * b[2]
    I_L = (b[0] - 1) + dimension
    return _freq(float(I_f)), _wavelength(float(I_L))


def crossing_to_torus_knot(crossing_number: int, bridge_index: int) -> tuple[int, int]:
    """
    Heuristic inverse mapping: (c, b) to (p, q) torus-knot parameters.

    For a torus knot T(p, q) with 2 <= p < q and gcd(p, q) = 1:
      - bridge number  b = p
      - crossing number c = q * (p - 1)   (Murasugi; min of the two forms)
    so the inverse is p = b, q = c / (p - 1). For p = 2 this gives q = c
    exactly (trefoil: c = 3 -> T(2, 3)).

    q is then bumped minimally to enforce q > p and gcd(p, q) = 1 --
    otherwise T(p, q) is a torus LINK (multiple components), not a knot.
    """
    if crossing_number <= 0:
        return 2, 3  # default: trefoil
    p = max(2, bridge_index)
    q = max(p + 1, round(crossing_number / (p - 1)))
    while math.gcd(p, q) != 1:
        q += 1
    return p, q


def build_hopf_grid(p: int, q: int, n_points: int = 256) -> np.ndarray:
    """
    Sample the (p, q) torus knot on the Clifford torus in S3.

    Parametrization (independent phases per complex coordinate):
        z1 = e^{i p t} / sqrt(2),   z2 = e^{i q t} / sqrt(2)
    i.e. (x, y, z, w) = (cos pt, sin pt, cos qt, sin qt) / sqrt(2).

    The curve winds p times around one generator of the torus and q times
    around the other; under the Hopf map it projects to a curve of the
    correct linking structure. (The previous parametrization shared one
    phase between z1 and z2 -- z1 = cos(pt) e^{iqt}, z2 = sin(pt) e^{iqt} --
    whose Hopf image degenerates to a great circle: a spherical Lissajous
    curve, not a T(p, q) knot. The JS visualizers were already correct.)

    Uses endpoint=False so the closed curve has no duplicated point.

    Returns (n_points, 4) array: (x, y, z, w) quaternion coords on S3.
    """
    t = np.linspace(0, 2 * math.pi, n_points, endpoint=False)
    inv_sqrt2 = 1.0 / math.sqrt(2.0)
    pts = np.stack([
        np.cos(p * t),
        np.sin(p * t),
        np.cos(q * t),
        np.sin(q * t),
    ], axis=1) * inv_sqrt2
    return pts.astype(np.float32)


class TopologyToField:
    """
    Converts a ConceptTarget's topological signature into:
    - target frequency (Hz) and wavelength (nm) via TPMM
    - a target Hopf map grid for the controller to invert

    This is where RSR clamping is applied — betti_to_physical() itself is pure math.
    """

    def translate(self, concept: ConceptTarget) -> dict:
        """
        Returns dict with:
          target_freq_hz, target_wavelength_nm,
          torus_p, torus_q, hopf_grid (np.ndarray)
        """
        sig = concept.signature
        freq, wl = betti_to_physical(sig.betti, sig.dimension)

        # RSR enforcement: clamp frequency to Resonant Stability Regime
        if not (_RSR_MIN <= freq <= _RSR_MAX):
            logger.warning(
                "TPMM freq %.2f Hz outside RSR [%.1f-%.1f] for betti=%s. Clamping.",
                freq, _RSR_MIN, _RSR_MAX, sig.betti,
            )
            freq = float(np.clip(freq, _RSR_MIN, _RSR_MAX))

        p, q = crossing_to_torus_knot(sig.crossing_number, sig.bridge_index)
        grid = build_hopf_grid(p, q)

        return {
            "target_freq_hz": freq,
            "target_wavelength_nm": wl,
            "torus_p": p,
            "torus_q": q,
            "hopf_grid": grid,
        }
