# NHCS — Next-Session Roadmap

_Written 2026-07-04, end of the controller-overhaul session. Read this before touching AIAN, `twin.py`, or the CRIM loop._

## Where things stand (done + verified this session)

- **Spectral controller** replaces the Beltrami optimiser. Curl-based complexity
  was measuring a boundary-mask artifact (curl B ≡ 0 in the current-free interior);
  replaced with the grid-convergent gradient-energy index
  `C = <||∇B||_F²>/<|B|²> · L²`, solved in closed form as a generalized Rayleigh
  quotient over the 12×12 pencil. Exact solves (~1e-11 %), ~150× faster, forms
  cached per grid size. Files: `coil_field.py`, `controller.py`, `twin.py`.
- **Achievable spectrum** (gs=12): `[0.002×3, 5.15–5.18×5, 14.45×3, 68.4×1]` —
  icosahedral symmetry multiplets. Structurally stable gs=12→32; only the top
  singlet drifts (68.4→~65 asymptotic), absorbed by reading anchors at runtime.
- **I_f remap** across the full spectrum via `target(I_f) = c_lo + (c_hi−c_lo)·I_f/(4+I_f)`.
  Concept separation improved from 0.96–0.99 cosine to 0.32–0.53 adjacent.
- **Controller grid decoupled** from render grid (`_CTRL_GRID_SIZE=12` fixed;
  anchors read from `controller.spectrum()`, not hardcoded) so concept→field
  mapping is reproducible across dev/fidelity settings.
- **Torus knot fix** in `topology_to_field.build_hopf_grid` — true T(p,q) on the
  Clifford torus (independent phases, `endpoint=False`); `crossing_to_torus_knot`
  uses the Murasugi relation and enforces gcd(p,q)=1. JS visualizers were already
  correct (they use THREE.TorusKnotGeometry).
- **Beam-search dedup** in `search.py` — dedupes by Betti signature, min-max
  normalises complexity vs diversity so `diversity_weight` is meaningful. Removed
  debug `logger.info(b)` log spam. Added "N unique signatures" instrumentation.
- **pid.py** `float(None)` crash fixed. **coil_field.py** chunked `field_at_batch`,
  `mask_outside=False`, `basis_field_grid()`, closed file handle.
- **Phenomenology logger** `nhcs_binaural_v2.html` rebuilt with hard session-lock
  and `field_map` version tags (`beltrami-v1` vs `spectral-v2`) so datasets can't
  be silently pooled across the remap.
- **AIAN semantic-head debias: TRIED AND REVERTED.** A per-dimension saturating
  variant reduced the β₀ bias but deflated aggregate novelty below the 0.6
  threshold → AIAN kept nothing. Calibration showed the head's saturated ~1.0
  output is load-bearing (other three heads avg ~0.56, below threshold). Reverted;
  bias caveat documented in the docstring. **Do not re-attempt in isolation.**

## The SDR collapse: ROOT CAUSE FOUND & CONFIRMED (2026-07-04, isolated harness)

Both runs show SDR nonzero ONLY for the three β₁=2 concepts (0.267–0.309);
everything β₁≥3 flatlines at exactly 0.000.

**The SDR collapse is a Layer-3 software artifact. It has NOTHING to do with the
field physics, the icosahedral spectrum, or the top eigenmode. The original
"symmetric top mode kills directional asymmetry" hypothesis was WRONG — tracing
the code and running an isolated harness falsified it BEFORE any code changed.
This is the measure-first discipline paying off: we nearly clamped c_hi to fix a
cause that does not exist.**

### Actual mechanism (traced through runner._run_crim_loop + prime_map + phen_space, harness-proven)

1. `_run_crim_loop` builds the two SDR inputs as:
   - `initial = mapper.map(spatial_3d, temporal, magnitude)`
   - `final   = mapper.map(spatial_3d, temporal, magnitude * iis)`
   Only the magnitude arg differs. `spatial_3d` and `temporal` are FROZEN — the
   field is never re-projected, the biometric trajectory never re-enters the
   semantics. `target_primes` is never passed to `semantic_distance_reduction`.

2. `PrimeMapper` bins magnitude via `tanh` into 3 bands: LO<0.3 (LITTLE/SMALL),
   MID 0.3–0.7 (SOME), HI>0.7 (MUCH/BIG/VERY). When `magnitude` and
   `magnitude*iis` fall in the SAME band, the identical prime SET fires; the only
   difference is a uniform weight scale, which cosine-normalisation erases.
   ⇒ SDR = 0 exactly (harness: 0.0003–0.0014 fp-noise, logs as 0.0000).

3. `magnitude = |mean(|raw|)|` from `phen_space.project_full`, and `spatial_3d`
   is normalised to a unit vector (structural intensity discarded). The surviving
   magnitude is small; for iis~0.5, `magnitude*iis` escapes the LO band only when
   magnitude > ~0.38. Most concepts sit below that ⇒ SDR=0. The β₁=2 concepts
   scored nonzero because their magnitude happened to sit near the tanh BAND
   BOUNDARY — not near any field/topology threshold.

Harness result: same-band pairs give identical prime sets and SDR~0; only
MID→LO band crossings produce SDR~0.18. Reproducible in full isolation from
RSE/ICVP/controller/PID.

### Consequence for the physics: c_hi CLAMP IS CANCELLED

DO NOT clamp c_hi to 14.45. The full icosahedral spectrum [0.002, 68.406] is
mathematically sound and safe to use. The clamp would have compressed the physics
range to "fix" a tanh-binning artifact in Layer 3 with no physical basis. The
spectral-v2 remap stays as-is.

## Two INDEPENDENT next-session threads (decoupled — the c_hi coupling was based on the wrong hypothesis)

### Thread A — SDR / CRIM loop (Layer 3). Three stacked defects, exact root cause in hand.

(a) **SDR is structurally broken.** It compares a field projection against the
    SAME projection with a scaled magnitude; never re-projects an evolved field,
    ignores its own `target_primes` argument. Measures a scalar band-crossing,
    not semantic drift toward a target. Rewrite: either project an actually-
    evolved field at loop end, or compare final primes against `target_primes`
    (the concept's intended NSM primes) as the docstring claims.

(b) **SyntheticSubject is concept-blind.** `SyntheticSubject.step` responds only
    to `iis`; no field/topology term enters HRV/GSR/pupil. Identical physiological
    distribution for [9,1,0] and [4,4,0]. In synthetic mode SDR cannot measure
    anything concept-specific until the subject is coupled to the concept (e.g.
    field magnitude/complexity modulates arousal), OR SDR should be reported as
    N/A-under-synthetic rather than a misleading 0.0000.

(c) **phen_space normalises away magnitude.** `spatial_3d` is unit-normalised,
    discarding the field's structural intensity — the richest signal — so the one
    varying channel feeding SDR is the uniform-scale magnitude, the worst choice.
    Consider preserving magnitude in the spatial channel, or feeding field
    variance (not just the mean tensor) into the projection.

Validate (a)+(b)+(c) TOGETHER: fixing SDR's comparison is pointless if the
subject feeding it is concept-blind, and both depend on phen_space surfacing real
per-concept variation.

### Thread B — Topological diversity (AIAN). Still real, now unlinked from physics.

RSE+AIAN starve the pipeline of β₁≥3 concepts (per-round unique-signature counts
drop to 1 in some rounds; mean β₁ stuck 1–4). The AIAN semantic head rewards
high-β₀ blobs. Fix requires recalibrating threshold AND head weights TOGETHER
(the isolated semantic-head edit failed this session — see above). Candidate:
lower threshold toward ~0.60 and/or `embed_heavy` head weights, with its own
keep-rate test before trusting it.

Either thread can go first. Thread A is better-scoped right now (root cause
confirmed). Neither touches Layer 2 — the physics engine is verified and closed.

## Guardrails carried forward (from CLAUDE.md)
- RSR frequency clamp 15–40 Hz (enforced in RetargetRequest validator). Note
  β=[9,1,0]'s raw 10.83 Hz clamps to 15 Hz — that concept's audio doesn't reflect
  its topology; flag it if it ever enters a listening session.
- AIAN novelty threshold 0.6; ICVP supermajority >66.7%.
- Audio/TPMM path is unchanged across the whole overhaul — verified `[7,3,0]`
  phenomenology session stays valid as a binaural data point.
