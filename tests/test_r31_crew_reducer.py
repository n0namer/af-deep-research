"""R31 independent reducer coverage for current provenance, CAS, and abstention contracts."""
from __future__ import annotations

import hashlib
from pathlib import Path
from types import SimpleNamespace

import pytest

from reasoners.deep_research_ext import final_verifier as verifier
from reasoners.deep_research_ext import research_run as runs
from reasoners.deep_research_ext import verified_pipeline as pipeline

ROOT = Path(__file__).resolve().parents[1]
PIPELINE = ROOT / "reasoners" / "deep_research_ext" / "verified_pipeline.py"
PIPELINE_SHA256 = "97cf7e84e8f62c1190d1b5a6c4ac59be6d175e336be8dd1db3b64b9ea81dbd87"


def _candidate():
    source_sha = hashlib.sha256(PIPELINE.read_bytes()).hexdigest()
    return pipeline.build_grounded_verified_report(
        report_id="r31-reducer",
        query="reducer provenance",
        source_revision=source_sha,
        source_owner="r31-owner",
        source_file_sha256=source_sha,
        facts=[{"fact_id": "fact-1", "source_id": "verified_pipeline.py", "source_sha256": source_sha}],
        payload={"gate": "r31"},
    )


def test_positive_current_source_persists_once_and_fences_terminal_effect():
    assert hashlib.sha256(PIPELINE.read_bytes()).hexdigest() == PIPELINE_SHA256
    store = pipeline.DurableVerifiedSourceReportStore()
    candidate = _candidate()

    first = pipeline.persist_grounded_verified_report(
        store, candidate, owner="r31-owner", effect_id="terminal-effect"
    )
    replay = pipeline.persist_grounded_verified_report(
        store, candidate, owner="r31-owner", effect_id="terminal-effect"
    )

    assert first[1:] == (True, True)
    assert replay[1:] == (False, False)
    assert store.effect_count() == 1
    assert pipeline.resume_grounded_verified_report(
        store, candidate.report_id, owner="r31-owner", source_file_sha256=candidate.source_file_sha256
    ).report_id == candidate.report_id


def test_negative_resume_rejects_stale_source_identity():
    store = pipeline.DurableVerifiedSourceReportStore()
    candidate = _candidate()
    pipeline.persist_grounded_verified_report(store, candidate, owner="r31-owner")

    with pytest.raises(pipeline.VerifiedSourceReportError, match="source file SHA"):
        pipeline.resume_grounded_verified_report(
            store, candidate.report_id, owner="r31-owner", source_file_sha256="0" * 64
        )


def test_negative_checkpoint_rejects_stale_sequence_and_revision():
    store = runs.ResearchRunStore()
    _, run = runs.begin_research_run(
        "r31 query", store=store, source_revision="rev-current", source_owner="r31-owner"
    )

    with pytest.raises(runs.StaleResearchRunError):
        runs.checkpoint_research_run(
            store, run, stage="query", source_revision="rev-stale",
            source_owner="r31-owner", expected_checkpoint_seq=0,
        )

    with pytest.raises(runs.ResearchRunCheckpointError, match="sequence is stale"):
        runs.checkpoint_research_run(
            store, run, stage="query", source_revision="rev-current",
            source_owner="r31-owner", expected_checkpoint_seq=1,
        )


@pytest.mark.asyncio
async def test_negative_final_verifier_abstains_without_citation():
    async def extractor(**kwargs):
        return verifier.DraftClaimList(
            claims=[verifier.DraftClaim(claim_id="D1", text="Unsupported claim", citation_ids=[])]
        )

    state = await verifier.verify_final_document(
        document_package={"executive_summary": "Unsupported claim", "source_notes": []},
        research_package={"source_articles": []},
        source_strictness="strict",
        ai_call=None,
        claim_extractor=extractor,
        adjudicator=SimpleNamespace(),
    )

    assert state.passed is False
    assert state.unsupported_claims[0].reason == "material_claim_has_no_citation"
