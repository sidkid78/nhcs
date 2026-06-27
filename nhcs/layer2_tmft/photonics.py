"""
Magneto-photonic layer: maps wavelength (nm) → RGB colour tuple.

Uses a simple piecewise linear spectral locus approximation
for the 420-720 nm range visible to the chamber optical sensors.
"""

from __future__ import annotations
import numpy as np


def wavelength_to_rgb(wavelength_nm: float) -> tuple[float, float, float]:
    """
    Convert a visible wavelength to an approximate (R, G, B) tuple ∈ [0,1].
    Based on the CIE approximation by Dan Bruton (physics.sfasu.edu).
    """
    wl = float(np.clip(wavelength_nm, 380, 750))
    if 380 <= wl < 440:
        r, g, b = -(wl - 440) / 60, 0.0, 1.0
    elif 440 <= wl < 490:
        r, g, b = 0.0, (wl - 440) / 50, 1.0
    elif 490 <= wl < 510:
        r, g, b = 0.0, 1.0, -(wl - 510) / 20
    elif 510 <= wl < 580:
        r, g, b = (wl - 510) / 70, 1.0, 0.0
    elif 580 <= wl < 645:
        r, g, b = 1.0, -(wl - 645) / 65, 0.0
    else:
        r, g, b = 1.0, 0.0, 0.0

    # Intensity drop-off at spectral edges
    if 380 <= wl < 420:
        factor = 0.3 + 0.7 * (wl - 380) / 40
    elif 700 < wl <= 750:
        factor = 0.3 + 0.7 * (750 - wl) / 50
    else:
        factor = 1.0

    return (
        float(np.clip(r * factor, 0.0, 1.0)),
        float(np.clip(g * factor, 0.0, 1.0)),
        float(np.clip(b * factor, 0.0, 1.0)),
    )


def emission_spectrum(
    wavelength_nm: float,
    frequency_hz: float,
    duration_s: float = 1.0,
    sample_hz: float = 60.0,
) -> dict:
    """
    Generate a sampled emission spectrum trajectory.

    Returns dict with lists: timestamps_s, wavelength_nm, frequency_hz, intensity.
    """
    n = max(2, int(duration_s * sample_hz))
    t = np.linspace(0, duration_s, n)
    # Sinusoidal intensity modulated at frequency_hz
    intensity = 0.5 + 0.5 * np.sin(2 * np.pi * frequency_hz * t)
    return {
        "timestamps_s": t.tolist(),
        "wavelength_nm": [wavelength_nm] * n,
        "frequency_hz": [frequency_hz] * n,
        "intensity": intensity.tolist(),
    }
