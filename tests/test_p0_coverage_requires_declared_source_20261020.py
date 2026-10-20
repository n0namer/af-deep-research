"""An unowned source must not count as verified requirement coverage."""
from datetime import datetime, timezone

from reasoners.deep_research_ext.coverage import assess_candidate_coverage
from reasoners.deep_research_ext.evidence_ledger import EvidenceClaim, EvidenceLedger, EvidenceSource
from reasoners.deep_research_ext.task_contract import build_answer_contract


def sample_ledger(claim_source_id: int):
    source = EvidenceSource(
        source_id=10,
        title="RFC 9114",
        url="https://www.rfc-editor.org/info/rfc9114",
        content_hash="a" * 64,
        source_class="primary_doc",
        provenance_group="rfc-editor.org",
        retrieved_at=datetime.now(timezone.utc).isoformat(),
    )
    claim = EvidenceClaim(
        claim_id="A10-C1",
        text="RFC 9114 specifies HTTP/3",
        source_id=claim_source_id,
        requirement_ids=["R1"],
        status="verified",
        support_state="source_entailed",
        source_independence_group="rfc-editor.org",
    )
    return EvidenceLedger(
        sources=[source],
        claims=[claim],
        created_at=datetime.now(timezone.utc).isoformat(),
    )


def test_declared_source_counts_toward_verified_coverage():
    c = build_answer_contract("Which RFC specifies HTTP/3?", source_strictness="strict")
    state = assess_candidate_coverage(c, sample_ledger(10))
    assert state.verified_coverage_ratio == 1.0
    assert state.requirements[0].status == "verified"


def test_foreign_source_must_not_be_verified_despite_supported_claim_flag():
    c = build_answer_contract("Which RFC specifies HTTP/3?", source_strictness="strict")
    state = assess_candidate_coverage(c, sample_ledger(999))
    assert state.verified_coverage_ratio == 0.0
    assert state.requirements[0].status != "verified"
    assert state.requirements[0].independent_source_groups == 0
