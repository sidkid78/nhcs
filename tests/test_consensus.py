"""
Tests: ICVP BFT consensus.
"""

import pytest
from nhcs.layer1_genesis.icvp.consensus import ConsensusProtocol
from nhcs.schemas import ICVPVote


def _make_vote(concept_id: str, approve: bool, et: float = 0.90, ap: float = 0.75) -> ICVPVote:
    return ICVPVote(
        concept_id=concept_id,
        validator_did=f"did:nhcs:test",
        approve=approve,
        et_score=et,
        ap_score=ap,
    )


class TestConsensusProtocol:
    def setup_method(self):
        self.proto = ConsensusProtocol(n_validators=5, supermajority=2/3)
        # Required = ceil(5 * 2/3) = ceil(3.33) = 4
        assert self.proto._required == 4

    def test_4_of_5_approve_passes(self):
        votes = [_make_vote("c1", True)] * 4 + [_make_vote("c1", False)]
        approved, _ = self.proto.tally(votes)
        assert approved is True

    def test_3_of_5_approve_fails(self):
        votes = [_make_vote("c1", True)] * 3 + [_make_vote("c1", False)] * 2
        approved, _ = self.proto.tally(votes)
        assert approved is False

    def test_unanimous_approval(self):
        votes = [_make_vote("c1", True)] * 5
        approved, summary = self.proto.tally(votes)
        assert approved is True
        assert summary["n_approve"] == 5

    def test_unanimous_rejection(self):
        votes = [_make_vote("c1", False)] * 5
        approved, _ = self.proto.tally(votes)
        assert approved is False

    def test_empty_votes_fails(self):
        approved, _ = self.proto.tally([])
        assert approved is False

    def test_summary_contains_required_fields(self):
        votes = [_make_vote("c1", True)] * 5
        _, summary = self.proto.tally(votes)
        for key in ("n_votes", "n_approve", "n_reject", "required", "approved", "mean_et", "mean_ap"):
            assert key in summary
