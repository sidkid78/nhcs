"""
NHCS run_009 — first dataset from the constructive (pushout) generator.

Config (decided 2026-10-12):
  - RSE mode "pushout": concepts built by gluing circles/spheres via the
    categorical pushout; Betti numbers verified on the point cloud.
  - ICVP persistence_gate "blocking": a concept needs persistent loops
    (persistence ratio >= 0.5) to be approved.
  - AIAN gate "log_only": novelty is scored and written to the CSV but does
    not reject (its heads are not calibrated for constructed concepts yet).

Output: data/nhcs_run_009.csv + data/nhcs_run_009.db
Run:    python run009.py
"""

import asyncio
import logging
import pathlib
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import collect_dataset as cd

for lg in ("sentence_transformers", "httpx", "huggingface_hub",
           "nhcs.layer1_genesis.rse", "nhcs.layer1_genesis.search",
           "nhcs.layer1_genesis.constructive"):
    logging.getLogger(lg).setLevel(logging.ERROR)

RUN = "009"
cd.OUT_CSV      = pathlib.Path(f"data/nhcs_run_{RUN}.csv")
cd.LEDGER_PATH  = f"data/nhcs_run_{RUN}.db"
cd.RNG_SEED     = 42
cd.N_CONCEPTS   = 20
cd.N_CRIM_STEPS = 20
cd.GRID_SIZE    = 8

cd.RSE_CONFIG  = {**cd.RSE_CONFIG, "mode": "pushout"}
cd.AIAN_CONFIG = {**cd.AIAN_CONFIG, "gate": "log_only"}
cd.ICVP_CONFIG = {**cd.ICVP_CONFIG, "persistence_gate": "blocking"}

if __name__ == "__main__":
    if cd.OUT_CSV.exists():
        sys.exit(f"{cd.OUT_CSV} already exists — bump RUN to avoid overwriting it.")
    asyncio.run(cd.collect())
