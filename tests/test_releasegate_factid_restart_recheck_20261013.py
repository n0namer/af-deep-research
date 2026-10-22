import json
import os
from pathlib import Path

import pytest


EXPECTED_SCHEMA = "af-deep-research.native-e2e-receipt.v1"
EXPECTED_SOURCE_SHA = "e10580c89eac7a4f6efb50c921ae9107ce8ad8dc"
FORBIDDEN_PROVIDER_MARKERS = (
    "dummy",
    "fake",
    "fixture",
    "mock",
    "simulat",
    "stub",
    "synthetic",
    "test-double",
)


def _load_native_receipt() -> dict:
    receipt_path = os.environ.get("AF_NATIVE_E2E_RECEIPT")
    if not receipt_path:
        pytest.fail(
            "BLOCKED: AF_NATIVE_E2E_RECEIPT must point to a native C4 E2E receipt"
        )

    path = Path(receipt_path).resolve()
    assert path.is_file(), f"BLOCKED: native receipt does not exist: {path}"
    receipt = json.loads(path.read_text(encoding="utf-8"))

    assert receipt.get("schema") == EXPECTED_SCHEMA
    assert receipt.get("native_execution") is True
    assert receipt.get("source", {}).get("git") == EXPECTED_SOURCE_SHA

    provider_identity = receipt.get("provider", {}).get("identity")
    assert isinstance(provider_identity, str) and provider_identity.strip(), (
        "provider.identity is required"
    )
    lowered_identity = provider_identity.casefold()
    assert not any(marker in lowered_identity for marker in FORBIDDEN_PROVIDER_MARKERS)
    assert receipt.get("provider", {}).get("mode") == "native-local"
    assert receipt.get("provider", {}).get("outbound_network") is False

    events = receipt.get("events")
    assert isinstance(events, list) and events, "native receipt must contain events"
    return receipt


@pytest.fixture(scope="module")
def native_receipt() -> dict:
    return _load_native_receipt()


def _event(receipt: dict, scenario: str, phase: str) -> dict:
    matches = [
        event
        for event in receipt["events"]
        if event.get("scenario") == scenario and event.get("phase") == phase
    ]
    assert len(matches) == 1, (
        f"expected exactly one {scenario}/{phase} event, found {len(matches)}"
    )
    return matches[0]


def _cited_fact_ids(event: dict) -> list[str]:
    citations = event.get("result", {}).get("citations", [])
    assert isinstance(citations, list)
    assert all(isinstance(citation, dict) for citation in citations)
    fact_ids = [citation.get("fact_id") for citation in citations]
    assert all(isinstance(fact_id, str) and fact_id for fact_id in fact_ids)
    return fact_ids


def test_positive_answer_cites_each_required_fact_id_exactly(native_receipt: dict) -> None:
    event = _event(native_receipt, "positive_exact_citation", "completed")
    required_fact_ids = event.get("request", {}).get("required_fact_ids")
    assert isinstance(required_fact_ids, list) and required_fact_ids
    assert len(required_fact_ids) == len(set(required_fact_ids))

    cited_fact_ids = _cited_fact_ids(event)
    assert cited_fact_ids == required_fact_ids
    assert event.get("result", {}).get("status") == "answered"


def test_negative_contamination_never_enters_answer_or_citations(
    native_receipt: dict,
) -> None:
    event = _event(native_receipt, "negative_contamination", "completed")
    contaminated_fact_ids = event.get("request", {}).get("contaminated_fact_ids")
    assert isinstance(contaminated_fact_ids, list) and contaminated_fact_ids

    cited_fact_ids = set(_cited_fact_ids(event))
    assert cited_fact_ids.isdisjoint(contaminated_fact_ids)

    answer = event.get("result", {}).get("answer", "")
    assert isinstance(answer, str)
    contamination_tokens = event.get("request", {}).get("contamination_tokens")
    assert isinstance(contamination_tokens, list) and contamination_tokens
    assert all(isinstance(token, str) and token for token in contamination_tokens)
    lowered_answer = answer.casefold()
    assert all(token.casefold() not in lowered_answer for token in contamination_tokens)


def test_contaminated_only_evidence_abstains_without_citations(
    native_receipt: dict,
) -> None:
    event = _event(native_receipt, "contaminated_only_abstention", "completed")
    assert event.get("result", {}).get("status") == "abstained"
    assert event.get("result", {}).get("answer") in (None, "")
    assert _cited_fact_ids(event) == []


def test_crash_checkpoint_is_persisted_and_resumed_by_new_process(
    native_receipt: dict,
) -> None:
    crashed = _event(native_receipt, "persistent_restart", "crashed")
    resumed = _event(native_receipt, "persistent_restart", "resumed")
    completed = _event(native_receipt, "persistent_restart", "completed")

    assert crashed.get("checkpoint", {}).get("persisted") is True
    checkpoint_id = crashed.get("checkpoint", {}).get("id")
    checkpoint_sequence = crashed.get("checkpoint", {}).get("sequence")
    assert isinstance(checkpoint_id, str) and checkpoint_id
    assert isinstance(checkpoint_sequence, int) and checkpoint_sequence >= 0

    assert resumed.get("resume", {}).get("checkpoint_id") == checkpoint_id
    assert resumed.get("resume", {}).get("from_sequence") == checkpoint_sequence
    assert resumed.get("run_id") == crashed.get("run_id") == completed.get("run_id")
    assert resumed.get("process_id") != crashed.get("process_id")
    assert completed.get("checkpoint", {}).get("sequence", -1) > checkpoint_sequence
    assert completed.get("result", {}).get("status") == "answered"

    required_fact_ids = completed.get("request", {}).get("required_fact_ids")
    assert isinstance(required_fact_ids, list) and required_fact_ids
    assert len(required_fact_ids) == len(set(required_fact_ids))
    assert _cited_fact_ids(completed) == required_fact_ids
