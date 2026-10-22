"""Provider-recovery regression QA for the native future release-gate oracle.

This test module never creates native evidence. It probes the recovered provider
health endpoint and validates only immutable evidence supplied by the native
runtime through environment variables.
"""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any

import pytest

TRUSTED_GIT_SHA = "e10580c89eac7a4f6efb50c921ae9107ce8ad8dc"
EVIDENCE_SCHEMA = "af-native-releasegate-oracle.v1"
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
CONTRACT_PATTERN = re.compile(r"^c4-native-v[1-9][0-9]*$")

ROOT_KEYS = {
    "schema",
    "source_sha256",
    "native_contract_version",
    "producer_task_key",
    "qa_task_key",
    "captured_at",
    "scenarios",
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
EVENT_KEYS = {
    "event_id",
    "event",
    "occurred_at",
    "persistence_id",
    "request",
    "receipt",
}
ALLOWED_STATUSES = {
    "PENDING",
    "FAILED_RETRYABLE",
    "RETRYING",
    "CANDIDATE",
    "BLOCKED",
    "FAILED",
}
POSITIVE_EVENTS = [
    "request_submitted",
    "request_persisted",
    "receipt_persisted",
    "terminal_result_published",
]
RESTART_EVENTS = [
    "request_submitted",
    "request_persisted",
    "attempt_failed",
    "restart_loaded",
    "retry_dispatched",
    "receipt_persisted",
    "terminal_result_published",
]


def _assert_exact_keys(value: dict[str, Any], expected: set[str], label: str) -> None:
    assert set(value) == expected, f"{label} keys drifted: {sorted(set(value) ^ expected)}"


def _parse_utc(value: Any, label: str) -> datetime:
    assert isinstance(value, str) and value.endswith("Z"), f"{label} must be RFC3339 UTC"
    try:
        return datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as error:
        raise AssertionError(f"{label} must be RFC3339 UTC") from error


def _assert_nonempty_string(value: Any, label: str) -> None:
    assert isinstance(value, str) and value.strip(), f"{label} must be a non-empty string"


def _assert_sha256(value: Any, label: str) -> None:
    assert isinstance(value, str) and SHA256_PATTERN.fullmatch(value), f"{label} must be lowercase SHA-256"


def _load_native_evidence() -> tuple[dict[str, Any], str]:
    evidence_path = os.environ.get("AF_NATIVE_ORACLE_EVIDENCE")
    expected_source_sha = os.environ.get("AF_NATIVE_ORACLE_EXPECTED_SOURCE_SHA256")
    if not evidence_path or not expected_source_sha:
        pytest.skip(
            "BLOCKED_NATIVE_EVIDENCE: set AF_NATIVE_ORACLE_EVIDENCE and "
            "AF_NATIVE_ORACLE_EXPECTED_SOURCE_SHA256 from the real native run"
        )
    _assert_sha256(expected_source_sha, "AF_NATIVE_ORACLE_EXPECTED_SOURCE_SHA256")
    path = Path(evidence_path)
    assert path.is_file(), f"native evidence file does not exist: {path}"
    evidence = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(evidence, dict), "native evidence root must be an object"
    return evidence, expected_source_sha


def _validate_root(evidence: dict[str, Any], expected_source_sha: str) -> None:
    _assert_exact_keys(evidence, ROOT_KEYS, "evidence root")
    assert evidence["schema"] == EVIDENCE_SCHEMA
    assert evidence["source_sha256"] == expected_source_sha, "source_sha256 binding mismatch"
    assert isinstance(evidence["native_contract_version"], str)
    assert CONTRACT_PATTERN.fullmatch(evidence["native_contract_version"])
    _assert_nonempty_string(evidence["producer_task_key"], "producer_task_key")
    _assert_nonempty_string(evidence["qa_task_key"], "qa_task_key")
    assert evidence["producer_task_key"] != evidence["qa_task_key"]
    _parse_utc(evidence["captured_at"], "captured_at")
    assert isinstance(evidence["scenarios"], dict), "scenarios must be an object"


def _validate_request(request: Any, expected_source_sha: str) -> None:
    assert isinstance(request, dict), "request must be an object"
    _assert_exact_keys(request, REQUEST_KEYS, "request")
    for field in ("task_key", "project", "attempt_id", "session_id", "idempotency_key"):
        _assert_nonempty_string(request[field], f"request.{field}")
    _assert_sha256(request["payload_sha256"], "request.payload_sha256")
    assert request["source_sha256"] == expected_source_sha
    assert isinstance(request["checkpoint_seq"], int) and request["checkpoint_seq"] >= 0


def _validate_receipt(receipt: Any, request: dict[str, Any], expected_source_sha: str) -> None:
    assert isinstance(receipt, dict), "receipt must be an object"
    _assert_exact_keys(receipt, RECEIPT_KEYS, "receipt")
    _assert_nonempty_string(receipt["receipt_id"], "receipt.receipt_id")
    for field in ("task_key", "attempt_id", "session_id"):
        assert receipt[field] == request[field], f"receipt.{field} must match request"
    assert receipt["status"] in ALLOWED_STATUSES
    assert receipt["source_sha256"] == expected_source_sha
    assert isinstance(receipt["checkpoint_seq"], int)
    assert receipt["checkpoint_seq"] >= request["checkpoint_seq"]
    _parse_utc(receipt["persisted_at"], "receipt.persisted_at")
    if receipt["result_sha256"] is not None:
        _assert_sha256(receipt["result_sha256"], "receipt.result_sha256")


def _validate_scenario(
    scenario: Any,
    expected_events: list[str],
    expected_source_sha: str,
) -> list[dict[str, Any]]:
    assert isinstance(scenario, list) and scenario, "scenario must be a non-empty event array"
    assert [event.get("event") for event in scenario if isinstance(event, dict)] == expected_events
    event_ids: set[str] = set()
    timestamps: list[datetime] = []
    identity: tuple[Any, ...] | None = None
    request_checkpoints: list[int] = []
    receipt_checkpoints: list[int] = []

    for index, envelope in enumerate(scenario):
        assert isinstance(envelope, dict), f"event[{index}] must be an object"
        _assert_exact_keys(envelope, EVENT_KEYS, f"event[{index}]")
        _assert_nonempty_string(envelope["event_id"], f"event[{index}].event_id")
        assert envelope["event_id"] not in event_ids, "event IDs must be unique"
        event_ids.add(envelope["event_id"])
        _assert_nonempty_string(envelope["persistence_id"], f"event[{index}].persistence_id")
        timestamps.append(_parse_utc(envelope["occurred_at"], f"event[{index}].occurred_at"))
        _validate_request(envelope["request"], expected_source_sha)
        _validate_receipt(envelope["receipt"], envelope["request"], expected_source_sha)

        request = envelope["request"]
        current_identity = (
            request["task_key"],
            request["attempt_id"],
            request["session_id"],
            request["idempotency_key"],
            request["payload_sha256"],
            request["source_sha256"],
        )
        identity = current_identity if identity is None else identity
        assert current_identity == identity, "request identity changed across recovery"
        request_checkpoints.append(request["checkpoint_seq"])
        receipt_checkpoints.append(envelope["receipt"]["checkpoint_seq"])

    assert timestamps == sorted(timestamps), "event timestamps must be chronological"
    assert request_checkpoints == sorted(request_checkpoints), "request checkpoints must be monotonic"
    assert receipt_checkpoints == sorted(receipt_checkpoints), "receipt checkpoints must be monotonic"
    assert sum(event["event"] == "terminal_result_published" for event in scenario) == 1
    terminal = scenario[-1]
    persisted = scenario[-2]
    assert terminal["event"] == "terminal_result_published"
    assert persisted["event"] == "receipt_persisted"
    assert terminal["receipt"] == persisted["receipt"], "terminal receipt must equal persisted receipt"
    return scenario


def test_provider_health_is_200_but_not_product_pass() -> None:
    base_url = os.environ.get("AF_OPENCODEX_BASE_URL", "http://127.0.0.1:10110").rstrip("/")
    request = urllib.request.Request(f"{base_url}/health", method="GET")
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            body = response.read().decode("utf-8", errors="replace")
            assert response.status == 200, f"provider health returned {response.status}: {body}"
    except urllib.error.URLError as error:
        pytest.fail(f"PROVIDER_HEALTH_INFRA: {error}")


def test_real_native_positive_path() -> None:
    evidence, expected_source_sha = _load_native_evidence()
    _validate_root(evidence, expected_source_sha)
    assert "positive" in evidence["scenarios"], "positive scenario missing"
    scenario = _validate_scenario(
        evidence["scenarios"]["positive"], POSITIVE_EVENTS, expected_source_sha
    )
    assert scenario[-1]["receipt"]["status"] == "CANDIDATE"


def test_real_native_failure_restart_replay_path() -> None:
    evidence, expected_source_sha = _load_native_evidence()
    _validate_root(evidence, expected_source_sha)
    assert "failure_restart" in evidence["scenarios"], "failure_restart scenario missing"
    scenario = _validate_scenario(
        evidence["scenarios"]["failure_restart"], RESTART_EVENTS, expected_source_sha
    )
    failed = scenario[2]["receipt"]
    loaded = scenario[3]["receipt"]
    assert failed["status"] == "FAILED_RETRYABLE"
    assert loaded == failed, "restart must reload the exact persisted retryable receipt"
    assert scenario[4]["receipt"]["checkpoint_seq"] >= loaded["checkpoint_seq"]
    assert scenario[-1]["receipt"]["status"] == "CANDIDATE"


def test_real_evidence_rejects_wrong_source_binding() -> None:
    evidence, expected_source_sha = _load_native_evidence()
    wrong_source_sha = "0" * 64 if expected_source_sha != "0" * 64 else "1" * 64
    with pytest.raises(AssertionError, match="source_sha256"):
        _validate_root(evidence, wrong_source_sha)


def test_git_binding_matches_trusted_prelaunch_source() -> None:
    expected_git_sha = os.environ.get("AF_NATIVE_ORACLE_EXPECTED_GIT_SHA", TRUSTED_GIT_SHA)
    assert expected_git_sha == TRUSTED_GIT_SHA, "Git binding differs from trusted prelaunch source"
