import os
import subprocess
import sys
import textwrap

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
)


def test_real_child_process_kill_resumes_without_repeating_side_effects(tmp_path):
    root = tmp_path / "runs"
    child = textwrap.dedent(
        """
        import os
        import sys
        from reasoners.deep_research_ext.research_run import (
            ResearchRunStore, begin_research_run, checkpoint_research_run,
        )
        store = ResearchRunStore(sys.argv[1])
        store, run = begin_research_run("crash-resume", store=store, source_revision="src-1", source_owner="owner-a")
        checkpoint_research_run(
            store, run, stage="retrieval", source_revision="src-1", source_owner="owner-a",
            source_ids=("source-1",), evidence_ids=("evidence-1",),
            payload={"provider_call_ids": ["call-1"], "effect_ids": ["effect-1"]},
        )
        os.kill(os.getpid(), 9)
        """
    )
    completed = subprocess.run(
        [sys.executable, "-c", child, str(root)],
        capture_output=True,
        text=True,
    )
    assert completed.returncode == -9, completed.stderr

    store = ResearchRunStore(str(root))
    run_id = next(p.stem for p in root.glob("*.json"))
    run, resume = resume_research_run(store, run_id, source_revision="src-1", source_owner="owner-a")
    assert run.stage == "retrieval"
    assert resume["next_stage"] == "ledger"
    assert resume["provider_call_ids"] == ("call-1",)
    assert resume["evidence_ids"] == ("evidence-1",)

    resumed = checkpoint_research_run(
        store, run, stage="ledger", source_revision="src-1", source_owner="owner-a",
        expected_checkpoint_seq=1,
        evidence_ids=("evidence-1", "evidence-2"),
        payload={"provider_call_ids": ["call-1", "call-2"]},
    )
    assert resumed.checkpoint_seq == 2
    assert resumed.payload["provider_call_ids"] == ["call-1", "call-2"]
    assert resumed.evidence_ids == ("evidence-1", "evidence-2")


def test_stale_source_revision_is_rejected(tmp_path):
    store, run = begin_research_run("revision-bound", store=ResearchRunStore(str(tmp_path)), source_revision="src-1")
    with pytest.raises(StaleResearchRunError):
        resume_research_run(store, run.run_id, source_revision="src-2")


def test_stale_checkpoint_sequence_is_rejected(tmp_path):
    store, run = begin_research_run("sequence-bound", store=ResearchRunStore(str(tmp_path)))
    current = checkpoint_research_run(store, run, stage="retrieval", expected_checkpoint_seq=0)
    with pytest.raises(ResearchRunCheckpointError, match="sequence is stale"):
        checkpoint_research_run(store, run, stage="ledger", expected_checkpoint_seq=0)
    with pytest.raises(ResearchRunCheckpointError, match="sequence is stale"):
        checkpoint_research_run(store, current, stage="ledger", expected_checkpoint_seq=0)


def test_duplicate_terminal_effect_is_not_reapplied():
    store = DurableVerifiedSourceReportStore()
    candidate = build_grounded_verified_report(
        report_id="report-1",
        query="query",
        source_revision="src-1",
        source_owner="owner-a",
        source_file_sha256="a" * 64,
        facts=[GroundedFact("fact-1", "source-1", "b" * 64)],
        payload={"answer": "grounded"},
    )
    first = persist_grounded_verified_report(store, candidate, owner="owner-a", effect_id="terminal-effect")
    second = persist_grounded_verified_report(store, candidate, owner="owner-a", effect_id="terminal-effect")
    assert first[2] is True
    assert second[2] is False
    assert store.effect_count() == 1


def test_duplicate_report_revision_with_changed_payload_is_rejected():
    store = DurableVerifiedSourceReportStore()
    candidate = build_grounded_verified_report(
        report_id="report-2",
        query="query",
        source_revision="src-1",
        source_owner="owner-a",
        source_file_sha256="a" * 64,
        facts=[GroundedFact("fact-1", "source-1", "b" * 64)],
        payload={"answer": "grounded"},
    )
    persist_grounded_verified_report(store, candidate, owner="owner-a")
    conflicting = build_grounded_verified_report(
        report_id="report-2",
        query="query",
        source_revision="src-1",
        source_owner="owner-a",
        source_file_sha256="a" * 64,
        facts=[GroundedFact("fact-1", "source-1", "b" * 64)],
        payload={"answer": "different"},
    )
    with pytest.raises(VerifiedSourceReportError, match="revision payload conflicts"):
        persist_grounded_verified_report(store, conflicting, owner="owner-a")
