from dataclasses import replace

import pytest

from reasoners.deep_research_ext.research_run import (
    ResearchRunCheckpointError,
    ResearchRunStore,
    StaleResearchRunError,
    begin_research_run,
    checkpoint_research_run,
    recorded_provider_call_ids,
    resume_research_run,
)


def test_native_checkpoint_pins_source_and_persists_provider_receipt(tmp_path):
    store, run = begin_research_run(
        "checkpoint provenance",
        store=ResearchRunStore(str(tmp_path)),
        source_revision="sha-c4-r9",
    )

    checkpointed = checkpoint_research_run(
        store,
        run,
        stage="retrieval",
        source_revision="sha-c4-r9",
        expected_checkpoint_seq=0,
        source_ids=("source-1",),
        payload={"provider_call_ids": ["provider-1"]},
    )

    loaded, resume = resume_research_run(
        store,
        checkpointed.run_id,
        source_revision="sha-c4-r9",
    )

    assert loaded.source_revision == "sha-c4-r9"
    assert loaded.source_ids == ("source-1",)
    assert resume["source_revision"] == "sha-c4-r9"
    assert resume["provider_call_ids"] == ("provider-1",)
    assert resume["terminal"] is False


def test_foreign_source_revision_fails_closed_without_loading_checkpoint(tmp_path):
    store, run = begin_research_run(
        "foreign source",
        store=ResearchRunStore(str(tmp_path)),
        source_revision="sha-c4-r9",
    )

    with pytest.raises(StaleResearchRunError, match="not 'sha-foreign'"):
        resume_research_run(store, run.run_id, source_revision="sha-foreign")


def test_stale_owner_and_sequence_replay_are_rejected(tmp_path):
    store, run = begin_research_run(
        "stale replay",
        store=ResearchRunStore(str(tmp_path)),
        source_revision="sha-c4-r9",
    )
    current = checkpoint_research_run(
        store,
        run,
        stage="retrieval",
        source_revision="sha-c4-r9",
        expected_checkpoint_seq=0,
    )

    with pytest.raises(ResearchRunCheckpointError, match="checkpoint sequence is stale"):
        checkpoint_research_run(
            store,
            replace(current, checkpoint_seq=0),
            stage="ledger",
            source_revision="sha-c4-r9",
        )


def test_restart_replay_deduplicates_provider_effects_and_preserves_fence(tmp_path):
    store, run = begin_research_run(
        "restart idempotency",
        store=ResearchRunStore(str(tmp_path)),
        source_revision="sha-c4-r9",
    )
    first = checkpoint_research_run(
        store,
        run,
        stage="retrieval",
        source_revision="sha-c4-r9",
        expected_checkpoint_seq=0,
        payload={"provider_call_ids": ["provider-1", "provider-1"]},
    )

    resumed, _ = resume_research_run(store, first.run_id, source_revision="sha-c4-r9")
    second = checkpoint_research_run(
        store,
        resumed,
        stage="ledger",
        source_revision="sha-c4-r9",
        expected_checkpoint_seq=1,
        payload={"provider_call_ids": ["provider-1", "provider-2"]},
    )

    assert recorded_provider_call_ids(second) == ("provider-1", "provider-2")
    assert second.checkpoint_seq == 2
    assert second.source_revision == "sha-c4-r9"
    with pytest.raises(ResearchRunCheckpointError, match="checkpoint sequence is stale"):
        checkpoint_research_run(
            store,
            first,
            stage="ledger",
            source_revision="sha-c4-r9",
        )
