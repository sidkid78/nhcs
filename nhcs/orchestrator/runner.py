"""
End-to-end runner: wires all three layers via the message bus.

Usage::

    runner = EndToEndRunner()
    asyncio.run(runner.run(n_concepts=3))
"""

from __future__ import annotations

import asyncio
import logging

from nhcs.bus import MessageBus, get_bus
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
from nhcs.schemas import (
    ConceptTarget,
    IntegrationFeedback,
    MeritScores,
    TopologicalSignature,
)

logger = logging.getLogger(__name__)


class EndToEndRunner:
    """
    Wires all three layers into a closed loop.

    Parameters
    ----------
    n_validators : int
    n_crim_steps : int  (biometric feedback steps per concept)
    ledger_path  : str
    grid_size    : int  (voxels per axis for TMFT field grid)
    rse_n_seeds  : int  (number of seed complexes per RSE run)
    """

    def __init__(
        self,
        n_validators: int = 5,
        n_crim_steps: int = 50,
        ledger_path: str = ":memory:",
        rng_seed: int = 42,
        grid_size: int = 16,
        rse_n_seeds: int = 20,
    ) -> None:
        # Layer 1
        self.rse = RecursiveSynthesisEngine(
            n_seed_complexes=rse_n_seeds,
            rng_seed=rng_seed,
        )
        self.aian = AIAN()
        self.beam = DivergentBeamSearch(beam_width=3)
        self.merit = MeritEvaluator()
        self.validators = [ValidatorNode() for _ in range(n_validators)]
        self.consensus = ConsensusProtocol(n_validators=n_validators)
        self.ledger = GlobalKnowledgeLedger(ledger_path)
        self.slashing = SlashingDetector()

        # Layer 2
        self.twin = DigitalTwin(grid_size=grid_size)

        # Layer 3
        self.airlock = AbstractionCalibrationAirlock()
        self.biometrics = BiometricsLSL(synthetic=True)
        self.cli_est = CognitiveLoadIndex()
        self.phen = PhenomenologicalVectorSpace()
        self.mapper = PrimeMapper()
        self.renderer = HopfFieldRenderer(headless=True)

        self.n_crim_steps = n_crim_steps
        self.bus = get_bus()

    # ------------------------------------------------------------------
    # Layer 1: generate + validate a concept
    # ------------------------------------------------------------------

    def _generate_concept(self) -> ConceptTarget | None:
        candidates = self.rse.run()
        passed = self.aian.filter(candidates)
        if not passed:
            logger.warning("All candidates rejected by AIAN.")
            return None

        selected = self.beam.select(passed)
        if not selected:
            return None

        best = selected[0]
        novelty = getattr(best, "_novelty_score", 0.0)

        # Slashing check
        slash = self.slashing.detect(
            concept_id="pending",
            betti=best.invariant.betti,
        )
        if slash.tainted:
            logger.warning("Slashing: concept flagged as human-tainted. Skipping.")
            return None

        # ICVP votes
        import uuid
        concept_id = str(uuid.uuid4())
        votes = [v.evaluate(best, concept_id, novelty) for v in self.validators]
        approved, summary = self.consensus.tally(votes)
        if not approved:
            logger.info("Concept %s rejected by ICVP: %s", concept_id[:8], summary)
            return None

        # Commit to ledger
        merit_scores = self.merit.evaluate(best, novelty)
        self.ledger.commit(
            concept_id=concept_id,
            did="did:nhcs:orchestrator",
            betti=best.invariant.betti,
            merit_dict=merit_scores.model_dump(),
            votes_list=[v.model_dump(mode="json") for v in votes],
            consensus_dict=summary,
        )

        betti = best.invariant.betti
        sig = TopologicalSignature(
            betti=betti,
            euler_characteristic=best.invariant.euler_characteristic,
            dimension=best.invariant.dimension,
            persistence_entropy=best.invariant.persistence_entropy,
            complexity_score=best.invariant.complexity_score,
        )
        return ConceptTarget(
            concept_id=concept_id,
            signature=sig,
            merit=merit_scores,
            hopf_map_grid=[[0.0]] * 4,
        )

    # ------------------------------------------------------------------
    # Layer 3: closed-loop biometric integration
    # ------------------------------------------------------------------

    def _run_crim_loop(self, concept: ConceptTarget, realization) -> IntegrationFeedback:
        pid = ImmersionIntensityPID(
            concept_id=concept.concept_id,
            current_freq_hz=realization.target_frequency_hz,
        )

        field_tensors = realization.field_tensor_array()
        spatial_3d, temporal, magnitude = self.phen.project_full(field_tensors)
        initial_primes = [(r.prime, r.weight) for r in
                          self.mapper.map(spatial_3d, temporal, magnitude)]

        cli_series, iis_series = [], []
        hrv_series, gsr_series, pupil_series = [], [], []

        iis = 0.5
        for _ in range(self.n_crim_steps):
            sample = self.biometrics.read(iis=iis, dt=0.1)
            cli = self.cli_est.estimate(
                sample.hrv_rmssd_ms, sample.gsr_microsiemens, sample.pupil_diameter_mm
            )
            iis, retarget = pid.step(cli)
            if iis is None:
                iis = 0.5

            cli_series.append(cli)
            iis_series.append(iis)
            hrv_series.append(sample.hrv_rmssd_ms)
            gsr_series.append(sample.gsr_microsiemens)
            pupil_series.append(sample.pupil_diameter_mm)

        final_primes = [(r.prime, r.weight) for r in
                        self.mapper.map(spatial_3d, temporal, magnitude * iis)]
        bhi = biometric_homeostasis_index(hrv_series, gsr_series, pupil_series)
        sdr, sdr_conf = semantic_distance_reduction(initial_primes, final_primes)

        logger.debug(
            "CRIM: iis_final=%.3f  initial_primes=%s  final_primes=%s  SDR=%.4f",
            float(iis_series[-1]) if iis_series else 0.5,
            [p for p, _ in initial_primes[:3]],
            [p for p, _ in final_primes[:3]],
            sdr,
        )

        return IntegrationFeedback(
            concept_id=concept.concept_id,
            cli_series=cli_series,
            iis_series=iis_series,
            bhi=bhi,
            sdr=sdr,
            sdr_confidence=sdr_conf,
            synthetic_subject=True,
            n_integration_steps=self.n_crim_steps,
        )

    # ------------------------------------------------------------------
    # Public: run N concepts end-to-end
    # ------------------------------------------------------------------

    async def run(self, n_concepts: int = 1) -> list[IntegrationFeedback]:
        feedbacks = []
        attempts = 0
        max_attempts = n_concepts * 5

        while len(feedbacks) < n_concepts and attempts < max_attempts:
            attempts += 1

            # Layer 1
            concept = self._generate_concept()
            if concept is None:
                continue

            await self.bus.publish("concept_target", concept)

            # Layer 2
            realization = self.twin.step(concept)
            if not self.airlock.check_physical_integrity(realization):
                logger.warning("Airlock rejected realization for concept %s.", concept.concept_id[:8])
                continue

            render_result = self.renderer.render(realization)
            await self.bus.publish("physical_realization", realization)

            # Layer 3
            feedback = self._run_crim_loop(concept, realization)
            feedbacks.append(feedback)
            await self.bus.publish("integration_feedback", feedback)

            logger.info(
                "Concept %s complete: BHI=%.4f SDR=%.4f CLI_mean=%.4f",
                concept.concept_id[:8],
                feedback.bhi,
                feedback.sdr,
                sum(feedback.cli_series) / max(len(feedback.cli_series), 1),
            )

        return feedbacks
