"""Native final-document fact/source/citation ownership checks (no mock search)."""
from __future__ import annotations

import asyncio

import pytest

from doc_generation_pipeline import AIAssessment, AIAssessmentList
from reasoners.deep_research_ext.final_verifier import (
    DraftClaim,
    DraftClaimList,
    verify_final_document,
)

SOURCE_URL = "https://www.rfc-editor.org/rfc/rfc9114"


def assess(*, assessment_source_id: int | None, fact_id: str = "D1:S1"):
    async def extractor(**kwargs):
        return DraftClaimList(claims=[
            DraftClaim(claim_id="D1", text="RFC 9114 defines HTTP/3.", citation_ids=[1]),
        ])

    async def adjudicator(facts, policy, **kwargs):
        assert len(facts) == 1
        assert facts[0].source_id == 10
        assert facts[0].fact_id == "D1:S1"
        return AIAssessmentList(assessments=[AIAssessment(
            fact_id=fact_id,
            source_id=assessment_source_id,
            is_allowed=True,
            is_source_supported=True,
            is_verified=True,
            disagreement_score=0.0,
        )])

    document = {
        "document_title": "HTTP/3",
        "executive_summary": "RFC 9114 defines HTTP/3. [1]",
        "sections": [],
        "source_notes": [{"citation_id": 1, "title": "RFC 9114", "url": SOURCE_URL}],
    }
    research = {
        "source_articles": [{
            "id": 10, "title": "RFC 9114", "url": SOURCE_URL,
            "content": "RFC 9114: HTTP/3. HTTP/3 uses QUIC as its transport.",
        }],
    }
    return asyncio.run(verify_final_document(
        document_package=document,
        research_package=research,
        source_strictness="strict",
        ai_call=None,
        claim_extractor=extractor,
        adjudicator=adjudicator,
    ))


def test_exact_fact_and_source_identity_is_accepted():
    state = assess(assessment_source_id=10)
    assert state.passed is True
    assert state.supported_claim_count == 1


@pytest.mark.parametrize("wrong_id", [None, 1, 999])
def test_missing_or_foreign_source_identity_fails_closed(wrong_id):
    state = assess(assessment_source_id=wrong_id)
    assert state.passed is False
    assert state.supported_claim_count == 0
    assert state.unsupported_claims[0].reason == "cited_evidence_does_not_entail_claim"


def test_right_source_but_foreign_fact_identity_is_rejected():
    state = assess(assessment_source_id=10, fact_id="FOREIGN:S1")
    assert state.passed is False
    assert state.supported_claim_count == 0
