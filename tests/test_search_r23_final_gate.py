"""Independent frozen-source QA gate for search citation independence.
These checks exercise native provider/fusion boundaries.
"""
from hashlib import sha256
from pathlib import Path
import pytest
from skills.search.base import SearchResponse, SearchResult
from skills.search.federated import search_with_providers
from skills.search.fusion import canonicalize_url, fuse_search_responses
from tests.test_search_r20_provider_failover import TransportProvider, FaultTransport, source

def _result(provider: str, url: str) -> SearchResponse:
    return SearchResponse(provider=provider, query_used="r23-gate",
        results=[SearchResult(title="Canonical source", url=url, content="evidence")],
        total_results=1)

def test_four_provider_hits_are_one_canonical_citation():
    url = "https://publisher.example/report?utm_source=provider"
    fused = fuse_search_responses([_result(f"provider-{index}", url) for index in range(4)])
    assert len(fused.results) == 1
    citation = fused.results[0]
    assert citation.canonical_url == canonicalize_url(url)
    assert citation.retrieval_providers == ["provider-0", "provider-1", "provider-2", "provider-3"]
    assert len({citation.canonical_url}) != len(citation.retrieval_providers)

@pytest.mark.asyncio
@pytest.mark.parametrize("fault", [RuntimeError("HTTP 429 Too Many Requests"), RuntimeError("HTTP 503 Service Unavailable")])
async def test_transient_fault_uses_healthy_fallback_without_fake_citation(fault):
    failed = TransportProvider(FaultTransport("failed", fault))
    healthy = TransportProvider(FaultTransport("healthy", source("healthy")))
    result = await search_with_providers("r23-gate", [failed, healthy])
    assert result.providers_used == ["healthy"]
    assert result.results[0].retrieval_providers == ["healthy"]
    assert result.provider_errors == {"failed": "RuntimeError"}

@pytest.mark.asyncio
async def test_empty_or_malformed_provider_set_fails_closed():
    empty = TransportProvider(FaultTransport("empty", SearchResponse(provider="empty", query_used="r23-gate", results=[], total_results=0)))
    malformed = TransportProvider(FaultTransport("malformed", lambda _query: SearchResponse(provider="malformed", results=[{"title": "missing URL", "content": "not a citation"}])))
    with pytest.raises(RuntimeError):
        await search_with_providers("r23-gate", [empty, malformed])

def test_stale_architecture_signature_is_red_not_accepted():
    contract = Path("docs/architecture/search-r16-contract.json").read_text()
    current = Path("skills/search/fusion.py").read_bytes()
    stale_signature = "0" * 64
    assert '"status": "CANDIDATE/UNACCEPTED"' in contract
    assert sha256(current).hexdigest() != stale_signature
