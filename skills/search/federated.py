"""Bounded federated-search orchestration with provider failure isolation."""

import asyncio
import os
from typing import List, Optional, Sequence

from .base import SearchProvider, SearchResponse
from .fusion import fuse_search_responses
from .registry import get_available_providers, get_provider


def _bounded_int(env_name: str, default: int, minimum: int, maximum: int) -> int:
    try:
        value = int(os.getenv(env_name, str(default)))
    except (TypeError, ValueError):
        value = default
    return max(minimum, min(value, maximum))


def select_federated_providers(provider_names: Optional[Sequence[str]] = None) -> List[SearchProvider]:
    """Resolve a bounded ordered set of configured search providers."""
    if provider_names is None:
        raw = os.getenv("SEARCH_PROVIDERS", "").strip()
        provider_names = [item.strip().lower() for item in raw.split(",") if item.strip()] if raw else None

    providers: List[SearchProvider] = []
    if provider_names:
        seen = set()
        for name in provider_names:
            normalized = name.strip().lower()
            if normalized in seen:
                continue
            seen.add(normalized)
            provider = get_provider(normalized)
            if provider and provider.is_available():
                providers.append(provider)
    else:
        providers = get_available_providers()

    max_providers = _bounded_int("SEARCH_FEDERATED_MAX_PROVIDERS", 2, 1, 8)
    return providers[:max_providers]


async def search_with_providers(
    query: str,
    providers: Sequence[SearchProvider],
    max_results: Optional[int] = None,
) -> SearchResponse:
    """Execute providers concurrently and fuse successful ranked responses."""
    providers = list(providers)
    if not providers:
        raise RuntimeError("No search providers available for federated search")

    outcomes = await asyncio.gather(
        *(provider.search(query) for provider in providers),
        return_exceptions=True,
    )

    successful = []
    errors = {}
    for provider, outcome in zip(providers, outcomes):
        if isinstance(outcome, Exception):
            errors[provider.name] = type(outcome).__name__
            continue
        successful.append(outcome)

    if not successful:
        failed = ", ".join(sorted(errors)) or "unknown"
        raise RuntimeError(f"All federated search providers failed: {failed}")

    if max_results is None:
        max_results = _bounded_int("SEARCH_FEDERATED_MAX_RESULTS", 10, 1, 50)

    fused = fuse_search_responses(successful, max_results=max_results)
    fused.provider_errors = errors
    return fused


async def federated_search(
    query: str,
    provider_names: Optional[Sequence[str]] = None,
    max_results: Optional[int] = None,
) -> SearchResponse:
    """Search a bounded provider set and return one fused response."""
    providers = select_federated_providers(provider_names)
    return await search_with_providers(query, providers, max_results=max_results)
