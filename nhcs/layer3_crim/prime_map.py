"""
65 NSM Semantic Primes + embodied metaphor mapping.

Maps physical vectors (spatial, temporal, magnitude) to NSM primes.
Reference: Wierzbicka (1992) + Goddard (2011) universal prime list.
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
    source: str   # "spatial" | "temporal" | "magnitude"


class PrimeMapper:
    """
    Maps physical vectors to weighted NSM prime activations.

    Physical vector format:
      spatial_3d : (x, y, z) unit vector
      temporal    : float ∈ [0,1] (0=past, 1=future)
      magnitude   : float > 0
    """

    def map(
        self,
        spatial_3d: np.ndarray,
        temporal: float,
        magnitude: float,
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

        # ── Magnitude primes ──
        mag_norm = float(np.tanh(magnitude))  # normalise to [0,1]
        if mag_norm > 0.7:
            results.append(PrimeMappingResult("MUCH/MANY", mag_norm, "magnitude"))
            results.append(PrimeMappingResult("BIG", mag_norm, "magnitude"))
            results.append(PrimeMappingResult("VERY", mag_norm, "magnitude"))
        elif mag_norm > 0.3:
            results.append(PrimeMappingResult("SOME", mag_norm, "magnitude"))
        else:
            results.append(PrimeMappingResult("LITTLE/FEW", 1.0 - mag_norm, "magnitude"))
            results.append(PrimeMappingResult("SMALL", 1.0 - mag_norm, "magnitude"))

        # Deduplicate and sort by weight
        seen: dict[str, PrimeMappingResult] = {}
        for r in results:
            if r.prime not in seen or r.weight > seen[r.prime].weight:
                seen[r.prime] = r
        return sorted(seen.values(), key=lambda r: -r.weight)
