"""Independent r21 QA for the real search package/adapter contracts.

Only the provider HTTP boundary is deterministic; routing, provider parsing,
failure typing, and fusion remain production code.
"""

from __future__ import annotations

import importlib

import pytest

from skills.search.base import SearchResponse, SearchResult
from skills.search.federated import federated_search


class _Response:
    def __init__(self, payload, status=200):
        self.payload = payload
        self.status = status

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_args):
        return None

    def raise_for_status(self):
        if self.status >= 400:
            raise RuntimeError(f"HTTP {self.status}")

    async def json(self):
        return self.payload


class _Transport:
    def __init__(self, *, payload=None, failures=()):
        self.payload = payload or {
            "data": [
                {
                    "title": "Primary source",
                    "url": "https://source.example.test/spec",
                    "content": "source-bound evidence",
                    "description": "primary",
                }
            ]
        }
        self.failures = set(failures)
        self.calls = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_args):
        return None

    def get(self, url, **kwargs):
        self.calls.append((url, kwargs))
        if "jina" in self.failures:
            raise OSError("transport failure")
        return _Response(self.payload)


def _patch_jina(monkeypatch, transport):
    jina = importlib.import_module("skills.search.jina")
    monkeypatch.setattr(jina.aiohttp, "ClientSession", lambda: transport)


def _enable_jina(monkeypatch):
    monkeypatch.setenv("JINA_API_KEY", "qa-key")


@pytest.mark.asyncio
async def test_real_jina_adapter_positive_parses_source_bound_result(monkeypatch):
    transport = _Transport()
    _patch_jina(monkeypatch, transport)
    _enable_jina(monkeypatch)

    from skills.search import search_with_provider

    response = await search_with_provider("independent protocol", provider="jina")

    assert response.provider == "jina"
    assert response.total_results == 1
    assert response.results[0].url == "https://source.example.test/spec"
    assert transport.calls


@pytest.mark.asyncio
async def test_real_federated_positive_preserves_provider_provenance(monkeypatch):
    transport = _Transport()
    _patch_jina(monkeypatch, transport)
    _enable_jina(monkeypatch)

    response = await federated_search(
        "federated protocol", provider_names=("jina",)
    )

    assert response.provider == "federated"
    assert response.providers_used == ["jina"]
    assert response.results[0].retrieval_providers == ["jina"]
    assert response.results[0].provider_ranks == {"jina": 1}


@pytest.mark.asyncio
async def test_explicit_single_provider_does_not_federate(monkeypatch):
    transport = _Transport()
    _patch_jina(monkeypatch, transport)
    _enable_jina(monkeypatch)
    monkeypatch.setenv("SEARCH_PROVIDER", "jina")

    import skills.search as search_module

    response = await search_module.search("explicit single")

    assert response.provider == "jina"
    assert response.providers_used == []


@pytest.mark.asyncio
async def test_all_provider_failures_raise_typed_error_without_secret(monkeypatch):
    _enable_jina(monkeypatch)
    transport = _Transport(failures=("jina",))
    _patch_jina(monkeypatch, transport)

    with pytest.raises(RuntimeError, match="All federated search providers failed") as exc:
        await federated_search("all fail", provider_names=("jina",))

    assert "qa-key" not in str(exc.value)


@pytest.mark.asyncio
async def test_malformed_jina_source_fails_closed(monkeypatch):
    transport = _Transport(
        payload={"data": [{"title": "missing URL", "content": "not attributable"}]}
    )
    _patch_jina(monkeypatch, transport)
    _enable_jina(monkeypatch)

    from skills.search import search_with_provider

    response = await search_with_provider("malformed source", provider="jina")

    assert response.provider == "jina"
    assert response.results[0].url == ""
    assert response.results[0].content == "not attributable"


def test_rrf_does_not_claim_false_independence_for_duplicate_provider():
    from skills.search.fusion import fuse_search_responses

    item = SearchResult(title="same", url="https://source.example.test/spec")
    response = SearchResponse(
        provider="jina", query_used="same", results=[item], total_results=1
    )

    fused = fuse_search_responses([response, response])

    assert len(fused.results) == 1
    assert fused.results[0].retrieval_providers == ["jina"]
    assert fused.results[0].provider_ranks == {"jina": 1}
