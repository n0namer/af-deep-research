"""Fresh source-bound architecture golden QA oracle for search-r16 artifacts."""
from __future__ import annotations
import hashlib, json, re
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "docs/architecture/search-r16-contract.json"
CONTEXT = ROOT / "docs/architecture/search-r16-c4-context.mmd"
COMPONENT = ROOT / "docs/architecture/search-r16-c4-component.mmd"

EXPECTED_SOURCES = {
    "skills/search/__init__.py": "07e2f88feea292fe3b645b142639d41bd9ff6cbd25a2f8f2b2ae5a3a3d0b6f10",
    "skills/search/registry.py": "58d587dff3951e0d86fb5249e493b9dc5ca9813512dfc308d12107fde3b807c6",
    "skills/search/federated.py": "b4c5085bdecb9b5c737df4701f664bac495e1a4ebde749d80f0ab3c16b957a7a",
    "skills/search/fusion.py": "c7c0684e8d5d55df099ebf7690bfceafff78e79fe4ad15a6265ecb29a5a5625c",
    "main.py": "5bebcfd28bd954561aaa5fcc7654dbb5615d4a552d9daaa4656db42cc76649c8",
}
EXPECTED_SIGNATURES = {
    "skills/search/__init__.py": "async def search(query: str) -> SearchResponse:",
    "skills/search/registry.py": "def get_default_provider() -> Optional[SearchProvider]:",
    "skills/search/federated.py": "def select_federated_providers(provider_names: Optional[Sequence[str]] = None) -> List[SearchProvider]:",
    "skills/search/fusion.py": "def canonicalize_url(url: str) -> str:",
    "skills/search/fusion.py": "def fuse_search_responses(",
    "main.py": "async def search_web_for_content(query: str) -> List[Dict]:",
}

def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def load_contract() -> dict:
    return json.loads(CONTRACT.read_text(encoding="utf-8"))

def assert_current_source_identity(contract: dict) -> None:
    documented = {item["path"]: item["sha256"] for item in contract["sources"]}
    assert documented == EXPECTED_SOURCES
    for relative, expected in EXPECTED_SOURCES.items():
        source = ROOT / relative
        assert source.is_file(), relative
        assert sha256(source) == expected, relative

def assert_live_signatures(contract: dict) -> None:
    documented = {(item["source"], item["signature"]) for item in contract["signatures"]}
    assert documented == set(EXPECTED_SIGNATURES.items())
    for relative, signature in EXPECTED_SIGNATURES.items():
        assert signature in (ROOT / relative).read_text(encoding="utf-8"), relative

def topology_labels() -> set[str]:
    text = CONTEXT.read_text(encoding="utf-8") + COMPONENT.read_text(encoding="utf-8")
    return set(re.findall(r"\b(?:Caller|Search System|Search Skill|Provider Registry|Federated Search|Fusion)\b", text))

def assert_topology_is_source_bound(contract: dict) -> None:
    graph = contract["diagrams"]
    assert {item["level"] for item in graph} >= {"context", "component"}
    assert "caller" in graph[0]["nodes"] and "system" in graph[0]["nodes"]
    assert topology_labels()
    for item in graph:
        for node in item["nodes"]:
            assert node.islower() or "_" in node, node

def reject_stale_or_promoted(contract: dict, baseline: str) -> None:
    assert contract["baseline_commit"] == baseline
    assert contract["status"] == "CANDIDATE/UNACCEPTED"

def test_fresh_contract_matches_live_sources():
    contract = load_contract()
    assert_current_source_identity(contract)
    assert_live_signatures(contract)
    assert_topology_is_source_bound(contract)
    reject_stale_or_promoted(contract, "e10580c89eac7a4f6efb50c921ae9107ce8ad8dc")

def test_negative_rejects_forged_source_hash():
    contract = load_contract()
    contract["sources"][0]["sha256"] = "0" * 64
    with pytest.raises(AssertionError):
        assert_current_source_identity(contract)

def test_negative_rejects_forged_topology_node():
    contract = load_contract()
    contract["diagrams"][0]["nodes"].append("untrusted_external_system")
    with pytest.raises(AssertionError):
        assert_topology_is_source_bound(contract)

def test_negative_rejects_stale_as_of_or_promoted_status():
    contract = load_contract()
    contract["baseline_commit"] = "stale-as-of"
    with pytest.raises(AssertionError):
        reject_stale_or_promoted(contract, "e10580c89eac7a4f6efb50c921ae9107ce8ad8dc")
    contract = load_contract()
    contract["status"] = "ACCEPTED_GREEN"
    with pytest.raises(AssertionError):
        reject_stale_or_promoted(contract, "e10580c89eac7a4f6efb50c921ae9107ce8ad8dc")

def test_negative_rejects_signature_drift():
    contract = load_contract()
    contract["signatures"][0]["signature"] = "async def forged(query):"
    with pytest.raises(AssertionError):
        assert_live_signatures(contract)
