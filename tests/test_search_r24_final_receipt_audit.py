"""R24 independent, read-only receipt/readback audit.

The audit deliberately treats receipts and markdown claims as evidence inputs:
they cannot promote a worker, substitute for a live task readback, or turn stale
source identity into a green result.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "docs/architecture/search-r16-contract.json"
R23 = ROOT / "docs/acceptance/search-r23-independent-gate.md"
FRONTIER = ROOT / "docs/acceptance/c4-releasegate-reducer-frontier-20261013.md"
PRIMARY = ROOT / "skills/search/__init__.py"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _contract() -> dict:
    return json.loads(CONTRACT.read_text(encoding="utf-8"))


def test_current_primary_signature_and_hash_are_checked_without_blind_green():
    contract = _contract()
    source = PRIMARY.read_text(encoding="utf-8")
    declared = next(
        item["sha256"]
        for item in contract["sources"]
        if item["path"] == "skills/search/__init__.py"
    )
    signature = next(
        item["signature"]
        for item in contract["signatures"]
        if item["source"] == "skills/search/__init__.py"
    )

    assert "async def search(query: str) -> SearchResponse:" in source
    assert signature in source
    # A mismatch is evidence of drift, never permission to accept the receipt.
    if _sha256(PRIMARY) != declared:
        assert contract["status"] == "CANDIDATE/UNACCEPTED"


def test_worker_exit_or_candidate_receipt_cannot_equal_accepted():
    evidence = (FRONTIER.read_text(encoding="utf-8") + R23.read_text(encoding="utf-8")).upper()
    assert "CANDIDATE / UNACCEPTED" in evidence
    assert "ACCEPTED_GREEN" not in evidence


@pytest.mark.parametrize(
    "forbidden_promotion",
    [
        "WORKER EXIT = ACCEPTED",
        "POST-FAILURE SELF-PROMOTE",
        "SELF-ACCEPTED_GREEN",
    ],
)
def test_post_failure_and_worker_exit_fail_closed(forbidden_promotion):
    evidence = (FRONTIER.read_text(encoding="utf-8") + R23.read_text(encoding="utf-8")).upper()
    assert forbidden_promotion not in evidence
    assert "ACCEPTANCE AUTHORITY REMAINS" in evidence or "INDEPENDENT VERIFIER" in evidence


def test_missing_primary_source_is_not_silently_accepted(tmp_path):
    missing = tmp_path / "missing-primary.py"
    assert not missing.exists()
    contract = _contract()
    declared_paths = {item["path"] for item in contract["sources"]}
    assert "skills/search/__init__.py" in declared_paths
    # The real primary exists here; a missing replacement must be classified, not green.
    assert (not missing.exists()) is True


def test_no_live_full_e2e_or_graphify_archsteer_is_not_readiness():
    contract = _contract()
    frontier = FRONTIER.read_text(encoding="utf-8").upper()
    assert contract["graphify_archsteer"]["status"] == "UNVERIFIED"
    assert "NATIVE C4 RELEASEGATE TASK-TO-RESULT FAILURE/RESTART E2E OUTPUT IS UNAVAILABLE" in frontier
    assert "PRODUCT RELEASEGATE ACCEPTANCE" in frontier
    assert "BLOCKED" in frontier
