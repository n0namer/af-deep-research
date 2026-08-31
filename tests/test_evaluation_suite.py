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


def test_source_reference_integrity_accepts_matching_retrieved_source_and_rejects_fabrication():
    from reasoners.deep_research_ext.evaluation import count_source_reference_integrity_failures
    research={"source_articles":[{"id":1,"url":"https://example.org/a","title":"Official A"}]}
    good={"source_notes":[{"citation_id":1,"url":"https://example.org/a","title":"Official A"}]}
    bad={"source_notes":[
        {"citation_id":1,"url":"https://example.org/a","title":"Invented title"},
        {"citation_id":2,"url":"https://example.org/missing","title":"Missing source"},
    ]}
    assert count_source_reference_integrity_failures(good,research)==0
    assert count_source_reference_integrity_failures(bad,research)==2


def test_rfc_offline_gate_requires_only_relevant_hard_signals():
    from reasoners.deep_research_ext.evaluation import evaluate_stored_semantic_snapshot, fixture_index
    fixture=fixture_index()["DR-P01"]
    result=evaluate_stored_semantic_snapshot(fixture,{
        "requirement_states":{"R1":"supported","R2":"supported"},
        "unsupported_material_claims":0,
        "fabricated_artifacts":0,
        "citation_entailment_ratio":1.0,
    })
    assert result.status=="PASS"
    assert result.missing_signals==()


def test_adversarial_offline_gate_requires_prompt_injection_signal():
    from reasoners.deep_research_ext.evaluation import evaluate_stored_semantic_snapshot, fixture_index
    fixture=fixture_index()["DR-P06"]
    result=evaluate_stored_semantic_snapshot(fixture,{
        "requirement_states":{"R1":"supported","R2":"supported"},
        "unsupported_material_claims":0,
        "fabricated_artifacts":0,
        "citation_entailment_ratio":1.0,
    })
    assert result.status=="EVIDENCE_MISSING"
    assert result.missing_signals==("prompt_injection_success",)


def test_frozen_core_has_24_cases_with_broad_domain_and_failure_mode_coverage():
    from reasoners.deep_research_ext.evaluation import frozen_core_fixtures
    fixtures=frozen_core_fixtures()
    assert len(fixtures)==24
    assert len({f.test_id for f in fixtures})==24
    assert len({f.domain for f in fixtures})>=8
    assert len({f.capability_class for f in fixtures})>=9


def test_all_24_frozen_core_cases_replay_to_expected_baseline_pass():
    from reasoners.deep_research_ext.evaluation import frozen_core_corpora, frozen_core_fixtures, replay_frozen_fixture
    fixtures={f.test_id:f for f in frozen_core_fixtures()}
    corpora=frozen_core_corpora()
    assert set(corpora)==set(fixtures)
    failures=[]
    for test_id in sorted(fixtures):
        result=replay_frozen_fixture(fixtures[test_id],corpora[test_id])
        if not result.gate.passed:
            failures.append((test_id,result.gate.failures,result.observation.requirement_states))
    assert failures==[]


def test_all_24_frozen_core_cases_fail_after_removing_decisive_admissible_evidence():
    from reasoners.deep_research_ext.evaluation import frozen_core_corpora, frozen_core_fixtures, remove_all_admissible_evidence, replay_frozen_fixture
    fixtures={f.test_id:f for f in frozen_core_fixtures()}
    corpora=frozen_core_corpora()
    false_passes=[]
    for test_id in sorted(fixtures):
        mutated=remove_all_admissible_evidence(corpora[test_id])
        result=replay_frozen_fixture(fixtures[test_id],mutated)
        if result.gate.passed:
            false_passes.append(test_id)
    assert false_passes==[]


def test_repeated_run_aggregation_measures_pass_state_source_and_latency_stability():
    from reasoners.deep_research_ext.evaluation import EvaluationRunRecord, aggregate_repeated_runs
    records=[
        EvaluationRunRecord('DR-P01','r1','PASS',(('R1','supported'),('R2','supported')),('S1','S2'),10.0),
        EvaluationRunRecord('DR-P01','r2','PASS',(('R1','supported'),('R2','supported')),('S1','S2'),12.0),
        EvaluationRunRecord('DR-P01','r3','FAIL',(('R1','supported'),('R2','unresolved')),('S1',),20.0),
    ]
    summary=aggregate_repeated_runs(records)
    assert summary.repetitions==3
    assert summary.pass_count==2
    assert summary.pass_rate==0.6667
    assert summary.requirement_state_stability==0.6667
    assert summary.source_set_stability==0.6667
    assert summary.latency_p50_seconds==12.0
    assert summary.latency_p95_seconds==19.2


def test_repeated_run_aggregation_rejects_mixed_fixture_records():
    from reasoners.deep_research_ext.evaluation import EvaluationRunRecord, aggregate_repeated_runs
    records=[
        EvaluationRunRecord('DR-P01','r1','PASS',(),(),1.0),
        EvaluationRunRecord('DR-P02','r2','PASS',(),(),1.0),
    ]
    try:
        aggregate_repeated_runs(records)
    except ValueError as exc:
        assert 'one fixture' in str(exc)
    else:
        raise AssertionError('mixed fixture records accepted')


def test_holdout_lane_is_separate_from_24_case_development_core():
    from reasoners.deep_research_ext.evaluation import frozen_core_fixtures, holdout_fixtures
    core_ids={f.test_id for f in frozen_core_fixtures()}
    holdout=holdout_fixtures()
    assert len(holdout)==6
    assert all(f.test_id.startswith('DR-H') for f in holdout)
    assert core_ids.isdisjoint({f.test_id for f in holdout})


def test_all_holdout_cases_replay_to_expected_pass_and_fail_when_decisive_evidence_removed():
    from reasoners.deep_research_ext.evaluation import holdout_corpora, holdout_fixtures, remove_all_admissible_evidence, replay_frozen_fixture
    fixtures={f.test_id:f for f in holdout_fixtures()}
    corpora=holdout_corpora()
    assert set(fixtures)==set(corpora)
    for test_id in sorted(fixtures):
        baseline=replay_frozen_fixture(fixtures[test_id],corpora[test_id])
        assert baseline.gate.passed is True, test_id
        mutated=replay_frozen_fixture(fixtures[test_id],remove_all_admissible_evidence(corpora[test_id]))
        assert mutated.gate.passed is False, test_id
