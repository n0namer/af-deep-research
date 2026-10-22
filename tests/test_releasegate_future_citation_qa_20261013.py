"""Independent native ReleaseGate oracle over immutable runtime evidence.

Reproducible command (PowerShell):
    $env:AF_NATIVE_ORACLE_EVIDENCE='C:\path\native-oracle-evidence.json'
    $env:AF_NATIVE_ORACLE_EXPECTED_SOURCE_SHA='<64 lowercase hex chars>'
    python -m pytest -q tests/test_releasegate_future_citation_qa_20261013.py

The evidence file must be produced by the native implementation. This test never
creates a fake transport, persistence adapter, receipt, restart, or retry.
"""

from __future__ import annotations

import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any

import pytest

SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
TIMESTAMP_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$")
CONTRACT_VERSION_RE = re.compile(r"^c4-native-v\d+$")

ROOT_KEYS = {
    "schema",
    "source_sha256",
    "native_contract_version",
    "producer_task_key",
    "qa_task_key",
    "captured_at",
    "scenarios",
}
SCENARIO_KEYS = {"name", "events"}
EVENT_KEYS = {
    "event_id",
    "event",
    "occurred_at",
    "persistence_id",
    "request",
    "receipt",
}
REQUEST_KEYS = {
    "task_key",
    "project",
    "attempt_id",
    "session_id",
    "payload_sha256",
    "source_sha256",
    "idempotency_key",
    "checkpoint_seq",
}
RECEIPT_KEYS = {
    "receipt_id",
    "task_key",
    "attempt_id",
    "session_id",
    "status",
    "source_sha256",
    "checkpoint_seq",
    "persisted_at",
    "result_sha256",
}
ALLOWED_EVENTS = {
    "request_submitted",
    "request_persisted",
    "attempt_failed",
    "restart_loaded",
    "retry_dispatched",
    "receipt_persisted",
    "terminal_result_published",
}
ALLOWED_RECEIPT_STATUSES = {
    "PENDING",
    "FAILED_RETRYABLE",
    "RETRYING",
    "CANDIDATE",
    "BLOCKED",
    "FAILED",
}


def _assert_exact_keys(value: dict[str, Any], expected: set[str], label: str) -> None:
    assert set(value) == expected, (
        f"{label} DTO signature drift: expected {sorted(expected)}, "
        f"received {sorted(value)}"
    )


def _assert_sha(value: Any, label: str) -> None:
    assert isinstance(value, str) and SHA256_RE.fullmatch(value), (
        f"{label} must be a lowercase SHA-256"
    )


def _parse_timestamp(value: Any, label: str) -> datetime:
    assert isinstance(value, str) and TIMESTAMP_RE.fullmatch(value), (
        f"{label} must be an RFC3339 UTC timestamp"
    )
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _load_evidence() -> dict[str, Any]:
    evidence_path = os.environ.get("AF_NATIVE_ORACLE_EVIDENCE")
    expected_source_sha = os.environ.get("AF_NATIVE_ORACLE_EXPECTED_SOURCE_SHA")
    if not evidence_path or not expected_source_sha:
        pytest.skip(
            "live native evidence unavailable: set AF_NATIVE_ORACLE_EVIDENCE and "
            "AF_NATIVE_ORACLE_EXPECTED_SOURCE_SHA"
        )

    _assert_sha(expected_source_sha, "AF_NATIVE_ORACLE_EXPECTED_SOURCE_SHA")
    path = Path(evidence_path).resolve(strict=True)
    assert path.is_file(), "AF_NATIVE_ORACLE_EVIDENCE must resolve to a file"

    evidence = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(evidence, dict), "oracle evidence root must be a JSON object"
    _assert_exact_keys(evidence, ROOT_KEYS, "evidence root")
    assert evidence["schema"] == "af-native-releasegate-oracle.v1"
    assert evidence["source_sha256"] == expected_source_sha
    _assert_sha(evidence["source_sha256"], "evidence source_sha256")
    assert CONTRACT_VERSION_RE.fullmatch(evidence["native_contract_version"])
    assert isinstance(evidence["producer_task_key"], str) and evidence["producer_task_key"]
    assert isinstance(evidence["qa_task_key"], str) and evidence["qa_task_key"]
    assert evidence["producer_task_key"] != evidence["qa_task_key"], (
        "producer and independent QA task keys must differ"
    )
    _parse_timestamp(evidence["captured_at"], "evidence captured_at")
    assert isinstance(evidence["scenarios"], list) and evidence["scenarios"]
    return evidence


def _scenario(evidence: dict[str, Any], name: str) -> list[dict[str, Any]]:
    assert all(isinstance(item, dict) for item in evidence["scenarios"]), (
        "every scenario must be a JSON object"
    )
    matches = [item for item in evidence["scenarios"] if item.get("name") == name]
    assert len(matches) == 1, f"expected exactly one {name!r} scenario"
    scenario = matches[0]
    assert isinstance(scenario, dict)
    _assert_exact_keys(scenario, SCENARIO_KEYS, f"scenario {name}")
    assert isinstance(scenario["events"], list) and scenario["events"]
    return scenario["events"]


def _validate_event(
    event: dict[str, Any], source_sha: str, contract_version: str
) -> None:
    assert isinstance(event, dict)
    _assert_exact_keys(event, EVENT_KEYS, f"event {event.get('event_id', '<missing>')}")
    assert isinstance(event["event_id"], str) and event["event_id"]
    assert event["event"] in ALLOWED_EVENTS
    _parse_timestamp(event["occurred_at"], f"event {event['event_id']} occurred_at")
    assert isinstance(event["persistence_id"], str) and event["persistence_id"]

    request = event["request"]
    assert isinstance(request, dict)
    _assert_exact_keys(request, REQUEST_KEYS, f"event {event['event_id']} request")
    for key in ("task_key", "project", "attempt_id", "session_id", "idempotency_key"):
        assert isinstance(request[key], str) and request[key]
    _assert_sha(request["payload_sha256"], "request payload_sha256")
    assert request["source_sha256"] == source_sha
    assert isinstance(request["checkpoint_seq"], int) and request["checkpoint_seq"] >= 0

    receipt = event["receipt"]
    if receipt is None:
        assert event["event"] in {"request_submitted", "request_persisted"}
        return

    assert isinstance(receipt, dict)
    _assert_exact_keys(receipt, RECEIPT_KEYS, f"event {event['event_id']} receipt")
    for key in ("receipt_id", "task_key", "attempt_id", "session_id"):
        assert isinstance(receipt[key], str) and receipt[key]
    assert receipt["status"] in ALLOWED_RECEIPT_STATUSES
    assert receipt["source_sha256"] == source_sha
    assert isinstance(receipt["checkpoint_seq"], int) and receipt["checkpoint_seq"] >= 0
    _parse_timestamp(receipt["persisted_at"], "receipt persisted_at")
    if receipt["result_sha256"] is not None:
        _assert_sha(receipt["result_sha256"], "receipt result_sha256")

    for identity_key in ("task_key", "attempt_id", "session_id"):
        assert receipt[identity_key] == request[identity_key]
    assert receipt["checkpoint_seq"] >= request["checkpoint_seq"]
    assert contract_version.startswith("c4-native-v")


def _validate_scenario_events(
    evidence: dict[str, Any], scenario_name: str
) -> list[dict[str, Any]]:
    events = _scenario(evidence, scenario_name)
    event_ids: set[str] = set()
    timestamps: list[datetime] = []
    for event in events:
        _validate_event(
            event,
            evidence["source_sha256"],
            evidence["native_contract_version"],
        )
        assert event["event_id"] not in event_ids, "event IDs must be unique"
        event_ids.add(event["event_id"])
        timestamps.append(
            _parse_timestamp(event["occurred_at"], f"event {event['event_id']} occurred_at")
        )
    assert timestamps == sorted(timestamps), "events must be chronologically ordered"
    return events


def test_positive_request_receipt_persistence_oracle() -> None:
    evidence = _load_evidence()
    events = _validate_scenario_events(evidence, "positive")
    event_names = [event["event"] for event in events]
    assert event_names == [
        "request_submitted",
        "request_persisted",
        "receipt_persisted",
        "terminal_result_published",
    ]

    requests = [event["request"] for event in events]
    identity = (
        requests[0]["task_key"],
        requests[0]["attempt_id"],
        requests[0]["session_id"],
        requests[0]["idempotency_key"],
    )
    assert all(
        (
            request["task_key"],
            request["attempt_id"],
            request["session_id"],
            request["idempotency_key"],
        )
        == identity
        for request in requests
    )

    persisted = events[-2]["receipt"]
    published = events[-1]["receipt"]
    assert persisted == published, "published terminal receipt must equal persisted receipt"
    assert published["status"] == "CANDIDATE"
    _assert_sha(published["result_sha256"], "positive terminal result_sha256")


def test_failure_restart_retry_recovery_oracle() -> None:
    evidence = _load_evidence()
    events = _validate_scenario_events(evidence, "failure_restart")
    event_names = [event["event"] for event in events]
    assert event_names == [
        "request_submitted",
        "request_persisted",
        "attempt_failed",
        "restart_loaded",
        "retry_dispatched",
        "receipt_persisted",
        "terminal_result_published",
    ]

    requests = [event["request"] for event in events]
    assert len({request["task_key"] for request in requests}) == 1
    assert len({request["session_id"] for request in requests}) == 1
    assert len({request["idempotency_key"] for request in requests}) == 1
    assert len({request["payload_sha256"] for request in requests}) == 1
    assert len({request["source_sha256"] for request in requests}) == 1

    failed_receipt = events[2]["receipt"]
    restart_receipt = events[3]["receipt"]
    retry_receipt = events[4]["receipt"]
    terminal_receipt = events[-1]["receipt"]
    assert failed_receipt["status"] == "FAILED_RETRYABLE"
    assert restart_receipt == failed_receipt, (
        "restart must load the exact persisted failure receipt before retry"
    )
    assert retry_receipt["status"] == "RETRYING"
    assert retry_receipt["checkpoint_seq"] > failed_receipt["checkpoint_seq"]
    assert terminal_receipt["status"] == "CANDIDATE"
    assert terminal_receipt["checkpoint_seq"] >= retry_receipt["checkpoint_seq"]
    _assert_sha(terminal_receipt["result_sha256"], "recovered result_sha256")
    assert events[-2]["receipt"] == terminal_receipt, (
        "terminal result must be persisted before publication"
    )


def test_no_duplicate_terminal_or_stale_checkpoint_acceptance() -> None:
    evidence = _load_evidence()
    events = _validate_scenario_events(evidence, "failure_restart")
    terminal_events = [
        event for event in events if event["event"] == "terminal_result_published"
    ]
    assert len(terminal_events) == 1, "duplicate terminal publication is forbidden"

    checkpoints = [event["request"]["checkpoint_seq"] for event in events]
    assert checkpoints == sorted(checkpoints), "stale request checkpoints are forbidden"
    receipt_checkpoints = [
        event["receipt"]["checkpoint_seq"]
        for event in events
        if event["receipt"] is not None
    ]
    assert receipt_checkpoints == sorted(receipt_checkpoints), (
        "stale receipt checkpoints are forbidden"
    )
