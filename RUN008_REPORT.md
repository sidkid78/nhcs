# run008 — AIAN Parameter-Grid Sweep

**Date:** 2026-06-30
**Driver:** `run008.py` → `collect_dataset.collect()`
**Seed:** 42 (identical RSE candidate stream across all cells)
**Per cell:** `N_CONCEPTS=8`, `N_CRIM_STEPS=20`, `GRID_SIZE=8`
**Invariants:** real GUDHI 3.12.0 persistent homology (not the stub)
**Wall time:** ~55 min (strict cells exhaust all 64 attempts)

## Purpose

First experiment to exercise the two AIAN knobs made config-driven in the prior
session (`novelty_threshold`, `head_weights`). Crosses:

- `novelty_threshold ∈ {0.50, 0.60, 0.70}`
- `head_weights` (semantic, heuristic, aesthetic, embedding):
  - `baseline`    = `[0.15, 0.25, 0.20, 0.40]`
  - `embed_heavy` = `[0.10, 0.15, 0.15, 0.60]`
  - `balanced`    = `[0.25, 0.25, 0.25, 0.25]`
  - `shape_heavy` = `[0.15, 0.35, 0.35, 0.15]`

3 × 4 = 12 cells. Same seed across cells ⇒ only the AIAN gate/weights differ
(controlled comparison).

## Results

| thr | weights | collected | attempts | pass-rate | mean novelty | mean β₁ | mean cmplx | BHI | CLI | SDR |
|-----|---------|-----------|----------|-----------|--------------|---------|------------|-----|-----|-----|
| 0.50 | baseline    | 8/8 | 8  | 1.00 | 0.575 | 4.0 | 13.57 | 0.967 | 0.145 | 0.394 |
| 0.50 | embed_heavy | 8/8 | 8  | 1.00 | 0.639 | 4.0 | 13.57 | 0.967 | 0.145 | 0.394 |
| 0.50 | balanced    | 8/8 | 8  | 1.00 | 0.547 | 4.0 | 13.57 | 0.967 | 0.145 | 0.394 |
| 0.50 | shape_heavy | 8/8 | 9  | 0.89 | 0.522 | 2.6 | 12.24 | 0.967 | 0.145 | 0.312 |
| 0.60 | baseline    | 8/8 | 8  | 1.00 | 0.619 | 2.6 | 12.36 | 0.967 | 0.145 | 0.315 |
| 0.60 | embed_heavy | 8/8 | 8  | 1.00 | 0.639 | 4.0 | 13.57 | 0.967 | 0.145 | 0.394 |
| 0.60 | balanced    | 8/8 | 8  | 1.00 | 0.624 | 2.1 | 11.97 | 0.967 | 0.145 | 0.261 |
| 0.60 | shape_heavy | 3/8 | 64 | 0.05 | 0.635 | 1.3 | 10.46 | 0.950 | 0.130 | 0.110 |
| 0.70 | baseline    | 2/8 | 64 | 0.03 | 0.707 | 1.5 | 10.97 | 0.938 | 0.119 | 0.163 |
| 0.70 | embed_heavy | 3/8 | 64 | 0.05 | 0.722 | 1.3 | 10.46 | 0.950 | 0.130 | 0.110 |
| 0.70 | balanced    | 2/8 | 64 | 0.03 | 0.715 | 1.5 | 10.97 | 0.938 | 0.119 | 0.163 |
| 0.70 | shape_heavy | 0/8 | 64 | 0.00 | —     | —   | —     | —     | —     | —     |

Per-cell rows: `data/nhcs_run_008_t{thr}_{weights}.csv` (+ `.db` ledgers).
Aggregate: `data/nhcs_run_008_summary.csv`.

## Findings

1. **`novelty_threshold` is the operative control — and it's a cliff, not a ramp.**
   Pass-rate holds at ~1.0 through 0.60, then collapses to 0.03–0.05 at 0.70 (0/8
   for shape_heavy). The candidate novelty distribution is densely packed just
   below ~0.66; above it the pipeline starves, burning all 64 attempts to scrape
   2–3 concepts. **Usable band ≈ 0.55–0.65; above ~0.66 is impractical.**

2. **`head_weights` only bites near the gate boundary.** At thr=0.50,
   baseline/embed_heavy/balanced produced *identical* downstream metrics
   (β₁=4, BHI=0.967, SDR=0.394) — only recorded novelty differs, because when
   everything passes, all weightings select the same first 8 concepts. Weights
   only change *which* concepts survive once the threshold is actually filtering.
   (Also a clean determinism check on seed 42.)

3. **`shape_heavy` is the strictest weighting; `embed_heavy` the most permissive.**
   shape_heavy (0.70 on geometry heads, 0.15 on embedding) is the only config to
   lose a concept at 0.50, the first to collapse at 0.60, and the sole 0/8.
   embed_heavy yields the highest novelty and never starves until 0.70. Cause:
   the embedding head scores high (~0.6–0.7); down-weighting it drags the
   aggregate under the gate.

4. **Selection bias in topology.** As the gate tightens, surviving concepts have
   *lower* β₁ (4 → ~1.3) and lower complexity (13.6 → 10.5). High-novelty
   survivors are geometrically *sparser* — the embedding/semantic heads are not
   rewarding raw loop count.

5. **Downstream loop is independent of AIAN config**, as architecturally
   expected (Layer 2→3 boundary). BHI 0.94–0.97, CLI pinned 0.12–0.15 (far below
   the 0.6 flow target, consistent with prior runs). SDR tracks the gate only via
   which concepts pass.

## Recommendations

- Treat `novelty_threshold ≈ 0.60` as the practical ceiling for production runs.
- To raise novelty *without* starving the pipeline, increase the **embedding
  weight** rather than the threshold.
- Use `shape_heavy` as a deliberate high-selectivity knob when aggressive
  rejection is desired.

## Caveats

- Strict cells (thr=0.70) collected only 2–3 concepts; their per-cell means are
  small-sample and noisy.
- Cross-threshold topology comparison mixes sub-populations: thr=0.50 cells take
  the first 8 candidates unfiltered, while thr=0.70 cells keep only the 2–3
  rarest high-novelty candidates from 64 attempts.
- `max_attempts = N_CONCEPTS * 8 = 64` capped the strict cells; a higher cap
  would collect more but at steep compute cost.
