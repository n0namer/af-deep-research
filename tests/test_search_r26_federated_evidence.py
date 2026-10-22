"""R26 deterministic oracle for federated live-evidence search behavior.

These tests inject provider transports and never contact external services.
"""
import asyncio
import hashlib
import os

import pytest

from skills.search import search, search_with_provider
from skills.search.base import SearchResponse, SearchResult
from skills.search.federated import search_with_providers
from skills.search.fusion import fuse_search_responses


class FakeProvider:
    def __init__(self, name, response=None, error=None):
        self.name = name
        self._response = response
        self._error = error
        self.calls = []

    def is_available(self):
        return True

    async def search(self, query):
        self.calls.append(query)
        if self._error:
            raise self._error
        return self._response


def response(provider, *items):
    return SearchResponse(
        provider=provider,
        query_used="federated evidence",
        results=[SearchResult(title=t, url=u, content=c) for t, u, c in items],
        total_results=len(items),
    )


def test_federated_identity_dedupes_canonical_urls_without_fake_independence():
    result = fuse_search_responses(
        [
            response("brave", ("Canonical", "HTTPS://Example.com/report/?utm_source=x", "short")),
            response("tavily", ("Canonical copy", "https://example.com/report", "longer")),
            response("firecrawl", ("Other", "https://other.example/a", "source")),
        ]
    )

    canonical = next(item for item in result.results if item.canonical_url == "https://example.com/report")
    assert len(result.results) == 2
    assert canonical.retrieval_providers == ["brave", "tavily"]
    assert canonical.provider_ranks == {"brave": 1, "tavily": 1}
    assert canonical.content == "longer"


def test_federated_success_is_bounded_when_one_adapter_returns_429_or_503():
    ok = response("brave", ("Live", "https://example.com/live", "verified"))
    providers = [
        FakeProvider("brave", response=ok),
        FakeProvider("tavily", error=RuntimeError("HTTP 429")),
        FakeProvider("firecrawl", error=RuntimeError("HTTP 503")),
    ]

    result = asyncio.run(search_with_providers("q", providers, max_results=5))

    assert result.provider == "federated"
    assert result.providers_used == ["brave"]
    assert result.provider_errors == {"tavily": "RuntimeError", "firecrawl": "RuntimeError"}
    assert [item.url for item in result.results] == ["https://example.com/live"]


def test_missing_adapters_and_unknown_single_provider_refuse_deterministically(monkeypatch):
    monkeypatch.delenv("SEARCH_PROVIDER", raising=False)
    monkeypatch.setenv("SEARCH_MODE", "federated")
    monkeypatch.setenv("SEARCH_PROVIDERS", "brave,perplexity,tavily,firecrawl")
    monkeypatch.setenv("SEARCH_FEDERATED_MAX_PROVIDERS", "4")

    from skills.search import federated as federated_module
    monkeypatch.setattr(
        federated_module,
        "get_provider",
        lambda name: FakeProvider(name) if name in {"brave", "perplexity", "tavily", "firecrawl"} else None,
    )
    monkeypatch.setattr(
        federated_module,
        "get_available_providers",
        lambda: [FakeProvider(name) for name in ("brave", "perplexity", "tavily", "firecrawl")],
    )

    selected = federated_module.select_federated_providers()
    assert [provider.name for provider in selected] == ["brave", "perplexity", "tavily", "firecrawl"]

    with pytest.raises(ValueError, match="Unknown provider"):
        asyncio.run(search_with_provider("q", "not-configured"))


def test_auto_and_single_dispatch_preserve_provider_identity(monkeypatch):
    provider = FakeProvider("brave", response=response("brave", ("One", "https://example.com/one", "evidence")))

    import skills.search as search_module
    monkeypatch.delenv("SEARCH_PROVIDER", raising=False)
    monkeypatch.setenv("SEARCH_MODE", "auto")
    monkeypatch.setattr(search_module, "select_federated_providers", lambda: [provider])
    monkeypatch.setattr(search_module, "get_default_provider", lambda: provider)

    auto_result = asyncio.run(search("q"))
    assert auto_result.provider == "brave"
    assert provider.calls == ["q"]

    monkeypatch.setenv("SEARCH_PROVIDER", "brave")
    monkeypatch.setattr(search_module, "get_default_provider", lambda: provider)
    single_result = asyncio.run(search("q2"))
    assert single_result.provider == "brave"
    assert provider.calls == ["q", "q2"]


def test_source_hash_is_recorded_for_this_oracle():
    source = open("skills/search/fusion.py", encoding="utf-8").read().encode()
    assert hashlib.sha256(source).hexdigest() == "c7c0684e8d5d55df099ebf7690bfceafff78e79fe4ad15a6265ecb29a5a5625c"
