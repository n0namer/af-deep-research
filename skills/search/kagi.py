"""Kagi Search provider using the official v1 Search API."""

from datetime import datetime
from typing import Optional

import aiohttp

from .base import SearchProvider, SearchResponse, SearchResult


def _parse_published(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None


class KagiSearchProvider(SearchProvider):
    """Search through Kagi's programmable premium search results."""

    @property
    def name(self) -> str:
        return "kagi"

    @property
    def api_key_env_var(self) -> str:
        return "KAGI_API_TOKEN"

    async def search(self, query: str) -> SearchResponse:
        token = self.get_api_key()
        if not token:
            raise ValueError(f"{self.api_key_env_var} environment variable is required")

        url = "https://kagi.com/api/v1/search"
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bot {token}",
        }
        params = {"q": query}

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params) as response:
                response.raise_for_status()
                data = await response.json()

        raw_results = data.get("data") or data.get("results") or []
        results = []
        for item in raw_results:
            # Search result objects are type 0; ignore related-search/meta objects.
            if item.get("t") not in (None, 0) or not item.get("url"):
                continue
            snippet = item.get("snippet") or item.get("description") or ""
            results.append(SearchResult(
                title=item.get("title", ""),
                url=item.get("url", ""),
                content=snippet,
                description=snippet or None,
                published_time=_parse_published(item.get("published")),
            ))

        return SearchResponse(
            results=results,
            total_results=len(results),
            query_used=query,
            provider=self.name,
        )
