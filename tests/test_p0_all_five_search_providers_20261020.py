"""Ensure all five configured search providers are admitted by the existing federated selector.

No external API calls. The explicit bound must not silently exclude Firecrawl.
"""
from dataclasses import dataclass
import importlib

import pytest

federated = importlib.import_module("skills.search.federated")


@dataclass
class Provider:
    name: str

    def is_available(self):
        return True


PROVIDERS = ("brave", "perplexity", "tavily", "jina", "firecrawl")


def test_five_configured_search_providers_are_not_truncated(monkeypatch):
    monkeypatch.setenv("SEARCH_FEDERATED_MAX_PROVIDERS", "5")
    monkeypatch.delenv("SEARCH_PROVIDERS", raising=False)
    monkeypatch.setattr(federated, "get_available_providers", lambda: [Provider(x) for x in PROVIDERS])
    selected = federated.select_federated_providers()
    assert [p.name for p in selected] == list(PROVIDERS)


def test_explicit_five_providers_are_selected_in_order(monkeypatch):
    monkeypatch.setenv("SEARCH_FEDERATED_MAX_PROVIDERS", "5")
    monkeypatch.setenv("SEARCH_PROVIDERS", "brave,perplexity,tavily,jina,firecrawl")
    monkeypatch.setattr(federated, "get_provider", lambda name: Provider(name))
    selected = federated.select_federated_providers()
    assert [p.name for p in selected] == list(PROVIDERS)


def test_cap_still_applies_and_ignores_duplicates(monkeypatch):
    monkeypatch.setenv("SEARCH_FEDERATED_MAX_PROVIDERS", "5")
    monkeypatch.setenv("SEARCH_PROVIDERS", "brave,perplexity,tavily,jina,firecrawl,brave,serper")
    monkeypatch.setattr(federated, "get_provider", lambda name: Provider(name))
    selected = federated.select_federated_providers()
    assert [p.name for p in selected] == list(PROVIDERS)
