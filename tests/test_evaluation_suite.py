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
