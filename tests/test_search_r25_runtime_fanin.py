"""Independent r25 runtime fan-in tests over the real search interfaces.

The default suite uses deterministic transport-boundary doubles: provider objects
remain the real adapter/registry interfaces while network calls are replaced at
the async provider boundary. True requests are opt-in via R25_TRUE_REQUESTS=1
and remain bounded by R25_TRUE_REQUEST_TIMEOUT_SECONDS (default 5 seconds).
"""
from __future__ import annotations

import asyncio
import importlib
import os
from unittest.mock import AsyncMock

import pytest

from skills.search.base import SearchProvider, SearchResponse, SearchResult
from skills.search.federated import (
    federated_search,
    search_with_providers,
    select_federated_providers,
)
from skills.search.fusion import fuse_search_responses
from skills.search.registry import get_provider


FOUR_ADAPTERS = ("jina", "tavily", "firecrawl", "serper")


def _response(provider: str, url: str, content: str = "r25 source") -> SearchResponse:
    return SearchResponse(
        provider=provider,
        query_used="r25",
        results=[SearchResult(title=provider, url=url, content=content)],
        total_results=1,
    )


class BoundaryProvider(SearchProvider):
    """Real SearchProvider contract with a deterministic transport boundary."""

    def __init__(self, name: str, result=None, error: BaseException | None = None):
        self._name = name
        self.result = result
        self.error = error
        self.calls = 0

    @property
    def name(self) -> str:
        return self._name

    @property
    def api_key_env_var(self) -> str:
        return f"R25_{self._name.upper()}_KEY"

    def is_available(self) -> bool:
        return True

    async def search(self, query: str) -> SearchResponse:
        self.calls += 1
        if self.error:
            raise self.error
        return self.result


def test_registry_exposes_four_real_provider_adapters():
    for name in FOUR_ADAPTERS:
        provider = get_provider(name)
        assert isinstance(provider, SearchProvider)
        assert provider.name == name


@pytest.mark.asyncio
async def test_explicit_single_selection_calls_only_selected_provider(monkeypatch):
    selected = BoundaryProvider("tavily", _response("tavily", "https://tavily.example/r25"))
    unselected = BoundaryProvider("jina", _response("jina", "https://jina.example/r25"))

    selected.search = AsyncMock(wraps=selected.search)
    unselected.search = AsyncMock(wraps=unselected.search)
    result = await search_with_providers("r25", [selected])

    assert result.provider == "federated"
    assert result.providers_used == ["tavily"]
    selected.search.assert_awaited_once_with("r25")
    unselected.search.assert_not_awaited()


def test_auto_federation_is_bounded_and_deduplicates_provider_names(monkeypatch):
    monkeypatch.setenv("SEARCH_PROVIDERS", "jina,tavily,jina,firecrawl,serper")
    monkeypatch.setenv("SEARCH_FEDERATED_MAX_PROVIDERS", "3")
    providers = select_federated_providers(
        [name for name in FOUR_ADAPTERS if name in {"jina", "tavily", "firecrawl", "serper"}]
    )
    assert len(providers) <= 3
    assert len({provider.name for provider in providers}) == len(providers)


@pytest.mark.asyncio
@pytest.mark.parametrize("status", [429, 503])
async def test_provider_outage_keeps_healthy_fallback_and_redacts_transport_error(status):
    failed = BoundaryProvider(
        "jina",
        error=RuntimeError(f"HTTP {status}: secret-token"),
    )
    healthy = BoundaryProvider("serper", _response("serper", "https://serper.example/r25"))

    result = await search_with_providers("r25", [failed, healthy])

    assert result.providers_used == ["serper"]
    assert result.provider_errors == {"jina": "RuntimeError"}
    assert "secret-token" not in repr(result)


def test_rrf_deduplicates_same_canonical_url_but_preserves_independent_provenance():
    result = fuse_search_responses(
        [
            _response("jina", "https://source.example/report/?utm_source=mail#part"),
            _response("tavily", "https://source.example/report"),
        ]
    )

    assert len(result.results) == 1
    item = result.results[0]
    assert item.canonical_url == "https://source.example/report"
    assert item.retrieval_providers == ["jina", "tavily"]
    assert item.provider_ranks == {"jina": 1, "tavily": 1}


def test_invalid_jina_urls_fail_closed():
    jina = importlib.import_module("skills.search.jina")
    with pytest.raises(ValueError, match="absolute HTTPS URL"):
        jina._parse_result({"title": "bad", "url": "http://not-https", "content": "x"})
    with pytest.raises(ValueError, match="absolute HTTPS URL"):
        jina._parse_result({"title": "bad", "url": "not-a-url", "content": "x"})


@pytest.mark.asyncio
async def test_all_provider_failure_fails_closed():
    with pytest.raises(RuntimeError, match="All federated search providers failed"):
        await search_with_providers(
            "r25",
            [
                BoundaryProvider("jina", error=RuntimeError("HTTP 503")),
                BoundaryProvider("tavily", error=RuntimeError("HTTP 429")),
            ],
        )


@pytest.mark.asyncio
async def test_opt_in_true_request_is_bounded_and_skipped_by_default():
    if os.getenv("R25_TRUE_REQUESTS") != "1":
        pytest.skip("set R25_TRUE_REQUESTS=1 to enable bounded provider requests")
    timeout = max(1, min(int(os.getenv("R25_TRUE_REQUEST_TIMEOUT_SECONDS", "5")), 10))
    provider = get_provider("jina")
    if provider is None or not provider.is_available():
        pytest.skip("Jina credentials are not configured")
    await asyncio.wait_for(provider.search("r25 bounded probe"), timeout=timeout)
