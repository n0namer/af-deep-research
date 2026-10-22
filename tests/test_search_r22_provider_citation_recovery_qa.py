"""Independent r22 QA for provider recovery and native citation/report integrity.

The tests use public provider and verified-report boundaries. They intentionally
avoid patching production internals and preserve fail-closed behavior.
"""

import asyncio
import pytest

from reasoners.deep_research_ext.verified_pipeline import (
    DurableVerifiedSourceReportStore, GroundedFact, VerifiedSourceReport,
    VerifiedSourceReportError, build_grounded_verified_report,
    persist_grounded_verified_report, resume_grounded_verified_report,
)
from skills.search.base import SearchProvider, SearchResponse, SearchResult
from skills.search.federated import search_with_providers


class StubProvider(SearchProvider):
    def __init__(self, name, outcome):
        self._name, self.outcome = name, outcome
    @property
    def name(self): return self._name
    @property
    def api_key_env_var(self): return "R22_UNUSED_KEY"
    def is_available(self): return True
    async def search(self, query):
        if isinstance(self.outcome, BaseException): raise self.outcome
        return self.outcome


def response(provider, url="https://source.example/fact"):
    return SearchResponse(provider=provider, query_used="r22",
        results=[SearchResult(title=provider, url=url, content="current source")],
        total_results=1)


@pytest.mark.asyncio
@pytest.mark.parametrize("status", [429, 503])
async def test_http_provider_failures_are_isolated(status):
    result = await search_with_providers("r22", [
        StubProvider("unhealthy", RuntimeError(f"HTTP {status}")),
        StubProvider("healthy", response("healthy")),
    ])
    assert result.providers_used == ["healthy"]
    assert result.provider_errors == {"unhealthy": "RuntimeError"}
    assert result.results[0].retrieval_providers == ["healthy"]


@pytest.mark.asyncio
async def test_all_provider_outage_fails_closed_without_transport_details():
    secret = "r22-secret"
    with pytest.raises(RuntimeError) as error:
        await search_with_providers("r22", [
            StubProvider("alpha", RuntimeError(f"503 body {secret}")),
            StubProvider("beta", asyncio.TimeoutError(secret)),
        ])
    assert str(error.value) == "All federated search providers failed: alpha, beta"
    assert secret not in str(error.value)


def grounded(abstentions=("R2",)):
    return build_grounded_verified_report(
        report_id="report-r22", query="r22", source_revision="source-revision-1",
        source_owner="qa-owner", source_file_sha256="a" * 64,
        facts=[GroundedFact("fact-a", "source-a", "b" * 64)],
        payload={"claims": ["fact-a"]}, abstained_requirement_ids=abstentions)


def test_foreign_fact_or_source_ids_are_rejected_at_report_boundary():
    with pytest.raises(VerifiedSourceReportError, match="facts must reference declared source_ids"):
        VerifiedSourceReport(
            report_id="report-r22", query="r22", source_ids=("source-a",),
            revision=1, payload={},
            facts=(GroundedFact("fact-a", "foreign-source", "b" * 64),))
    with pytest.raises(VerifiedSourceReportError, match="facts must be a non-empty"):
        build_grounded_verified_report(
            report_id="report-r22", query="r22", source_revision="rev",
            source_owner="qa-owner", source_file_sha256="a" * 64,
            facts=[], payload={"claims": ["foreign-fact"]})


def test_partial_abstention_survives_persistence_and_restart():
    store = DurableVerifiedSourceReportStore()
    persisted, changed, effect = persist_grounded_verified_report(
        store, grounded(("R2", "R3")), owner="qa-owner", effect_id="terminal-r22")
    assert changed is True and effect is True
    assert persisted.abstained_requirement_ids == ("R2", "R3")
    resumed = resume_grounded_verified_report(
        store, "report-r22", owner="qa-owner", source_file_sha256="a" * 64)
    assert resumed.facts[0].source_id == "source-a"
    assert resumed.abstained_requirement_ids == ("R2", "R3")


def test_restart_rejects_foreign_owner_or_changed_source_fingerprint():
    store = DurableVerifiedSourceReportStore()
    persist_grounded_verified_report(store, grounded(), owner="qa-owner")
    with pytest.raises(VerifiedSourceReportError, match="source owner"):
        resume_grounded_verified_report(store, "report-r22",
            owner="foreign-owner", source_file_sha256="a" * 64)
    with pytest.raises(VerifiedSourceReportError, match="source file SHA"):
        resume_grounded_verified_report(store, "report-r22",
            owner="qa-owner", source_file_sha256="c" * 64)


def test_duplicate_terminal_effect_is_idempotent_but_stale_revision_is_rejected():
    store = DurableVerifiedSourceReportStore()
    candidate = grounded()
    persist_grounded_verified_report(store, candidate, owner="qa-owner", effect_id="terminal-r22")
    _, changed, effect = persist_grounded_verified_report(
        store, candidate, owner="qa-owner", effect_id="terminal-r22")
    assert changed is False and effect is False and store.effect_count() == 1
    stale = candidate.__class__(
        report_id=candidate.report_id, query=candidate.query,
        source_ids=candidate.source_ids, revision=3, payload=candidate.payload,
        source_revision=candidate.source_revision, source_owner=candidate.source_owner,
        source_file_sha256=candidate.source_file_sha256, facts=candidate.facts,
        abstained_requirement_ids=candidate.abstained_requirement_ids)
    with pytest.raises(VerifiedSourceReportError, match="revision"):
        persist_grounded_verified_report(store, stale, owner="qa-owner")
