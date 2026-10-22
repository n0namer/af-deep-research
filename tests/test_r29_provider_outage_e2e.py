"""Provider outage and deterministic fail-closed acceptance checks.

These tests exercise the real federated-search orchestration module with small
in-process provider doubles at its public interface boundary. They do not mock
the orchestration function under test.
"""

import asyncio

import pytest

from skills.search import federated


class _Provider:
    def __init__(self, name, outcome):
        self.name = name
        self._outcome = outcome

    def is_available(self):
        return True

    async def search(self, query):
        if isinstance(self._outcome, BaseException):
            raise self._outcome
        return self._outcome


class _Response:
    def __init__(self, provider):
        self.provider = provider
        self.results = []
        self.query_used = "outage-check"


def test_one_provider_outage_returns_deterministic_partial_response(monkeypatch):
    healthy = _Provider("healthy", _Response("healthy"))
    unavailable = _Provider("outage-503", RuntimeError("503 capacity exhausted"))

    result = asyncio.run(
        federated.search_with_providers("outage-check", [healthy, unavailable])
    )

    assert result.provider == "federated"
    assert result.providers_used == ["healthy"]
    assert result.provider_errors == {"outage-503": "RuntimeError"}


def test_all_provider_outage_fails_closed_with_provider_names():
    providers = [
        _Provider("provider-429", RuntimeError("429 too many requests")),
        _Provider("provider-503", RuntimeError("503 unavailable")),
    ]

    with pytest.raises(RuntimeError, match="All federated search providers failed"):
        asyncio.run(federated.search_with_providers("outage-check", providers))


def test_provider_selection_deduplicates_and_applies_capacity_bound(monkeypatch):
    providers = {
        name: _Provider(name, _Response(name))
        for name in ("a", "b", "c")
    }
    monkeypatch.setattr(federated, "get_provider", providers.get)
    monkeypatch.setenv("SEARCH_FEDERATED_MAX_PROVIDERS", "2")

    selected = federated.select_federated_providers(["a", "a", "b", "c"])

    assert [provider.name for provider in selected] == ["a", "b"]


def test_invalid_capacity_configuration_is_bounded_and_cannot_disable_selection(monkeypatch):
    providers = {
        name: _Provider(name, _Response(name))
        for name in ("a", "b")
    }
    monkeypatch.setattr(federated, "get_provider", providers.get)
    monkeypatch.setenv("SEARCH_FEDERATED_MAX_PROVIDERS", "not-an-int")

    selected = federated.select_federated_providers(["a", "b"])

    assert [provider.name for provider in selected] == ["a", "b"]
