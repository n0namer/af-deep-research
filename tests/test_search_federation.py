"""Routing and federation contract tests for skills.search."""

import importlib

import pytest

from skills.search.base import SearchProvider, SearchResponse, SearchResult
from skills.search.federated import search_with_providers


class StubProvider(SearchProvider):
    def __init__(self, provider_name, response=None, error=None):
        self._provider_name = provider_name
        self.response = response
        self.error = error

    @property
    def name(self):
        return self._provider_name

    @property
    def api_key_env_var(self):
        return "UNUSED_TEST_KEY"

    def is_available(self):
        return True

    async def search(self, query):
        if self.error:
            raise self.error
        return self.response


def response(provider, url, query="federated routing"):
    return SearchResponse(
        provider=provider,
        query_used=query,
        results=[SearchResult(title=provider, url=url, content="evidence")],
        total_results=1,
    )


@pytest.fixture
def search_module():
    return importlib.import_module("skills.search")


@pytest.mark.asyncio
async def test_federated_mode_routes_two_available_providers_and_records_them(
    monkeypatch, search_module
):
    first = StubProvider("brave", response("brave", "https://example.test/a"))
    second = StubProvider("tavily", response("tavily", "https://example.test/b"))
    monkeypatch.setenv("SEARCH_MODE", "federated")
    monkeypatch.delenv("SEARCH_PROVIDER", raising=False)
    monkeypatch.setattr(search_module, "select_federated_providers", lambda: [first, second])

    result = await search_module.search("federated routing")

    assert result.provider == "federated"
    assert result.providers_used == ["brave", "tavily"]


@pytest.mark.asyncio
async def test_auto_mode_federates_when_two_providers_are_available(
    monkeypatch, search_module
):
    first = StubProvider("brave", response("brave", "https://example.test/a"))
    second = StubProvider("tavily", response("tavily", "https://example.test/b"))
    monkeypatch.setenv("SEARCH_MODE", "auto")
    monkeypatch.delenv("SEARCH_PROVIDER", raising=False)
    monkeypatch.setattr(search_module, "select_federated_providers", lambda: [first, second])

    result = await search_module.search("federated routing")

    assert result.provider == "federated"
    assert result.providers_used == ["brave", "tavily"]


@pytest.mark.asyncio
async def test_explicit_provider_overrides_federated_mode(monkeypatch, search_module):
    preferred = StubProvider("brave", response("brave", "https://example.test/a"))
    other = StubProvider("tavily", response("tavily", "https://example.test/b"))
    monkeypatch.setenv("SEARCH_MODE", "federated")
    monkeypatch.setenv("SEARCH_PROVIDER", "brave")
    monkeypatch.setattr(search_module, "get_default_provider", lambda: preferred)
    monkeypatch.setattr(search_module, "select_federated_providers", lambda: [preferred, other])

    result = await search_module.search("federated routing")

    assert result.provider == "brave"
    assert result.providers_used == []


@pytest.mark.asyncio
async def test_single_mode_and_one_provider_preserve_single_provider_behavior(
    monkeypatch, search_module
):
    only = StubProvider("brave", response("brave", "https://example.test/a"))
    monkeypatch.setenv("SEARCH_MODE", "single")
    monkeypatch.delenv("SEARCH_PROVIDER", raising=False)
    monkeypatch.setattr(search_module, "get_default_provider", lambda: only)
    monkeypatch.setattr(search_module, "get_available_providers", lambda: [only])

    result = await search_module.search("federated routing")

    assert result.provider == "brave"


@pytest.mark.asyncio
async def test_no_available_provider_keeps_existing_failure(monkeypatch, search_module):
    monkeypatch.setenv("SEARCH_MODE", "federated")
    monkeypatch.delenv("SEARCH_PROVIDER", raising=False)
    monkeypatch.setattr(search_module, "get_available_providers", lambda: [])

    with pytest.raises(RuntimeError, match="No search providers available"):
        await search_module.search("federated routing")


@pytest.mark.asyncio
async def test_partial_failure_returns_healthy_result_and_redacts_secret():
    secret = "never-expose-this-token"
    healthy = StubProvider("brave", response("brave", "https://example.test/a"))
    failed = StubProvider("tavily", error=RuntimeError(f"request failed: {secret}"))

    result = await search_with_providers("federated routing", [healthy, failed])

    assert result.provider == "federated"
    assert result.providers_used == ["brave"]
    assert result.provider_errors == {"tavily": "RuntimeError"}
    assert secret not in repr(result)


@pytest.mark.asyncio
async def test_all_failures_raise_without_error_details_or_tokens():
    secret = "never-expose-this-token"
    first = StubProvider("brave", error=RuntimeError(secret))
    second = StubProvider("tavily", error=ValueError(secret))

    with pytest.raises(RuntimeError) as exc_info:
        await search_with_providers("federated routing", [first, second])

    assert "brave" in str(exc_info.value)
    assert "tavily" in str(exc_info.value)
    assert secret not in str(exc_info.value)


@pytest.mark.asyncio
async def test_federated_rrf_canonicalizes_duplicate_urls():
    first = StubProvider(
        "brave",
        response("brave", "https://example.test/report/?utm_source=newsletter#section"),
    )
    second = StubProvider("tavily", response("tavily", "https://example.test/report"))

    result = await search_with_providers("federated routing", [first, second])

    assert result.provider == "federated"
    assert result.providers_used == ["brave", "tavily"]
    assert len(result.results) == 1
    assert result.results[0].retrieval_providers == ["brave", "tavily"]
