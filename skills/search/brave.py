"""Brave Search provider using the official Brave Web Search API."""

from typing import Optional

import aiohttp

from .base import SearchProvider, SearchResponse, SearchResult


class BraveSearchProvider(SearchProvider):
    """Search the web through Brave's structured Web Search API."""

    def __init__(self, count: int = 10, country: Optional[str] = None, search_lang: Optional[str] = None):
        self.count = max(1, min(int(count), 20))
        self.country = country
        self.search_lang = search_lang

    @property
    def name(self) -> str:
        return "brave"

    @property
    def api_key_env_var(self) -> str:
        return "BRAVE_SEARCH_API_KEY"

    async def search(self, query: str) -> SearchResponse:
        api_key = self.get_api_key()
        if not api_key:
            raise ValueError(f"{self.api_key_env_var} environment variable is required")

        params = {"q": query, "count": self.count}
        if self.country:
            params["country"] = self.country
        if self.search_lang:
            params["search_lang"] = self.search_lang

        headers = {
            "Accept": "application/json",
            "X-Subscription-Token": api_key,
        }
        url = "https://api.search.brave.com/res/v1/web/search"

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params) as response:
                response.raise_for_status()
                data = await response.json()

        results = []
        for item in (data.get("web") or {}).get("results", []):
            description = item.get("description") or ""
            results.append(SearchResult(
                title=item.get("title", ""),
                url=item.get("url", ""),
                content=description,
                description=description or None,
            ))

        return SearchResponse(
            results=results,
            total_results=len(results),
            query_used=query,
            provider=self.name,
        )
