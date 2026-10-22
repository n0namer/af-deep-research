import asyncio
from dataclasses import dataclass, replace
from types import SimpleNamespace

import pytest

from reasoners.deep_research_ext.verification_bridge import verify_ledger_claims


@dataclass(frozen=True)
class Source:
    source_id: int
    url: str
    content_hash: str


@dataclass(frozen=True)
class Claim:
    claim_id: str
    source_id: int
    text: str
    status: str = "pending"
    support_state: str = "unverified"
    admissible: bool = False
    source_verified: bool = False
    disagreement_score: float = 0.0

    def model_copy(self, *, update):
        return replace(self, **update)


@dataclass(frozen=True)
class Ledger:
    sources: list
    claims: list

    def model_copy(self, *, update):
        return replace(self, **update)


def make_ledger(*, url="https://example.test/source", content_hash="hash-1"):
    return Ledger(
        sources=[Source(source_id=7, url=url, content_hash=content_hash)],
        claims=[Claim(claim_id="fact-7", source_id=7, text="The source supports this fact.")],
    )


def supported_assessment(*, source_id=7, fact_id="fact-7"):
    return SimpleNamespace(
        fact_id=fact_id,
        source_id=source_id,
        is_allowed=True,
        is_verified=True,
        is_source_supported=True,
        disagreement_score=0.0,
    )


def run_verification(**kwargs):
    return asyncio.run(verify_ledger_claims(**kwargs))


def test_unique_source_entailment_updates_claim():
    ledger = make_ledger()
    calls = []

    async def adjudicator(batch, strictness, **kwargs):
        calls.append((batch, strictness))
        return SimpleNamespace(assessments=[supported_assessment()])

    verified = run_verification(
        ledger=ledger,
        research_package={
            "source_articles": [
                {
                    "id": 7,
                    "url": "https://example.test/source",
                    "content_hash": "hash-1",
                    "content": "The source supports this fact.",
                }
            ]
        },
        source_strictness="verified-only",
        adjudicator=adjudicator,
    )

    assert len(calls) == 1
    assert calls[0][0][0].fact_id == "fact-7"
    assert calls[0][0][0].source_id == 7
    assert calls[0][1] == "verified-only"
    assert verified.claims[0].status == "verified"
    assert verified.claims[0].support_state == "source_entailed"


def test_duplicate_source_url_abstains_in_verified_only_mode():
    ledger = make_ledger()

    with pytest.raises(ValueError, match="No eligible evidence remains"):
        run_verification(
            ledger=ledger,
            research_package={
                "source_articles": [
                    {"id": 7, "url": "https://example.test/source", "content_hash": "hash-1", "content": "a"},
                    {"id": 8, "url": "https://example.test/source", "content_hash": "hash-2", "content": "b"},
                ]
            },
            source_strictness="verified-only",
        )


def test_source_mismatched_assessment_is_rejected_without_mutation():
    ledger = make_ledger()

    async def adjudicator(batch, strictness, **kwargs):
        return SimpleNamespace(assessments=[supported_assessment(source_id=999)])

    result = run_verification(
        ledger=ledger,
        research_package={
            "source_articles": [
                {
                    "id": 7,
                    "url": "https://example.test/source",
                    "content_hash": "hash-1",
                    "content": "The source supports this fact.",
                }
            ]
        },
        source_strictness="verified-only",
        adjudicator=adjudicator,
    )

    assert result.claims == ledger.claims
    assert result.claims[0].status == "pending"


def test_restart_retry_preserves_ledger_after_failure_then_verifies():
    ledger = make_ledger()
    attempts = 0

    async def adjudicator(batch, strictness, **kwargs):
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise RuntimeError("temporary adjudicator outage")
        return SimpleNamespace(assessments=[supported_assessment()])

    first = run_verification(
        ledger=ledger,
        research_package={
            "source_articles": [
                {
                    "id": 7,
                    "url": "https://example.test/source",
                    "content_hash": "hash-1",
                    "content": "The source supports this fact.",
                }
            ]
        },
        source_strictness="verified-only",
        adjudicator=adjudicator,
    )
    second = run_verification(
        ledger=first,
        research_package={
            "source_articles": [
                {
                    "id": 7,
                    "url": "https://example.test/source",
                    "content_hash": "hash-1",
                    "content": "The source supports this fact.",
                }
            ]
        },
        source_strictness="verified-only",
        adjudicator=adjudicator,
    )

    assert first is ledger
    assert first.claims == ledger.claims
    assert attempts == 2
    assert second.claims[0].status == "verified"
    assert second.claims[0].support_state == "source_entailed"
