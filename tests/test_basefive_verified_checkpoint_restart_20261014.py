from pathlib import Path

import pytest

from reasoners.deep_research_ext.research_run import (
    ResearchRunCheckpointError,
    ResearchRunStore,
    StaleResearchRunError,
    begin_research_run,
    checkpoint_research_run,
    resume_research_run,
)


SOURCE_REVISION = "basefive-source-v1"


def test_full_cycle_persists_verified_citation_and_partial_abstention(tmp_path: Path):
    store = ResearchRunStore(str(tmp_path))
    _, run = begin_research_run(
        "Report only source-grounded facts",
        store=store,
        source_revision=SOURCE_REVISION,
    )

    retrieved = checkpoint_research_run(
        store,
        run,
        stage="retrieval",
        payload={
            "research_package": {
                "source_articles": [{"id": "S1", "url": "https://source.example/fact"}],
            },
            "provider_call_ids": ["provider-1"],
        },
    )
    verified = checkpoint_research_run(
        store,
        retrieved,
        stage="evidence_verified",
        source_ids=("S1",),
        evidence_summary={
            "verified_citations": ["S1"],
            "citation_entailment_ratio": 1.0,
        },
        open_gap_ids=("R2",),
        payload={
            "terminal_mode": "verified_partial",
            "partial_abstention": {"unresolved_requirement_ids": ["R2"]},
        },
    )

    resumed, plan = resume_research_run(
        store,
        verified.run_id,
        source_revision=SOURCE_REVISION,
    )

    assert resumed.checkpoint_seq == 2
    assert resumed.source_ids == ("S1",)
    assert resumed.evidence_summary["citation_entailment_ratio"] == 1.0
    assert resumed.payload["terminal_mode"] == "verified_partial"
    assert plan["next_stage"] == "synthesis"
    assert plan["missing_gap_ids"] == ("R2",)
    assert plan["provider_call_ids"] == ("provider-1",)


def test_resume_rejects_stale_source_revision(tmp_path: Path):
    store = ResearchRunStore(str(tmp_path))
    _, run = begin_research_run(
        "Source-fenced query",
        store=store,
        source_revision=SOURCE_REVISION,
    )
    checkpoint_research_run(store, run, stage="retrieval")

    with pytest.raises(StaleResearchRunError, match="not 'basefive-source-v2'"):
        resume_research_run(store, run.run_id, source_revision="basefive-source-v2")


def test_checkpoint_rejects_stale_in_memory_run_without_optional_sequence(tmp_path: Path):
    store = ResearchRunStore(str(tmp_path))
    _, original = begin_research_run(
        "Reject stale checkpoint writer",
        store=store,
        source_revision=SOURCE_REVISION,
    )
    latest = checkpoint_research_run(store, original, stage="retrieval")

    with pytest.raises(ResearchRunCheckpointError, match="checkpoint sequence is stale"):
        checkpoint_research_run(store, original, stage="ledger")

    assert store.load(original.run_id, source_revision=SOURCE_REVISION) == latest


def test_replay_source_cannot_cross_source_revision(tmp_path: Path, monkeypatch):
    store = ResearchRunStore(str(tmp_path))
    original = begin_research_run(
        "Replay-fenced query",
        store=store,
        source_revision=SOURCE_REVISION,
    )[1]
    checkpoint_research_run(store, original, stage="research_package_ready")
    monkeypatch.setattr(
        "reasoners.deep_research_ext.research_run.current_agentfield_identity",
        lambda: ("basefive-replay", original.run_id),
    )

    with pytest.raises(StaleResearchRunError, match="not 'basefive-source-v2'"):
        begin_research_run(
            "Replay-fenced query",
            store=store,
            source_revision="basefive-source-v2",
        )
    assert not store.path_for("basefive-replay").exists()
