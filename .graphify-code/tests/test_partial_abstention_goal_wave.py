import asyncio
from types import SimpleNamespace

from doc_generation_pipeline import DocumentResponse
from reasoners.deep_research_ext import verified_pipeline as vp
from reasoners.deep_research_ext.models import ExtensionTrace, ResearchRequirement
from reasoners.deep_research_ext.methodology import select_methodology
from reasoners.deep_research_ext.task_contract import build_answer_contract


UPSTREAM = {
    "query": "Report one supported fact and disclose any unresolved requirement",
    "mode": "general",
    "research_focus": 3,
    "research_scope": 3,
    "max_research_loops": 1,
    "max_gap_rounds": 0,
    "num_parallel_streams": 1,
    "tension_lens": "balanced",
    "source_strictness": "strict",
    "evidence_style": "standard",
    "analysis_depth": "ANALYTICAL_BRIEF",
    "model": None,
    "api_key": None,
}


def _trace():
    contract = build_answer_contract(UPSTREAM["query"], source_strictness="strict")
    contract = contract.model_copy(update={
        "requirements": [
            ResearchRequirement(
                requirement_id="R1",
                question="What is the supported fact?",
                required_source_class="primary_or_authoritative_where_applicable",
            ),
            ResearchRequirement(
                requirement_id="R2",
                question="What remains unresolved?",
                required_source_class="primary_or_authoritative_where_applicable",
            ),
        ]
    })
    return ExtensionTrace(answer_contract=contract, method_selection=select_methodology(contract))


def _package(*, include_decisive=True, include_disputed=False):
    articles = []
    evidence = []
    if include_decisive:
        articles.append({
            "id": 101,
            "title": "Primary source",
            "url": "https://frozen.example/primary",
            "content": "The supported fact is that the protocol launched in 2024.",
            "content_hash": "primary-v1",
        })
        evidence.append({
            "article_id": 101,
            "facts": ["The supported fact is that the protocol launched in 2024."],
            "quotes": [],
        })
    if include_disputed:
        articles.append({
            "id": 102,
            "title": "Disputed source",
            "url": "https://frozen.example/disputed",
            "content": "A disputed source claims the protocol launched in 2025.",
            "content_hash": "disputed-v1",
        })
        evidence.append({
            "article_id": 102,
            "facts": ["A disputed source claims the protocol launched in 2025."],
            "quotes": [],
        })
    return {"source_articles": articles, "article_evidence": evidence}


def _document(text="The fluent writer asserted an unsupported conclusion."):
    return DocumentResponse(
        mode="general",
        version="base20-test-v1",
        research_package={
            "document_title": "Fluent draft",
            "executive_summary": text,
            "sections": [],
            "source_notes": [],
            "disclaimers": [],
        },
        metadata={},
    )


def _patch_deterministic_evidence(monkeypatch, *, disputed_source_ids=()):
    disputed_source_ids = {int(source_id) for source_id in disputed_source_ids}

    async def map_claims(*, ledger, **kwargs):
        return ledger.model_copy(update={
            "claims": [
                claim.model_copy(update={
                    "requirement_ids": ["R2"] if int(claim.source_id) == 102 else ["R1"]
                })
                for claim in ledger.claims
            ]
        })

    async def verify_claims(*, ledger, research_package, **kwargs):
        available = {int(item["id"]) for item in research_package.get("source_articles", [])}
        return ledger.model_copy(update={
            "claims": [
                claim.model_copy(update={
                    "status": (
                        "disputed" if int(claim.source_id) in disputed_source_ids else "verified"
                    ) if int(claim.source_id) in available else "unverified",
                    "support_state": "source_entailed" if int(claim.source_id) in available else "candidate_extracted",
                })
                for claim in ledger.claims
            ]
        })

    monkeypatch.setattr(vp, "map_claims_to_requirements", map_claims)
    monkeypatch.setattr(vp, "verify_ledger_claims", verify_claims)


def _run(monkeypatch, *, package, writer, disputed_source_ids=()):
    _patch_deterministic_evidence(monkeypatch, disputed_source_ids=disputed_source_ids)
    calls = []

    async def prepare(**kwargs):
        return SimpleNamespace(research_package=package, metadata={"provider": "frozen"})

    async def generate(**kwargs):
        calls.append("writer")
        return writer

    result = asyncio.run(vp.execute_verified_pipeline(
        trace=_trace(),
        prepare_research_package=prepare,
        generate_document_from_package=generate,
        upstream_kwargs=dict(UPSTREAM),
        ai_call=None,
    ))
    return result, calls


def test_base20_partial_abstention_is_source_entailed_and_provenance_bound(monkeypatch):
    result, calls = _run(monkeypatch, package=_package(), writer=_document())

    assert calls == []
    assert result.mode == "verified_partial"
    assert result.research_package["document_title"] == "Verified Research — Partial Evidence Report"
    assert result.research_package["sections"][0]["content"] == "- The supported fact is that the protocol launched in 2024. [1]"
    assert "Insufficient verified evidence" in result.research_package["sections"][1]["content"]
    assert result.research_package["source_notes"] == [{
        "citation_id": 1,
        "title": "Primary source",
        "domain": "frozen.example",
        "url": "https://frozen.example/primary",
    }]
    extension = result.metadata["verified_research_extension"]
    assert extension["delivery_verification"]["mode"] == "verified_partial"
    assert extension["delivery_verification"]["unresolved_requirement_ids"] == ["R2"]


def test_base20_fluent_final_synthesis_cannot_bypass_partial_gate(monkeypatch):
    result, calls = _run(
        monkeypatch,
        package=_package(),
        writer=_document("The protocol definitely achieved the unsupported outcome."),
    )

    assert calls == []
    assert result.mode == "verified_partial"
    rendered = result.research_package
    assert "definitely achieved" not in rendered["executive_summary"]
    assert all("unsupported" not in section["content"].lower() for section in rendered["sections"])


def test_base20_decisive_evidence_removal_abstains_for_all_requirements(monkeypatch):
    result, calls = _run(monkeypatch, package=_package(include_decisive=False), writer=_document())

    assert calls == []
    assert result.mode == "verified_partial"
    assert all("Insufficient verified evidence" in section["content"] for section in result.research_package["sections"])
    assert result.metadata["verified_research_extension"]["delivery_verification"]["unresolved_requirement_ids"] == ["R1", "R2"]


def test_base20_disputed_source_is_disclosed_not_promoted(monkeypatch):
    result, calls = _run(
        monkeypatch,
        package=_package(include_disputed=True),
        writer=_document(),
        disputed_source_ids=(102,),
    )

    assert calls == []
    assert result.mode == "verified_partial"
    unresolved_section = result.research_package["sections"][1]["content"]
    assert "Contradictory evidence detected:" in unresolved_section
    assert "DISPUTED:" in unresolved_section
    assert "Insufficient verified evidence" in unresolved_section
    assert result.metadata["verified_research_extension"]["contradictions"]["requirement_ids"] == ["R2"]
