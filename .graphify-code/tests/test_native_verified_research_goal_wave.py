import asyncio
from types import SimpleNamespace

from doc_generation_pipeline import AIAssessment, AIAssessmentList, DocumentResponse
from reasoners.deep_research_ext import verified_pipeline as vp
from reasoners.deep_research_ext.final_verifier import DraftClaim, DraftClaimList
from reasoners.deep_research_ext.methodology import select_methodology
from reasoners.deep_research_ext.models import ExtensionTrace, ResearchRequirement
from reasoners.deep_research_ext.task_contract import build_answer_contract


UPSTREAM = {
    "query": "Identify the frozen protocol facts and report them with evidence",
    "mode": "general",
    "research_focus": 3,
    "research_scope": 3,
    "max_research_loops": 1,
    "max_gap_rounds": 2,
    "num_parallel_streams": 1,
    "tension_lens": "balanced",
    "source_strictness": "strict",
    "evidence_style": "standard",
    "analysis_depth": "ANALYTICAL_BRIEF",
    "model": None,
    "api_key": None,
}


FACTS = {
    101: ("R1", "The protocol launched in 2024."),
    202: ("R2", "The protocol is specified by the frozen primary standard."),
}


def _trace():
    contract = build_answer_contract(UPSTREAM["query"], source_strictness="strict")
    contract = contract.model_copy(update={
        "requirements": [
            ResearchRequirement(
                requirement_id="R1",
                question="When did the protocol launch?",
                required_source_class="primary_or_authoritative_where_applicable",
            ),
            ResearchRequirement(
                requirement_id="R2",
                question="What specifies the protocol?",
                required_source_class="primary_or_authoritative_where_applicable",
            ),
        ]
    })
    return ExtensionTrace(answer_contract=contract, method_selection=select_methodology(contract))


def _package(source_ids=(101,)):
    articles = []
    evidence = []
    for source_id in source_ids:
        requirement_id, fact = FACTS[source_id]
        articles.append({
            "id": source_id,
            "title": f"Frozen primary source {source_id}",
            "url": f"https://frozen.example/{source_id}",
            "content": fact,
            "content_hash": f"frozen-{source_id}-v1",
        })
        evidence.append({
            "article_id": source_id,
            "facts": [fact],
            "quotes": [],
        })
    return {"source_articles": articles, "article_evidence": evidence}


def _document():
    return DocumentResponse(
        mode="general",
        version="frozen-native-v1",
        research_package={
            "document_title": "Frozen evidence report",
            "executive_summary": "The protocol launched in 2024 [1].",
            "sections": [],
            "source_notes": [
                {
                    "citation_id": 1,
                    "title": "Frozen primary source 101",
                    "url": "https://frozen.example/101",
                },
                {
                    "citation_id": 2,
                    "title": "Frozen primary source 202",
                    "url": "https://frozen.example/202",
                },
            ],
            "disclaimers": [],
        },
        metadata={},
    )


def _patch_deterministic_evidence(monkeypatch):
    async def map_claims(*, ledger, **kwargs):
        return ledger.model_copy(update={
            "claims": [
                claim.model_copy(update={
                    "requirement_ids": [FACTS[int(claim.source_id)][0]],
                })
                for claim in ledger.claims
            ]
        })

    async def verify_claims(*, ledger, research_package, **kwargs):
        available = {int(item["id"]) for item in research_package.get("source_articles", [])}
        return ledger.model_copy(update={
            "claims": [
                claim.model_copy(update={
                    "status": "verified" if int(claim.source_id) in available else "unverified",
                    "support_state": "source_entailed" if int(claim.source_id) in available else "candidate_extracted",
                })
                for claim in ledger.claims
            ]
        })

    monkeypatch.setattr(vp, "map_claims_to_requirements", map_claims)
    monkeypatch.setattr(vp, "verify_ledger_claims", verify_claims)


async def _good_ai_call(*, schema, **kwargs):
    if schema is DraftClaimList:
        return DraftClaimList(claims=[
            DraftClaim(
                claim_id="D1",
                text="The protocol launched in 2024.",
                citation_ids=[1],
            ),
        ])
    if schema is AIAssessmentList:
        return AIAssessmentList(assessments=[
            AIAssessment(
                fact_id=fact_id,
                is_allowed=True,
                is_source_supported=True,
                is_verified=True,
                disagreement_score=0.0,
            )
            for fact_id in ("D1:S1",)
        ])
    raise AssertionError(f"unexpected schema: {getattr(schema, '__name__', schema)}")


def test_native_full_cycle_retrieves_gap_persists_receipt_and_verifies_citations(monkeypatch):
    _patch_deterministic_evidence(monkeypatch)
    retrieval_calls = []
    gap_calls = []

    async def prepare(**kwargs):
        return SimpleNamespace(research_package=_package((101,)), metadata={"provider": "frozen-primary"})

    async def stream_executor(**kwargs):
        retrieval_calls.append(kwargs)
        return {"source_articles": _package((202,))["source_articles"], "article_evidence": _package((202,))["article_evidence"]}

    async def gap_round(**kwargs):
        gap_calls.append(kwargs["coverage"].verified_coverage_ratio)
        retrieved = await stream_executor(requirement_ids=("R2",))
        package = {
            "source_articles": kwargs["research_package"]["source_articles"] + retrieved["source_articles"],
            "article_evidence": kwargs["research_package"]["article_evidence"] + retrieved["article_evidence"],
        }
        ledger = vp.build_evidence_ledger(package, [])
        ledger = await vp.map_claims_to_requirements(
            ledger=ledger,
            contract=kwargs["contract"],
            ai_call=kwargs["ai_call"],
        )
        ledger = await vp.verify_ledger_claims(
            ledger=ledger,
            research_package=package,
            source_strictness="strict",
            ai_call=kwargs["ai_call"],
        )
        return package, ledger, SimpleNamespace(
            novelty_exhausted=False,
            model_dump=lambda: {"retrieved_requirement_ids": ["R2"], "novelty_exhausted": False},
        )

    monkeypatch.setattr(vp, "run_gap_research_round", gap_round)

    async def writer(**kwargs):
        return _document()

    result = asyncio.run(vp.execute_verified_pipeline(
        trace=_trace(),
        prepare_research_package=prepare,
        generate_document_from_package=writer,
        stream_executor=stream_executor,
        upstream_kwargs=dict(UPSTREAM),
        ai_call=_good_ai_call,
    ))

    assert result.mode == "general"
    extension = result.metadata["verified_research_extension"]
    assert extension["coverage_state"]["verified_coverage_ratio"] == 1.0
    assert len(extension["gap_rounds"]) == 1
    assert gap_calls == [0.5]
    assert len(retrieval_calls) == 1
    assert extension["final_verification"]["passed"] is True
    receipt = result.metadata["research_run"]
    assert receipt["run_id"]
    assert receipt["checkpoint_seq"] >= 4
    assert receipt["stage"] == "completed"


def test_native_negative_cycle_fails_closed_for_missing_citation_and_false_fact_id():
    from reasoners.deep_research_ext.final_verifier import verify_final_document

    async def missing_citation_claims(**kwargs):
        return DraftClaimList(claims=[
            DraftClaim(claim_id="D1", text="The protocol launched in 2024.", citation_ids=[]),
        ])

    missing = asyncio.run(verify_final_document(
        document_package=_document().research_package,
        research_package=_package((101, 202)),
        source_strictness="strict",
        ai_call=_good_ai_call,
        claim_extractor=missing_citation_claims,
    ))
    assert missing.passed is False
    assert missing.unsupported_claims[0].reason == "material_claim_has_no_citation"

    async def false_id_adjudicator(batch, strictness, **kwargs):
        return AIAssessmentList(assessments=[
            AIAssessment(
                fact_id="D1:S999",
                is_allowed=True,
                is_source_supported=True,
                is_verified=True,
                disagreement_score=0.0,
            )
        ])

    async def cited_claims(**kwargs):
        return DraftClaimList(claims=[
            DraftClaim(claim_id="D1", text="The protocol launched in 2024.", citation_ids=[1]),
        ])

    false_id = asyncio.run(verify_final_document(
        document_package=_document().research_package,
        research_package=_package((101, 202)),
        source_strictness="strict",
        ai_call=_good_ai_call,
        claim_extractor=cited_claims,
        adjudicator=false_id_adjudicator,
    ))
    assert false_id.passed is False
    assert false_id.unsupported_claims[0].reason == "cited_evidence_does_not_entail_claim"
