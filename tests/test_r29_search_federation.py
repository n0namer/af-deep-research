import asyncio

import pytest

from skills.search.base import SearchProvider, SearchResponse, SearchResult
from skills.search.federated import select_federated_providers, search_with_providers


class StubProvider(SearchProvider):
    def __init__(self, provider_name, results=(), failure=None):
        self._name = provider_name
        self._results = list(results)
        self._failure = failure
        self.calls = 0

    @property
    def name(self):
        return self._name

    @property
    def api_key_env_var(self):
        return f"{self._name.upper()}_API_KEY"

    def is_available(self):
        return True

    async def search(self, query):
        self.calls += 1
        await asyncio.sleep(0)
        if self._failure:
            raise self._failure
        return SearchResponse(
            results=self._results,
            total_results=len(self._results),
            query_used=query,
            provider=self.name,
        )


def result(url, title="source", content="content"):
    return SearchResult(title=title, url=url, content=content)


@pytest.mark.asyncio
async def test_four_provider_fanout_and_canonical_dedup(monkeypatch):
    monkeypatch.delenv("SEARCH_FEDERATED_MAX_PROVIDERS", raising=False)
    providers = [
        StubProvider("one", [result("https://example.test/a?utm_source=x")]),
        StubProvider("two", [result("https://EXAMPLE.TEST/a/")]),
        StubProvider("three", [result("https://example.test/b")]),
        StubProvider("four", [result("https://example.test/c")]),
    ]

    response = await search_with_providers("q", providers)

    assert [provider.calls for provider in providers] == [1, 1, 1, 1]
    assert len(response.results) == 3
    assert response.results[0].canonical_url == "https://example.test/a"
    assert set(response.results[0].retrieval_providers) == {"one", "two"}


def test_provider_selection_is_bounded_to_four_and_deduplicated(monkeypatch):
    providers = [StubProvider(str(i)) for i in range(6)]
    monkeypatch.setattr(
        "skills.search.federated.get_provider",
        lambda name: next((provider for provider in providers if provider.name == name), None),
    )
    monkeypatch.setenv("SEARCH_PROVIDERS", "0,1,1,2,3,4,5")
    monkeypatch.setenv("SEARCH_FEDERATED_MAX_PROVIDERS", "999")

    selected = select_federated_providers()

    assert [provider.name for provider in selected] == ["0", "1", "2", "3"]


@pytest.mark.asyncio
async def test_one_provider_failure_is_isolated_and_reported():
    providers = [
        StubProvider("ok", [result("https://example.test/ok")]),
        StubProvider("bad", failure=TimeoutError()),
    ]

    response = await search_with_providers("q", providers)

    assert len(response.results) == 1
    assert response.provider_errors == {"bad": "TimeoutError"}


@pytest.mark.asyncio
async def test_empty_provider_set_is_rejected():
    with pytest.raises(RuntimeError, match="No search providers"):
        await search_with_providers("q", [])
