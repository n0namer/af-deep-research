import asyncio
from dataclasses import dataclass, replace
from types import SimpleNamespace

from reasoners.deep_research_ext.verification_bridge import verify_ledger_claims


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


def test_long_bundle_preserves_all_valid_fact_and_source_owners():
    ledger, package = fixture()

    async def adjudicator(batch, strictness, **kwargs):
        return SimpleNamespace(
            assessments=[Assessment(fact.fact_id, fact.source_id) for fact in batch]
        )

    updated = run(
        verify_ledger_claims(
            ledger=ledger,
            research_package=package,
            source_strictness="verified-only",
            adjudicator=adjudicator,
        )
    )

    assert len(updated.claims) == 26
    assert all(claim.status == "verified" for claim in updated.claims)
    assert all(claim.support_state == "source_entailed" for claim in updated.claims)


def test_long_bundle_wrong_source_owner_abstains_without_partial_credit():
    ledger, package = fixture()

    async def adjudicator(batch, strictness, **kwargs):
        return SimpleNamespace(
            assessments=[
                Assessment(fact.fact_id, fact.source_id if fact.source_id != 13 else 999)
                for fact in batch
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

    assert updated.claims[12] == ledger.claims[12]
    assert all(
        claim.status == "verified"
        for index, claim in enumerate(updated.claims)
        if index != 12
    )


def test_long_bundle_duplicate_assessment_abstains_without_partial_credit():
    ledger, package = fixture()

    async def adjudicator(batch, strictness, **kwargs):
        assessments = [Assessment(fact.fact_id, fact.source_id) for fact in batch]
        if batch[0].fact_id == "fact-1":
            assessments.append(Assessment("fact-1", batch[0].source_id))
        return SimpleNamespace(assessments=assessments)

    updated = run(
        verify_ledger_claims(
            ledger=ledger,
            research_package=package,
            source_strictness="verified-only",
            adjudicator=adjudicator,
        )
    )

    assert updated.claims[0] == ledger.claims[0]
    assert all(claim.status == "verified" for claim in updated.claims[1:])


def test_duplicate_source_article_is_ambiguous_and_abstains():
    ledger, package = fixture()
    package["source_articles"].append(
        {
            "id": 7,
            "url": "https://example.org/other-source",
            "content_hash": "sha256:other-source",
            "content": "Conflicting evidence",
        }
    )
    captured = {}

    async def adjudicator(batch, strictness, **kwargs):
        captured["batch"] = batch
        return SimpleNamespace(
            assessments=[Assessment(fact.fact_id, fact.source_id) for fact in batch]
        )

    updated = run(
        verify_ledger_claims(
            ledger=ledger,
            research_package=package,
            source_strictness="verified-only",
            adjudicator=adjudicator,
        )
    )

    assert len(captured["batch"]) == 25
    assert updated.claims[6] == ledger.claims[6]
    assert all(claim.status == "verified" for claim in updated.claims[0:6])
    assert all(claim.status == "verified" for claim in updated.claims[7:])


def test_batch_crash_then_restart_replays_cleanly_without_failed_credit():
    ledger, package = fixture()
    calls = 0

    async def crashing_adjudicator(batch, strictness, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise RuntimeError("simulated second-batch crash")
        return SimpleNamespace(
            assessments=[Assessment(fact.fact_id, fact.source_id) for fact in batch]
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
            assessments=[Assessment(fact.fact_id, fact.source_id) for fact in batch]
        )

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
