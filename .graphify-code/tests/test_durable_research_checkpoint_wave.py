import json

import pytest

from reasoners.deep_research_ext.research_run import (
    ResearchRunCheckpointError,
    ResearchRunStore,
    StaleResearchRunError,
    begin_research_run,
    checkpoint_research_run,
    provider_call_already_recorded,
    resume_research_run,
)


def test_restart_resumes_only_missing_gap_and_preserves_conflict_terminal_state(tmp_path):
    store = ResearchRunStore(str(tmp_path))
    _, run = begin_research_run("protocol query", store=store, source_revision="src-v1")

    run = checkpoint_research_run(
        store,
        run,
        stage="query",
        source_revision="src-v1",
        payload={"provider_call_ids": ["query-1"]},
    )
    run = checkpoint_research_run(
        store,
        run,
        stage="retrieval",
        source_ids=("S1",),
        open_gap_ids=("gap-2",),
        payload={"provider_call_ids": ["query-1", "retrieve-gap-1"]},
    )
    run = checkpoint_research_run(
        store,
        run,
        stage="ledger",
        conflicts=("claim-1-vs-claim-2",),
        payload={"provider_call_ids": ["query-1", "retrieve-gap-1"]},
    )

    reloaded, plan = resume_research_run(store, run.run_id, source_revision="src-v1")
    assert reloaded.checkpoint_seq == 3
    assert plan["next_stage"] == "coverage"
    assert plan["missing_gap_ids"] == ("gap-2",)
    assert plan["provider_call_ids"] == ("query-1", "retrieve-gap-1")
    assert plan["conflicts"] == ("claim-1-vs-claim-2",)
    assert provider_call_already_recorded(reloaded, "retrieve-gap-1")
    assert not provider_call_already_recorded(reloaded, "retrieve-gap-2")

    run = checkpoint_research_run(
        store,
        reloaded,
        stage="coverage",
        open_gap_ids=(),
        payload={
            "provider_call_ids": ["query-1", "retrieve-gap-1", "retrieve-gap-2"],
        },
    )
    run = checkpoint_research_run(store, run, stage="final_review")
    run = checkpoint_research_run(store, run, stage="completed", status="completed")

    terminal, terminal_plan = resume_research_run(store, run.run_id, source_revision="src-v1")
    assert terminal.stage == "completed"
    assert terminal.status == "completed"
    assert terminal.conflicts == ("claim-1-vs-claim-2",)
    assert terminal_plan["terminal"] is True
    assert terminal_plan["missing_gap_ids"] == ()
    assert terminal_plan["provider_call_ids"][-1] == "retrieve-gap-2"


def test_stale_revision_and_corrupt_checkpoint_fail_closed(tmp_path):
    store = ResearchRunStore(str(tmp_path))
    _, run = begin_research_run("revisioned query", store=store, source_revision="src-v1")
    checkpoint_research_run(store, run, stage="query", source_revision="src-v1")

    with pytest.raises(StaleResearchRunError):
        resume_research_run(store, run.run_id, source_revision="src-v2")

    checkpoint_path = store.path_for(run.run_id)
    checkpoint_path.write_text("{not-json", encoding="utf-8")
    with pytest.raises(ResearchRunCheckpointError, match="corrupt checkpoint"):
        store.load(run.run_id)


def test_stale_sequence_cannot_overwrite_newer_checkpoint(tmp_path):
    store = ResearchRunStore(str(tmp_path))
    _, run = begin_research_run("sequence query", store=store, source_revision="src-v1")
    current = checkpoint_research_run(store, run, stage="query", expected_checkpoint_seq=0)
    checkpoint_research_run(store, current, stage="retrieval", expected_checkpoint_seq=1)

    with pytest.raises(ResearchRunCheckpointError, match="sequence is stale"):
        checkpoint_research_run(store, current, stage="ledger", expected_checkpoint_seq=0)

    loaded = store.load(run.run_id)
    assert loaded is not None
    assert loaded.stage == "retrieval"
    assert loaded.checkpoint_seq == 2


def test_checkpoint_json_contains_source_revision_and_stage_history(tmp_path):
    store = ResearchRunStore(str(tmp_path))
    _, run = begin_research_run("receipt query", store=store, source_revision="src-v9")
    run = checkpoint_research_run(store, run, stage="query")
    raw = json.loads(store.path_for(run.run_id).read_text(encoding="utf-8"))

    assert raw["source_revision"] == "src-v9"
    assert raw["stage_history"] == ["started", "query"]
