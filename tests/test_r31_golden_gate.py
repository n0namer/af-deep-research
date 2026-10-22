"""R31 six-domain golden-answer and strict source-grounding gate.

This test is intentionally isolated: it exercises current production verifier and
provenance contracts without changing product code or external task state.
"""
from __future__ import annotations

import asyncio
import hashlib
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
EXT = ROOT / "reasoners" / "deep_research_ext"
if str(EXT) not in sys.path:
    sys.path.insert(0, str(EXT))

from final_verifier import (  # noqa: E402
    DraftClaim,
    DraftClaimList,
    verify_final_document,
)
from reasoners.deep_research_ext.verified_pipeline import (  # noqa: E402
    build_grounded_verified_report,
    source_file_sha256,
)


DOMAINS = ("research", "engineering", "security", "operations", "policy", "economics")
SOURCE_URLS = {index: f"https://example.org/{domain}" for index, domain in enumerate(DOMAINS, 1)}
ARTICLES = [
    {"id": index, "url": SOURCE_URLS[index], "content": f"Primary source for {domain}."}
    for index, domain in enumerate(DOMAINS, 1)
]


def _document(citation_ids):
    return {
        "executive_summary": "Six-domain source-grounded golden answer.",
        "source_notes": [
            {"citation_id": citation_id, "url": SOURCE_URLS.get(citation_id, "https://missing.example")}
            for citation_id in citation_ids
        ],
    }


def _research(articles=None):
    return {"source_articles": ARTICLES if articles is None else articles}


async def _six_domain_extractor(**kwargs):
    return DraftClaimList(
        claims=[
            DraftClaim(
                claim_id=f"D{index}",
                text=f"Grounded answer for {domain}.",
                citation_ids=[index],
            )
            for index, domain in enumerate(DOMAINS, 1)
        ]
    )


async def _supported_adjudicator(candidates, *args, **kwargs):
    return SimpleNamespace(
        assessments=[
            SimpleNamespace(
                fact_id=candidate.fact_id,
                is_allowed=True,
                is_source_supported=True,
            )
            for candidate in candidates
        ]
    )


@pytest.mark.asyncio
async def test_six_domain_golden_answer_is_source_grounded_and_versioned():
    state = await verify_final_document(
        document_package=_document(range(1, 7)),
        research_package=_research(),
        source_strictness="strict",
        ai_call=None,
        claim_extractor=_six_domain_extractor,
        adjudicator=_supported_adjudicator,
    )
    assert state.passed is True
    assert state.material_claim_count == 6
    assert state.supported_claim_count == 6
    assert state.unsupported_claims == []

    source_path = EXT / "verified_pipeline.py"
    digest = source_file_sha256(source_path)
    report = build_grounded_verified_report(
        report_id="r31-six-domain-golden",
        query="six-domain source-grounded answer",
        source_revision=digest,
        source_owner="r31",
        source_file_sha256=digest,
        facts=[
            {
                "fact_id": f"domain-{domain}",
                "source_id": f"source-{domain}",
                "source_sha256": digest,
            }
            for domain in DOMAINS
        ],
        payload={"domains": list(DOMAINS), "strictness": "strict"},
    )
    assert report.dto_version == "r10"
    assert report.source_ids == tuple(f"source-{domain}" for domain in DOMAINS)
    assert len(report.facts) == 6


@pytest.mark.asyncio
async def test_abstains_when_material_claim_has_no_citation():
    async def extractor(**kwargs):
        return DraftClaimList(
            claims=[DraftClaim(claim_id="D1", text="Uncited domain answer.", citation_ids=[])]
        )

    state = await verify_final_document(
        document_package=_document([]),
        research_package=_research(),
        source_strictness="strict",
        ai_call=None,
        claim_extractor=extractor,
        adjudicator=_supported_adjudicator,
    )
    assert state.passed is False
    assert state.unsupported_claims[0].reason == "material_claim_has_no_citation"


@pytest.mark.asyncio
async def test_abstains_when_cited_source_is_unavailable():
    async def extractor(**kwargs):
        return DraftClaimList(
            claims=[DraftClaim(claim_id="D1", text="Unavailable-source answer.", citation_ids=[1])]
        )

    state = await verify_final_document(
        document_package=_document([1]),
        research_package=_research([]),
        source_strictness="strict",
        ai_call=None,
        claim_extractor=extractor,
        adjudicator=_supported_adjudicator,
    )
    assert state.passed is False
    assert state.unsupported_claims[0].reason == "cited_source_not_available_for_verification"


@pytest.mark.asyncio
async def test_abstains_when_citation_marker_is_duplicated():
    async def extractor(**kwargs):
        return DraftClaimList(
            claims=[DraftClaim(claim_id="D1", text="Ambiguous evidence.", citation_ids=[1, 1])]
        )

    state = await verify_final_document(
        document_package=_document([1]),
        research_package=_research(),
        source_strictness="strict",
        ai_call=None,
        claim_extractor=extractor,
        adjudicator=_supported_adjudicator,
    )
    assert state.passed is False
    assert state.unsupported_claims[0].reason == "duplicate_citation_ids"


def test_source_receipt_matches_current_provenance_implementation():
    source_path = EXT / "verified_pipeline.py"
    assert hashlib.sha256(source_path.read_bytes()).hexdigest() == (
        "97cf7e84e8f62c1190d1b5a6c4ac59be6d175e336be8dd1db3b64b9ea81dbd87"
    )
