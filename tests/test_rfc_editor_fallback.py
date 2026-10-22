import asyncio

import pytest

from skills.search import get_default_provider
from skills.search.rfc_editor import RFCEditorSearchProvider, rfc_numbers_in


def test_rfc_editor_fallback_is_selected_without_search_credentials(monkeypatch):
    for name in (
        "BRAVE_SEARCH_API_KEY", "PERPLEXITY_API_KEY", "TAVILY_API_KEY",
        "KAGI_API_TOKEN", "JINA_API_KEY", "FIRECRAWL_API_KEY", "SERPER_API_KEY",
    ):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.delenv("SEARCH_PROVIDER", raising=False)
    assert get_default_provider().name == "rfc_editor"


def test_credentialed_provider_remains_preferred_over_rfc_fallback(monkeypatch):
    monkeypatch.delenv("SEARCH_PROVIDER", raising=False)
    monkeypatch.setenv("JINA_API_KEY", "test-key")
    assert get_default_provider().name == "jina"


def test_rfc_editor_fallback_only_accepts_explicit_rfc_queries():
    assert rfc_numbers_in("What does RFC 9114 specify about HTTP/3?") == ("9114",)
    with pytest.raises(ValueError, match="explicit RFC number"):
        asyncio.run(RFCEditorSearchProvider().search("What is HTTP/3?"))


def test_rfc_editor_fallback_returns_primary_rfc_url(monkeypatch):
    provider = RFCEditorSearchProvider()

    async def fake_fetch(number):
        assert number == "9114"
        return "RFC 9114: HTTP/3"

    monkeypatch.setattr(provider, "_fetch_rfc", fake_fetch)
    response = asyncio.run(provider.search("What does RFC 9114 specify about HTTP/3?"))
    assert response.provider == "rfc_editor"
    assert response.results[0].url == "https://www.rfc-editor.org/rfc/rfc9114.txt"
    assert response.results[0].content == "RFC 9114: HTTP/3"
