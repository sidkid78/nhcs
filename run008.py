"""
NHCS run_008 — AIAN parameter-grid sweep.

Crosses the two newly config-driven AIAN knobs:
  - novelty_threshold ∈ {0.50, 0.60, 0.70}
  - head_weights      ∈ {baseline, embed_heavy, balanced, shape_heavy}

3 × 4 = 12 cells, all on the same RSE seed (42) so the candidate stream is
identical across cells and only the AIAN gate/weights differ — a controlled
comparison.

Each cell writes its own per-concept CSV + ledger:
    data/nhcs_run_008_t{thr}_{wname}.csv / .db
and one aggregate row to:
    data/nhcs_run_008_summary.csv
capturing pass-rate and mean downstream metrics per cell.

Run:  python run008.py
"""

from __future__ import annotations

import asyncio
import csv
import logging
import statistics
import sys
from pathlib import Path

# Force UTF-8 on stdout for Windows cp1252 compatibility.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import collect_dataset as cd

# Quiet the verbose per-candidate / model-load chatter; we want the sweep line.
for _lg in (
    "sentence_transformers", "httpx", "huggingface_hub",
    "nhcs.layer1_genesis.rse", "nhcs.layer1_genesis.search",
    "nhcs.layer1_genesis.aian", "nhcs.collect",
):
    logging.getLogger(_lg).setLevel(logging.ERROR)

logger = logging.getLogger("nhcs.run008")
logging.basicConfig(level=logging.INFO, format="%(message)s", stream=sys.stdout)

# ── Sweep grid ────────────────────────────────────────────────────────────
THRESHOLDS = [0.50, 0.60, 0.70]
WEIGHTS: dict[str, list[float]] = {
    # name          [semantic, heuristic, aesthetic, embedding]
    "baseline":    [0.15, 0.25, 0.20, 0.40],
    "embed_heavy": [0.10, 0.15, 0.15, 0.60],
    "balanced":    [0.25, 0.25, 0.25, 0.25],
    "shape_heavy": [0.15, 0.35, 0.35, 0.15],
}

# ── Shared run params (held constant across all cells) ─────────────────────
cd.RNG_SEED     = 42
cd.N_CONCEPTS   = 8
cd.N_CRIM_STEPS = 20
cd.GRID_SIZE    = 8

OUT = Path("data")

SUMMARY_FIELDS = [
    "cell", "novelty_threshold", "weights_name", "head_weights",
    "n_collected", "n_target", "attempts", "pass_rate",
    "mean_novelty", "mean_beta1", "mean_complexity",
    "mean_bhi", "mean_cli", "mean_sdr",
]


def _mean(rows, key):
    vals = [r[key] for r in rows if r.get(key) is not None]
    return round(statistics.mean(vals), 4) if vals else None


async def main() -> None:
    summary_rows = []
    cells = [(thr, wname, w) for thr in THRESHOLDS for wname, w in WEIGHTS.items()]
    logger.info("run_008 sweep — %d cells (seed=%d, N=%d/cell)\n",
                len(cells), cd.RNG_SEED, cd.N_CONCEPTS)

    for i, (thr, wname, w) in enumerate(cells, 1):
        tag = f"t{int(thr * 100)}_{wname}"
        cd.OUT_CSV     = OUT / f"nhcs_run_008_{tag}.csv"
        cd.LEDGER_PATH = str(OUT / f"nhcs_run_008_{tag}.db")
        cd.AIAN_CONFIG = {"novelty_threshold": thr, "head_weights": w}

        logger.info("[%2d/%d] thr=%.2f  weights=%-11s ...", i, len(cells), thr, wname)
        result = await cd.collect()

        rows = result["rows"]
        attempts = result["attempts"]
        n_coll = result["n_collected"]
        pass_rate = round(n_coll / attempts, 4) if attempts else 0.0

        srow = {
            "cell": tag,
            "novelty_threshold": thr,
            "weights_name": wname,
            "head_weights": "|".join(str(x) for x in w),
            "n_collected": n_coll,
            "n_target": cd.N_CONCEPTS,
            "attempts": attempts,
            "pass_rate": pass_rate,
            "mean_novelty": _mean(rows, "novelty_aggregate"),
            "mean_beta1": _mean(rows, "beta1"),
            "mean_complexity": _mean(rows, "complexity_score"),
            "mean_bhi": _mean(rows, "bhi"),
            "mean_cli": _mean(rows, "cli_mean"),
            "mean_sdr": _mean(rows, "sdr"),
        }
        summary_rows.append(srow)
        logger.info(
            "        -> collected %d/%d (pass_rate=%.3f)  "
            "novelty=%s  BHI=%s  CLI=%s  SDR=%s",
            n_coll, cd.N_CONCEPTS, pass_rate,
            srow["mean_novelty"], srow["mean_bhi"],
            srow["mean_cli"], srow["mean_sdr"],
        )

    summary_path = OUT / "nhcs_run_008_summary.csv"
    with open(summary_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=SUMMARY_FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(summary_rows)

    logger.info("\n=== SWEEP COMPLETE ===")
    logger.info("Cells: %d   Summary: %s", len(summary_rows), summary_path)


if __name__ == "__main__":
    asyncio.run(main())
