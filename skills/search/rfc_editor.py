"""Unauthenticated, narrowly-scoped retrieval from the RFC Editor."""

import re

import aiohttp

from .base import SearchProvider, SearchResponse, SearchResult


_RFC_NUMBER = re.compile(r"\brfc\s*(\d{3,5})\b", re.IGNORECASE)
_RFC_URL = "https://www.rfc-editor.org/rfc/rfc{number}.txt"


def rfc_numbers_in(query: str):
    """Return distinct RFC identifiers explicitly named by a query."""
    return tuple(dict.fromkeys(_RFC_NUMBER.findall(query or "")))


class RFCEditorSearchProvider(SearchProvider):
    """Fetch explicitly requested RFCs from their primary public publisher.

    This is deliberately not a general web-search replacement.  It is only
    available for queries that name an RFC and it neither accepts nor requires
    credentials.
    """

    @property
    def name(self) -> str:
        return "rfc_editor"

    @property
    def api_key_env_var(self) -> str:
        return ""

    def is_available(self) -> bool:
        return True

    async def _fetch_rfc(self, number: str) -> str:
        timeout = aiohttp.ClientTimeout(total=20)
        # RFC primary text is fetched directly.  This must not inherit a
        # workstation proxy setting: R4 proved the configured proxy refuses
        # connections while the authoritative host is reachable directly.
        # This environment's optional aiodns resolver also times out for this
        # host despite socket.getaddrinfo succeeding, so force aiohttp onto
        # its threaded (standard-library socket) resolver.
        connector = aiohttp.TCPConnector(resolver=aiohttp.ThreadedResolver())
        async with aiohttp.ClientSession(
            timeout=timeout, trust_env=False, connector=connector
        ) as session:
            async with session.get(_RFC_URL.format(number=number)) as response:
                response.raise_for_status()
                return await response.text()

    async def search(self, query: str) -> SearchResponse:
        numbers = rfc_numbers_in(query)
        if not numbers:
            raise ValueError("rfc_editor fallback requires an explicit RFC number")

        results = []
        for number in numbers:
            content = await self._fetch_rfc(number)
            url = _RFC_URL.format(number=number)
            results.append(SearchResult(
                title=f"RFC {number}",
                url=url,
                content=content,
                description=f"Primary RFC Editor text for RFC {number}",
            ))
        return SearchResponse(
            results=results,
            total_results=len(results),
            query_used=query,
            provider=self.name,
        )
