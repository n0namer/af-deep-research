"""Focused C4 abstention E2E coverage for the real final verifier boundary."""
from __future__ import annotations
import hashlib
import sys
from pathlib import Path
from types import SimpleNamespace
import pytest

ROOT = Path(__file__).resolve().parents[1]
EXT = ROOT / "reasoners" / "deep_research_ext"
if str(EXT) not in sys.path:
    sys.path.insert(0, str(EXT))
from final_verifier import DraftClaim, DraftClaimList, verify_final_document

SOURCE_URL = "https://example.org/source"
ARTICLE = {"id": 7, "url": SOURCE_URL, "content": "The source supports the claim."}

def _document(citation_ids):
    return {"executive_summary": "A source-backed claim.", "source_notes": [
        {"citation_id": citation_id, "url": SOURCE_URL} for citation_id in citation_ids
    ]}

def _research(articles=None):
    return {"source_articles": [ARTICLE] if articles is None else articles}

async def _extractor(*args, **kwargs):
    return DraftClaimList(claims=[DraftClaim(claim_id="D1", text="The claim is supported.", citation_ids=[1])])

async def _supported_adjudicator(candidates, *args, **kwargs):
    return SimpleNamespace(assessments=[SimpleNamespace(
        fact_id=candidates[0].fact_id, is_allowed=True, is_source_supported=True
    )])

@pytest.mark.asyncio
async def test_real_verifier_accepts_source_backed_claim():
    state = await verify_final_document(document_package=_document([1]), research_package=_research(),
        source_strictness="strict", ai_call=None, claim_extractor=_extractor,
        adjudicator=_supported_adjudicator)
    assert state.passed is True
    assert state.material_claim_count == 1
    assert state.supported_claim_count == 1
    assert state.unsupported_claims == []

@pytest.mark.asyncio
async def test_abstains_when_claim_has_no_citation():
    async def extractor(*args, **kwargs):
        return DraftClaimList(claims=[DraftClaim(claim_id="D1", text="Uncited fact.", citation_ids=[])])
    state = await verify_final_document(document_package=_document([]), research_package=_research(),
        source_strictness="strict", ai_call=None, claim_extractor=extractor,
        adjudicator=_supported_adjudicator)
    assert state.passed is False
    assert state.unsupported_claims[0].reason == "material_claim_has_no_citation"

@pytest.mark.asyncio
async def test_abstains_when_cited_source_is_missing():
    state = await verify_final_document(document_package=_document([1]), research_package=_research([]),
        source_strictness="strict", ai_call=None, claim_extractor=_extractor,
        adjudicator=_supported_adjudicator)
    assert state.passed is False
    assert state.unsupported_claims[0].reason == "cited_source_not_available_for_verification"

@pytest.mark.asyncio
async def test_abstains_on_duplicate_citation_ids():
    async def extractor(*args, **kwargs):
        return DraftClaimList(claims=[DraftClaim(claim_id="D1", text="Duplicated evidence.", citation_ids=[1, 1])])
    state = await verify_final_document(document_package=_document([1]), research_package=_research(),
        source_strictness="strict", ai_call=None, claim_extractor=extractor,
        adjudicator=_supported_adjudicator)
    assert state.passed is False
    assert state.unsupported_claims[0].reason == "duplicate_citation_ids"

@pytest.mark.asyncio
async def test_abstains_when_adjudication_fails_closed():
    async def failing_adjudicator(*args, **kwargs):
        raise RuntimeError("provider unavailable")
    state = await verify_final_document(document_package=_document([1]), research_package=_research(),
        source_strictness="strict", ai_call=None, claim_extractor=_extractor,
        adjudicator=failing_adjudicator)
    assert state.passed is False
    assert state.unsupported_claims[0].reason == "claim_verification_failed_closed"

def test_source_receipt_matches_current_production_file():
    source = ROOT / "reasoners" / "deep_research_ext" / "final_verifier.py"
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    assert digest == "d812e7f1b4f9b5375c5e0473076c84d8251b2e92e9aa42ae0d84be41f1b16e4f"
