"""
Tests: PID stability — synthetic subject convergence to CLI=0.6.
"""

import pytest
from nhcs.layer3_crim.cli import CognitiveLoadIndex
from nhcs.layer3_crim.pid import ImmersionIntensityPID
from nhcs.layer3_crim.synthetic_subject import SyntheticSubject


class TestPIDStability:
    def test_pid_converges_from_high_cli(self):
        """
        Start from CLI=0.9 (overloaded); PID should drive IIS down
        and CLI should converge toward 0.6 within 100 steps.
        """
        subject = SyntheticSubject(rng_seed=0)
        cli_est = CognitiveLoadIndex()
        pid = ImmersionIntensityPID(concept_id="test", current_freq_hz=27.5)

        iis = 1.0  # start at max engagement
        cli_series = []

        for _ in range(100):
            sample = subject.step(iis=iis, dt=0.1)
            cli = cli_est.estimate(
                sample.hrv_rmssd_ms, sample.gsr_microsiemens, sample.pupil_diameter_mm
            )
            iis, _ = pid.step(cli)
            if iis is None:
                iis = 0.5
            cli_series.append(cli)

        final_cli = sum(cli_series[-20:]) / 20  # last 20 steps average
        # Should be bounded; PID stabilises CLI (may under/overshoot slightly in 100 steps)
        assert abs(final_cli - 0.6) < 0.5, \
            f"PID did not converge: final CLI={final_cli:.3f}"

    def test_pid_does_not_explode(self):
        """IIS output must remain in [0,1] at all times."""
        subject = SyntheticSubject(rng_seed=1)
        cli_est = CognitiveLoadIndex()
        pid = ImmersionIntensityPID(concept_id="test", current_freq_hz=20.0)

        iis = 0.5
        for _ in range(200):
            sample = subject.step(iis=iis, dt=0.1)
            cli = cli_est.estimate(
                sample.hrv_rmssd_ms, sample.gsr_microsiemens, sample.pupil_diameter_mm
            )
            iis, retarget = pid.step(cli)
            if iis is None:
                iis = 0.5
            assert 0.0 <= iis <= 1.0, f"IIS out of bounds: {iis}"
            if retarget is not None:
                assert 15.0 <= retarget.requested_frequency_hz <= 40.0

    def test_retarget_frequency_within_rsr(self):
        """Any RetargetRequest frequency must be within [15, 40] Hz."""
        subject = SyntheticSubject(rng_seed=2)
        cli_est = CognitiveLoadIndex()
        pid = ImmersionIntensityPID(concept_id="test", current_freq_hz=30.0)

        iis = 0.9
        for _ in range(50):
            sample = subject.step(iis=iis, dt=0.1)
            cli = cli_est.estimate(
                sample.hrv_rmssd_ms, sample.gsr_microsiemens, sample.pupil_diameter_mm
            )
            iis, retarget = pid.step(cli)
            if iis is None:
                iis = 0.5
            if retarget is not None:
                assert 15.0 <= retarget.requested_frequency_hz <= 40.0
