import asyncio
from dataclasses import dataclass, replace
from types import SimpleNamespace

import pytest

from reasoners.deep_research_ext.verification_bridge import verify_ledger_claims


@dataclass(frozen=True)
class SourceDtoDouble:
    source_id: int
    url: str
    content_hash: str


@dataclass(frozen=True)
class ClaimDtoDouble:
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
class LedgerDtoDouble:
    sources: tuple[SourceDtoDouble, ...]
    claims: tuple[ClaimDtoDouble, ...]

    def model_copy(self, *, update):
        return replace(self, **update)


@dataclass(frozen=True)
class AssessmentDtoDouble:
    fact_id: str
    is_allowed: bool = True
    is_verified: bool = True
    is_source_supported: bool = True
    disagreement_score: float = 0.0
    source_id: int | None = None


def run(coroutine):
    return asyncio.run(coroutine)


def make_ledger():
    return LedgerDtoDouble(
        sources=(
            SourceDtoDouble(
                source_id=7,
                url="https://example.org/native-source",
                content_hash="sha256:native-source-v1",
            ),
        ),
        claims=(
            ClaimDtoDouble(
                claim_id="fact-native-7",
                text="The bounded native claim.",
                source_id=7,
            ),
        ),
    )


def make_package(*, source_id=7, url="https://example.org/native-source", content_hash="sha256:native-source-v1"):
    return {
        "source_articles": [
            {
                "id": source_id,
                "url": url,
                "content_hash": content_hash,
                "content": "The bounded native claim is directly supported.",
            }
        ]
    }


def test_native_positive_path_preserves_fact_and_source_identity():
    ledger = make_ledger()
    captured = {}

    async def adjudicator(batch, strictness, **kwargs):
        captured["batch"] = batch
        captured["strictness"] = strictness
        captured["kwargs"] = kwargs
        return SimpleNamespace(
            assessments=[
                AssessmentDtoDouble(
                    fact_id=batch[0].fact_id,
                    source_id=batch[0].source_id,
                )
            ]
        )

    updated = run(
        verify_ledger_claims(
            ledger=ledger,
            research_package=make_package(),
            source_strictness="verified-only",
            adjudicator=adjudicator,
        )
    )

    assert len(captured["batch"]) == 1
    fact = captured["batch"][0]
    assert fact.fact_id == "fact-native-7"
    assert fact.source_id == 7
    assert fact.content == "The bounded native claim."
    assert fact.source_text == "The bounded native claim is directly supported."
    assert captured["strictness"] == "verified-only"
    assert updated.claims[0].text == ledger.claims[0].text
    assert updated.claims[0].status == "verified"
    assert updated.claims[0].support_state == "source_entailed"
    assert updated.claims[0].source_verified is True


def test_foreign_fact_id_and_injected_citation_do_not_credit_native_claim():
    ledger = make_ledger()

    async def adversarial_adjudicator(batch, strictness, **kwargs):
        return SimpleNamespace(
            assessments=[
                AssessmentDtoDouble(fact_id="foreign-fact", source_id=999),
                AssessmentDtoDouble(fact_id="", source_id=batch[0].source_id),
            ]
        )

    updated = run(
        verify_ledger_claims(
            ledger=ledger,
            research_package=make_package(),
            source_strictness="verified-only",
            adjudicator=adversarial_adjudicator,
        )
    )

    assert updated.claims == ledger.claims
    assert updated.claims[0].status == "pending"
    assert updated.claims[0].support_state == "unknown"


def test_noneligible_stale_source_abstains_before_adjudication():
    ledger = make_ledger()
    calls = 0

    async def must_not_run(batch, strictness, **kwargs):
        nonlocal calls
        calls += 1
        return SimpleNamespace(assessments=[])

    with pytest.raises(
        ValueError,
        match="No eligible evidence remains for verified ledger adjudication",
    ):
        run(
            verify_ledger_claims(
                ledger=ledger,
                research_package=make_package(content_hash="sha256:stale-restart-copy"),
                source_strictness="verified-only",
                adjudicator=must_not_run,
            )
        )

    assert calls == 0
    assert ledger.claims[0].status == "pending"
    assert ledger.claims[0].support_state == "unknown"


def test_crash_then_restart_retry_does_not_credit_failed_attempt():
    ledger = make_ledger()

    async def crashed_adjudicator(batch, strictness, **kwargs):
        raise RuntimeError("simulated adjudicator crash before durable result")

    after_crash = run(
        verify_ledger_claims(
            ledger=ledger,
            research_package=make_package(),
            source_strictness="verified-only",
            adjudicator=crashed_adjudicator,
        )
    )

    assert after_crash.claims == ledger.claims

    async def restarted_adjudicator(batch, strictness, **kwargs):
        return SimpleNamespace(
            assessments=[
                AssessmentDtoDouble(
                    fact_id=batch[0].fact_id,
                    source_id=batch[0].source_id,
                )
            ]
        )

    after_restart = run(
        verify_ledger_claims(
            ledger=ledger,
            research_package=make_package(),
            source_strictness="verified-only",
            adjudicator=restarted_adjudicator,
        )
    )

    assert ledger.claims[0].status == "pending"
    assert after_restart.claims[0].status == "verified"
    assert after_restart.claims[0].text == ledger.claims[0].text


def test_same_fact_id_with_wrong_source_identity_must_abstain():
    ledger = make_ledger()

    async def source_swapped_adjudicator(batch, strictness, **kwargs):
        return SimpleNamespace(
            assessments=[
                AssessmentDtoDouble(
                    fact_id=batch[0].fact_id,
                    source_id=999,
                )
            ]
        )

    updated = run(
        verify_ledger_claims(
            ledger=ledger,
            research_package=make_package(),
            source_strictness="verified-only",
            adjudicator=source_swapped_adjudicator,
        )
    )

    assert updated.claims == ledger.claims


def test_duplicate_same_fact_id_injected_assessment_must_abstain():
    ledger = make_ledger()

    async def duplicate_injection_adjudicator(batch, strictness, **kwargs):
        return SimpleNamespace(
            assessments=[
                AssessmentDtoDouble(
                    fact_id=batch[0].fact_id,
                    is_allowed=False,
                    is_verified=False,
                    is_source_supported=False,
                    source_id=batch[0].source_id,
                ),
                AssessmentDtoDouble(
                    fact_id=batch[0].fact_id,
                    source_id=batch[0].source_id,
                ),
            ]
        )

    updated = run(
        verify_ledger_claims(
            ledger=ledger,
            research_package=make_package(),
            source_strictness="verified-only",
            adjudicator=duplicate_injection_adjudicator,
        )
    )

    assert updated.claims == ledger.claims
