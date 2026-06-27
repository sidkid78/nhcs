# NHCS Run Results

Recorded 2026-06-27 on Windows 11, Python 3.13.3 (`.venv`), CPU-only.

## Test suite

```
pytest -q
```

**35 passed in 96.63s** (0 failures, 0 errors).

Covers: `test_consensus`, `test_e2e_smoke`, `test_invariants`, `test_pid_stability`, `test_tpmm`.
Heavy first-run cost is model/extension import (sentence-transformers, gudhi, jax), not test logic.

## Demo pipeline

```
python -m nhcs.orchestrator.digital_twin_demo   # nhcs-demo
```

One concept, end-to-end through all three layers. Config (`configs/default.yaml`):
`grid_size=16  n_seeds=20  n_crim_steps=50`. Exit code 0.

### Per-layer trace

| Stage | Result |
|-------|--------|
| Layer 1 — RSE | 20/20 valid candidate complexes |
| Layer 1 — AIAN | kept 1/20 (novelty filter, threshold 0.6) |
| Layer 1 — Divergent Beam Search | selected 1/1 |
| Layer 1 — ICVP consensus | 5/5 approved (need 4) → **PASS** |
| Layer 1 — Ledger | committed `69fa320c` |
| Layer 2 — TPMM | freq 10.83 Hz outside RSR [15–40] for `betti=[9,1,0]` → **clamped to 15.0 Hz** |
| Layer 2 — Controller | `target_c=8.500 achieved=6.1875 error=27.2% iters=9 success=True [L=45mm]` |
| Layer 2 — DigitalTwin | `B=1.03 mT  freq=15.0 Hz` (0.95 s) |

### Final metrics

| Metric | Value | Target / note |
|--------|-------|---------------|
| Concept ID | `69fa320c` | committed to ledger (size 1) |
| BHI (biometric stability) | **0.9101** | target → 1.0 |
| SDR (semantic distance reduction) | **0.0018** | higher = more uptake |
| SDR confidence | 1.0000 | |
| CLI mean | **0.1479** | target 0.6 (flow state) |
| IIS final | 0.4631 | |
| CRIM steps | 50 | |

### Observations

- The loop runs and is **stable** (BHI ≈ 0.91), which is the Milestone-3 success criterion ("verify the loop is stable").
- **CLI mean 0.15 is well below the 0.6 flow-state setpoint** — the PID does not drive the synthetic subject into the target band within 50 steps. Worth checking PID gains in `configs/crim_pid.yaml` and/or step count.
- **SDR ≈ 0.0018 is near zero** — negligible semantic-distance reduction on a single concept, expected for one-shot (no closed-loop adaptation across rounds).
- Layer 2 controller leaves **27.2% crossing-number error** (`target_c=8.5`, `achieved=6.19`); reduced-order Hopfion model at `grid_size=16` (dev fidelity, not 64).
- The requested oscillation frequency (10.83 Hz) was below the hard 15–40 Hz stability floor and was clamped, as designed.

## Issue surfaced and fixed during this run

`nhcs/orchestrator/digital_twin_demo.py` logs the RESULTS block with Unicode characters (`━`, `→`).
On Windows the default stdout is cp1252, so those `logger.info` calls raised `UnicodeEncodeError`
and the RESULTS table was **lost** (the pipeline itself still completed, exit 0).

**Fixed:** added `sys.stdout.reconfigure(encoding="utf-8")` at startup (before `logging.basicConfig`,
which captures `sys.stdout`), matching the idiom already used by the root-level scripts
(`collect_dataset.py`, etc.). Verified: plain `nhcs-demo` with no env vars now prints the full
RESULTS block on Windows, exit 0.
