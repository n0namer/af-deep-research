from types import SimpleNamespace

import pytest

from reasoners.deep_research_ext.synthesis_guard import has_source_entailed_support


def claim(source_id, support_state="source_entailed"):
    return SimpleNamespace(source_id=source_id, support_state=support_state)


def test_accepts_verified_claim_with_declared_source():
    assert has_source_entailed_support(claim("src-1"), {"src-1"})


@pytest.mark.parametrize(
    "candidate",
    [
        claim("missing-source"),
        claim("src-1", "model_inferred"),
        claim("src-1", "source_contradicted"),
    ],
    ids=["undeclared-source", "non-entailed-support", "contradicted-support"],
)
def test_rejects_claims_without_source_entailment(candidate):
    assert not has_source_entailed_support(candidate, {"src-1"})
