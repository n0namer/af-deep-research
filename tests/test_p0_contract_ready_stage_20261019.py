"""Regression: the live verified research bootstrap must persist contract_ready."""

from reasoners.deep_research_ext.research_run import (
    ResearchRunStore, begin_research_run, checkpoint_research_run,
    resume_research_run,
)


def test_contract_ready_checkpoint_persists_and_resumes(tmp_path):
    store, run = begin_research_run(
        "Which RFC specifies HTTP/3?",
        store=ResearchRunStore(str(tmp_path)),
        source_revision="source-p0-20261019",
        source_owner="p0-integration",
    )
    ready = checkpoint_research_run(
        store, run, stage="contract_ready",
        payload={"answer_contract": {"query": run.query}},
    )
    resumed, trace = resume_research_run(
        store, run.run_id, source_revision="source-p0-20261019",
        source_owner="p0-integration",
    )
    assert ready.checkpoint_seq == 1
    assert resumed.stage == "contract_ready"
    assert trace["next_stage"] == "research"
