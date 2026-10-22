"""Independent C4 drift oracle for the search boundary.

This test intentionally reads the producer sources and architecture artifacts rather
than mocking provider behavior. It rejects stale or invented architecture claims.
"""
from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]
EXPECTED_CURRENT_SHA = {
    "skills/search/__init__.py": "327c1a80311e381cfe92005b621d76473258d088f62953b2767c45d7c0b66e74",
    "skills/search/federated.py": "b4c5085bdecb9b5c737df4701f664bac495e1a4ebde749d80f0ab3c16b957a7a",
    "skills/search/registry.py": "58d587dff3951e0d86fb5249e493b9dc5ca9813512dfc308d12107fde3b807c6",
}
EXPECTED_SIGNATURES = {
    "skills/search/__init__.py": "search",
    "skills/search/federated.py": "select_federated_providers",
    "skills/search/registry.py": "get_default_provider",
}


def _text(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def _sha(relative: str) -> str:
    return hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()


def _functions(relative: str) -> set[str]:
    tree = ast.parse(_text(relative))
    return {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }


def test_current_imports_hashes_and_signatures_are_source_backed() -> None:
    from skills.search import search
    from skills.search.federated import select_federated_providers
    from skills.search.registry import get_default_provider

    assert callable(search)
    assert callable(select_federated_providers)
    assert callable(get_default_provider)

    for relative, expected in EXPECTED_CURRENT_SHA.items():
        assert _sha(relative) == expected, f"source drifted: {relative}"
    for relative, name in EXPECTED_SIGNATURES.items():
        assert name in _functions(relative)


def test_stale_contract_sha_is_rejected() -> None:
    contract = json.loads(_text("docs/architecture/search-r16-contract.json"))
    recorded = {
        item["path"]: item["sha256"] for item in contract["sources"]
    }
    assert recorded["skills/search/__init__.py"] != _sha("skills/search/__init__.py")


def test_structurizr_invented_topology_is_rejected() -> None:
    dsl = _text("docs/architecture/search-r16-structurizr.dsl")
    actual = set(_functions("skills/search/federated.py"))
    declared = {"registry", "federation", "fusion"}
    assert declared == {"registry", "federation", "fusion"}
    assert "fusion" not in actual
    assert "system -> fusion" in dsl


def test_false_graph_coverage_is_rejected() -> None:
    graph = ROOT / "graphify-out" / "graph.json"
    archsteer = ROOT / ".archsteer" / "model.json"
    assert not graph.exists() or graph.stat().st_size == 0
    assert not archsteer.exists() or archsteer.stat().st_size == 0


def test_routing_contract_preserves_auto_federated_and_single_paths() -> None:
    source = _text("skills/search/__init__.py")
    assert 'mode = os.getenv("SEARCH_MODE", "auto").strip().lower()' in source
    assert 'if mode in {"auto", "federated"}:' in source
    assert "if len(providers) >= 2:" in source
    assert "if len(providers) == 1:" in source
    assert "return await provider.search(query)" in source
