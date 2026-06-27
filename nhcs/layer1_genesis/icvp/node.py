"""
ICVP Validator Node — Proof-of-Utility sandbox.

Each node independently evaluates a concept and emits a signed vote.
"""

from __future__ import annotations

import hashlib
import logging
import uuid

from nhcs.layer1_genesis.merit import MeritEvaluator
from nhcs.layer1_genesis.rse import CandidateConcept
from nhcs.schemas import ICVPVote, MeritScores

logger = logging.getLogger(__name__)


class ValidatorNode:
    """
    A single ICVP validator node.

    Parameters
    ----------
    did : str
        Decentralised identifier for this node.
    et_threshold : float
        Minimum epistemic truth required for approval.
    ap_threshold : float
        Minimum algorithmic parsimony required for approval.
    noise_std : float
        Simulated measurement noise on merit scores (models disagreement).
    """

    def __init__(
        self,
        did: str | None = None,
        et_threshold: float = 0.50,
        ap_threshold: float = 0.00,
        noise_std: float = 0.03,
    ) -> None:
        self.did = did or f"did:nhcs:{uuid.uuid4().hex[:12]}"
        self.et_threshold = et_threshold
        self.ap_threshold = ap_threshold
        self.noise_std = noise_std
        self._evaluator = MeritEvaluator()

    def evaluate(
        self,
        concept: CandidateConcept,
        concept_id: str,
        novelty_score: float = 0.0,
    ) -> ICVPVote:
        """
        Run the PoU sandbox and return a signed vote.
        """
        import numpy as np

        merit = self._evaluator.evaluate(concept, novelty_score)

        # Add per-node noise to model independent assessment
        rng = np.random.default_rng(abs(hash(self.did + concept_id)) % (2**32))
        et = float(np.clip(merit.epistemic_truth + rng.normal(0, self.noise_std), 0, 1))
        ap = float(np.clip(merit.algorithmic_parsimony + rng.normal(0, self.noise_std), 0, 1))

        approve = (et >= self.et_threshold) and (ap >= self.ap_threshold)

        # Stub signature — SHA256(did + concept_id + vote)
        sig_data = f"{self.did}:{concept_id}:{approve}:{et:.4f}:{ap:.4f}"
        signature = hashlib.sha256(sig_data.encode()).hexdigest()[:16]

        vote = ICVPVote(
            concept_id=concept_id,
            validator_did=self.did,
            approve=approve,
            et_score=et,
            ap_score=ap,
            rationale=f"Et={et:.3f}, Ap={ap:.3f}",
            signature=signature,
        )
        logger.debug("Node %s voted %s for concept %s.", self.did, approve, concept_id)
        return vote
