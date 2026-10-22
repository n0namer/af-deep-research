"""Independent r16 search release-gate reducer.

This file is deliberately self-contained: it reduces observed receipts and never
calls providers, mutates live task state, or promotes an untrusted candidate.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


LAYERS = (
    "ADAPTER_REAL_PASS",
    "FEDERATED_ENGINE_PASS",
    "PACKAGE_ROUTING_PASS",
    "MAIN_INTEGRATION_PASS",
    "FACT_ID_BRIDGE_PASS",
    "NATIVE_FULL_RESEARCH_PASS",
)
VERIFIED_PIPELINE_SHA256 = (
    "97cf7e84e8f62c1190d1b5a6c4ac59be6d175e336be8dd1db3b64b9ea81dbd87"
)


def artifact_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_report(raw: str | dict[str, Any]) -> dict[str, Any]:
    """Parse the reducer report boundary without accepting an unknown schema."""
    try:
        report = json.loads(raw) if isinstance(raw, str) else raw
    except (TypeError, ValueError) as exc:
        raise ValueError("report is not valid JSON") from exc
    if not isinstance(report, dict):
        raise ValueError("report must be a mapping")
    if report.get("schema") != "search-r16-releasegate-reducer.v1":
        raise ValueError("unsupported report schema")
    if report.get("status") not in {"PENDING_UNACCEPTED", "FAIL"}:
        raise ValueError("report has invalid reducer status")
    return report


def _fail(reason: str) -> dict[str, Any]:
    return {"status": "FAIL", "reason": reason}


def _infra(reason: str) -> dict[str, Any]:
    return {"status": "INFRA_BLOCKED", "reason": reason}


def validate_observed_layer(
    layer: str,
    receipt: dict[str, Any],
    *,
    expected_sha256: str,
) -> dict[str, Any]:
    """Validate one observed layer without treating a label as runtime proof."""
    if layer not in LAYERS:
        return _fail("unknown release-gate layer")
    if receipt.get("status") != "PASS":
        if receipt.get("error_code") == 429:
            return _infra("provider returned HTTP 429")
        return _fail("layer did not produce an observed PASS")
    if receipt.get("mock_only") is True:
        return _fail("mock-only evidence cannot produce a gold PASS")
    if receipt.get("observed_runtime") is not True:
        return _fail("runtime observation is absent")
    if receipt.get("source_sha256") != expected_sha256:
        return _fail("stale or mismatched source SHA")
    providers = receipt.get("providers")
    if not isinstance(providers, list) or not providers:
        return _fail("missing provider evidence")
    if any(
        not isinstance(provider, dict)
        or not provider.get("name")
        or provider.get("status") != "success"
        for provider in providers
    ):
        return _fail("provider evidence is incomplete")
    source_ids = receipt.get("source_ids")
    citations = receipt.get("citations")
    if not isinstance(source_ids, list) or not source_ids:
        return _fail("missing source IDs")
    if not isinstance(citations, list) or not citations:
        return _fail("missing citation evidence")
    declared = set(source_ids)
    for citation in citations:
        if not isinstance(citation, dict):
            return _fail("citation is not a mapping")
        if citation.get("source_id") not in declared:
            return _fail("citation references an undeclared source ID")
        if citation.get("verified") is not True or not citation.get("quote"):
            return _fail("citation is fake or unverified")
        if citation.get("source_sha256") != expected_sha256:
            return _fail("citation has stale source SHA")
    return {"status": "PASS", "evidence": "observed runtime and exact SHA bound"}


def reduce_release_gate(
    receipts: dict[str, dict[str, Any]],
    *,
    expected_sha256: str,
    independent_qa: dict[str, Any] | None,
) -> dict[str, Any]:
    """Return a typed reduction; acceptance is intentionally external."""
    layers = {
        layer: validate_observed_layer(
            layer, receipts.get(layer, {}), expected_sha256=expected_sha256
        )
        for layer in LAYERS
    }
    qa_ready = (
        isinstance(independent_qa, dict)
        and independent_qa.get("status") == "PASS"
        and independent_qa.get("source_sha256") == expected_sha256
        and independent_qa.get("fresh_runtime") is True
    )
    all_layers_pass = all(result["status"] == "PASS" for result in layers.values())
    return {
        "schema": "search-r16-releasegate-reducer.v1",
        "layers": layers,
        "independent_qa": "PASS" if qa_ready else "MISSING",
        "status": "PENDING_UNACCEPTED",
        "accepted_green": False,
        "reason": (
            "candidate evidence is never self-accepted"
            if all_layers_pass and qa_ready
            else "one or more release gates lack admissible evidence"
        ),
    }


def future_frontier_tasks() -> list[dict[str, Any]]:
    """Future work is dependency-ready but ownership remains unclaimed."""
    return [
        {
            "id": "r17-adapter-and-federated-live-receipt",
            "depends_on": [],
            "owner": None,
            "dod": "fresh four-provider receipt with exact source SHA and provider outcomes",
        },
        {
            "id": "r17-native-research-qa",
            "depends_on": ["r17-adapter-and-federated-live-receipt"],
            "owner": None,
            "dod": "independent QA receipt covering citation and restart boundaries",
        },
        {
            "id": "r17-reducer-refill",
            "depends_on": ["r17-native-research-qa"],
            "owner": None,
            "dod": "reduce only after the preceding receipts are independently readable",
        },
    ]


def _good_receipt(sha: str = VERIFIED_PIPELINE_SHA256) -> dict[str, Any]:
    return {
        "status": "PASS",
        "observed_runtime": True,
        "source_sha256": sha,
        "providers": [{"name": "provider-a", "status": "success"}],
        "source_ids": ["src-1"],
        "citations": [
            {
                "source_id": "src-1",
                "source_sha256": sha,
                "verified": True,
                "quote": "Observed source-backed fact.",
            }
        ],
    }


def test_report_parser_accepts_typed_candidate_and_rejects_bad_inputs():
    candidate = {
        "schema": "search-r16-releasegate-reducer.v1",
        "status": "PENDING_UNACCEPTED",
    }
    assert parse_report(json.dumps(candidate)) == candidate
    for raw in ("not-json", "[]", '{"schema":"unknown","status":"FAIL"}'):
        try:
            parse_report(raw)
        except ValueError:
            pass
        else:
            raise AssertionError("invalid report accepted")


def test_artifact_checksum_readback_is_source_bound():
    path = Path(__file__).parents[1] / "reasoners/deep_research_ext/verified_pipeline.py"
    assert artifact_sha256(path) == VERIFIED_PIPELINE_SHA256


def test_all_layers_pass_individually_but_reducer_stays_unaccepted_without_qa():
    receipts = {layer: _good_receipt() for layer in LAYERS}
    result = reduce_release_gate(
        receipts, expected_sha256=VERIFIED_PIPELINE_SHA256, independent_qa=None
    )
    assert all(item["status"] == "PASS" for item in result["layers"].values())
    assert result["independent_qa"] == "MISSING"
    assert result["status"] == "PENDING_UNACCEPTED"
    assert result["accepted_green"] is False


def test_missing_provider_is_rejected():
    receipt = _good_receipt()
    receipt["providers"] = []
    assert validate_observed_layer(
        LAYERS[0], receipt, expected_sha256=VERIFIED_PIPELINE_SHA256
    )["status"] == "FAIL"


def test_fake_citation_and_bad_source_id_are_rejected():
    receipt = _good_receipt()
    receipt["citations"][0]["verified"] = False
    assert validate_observed_layer(
        LAYERS[0], receipt, expected_sha256=VERIFIED_PIPELINE_SHA256
    )["status"] == "FAIL"
    receipt = _good_receipt()
    receipt["citations"][0]["source_id"] = "invented"
    assert validate_observed_layer(
        LAYERS[0], receipt, expected_sha256=VERIFIED_PIPELINE_SHA256
    )["status"] == "FAIL"


def test_stale_sha_is_rejected_even_when_everything_else_looks_green():
    receipt = _good_receipt("0" * 64)
    assert validate_observed_layer(
        LAYERS[0], receipt, expected_sha256=VERIFIED_PIPELINE_SHA256
    )["status"] == "FAIL"


def test_mock_only_gold_pass_is_rejected():
    receipt = _good_receipt()
    receipt["mock_only"] = True
    assert validate_observed_layer(
        LAYERS[0], receipt, expected_sha256=VERIFIED_PIPELINE_SHA256
    )["status"] == "FAIL"


def test_429_is_distinguished_as_infrastructure_block():
    receipt = {"status": "ERROR", "error_code": 429}
    result = validate_observed_layer(
        LAYERS[1], receipt, expected_sha256=VERIFIED_PIPELINE_SHA256
    )
    assert result == {"status": "INFRA_BLOCKED", "reason": "provider returned HTTP 429"}


def test_future_frontier_has_dependencies_without_invented_ownership():
    tasks = future_frontier_tasks()
    ids = {task["id"] for task in tasks}
    assert all(task["owner"] is None for task in tasks)
    assert tasks[1]["depends_on"] == [tasks[0]["id"]]
    assert tasks[2]["depends_on"] == [tasks[1]["id"]]
    assert all(set(task["depends_on"]) <= ids for task in tasks)


def test_missing_layer_is_not_synthesized_from_other_passes():
    receipts = {layer: _good_receipt() for layer in LAYERS[:-1]}
    result = reduce_release_gate(
        receipts,
        expected_sha256=VERIFIED_PIPELINE_SHA256,
        independent_qa={
            "status": "PASS",
            "source_sha256": VERIFIED_PIPELINE_SHA256,
            "fresh_runtime": True,
        },
    )
    assert result["layers"][LAYERS[-1]]["status"] == "FAIL"
    assert result["status"] == "PENDING_UNACCEPTED"
