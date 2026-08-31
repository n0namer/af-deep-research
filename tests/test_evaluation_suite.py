from reasoners.deep_research_ext.evaluation import EvalObservation, evaluate_hard_gates, fixture_index, pilot_fixtures


def test_pilot_eval_suite_has_heterogeneous_capability_coverage():
    fixtures = pilot_fixtures()
    assert len(fixtures) == 6
    assert len({f.domain for f in fixtures}) == 6
    assert len({f.capability_class for f in fixtures}) == 6
    assert set(fixture_index()) == {f"DR-P0{i}" for i in range(1, 7)}


def test_hard_gate_accepts_explicit_unresolved_and_contradicted_states():
    fixture = fixture_index()["DR-P05"]
    result = evaluate_hard_gates(
        fixture,
        EvalObservation(requirement_states={"R1": "supported", "R2": "unresolved"}),
    )
    assert result.passed is True
    assert result.requirement_coverage_ratio == 1.0
    assert result.failures == ()


def test_hard_gate_fails_closed_on_unsupported_claim_or_wrong_requirement_state():
    fixture = fixture_index()["DR-P04"]
    result = evaluate_hard_gates(
        fixture,
        EvalObservation(
            requirement_states={"R1": "supported", "R2": "unresolved"},
            unsupported_material_claims=1,
            citation_entailment_ratio=0.9,
        ),
    )
    assert result.passed is False
    assert result.requirement_coverage_ratio == 0.5
    assert any("R1:" in failure for failure in result.failures)
    assert "unsupported_material_claims=1" in result.failures
    assert "citation_entailment_ratio=0.900000" in result.failures


def test_frozen_rfc_anchor_replays_to_pass_from_primary_evidence():
    from reasoners.deep_research_ext.evaluation import fixture_index, pilot_frozen_corpora, replay_frozen_fixture
    fixture = fixture_index()["DR-P01"]
    corpus = pilot_frozen_corpora()["DR-P01"]
    result = replay_frozen_fixture(fixture, corpus)
    assert result.gate.passed is True
    assert result.observation.requirement_states == {"R1": "supported", "R2": "supported"}
    assert result.used_document_ids == ("RFC9000-primary",)


def test_evidence_removal_mutation_forces_unresolved_and_gate_failure():
    from reasoners.deep_research_ext.evaluation import fixture_index, mutate_corpus_remove_documents, pilot_frozen_corpora, replay_frozen_fixture
    fixture = fixture_index()["DR-P01"]
    corpus = mutate_corpus_remove_documents(pilot_frozen_corpora()["DR-P01"], ["RFC9000-primary"])
    result = replay_frozen_fixture(fixture, corpus)
    assert result.gate.passed is False
    assert result.observation.requirement_states == {"R1": "unresolved", "R2": "unresolved"}
    assert result.used_document_ids == ()


def test_frozen_primary_snapshot_hash_is_stable():
    from reasoners.deep_research_ext.evaluation import _sha256_text, pilot_frozen_corpora
    doc = pilot_frozen_corpora()["DR-P01"].documents[0]
    assert doc.content_sha256 == _sha256_text(doc.content)
    assert doc.source_url == "https://www.rfc-editor.org/rfc/rfc9000.txt"
    assert "Request for Comments: 9000" in doc.content
    assert "May 2021" in doc.content


def test_all_six_pilot_frozen_corpora_replay_to_expected_gate_pass():
    from reasoners.deep_research_ext.evaluation import fixture_index, pilot_frozen_corpora, replay_frozen_fixture
    fixtures = fixture_index()
    corpora = pilot_frozen_corpora()
    assert set(corpora) == set(fixtures) == {f"DR-P0{i}" for i in range(1, 7)}
    results = {test_id: replay_frozen_fixture(fixtures[test_id], corpora[test_id]) for test_id in sorted(fixtures)}
    assert all(result.gate.passed for result in results.values())
    assert results["DR-P02"].observation.requirement_states == {"R1": "supported", "R2": "contradicted"}
    assert results["DR-P03"].observation.requirement_states == {"R1": "supported", "R2": "supported"}
    assert results["DR-P04"].observation.requirement_states == {"R1": "contradicted", "R2": "unresolved"}
    assert results["DR-P05"].observation.requirement_states == {"R1": "supported", "R2": "unresolved"}
    assert results["DR-P06"].observation.requirement_states == {"R1": "supported", "R2": "supported"}


def test_each_pilot_has_a_causal_evidence_removal_mutation_that_fails_closed():
    from reasoners.deep_research_ext.evaluation import fixture_index, mutate_corpus_remove_documents, pilot_frozen_corpora, replay_frozen_fixture
    fixtures = fixture_index()
    corpora = pilot_frozen_corpora()
    removals = {
        "DR-P01": ["RFC9000-primary"],
        "DR-P02": ["SCI-study-b"],
        "DR-P03": ["STATE-current"],
        "DR-P04": ["HIST-primary"],
        "DR-P05": ["BIZ-official-a", "BIZ-official-b"],
        "DR-P06": ["PROD-primary"],
    }
    for test_id, document_ids in removals.items():
        mutated = mutate_corpus_remove_documents(corpora[test_id], document_ids)
        result = replay_frozen_fixture(fixtures[test_id], mutated)
        assert result.gate.passed is False, test_id


def test_provenance_and_adversarial_documents_cannot_substitute_for_primary_evidence():
    from reasoners.deep_research_ext.evaluation import fixture_index, mutate_corpus_remove_documents, pilot_frozen_corpora, replay_frozen_fixture
    fixture = fixture_index()["DR-P06"]
    corpus = mutate_corpus_remove_documents(pilot_frozen_corpora()["DR-P06"], ["PROD-primary"])
    result = replay_frozen_fixture(fixture, corpus)
    assert result.gate.passed is False
    assert result.used_document_ids == ()
    assert result.observation.requirement_states == {"R1": "unresolved", "R2": "unresolved"}


def test_offline_semantic_snapshot_passes_only_when_all_hard_signals_are_present():
    from reasoners.deep_research_ext.evaluation import evaluate_stored_semantic_snapshot, fixture_index
    fixture=fixture_index()["DR-P01"]
    snapshot={
        "requirement_states":{"R1":"supported","R2":"supported"},
        "unsupported_material_claims":0,
        "fabricated_artifacts":0,
        "citation_entailment_ratio":1.0,
        "silent_contradiction_loss":0,
        "false_premise_adoption":0,
        "prompt_injection_success":0,
    }
    result=evaluate_stored_semantic_snapshot(fixture,snapshot)
    assert result.status=="PASS"
    assert result.failures==()
    assert result.missing_signals==()


def test_offline_semantic_snapshot_is_evidence_missing_not_false_pass_when_signals_absent():
    from reasoners.deep_research_ext.evaluation import evaluate_stored_semantic_snapshot, fixture_index
    fixture=fixture_index()["DR-P01"]
    result=evaluate_stored_semantic_snapshot(
        fixture,
        {"requirement_states":{"R1":"supported","R2":"supported"},"unsupported_material_claims":0},
    )
    assert result.status=="EVIDENCE_MISSING"
    assert "fabricated_artifacts" in result.missing_signals
    assert "citation_entailment_ratio" in result.missing_signals


def test_offline_semantic_snapshot_fails_on_wrong_requirement_state_even_with_missing_signals():
    from reasoners.deep_research_ext.evaluation import evaluate_stored_semantic_snapshot, fixture_index
    fixture=fixture_index()["DR-P01"]
    result=evaluate_stored_semantic_snapshot(
        fixture,
        {"requirement_states":{"R1":"unresolved","R2":"supported"}},
    )
    assert result.status=="FAIL"
    assert any(item.startswith("R1:") for item in result.failures)


def test_research_run_snapshot_offline_scoring_reads_persisted_semantic_snapshot():
    from types import SimpleNamespace
    from reasoners.deep_research_ext.evaluation import evaluate_research_run_snapshot, fixture_index
    fixture=fixture_index()["DR-P01"]
    run=SimpleNamespace(payload={"semantic_snapshot":{
        "requirement_states":{"R1":"supported","R2":"supported"},
        "unsupported_material_claims":0,
        "fabricated_artifacts":0,
        "citation_entailment_ratio":1.0,
        "silent_contradiction_loss":0,
        "false_premise_adoption":0,
        "prompt_injection_success":0,
    }})
    result=evaluate_research_run_snapshot(fixture,run)
    assert result.status=="PASS"


def test_research_run_snapshot_offline_scoring_requires_snapshot_presence():
    from types import SimpleNamespace
    from reasoners.deep_research_ext.evaluation import evaluate_research_run_snapshot, fixture_index
    result=evaluate_research_run_snapshot(fixture_index()["DR-P01"],SimpleNamespace(payload={}))
    assert result.status=="EVIDENCE_MISSING"
    assert result.missing_signals==("semantic_snapshot",)
