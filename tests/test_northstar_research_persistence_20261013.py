from __future__ import annotations

import json
from pathlib import Path

import pytest

from reasoners.deep_research_ext import research_run as research_run_module
from reasoners.deep_research_ext.research_run import (
    ResearchRun,
    ResearchRunCheckpointError,
    ResearchRunStore,
    StaleResearchRunError,
    begin_research_run,
    checkpoint_research_run,
    recorded_provider_call_ids,
    resume_research_run,
)

SOURCE_REVISION = "e10580c89eac7a4f6efb50c921ae9107ce8ad8dc"


def _run(
    run_id: str,
    *,
    query: str = "verify durable research",
    stage: str = "started",
    checkpoint_seq: int = 0,
    status: str = "running",
    source_revision: str = SOURCE_REVISION,
    payload: dict[str, object] | None = None,
) -> ResearchRun:
    return ResearchRun(
        run_id=run_id,
        query=query,
        stage=stage,
        checkpoint_seq=checkpoint_seq,
        status=status,
        created_at=1.0,
        updated_at=1.0,
        source_revision=source_revision,
        stage_history=(stage,),
        payload=payload or {},
    )


def test_native_save_load_restart_preserves_terminal_report_once(tmp_path: Path) -> None:
    store = ResearchRunStore(str(tmp_path))
    original = _run(
        "native-terminal-run",
        stage="completed",
        checkpoint_seq=4,
        status="completed",
        payload={
            "accepted_report_ids": ["report-c4-001"],
            "provider_call_ids": ["provider-001", "provider-001"],
        },
    )

    checkpoint_path = store.save(original)
    restarted_store = ResearchRunStore(str(tmp_path))
    loaded, resume_plan = resume_research_run(
        restarted_store,
        original.run_id,
        source_revision=SOURCE_REVISION,
    )

    assert checkpoint_path == tmp_path / "native-terminal-run.json"
    assert loaded == original
    assert resume_plan["terminal"] is True
    assert resume_plan["next_stage"] == "done"
    assert resume_plan["provider_call_ids"] == ("provider-001",)
    assert loaded.payload["accepted_report_ids"] == ["report-c4-001"]
    assert list(tmp_path.glob("native-terminal-run.json")) == [checkpoint_path]
    assert not list(tmp_path.glob("*.tmp-*"))


def test_begin_reuses_run_id_after_persistent_restart(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        research_run_module,
        "current_agentfield_identity",
        lambda: ("stable-agentfield-run", None),
    )

    first_store, first = begin_research_run(
        "same query",
        store=ResearchRunStore(str(tmp_path)),
        source_revision=SOURCE_REVISION,
    )
    restarted_store, restarted = begin_research_run(
        "same query",
        store=ResearchRunStore(str(tmp_path)),
        source_revision=SOURCE_REVISION,
    )

    assert first_store.path_for(first.run_id) == restarted_store.path_for(restarted.run_id)
    assert restarted == first
    assert restarted.run_id == "stable-agentfield-run"
    assert len(list(tmp_path.glob("*.json"))) == 1


def test_foreign_query_cannot_reuse_persisted_run_id(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        research_run_module,
        "current_agentfield_identity",
        lambda: ("foreign-query-run", None),
    )
    store = ResearchRunStore(str(tmp_path))
    _, original = begin_research_run(
        "original query",
        store=store,
        source_revision=SOURCE_REVISION,
    )

    with pytest.raises(ValueError, match="different query"):
        begin_research_run(
            "foreign query",
            store=ResearchRunStore(str(tmp_path)),
            source_revision=SOURCE_REVISION,
        )

    assert store.load(original.run_id, source_revision=SOURCE_REVISION) == original


def test_invalid_run_id_cannot_escape_checkpoint_root(tmp_path: Path) -> None:
    store = ResearchRunStore(str(tmp_path))

    with pytest.raises(ValueError, match="unsafe run_id"):
        store.save(_run("../foreign-checkpoint"))

    assert not list(tmp_path.rglob("*.json"))


def test_stale_source_revision_is_rejected_after_restart(tmp_path: Path) -> None:
    store = ResearchRunStore(str(tmp_path))
    store.save(_run("stale-source-run"))

    with pytest.raises(StaleResearchRunError, match="belongs to source revision"):
        ResearchRunStore(str(tmp_path)).load(
            "stale-source-run",
            source_revision="foreign-revision",
        )


def test_crash_replay_inherits_evidence_without_duplicate_provider_calls(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    store = ResearchRunStore(str(tmp_path))
    store.save(
        _run(
            "crashed-source-run",
            stage="failed",
            checkpoint_seq=3,
            status="failed",
            payload={
                "research_package": {"package_id": "package-001"},
                "accepted_report_ids": ["report-c4-001"],
                "provider_call_ids": ["provider-001", "provider-001"],
            },
        )
    )
    monkeypatch.setattr(
        research_run_module,
        "current_agentfield_identity",
        lambda: ("crash-retry-run", "crashed-source-run"),
    )

    _, replay = begin_research_run(
        "verify durable research",
        store=ResearchRunStore(str(tmp_path)),
        source_revision=SOURCE_REVISION,
    )
    _, restarted_replay = begin_research_run(
        "verify durable research",
        store=ResearchRunStore(str(tmp_path)),
        source_revision=SOURCE_REVISION,
    )

    assert replay == restarted_replay
    assert replay.replay_source_run_id == "crashed-source-run"
    assert replay.stage == "research_package_ready"
    assert replay.payload["accepted_report_ids"] == ["report-c4-001"]
    assert recorded_provider_call_ids(replay) == ("provider-001",)
    assert sorted(path.name for path in tmp_path.glob("*.json")) == [
        "crash-retry-run.json",
        "crashed-source-run.json",
    ]


def test_stale_checkpoint_writer_cannot_overwrite_newer_persisted_evidence(
    tmp_path: Path,
) -> None:
    store = ResearchRunStore(str(tmp_path))
    original = _run(
        "stale-writer-run",
        payload={"accepted_report_ids": ["report-c4-001"]},
    )
    store.save(original)
    newer = checkpoint_research_run(
        store,
        original,
        stage="retrieval",
        expected_checkpoint_seq=0,
        evidence_summary={"fresh": True},
    )

    with pytest.raises(ResearchRunCheckpointError, match="checkpoint sequence is stale"):
        checkpoint_research_run(
            store,
            original,
            stage="ledger",
            expected_checkpoint_seq=0,
            evidence_summary={"stale": True},
        )

    persisted = store.load(original.run_id, source_revision=SOURCE_REVISION)
    assert persisted == newer
    assert persisted is not None
    assert persisted.evidence_summary == {"fresh": True}
    assert json.loads(store.path_for(original.run_id).read_text(encoding="utf-8"))[
        "checkpoint_seq"
    ] == 1
