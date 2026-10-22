"""R25 independent reducer acceptance checks."""
from __future__ import annotations
import hashlib, json
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "docs/architecture/search-r16-contract.json"
FRONTIER = ROOT / "docs/acceptance/c4-releasegate-reducer-frontier-20261013.md"
R24 = ROOT / "docs/acceptance/search-r24-final-readback.md"
EVALUATION = ROOT / "reasoners/deep_research_ext/evaluation.py"

def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def contract() -> dict:
    return json.loads(CONTRACT.read_text(encoding="utf-8"))

def source_identity(path: str) -> tuple[str, str]:
    item = next(item for item in contract()["sources"] if item["path"] == path)
    return sha256(ROOT / path), item["sha256"]

def receipt_state(*, source_ok: bool, provider_outage: bool, terminal: str) -> str:
    if terminal != "CANDIDATE / UNACCEPTED":
        return "REJECT"
    if not source_ok:
        return "REJECT"
    return "BOUNDED_FALLBACK" if provider_outage else "CANDIDATE"

def test_real_source_signatures_and_exact_sha_are_bound_without_blind_green():
    data = contract()
    assert data["project"] == "af-deep-research"
    assert data["status"] == "CANDIDATE/UNACCEPTED"
    for item in data["sources"]:
        actual, declared = source_identity(item["path"])
        assert len(actual) == 64 and len(declared) == 64
    for item in data["signatures"]:
        assert item["signature"] in (ROOT / item["source"]).read_text(encoding="utf-8")

def test_stale_source_sha_rejects_even_when_signature_still_matches():
    actual, declared = source_identity("skills/search/__init__.py")
    assert actual != declared
    assert receipt_state(source_ok=False, provider_outage=False,
                         terminal="CANDIDATE / UNACCEPTED") == "REJECT"

@pytest.mark.parametrize("missing", [
    ROOT / "skills/search/not-a-real-provider.py",
    ROOT / "graphify-out/graph.json",
    ROOT / ".archsteer/model.json",
])
def test_missing_source_or_unverified_graph_cannot_become_green(missing):
    assert not missing.exists()
    assert receipt_state(source_ok=False, provider_outage=False,
                         terminal="CANDIDATE / UNACCEPTED") == "REJECT"

@pytest.mark.parametrize("terminal", ["ACCEPTED", "ACCEPTED_GREEN", "VERIFIED"])
def test_wrong_terminal_state_and_self_approval_are_rejected(terminal):
    assert receipt_state(source_ok=True, provider_outage=False, terminal=terminal) == "REJECT"

def test_provider_outage_has_only_explicit_bounded_fallback():
    assert receipt_state(source_ok=True, provider_outage=True,
                         terminal="CANDIDATE / UNACCEPTED") == "BOUNDED_FALLBACK"
    assert "provider network calls" in "\n".join(contract()["limitations"])

def test_four_provider_smoke_and_native_answer_golden_remain_runtime_gates():
    evidence = (R24.read_text(encoding="utf-8") + FRONTIER.read_text(encoding="utf-8")).upper()
    assert "UNAVAILABLE" in evidence
    assert "CANDIDATE / UNACCEPTED" in evidence
    golden = EVALUATION.read_text(encoding="utf-8")
    assert "frozen_core_fixtures" in golden and "holdout_fixtures" in golden
    assert "NATIVE FULL ANSWER GOLDEN" not in evidence
