"""Independent provider-transport resilience tests for federated search and fusion.

These tests inject failures at the SearchProvider transport boundary. They do not
patch registry, orchestration, or fusion internals.
"""

import asyncio
from dataclasses import dataclass
from time import monotonic

import pytest
from skills.search.base import SearchProvider, SearchResponse, SearchResult
from skills.search.federated import search_with_providers


@dataclass
class FaultTransport:
    provider: str
    outcome: object
    delay: float = 0.0
    active: int = 0
    peak: int = 0

    async def request(self, query: str) -> SearchResponse:
        self.active += 1
        self.peak = max(self.peak, self.active)
        try:
            if self.delay:
                await asyncio.sleep(self.delay)
            if isinstance(self.outcome, BaseException):
                raise self.outcome
            if callable(self.outcome):
                return self.outcome(query)
            return self.outcome
        finally:
            self.active -= 1


class TransportProvider(SearchProvider):
    def __init__(self, transport: FaultTransport):
        self.transport = transport

    @property
    def name(self) -> str:
        return self.transport.provider

    @property
    def api_key_env_var(self) -> str:
        return "UNUSED_PROVIDER_TEST_KEY"

    def is_available(self) -> bool:
        return True

    async def search(self, query: str) -> SearchResponse:
        return await self.transport.request(query)


def source(provider: str, url: str = "https://example.test/healthy") -> SearchResponse:
    return SearchResponse(
        provider=provider,
        query_used="fault-injection",
        results=[
            SearchResult(
                title=f"{provider} source",
                url=url,
                content="source-backed evidence",
            )
        ],
        total_results=1,
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "fault",
    [
        RuntimeError("HTTP 429 Too Many Requests"),
        RuntimeError("HTTP 503 Service Unavailable"),
        asyncio.TimeoutError(),
    ],
    ids=["429", "503", "timeout"],
)
async def test_transient_transport_fault_isolated_and_healthy_sibling_keeps_provenance(fault):
    failed = TransportProvider(FaultTransport("failed", fault))
    healthy = TransportProvider(FaultTransport("healthy", source("healthy")))

    result = await search_with_providers("fault-injection", [failed, healthy])

    assert result.providers_used == ["healthy"]
    assert [item.url for item in result.results] == ["https://example.test/healthy"]
    assert result.results[0].retrieval_providers == ["healthy"]
    assert result.provider_errors == {"failed": type(fault).__name__}


@pytest.mark.asyncio
async def test_all_provider_transport_failures_fail_closed_and_redact_error_details():
    secret = "provider-secret-must-not-leak"
    first = TransportProvider(
        FaultTransport("first", RuntimeError(f"429 response body {secret}"))
    )
    second = TransportProvider(
        FaultTransport("second", asyncio.TimeoutError(secret))
    )

    with pytest.raises(RuntimeError) as exc_info:
        await search_with_providers("fault-injection", [first, second])

    message = str(exc_info.value)
    assert "first" in message and "second" in message
    assert secret not in message
    assert "RuntimeError" not in message
    assert "TimeoutError" not in message


@pytest.mark.asyncio
async def test_malformed_provider_payload_isolated_and_healthy_source_survives():
    def malformed(_query: str) -> SearchResponse:
        return SearchResponse(
            provider="malformed",
            results=[{"title": "missing URL", "content": "not a citation"}],
        )

    malformed_transport = TransportProvider(FaultTransport("malformed", malformed))
    healthy = TransportProvider(FaultTransport("healthy", source("healthy")))

    result = await search_with_providers(
        "fault-injection", [malformed_transport, healthy]
    )

    assert result.providers_used == ["healthy"]
    assert result.provider_errors == {"malformed": "ValidationError"}
    assert result.results[0].retrieval_providers == ["healthy"]


@pytest.mark.asyncio
async def test_provider_calls_are_concurrent_with_bounded_input_set():
    transports = [
        FaultTransport(f"provider-{index}", source(f"provider-{index}"), delay=0.03)
        for index in range(3)
    ]
    providers = [TransportProvider(transport) for transport in transports]

    started = monotonic()
    result = await search_with_providers("fault-injection", providers, max_results=10)
    elapsed = monotonic() - started

    assert result.providers_used == [f"provider-{index}" for index in range(3)]
    assert all(transport.peak == 1 for transport in transports)
    assert elapsed < 0.08
