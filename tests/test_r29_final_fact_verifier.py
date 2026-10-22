import asyncio
import importlib.util
import sys
import types
from pathlib import Path
from types import SimpleNamespace

import pytest


@pytest.fixture
def verifier_module():
    fake = types.ModuleType("doc_generation_pipeline")
    fake.AIAssessmentList = object
    fake.FactForAdjudication = lambda **kwargs: SimpleNamespace(**kwargs)
    fake._classify_source = lambda url: ("primary", 1.0)
    fake._normalize_source_strictness = lambda value: value
    fake.adjudicate_evidence_ai = None
    sys.modules["doc_generation_pipeline"] = fake
    path = Path(__file__).parents[1] / "reasoners" / "deep_research_ext" / "final_verifier.py"
    spec = importlib.util.spec_from_file_location("r29_final_verifier", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_verification(module, claims, assessments=None):
    async def extract(**kwargs):
        return module.DraftClaimList(claims=claims)

    async def adjudicate(*args, **kwargs):
        return SimpleNamespace(assessments=list(assessments or []))

    return asyncio.run(module.verify_final_document(
        document_package={"source_notes": [{"citation_id": 1, "url": "https://source.test/a"}]},
        research_package={"source_articles": [{"id": 10, "url": "https://source.test/a", "content": "Evidence."}]},
        source_strictness="balanced", ai_call=object(),
        claim_extractor=extract, adjudicator=adjudicate,
    ))


def make_claim(module, citation_ids=(1,)):
    return module.DraftClaim(claim_id="D1", text="A supported fact.", citation_ids=list(citation_ids))


def test_positive_exact_supported_fact_identity(verifier_module):
    assessment = SimpleNamespace(fact_id="D1:S1", is_allowed=True, is_source_supported=True)
    state = run_verification(verifier_module, [make_claim(verifier_module)], [assessment])
    assert state.passed is True
    assert state.supported_claim_count == 1


def test_negative_no_citation(verifier_module):
    state = run_verification(verifier_module, [make_claim(verifier_module, ())])
    assert state.passed is False
    assert state.unsupported_claims[0].reason == "material_claim_has_no_citation"


def test_negative_duplicate_citation_identity(verifier_module):
    state = run_verification(verifier_module, [make_claim(verifier_module, (1, 1))])
    assert state.passed is False
    assert state.unsupported_claims[0].reason == "duplicate_citation_ids"


def test_negative_unknown_citation_fails_closed(verifier_module):
    state = run_verification(verifier_module, [make_claim(verifier_module, (99,))])
    assert state.passed is False
    assert state.unsupported_claims[0].reason == "cited_source_not_available_for_verification"


def test_negative_wrong_fact_id(verifier_module):
    assessment = SimpleNamespace(fact_id="D1:S999", is_allowed=True, is_source_supported=True)
    state = run_verification(verifier_module, [make_claim(verifier_module)], [assessment])
    assert state.passed is False
    assert state.unsupported_claims[0].reason == "cited_evidence_does_not_entail_claim"


def test_negative_unsupported_evidence(verifier_module):
    assessment = SimpleNamespace(fact_id="D1:S1", is_allowed=False, is_source_supported=False)
    state = run_verification(verifier_module, [make_claim(verifier_module)], [assessment])
    assert state.passed is False
    assert state.unsupported_claims[0].reason == "cited_evidence_does_not_entail_claim"
