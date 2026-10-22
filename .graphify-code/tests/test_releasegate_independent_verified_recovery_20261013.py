import asyncio
import hashlib
from pathlib import Path

import pytest

from doc_generation_pipeline import AIAssessment, AIAssessmentList
from reasoners.deep_research_ext import research_run as rr
from reasoners.deep_research_ext.final_verifier import (
    DraftClaim,
    DraftClaimList,
    verify_final_document,
)
from reasoners.deep_research_ext.research_run import (
    ResearchRunStore,
    begin_research_run,
    checkpoint_research_run,
    resume_research_run,
)


SOURCE_REVISION = "releasegate-independent-source-v1"
QUERY = "Report only the verified launch fact."

REVIEWED_SHA256 = {
    "reasoners/deep_research_ext/verified_pipeline.py": "1ea0b249afc0c84d57824b78c5b4e6b3a79ae40a5b5890ed1a91d1046a872d1f",
    "reasoners/deep_research_ext/research_run.py": "713caa8e1d6c4e96127b72571b42ab34882542cd478976fe83bb3e2785681d4c",
    "reasoners/deep_research_ext/final_verifier.py": "d9210579b1a673b1cdc7dbd15f4f0cff660c1e75eedaa4abc54d9a910c00aef1",
    "tests/test_releasegate_native_evidence_20261013.py": "75171c60b92236c6fee6b7e47facc10af659e90c5796ed381250055b18c00b54",
    "tests/test_releasegate_restart_resume_20261013.py": "850e3c0b97c886332bac8089c7e2a9dcd425f48186e25e4db6bdb16bbeab96cc",
    "docs/acceptance/releasegate-native-evidence-20261013.md": "1c315d1e2943cf3bd812a7d5d2d3eac038f1e9f2693725abef3ff223bdd83b76",
    "docs/acceptance/releasegate-restart-resume-20261013.md": "d90c0894e3a3019166712b363ad7d44c4aeae1e2862080cfcd3a50321b0581ba",
}


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


def _document_package():
    return {
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
    }


def test_independent_gate_is_bound_to_reviewed_source_and_producer_artifacts():
    root = Path(__file__).resolve().parents[1]
    observed = {
        relative: hashlib.sha256((root / relative).read_bytes()).hexdigest()
        for relative in REVIEWED_SHA256
    }
    assert observed == REVIEWED_SHA256


async def _single_cited_claim(**kwargs):
    return DraftClaimList(
        claims=[
            DraftClaim(
                claim_id="D1",
                text="The protocol launched in 2024.",
                citation_ids=[1],
            )
        ]
    )


async def _duplicate_positive_fact_ids(batch, strictness, **kwargs):
    assert [item.fact_id for item in batch] == ["D1:S1"]
    duplicate = AIAssessment(
        fact_id="D1:S1",
        is_allowed=True,
        is_source_supported=True,
        is_verified=True,
        disagreement_score=0.0,
    )
    return AIAssessmentList(assessments=[duplicate, duplicate])


def test_duplicate_positive_fact_id_cannot_verify_one_citation_twice():
    result = asyncio.run(
        verify_final_document(
            document_package=_document_package(),
            research_package=_research_package(),
            source_strictness="strict",
            ai_call=None,
            claim_extractor=_single_cited_claim,
            adjudicator=_duplicate_positive_fact_ids,
        )
    )

    assert result.passed is False
    assert result.supported_claim_count == 0
    assert result.unsupported_claims[0].reason == "cited_evidence_does_not_entail_claim"


def test_same_native_identity_retry_preserves_terminal_payload(monkeypatch, tmp_path):
    identity = {"value": ("native-terminal-run", None)}
    monkeypatch.setattr(rr, "current_agentfield_identity", lambda: identity["value"])
    store = ResearchRunStore(str(tmp_path))
    _, started = begin_research_run(QUERY, store=store, source_revision=SOURCE_REVISION)
    completed = checkpoint_research_run(
        store,
        started,
        stage="completed",
        status="completed",
        source_revision=SOURCE_REVISION,
        source_ids=("101",),
        payload={
            "research_package": _research_package(),
            "document_package": _document_package(),
            "terminal_mode": "verified_document",
        },
    )

    _, retried = begin_research_run(QUERY, store=store, source_revision=SOURCE_REVISION)
    reloaded, plan = resume_research_run(
        store,
        retried.run_id,
        source_revision=SOURCE_REVISION,
    )

    assert retried == completed
    assert reloaded == completed
    assert plan["terminal"] is True
    assert plan["next_stage"] == "done"


@pytest.mark.parametrize(
    ("terminal_mode", "document_package"),
    [
        ("verified_document", _document_package()),
        ("programmatic_partial_abstention", None),
    ],
)
def test_new_native_replay_of_terminal_run_stays_terminal_and_cannot_duplicate_output(
    monkeypatch,
    tmp_path,
    terminal_mode,
    document_package,
):
    identity = {"value": ("native-original", None)}
    monkeypatch.setattr(rr, "current_agentfield_identity", lambda: identity["value"])
    store = ResearchRunStore(str(tmp_path))
    _, started = begin_research_run(QUERY, store=store, source_revision=SOURCE_REVISION)
    terminal_payload = {
        "research_package": _research_package(),
        "terminal_mode": terminal_mode,
        "provider_call_ids": ["source-call-1", "report-call-1"],
    }
    if document_package is not None:
        terminal_payload["document_package"] = document_package
    completed = checkpoint_research_run(
        store,
        started,
        stage="completed",
        status="completed",
        source_revision=SOURCE_REVISION,
        source_ids=("101",),
        payload=terminal_payload,
    )

    identity["value"] = ("native-replay", completed.run_id)
    _, replay = begin_research_run(QUERY, store=store, source_revision=SOURCE_REVISION)
    reloaded, plan = resume_research_run(
        store,
        replay.run_id,
        source_revision=SOURCE_REVISION,
    )

    assert replay.replay_source_run_id == completed.run_id
    assert replay.stage == "completed"
    assert replay.status == "completed"
    assert replay.payload == completed.payload
    assert reloaded == replay
    assert plan["terminal"] is True
    assert plan["next_stage"] == "done"
    assert plan["provider_call_ids"] == ("source-call-1", "report-call-1")
