"""
Abstraction Calibration Airlock.

Middleware between TMFT (Layer 2) and CRIM (Layer 3).
Enforces TMFT hardware guardrails: CRIM's semantic throttling
cannot alter TMFT frequencies outside the 15-40 Hz RSR.
"""

from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import yaml

from nhcs.schemas import PhysicalRealization, RetargetRequest

logger = logging.getLogger(__name__)

_CONFIG_PATH = Path(__file__).parent.parent.parent / "configs" / "crim_pid.yaml"


class AbstractionCalibrationAirlock:
    """
    Validates and sanitises all L3→L2 RetargetRequests.
    """

    def __init__(self, config_path: Path | None = None) -> None:
        cfg = yaml.safe_load(open(config_path or _CONFIG_PATH))
        guard = cfg["tmft_guardrails"]
        iis_cfg = cfg["iis"]
        self.freq_min = guard["freq_min_hz"]
        self.freq_max = guard["freq_max_hz"]
        # Charge error threshold — read from config (relaxed for simulation mode).
        self.max_charge_error_pct = float(guard.get("max_charge_error_pct", 50.0))
        self.abstraction_levels = iis_cfg["abstraction_levels"]

    def validate_retarget(self, request: RetargetRequest) -> RetargetRequest:
        """Clamp requested frequency to RSR."""
        clamped = float(np.clip(request.requested_frequency_hz,
                                self.freq_min, self.freq_max))
        if abs(clamped - request.requested_frequency_hz) > 0.01:
            logger.warning(
                "Airlock clamped retarget %.2f → %.2f Hz (RSR [%.0f-%.0f Hz]).",
                request.requested_frequency_hz, clamped, self.freq_min, self.freq_max,
            )
        return RetargetRequest(
            concept_id=request.concept_id,
            requested_frequency_hz=clamped,
            urgency=request.urgency,
        )

    def iis_to_abstraction_level(self, iis: float) -> int:
        """Map IIS ∈ [0,1] → discrete abstraction level ∈ [0, n-1]."""
        level = int(np.round(iis * (self.abstraction_levels - 1)))
        return int(np.clip(level, 0, self.abstraction_levels - 1))

    def check_physical_integrity(self, realization: PhysicalRealization) -> bool:
        """
        Verify a PhysicalRealization is within safe operating bounds.

        Frequency must be within RSR [15, 40] Hz.
        Charge error must be below max_charge_error_pct (config-driven;
        relaxed in simulation mode pending hardware calibration).
        """
        freq_ok = self.freq_min <= realization.target_frequency_hz <= self.freq_max
        charge_ok = realization.charge_error_pct < self.max_charge_error_pct

        if not freq_ok:
            logger.error(
                "Airlock: realization frequency %.2f Hz outside RSR!",
                realization.target_frequency_hz,
            )
        if not charge_ok:
            logger.warning(
                "Airlock: charge error %.1f%% exceeds threshold %.1f%%.",
                realization.charge_error_pct, self.max_charge_error_pct,
            )
        return freq_ok and charge_ok
