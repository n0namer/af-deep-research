from __future__ import annotations

from pathlib import Path

import pytest

from reasoners.deep_research_ext import research_run as research_run_module
from reasoners.deep_research_ext.research_run import (
    ResearchRun,
    ResearchRunCheckpointError,
    ResearchRunStore,
    begin_research_run,
    checkpoint_research_run,
)

SOURCE_REVISION = "e10580c89eac7a4f6efb50c921ae9107ce8ad8dc"


def _run(
    run_id: str,
    *,
    query: str = "verify durable research",
    stage: str = "started",
    checkpoint_seq: int = 0,
    status: str = "running",
    created_at: float = 1.0,
    replay_source_run_id: str | None = None,
    payload: dict[str, object] | None = None,
) -> ResearchRun:
    return ResearchRun(
        run_id=run_id,
        query=query,
        stage=stage,
        checkpoint_seq=checkpoint_seq,
        status=status,
        created_at=created_at,
        updated_at=created_at,
        replay_source_run_id=replay_source_run_id,
        source_revision=SOURCE_REVISION,
        stage_history=(stage,),
        payload=payload or {},
    )


def test_checkpoint_compares_expected_sequence_to_persisted_state(tmp_path: Path) -> None:
    store = ResearchRunStore(str(tmp_path))
    original = _run(
        "persisted-sequence-run",
        payload={"accepted_report_ids": ["report-c4-001"]},
    )
    store.save(original)
    first = checkpoint_research_run(
        store,
        original,
        stage="retrieval",
        expected_checkpoint_seq=0,
        evidence_summary={"fresh": True},
    )

    second = checkpoint_research_run(
        store,
        original,
        stage="ledger",
        expected_checkpoint_seq=1,
    )

    assert first.checkpoint_seq == 1
    assert second.checkpoint_seq == 2
    assert second.evidence_summary == {"fresh": True}
    assert second.payload["accepted_report_ids"] == ["report-c4-001"]
    assert store.load(original.run_id, source_revision=SOURCE_REVISION) == second


def test_checkpoint_rejects_different_owner_with_same_run_id(tmp_path: Path) -> None:
    store = ResearchRunStore(str(tmp_path))
    owner = _run(
        "owned-run",
        payload={"accepted_report_ids": ["report-c4-001"]},
    )
    store.save(owner)
    intruder = _run(
        owner.run_id,
        query="foreign query",
        created_at=2.0,
        payload={"accepted_report_ids": ["foreign-report"]},
    )

    with pytest.raises(ResearchRunCheckpointError, match="checkpoint owner mismatch"):
        checkpoint_research_run(
            store,
            intruder,
            stage="retrieval",
            expected_checkpoint_seq=0,
        )

    assert store.load(owner.run_id, source_revision=SOURCE_REVISION) == owner


def test_crash_replay_stale_writer_preserves_latest_report(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    store = ResearchRunStore(str(tmp_path))
    crashed = _run(
        "crashed-source-run",
        stage="failed",
        checkpoint_seq=3,
        status="failed",
        payload={
            "research_package": {"package_id": "package-001"},
            "accepted_report_ids": ["report-c4-001"],
        },
    )
    store.save(crashed)
    monkeypatch.setattr(
        research_run_module,
        "current_agentfield_identity",
        lambda: ("crash-replay-run", crashed.run_id),
    )
    _, replay = begin_research_run(
        crashed.query,
        store=store,
        source_revision=SOURCE_REVISION,
    )
    latest = checkpoint_research_run(
        store,
        replay,
        stage="evidence_verified",
        expected_checkpoint_seq=0,
        evidence_summary={"verified": True},
    )

    with pytest.raises(ResearchRunCheckpointError, match="checkpoint sequence is stale"):
        checkpoint_research_run(
            store,
            replay,
            stage="ledger",
            expected_checkpoint_seq=0,
            payload={"accepted_report_ids": ["stale-report"]},
        )

    persisted = store.load(replay.run_id, source_revision=SOURCE_REVISION)
    assert persisted == latest
    assert persisted is not None
    assert persisted.evidence_summary == {"verified": True}
    assert persisted.payload["accepted_report_ids"] == ["report-c4-001"]
