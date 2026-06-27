---
skill: analyze_codebase
target: .
generated: 2026-05-03 19:53:25
tool_calls: 14
---

# Codebase Analysis: nhcs (Non-Human Conceptual Synthesis)

## TL;DR
NHCS is a three-layer research prototype for generating and communicating non-anthropocentric concepts. It uses a decoupled async message bus to coordinate concept synthesis (topological), physics simulation (Hopfion fields), and cognitive feedback (biometrics/rendering).

## Project Type & Entry Points
- Type: Research Prototype / Agent / Orchestrator
- Entry: `nhcs/orchestrator/digital_twin_demo.py` → `main`
- Run: `nhcs-demo` or `python -m nhcs.orchestrator.digital_twin_demo`

## Architecture
- `nhcs/bus.py` — Async message bus for inter-layer communication.
- `nhcs/schemas.py` — Pydantic v2 models for data contracts.
- `nhcs/layer1_genesis/` — Concept synthesis using topological invariants and consensus mechanisms.
- `nhcs/layer2_tmft/` — Topological Magnetic Field Theory simulation (JAX-based).
- `nhcs/layer3_crim/` — Cognitive feedback loop using biometrics and rendering.
- `nhcs/orchestrator/` — Wires the layers together into a closed loop.

## Tech Stack
| Layer     | Technology   | Version | Notes |
|-----------|-------------|---------|-------|
| Runtime   | Python      | >=3.11  | Fully async |
| Topology  | GUDHI, Ripser | -       | Layer 1 |
| Physics   | JAX, SciPy   | -       | Layer 2 |
| Rendering | Open3D      | -       | Layer 3 |
| ML/Embed  | Torch, sentence-transformers | - | Layer 1 |
| IO/Bus    | Pydantic v2, PyZMQ | - | Infrastructure |

## Dependencies (Notable)
- ✅ `jax` — Used for high-performance physics simulation in Layer 2.
- ✅ `gudhi` — Core topological library for concept generation.
- ✅ `sentence-transformers` — Used for concept embedding/novelty scoring.
- ✅ `open3d` — Used for rendering physical realizations.

## Code Quality Signals
- ✅ Well-structured with clear layer decoupling and message contracts.
- ✅ Extensively documented in `CLAUDE.md`.
- ⚠️  Placeholder logic (e.g., `_record` in `bus.py`, `[[0.0]] * 4` hopf_map_grid in `runner.py`).
- ⚠️  One TODO found in `nhcs/layer3_crim/biometrics_lsl.py` regarding hardware mode.

## Data & State Flow
1. **Layer 1 (Genesis)**: Seeds and refines topological structures (hypergraphs). AIAN penalizes human-like patterns. ICVP ensures consensus (>66%) and emits a `ConceptTarget`.
2. **Layer 2 (TMFT)**: Receives `ConceptTarget`. Maps topological signatures to Hopfion field configurations. Solves physics (LLG) and emits `PhysicalRealization`.
3. **Layer 3 (CRIM)**: Receives `PhysicalRealization`. Renders field via Open3D. Simulates/reads biometrics (hrv, gsr, pupil). Estimates Cognitive Load (CLI). Runs PID to adjust intensity and emits `IntegrationFeedback` back to Layer 1.

## Gaps & Recommendations
Prioritized — highest impact first:
1. **Complete Hardware Mode** — `nhcs/layer3_crim/biometrics_lsl.py` — Implement LSL inlet pulling for real biometric data.
2. **Expand Hopf Map sampled grid** — `nhcs/orchestrator/runner.py` — Replace `[[0.0]] * 4` placeholder with actual sampled grid if required by L2 solvers.
3. **Implement Q-tensor and Navier-Stokes** — `nhcs/layer2_tmft/` — Fill placeholders mentioned in `CLAUDE.md` for more complete physics simulation.

## Files Read
- `pyproject.toml`
- `CLAUDE.md`
- `nhcs/bus.py`
- `nhcs/schemas.py`
- `nhcs/orchestrator/runner.py`
