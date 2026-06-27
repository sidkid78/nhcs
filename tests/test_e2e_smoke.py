"""
End-to-end smoke test: full pipeline completes without exception.
"""

import asyncio
import pytest

from nhcs.bus import reset_bus
from nhcs.orchestrator.runner import EndToEndRunner


@pytest.mark.asyncio
async def test_e2e_smoke_runs_without_exception():
    """Full pipeline: RSE → AIAN → ICVP → TMFT → CRIM should complete."""
    reset_bus()
    runner = EndToEndRunner(
        n_validators=3,
        n_crim_steps=10,
        ledger_path=":memory:",
        rng_seed=7,
    )
    feedbacks = await runner.run(n_concepts=1)
    assert len(feedbacks) >= 1


@pytest.mark.asyncio
async def test_e2e_sdr_non_negative():
    reset_bus()
    runner = EndToEndRunner(n_validators=3, n_crim_steps=10, ledger_path=":memory:", rng_seed=13)
    feedbacks = await runner.run(n_concepts=1)
    assert len(feedbacks) >= 1
    assert feedbacks[0].sdr >= 0.0


@pytest.mark.asyncio
async def test_e2e_ledger_grows():
    reset_bus()
    runner = EndToEndRunner(n_validators=3, n_crim_steps=5, ledger_path=":memory:", rng_seed=21)
    await runner.run(n_concepts=1)
    assert len(runner.ledger) >= 1


@pytest.mark.asyncio
async def test_e2e_cli_bounded():
    """CLI must remain in [0,1] throughout."""
    reset_bus()
    runner = EndToEndRunner(n_validators=3, n_crim_steps=20, ledger_path=":memory:", rng_seed=99)
    feedbacks = await runner.run(n_concepts=1)
    if feedbacks:
        for cli in feedbacks[0].cli_series:
            assert 0.0 <= cli <= 1.0, f"CLI out of range: {cli}"
