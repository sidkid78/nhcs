"""
Synthetic biometric subject.

Generates simulated HRV (McSharry ECG model proxy), GSR (leaky integrator),
and pupillometry (light-reflex + cognitive load) streams.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np


@dataclass
class BiometricSample:
    timestamp_s: float
    hrv_rmssd_ms: float     # root-mean-square of successive RR differences
    gsr_microsiemens: float  # galvanic skin response
    pupil_diameter_mm: float


class SyntheticSubject:
    """
    Produces physiologically plausible biometric streams in response to
    an Immersion Intensity Score (IIS) drive.

    Parameters
    ----------
    rng_seed : int
    baseline_hrv_ms : float
    baseline_gsr : float
    baseline_pupil_mm : float
    """

    def __init__(
        self,
        rng_seed: int = 0,
        baseline_hrv_ms: float = 50.0,
        baseline_gsr: float = 2.0,
        baseline_pupil_mm: float = 3.5,
    ) -> None:
        self.rng = np.random.default_rng(rng_seed)
        self.t = 0.0
        self._hrv = baseline_hrv_ms
        self._gsr = baseline_gsr
        self._pupil = baseline_pupil_mm
        self._baseline_hrv = baseline_hrv_ms
        self._baseline_gsr = baseline_gsr
        self._baseline_pupil = baseline_pupil_mm

    def step(self, iis: float, dt: float = 0.1) -> BiometricSample:
        """
        Advance simulation by dt seconds given current IIS ∈ [0,1].

        Higher IIS → more cognitive engagement:
          - HRV decreases (sympathetic arousal suppresses vagal tone)
          - GSR increases (electrodermal arousal)
          - Pupil dilates (locus coeruleus-mediated dilation)
        """
        self.t += dt

        # McSharry-inspired HRV: mean RR ≈ 60/HR, RMSSD decreases with arousal
        hr_target = 60.0 + iis * 40.0   # 60 bpm resting → 100 bpm peak
        rr_ms = 60000.0 / hr_target
        noise = self.rng.normal(0, 3.0)
        rmssd = max(5.0, rr_ms * 0.1 + noise)

        # Leaky-integrator GSR
        gsr_drive = self._baseline_gsr + iis * 8.0
        tau_gsr = 3.0  # seconds
        self._gsr += (gsr_drive - self._gsr) / tau_gsr * dt + \
                     self.rng.normal(0, 0.05)
        self._gsr = max(0.1, self._gsr)

        # Pupil: 2–8 mm range, dilates with cognitive load
        pupil_target = 2.0 + iis * 6.0
        tau_pupil = 0.5
        self._pupil += (pupil_target - self._pupil) / tau_pupil * dt + \
                       self.rng.normal(0, 0.02)
        self._pupil = float(np.clip(self._pupil, 1.5, 9.0))

        return BiometricSample(
            timestamp_s=self.t,
            hrv_rmssd_ms=rmssd,
            gsr_microsiemens=self._gsr,
            pupil_diameter_mm=self._pupil,
        )
