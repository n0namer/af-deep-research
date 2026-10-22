"""Native C4 release-gate checks for grounded research restart and fencing.

These tests exercise the repository's real filesystem/DTO implementations. They do
not replace the provider or pipeline with mocks; external network/provider calls
are intentionally outside this deterministic release-gate boundary.
"""

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
from reasoners.deep_research_ext.verified_pipeline import (
    DurableVerifiedSourceReportStore,
    GroundedFact,
    VerifiedSourceReportError,
    build_grounded_verified_report,
    persist_grounded_verified_report,
    resume_grounded_verified_report,
)


SOURCE_SHA = "a" * 64
SOURCE_REVISION = "source-revision-r29"
OWNER = "release-gate-owner"


def test_real_question_research_report_trace_and_restart(tmp_path: Path):
    store = ResearchRunStore(str(tmp_path / "runs"))
    run_store, run = begin_research_run(
        "How does grounded research restart safely?",
        store=store,
        source_revision=SOURCE_REVISION,
        source_owner=OWNER,
    )

    checkpoint = checkpoint_research_run(
        run_store,
        run,
        stage="research_package_ready",
        source_ids=("source-1",),
        payload={
            "research_package": {"source_articles": [{"id": "source-1"}]},
            "provider_call_ids": ["provider-call-1"],
        },
    )
    checkpoint = checkpoint_research_run(
        run_store,
        checkpoint,
        stage="completed",
        status="completed",
        expected_checkpoint_seq=1,
        evidence_ids=("evidence-1",),
        payload={"report": {"trace_id": "trace-1"}},
    )

    resumed, trace = resume_research_run(
        run_store, run.run_id, source_revision=SOURCE_REVISION, source_owner=OWNER
    )
    assert resumed.checkpoint_seq == 2
    assert trace["terminal"] is True
    assert trace["provider_call_ids"] == ("provider-call-1",)
    assert trace["evidence_ids"] == ("evidence-1",)
    assert trace["report"] == {"trace_id": "trace-1"}

    report_store = DurableVerifiedSourceReportStore()
    report = build_grounded_verified_report(
        report_id="report-1",
        query=run.query,
        source_revision=SOURCE_REVISION,
        source_owner=OWNER,
        source_file_sha256=SOURCE_SHA,
        facts=[
            GroundedFact(
                fact_id="fact-1",
                source_id="source-1",
                source_sha256=SOURCE_SHA,
            )
        ],
        payload={"run_id": run.run_id, "trace_id": "trace-1"},
    )
    persisted, changed, effect = persist_grounded_verified_report(
        report_store,
        report,
        owner=OWNER,
        effect_id="terminal-effect-1",
    )
    assert changed is True
    assert effect is True
    assert report_store.effect_count() == 1

    replayed = resume_grounded_verified_report(
        report_store,
        persisted.report_id,
        owner=OWNER,
        source_file_sha256=SOURCE_SHA,
    )
    assert replayed.report_id == "report-1"
    assert replayed.dto_version == "r10"
    assert replayed.payload["run_id"] == run.run_id


def test_restart_rejects_stale_source_revision(tmp_path: Path):
    store = ResearchRunStore(str(tmp_path / "runs"))
    _, run = begin_research_run(
        "revision fence", store=store, source_revision=SOURCE_REVISION, source_owner=OWNER
    )
    with pytest.raises(StaleResearchRunError):
        resume_research_run(store, run.run_id, source_revision="stale-revision")


def test_restart_rejects_stale_checkpoint_sequence(tmp_path: Path):
    store = ResearchRunStore(str(tmp_path / "runs"))
    _, run = begin_research_run(
        "sequence fence", store=store, source_revision=SOURCE_REVISION, source_owner=OWNER
    )
    current = checkpoint_research_run(store, run, stage="query")
    with pytest.raises(ResearchRunCheckpointError, match="sequence is stale"):
        checkpoint_research_run(
            store, run, stage="retrieval", expected_checkpoint_seq=0
        )
    assert current.checkpoint_seq == 1


def test_report_restart_rejects_wrong_owner_and_source_sha():
    report_store = DurableVerifiedSourceReportStore()
    report = build_grounded_verified_report(
        report_id="report-fence",
        query="report fencing",
        source_revision=SOURCE_REVISION,
        source_owner=OWNER,
        source_file_sha256=SOURCE_SHA,
        facts=[{"fact_id": "fact-1", "source_id": "source-1", "source_sha256": SOURCE_SHA}],
        payload={"answer": "grounded"},
    )
    persist_grounded_verified_report(report_store, report, owner=OWNER)

    with pytest.raises(VerifiedSourceReportError, match="source owner"):
        resume_grounded_verified_report(
            report_store, report.report_id, owner="wrong-owner", source_file_sha256=SOURCE_SHA
        )
    with pytest.raises(VerifiedSourceReportError, match="source file SHA"):
        resume_grounded_verified_report(
            report_store, report.report_id, owner=OWNER, source_file_sha256="b" * 64
        )


def test_grounded_report_rejects_duplicate_fact_ids():
    with pytest.raises(VerifiedSourceReportError, match="unique fact_id"):
        build_grounded_verified_report(
            report_id="report-invalid",
            query="invalid grounded report",
            source_revision=SOURCE_REVISION,
            source_owner=OWNER,
            source_file_sha256=SOURCE_SHA,
            facts=[
                {"fact_id": "same", "source_id": "source-1", "source_sha256": SOURCE_SHA},
                {"fact_id": "same", "source_id": "source-1", "source_sha256": SOURCE_SHA},
            ],
            payload={},
        )
