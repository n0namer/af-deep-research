import asyncio
from types import SimpleNamespace

import pytest

from doc_generation_pipeline import DocumentResponse
from reasoners.deep_research_ext import research_run as rr
from reasoners.deep_research_ext import verified_pipeline as vp
from reasoners.deep_research_ext.models import ExtensionTrace, ResearchRequirement
from reasoners.deep_research_ext.methodology import select_methodology
from reasoners.deep_research_ext.research_run import (
    ResearchRunCheckpointError,
    ResearchRunStore,
    StaleResearchRunError,
    begin_research_run,
    checkpoint_research_run,
    resume_research_run,
)
from reasoners.deep_research_ext.task_contract import build_answer_contract


UPSTREAM = {
    "query": "Report the source-entailed protocol launch fact and abstain from unsupported outcomes.",
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
                question="What source-entailed protocol launch fact is available?",
                required_source_class="primary_or_authoritative_where_applicable",
            ),
            ResearchRequirement(
                requirement_id="R2",
                question="What outcome remains unsupported?",
                required_source_class="primary_or_authoritative_where_applicable",
            ),
        ]
    })
    return ExtensionTrace(answer_contract=contract, method_selection=select_methodology(contract))


def _package():
    return {
        "source_articles": [{
            "id": 101,
            "title": "Frozen primary record",
            "url": "https://frozen.example/record",
            "content": "The protocol launched in 2024.",
            "content_hash": "frozen-primary-v1",
        }],
        "article_evidence": [{
            "article_id": 101,
            "facts": ["The protocol launched in 2024."],
            "quotes": [],
        }],
    }


def _writer():
    return DocumentResponse(
        mode="general",
        version="independent-qa-v1",
        research_package={
            "document_title": "Untrusted fluent draft",
            "executive_summary": "The protocol achieved an unsupported outcome.",
            "sections": [],
            "source_notes": [],
            "disclaimers": [],
        },
        metadata={},
    )


def _patch_deterministic_ledger(monkeypatch):
    async def map_claims(*, ledger, **kwargs):
        return ledger.model_copy(update={
            "claims": [
                claim.model_copy(update={"requirement_ids": ["R1"]})
                for claim in ledger.claims
            ]
        })

    async def verify_claims(*, ledger, **kwargs):
        return ledger.model_copy(update={
            "claims": [
                claim.model_copy(update={
                    "status": "verified",
                    "support_state": "source_entailed",
                })
                for claim in ledger.claims
            ]
        })

    monkeypatch.setattr(vp, "map_claims_to_requirements", map_claims)
    monkeypatch.setattr(vp, "verify_ledger_claims", verify_claims)


def _execute(*, store, run, prepare, generate):
    return asyncio.run(vp.execute_verified_pipeline(
        trace=_trace(),
        prepare_research_package=prepare,
        generate_document_from_package=generate,
        upstream_kwargs=dict(UPSTREAM),
        ai_call=None,
        run_store=store,
        research_run=run,
    ))


def test_independent_qa_interrupted_ledger_resumes_cached_package_once_and_rejects_zero_eligible_evidence(monkeypatch, tmp_path):
    _patch_deterministic_ledger(monkeypatch)
    store = ResearchRunStore(str(tmp_path))
    _, run = begin_research_run(UPSTREAM["query"], store=store, source_revision="accepted-source-v1")
    calls = {"prepare": 0, "writer": 0, "fail_once": True}

    async def prepare(**kwargs):
        calls["prepare"] += 1
        return SimpleNamespace(research_package=_package(), metadata={"provider": "frozen"})

    async def generate(**kwargs):
        calls["writer"] += 1
        return _writer()

    original_checkpoint = vp.checkpoint_research_run

    def interrupt_after_ledger(store_arg, run_arg, **kwargs):
        if kwargs.get("stage") == "evidence_verified" and calls["fail_once"]:
            calls["fail_once"] = False
            raise RuntimeError("simulated interruption after ledger work")
        return original_checkpoint(store_arg, run_arg, **kwargs)

    monkeypatch.setattr(vp, "checkpoint_research_run", interrupt_after_ledger)
    with pytest.raises(RuntimeError, match="simulated interruption"):
        _execute(store=store, run=run, prepare=prepare, generate=generate)

    interrupted = store.load(run.run_id, source_revision="accepted-source-v1")
    assert interrupted is not None
    assert interrupted.stage == "research_package_ready"
    assert interrupted.status == "running"
    assert interrupted.payload["research_package"] == _package()

    resumed, plan = resume_research_run(store, run.run_id, source_revision="accepted-source-v1")
    assert plan["terminal"] is False
    assert plan["next_stage"] == "evidence_verification"

    with pytest.raises(ValueError, match="eligible evidence"):
        _execute(store=store, run=resumed, prepare=prepare, generate=generate)

    rejected = store.load(run.run_id, source_revision="accepted-source-v1")
    assert rejected is not None
    assert rejected.status == "running"
    assert rejected.payload["research_package"] == _package()
    assert calls == {"prepare": 1, "writer": 0, "fail_once": False}

    retry, retry_plan = resume_research_run(
        store,
        run.run_id,
        source_revision="accepted-source-v1",
    )
    assert retry == rejected
    assert retry_plan["terminal"] is False


def test_independent_qa_duplicate_restart_preserves_terminal_checkpoint(monkeypatch, tmp_path):
    store = ResearchRunStore(str(tmp_path))
    monkeypatch.setattr(rr, "current_agentfield_identity", lambda: ("duplicate-restart", None))

    _, original = begin_research_run("duplicate query", store=store, source_revision="accepted-source-v1")
    completed = checkpoint_research_run(
        store,
        original,
        stage="completed",
        status="completed",
        source_revision="accepted-source-v1",
        open_gap_ids=("should-not-be-reopened",),
        conflicts=("preserved-conflict",),
        payload={"terminal_mode": "verified_document", "provider_call_ids": ["provider-1"]},
    )

    _, duplicate = begin_research_run("duplicate query", store=store, source_revision="accepted-source-v1")
    terminal, plan = resume_research_run(store, duplicate.run_id, source_revision="accepted-source-v1")

    assert duplicate == completed
    assert terminal == completed
    assert plan["terminal"] is True
    assert plan["missing_gap_ids"] == ()
    assert plan["provider_call_ids"] == ("provider-1",)
    assert plan["conflicts"] == ("preserved-conflict",)


def test_independent_qa_stale_source_and_sequence_fail_closed_without_terminal_regression(tmp_path):
    store = ResearchRunStore(str(tmp_path))
    _, run = begin_research_run("fenced query", store=store, source_revision="accepted-source-v1")
    current = checkpoint_research_run(
        store,
        run,
        stage="ledger",
        source_revision="accepted-source-v1",
        expected_checkpoint_seq=0,
    )
    terminal = checkpoint_research_run(
        store,
        current,
        stage="completed",
        status="completed",
        expected_checkpoint_seq=1,
    )

    with pytest.raises(StaleResearchRunError):
        resume_research_run(store, terminal.run_id, source_revision="accepted-source-v2")
    with pytest.raises(ResearchRunCheckpointError, match="checkpoint sequence is stale"):
        checkpoint_research_run(
            store,
            current,
            stage="coverage",
            expected_checkpoint_seq=0,
        )

    reloaded, plan = resume_research_run(store, terminal.run_id, source_revision="accepted-source-v1")
    assert reloaded == terminal
    assert reloaded.stage == "completed"
    assert reloaded.status == "completed"
    assert plan["terminal"] is True
