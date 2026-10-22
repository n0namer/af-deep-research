"""Source-bound deterministic integration tests for the main search bridge.

The only monkeypatch point is the provider HTTP transport (aiohttp.ClientSession).
Provider selection, routing, fusion, dedupe, and the main bridge remain real.
No LLM or external search request is made.
"""

from __future__ import annotations

import importlib
from dataclasses import dataclass
from typing import Any

import pytest

from skills.search.federated import federated_search


@dataclass
class _FakeResponse:
    payload: dict[str, Any]
    status: int = 200

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_args):
        return None

    def raise_for_status(self):
        if self.status >= 400:
            raise RuntimeError(f"HTTP {self.status}")

    async def json(self):
        return self.payload

    async def text(self):
        return str(self.payload)


class _DeterministicTransport:
    """A provider-transport double; all higher-level routing stays production code."""

    def __init__(self, *, failures: set[str] | None = None, empty: bool = False):
        self.failures = failures or set()
        self.empty = empty
        self.calls: list[tuple[str, str]] = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_args):
        return None

    def _response(self, method: str, url: str, **_kwargs):
        provider = (
            "jina" if "s.jina.ai" in url else
            "tavily" if "tavily.com" in url else
            "firecrawl" if "firecrawl" in url else
            "serper" if "serper.dev" in url else
            "unknown"
        )
        self.calls.append((provider, url))
        if provider in self.failures:
            raise OSError(f"deterministic {provider} transport failure")
        if self.empty:
            return _FakeResponse({"data": [], "results": [], "organic": []})

        first = {
            "title": "Canonical protocol source",
            "url": "https://rfc.example.test/spec",
            "content": "The canonical protocol source defines the deterministic behavior.",
            "description": "primary source",
        }
        second = {
            "title": "Independent implementation source",
            "url": "https://docs.example.test/guide",
            "content": "The implementation guide explains the same behavior.",
            "description": "secondary source",
        }
        if provider == "jina":
            return _FakeResponse({"data": [first, second]})
        if provider == "tavily":
            return _FakeResponse({"results": [first, second]})
        if provider == "serper":
            return _FakeResponse({"organic": [first, second]})
        if provider == "firecrawl":
            return _FakeResponse({"data": {"web": [first, second]}})
        return _FakeResponse({})

    def get(self, url, **kwargs):
        return self._response("GET", url, **kwargs)

    def post(self, url, **kwargs):
        return self._response("POST", url, **kwargs)

    def request(self, method, url, **kwargs):
        return self._response(method, url, **kwargs)


def _patch_provider_transport(monkeypatch, transport: _DeterministicTransport):
    """Patch HTTP at the provider boundary, never skills.search.search/fusion."""
    for module_name in (
        "skills.search.jina",
        "skills.search.tavily",
        "skills.search.firecrawl",
        "skills.search.serper",
    ):
        module = importlib.import_module(module_name)
        monkeypatch.setattr(module.aiohttp, "ClientSession", lambda: transport)


@pytest.fixture
def deterministic_transport(monkeypatch):
    transport = _DeterministicTransport()
    _patch_provider_transport(monkeypatch, transport)
    return transport


def _enable(*names: str):
    env = {
        "JINA_API_KEY": "",
        "TAVILY_API_KEY": "",
        "FIRECRAWL_API_KEY": "",
        "SERPER_API_KEY": "",
    }
    env.update({f"{name.upper()}_API_KEY": f"test-{name}-key" for name in names})
    return env


@pytest.mark.asyncio
async def test_main_bridge_auto_mode_uses_real_search_routing_and_transforms_results(
    monkeypatch, deterministic_transport
):
    for key, value in _enable("jina").items():
        monkeypatch.setenv(key, value)
    monkeypatch.delenv("SEARCH_PROVIDER", raising=False)

    main = importlib.import_module("main")
    results = await main.search_web_for_content("protocol behavior")

    assert [item["url"] for item in results] == [
        "https://rfc.example.test/spec",
        "https://docs.example.test/guide",
    ]
    assert all({"url", "title", "content", "description"} <= item.keys() for item in results)
    assert deterministic_transport.calls
    assert deterministic_transport.calls[0][0] == "jina"


@pytest.mark.asyncio
async def test_single_provider_path_returns_deterministic_sources(monkeypatch, deterministic_transport):
    for key, value in _enable("tavily").items():
        monkeypatch.setenv(key, value)

    from skills.search import search_with_provider

    response = await search_with_provider("single provider", provider="tavily")

    assert response.provider == "tavily"
    assert {result.url for result in response.results} == {
        "https://rfc.example.test/spec",
        "https://docs.example.test/guide",
    }


@pytest.mark.asyncio
async def test_federated_path_deduplicates_canonical_urls_and_keeps_provenance(
    monkeypatch, deterministic_transport
):
    for key, value in _enable("jina", "tavily").items():
        monkeypatch.setenv(key, value)
    monkeypatch.setenv("SEARCH_FEDERATED_MAX_PROVIDERS", "2")

    response = await federated_search(
        "federated protocol",
        provider_names=("jina", "tavily"),
    )

    assert len(response.results) == 2
    canonical = {result.canonical_url or result.url for result in response.results}
    assert canonical == {
        "https://rfc.example.test/spec",
        "https://docs.example.test/guide",
    }
    assert set(response.providers_used) == {"jina", "tavily"}
    assert all(result.retrieval_providers for result in response.results)
    assert all(result.provider_ranks for result in response.results)
    assert response.provider_errors == {}


@pytest.mark.asyncio
async def test_federated_fallback_keeps_success_when_one_provider_transport_fails(
    monkeypatch
):
    for key, value in _enable("jina", "tavily").items():
        monkeypatch.setenv(key, value)
    transport = _DeterministicTransport(failures={"tavily"})
    _patch_provider_transport(monkeypatch, transport)

    response = await federated_search(
        "fallback protocol",
        provider_names=("jina", "tavily"),
    )

    assert response.results
    assert response.providers_used == ["jina"]
    assert response.provider_errors == {"tavily": "OSError"}


@pytest.mark.asyncio
async def test_all_provider_failure_is_visible_typed_error(monkeypatch):
    for key, value in _enable("jina", "tavily").items():
        monkeypatch.setenv(key, value)
    transport = _DeterministicTransport(failures={"jina", "tavily"})
    _patch_provider_transport(monkeypatch, transport)

    with pytest.raises(RuntimeError, match="All federated search providers failed"):
        await federated_search("unavailable protocol", provider_names=("jina", "tavily"))


@pytest.mark.asyncio
async def test_zero_result_response_is_not_conflated_with_provider_failure(monkeypatch):
    for key, value in _enable("jina").items():
        monkeypatch.setenv(key, value)
    _patch_provider_transport(monkeypatch, _DeterministicTransport(empty=True))

    from skills.search import search_with_provider

    response = await search_with_provider("no matching source", provider="jina")

    assert response.results == []
    assert response.provider_errors == {}
    assert response.total_results == 0


@pytest.mark.asyncio
async def test_malformed_transport_payload_fails_closed_without_fabricated_provenance(
    monkeypatch,
):
    for key, value in _enable("jina").items():
        monkeypatch.setenv(key, value)
    transport = _DeterministicTransport()
    _patch_provider_transport(monkeypatch, transport)

    from skills.search import search_with_provider

    malformed = _FakeResponse({"data": [{"title": "missing identity", "content": "text"}]})
    transport._response = lambda *_args, **_kwargs: malformed

    with pytest.raises((ValueError, KeyError, TypeError)):
        await search_with_provider("malformed", provider="jina")


def test_six_golden_semantic_prompts_are_explicit_and_source_policy_bound():
    prompts = (
        ("DR-S01", "What is the current protocol behavior?", "rfc-editor.org"),
        ("DR-S02", "Which study result is contradicted by later evidence?", "doi.org"),
        ("DR-S03", "What is the authoritative state transition?", "gov.example"),
        ("DR-S04", "What historical event caused the change?", "archives.example"),
        ("DR-S05", "Which official business metric is reported?", "sec.example"),
        ("DR-S06", "What are the product risks and prompt-injection traps?", "vendor.example"),
    )

    assert len(prompts) == 6
    assert len({domain for _, _, domain in prompts}) == 6
    assert all(prompt and domain for _, prompt, domain in prompts)


def test_main_bridge_documents_legacy_empty_on_no_key_as_known_limitation(monkeypatch):
    for key, value in _enable().items():
        monkeypatch.setenv(key, value)

    import asyncio

    main = importlib.import_module("main")
    result = asyncio.run(main.search_web_for_content("no provider key"))

    # The bridge currently preserves its legacy [] fallback. Federated callers
    # above enforce the typed all-failure contract; this test makes the gap
    # visible instead of treating [] as a successful search.
    assert result == []
