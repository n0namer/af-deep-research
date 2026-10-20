"""P0 strict evidence-only publication: only exact declared source-owned claims may appear."""
from datetime import datetime, timezone

import pytest

from reasoners.deep_research_ext.coverage import CoverageState, RequirementCoverage
from reasoners.deep_research_ext.evidence_ledger import EvidenceClaim, EvidenceLedger, EvidenceSource
from reasoners.deep_research_ext.synthesis_guard import build_evidence_only_gap_response
from reasoners.deep_research_ext.task_contract import build_answer_contract


def response_with_claim(*, source_id: int, support_state: str = "source_entailed", status: str = "verified"):
    contract = build_answer_contract("Which RFC specifies HTTP/3?", source_strictness="strict")
    source = EvidenceSource(
        source_id=10, title="IETF RFC 9114",
        url="https://www.rfc-editor.org/info/rfc9114",
        content_hash="a" * 64, source_class="primary_doc",
        provenance_group="rfc-editor.org",
        retrieved_at=datetime.now(timezone.utc).isoformat(),
    )
    claim = EvidenceClaim(
        claim_id="A10-C1", text="RFC 9114 defines HTTP/3.",
        source_id=source_id, requirement_ids=["R1"],
        status=status, support_state=support_state,
    )
    ledger = EvidenceLedger(
        sources=[source], claims=[claim],
        created_at=datetime.now(timezone.utc).isoformat(),
    )
    # Deliberately provide a stale/overconfident coverage snapshot. The
    # report should not promote such a claim merely because coverage says 1.
    coverage = CoverageState(
        requirements=[RequirementCoverage(requirement_id="R1", status="verified")],
        verified_coverage_ratio=1.0,
        candidate_coverage_ratio=1.0,
    )
    return build_evidence_only_gap_response(
        contract=contract, ledger=ledger, coverage=coverage,
        metadata={"verified_research_extension": {}},
    )


def test_matching_source_and_entailed_fact_passes():
    report = response_with_claim(source_id=10)
    assert report.mode == "verified_evidence_only"
    assert "RFC 9114 defines HTTP/3" in report.research_package["sections"][0]["content"]
    assert len(report.research_package["source_notes"]) == 1


@pytest.mark.parametrize(("source_id", "support_state", "status"), [
    (999, "source_entailed", "verified"),
    (10, "candidate_extracted", "verified"),
    (10, "source_entailed", "unverified"),
])
def test_unbound_or_unverified_claim_fails_closed(source_id, support_state, status):
    report = response_with_claim(source_id=source_id, support_state=support_state, status=status)
    assert report.mode == "verified_partial"
    assert "RFC 9114 defines HTTP/3" not in report.research_package["sections"][0]["content"]
    assert not report.research_package["source_notes"]
    assert report.metadata["verified_research_extension"]["delivery_verification"]["passed"] is False
