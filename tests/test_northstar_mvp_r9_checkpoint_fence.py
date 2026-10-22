from pathlib import Path

import pytest

from reasoners.deep_research_ext.research_run import (
    ResearchRunCheckpointError,
    ResearchRunStore,
    StaleResearchRunError,
    begin_research_run,
    checkpoint_research_run,
    evidence_already_recorded,
    provider_call_already_recorded,
    resume_research_run,
)


REVISION = "frozen-source-r9"
OWNER = "source-owner-r9"


def test_native_positive_persists_fenced_result_and_dedupes_effect_ids(tmp_path: Path):
    store = ResearchRunStore(str(tmp_path))
    _, run = begin_research_run("source grounded report", store=store, source_revision=REVISION, source_owner=OWNER)
    checkpoint = checkpoint_research_run(
        store,
        run,
        stage="evidence_verified",
        source_revision=REVISION,
        source_owner=OWNER,
        source_ids=("S1",),
        evidence_ids=("E1", "E1"),
        payload={
            "provider_call_ids": ["call-1", "call-1"],
            "evidence_ids": ["E1", "E2"],
            "partial_abstention": {"unresolved_requirement_ids": ["R2"]},
            "report": {"mode": "verified_partial", "facts": ["S1"]},
        },
    )

    restarted, plan = resume_research_run(store, checkpoint.run_id, source_revision=REVISION, source_owner=OWNER)
    assert restarted.checkpoint_seq == 1
    assert restarted.source_revision == REVISION
    assert restarted.source_owner == OWNER
    assert restarted.evidence_ids == ("E1", "E2")
    assert plan["provider_call_ids"] == ("call-1",)
    assert plan["evidence_ids"] == ("E1", "E2")
    assert plan["partial_abstention"] is True
    assert plan["report"] == {"mode": "verified_partial", "facts": ["S1"]}
    assert provider_call_already_recorded(restarted, "call-1")
    assert evidence_already_recorded(restarted, "E2")


def test_wrong_source_owner_fails_closed_without_overwriting_checkpoint(tmp_path: Path):
    store = ResearchRunStore(str(tmp_path))
    _, run = begin_research_run("owner fenced", store=store, source_revision=REVISION, source_owner=OWNER)
    saved = checkpoint_research_run(store, run, stage="retrieval", source_owner=OWNER)

    with pytest.raises(ResearchRunCheckpointError, match="source owner"):
        checkpoint_research_run(store, saved, stage="ledger", source_owner="wrong-owner")
    with pytest.raises(ResearchRunCheckpointError, match="source owner"):
        resume_research_run(store, saved.run_id, source_owner="wrong-owner")

    assert store.load(saved.run_id).checkpoint_seq == saved.checkpoint_seq
    assert store.load(saved.run_id).stage == "retrieval"


def test_stale_source_and_duplicate_writer_are_rejected(tmp_path: Path):
    store = ResearchRunStore(str(tmp_path))
    _, original = begin_research_run("restart fence", store=store, source_revision=REVISION, source_owner=OWNER)
    latest = checkpoint_research_run(store, original, stage="retrieval", source_owner=OWNER)

    with pytest.raises(ResearchRunCheckpointError, match="checkpoint sequence is stale"):
        checkpoint_research_run(store, original, stage="ledger", source_owner=OWNER)
    with pytest.raises(StaleResearchRunError, match="not 'changed-source'"):
        resume_research_run(store, latest.run_id, source_revision="changed-source", source_owner=OWNER)

    assert store.load(latest.run_id, source_revision=REVISION) == latest


def test_cancelled_or_partial_run_resumes_without_repeating_provider_effect(tmp_path: Path):
    store = ResearchRunStore(str(tmp_path))
    _, run = begin_research_run("cancel safe", store=store, source_revision=REVISION, source_owner=OWNER)
    interrupted = checkpoint_research_run(
        store,
        run,
        stage="retrieval",
        status="cancelled",
        source_owner=OWNER,
        payload={"provider_call_ids": ["call-cancelled"], "report": {"mode": "abstain"}},
    )

    resumed, plan = resume_research_run(store, interrupted.run_id, source_revision=REVISION, source_owner=OWNER)
    assert resumed.status == "cancelled"
    assert plan["provider_call_ids"] == ("call-cancelled",)
    assert plan["report"] == {"mode": "abstain"}
    assert provider_call_already_recorded(resumed, "call-cancelled")
    assert plan["terminal"] is False
