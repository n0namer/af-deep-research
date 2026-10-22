from __future__ import annotations

import json
from pathlib import Path

import pytest

from reasoners.deep_research_ext.research_run import (
    ResearchRun,
    ResearchRunCheckpointError,
    ResearchRunStore,
    StaleResearchRunError,
    begin_research_run,
    checkpoint_research_run,
    resume_research_run,
)

SOURCE_REVISION = "e10580c89eac7a4f6efb50c921ae9107ce8ad8dc"


def _completed_report(run_id: str = "durable-report") -> ResearchRun:
    return ResearchRun(
        run_id=run_id,
        query="durable report query",
        stage="completed",
        checkpoint_seq=2,
        status="completed",
        created_at=1.0,
        updated_at=2.0,
        source_revision=SOURCE_REVISION,
        stage_history=("started", "completed"),
        payload={
            "report": {"report_id": "report-001", "answer": "persisted"},
            "provider_call_ids": ["provider-1", "provider-1"],
        },
    )


def test_completed_report_survives_process_local_store_recreation(tmp_path: Path) -> None:
    first_process_store = ResearchRunStore(str(tmp_path))
    original = _completed_report()
    path = first_process_store.save(original)

    restarted_store = ResearchRunStore(str(tmp_path))
    loaded, plan = resume_research_run(
        restarted_store, original.run_id, source_revision=SOURCE_REVISION
    )

    assert path == tmp_path / "durable-report.json"
    assert loaded.payload["report"] == {"report_id": "report-001", "answer": "persisted"}
    assert plan["report"] == loaded.payload["report"]
    assert plan["terminal"] is True
    assert plan["provider_call_ids"] == ("provider-1",)
    assert list(tmp_path.glob("*.json")) == [path]


def test_report_is_not_claimed_durable_before_checkpoint(tmp_path: Path) -> None:
    store = ResearchRunStore(str(tmp_path))
    _, run = begin_research_run(
        "uncheckpointed report query", store=store, source_revision=SOURCE_REVISION
    )

    assert run.payload.get("report") is None
    assert resume_research_run(
        ResearchRunStore(str(tmp_path)), run.run_id, source_revision=SOURCE_REVISION
    )[1]["report"] is None


def test_corrupt_report_checkpoint_fails_closed(tmp_path: Path) -> None:
    store = ResearchRunStore(str(tmp_path))
    store.save(_completed_report())
    store.path_for("durable-report").write_text("{not-json", encoding="utf-8")

    with pytest.raises(ResearchRunCheckpointError, match="corrupt checkpoint"):
        store.load("durable-report")


def test_stale_source_revision_cannot_resume_report(tmp_path: Path) -> None:
    store = ResearchRunStore(str(tmp_path))
    store.save(_completed_report())

    with pytest.raises(StaleResearchRunError, match="belongs to source revision"):
        resume_research_run(store, "durable-report", source_revision="foreign-revision")


def test_stale_checkpoint_writer_cannot_overwrite_report(tmp_path: Path) -> None:
    store = ResearchRunStore(str(tmp_path))
    original = _completed_report()
    store.save(original)
    newer = checkpoint_research_run(
        store, original, stage="final_review", expected_checkpoint_seq=2,
        payload={"report": {"report_id": "report-002"}},
    )

    with pytest.raises(ResearchRunCheckpointError, match="checkpoint sequence is stale"):
        checkpoint_research_run(
            store, original, stage="failed", expected_checkpoint_seq=2,
            payload={"report": {"report_id": "forged"}},
        )

    assert store.load("durable-report", source_revision=SOURCE_REVISION) == newer
    assert json.loads(store.path_for("durable-report").read_text(encoding="utf-8"))["payload"]["report"]["report_id"] == "report-002"


def test_unsafe_report_run_id_cannot_escape_store(tmp_path: Path) -> None:
    store = ResearchRunStore(str(tmp_path))

    with pytest.raises(ValueError, match="unsafe run_id"):
        store.save(_completed_report("../outside"))

    assert not list(tmp_path.rglob("*.json"))
