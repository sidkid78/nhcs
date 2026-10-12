"""
65 NSM Semantic Primes + embodied metaphor mapping.

Maps physical vectors (spatial, temporal, magnitude, variability) to NSM primes.
Reference: Wierzbicka (1992) + Goddard (2011) universal prime list.

Thread A (spectral-v2) changes:
  * Magnitude primes use SMOOTH overlapping memberships instead of hard tanh
    bands. The old three-band cliff meant two magnitudes in the same band
    produced an identical prime SET whose only difference (a uniform weight
    scale) was erased by cosine normalisation → SDR ≡ 0. Smooth memberships give
    continuous weight response, so any magnitude change moves the prime vector.
  * A `variability` channel (structural turbulence from phen_space) maps to
    THE SAME (coherent field) vs OTHER/ELSE (cancelling / turbulent field).
  * `concept_to_primes()` derives a canonical NSM target vector from a concept's
    topology + affect, so SDR can measure convergence toward the concept's
    intended meaning rather than mere displacement from the start. Tagged
    encoding-v1 (see IntegrationFeedback.sdr_version); the Betti→prime
    assignments are a modelling choice, not derived physics.
  * `embodied_primes()` turns the subject's terminal state into engagement
    primes (FEEL / DO / intensity) so the final vector reflects the subject's
    response, not just the stimulus.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

# ---------------------------------------------------------------------------
# All 65 NSM primes (Goddard 2011 canonical list)
# ---------------------------------------------------------------------------
NSM_PRIMES: list[str] = [
    # Substantives
    "I", "YOU", "SOMEONE", "SOMETHING/THING", "PEOPLE", "BODY",
    # Determiners
    "THIS", "THE SAME", "OTHER/ELSE",
    # Quantifiers
    "ONE", "TWO", "SOME", "ALL", "MUCH/MANY", "LITTLE/FEW",
    # Evaluators
    "GOOD", "BAD",
    # Descriptors
    "BIG", "SMALL",
    # Mental predicates
    "THINK", "KNOW", "WANT", "FEEL", "SEE", "HEAR",
    # Speech
    "SAY", "WORDS", "TRUE",
    # Actions & events
    "DO", "HAPPEN", "MOVE", "TOUCH",
    # Existence & possession
    "THERE IS", "HAVE",
    # Life & death
    "LIVE", "DIE",
    # Time
    "WHEN/TIME", "NOW", "BEFORE", "AFTER", "A LONG TIME", "A SHORT TIME", "FOR SOME TIME", "MOMENT",
    # Space
    "WHERE/PLACE", "HERE", "ABOVE", "BELOW", "FAR", "NEAR", "SIDE", "INSIDE",
    # Logical
    "NOT", "MAYBE", "CAN", "BECAUSE", "IF",
    # Intensifier
    "VERY", "MORE",
    # Similarity
    "LIKE/AS/WAY",
]

assert len(NSM_PRIMES) >= 60, f"Expected ≥60 NSM primes, got {len(NSM_PRIMES)}"


@dataclass
class PrimeMappingResult:
    prime: str
    weight: float
    source: str   # "spatial" | "temporal" | "magnitude" | "variability" | ...


def _gauss(x: float, mu: float, sigma: float) -> float:
    """Smooth Gaussian membership in [0,1]."""
    return float(math.exp(-((x - mu) ** 2) / (2.0 * sigma * sigma)))


class PrimeMapper:
    """
    Maps physical vectors to weighted NSM prime activations.

    Physical vector format:
      spatial_3d  : (x, y, z) unit vector
      temporal    : float ∈ [0,1] (0=past, 1=future)
      magnitude   : float > 0
      variability : float ∈ [0,1] (structural turbulence; optional)
    """

    def map(
        self,
        spatial_3d: np.ndarray,
        temporal: float,
        magnitude: float,
        variability: float | None = None,
    ) -> list[PrimeMappingResult]:
        results: list[PrimeMappingResult] = []

        # ── Spatial primes ──
        x, y, z = spatial_3d[0], spatial_3d[1], spatial_3d[2]
        if z > 0.4:
            results.append(PrimeMappingResult("ABOVE", float(z), "spatial"))
        if z < -0.4:
            results.append(PrimeMappingResult("BELOW", float(-z), "spatial"))
        radial = float(math.sqrt(x**2 + y**2))
        if radial < 0.3:
            results.append(PrimeMappingResult("HERE", 1.0 - radial, "spatial"))
        elif radial < 0.7:
            results.append(PrimeMappingResult("NEAR", 1.0 - radial, "spatial"))
        else:
            results.append(PrimeMappingResult("FAR", radial, "spatial"))
        if x > 0.5:
            results.append(PrimeMappingResult("SIDE", float(x), "spatial"))
        if x < -0.5:
            results.append(PrimeMappingResult("SIDE", float(-x), "spatial"))

        # ── Temporal primes ──
        if temporal < 0.3:
            results.append(PrimeMappingResult("BEFORE", 1.0 - temporal / 0.3, "temporal"))
        elif temporal < 0.7:
            results.append(PrimeMappingResult("NOW", 1.0 - abs(temporal - 0.5) * 4, "temporal"))
        else:
            results.append(PrimeMappingResult("AFTER", (temporal - 0.7) / 0.3, "temporal"))

        if temporal < 0.1 or temporal > 0.9:
            results.append(PrimeMappingResult("A LONG TIME", 1.0, "temporal"))
        elif 0.45 <= temporal <= 0.55:
            results.append(PrimeMappingResult("MOMENT", 1.0, "temporal"))

        # ── Magnitude primes (SMOOTH overlapping memberships) ──
        # mag_norm ∈ (0,1). Three overlapping Gaussians centred LO/MID/HI plus a
        # monotone HIGH ramp. Every prime that can fire always fires with a
        # continuous weight, so ANY change in magnitude moves the vector — the
        # exact-zero band-collapse is structurally impossible.
        mag_norm = float(np.tanh(magnitude))
        w_lo = _gauss(mag_norm, 0.0, 0.28)
        w_mid = _gauss(mag_norm, 0.5, 0.22)
        w_hi = _gauss(mag_norm, 1.0, 0.28)
        ramp = mag_norm  # monotone intensity ramp

        results.append(PrimeMappingResult("LITTLE/FEW", w_lo, "magnitude"))
        results.append(PrimeMappingResult("SMALL", w_lo, "magnitude"))
        results.append(PrimeMappingResult("SOME", w_mid, "magnitude"))
        results.append(PrimeMappingResult("MUCH/MANY", 0.5 * w_hi + 0.5 * ramp, "magnitude"))
        results.append(PrimeMappingResult("BIG", 0.5 * w_hi + 0.5 * ramp, "magnitude"))
        results.append(PrimeMappingResult("VERY", ramp, "magnitude"))

        # ── Variability primes (structural turbulence) ──
        if variability is not None:
            v = float(np.clip(variability, 0.0, 1.0))
            # coherent field → THE SAME ; cancelling/turbulent → OTHER/ELSE
            results.append(PrimeMappingResult("THE SAME", 1.0 - v, "variability"))
            results.append(PrimeMappingResult("OTHER/ELSE", v, "variability"))

        return _dedup_sorted(results)


def _dedup_sorted(results: list[PrimeMappingResult]) -> list[PrimeMappingResult]:
    """Keep the max-weight instance of each prime, sorted by descending weight."""
    seen: dict[str, PrimeMappingResult] = {}
    for r in results:
        if r.prime not in seen or r.weight > seen[r.prime].weight:
            seen[r.prime] = r
    return sorted(seen.values(), key=lambda r: -r.weight)


# ---------------------------------------------------------------------------
# Canonical target encoding: concept → NSM primes  (encoding-v1)
# ---------------------------------------------------------------------------
def concept_to_primes(
    betti: list[int],
    complexity_score: float = 0.0,
    arousal: float = 0.5,
    valence: float = 0.0,
) -> list[tuple[str, float]]:
    """
    Derive a concept's intended NSM prime vector from its topology + affect.

    This is the *target* SDR converges toward. Assignments (encoding-v1):
      β₀ (components) → cardinality: ONE / TWO / SOME / MUCH-MANY
      β₁ (loops)      → MOVE (recurrent circulation), strength ∝ min(β₁/3, 1)
      β₂ (voids)      → INSIDE + THERE IS (enclosed interior)
      complexity      → VERY / MORE
      arousal         → FEEL + DO
      valence         → GOOD (v>0) / BAD (v<0), weight ∝ |v|
      structure       → OTHER/ELSE (dense/complex) vs THE SAME (simple/coherent),
                        matching the phen_space variability channel.

    Returns [(prime, weight), ...] with weights in ~[0,1]. Modelling choice, not
    derived physics — versioned so pre/post values are never pooled.
    """
    b = list(betti) + [0, 0, 0]  # pad
    b0, b1, b2 = int(b[0]), int(b[1]), int(b[2])
    out: list[tuple[str, float]] = []

    # β₀ → cardinality
    if b0 <= 1:
        out.append(("ONE", 0.9))
    elif b0 == 2:
        out.append(("TWO", 0.9))
    elif b0 <= 5:
        out.append(("SOME", 0.8))
    else:
        out.append(("MUCH/MANY", 0.9))

    # β₁ → recurrent circulation
    if b1 > 0:
        out.append(("MOVE", float(np.clip(b1 / 3.0, 0.2, 1.0))))
        if b1 >= 3:
            out.append(("MUCH/MANY", 0.6))  # many loops

    # β₂ → enclosed interior
    if b2 > 0:
        out.append(("INSIDE", float(np.clip(0.4 + 0.2 * b2, 0.4, 1.0))))
        out.append(("THERE IS", 0.6))

    # complexity → intensifier
    c = float(np.clip(math.tanh(max(complexity_score, 0.0)), 0.0, 1.0))
    if c > 0.05:
        out.append(("VERY", c))
        out.append(("MORE", 0.6 * c))

    # arousal → embodied engagement
    a = float(np.clip(arousal, 0.0, 1.0))
    out.append(("FEEL", a))
    out.append(("DO", 0.7 * a))

    # valence → evaluation
    if valence > 1e-3:
        out.append(("GOOD", float(np.clip(valence, 0.0, 1.0))))
    elif valence < -1e-3:
        out.append(("BAD", float(np.clip(-valence, 0.0, 1.0))))

    # structural coherence → similarity primes (matches phen_space variability).
    # Topologically dense / complex concepts present as turbulent, directionally
    # incoherent fields (OTHER/ELSE); simple concepts as coherent (THE SAME).
    structure = float(np.clip(0.5 * min(b1 / 4.0, 1.0) + 0.5 * c, 0.0, 1.0))
    if structure >= 0.5:
        out.append(("OTHER/ELSE", structure))
    else:
        out.append(("THE SAME", 1.0 - structure))

    # collapse duplicates (max weight)
    seen: dict[str, float] = {}
    for p, w in out:
        if p not in seen or w > seen[p]:
            seen[p] = w
    return sorted(seen.items(), key=lambda kv: -kv[1])


# ---------------------------------------------------------------------------
# Embodied primes: subject terminal state → engagement NSM primes
# ---------------------------------------------------------------------------
def embodied_primes(
    mean_cli: float,
    iis: float,
    bhi: float = 1.0,
) -> list[tuple[str, float]]:
    """
    Turn the subject's terminal state into embodied primes appended to the FINAL
    vector, so SDR reflects the subject's response converging toward the
    concept's intended affect/intensity.

      mean_cli → FEEL   (felt cognitive/autonomic engagement)
                 + reinforces VERY / MORE (high engagement = intensity)
      iis      → DO     (active immersion / engagement)
      bhi      → GOOD   (homeostatic stability), LOW weight only

    Design note (measured, spectral-v2): the original spec mapped BHI → GOOD/BAD
    at full weight. The harness showed BHI ≈ 0.91 for EVERY concept in synthetic
    mode (the subject's leaky integrators always settle), so a full-weight BHI
    term injects a constant, concept-blind, always-positive affect that both
    fails to discriminate and mis-signs negative-valence concepts. Embodied
    VALENCE cannot be synthesised without reading the concept's own valence
    (circular → trivially inflates SDR), so the subject legitimately has no
    hedonic channel here. GOOD is therefore kept only as a weak "experience was
    tolerable" signal; BAD is not synthesised. This is a synthetic-mode ceiling,
    not a defect — a real subject with an affect channel would restore it.
    """
    cli = float(np.clip(mean_cli, 0.0, 1.0))
    im = float(np.clip(iis, 0.0, 1.0))
    stab = float(np.clip(bhi, 0.0, 1.0))
    out: list[tuple[str, float]] = [
        ("FEEL", cli),
        ("DO", im),
        ("VERY", 0.5 * cli),
        ("MORE", 0.4 * cli),
        ("GOOD", 0.3 * stab),   # low weight; near-constant in synthetic mode
    ]
    return out
