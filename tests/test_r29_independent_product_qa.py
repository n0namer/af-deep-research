"""Independent r29 product QA for the source-bound research-run contract."""
from __future__ import annotations
import pytest
from reasoners.deep_research_ext.research_run import (
    ResearchRunCheckpointError, ResearchRunStore, StaleResearchRunError,
    begin_research_run, checkpoint_research_run, resume_research_run,
)

def test_real_run_checkpoint_and_resume_preserves_terminal_receipts(tmp_path):
    store = ResearchRunStore(str(tmp_path))
    _, run = begin_research_run("independent QA", store=store, source_revision="rev-a", source_owner="producer-a")
    checkpointed = checkpoint_research_run(
        store, run, stage="completed", status="completed", source_revision="rev-a",
        source_owner="producer-a", expected_checkpoint_seq=0,
        evidence_ids=("evidence-1",), payload={"terminal_receipt": "receipt-1"},
    )
    resumed, summary = resume_research_run(store, checkpointed.run_id, source_revision="rev-a", source_owner="producer-a")
    assert resumed.status == "completed"
    assert resumed.checkpoint_seq == 1
    assert summary["status"] == "completed"
    assert summary["evidence_ids"] == ("evidence-1",)
    assert summary["payload"]["terminal_receipt"] == "receipt-1"

def test_adversarial_run_id_traversal_is_rejected(tmp_path):
    store = ResearchRunStore(str(tmp_path))
    with pytest.raises(ValueError, match="unsafe run_id"):
        store.path_for("../escape")

def test_adversarial_stale_source_revision_cannot_resume(tmp_path):
    store = ResearchRunStore(str(tmp_path))
    _, run = begin_research_run("revision fence", store=store, source_revision="rev-current", source_owner="owner-a")
    with pytest.raises(StaleResearchRunError, match="source revision"):
        resume_research_run(store, run.run_id, source_revision="rev-old", source_owner="owner-a")

def test_adversarial_stale_checkpoint_sequence_cannot_overwrite(tmp_path):
    store = ResearchRunStore(str(tmp_path))
    _, run = begin_research_run("sequence fence", store=store, source_revision="rev-a", source_owner="owner-a")
    checkpointed = checkpoint_research_run(
        store, run, stage="retrieval", source_revision="rev-a",
        source_owner="owner-a", expected_checkpoint_seq=0,
    )
    with pytest.raises(ResearchRunCheckpointError, match="checkpoint sequence"):
        checkpoint_research_run(
            store, checkpointed, stage="ledger", source_revision="rev-a",
            source_owner="owner-a", expected_checkpoint_seq=0,
        )
