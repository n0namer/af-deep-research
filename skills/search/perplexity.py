"""Perplexity Search provider using the official structured Search API."""

from datetime import datetime
from typing import Optional

import aiohttp

from .base import SearchProvider, SearchResponse, SearchResult


def _parse_date(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None


class PerplexitySearchProvider(SearchProvider):
    """Search the web through Perplexity's structured Search API, not Sonar."""

    def __init__(self, max_results: int = 10, search_context_size: str = "low"):
        self.max_results = max(1, min(int(max_results), 20))
        self.search_context_size = search_context_size

    @property
    def name(self) -> str:
        return "perplexity"

    @property
    def api_key_env_var(self) -> str:
        return "PERPLEXITY_API_KEY"

    async def search(self, query: str) -> SearchResponse:
        api_key = self.get_api_key()
        if not api_key:
            raise ValueError(f"{self.api_key_env_var} environment variable is required")

        url = "https://api.perplexity.ai/search"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "query": query,
            "max_results": self.max_results,
            "search_type": "web",
            "search_context_size": self.search_context_size,
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                response.raise_for_status()
                data = await response.json()

        results = []
        for item in data.get("results", []):
            snippet = item.get("snippet") or ""
            results.append(SearchResult(
                title=item.get("title", ""),
                url=item.get("url", ""),
                content=snippet,
                description=snippet or None,
                published_time=_parse_date(item.get("date")),
            ))

        return SearchResponse(
            results=results,
            total_results=len(results),
            query_used=query,
            provider=self.name,
        )
