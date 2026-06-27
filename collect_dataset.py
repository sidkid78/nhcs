"""
NHCS Dataset Collection Run

Instruments the full pipeline to capture per-concept:
  - Betti profile (b0, b1, b2)
  - Topological complexity score
  - AIAN novelty score (per head + aggregate)
  - Physical parameters (freq, wavelength, charge_error, mean_B)
  - NSM prime activations (top-5 with weights)
  - Biometric outcomes (BHI, CLI_mean, CLI_std, IIS_final)
  - SDR + confidence
"""

from __future__ import annotations

import asyncio
import csv
import logging
import os
import sys
import time
from pathlib import Path

# Force UTF-8 on stdout so Unicode log chars don't crash on Windows cp1252
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Silence verbose third-party loggers
for _lg in ("httpx", "huggingface_hub", "sentence_transformers"):
    logging.getLogger(_lg).setLevel(logging.WARNING)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("nhcs.collect")

import numpy as np

from nhcs.bus import reset_bus
from nhcs.layer1_genesis.aian import AIAN
from nhcs.layer1_genesis.icvp.consensus import ConsensusProtocol
from nhcs.layer1_genesis.icvp.ledger import GlobalKnowledgeLedger
from nhcs.layer1_genesis.icvp.node import ValidatorNode
from nhcs.layer1_genesis.icvp.slashing import SlashingDetector
from nhcs.layer1_genesis.merit import MeritEvaluator
from nhcs.layer1_genesis.rse import RecursiveSynthesisEngine
from nhcs.layer1_genesis.search import DivergentBeamSearch
from nhcs.layer2_tmft.twin import DigitalTwin
from nhcs.layer3_crim.airlock import AbstractionCalibrationAirlock
from nhcs.layer3_crim.biometrics_lsl import BiometricsLSL
from nhcs.layer3_crim.cli import CognitiveLoadIndex
from nhcs.layer3_crim.metrics import biometric_homeostasis_index, semantic_distance_reduction
from nhcs.layer3_crim.phen_space import PhenomenologicalVectorSpace
from nhcs.layer3_crim.pid import ImmersionIntensityPID
from nhcs.layer3_crim.prime_map import PrimeMapper
from nhcs.layer3_crim.render import HopfFieldRenderer
from nhcs.schemas import ConceptTarget, TopologicalSignature

N_CONCEPTS   = 10
N_VALIDATORS = 5
N_CRIM_STEPS = 20
GRID_SIZE    = 8
RSE_N_SEEDS  = 20
RNG_SEED     = 42
# AIAN discriminator hyperparameters — mirrors the `layer1.aian` block in
# configs/default.yaml. Override per run from a driver, e.g.:
#   cd.AIAN_CONFIG = {"novelty_threshold": 0.5, "head_weights": [0.4, 0.1, 0.1, 0.4]}
AIAN_CONFIG  = {
    "novelty_threshold": 0.6,
    "head_weights": [0.15, 0.25, 0.20, 0.40],  # [semantic, heuristic, aesthetic, embedding]
}
OUT_DIR      = Path("data")
OUT_CSV      = OUT_DIR / "nhcs_run_001.csv"
LEDGER_PATH  = str(OUT_DIR / "nhcs_run_001.db")

CSV_FIELDS = [
    "run_idx", "concept_id",
    "beta0", "beta1", "beta2", "euler", "topo_dimension",
    "persistence_entropy", "complexity_score",
    "novelty_semantic", "novelty_heuristic", "novelty_aesthetic", "novelty_embedding",
    "novelty_aggregate", "aian_pass",
    "icvp_n_approve", "icvp_required", "icvp_mean_et", "icvp_mean_ap",
    "target_freq_hz", "target_wl_nm", "torus_p", "torus_q",
    "charge_error_pct", "mean_b_mt",
    "prime1", "w1", "prime2", "w2", "prime3", "w3", "prime4", "w4", "prime5", "w5",
    "cli_mean", "cli_std", "cli_min", "cli_max",
    "iis_initial", "iis_final",
    "bhi",
    "sdr", "sdr_confidence",
    "wall_time_s",
]


async def collect():
    OUT_DIR.mkdir(exist_ok=True)
    reset_bus()

    logger.info("Initialising pipeline components...")
    rse        = RecursiveSynthesisEngine(n_seed_complexes=RSE_N_SEEDS, rng_seed=RNG_SEED)
    _aian_kwargs = {
        k: v for k, v in (AIAN_CONFIG or {}).items()
        if k in ("novelty_threshold", "encoder_model", "head_weights")
    }
    aian       = AIAN(**_aian_kwargs)
    beam       = DivergentBeamSearch(beam_width=3)
    merit      = MeritEvaluator()
    slash      = SlashingDetector()
    validators = [ValidatorNode() for _ in range(N_VALIDATORS)]
    consensus  = ConsensusProtocol(n_validators=N_VALIDATORS)
    ledger     = GlobalKnowledgeLedger(LEDGER_PATH)
    twin       = DigitalTwin(grid_size=GRID_SIZE)
    airlock    = AbstractionCalibrationAirlock()
    biometrics = BiometricsLSL(synthetic=True)
    cli_est    = CognitiveLoadIndex()
    phen       = PhenomenologicalVectorSpace()
    mapper     = PrimeMapper()
    renderer   = HopfFieldRenderer(headless=True)

    rows = []
    run_idx = 0
    attempts = 0
    max_attempts = N_CONCEPTS * 8

    logger.info("Starting collection run - target: %d concepts", N_CONCEPTS)

    while run_idx < N_CONCEPTS and attempts < max_attempts:
        attempts += 1
        t0 = time.perf_counter()
        row = {"run_idx": run_idx + 1}

        # Layer 1: RSE -> AIAN -> ICVP
        candidates = rse.run()
        passed     = aian.filter(candidates)

        if not passed:
            logger.warning("Attempt %d: all candidates rejected by AIAN", attempts)
            continue

        selected = beam.select(passed)
        if not selected:
            continue
        best    = selected[0]
        novelty = getattr(best, "_novelty_score", 0.0)

        inv = best.invariant
        b   = (inv.betti + [0, 0, 0])[:3]
        row["beta0"]              = b[0]
        row["beta1"]              = b[1]
        row["beta2"]              = b[2]
        row["euler"]              = inv.euler_characteristic
        row["topo_dimension"]     = inv.dimension
        row["persistence_entropy"]= round(inv.persistence_entropy, 5)
        row["complexity_score"]   = round(inv.complexity_score, 5)

        s1 = aian._semantic_head(inv.betti, inv.complexity_score)
        s2 = aian._heuristic_head(best.point_cloud)
        s3 = aian._aesthetic_head(best.point_cloud)
        s4 = aian._embedding_head(inv.betti, inv.euler_characteristic)
        row["novelty_semantic"]   = round(s1, 4)
        row["novelty_heuristic"]  = round(s2, 4)
        row["novelty_aesthetic"]  = round(s3, 4)
        row["novelty_embedding"]  = round(s4, 4)
        row["novelty_aggregate"]  = round(novelty, 4)
        row["aian_pass"]          = 1

        s = slash.detect(concept_id="pending", betti=inv.betti)
        if s.tainted:
            logger.warning("Concept slashed. Skipping.")
            continue

        import uuid
        concept_id = str(uuid.uuid4())
        votes      = [v.evaluate(best, concept_id, novelty) for v in validators]
        approved, summary = consensus.tally(votes)
        row["icvp_n_approve"] = summary.get("n_approve", 0)
        row["icvp_required"]  = summary.get("required", 0)
        row["icvp_mean_et"]   = round(summary.get("mean_et", 0), 4)
        row["icvp_mean_ap"]   = round(summary.get("mean_ap", 0), 4)

        if not approved:
            logger.info("Attempt %d: ICVP rejected concept", attempts)
            continue

        merit_scores = merit.evaluate(best, novelty)
        ledger.commit(
            concept_id=concept_id,
            did="did:nhcs:collect",
            betti=inv.betti,
            merit_dict=merit_scores.model_dump(),
            votes_list=[v.model_dump(mode="json") for v in votes],
            consensus_dict=summary,
        )
        row["concept_id"] = concept_id[:8]

        sig = TopologicalSignature(
            betti=inv.betti,
            euler_characteristic=inv.euler_characteristic,
            dimension=inv.dimension,
            persistence_entropy=inv.persistence_entropy,
            complexity_score=inv.complexity_score,
        )
        concept = ConceptTarget(
            concept_id=concept_id,
            signature=sig,
            merit=merit_scores,
            hopf_map_grid=[[0.0]] * 4,
        )

        # Layer 2: TMFT
        realization = twin.step(concept)
        if not airlock.check_physical_integrity(realization):
            logger.warning("Attempt %d: airlock rejected realization", attempts)
            continue

        renderer.render(realization)
        row["target_freq_hz"]  = round(realization.target_frequency_hz, 3)
        row["target_wl_nm"]    = round(realization.target_wavelength_nm, 2)
        row["torus_p"]         = b[0]
        row["torus_q"]         = b[1]
        row["charge_error_pct"]= round(realization.charge_error_pct, 2)
        row["mean_b_mt"]       = round(realization.mean_b_field_mt, 4)

        # Initial prime activation
        field_tensors = realization.field_tensor_array()
        spatial_3d, temporal, magnitude = phen.project_full(field_tensors)
        initial_primes = mapper.map(spatial_3d, temporal, magnitude)

        for k in range(5):
            if k < len(initial_primes):
                row[f"prime{k+1}"] = initial_primes[k].prime
                row[f"w{k+1}"]     = round(initial_primes[k].weight, 4)
            else:
                row[f"prime{k+1}"] = ""
                row[f"w{k+1}"]     = 0.0

        # Layer 3: CRIM loop
        pid = ImmersionIntensityPID(
            concept_id=concept_id,
            current_freq_hz=realization.target_frequency_hz,
        )
        cli_series, iis_series             = [], []
        hrv_series, gsr_series, pupil_series = [], [], []
        iis = 0.5
        row["iis_initial"] = iis

        for _ in range(N_CRIM_STEPS):
            sample = biometrics.read(iis=iis, dt=0.1)
            cli    = cli_est.estimate(
                sample.hrv_rmssd_ms, sample.gsr_microsiemens, sample.pupil_diameter_mm
            )
            iis, _ = pid.step(cli)
            if iis is None:
                iis = 0.5
            cli_series.append(cli)
            iis_series.append(iis)
            hrv_series.append(sample.hrv_rmssd_ms)
            gsr_series.append(sample.gsr_microsiemens)
            pupil_series.append(sample.pupil_diameter_mm)

        cli_arr = np.array(cli_series)
        row["cli_mean"]  = round(float(cli_arr.mean()), 4)
        row["cli_std"]   = round(float(cli_arr.std()),  4)
        row["cli_min"]   = round(float(cli_arr.min()),  4)
        row["cli_max"]   = round(float(cli_arr.max()),  4)
        row["iis_final"] = round(float(iis_series[-1]), 4)
        row["bhi"]       = round(
            biometric_homeostasis_index(hrv_series, gsr_series, pupil_series), 4
        )

        final_primes = mapper.map(spatial_3d, temporal, magnitude * iis)
        sdr, sdr_conf = semantic_distance_reduction(
            [(r.prime, r.weight) for r in initial_primes],
            [(r.prime, r.weight) for r in final_primes],
        )
        row["sdr"]            = round(sdr, 6)
        row["sdr_confidence"] = round(sdr_conf, 4)
        row["wall_time_s"]    = round(time.perf_counter() - t0, 2)

        rows.append(row)
        run_idx += 1
        logger.info(
            "[%2d/%d] concept=%s  b=[%d,%d,%d]  novelty=%.3f  "
            "freq=%.1fHz  BHI=%.3f  CLI=%.3f  SDR=%.4f  (%.1fs)",
            run_idx, N_CONCEPTS, row["concept_id"],
            b[0], b[1], b[2], novelty,
            row["target_freq_hz"], row["bhi"],
            row["cli_mean"], sdr, row["wall_time_s"],
        )

    # Write CSV
    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    logger.info("")
    logger.info("=== COLLECTION COMPLETE ===")
    logger.info("Concepts collected : %d/%d", len(rows), N_CONCEPTS)
    logger.info("Total attempts     : %d", attempts)
    logger.info("Ledger size        : %d", len(ledger))
    logger.info("Output             : %s", OUT_CSV)
    logger.info("=" * 50)

    if rows:
        import statistics
        from collections import Counter
        b1s    = [r["beta1"] for r in rows]
        novs   = [r["novelty_aggregate"] for r in rows]
        clis   = [r["cli_mean"] for r in rows]
        bhis   = [r["bhi"] for r in rows]
        primes = [r["prime1"] for r in rows if r.get("prime1")]
        sdrs   = [r["sdr"] for r in rows]

        logger.info("")
        logger.info("TOPOLOGY  beta1: %d-%d (mean %.1f)", min(b1s), max(b1s), statistics.mean(b1s))
        logger.info("NOVELTY   aggregate: %.3f-%.3f (mean %.3f)",
                    min(novs), max(novs), statistics.mean(novs))
        logger.info("SDR       range: %.4f-%.4f (mean %.4f)",
                    min(sdrs), max(sdrs), statistics.mean(sdrs))
        logger.info("BHI       range: %.3f-%.3f", min(bhis), max(bhis))
        logger.info("CLI mean  range: %.3f-%.3f", min(clis), max(clis))
        logger.info("")
        logger.info("PRIME1 distribution:")
        for prime, count in Counter(primes).most_common(6):
            logger.info("  %-22s %d/%d", prime, count, len(rows))


if __name__ == "__main__":
    asyncio.run(collect())
