# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

NHCS (Non-Human Conceptual Synthesis) — a three-layer research prototype for generating, translating, and communicating non-anthropocentric concepts. Python 3.11+, fully async.

## Build & Run Commands

```bash
# Install (editable, with dev dependencies)
pip install -e ".[dev]"
# or, with uv (uv.lock is checked in):
uv sync --extra dev

# Run the demo pipeline
nhcs-demo
# or: python -m nhcs.orchestrator.digital_twin_demo

# Run all tests
pytest

# Run a single test file, class, or test function (tests are class-based)
pytest tests/test_invariants.py
pytest tests/test_invariants.py::TestBettiNumbers::test_circle_has_one_loop -v
```

Tests use `asyncio_mode="auto"` (configured in pyproject.toml) — no manual event loop setup needed.

## Data Collection & Tooling (root-level scripts)

These are standalone scripts at the repo root (not part of the `nhcs` package), used to produce experimental runs and review outputs:

- **`collect_dataset.py`** — instruments the full pipeline and writes per-concept rows (Betti profile, complexity, AIAN novelty, physical params, NSM prime activations, biometrics, SDR) to `data/nhcs_run_*.csv` plus a `.db` ledger. Exposes module-level globals (`OUT_CSV`, `LEDGER_PATH`, `RNG_SEED`, `N_CONCEPTS`, `N_CRIM_STEPS`, `GRID_SIZE`) and an async `collect()`.
- **`run005.py` / `script.py`** — thin run drivers: import `collect_dataset as cd`, override its globals, then `asyncio.run(cd.collect())`. Copy this pattern to launch a new numbered run rather than editing `collect_dataset.py` directly.
- **`rate.py`** — local Flask app (`http://localhost:8765`) for human-in-the-loop phenomenological rating of renders; writes `data/prime_ratings.csv` (training data for the prime-mapping weights `W`). Reads renders from `renders/` and concept metadata from `data/nhcs_run_*.csv`.
- **`build_gallery.py`** — regenerates `gallery.html` from PNGs in `renders/`.

Scripts force UTF-8 on stdout for Windows (cp1252) compatibility — preserve that when adding new ones.

## Architecture

Three decoupled layers communicate via an async message bus (`nhcs/bus.py`):

```
Layer 1 (Genesis Core)  --ConceptTarget-->  Layer 2 (TMFT)  --PhysicalRealization-->  Layer 3 (CRIM)
       ^                                                              ^                      |
       |______________________ IntegrationFeedback ___________________|__ RetargetRequest ____|
```

**Layer 1 — `nhcs/layer1_genesis/`**: Concept synthesis. RSE seeds/refines topological structures (hypergraphs with persistent homology invariants). AIAN penalizes human-like concepts. ICVP runs BFT consensus (>66% supermajority) before emitting to Layer 2.

**Layer 2 — `nhcs/layer2_tmft/`**: Physics simulation. Maps topological signatures to Hopfion field configurations via Hopf map (S3->R3). JAX-based LLG solver and Biot-Savart coil field computation. Q-tensor and Navier-Stokes solvers are placeholders.

**Layer 3 — `nhcs/layer3_crim/`**: Cognitive feedback loop. Renders Hopf fields via Open3D (headless), estimates Cognitive Load Index (CLI), runs PID controller targeting CLI=0.6 (flow state). Uses synthetic biometric subject for headless testing.

**Physics boundary**: Layer 2 -> Layer 3 is unidirectional. CRIM cannot modify physics solvers (allows future hardware swap).

**Orchestration**: `nhcs/orchestrator/runner.py` (`EndToEndRunner`) wires all layers. Entry point is `nhcs/orchestrator/digital_twin_demo.py`.

## Key Conventions

- **Message contracts**: All inter-layer messages are Pydantic v2 models in `nhcs/schemas.py`. Five bus topics: `concept_target`, `physical_realization`, `integration_feedback`, `retarget_request`, `icvp_vote`.
- **Config-driven**: YAML files in `configs/` control all hyperparameters. `default.yaml` is the primary config (layer hyperparameters, mode, bus backend); `colloid_fe3o4.yaml`, `coil_array_dodec12.yaml`, and `crim_pid.yaml` hold domain-specific physics/hardware parameters. Some values are duplicated across files by design — e.g. `layer2.max_field_mt` in `default.yaml` mirrors `rosensweig_threshold_mt` in `colloid_fe3o4.yaml`. Mode is `simulation` (default) or `hardware`. Note `layer2.twin.grid_size` is read directly by `DigitalTwin` from `default.yaml` (16 for dev speed, 64 for fidelity).
- **Bus singleton**: `nhcs.bus.get_bus()` returns the module-level MessageBus. Call `reset_bus()` between tests.
- **Hard guardrails**: Resonant stability regime is 15-40 Hz, hard-clamped in the `RetargetRequest` Pydantic validator. AIAN novelty threshold is 0.6. ICVP supermajority is >66.7%.

## Heavy Dependencies

These may need build tools or special environment setup:
- `gudhi`, `ripser`, `persim` — persistent homology (C++ extensions)
- `jax`/`jaxlib` — CPU fallback works; GPU optional
- `torch` + `geoopt` — manifold embeddings (Poincare ball)
- `open3d` — may need OpenGL stubs on headless servers
- `pylsl` — Lab Streaming Layer (only needed in hardware mode)