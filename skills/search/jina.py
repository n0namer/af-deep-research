"""Jina AI Search Provider.

Provides web search using Jina AI's search API.
"""

from datetime import datetime
from typing import Any
from urllib.parse import urlparse

import aiohttp

from .base import SearchProvider, SearchResult, SearchResponse


def _parse_result(item: Any) -> SearchResult:
    """Parse one Jina result without fabricating source identity."""
    if not isinstance(item, dict):
        raise TypeError("Jina result must be an object")

    title = item.get("title")
    url = item.get("url")
    if not isinstance(title, str) or not title.strip():
        raise ValueError("Jina result title is required")
    if not isinstance(url, str) or not url.strip():
        raise ValueError("Jina result URL is required")

    parsed_url = urlparse(url)
    if parsed_url.scheme != "https" or not parsed_url.netloc:
        raise ValueError("Jina result URL must be an absolute HTTPS URL")

    published_time = None
    if item.get("publishedTime"):
        try:
            published_time = datetime.fromisoformat(
                item["publishedTime"].replace("Z", "+00:00")
            )
        except (ValueError, TypeError, AttributeError):
            pass

    return SearchResult(
        title=title,
        url=url,
        content=item.get("content", ""),
        description=item.get("description"),
        published_time=published_time,
    )


class JinaSearchProvider(SearchProvider):
    """Jina AI search provider implementation."""

    @property
    def name(self) -> str:
        return "jina"

    @property
    def api_key_env_var(self) -> str:
        return "JINA_API_KEY"

    async def search(self, query: str) -> SearchResponse:
        """Search using Jina AI and return structured results."""
        api_key = self.get_api_key()
        if not api_key:
            raise ValueError(f"{self.api_key_env_var} environment variable is required")

        url = "https://s.jina.ai/"
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {api_key}",
            "X-Engine": "browser",
        }
        params = {"q": query}

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params) as response:
                response.raise_for_status()
                data = await response.json()
                if not isinstance(data, dict):
                    raise TypeError("Jina response payload must be an object")

                raw_results = data.get("data", [])
                if not isinstance(raw_results, list):
                    raise TypeError("Jina response data must be a list")

                results = [_parse_result(item) for item in raw_results]

                return SearchResponse(
                    results=results,
                    total_results=len(results),
                    query_used=query,
                    provider=self.name,
                )
