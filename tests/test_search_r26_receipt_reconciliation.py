"""Independent R26 receipt reconciliation checks.

This file deliberately tests the acceptance boundary only. It does not mock a
full search run, call providers, mutate CrewSync, or promote a worker receipt.
"""
from __future__ import annotations

from typing import Any

TASK_KEY = "af-deep-research:v2-r26-receipt-reconciliation-20261015-r1"
SOURCE_SHA = "98fae3d2e5259526139558c7cf492a9c96817606a2e486c7f1d22074772633c2"


def reconcile_receipts(*, source_sha: str | None, worker: dict[str, Any] | None,
                       independent_qa: dict[str, Any] | None) -> dict[str, Any]:
    """Return a fail-closed decision without self-acceptance."""
    if source_sha != SOURCE_SHA:
        return {"status": "BLOCKED", "reason": "source_sha_missing_or_mismatched"}
    if not worker:
        return {"status": "BLOCKED", "reason": "typed_worker_result_missing"}
    if worker.get("task_key") != TASK_KEY:
        return {"status": "BLOCKED", "reason": "worker_task_key_mismatch"}
    if worker.get("outcome") != "CANDIDATE":
        return {"status": "BLOCKED", "reason": "worker_not_candidate"}
    if worker.get("acceptance") != {"level": "UNACCEPTED"}:
        return {"status": "BLOCKED", "reason": "worker_self_acceptance_or_bad_shape"}
    if not independent_qa:
        return {"status": "BLOCKED", "reason": "independent_qa_receipt_missing"}
    if independent_qa.get("status") != "PASS":
        return {"status": "BLOCKED", "reason": "independent_qa_not_pass"}
    if independent_qa.get("task_key") == TASK_KEY:
        return {"status": "BLOCKED", "reason": "self_qa_is_not_independent"}
    return {"status": "READY_TO_COMPLETE", "reason": "source_and_independent_qa_bound",
            "acceptance": "UNACCEPTED"}


def _candidate() -> dict[str, Any]:
    return {"schema": "go-core.worker-result.v1", "task_key": TASK_KEY,
            "outcome": "CANDIDATE", "acceptance": {"level": "UNACCEPTED"}}


def test_source_bound_candidate_with_independent_qa_is_ready_without_self_green() -> None:
    assert reconcile_receipts(
        source_sha=SOURCE_SHA, worker=_candidate(),
        independent_qa={"task_key": "independent-qa-r26", "status": "PASS"},
    ) == {"status": "READY_TO_COMPLETE",
          "reason": "source_and_independent_qa_bound", "acceptance": "UNACCEPTED"}


def test_missing_independent_qa_refuses_false_accepted_green() -> None:
    assert reconcile_receipts(
        source_sha=SOURCE_SHA, worker=_candidate(), independent_qa=None,
    ) == {"status": "BLOCKED", "reason": "independent_qa_receipt_missing"}


def test_self_approval_and_accepted_green_are_rejected() -> None:
    worker = _candidate()
    worker["acceptance"] = {"level": "ACCEPTED_GREEN"}
    assert reconcile_receipts(
        source_sha=SOURCE_SHA, worker=worker,
        independent_qa={"task_key": TASK_KEY, "status": "PASS"},
    ) == {"status": "BLOCKED",
          "reason": "worker_self_acceptance_or_bad_shape"}


def test_process_success_without_typed_result_is_blocked() -> None:
    assert reconcile_receipts(
        source_sha=SOURCE_SHA, worker=None,
        independent_qa={"task_key": "independent-qa-r26", "status": "PASS"},
    ) == {"status": "BLOCKED", "reason": "typed_worker_result_missing"}
