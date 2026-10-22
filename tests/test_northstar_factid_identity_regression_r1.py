import asyncio
from dataclasses import dataclass, replace
from types import SimpleNamespace

from reasoners.deep_research_ext.verification_bridge import verify_ledger_claims


@dataclass(frozen=True)
class SourceDouble:
    source_id: int
    url: str
    content_hash: str


@dataclass(frozen=True)
class ClaimDouble:
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
class LedgerDouble:
    sources: tuple[SourceDouble, ...]
    claims: tuple[ClaimDouble, ...]

    def model_copy(self, *, update):
        return replace(self, **update)


@dataclass(frozen=True)
class AssessmentDouble:
    fact_id: str
    source_id: int | None
    is_allowed: bool = True
    is_verified: bool = True
    is_source_supported: bool = True
    disagreement_score: float = 0.0


def run(coroutine):
    return asyncio.run(coroutine)


def make_fixture(count=1):
    sources = tuple(
        SourceDouble(
            source_id=index,
            url=f"https://example.org/source-{index}",
            content_hash=f"sha256:source-{index}",
        )
        for index in range(1, count + 1)
    )
    claims = tuple(
        ClaimDouble(
            claim_id=f"fact-{index}",
            text=f"Claim {index}",
            source_id=index,
        )
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
    return LedgerDouble(sources=sources, claims=claims), package


def test_exact_fact_and_source_owner_preserves_valid_evidence():
    ledger, package = make_fixture()

    async def adjudicator(batch, strictness, **kwargs):
        return SimpleNamespace(
            assessments=[AssessmentDouble(batch[0].fact_id, batch[0].source_id)]
        )

    updated = run(
        verify_ledger_claims(
            ledger=ledger,
            research_package=package,
            source_strictness="verified-only",
            adjudicator=adjudicator,
        )
    )

    assert updated.claims[0].status == "verified"
    assert updated.claims[0].support_state == "source_entailed"
    assert updated.claims[0].text == ledger.claims[0].text


def test_same_fact_from_wrong_source_owner_abstains():
    ledger, package = make_fixture()

    async def adjudicator(batch, strictness, **kwargs):
        return SimpleNamespace(
            assessments=[AssessmentDouble(batch[0].fact_id, source_id=999)]
        )

    updated = run(
        verify_ledger_claims(
            ledger=ledger,
            research_package=package,
            source_strictness="verified-only",
            adjudicator=adjudicator,
        )
    )

    assert updated.claims == ledger.claims


def test_duplicate_assessments_for_one_fact_abstain():
    ledger, package = make_fixture()

    async def adjudicator(batch, strictness, **kwargs):
        return SimpleNamespace(
            assessments=[
                AssessmentDouble(batch[0].fact_id, batch[0].source_id),
                AssessmentDouble(batch[0].fact_id, batch[0].source_id),
            ]
        )

    updated = run(
        verify_ledger_claims(
            ledger=ledger,
            research_package=package,
            source_strictness="verified-only",
            adjudicator=adjudicator,
        )
    )

    assert updated.claims == ledger.claims


def test_partial_batch_crash_abstains_then_clean_replay_succeeds():
    ledger, package = make_fixture(count=26)
    calls = 0

    async def crashing_adjudicator(batch, strictness, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise RuntimeError("simulated second-batch crash")
        return SimpleNamespace(
            assessments=[
                AssessmentDouble(fact.fact_id, fact.source_id)
                for fact in batch
            ]
        )

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
        return SimpleNamespace(
            assessments=[
                AssessmentDouble(fact.fact_id, fact.source_id)
                for fact in batch
            ]
        )

    after_replay = run(
        verify_ledger_claims(
            ledger=ledger,
            research_package=package,
            source_strictness="verified-only",
            adjudicator=replay_adjudicator,
        )
    )

    assert all(claim.status == "pending" for claim in ledger.claims)
    assert all(claim.status == "verified" for claim in after_replay.claims)
