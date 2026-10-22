import pytest

from reasoners.deep_research_ext.evaluation import (
    evaluate_stored_semantic_snapshot,
    frozen_core_corpora,
    frozen_core_fixtures,
    holdout_corpora,
    holdout_fixtures,
    mutate_corpus_remove_documents,
    remove_all_admissible_evidence,
    replay_frozen_fixture,
)
from reasoners.deep_research_ext.research_run import (
    ResearchRunCheckpointError,
    ResearchRunStore,
    StaleResearchRunError,
    begin_research_run,
    checkpoint_research_run,
    resume_research_run,
)


def test_frozen_core_and_holdout_baselines_are_source_independent():
    core_fixtures = {fixture.test_id: fixture for fixture in frozen_core_fixtures()}
    core_corpora = frozen_core_corpora()
    holdout = holdout_fixtures()
    holdout_ids = {fixture.test_id for fixture in holdout}

    assert len(core_fixtures) == 24
    assert len(holdout) == 6
    assert holdout_ids.isdisjoint(core_fixtures)
    assert set(core_corpora) == set(core_fixtures)
    assert set(holdout_corpora()) == holdout_ids
    assert all(
        replay_frozen_fixture(core_fixtures[test_id], core_corpora[test_id]).gate.passed
        for test_id in sorted(core_fixtures)
    )
    assert all(
        replay_frozen_fixture(fixture, holdout_corpora()[fixture.test_id]).gate.passed
        for fixture in holdout
    )


def test_holdout_fails_closed_when_all_admissible_evidence_is_removed():
    corpora = holdout_corpora()

    failures = []
    for fixture in holdout_fixtures():
        result = replay_frozen_fixture(
            fixture,
            remove_all_admissible_evidence(corpora[fixture.test_id]),
        )
        if result.gate.passed:
            failures.append(fixture.test_id)

    assert failures == []


def test_holdout_fails_closed_when_one_decisive_source_is_mutated_away():
    fixture = next(item for item in holdout_fixtures() if item.test_id == "DR-H02")
    corpus = holdout_corpora()[fixture.test_id]
    decisive_ids = [document.document_id for document in corpus.documents if document.admissible]

    mutated = mutate_corpus_remove_documents(corpus, decisive_ids[:1])
    result = replay_frozen_fixture(fixture, mutated)

    assert result.gate.passed is False
    assert result.observation.requirement_states["R1"] == "unresolved"


def test_adversarial_holdout_requires_explicit_prompt_injection_signal():
    fixture = next(item for item in holdout_fixtures() if item.test_id == "DR-H04")
    result = evaluate_stored_semantic_snapshot(
        fixture,
        {
            "requirement_states": {"R1": "supported", "R2": "supported"},
            "unsupported_material_claims": 0,
            "fabricated_artifacts": 0,
            "citation_entailment_ratio": 1.0,
        },
    )

    assert result.status == "EVIDENCE_MISSING"
    assert result.missing_signals == ("prompt_injection_success",)


def test_checkpoint_restart_preserves_provider_ids_and_rejects_stale_writes(tmp_path):
    store = ResearchRunStore(str(tmp_path))
    _, run = begin_research_run(
        "longbundle holdout",
        store=store,
        source_revision="source-v1",
    )
    checkpointed = checkpoint_research_run(
        store,
        run,
        stage="retrieval",
        expected_checkpoint_seq=0,
        payload={"provider_call_ids": ["provider-1", "provider-1"]},
    )

    resumed, plan = resume_research_run(
        store,
        checkpointed.run_id,
        source_revision="source-v1",
    )

    assert resumed.checkpoint_seq == 1
    assert plan["provider_call_ids"] == ("provider-1",)
    assert plan["terminal"] is False
    with pytest.raises(ResearchRunCheckpointError, match="checkpoint sequence is stale"):
        checkpoint_research_run(
            store,
            run,
            stage="ledger",
            expected_checkpoint_seq=0,
        )
    with pytest.raises(StaleResearchRunError, match="not 'source-v2'"):
        resume_research_run(store, checkpointed.run_id, source_revision="source-v2")
