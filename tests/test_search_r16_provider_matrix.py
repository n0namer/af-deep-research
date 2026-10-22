"""Deterministic provider matrix with opt-in live observations."""
from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass
from typing import Any, Callable
from urllib.parse import urlsplit

import pytest

from skills.search.brave import BraveSearchProvider
from skills.search.firecrawl import FirecrawlSearchProvider
from skills.search.perplexity import PerplexitySearchProvider
from skills.search.tavily import TavilySearchProvider

PRIMARY = {"rfc9110": "rfc-editor.org", "python313": "python.org"}
QUERIES = {"rfc9110": "RFC 9110", "python313": "Python 3.13"}
KEYS = {
    "brave": "BRAVE_SEARCH_API_KEY",
    "tavily": "TAVILY_API_KEY",
    "firecrawl": "FIRECRAWL_API_KEY",
    "perplexity": "PERPLEXITY_API_KEY",
}
UNSUPPORTED = {
    "jina": "outside this matrix",
    "serper": "outside this matrix",
    "exa": "no repository adapter is registered",
}


def source_class(url: str) -> str:
    if not isinstance(url, str) or not url.strip():
        raise ValueError("source URL is required")
    parsed = urlsplit(url.strip())
    hostname = (parsed.hostname or "").lower().rstrip(".")
    if parsed.scheme.lower() != "https" or not hostname:
        raise ValueError("source URL must have an HTTPS domain")
    if parsed.username or parsed.password:
        raise ValueError("source URL must not contain credentials")
    for bucket, domain in PRIMARY.items():
        if hostname == domain or hostname.endswith("." + domain):
            return bucket
    return "secondary"


@dataclass(frozen=True)
class Observation:
    provider: str
    query_id: str
    urls: tuple[str, ...]
    source_classes: tuple[str, ...]


def normalize_observation(provider: str, query_id: str, urls: list[str]) -> Observation:
    if not urls:
        raise ValueError("observation has no source URLs")
    normalized = tuple(url.strip() for url in urls)
    if len(set(normalized)) != len(normalized):
        raise ValueError("observation contains duplicate source URLs")
    classes = tuple(source_class(url) for url in normalized)
    if query_id not in classes:
        raise ValueError(f"observation has no primary {query_id} source")
    return Observation(provider, query_id, normalized, classes)


class FakeResponse:
    def __init__(self, payload: dict[str, Any]):
        self.payload = payload

    async def __aenter__(self) -> "FakeResponse":
        return self

    async def __aexit__(self, *_: object) -> None:
        return None

    def raise_for_status(self) -> None:
        return None

    async def json(self) -> dict[str, Any]:
        return self.payload


class FakeSession:
    def __init__(self, payload: dict[str, Any], calls: list[tuple[str, str]]):
        self.payload, self.calls = payload, calls

    async def __aenter__(self) -> "FakeSession":
        return self

    async def __aexit__(self, *_: object) -> None:
        return None

    def get(self, url: str, **_: Any) -> FakeResponse:
        self.calls.append(("GET", url))
        return FakeResponse(self.payload)

    def post(self, url: str, **_: Any) -> FakeResponse:
        self.calls.append(("POST", url))
        return FakeResponse(self.payload)


@dataclass(frozen=True)
class Case:
    name: str
    factory: Callable[[], Any]
    key: str
    payload: dict[str, Any]
    method: str
    endpoint: str


RFC = "https://www.rfc-editor.org/rfc/rfc9110.html"
PYTHON = "https://docs.python.org/3.13/"
CASES = [
    Case("brave", BraveSearchProvider, KEYS["brave"],
         {"web": {"results": [{"url": RFC}, {"url": PYTHON}]}},
         "GET", "https://api.search.brave.com/res/v1/web/search"),
    Case("tavily", TavilySearchProvider, KEYS["tavily"],
         {"results": [{"url": RFC}, {"url": PYTHON}]},
         "POST", "https://api.tavily.com/search"),
    Case("firecrawl", FirecrawlSearchProvider, KEYS["firecrawl"],
         {"data": [{"url": RFC}, {"url": PYTHON}]},
         "POST", "https://api.firecrawl.dev/v1/search"),
    Case("perplexity", PerplexitySearchProvider, KEYS["perplexity"],
         {"results": [{"url": RFC}, {"url": PYTHON}]},
         "POST", "https://api.perplexity.ai/search"),
]


@pytest.mark.parametrize("case", CASES, ids=lambda case: case.name)
def test_four_independent_adapters_use_isolated_fake_contracts(
    case: Case, monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[str, str]] = []
    monkeypatch.setattr("aiohttp.ClientSession", lambda: FakeSession(case.payload, calls))
    for key in KEYS.values():
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv(case.key, "test-only-key")
    response = asyncio.run(case.factory().search(QUERIES["rfc9110"]))
    assert response.provider == case.name
    urls = [result.url for result in response.results]
    assert urls == [RFC, PYTHON]
    assert calls and calls[0][0:2] == (case.method, case.endpoint)
    assert "test-only-key" not in repr(calls)
    assert normalize_observation(case.name, "rfc9110", urls).source_classes == (
        "rfc9110", "python313"
    )


@pytest.mark.parametrize("urls", [
    [], [""], ["https://"], ["http://www.rfc-editor.org/rfc/rfc9110.html"],
    ["https://rfc-editor.org.evil.example/rfc/rfc9110.html"],
    ["https://user:secret@www.rfc-editor.org/rfc/rfc9110.html"],
])
def test_validation_rejects_empty_fabricated_or_unsafe_domains(urls: list[str]) -> None:
    with pytest.raises(ValueError):
        normalize_observation("fake", "rfc9110", urls)


def test_validation_rejects_missing_primary_bucket_and_duplicates() -> None:
    with pytest.raises(ValueError, match="no primary"):
        normalize_observation("fake", "python313", ["https://example.org/article"])
    with pytest.raises(ValueError, match="duplicate"):
        normalize_observation("fake", "rfc9110", [RFC, RFC])


def test_jina_serper_exa_are_explicitly_outside_this_matrix() -> None:
    assert set(UNSUPPORTED) == {"jina", "serper", "exa"}
    assert all(UNSUPPORTED.values())


def live_enabled() -> bool:
    return os.getenv("REAL_NETWORK_TESTS", "").strip().lower() in {"1", "true", "yes"}


@pytest.mark.parametrize("name", tuple(KEYS))
@pytest.mark.parametrize("query_id", tuple(QUERIES))
def test_opt_in_live_observation_is_bounded_and_honest(name: str, query_id: str) -> None:
    if not live_enabled():
        pytest.skip("REAL_NETWORK_TESTS is not enabled")
    if not os.getenv(KEYS[name], "").strip():
        pytest.skip(f"{KEYS[name]} is not set; no live evidence claimed")
    factories = {
        "brave": BraveSearchProvider, "tavily": TavilySearchProvider,
        "firecrawl": FirecrawlSearchProvider, "perplexity": PerplexitySearchProvider,
    }
    response = asyncio.run(factories[name]().search(QUERIES[query_id]))
    observation = normalize_observation(
        name, query_id, [result.url for result in response.results]
    )
    assert observation.provider == name
    assert query_id in observation.source_classes
