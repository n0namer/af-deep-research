"""Independent r24 acceptance oracle for real search federation contracts.

This file intentionally exercises the public provider/federation boundaries and
uses deterministic transports/stubs so acceptance does not depend on credentials.
"""
from __future__ import annotations

import importlib

import pytest

from skills.search.base import SearchProvider, SearchResponse, SearchResult
from skills.search.federated import federated_search, search_with_providers
from skills.search.fusion import fuse_search_responses


class StubProvider(SearchProvider):
    def __init__(self, name: str, outcome):
        self._name = name
        self.outcome = outcome

    @property
    def name(self) -> str:
        return self._name

    @property
    def api_key_env_var(self) -> str:
        return "R24_UNUSED_KEY"

    def is_available(self) -> bool:
        return True

    async def search(self, query: str) -> SearchResponse:
        if isinstance(self.outcome, BaseException):
            raise self.outcome
        return self.outcome


def response(provider: str, url: str, content: str = "source-bound evidence") -> SearchResponse:
    return SearchResponse(
        provider=provider,
        query_used="r24",
        results=[SearchResult(title=provider, url=url, content=content)],
        total_results=1,
    )


@pytest.mark.asyncio
async def test_baseline_two_provider_federation_preserves_independent_provenance():
    first = StubProvider("jina", response("jina", "https://one.example/spec"))
    second = StubProvider("tavily", response("tavily", "https://two.example/spec"))

    result = await search_with_providers("r24", [first, second])

    assert result.provider == "federated"
    assert result.providers_used == ["jina", "tavily"]
    assert {p for item in result.results for p in item.retrieval_providers} == {
        "jina", "tavily"
    }


@pytest.mark.asyncio
async def test_forced_single_provider_baseline_does_not_claim_federation():
    provider = StubProvider("jina", response("jina", "https://one.example/spec"))

    result = await search_with_providers("r24", [provider])

    assert result.provider == "federated"
    assert result.providers_used == ["jina"]
    assert result.results[0].retrieval_providers == ["jina"]


@pytest.mark.asyncio
@pytest.mark.parametrize("status", [429, 503])
async def test_http_failure_falls_back_to_healthy_provider_without_transport_details(status):
    failed = StubProvider("unhealthy", RuntimeError(f"HTTP {status}: secret-token"))
    healthy = StubProvider("healthy", response("healthy", "https://healthy.example/spec"))

    result = await search_with_providers("r24", [failed, healthy])

    assert result.providers_used == ["healthy"]
    assert result.provider_errors == {"unhealthy": "RuntimeError"}
    assert "secret-token" not in repr(result)


@pytest.mark.asyncio
async def test_no_source_or_all_provider_failure_fails_closed():
    with pytest.raises(RuntimeError, match="All federated search providers failed"):
        await search_with_providers(
            "r24",
            [
                StubProvider("jina", RuntimeError("HTTP 503")),
                StubProvider("tavily", RuntimeError("HTTP 429")),
            ],
        )


def test_duplicate_canonical_url_is_not_independent_evidence():
    first = response(
        "jina", "https://source.example/report/?utm_source=mail#section"
    )
    second = response("tavily", "https://source.example/report")
    result = fuse_search_responses([first, second])

    assert len(result.results) == 1
    assert result.results[0].canonical_url == "https://source.example/report"
    assert result.results[0].retrieval_providers == ["jina", "tavily"]
    assert result.results[0].provider_ranks == {"jina": 1, "tavily": 1}


def test_invalid_jina_url_fails_closed_without_fabricating_identity():
    jina = importlib.import_module("skills.search.jina")

    with pytest.raises(ValueError, match="absolute HTTPS URL"):
        jina._parse_result(
            {"title": "unattributable", "url": "not-a-url", "content": "payload"}
        )
