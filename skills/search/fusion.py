"""Deterministic cross-provider URL deduplication and reciprocal-rank fusion."""

from typing import Dict, Iterable, List
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from .base import SearchResponse, SearchResult


_TRACKING_KEYS = {
    "gclid", "fbclid", "msclkid", "mc_cid", "mc_eid", "_hsenc", "_hsmi",
}


def canonicalize_url(url: str) -> str:
    """Normalize a URL for retrieval dedupe without changing source semantics."""
    value = (url or "").strip()
    if not value:
        return ""
    try:
        parts = urlsplit(value)
        scheme = parts.scheme.lower()
        netloc = parts.netloc.lower()
        path = parts.path or "/"
        if path != "/":
            path = path.rstrip("/") or "/"
        query_pairs = []
        for key, val in parse_qsl(parts.query, keep_blank_values=True):
            lower = key.lower()
            if lower.startswith("utm_") or lower in _TRACKING_KEYS:
                continue
            query_pairs.append((key, val))
        query = urlencode(sorted(query_pairs), doseq=True)
        return urlunsplit((scheme, netloc, path, query, ""))
    except Exception:
        return value.split("#", 1)[0].rstrip("/")


def fuse_search_responses(
    responses: Iterable[SearchResponse],
    max_results: int = 10,
    rrf_k: int = 60,
) -> SearchResponse:
    """Fuse provider rankings using RRF and canonical-URL deduplication."""
    responses = list(responses)
    if not responses:
        return SearchResponse(provider="federated")

    entries: Dict[str, Dict] = {}
    providers_used: List[str] = []
    query_used = ""

    for response in responses:
        provider = response.provider or "unknown"
        if provider not in providers_used:
            providers_used.append(provider)
        if not query_used and response.query_used:
            query_used = response.query_used
        seen_for_provider = set()

        for rank, result in enumerate(response.results, start=1):
            key = canonicalize_url(result.url)
            if not key or key in seen_for_provider:
                continue
            seen_for_provider.add(key)

            entry = entries.get(key)
            if entry is None:
                representative = result.model_copy(deep=True)
                representative.canonical_url = key
                representative.retrieval_providers = []
                representative.provider_ranks = {}
                representative.rrf_score = 0.0
                entry = {
                    "result": representative,
                    "score": 0.0,
                    "ranks": {},
                }
                entries[key] = entry
            else:
                representative = entry["result"]
                if len(result.content or "") > len(representative.content or ""):
                    representative.content = result.content
                    representative.description = result.description
                    if result.title:
                        representative.title = result.title
                    if result.published_time:
                        representative.published_time = result.published_time

            if provider in entry["ranks"]:
                continue
            entry["ranks"][provider] = rank
            entry["score"] += 1.0 / (rrf_k + rank)

    fused: List[SearchResult] = []
    for key, entry in entries.items():
        result = entry["result"]
        result.canonical_url = key
        result.provider_ranks = dict(entry["ranks"])
        result.retrieval_providers = list(entry["ranks"].keys())
        result.rrf_score = round(entry["score"], 12)
        fused.append(result)

    fused.sort(key=lambda item: (-(item.rrf_score or 0.0), item.canonical_url or item.url, item.title))
    fused = fused[: max(1, int(max_results))]

    return SearchResponse(
        results=fused,
        total_results=len(fused),
        query_used=query_used,
        provider="federated",
        providers_used=providers_used,
    )
