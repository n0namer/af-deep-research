"""Cross-run source ownership and citation-contamination acceptance checks.

These tests exercise the real persistence/replay boundaries, not mocks of them.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from reasoners.deep_research_ext.research_run import (
    ResearchRunCheckpointError,
    ResearchRunStore,
    StaleResearchRunError,
    begin_research_run,
    checkpoint_research_run,
)
from reasoners.deep_research_ext.verified_pipeline import (
    DurableVerifiedSourceReportStore,
    VerifiedSourceReportError,
    build_grounded_verified_report,
    persist_grounded_verified_report,
    resume_grounded_verified_report,
)


ROOT = Path(__file__).resolve().parents[1]
RESEARCH_SOURCE = ROOT / "reasoners/deep_research_ext/research_run.py"
REPORT_SOURCE = ROOT / "reasoners/deep_research_ext/verified_pipeline.py"
SOURCE_REVISION = "current-source-r29"
SOURCE_OWNER = "run-owner-a"
SOURCE_SHA = hashlib.sha256(REPORT_SOURCE.read_bytes()).hexdigest()
FACT_SHA = "a" * 64


def _candidate(*, owner: str = SOURCE_OWNER, revision: int = 1, source_sha: str = SOURCE_SHA):
    return build_grounded_verified_report(
        report_id="report-r29",
        query="cross-run source ownership",
        source_revision=SOURCE_REVISION,
        source_owner=owner,
        source_file_sha256=source_sha,
        facts=[{"fact_id": "fact-1", "source_id": "source-1", "source_sha256": FACT_SHA}],
        payload={"claim": "only source-1 supports this claim"},
        revision=revision,
    )


def test_real_source_bound_report_survives_persist_and_resume(tmp_path):
    store = DurableVerifiedSourceReportStore()
    candidate = _candidate()
    persisted, changed, effect_applied = persist_grounded_verified_report(
        store, candidate, owner=SOURCE_OWNER, effect_id="terminal-effect-r29"
    )

    resumed = resume_grounded_verified_report(
        store, persisted.report_id, owner=SOURCE_OWNER, source_file_sha256=SOURCE_SHA
    )

    assert changed is True
    assert effect_applied is True
    assert resumed == persisted
    assert store.effect_count() == 1
    assert len(SOURCE_SHA) == 64
    assert len(hashlib.sha256(RESEARCH_SOURCE.read_bytes()).hexdigest()) == 64


def test_cross_owner_report_is_rejected_before_persistence():
    with pytest.raises(VerifiedSourceReportError, match="source owner"):
        persist_grounded_verified_report(
            DurableVerifiedSourceReportStore(), _candidate(owner="owner-a"),
            owner="owner-b",
        )


def test_cross_source_sha_resume_is_rejected():
    store = DurableVerifiedSourceReportStore()
    persist_grounded_verified_report(store, _candidate(), owner=SOURCE_OWNER)

    with pytest.raises(VerifiedSourceReportError, match="source file SHA"):
        resume_grounded_verified_report(
            store, "report-r29", owner=SOURCE_OWNER, source_file_sha256="b" * 64
        )


def test_citation_identity_contamination_is_rejected_on_replay():
    store = DurableVerifiedSourceReportStore()
    persist_grounded_verified_report(store, _candidate(), owner=SOURCE_OWNER)

    contaminated = build_grounded_verified_report(
        report_id="report-r29",
        query="cross-run source ownership",
        source_revision=SOURCE_REVISION,
        source_owner=SOURCE_OWNER,
        source_file_sha256=SOURCE_SHA,
        facts=[{"fact_id": "fact-evil", "source_id": "source-evil", "source_sha256": FACT_SHA}],
        payload={"claim": "contaminated source"},
        revision=2,
    )

    with pytest.raises(VerifiedSourceReportError, match="identity"):
        persist_grounded_verified_report(store, contaminated, owner=SOURCE_OWNER)


def test_stale_checkpoint_revision_and_owner_are_rejected(tmp_path):
    store = ResearchRunStore(str(tmp_path))
    _, run = begin_research_run(
        "cross-run source ownership", store=store,
        source_revision=SOURCE_REVISION, source_owner=SOURCE_OWNER,
    )
    checkpointed = checkpoint_research_run(
        store, run, stage="research_package_ready",
        source_revision=SOURCE_REVISION, source_owner=SOURCE_OWNER,
        payload={"research_package": {"source_articles": []}},
    )

    with pytest.raises(StaleResearchRunError):
        store.load(checkpointed.run_id, source_revision="different-source")

    with pytest.raises(ResearchRunCheckpointError, match="source owner"):
        checkpoint_research_run(
            store, checkpointed, stage="evidence_verified",
            source_revision=SOURCE_REVISION, source_owner="owner-b",
            expected_checkpoint_seq=checkpointed.checkpoint_seq,
        )
