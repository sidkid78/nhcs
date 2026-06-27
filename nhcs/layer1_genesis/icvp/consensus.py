"""
ICVP Consensus — BFT supermajority voting.

Requires >= 2/3 of validator nodes to approve a concept before it
is committed to the ledger and emitted as a ConceptTarget.
"""

from __future__ import annotations

import logging
import math

from nhcs.schemas import ICVPVote

logger = logging.getLogger(__name__)


class ConsensusProtocol:
    """
    Simple in-process BFT: collect votes, check supermajority.

    Parameters
    ----------
    n_validators : int
    supermajority : float  (default 2/3)
    """

    def __init__(self, n_validators: int = 5, supermajority: float = 2 / 3) -> None:
        self.n_validators = n_validators
        self.supermajority = supermajority
        self._required = math.ceil(n_validators * supermajority)

    def tally(self, votes: list[ICVPVote]) -> tuple[bool, dict]:
        """
        Tally votes for a single concept.

        Returns
        -------
        (approved, summary_dict)
        """
        n = len(votes)
        approvals = sum(1 for v in votes if v.approve)
        approved = approvals >= self._required

        mean_et = sum(v.et_score for v in votes) / max(n, 1)
        mean_ap = sum(v.ap_score for v in votes) / max(n, 1)

        summary = {
            "n_votes": n,
            "n_approve": approvals,
            "n_reject": n - approvals,
            "required": self._required,
            "approved": approved,
            "mean_et": round(mean_et, 4),
            "mean_ap": round(mean_ap, 4),
        }
        logger.info(
            "Consensus: %d/%d approved (need %d) -> %s",
            approvals, n, self._required, "PASS" if approved else "FAIL",
        )
        return approved, summary
