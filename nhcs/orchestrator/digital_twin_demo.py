"""
NHCS "Hello World" — digital twin demo.

Runs one concept end-to-end through all three layers with a synthetic
subject and logs the key metrics.

Usage::

    python -m nhcs.orchestrator.digital_twin_demo
    # or:
    nhcs-demo
"""

from __future__ import annotations

import asyncio
import logging
import sys
from pathlib import Path

import yaml

from nhcs.bus import reset_bus
from nhcs.orchestrator.runner import EndToEndRunner

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("nhcs.demo")

_DEFAULT_CFG = Path(__file__).parent.parent.parent / "configs" / "default.yaml"


async def _run() -> None:
    reset_bus()

    # Load config — all tunable parameters come from here, not hardcoded
    cfg = yaml.safe_load(open(_DEFAULT_CFG))
    l1 = cfg["layer1"]
    l2 = cfg["layer2"]
    l3 = cfg["layer3"]

    runner = EndToEndRunner(
        n_validators=l1["icvp"]["n_validators"],
        n_crim_steps=l3["crim"]["n_crim_steps"],
        ledger_path=":memory:",
        rng_seed=cfg["run"]["seed"],
        grid_size=l2["twin"]["grid_size"],
        rse_n_seeds=l1["rse"]["n_seed_complexes"],
    )

    logger.info("=" * 60)
    logger.info("NHCS Digital Twin Demo — running 1 concept end-to-end")
    logger.info("grid_size=%d  n_seeds=%d  n_crim_steps=%d",
                l2["twin"]["grid_size"],
                l1["rse"]["n_seed_complexes"],
                l3["crim"]["n_crim_steps"])
    logger.info("=" * 60)

    feedbacks = await runner.run(n_concepts=1)

    if not feedbacks:
        logger.error("No concepts survived the full pipeline. Increase n_seed_complexes.")
        return

    fb = feedbacks[0]
    logger.info("")
    logger.info("━━━ RESULTS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    logger.info("Concept ID    : %s", fb.concept_id[:8])
    logger.info("Ledger size   : %d concept(s)", len(runner.ledger))
    logger.info("BHI           : %.4f  (biometric stability, target → 1.0)", fb.bhi)
    logger.info("SDR           : %.4f  (semantic distance reduction)", fb.sdr)
    logger.info("SDR confidence: %.4f", fb.sdr_confidence)
    logger.info("CLI mean      : %.4f  (target 0.6 = flow state)",
                sum(fb.cli_series) / len(fb.cli_series))
    logger.info("IIS final     : %.4f", fb.iis_series[-1] if fb.iis_series else 0.0)
    logger.info("CRIM steps    : %d", fb.n_integration_steps)
    logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")


def main() -> None:
    asyncio.run(_run())


if __name__ == "__main__":
    main()
