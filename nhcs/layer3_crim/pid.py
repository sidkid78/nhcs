"""
PID controller → Immersion Intensity Score (IIS).

Wraps simple-pid. Targets CLI setpoint (default 0.6 / Flow State).
Emits a RetargetRequest when TMFT frequency adjustment is needed,
subject to the 15-40 Hz Resonant Stability Regime hard guardrail.
"""

from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import yaml
from simple_pid import PID  # type: ignore

from nhcs.schemas import RetargetRequest

logger = logging.getLogger(__name__)

_CONFIG_PATH = Path(__file__).parent.parent.parent / "configs" / "crim_pid.yaml"


def _load_config() -> dict:
    return yaml.safe_load(open(_CONFIG_PATH))


class ImmersionIntensityPID:
    """
    PID controller that drives IIS to keep CLI at setpoint.

    Parameters
    ----------
    concept_id : str  (for RetargetRequest messages)
    current_freq_hz : float  (current TMFT operating frequency)
    """

    def __init__(
        self,
        concept_id: str = "",
        current_freq_hz: float = 27.5,
        config_path: Path | None = None,
    ) -> None:
        cfg = _load_config() if config_path is None else yaml.safe_load(open(config_path))
        pid_cfg = cfg["pid"]
        guard = cfg["tmft_guardrails"]

        self.concept_id = concept_id
        self._freq = float(np.clip(current_freq_hz, guard["freq_min_hz"], guard["freq_max_hz"]))
        self._freq_min = guard["freq_min_hz"]
        self._freq_max = guard["freq_max_hz"]

        self._pid = PID(
            Kp=pid_cfg["kp"],
            Ki=pid_cfg["ki"],
            Kd=pid_cfg["kd"],
            setpoint=pid_cfg["setpoint"],
            output_limits=(pid_cfg["output_min"], pid_cfg["output_max"]),
            sample_time=pid_cfg["sample_time_s"],
        )

    @property
    def current_freq_hz(self) -> float:
        return self._freq

    def step(self, cli: float) -> tuple[float, RetargetRequest | None]:
        """
        Advance PID one step.

        Returns
        -------
        iis : float ∈ [0, 1]
        retarget : RetargetRequest | None  (None if no freq adjustment needed)
        """
        iis = float(self._pid(cli))
        if iis is None:
            iis = 0.5  # PID not ready yet

        # Heuristic: map IIS → desired freq within stability regime
        desired_freq = self._freq_min + iis * (self._freq_max - self._freq_min)
        delta = abs(desired_freq - self._freq)
        retarget = None

        if delta > 0.5:  # only emit if meaningful change requested
            clamped = float(np.clip(desired_freq, self._freq_min, self._freq_max))
            self._freq = clamped
            retarget = RetargetRequest(
                concept_id=self.concept_id,
                requested_frequency_hz=clamped,
                urgency=float(delta / (self._freq_max - self._freq_min)),
            )
            logger.debug("PID retarget: %.2f Hz (IIS=%.3f)", clamped, iis)

        return iis, retarget
