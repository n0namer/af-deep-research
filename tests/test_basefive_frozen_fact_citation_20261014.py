import asyncio
from dataclasses import dataclass, replace
from types import SimpleNamespace

from reasoners.deep_research_ext.verification_bridge import (
    ADJUDICATION_BATCH_SIZE,
    verify_ledger_claims,
)


@dataclass(frozen=True)
class Source:
    source_id: int
    url: str
    content_hash: str


@dataclass(frozen=True)
class Claim:
    claim_id: str
    text: str
    source_id: int
    status: str = "pending"
    support_state: str = "unknown"
    admissible: bool = False
    source_verified: bool = False
    disagreement_score: float = 0.0

    def model_copy(self, *, update):
        return replace(self, **update)


@dataclass(frozen=True)
class Ledger:
    sources: tuple[Source, ...]
    claims: tuple[Claim, ...]

    def model_copy(self, *, update):
        return replace(self, **update)


@dataclass(frozen=True)
class Assessment:
    fact_id: str
    source_id: int | None
    is_allowed: bool = True
    is_verified: bool = True
    is_source_supported: bool = True
    disagreement_score: float = 0.0


def run(coroutine):
    return asyncio.run(coroutine)


def fixture(count=26):
    sources = tuple(
        Source(index, f"https://example.org/source-{index}", f"sha256:source-{index}")
        for index in range(1, count + 1)
    )
    claims = tuple(
        Claim(f"fact-{index}", f"Claim {index}", index)
        for index in range(1, count + 1)
    )
    package = {
        "source_articles": [
            {
                "id": source.source_id,
                "url": source.url,
                "content_hash": source.content_hash,
                "content": f"Evidence for claim {source.source_id}",
            }
            for source in sources
        ]
    }
    return Ledger(sources, claims), package


def verify(adjudicator):
    ledger, package = fixture()
    return ledger, run(
        verify_ledger_claims(
            ledger=ledger,
            research_package=package,
            source_strictness="verified-only",
            adjudicator=adjudicator,
        )
    )


def passing_assessments(batch):
    return [Assessment(fact.fact_id, fact.source_id) for fact in batch]


def test_positive_frozen_citation_preserves_each_fact_source_owner():
    async def adjudicator(batch, strictness, **kwargs):
        return _result(passing_assessments(batch))

    ledger, updated = verify(adjudicator)

    assert ADJUDICATION_BATCH_SIZE == 25
    assert len(updated.claims) == 26
    assert all(claim.status == "verified" for claim in updated.claims)
    assert all(claim.support_state == "source_entailed" for claim in updated.claims)
    assert all(claim.source_verified for claim in updated.claims)
    assert ledger.claims[0].status == "pending"


def test_foreign_fact_id_abstains_without_partial_credit():
    async def adjudicator(batch, strictness, **kwargs):
        assessments = passing_assessments(batch)
        if batch[0].fact_id == "fact-1":
            assessments[0] = Assessment("foreign-fact", batch[0].source_id)
        return _result(assessments)

    ledger, updated = verify(adjudicator)

    assert updated.claims[0] == ledger.claims[0]
    assert all(claim.status == "verified" for claim in updated.claims[1:])


def test_wrong_source_owner_abstains_without_partial_credit():
    async def adjudicator(batch, strictness, **kwargs):
        assessments = [
            Assessment(fact.fact_id, 999 if fact.fact_id == "fact-13" else fact.source_id)
            for fact in batch
        ]
        return _result(assessments)

    ledger, updated = verify(adjudicator)

    assert updated.claims[12] == ledger.claims[12]
    assert all(
        claim.status == "verified"
        for index, claim in enumerate(updated.claims)
        if index != 12
    )


def test_duplicate_assessment_abstains_without_partial_credit():
    async def adjudicator(batch, strictness, **kwargs):
        assessments = passing_assessments(batch)
        if batch[0].fact_id == "fact-1":
            assessments.append(Assessment("fact-1", batch[0].source_id))
        return _result(assessments)

    ledger, updated = verify(adjudicator)

    assert updated.claims[0] == ledger.claims[0]
    assert all(claim.status == "verified" for claim in updated.claims[1:])


def test_crash_then_restart_abstains_then_replays_cleanly():
    ledger, package = fixture()
    calls = 0

    async def crashing_adjudicator(batch, strictness, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise RuntimeError("simulated second-batch crash")
        return SimpleNamespace(assessments=passing_assessments(batch))

    after_crash = run(
        verify_ledger_claims(
            ledger=ledger,
            research_package=package,
            source_strictness="verified-only",
            adjudicator=crashing_adjudicator,
        )
    )
    assert after_crash.claims == ledger.claims

    async def replay_adjudicator(batch, strictness, **kwargs):
        return SimpleNamespace(assessments=passing_assessments(batch))

    after_restart = run(
        verify_ledger_claims(
            ledger=ledger,
            research_package=package,
            source_strictness="verified-only",
            adjudicator=replay_adjudicator,
        )
    )
    assert all(claim.status == "verified" for claim in after_restart.claims)
    assert all(claim.status == "pending" for claim in ledger.claims)


def _result(assessments):
    return SimpleNamespace(assessments=assessments)
