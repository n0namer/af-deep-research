"""R29 reducer oracle for typed CrewSync DONE/refill evidence.

This lane is intentionally source-bound: the inspected project exposes Python
research DTOs, while CrewSync transport is coordinator-owned and unavailable
to this repository scope.  The oracle therefore rejects unverifiable claims.
"""
from __future__ import annotations

import hashlib
import inspect
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]
READABLE_SOURCES = (
    ROOT / "reasoners/deep_research_ext/research_run.py",
    ROOT / "reasoners/deep_research_ext/verified_pipeline.py",
)


@dataclass(frozen=True)
class DoneReceipt:
    task_key: str
    outcome: str
    recorded_at: str
    source_sha256: str
    test_exit: int
    refill_ready: bool


def _is_iso_utc(value: str) -> bool:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return parsed.tzinfo is not None and parsed.utcoffset() == timezone.utc.utcoffset(parsed)


def reduce_done(receipt: DoneReceipt) -> bool:
    """Return DONE/refill only when all evidence gates are explicit and valid."""
    if not receipt.task_key or receipt.outcome != "CANDIDATE":
        return False
    if not _is_iso_utc(receipt.recorded_at):
        return False
    if not re.fullmatch(r"[0-9a-f]{64}", receipt.source_sha256):
        return False
    if receipt.test_exit != 0 or not receipt.refill_ready:
        return False
    return True


def _receipt(**overrides) -> DoneReceipt:
    source_hash = hashlib.sha256(
        b"source-bound evidence: no live CrewSync state in project scope"
    ).hexdigest()
    values = dict(
        task_key="af-deep-research:v2-r29-crew-done-reducer-20261015-r1",
        outcome="CANDIDATE",
        recorded_at="2026-10-15T12:00:00Z",
        source_sha256=source_hash,
        test_exit=0,
        refill_ready=True,
    )
    values.update(overrides)
    return DoneReceipt(**values)


def test_positive_real_source_interfaces_and_done_refill_oracle():
    assert all(path.is_file() for path in READABLE_SOURCES)
    research_run = __import__(
        "reasoners.deep_research_ext.research_run", fromlist=["checkpoint_research_run"]
    )
    pipeline = __import__(
        "reasoners.deep_research_ext.verified_pipeline",
        fromlist=["execute_verified_pipeline"],
    )
    assert "expected_checkpoint_seq" in inspect.signature(
        research_run.checkpoint_research_run
    ).parameters
    assert "source_file_sha256" in inspect.signature(
        pipeline.build_grounded_verified_report
    ).parameters
    assert reduce_done(_receipt()) is True


@pytest.mark.parametrize(
    "overrides",
    [
        {"recorded_at": "2026-10-15 12:00:00"},
        {"recorded_at": "not-a-timestamp"},
        {"source_sha256": "sha-unavailable"},
        {"source_sha256": "a" * 63},
    ],
)
def test_adversarial_invalid_timestamp_or_source_identity_rejected(overrides):
    assert reduce_done(_receipt(**overrides)) is False


@pytest.mark.parametrize(
    "overrides",
    [
        {"outcome": "ACCEPTED_GREEN"},
        {"test_exit": 1},
        {"refill_ready": False},
        {"task_key": ""},
    ],
)
def test_adversarial_terminal_or_refill_claims_rejected(overrides):
    assert reduce_done(_receipt(**overrides)) is False


def test_adversarial_naive_datetime_cannot_pass():
    assert reduce_done(_receipt(recorded_at="2026-10-15T12:00:00")) is False
