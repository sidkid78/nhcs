"""
LSL biometrics ingest — real or synthetic.

In simulation mode (default), delegates to SyntheticSubject.
In hardware mode, opens LSL inlets for HRV, GSR, and pupil streams.
"""

from __future__ import annotations

import logging
from typing import Optional

from nhcs.layer3_crim.synthetic_subject import BiometricSample, SyntheticSubject

logger = logging.getLogger(__name__)

try:
    import pylsl  # type: ignore
    _LSL_AVAILABLE = True
except ImportError:
    _LSL_AVAILABLE = False
    logger.debug("pylsl not available — BiometricsLSL will use synthetic subject only.")


class BiometricsLSL:
    """
    Unified biometric source.

    Parameters
    ----------
    synthetic : bool
        If True, use SyntheticSubject regardless of LSL availability.
    subject : SyntheticSubject | None
        Pre-built synthetic subject (for reproducible tests).
    """

    def __init__(
        self,
        synthetic: bool = True,
        subject: Optional[SyntheticSubject] = None,
    ) -> None:
        self._synthetic = synthetic or not _LSL_AVAILABLE
        if self._synthetic:
            self._subject = subject or SyntheticSubject()
            logger.info("BiometricsLSL: synthetic subject mode.")
        else:
            logger.info("BiometricsLSL: hardware LSL mode (not yet implemented).")

    def read(self, iis: float = 0.5, dt: float = 0.1) -> BiometricSample:
        """
        Read one biometric sample.

        In synthetic mode: steps the subject with current IIS.
        In hardware mode: pulls from LSL inlets (TODO).
        """
        if self._synthetic:
            return self._subject.step(iis, dt)
        else:
            raise NotImplementedError("Hardware LSL ingest not yet implemented.")
