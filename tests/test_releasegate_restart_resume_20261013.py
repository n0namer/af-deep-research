import asyncio
from types import SimpleNamespace

import pytest

from doc_generation_pipeline import AIAssessment, AIAssessmentList, DocumentResponse
from reasoners.deep_research_ext import research_run as rr
from reasoners.deep_research_ext import verified_pipeline as vp
from reasoners.deep_research_ext.final_verifier import DraftClaim, DraftClaimList
from reasoners.deep_research_ext.methodology import select_methodology
from reasoners.deep_research_ext.models import ExtensionTrace, ResearchRequirement
from reasoners.deep_research_ext.research_run import (
    ResearchRunStore,
    StaleResearchRunError,
    begin_research_run,
    checkpoint_research_run,
)
from reasoners.deep_research_ext.task_contract import build_answer_contract


SOURCE_REVISION = "releasegate-source-v1"
UPSTREAM = {
    "query": "Report the verified launch fact and abstain from unsupported outcomes.",
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


def _trace(*, include_unresolved=False):
    contract = build_answer_contract(UPSTREAM["query"], source_strictness="strict")
    requirements = [
        ResearchRequirement(
            requirement_id="R1",
            question="What verified launch fact is available?",
            required_source_class="primary_or_authoritative_where_applicable",
        )
    ]
    if include_unresolved:
        requirements.append(
            ResearchRequirement(
                requirement_id="R2",
                question="What outcome remains unsupported?",
                required_source_class="primary_or_authoritative_where_applicable",
            )
        )
    contract = contract.model_copy(update={"requirements": requirements})
    return ExtensionTrace(answer_contract=contract, method_selection=select_methodology(contract))


def _research_package():
    return {
        "source_articles": [
            {
                "id": 101,
                "title": "Frozen primary record",
                "url": "https://frozen.example/record",
                "content": "The protocol launched in 2024.",
                "content_hash": "frozen-primary-v1",
            }
        ],
        "article_evidence": [
            {
                "article_id": 101,
                "facts": ["The protocol launched in 2024."],
                "quotes": [],
            }
        ],
    }


def _document():
    return DocumentResponse(
        mode="general",
        version="releasegate-v1",
        research_package={
            "document_title": "Verified launch report",
            "executive_summary": "The protocol launched in 2024. [1]",
            "sections": [],
            "source_notes": [
                {
                    "citation_id": 1,
                    "title": "Frozen primary record",
                    "url": "https://frozen.example/record",
                }
            ],
            "disclaimers": [],
        },
        metadata={},
    )


def _patch_deterministic_ledger(monkeypatch):
    async def map_claims(*, ledger, **kwargs):
        return ledger.model_copy(
            update={
                "claims": [
                    claim.model_copy(update={"requirement_ids": ["R1"]})
                    for claim in ledger.claims
                ]
            }
        )

    async def verify_claims(*, ledger, **kwargs):
        return ledger.model_copy(
            update={
                "claims": [
                    claim.model_copy(
                        update={
                            "status": "verified",
                            "support_state": "source_entailed",
                        }
                    )
                    for claim in ledger.claims
                ]
            }
        )

    monkeypatch.setattr(vp, "map_claims_to_requirements", map_claims)
    monkeypatch.setattr(vp, "verify_ledger_claims", verify_claims)


async def _valid_final_ai_call(*, schema, **kwargs):
    if schema is DraftClaimList:
        return DraftClaimList(
            claims=[
                DraftClaim(
                    claim_id="D1",
                    text="The protocol launched in 2024.",
                    citation_ids=[1],
                )
            ]
        )
    if schema is AIAssessmentList:
        return AIAssessmentList(
            assessments=[
                AIAssessment(
                    fact_id="D1:S1",
                    is_allowed=True,
                    is_source_supported=True,
                    is_verified=True,
                    disagreement_score=0.0,
                )
            ]
        )
    raise AssertionError(f"unexpected schema: {getattr(schema, '__name__', schema)}")


def _execute(*, trace, store, run, prepare, writer, ai_call):
    return asyncio.run(
        vp.execute_verified_pipeline(
            trace=trace,
            prepare_research_package=prepare,
            generate_document_from_package=writer,
            upstream_kwargs=dict(UPSTREAM),
            ai_call=ai_call,
            run_store=store,
            research_run=run,
        )
    )


def test_native_restart_reuses_saved_evidence_and_emits_one_report(monkeypatch, tmp_path):
    _patch_deterministic_ledger(monkeypatch)
    identity = {"value": ("native-releasegate-original", None)}
    monkeypatch.setattr(rr, "current_agentfield_identity", lambda: identity["value"])
    store = ResearchRunStore(str(tmp_path))
    _, original = begin_research_run(
        UPSTREAM["query"], store=store, source_revision=SOURCE_REVISION
    )
    calls = {"source": 0, "report": 0, "interrupt": True}

    async def prepare(**kwargs):
        calls["source"] += 1
        return SimpleNamespace(
            research_package=_research_package(),
            metadata={"provider": "frozen", "provider_call_id": "source-call-1"},
        )

    async def writer(**kwargs):
        calls["report"] += 1
        return _document()

    real_checkpoint = vp.checkpoint_research_run

    def interrupt_after_snapshot(store_arg, run_arg, **kwargs):
        if kwargs.get("stage") == "evidence_verified" and calls["interrupt"]:
            calls["interrupt"] = False
            raise RuntimeError("simulated process interruption after evidence snapshot")
        return real_checkpoint(store_arg, run_arg, **kwargs)

    monkeypatch.setattr(vp, "checkpoint_research_run", interrupt_after_snapshot)
    with pytest.raises(RuntimeError, match="simulated process interruption"):
        _execute(
            trace=_trace(),
            store=store,
            run=original,
            prepare=prepare,
            writer=writer,
            ai_call=_valid_final_ai_call,
        )

    saved = store.load(original.run_id, source_revision=SOURCE_REVISION)
    assert saved is not None
    assert saved.stage == "research_package_ready"
    assert saved.payload["research_package"] == _research_package()
    assert calls == {"source": 1, "report": 0, "interrupt": False}

    monkeypatch.setattr(vp, "checkpoint_research_run", real_checkpoint)
    identity["value"] = ("native-releasegate-restart", original.run_id)
    _, replay = begin_research_run(
        UPSTREAM["query"], store=store, source_revision=SOURCE_REVISION
    )
    assert replay.replay_source_run_id == original.run_id
    assert replay.stage == "research_package_ready"
    assert replay.payload["research_package"] == saved.payload["research_package"]

    result = _execute(
        trace=_trace(),
        store=store,
        run=replay,
        prepare=prepare,
        writer=writer,
        ai_call=_valid_final_ai_call,
    )

    terminal = store.load(replay.run_id, source_revision=SOURCE_REVISION)
    assert calls == {"source": 1, "report": 1, "interrupt": False}
    assert result.mode == "general"
    assert result.metadata["research_phase_metadata"]["resumed_from_checkpoint"] is True
    assert result.metadata["research_phase_metadata"]["research_run_id"] == replay.run_id
    assert terminal is not None
    assert terminal.stage == "completed"
    assert terminal.status == "completed"
    assert terminal.payload["research_package"] == _research_package()
    assert terminal.payload["document_package"] == _document().research_package
    assert terminal.payload["terminal_mode"] == "verified_document"
    assert len(list(tmp_path.glob("*.json"))) == 2


def test_stale_revision_and_ambiguous_provider_fact_ids_fail_closed(monkeypatch, tmp_path):
    _patch_deterministic_ledger(monkeypatch)
    identity = {"value": ("native-stale-original", None)}
    monkeypatch.setattr(rr, "current_agentfield_identity", lambda: identity["value"])
    store = ResearchRunStore(str(tmp_path))
    _, original = begin_research_run(
        UPSTREAM["query"], store=store, source_revision=SOURCE_REVISION
    )
    original = checkpoint_research_run(
        store,
        original,
        stage="research_package_ready",
        source_ids=("101",),
        payload={
            "research_package": _research_package(),
            "research_phase_metadata": {"provider": "frozen"},
        },
    )

    identity["value"] = ("native-stale-restart", original.run_id)
    with pytest.raises(StaleResearchRunError):
        begin_research_run(
            UPSTREAM["query"],
            store=store,
            source_revision="releasegate-source-v2",
        )
    assert not store.path_for("native-stale-restart").exists()

    identity["value"] = ("native-ambiguous-run", None)
    _, ambiguous_run = begin_research_run(
        UPSTREAM["query"], store=store, source_revision=SOURCE_REVISION
    )
    calls = {"source": 0, "report": 0}

    async def prepare(**kwargs):
        calls["source"] += 1
        return SimpleNamespace(research_package=_research_package(), metadata={})

    async def writer(**kwargs):
        calls["report"] += 1
        return _document()

    async def ambiguous_ai_call(*, schema, **kwargs):
        if schema is DraftClaimList:
            return DraftClaimList(
                claims=[
                    DraftClaim(
                        claim_id="D1",
                        text="The protocol launched in 2024.",
                        citation_ids=[1],
                    )
                ]
            )
        if schema is AIAssessmentList:
            return AIAssessmentList(
                assessments=[
                    AIAssessment(
                        fact_id="D1:S1",
                        is_allowed=True,
                        is_source_supported=True,
                        is_verified=True,
                        disagreement_score=0.0,
                    ),
                    AIAssessment(
                        fact_id="D1:S999",
                        is_allowed=True,
                        is_source_supported=True,
                        is_verified=True,
                        disagreement_score=0.0,
                    ),
                ]
            )
        raise AssertionError(f"unexpected schema: {getattr(schema, '__name__', schema)}")

    result = _execute(
        trace=_trace(),
        store=store,
        run=ambiguous_run,
        prepare=prepare,
        writer=writer,
        ai_call=ambiguous_ai_call,
    )

    terminal = store.load(ambiguous_run.run_id, source_revision=SOURCE_REVISION)
    extension = result.metadata["verified_research_extension"]
    assert calls == {"source": 1, "report": 1}
    assert result.mode == "verified_evidence_only"
    assert extension["mode"] == "post_generation_rejected"
    assert extension["final_verification"]["passed"] is False
    assert extension["final_verification"]["unsupported_claims"][0]["reason"] == (
        "cited_evidence_does_not_entail_claim"
    )
    assert terminal is not None
    assert terminal.stage == "completed"
    assert terminal.payload["terminal_mode"] == "post_generation_rejected"


def test_restart_delivers_partial_abstention_without_source_or_writer_duplication(
    monkeypatch, tmp_path
):
    _patch_deterministic_ledger(monkeypatch)
    identity = {"value": ("native-partial-original", None)}
    monkeypatch.setattr(rr, "current_agentfield_identity", lambda: identity["value"])
    store = ResearchRunStore(str(tmp_path))
    _, original = begin_research_run(
        UPSTREAM["query"], store=store, source_revision=SOURCE_REVISION
    )
    calls = {"source": 0, "report": 0, "interrupt": True}

    async def prepare(**kwargs):
        calls["source"] += 1
        return SimpleNamespace(research_package=_research_package(), metadata={})

    async def writer(**kwargs):
        calls["report"] += 1
        return _document()

    real_checkpoint = vp.checkpoint_research_run

    def interrupt_after_snapshot(store_arg, run_arg, **kwargs):
        if kwargs.get("stage") == "evidence_verified" and calls["interrupt"]:
            calls["interrupt"] = False
            raise RuntimeError("simulated partial-run interruption")
        return real_checkpoint(store_arg, run_arg, **kwargs)

    monkeypatch.setattr(vp, "checkpoint_research_run", interrupt_after_snapshot)
    with pytest.raises(RuntimeError, match="simulated partial-run interruption"):
        _execute(
            trace=_trace(include_unresolved=True),
            store=store,
            run=original,
            prepare=prepare,
            writer=writer,
            ai_call=None,
        )

    monkeypatch.setattr(vp, "checkpoint_research_run", real_checkpoint)
    identity["value"] = ("native-partial-restart", original.run_id)
    _, replay = begin_research_run(
        UPSTREAM["query"], store=store, source_revision=SOURCE_REVISION
    )
    result = _execute(
        trace=_trace(include_unresolved=True),
        store=store,
        run=replay,
        prepare=prepare,
        writer=writer,
        ai_call=None,
    )

    terminal = store.load(replay.run_id, source_revision=SOURCE_REVISION)
    extension = result.metadata["verified_research_extension"]
    assert calls == {"source": 1, "report": 0, "interrupt": False}
    assert result.mode == "verified_partial"
    assert result.research_package["sections"][0]["content"] == (
        "- The protocol launched in 2024. [1]"
    )
    assert "Insufficient verified evidence" in result.research_package["sections"][1]["content"]
    assert extension["mode"] == "programmatic_partial_abstention"
    assert extension["delivery_verification"]["unresolved_requirement_ids"] == ["R2"]
    assert terminal is not None
    assert terminal.stage == "completed"
    assert terminal.payload["terminal_mode"] == "programmatic_partial_abstention"
    assert terminal.payload["semantic_snapshot"]["unsupported_material_claims"] == 0
    assert terminal.payload["semantic_snapshot"]["citation_entailment_ratio"] == 1.0
