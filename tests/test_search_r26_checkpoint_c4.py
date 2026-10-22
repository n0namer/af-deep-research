"""Independent R26 checkpoint/replay coverage against native Python APIs."""
from __future__ import annotations
import hashlib
from pathlib import Path
import pytest
from reasoners.deep_research_ext.research_run import (ResearchRunCheckpointError, ResearchRunStore, StaleResearchRunError, begin_research_run, checkpoint_research_run, resume_research_run)
from reasoners.deep_research_ext.verified_pipeline import (DurableVerifiedSourceReportStore, GroundedFact, VerifiedSourceReportError, build_grounded_verified_report, persist_grounded_verified_report, resume_grounded_verified_report)

SOURCE_SHA = hashlib.sha256(b"r26-source-checkpoint-fixture").hexdigest()

def _grounded(owner="owner-a", revision=1):
    return build_grounded_verified_report(report_id="report-r26", query="checkpoint replay", source_revision="source-r26", source_owner=owner, source_file_sha256=SOURCE_SHA, facts=(GroundedFact("fact-1", "source-1", SOURCE_SHA),), payload={"answer": "source-grounded"}, revision=revision)

def test_native_positive_checkpoint_replay_and_idempotent_effect(tmp_path: Path):
    store = ResearchRunStore(str(tmp_path / "runs"))
    _, run = begin_research_run("checkpoint replay", store=store, source_revision="source-r26", source_owner="owner-a")
    run = checkpoint_research_run(store, run, stage="research_package_ready", expected_checkpoint_seq=0, payload={"research_package": {"source_articles": [{"id": "source-1"}]}})
    resumed, report = resume_research_run(store, run.run_id, source_revision="source-r26", source_owner="owner-a")
    assert resumed.checkpoint_seq == 1
    assert report["source_revision"] == "source-r26"
    reports = DurableVerifiedSourceReportStore()
    canonical, changed, applied = persist_grounded_verified_report(reports, _grounded(), owner="owner-a", effect_id="effect-1")
    assert (canonical.report_id, changed, applied) == ("report-r26", True, True)
    _, changed_again, applied_again = persist_grounded_verified_report(reports, _grounded(), owner="owner-a", effect_id="effect-1")
    assert (changed_again, applied_again, reports.effect_count()) == (False, False, 1)
    assert resume_grounded_verified_report(reports, "report-r26", owner="owner-a", source_file_sha256=SOURCE_SHA).source_owner == "owner-a"

def test_foreign_owner_is_refused_for_checkpoint_and_report():
    store = ResearchRunStore()
    _, run = begin_research_run("owner gate", store=store, source_revision="source-r26", source_owner="owner-a")
    with pytest.raises(ResearchRunCheckpointError, match="source owner"): checkpoint_research_run(store, run, stage="query", source_owner="owner-b")
    reports = DurableVerifiedSourceReportStore()
    with pytest.raises(VerifiedSourceReportError, match="source owner"): persist_grounded_verified_report(reports, _grounded(), owner="owner-b")

def test_stale_source_revision_is_refused_on_restart(tmp_path: Path):
    store = ResearchRunStore(str(tmp_path / "runs"))
    _, run = begin_research_run("source gate", store=store, source_revision="source-r26", source_owner="owner-a")
    with pytest.raises(StaleResearchRunError, match="source revision"): resume_research_run(store, run.run_id, source_revision="source-drift")

def test_stale_checkpoint_sequence_and_interruption_do_not_mutate_state(tmp_path: Path):
    store = ResearchRunStore(str(tmp_path / "runs"))
    _, run = begin_research_run("cas", store=store, source_revision="source-r26")
    updated = checkpoint_research_run(store, run, stage="query", expected_checkpoint_seq=0)
    with pytest.raises(ResearchRunCheckpointError, match="sequence"): checkpoint_research_run(store, run, stage="retrieval", expected_checkpoint_seq=0)
    assert store.load(run.run_id).checkpoint_seq == updated.checkpoint_seq
    reports = DurableVerifiedSourceReportStore()
    with pytest.raises(Exception) as interrupted: persist_grounded_verified_report(reports, _grounded(), owner="owner-a", cancellation=lambda: True)
    assert interrupted.type.__name__ == "CancelledError"
    assert reports.load("report-r26") is None
