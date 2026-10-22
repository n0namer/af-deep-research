"""The production bootstrap stage must round-trip through the durable checkpoint API."""
import pytest
from reasoners.deep_research_ext.research_run import (
    ResearchRunStore, ResearchRunCheckpointError, begin_research_run,
    checkpoint_research_run, resume_research_run,
)

def test_bootstrap_contract_ready_stage_persists_and_resumes(tmp_path):
    store, run = begin_research_run(
        "Which RFC specifies HTTP/3?", store=ResearchRunStore(str(tmp_path))
    )
    ready = checkpoint_research_run(
        store, run, stage="contract_ready",
        payload={"answer_contract": {"query": "Which RFC specifies HTTP/3?"}},
    )
    assert ready.checkpoint_seq == 1
    saved, trace = resume_research_run(store, run.run_id)
    assert saved.stage == "contract_ready"
    assert saved.checkpoint_seq == 1
    assert trace["next_stage"] == "research"

def test_unknown_bootstrap_stage_stays_fail_closed(tmp_path):
    store, run = begin_research_run("question", store=ResearchRunStore(str(tmp_path)))
    with pytest.raises(ResearchRunCheckpointError, match="unknown checkpoint stage"):
        checkpoint_research_run(store, run, stage="unrecognised_future_stage")
