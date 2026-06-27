"""
Cognitive Load Index (CLI) estimator.

Combines HRV, GSR, and pupillometry into a single scalar ∈ [0,1].
0 = fully relaxed, 1 = cognitive overload.
Target setpoint = 0.6 (Flow State).

NOTE: biometric baseline calibration (Worker-Huma-2 gap) is pending.
Current weights are literature-based defaults.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import yaml

_CONFIG_PATH = Path(__file__).parent.parent.parent / "configs" / "crim_pid.yaml"


def _load_config() -> dict:
    with open(_CONFIG_PATH) as f:
        return yaml.safe_load(f)["cli"]


class CognitiveLoadIndex:
    """
    Estimates CLI from a single biometric sample.

    Parameters
    ----------
    config_path : Path | None  (uses crim_pid.yaml defaults)
    """

    def __init__(self, config_path: Path | None = None) -> None:
        cfg = _load_config() if config_path is None else \
              yaml.safe_load(open(config_path))["cli"]
        self.w_hrv = cfg["hrv_weight"]
        self.w_gsr = cfg["gsr_weight"]
        self.w_pupil = cfg["pupil_weight"]
        self.hrv_baseline = cfg["hrv_rmssd_baseline_ms"]
        self.gsr_baseline = cfg["gsr_baseline_microsiemens"]
        self.pupil_baseline = cfg["pupil_baseline_mm"]

    def estimate(
        self,
        hrv_rmssd_ms: float,
        gsr_microsiemens: float,
        pupil_diameter_mm: float,
    ) -> float:
        """
        Compute CLI ∈ [0, 1].

        Higher HRV deviation = higher load.
        Higher GSR = higher load.
        Larger pupil = higher load.
        """
        # Normalised deviations from baselines
        hrv_dev = float(np.clip(
            (self.hrv_baseline - hrv_rmssd_ms) / (self.hrv_baseline + 1e-6),
            0.0, 1.0,
        ))
        gsr_dev = float(np.clip(
            (gsr_microsiemens - self.gsr_baseline) / (self.gsr_baseline * 4 + 1e-6),
            0.0, 1.0,
        ))
        pupil_dev = float(np.clip(
            (pupil_diameter_mm - self.pupil_baseline) / (6.0 + 1e-6),
            0.0, 1.0,
        ))

        cli = (
            self.w_hrv * hrv_dev
            + self.w_gsr * gsr_dev
            + self.w_pupil * pupil_dev
        )
        return float(np.clip(cli, 0.0, 1.0))
