"""Independent r30 receipt reducer for r29 evidence fan-in.

This test is deliberately source-bound and conservative: a receipt is eligible only
when its evidence is complete and independently verified. Missing evidence is
BLOCKED, never silently promoted to DONE.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

import pytest

ROOT = Path(__file__).parents[1]
SOURCE_FILES = (
    ROOT / "reasoners/deep_research_ext/research_run.py",
    ROOT / "reasoners/deep_research_ext/verified_pipeline.py",
)
EXPECTED_SOURCE_SHA = {
    "reasoners/deep_research_ext/research_run.py":
        "87c193a386be13daa2b89dceac6b749a87ae9b47efd84b18bd598017c6e9e8c3",
    "reasoners/deep_research_ext/verified_pipeline.py":
        "97cf7e84e8f62c1190d1b5a6c4ac59be6d175e336be8dd1db3b64b9ea81dbd87",
}


@dataclass(frozen=True)
class Receipt:
    key: str
    worker_outcome: str
    source_sha256: str | None
    test_exit: int | None
    independent_qa: bool
    tests_present: bool
    stale_source: bool = False
    false_done: bool = False


def source_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def reduce_receipt(receipt: Receipt, *, current_source_sha: str) -> str:
    """Return only the conservative per-key state used by the reducer."""
    if not receipt.key or receipt.false_done:
        return "BLOCKED"
    if receipt.worker_outcome != "WORKER_COMPLETED":
        return "BLOCKED"
    if receipt.stale_source or receipt.source_sha256 != current_source_sha:
        return "BLOCKED"
    if receipt.test_exit != 0 or not receipt.tests_present:
        return "BLOCKED"
    if not receipt.independent_qa:
        return "BLOCKED"
    return "ELIGIBLE"


def _receipt(**overrides: object) -> Receipt:
    values: dict[str, object] = {
        "key": "af-deep-research:v2-r29-primary-source-eval-20261015-r1",
        "worker_outcome": "WORKER_COMPLETED",
        "source_sha256": "a" * 64,
        "test_exit": 0,
        "independent_qa": True,
        "tests_present": True,
    }
    values.update(overrides)
    return Receipt(**values)


def test_positive_real_sources_and_complete_receipt_are_eligible():
    current = source_sha256(SOURCE_FILES[0])
    receipt = _receipt(source_sha256=current)
    assert SOURCE_FILES[0].is_file()
    assert len(current) == 64
    assert reduce_receipt(receipt, current_source_sha=current) == "ELIGIBLE"


@pytest.mark.parametrize(
    "overrides",
    [
        {"independent_qa": False},
        {"stale_source": True},
        {"tests_present": False},
        {"test_exit": 1},
    ],
)
def test_negative_missing_qa_stale_source_or_missing_tests_is_blocked(overrides):
    current = source_sha256(SOURCE_FILES[0])
    assert reduce_receipt(_receipt(source_sha256=current, **overrides),
                          current_source_sha=current) == "BLOCKED"


def test_negative_worker_completed_is_not_done_without_true_independent_qa():
    current = source_sha256(SOURCE_FILES[0])
    receipt = _receipt(independent_qa=False)
    assert receipt.worker_outcome == "WORKER_COMPLETED"
    assert reduce_receipt(receipt, current_source_sha=current) == "BLOCKED"


def test_negative_false_done_and_missing_key_are_blocked():
    current = source_sha256(SOURCE_FILES[0])
    assert reduce_receipt(
        _receipt(false_done=True, source_sha256=current),
        current_source_sha=current,
    ) == "BLOCKED"
    assert reduce_receipt(
        _receipt(key="", source_sha256=current),
        current_source_sha=current,
    ) == "BLOCKED"


def test_current_source_receipts_are_bound_to_expected_hashes():
    observed = {path.relative_to(ROOT).as_posix(): source_sha256(path) for path in SOURCE_FILES}
    assert observed == EXPECTED_SOURCE_SHA
