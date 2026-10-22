import pytest

from reasoners.deep_research_ext.verification_bridge import validate_fact_ownership


def test_accepts_fact_owned_by_declared_source():
    validate_fact_ownership(
        fact_id="claim-1",
        source_id=7,
        claim_source_id=7,
        eligible_source_ids={7},
    )


@pytest.mark.parametrize(
    ("fact_id", "source_id", "claim_source_id", "eligible"),
    [
        ("claim-1", 7, 8, {7, 8}),  # cross-source ownership
        ("claim-1", 7, 7, {8}),  # undeclared source
        ("", 7, 7, {7}),  # missing fact identity
    ],
)
def test_rejects_provenance_mismatches(fact_id, source_id, claim_source_id, eligible):
    with pytest.raises(ValueError):
        validate_fact_ownership(
            fact_id=fact_id,
            source_id=source_id,
            claim_source_id=claim_source_id,
            eligible_source_ids=eligible,
        )


def test_rejects_boolean_source_id():
    with pytest.raises(ValueError):
        validate_fact_ownership(
            fact_id="claim-1",
            source_id=True,
            claim_source_id=1,
            eligible_source_ids={1},
        )
