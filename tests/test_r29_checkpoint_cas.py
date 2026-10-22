import pytest
from dataclasses import replace

from reasoners.deep_research_ext.research_run import (
    ResearchRunCheckpointError,
    ResearchRunStore,
    StaleResearchRunError,
    begin_research_run,
    checkpoint_research_run,
    resume_research_run,
)


def _store(tmp_path):
    store, run = begin_research_run(
        "checkpoint fencing",
        store=ResearchRunStore(str(tmp_path)),
        source_revision="rev-1",
        source_owner="owner-a",
    )
    return store, run


def test_checkpoint_accepts_matching_owner_and_sequence(tmp_path):
    store, run = _store(tmp_path)

    updated = checkpoint_research_run(
        store,
        run,
        stage="retrieval",
        expected_checkpoint_seq=0,
        source_owner="owner-a",
    )

    assert updated.checkpoint_seq == 1
    assert resume_research_run(store, run.run_id, source_owner="owner-a")[0] == updated


def test_checkpoint_rejects_foreign_requested_owner(tmp_path):
    store, run = _store(tmp_path)

    with pytest.raises(ResearchRunCheckpointError, match="source owner"):
        checkpoint_research_run(
            store,
            run,
            stage="retrieval",
            expected_checkpoint_seq=0,
            source_owner="owner-b",
        )


def test_checkpoint_rejects_stale_sequence_after_another_writer(tmp_path):
    store, run = _store(tmp_path)
    current = checkpoint_research_run(
        store, run, stage="retrieval", expected_checkpoint_seq=0, source_owner="owner-a"
    )

    with pytest.raises(ResearchRunCheckpointError, match="sequence is stale"):
        checkpoint_research_run(
            store,
            run,
            stage="ledger",
            expected_checkpoint_seq=0,
            source_owner="owner-a",
        )

    assert store.load(run.run_id).checkpoint_seq == current.checkpoint_seq


def test_checkpoint_rejects_stale_unowned_snapshot_after_owner_claim(tmp_path):
    store, run = begin_research_run(
        "checkpoint fencing",
        store=ResearchRunStore(str(tmp_path)),
        source_revision="rev-1",
    )
    claimed = checkpoint_research_run(
        store,
        run,
        stage="retrieval",
        expected_checkpoint_seq=0,
        source_owner="owner-a",
    )
    stale_snapshot = replace(run, checkpoint_seq=claimed.checkpoint_seq)

    with pytest.raises(ResearchRunCheckpointError, match="owner mismatch"):
        checkpoint_research_run(
            store,
            stale_snapshot,
            stage="ledger",
            expected_checkpoint_seq=claimed.checkpoint_seq,
            source_owner="owner-a",
        )


def test_resume_rejects_foreign_source_revision(tmp_path):
    store, run = _store(tmp_path)

    with pytest.raises(StaleResearchRunError, match="source revision"):
        resume_research_run(store, run.run_id, source_revision="rev-2", source_owner="owner-a")
