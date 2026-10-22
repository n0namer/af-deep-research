"""Live, native AgentField Deep Research benchmark with frozen multi-domain questions.

Opt-in: DR_LIVE_BENCH=1 python -m pytest -s -q tests/test_p0_native_agentfield_benchmark_20261019.py
No direct reasoner calls, no agentfield restarts, and no blind POST retries.
Historical deterministic tests are intentionally retained unchanged.
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import os
import re
import time
from pathlib import Path
from urllib.parse import urlsplit

import aiohttp
import pytest

FIXTURE = Path(__file__).parent / "fixtures" / "native_agentfield_deep_research_cases_20261019.json"
CASES = json.loads(FIXTURE.read_text(encoding="utf-8"))
SERVER = os.getenv("DR_BENCH_AGENTFIELD_URL", "http://127.0.0.1:8080").rstrip("/")
TARGET = "meta_deep_research.execute_verified_deep_research"
RUN_DIR = Path(os.getenv("DR_LIVE_BENCH_OUT", r"D:\Temp\af-deep-research-p0-20261019\native-multidomain-v1"))
MAX_RUNNING = min(4, max(1, int(os.getenv("DR_BENCH_CONCURRENCY", "3"))))
MAX_SECONDS = max(60, int(os.getenv("DR_BENCH_CASE_TIMEOUT", "720")))
ABSTAIN = (
    "not yet", "not known", "not been announced", "cannot be known",
    "cannot verify", "cannot be verified", "cannot identify",
    "does not exist", "doesn't exist", "not published",
    "no published", "no official", "no such", "not available",
    "not possible to", "no reliable", "unverified", "no evidence",
    "no record", "has not been awarded", "no known",
)


def score_result(case: dict, execution: dict) -> dict:
    """Transparent structural and anchor rubric; not semantic fact entailment."""
    result = execution.get("result") or {}
    report = result.get("research_package") or {}
    if not isinstance(report, dict):
        report = {}
    sections = report.get("sections") or []
    notes = report.get("source_notes") or []
    summary = report.get("executive_summary") or ""
    document = "\n".join(
        [str(report.get("document_title") or ""), str(summary)]
        + [str(section.get("title") or "") + "\n" + str(section.get("content") or "")
           for section in sections if isinstance(section, dict)]
    )
    folded = document.casefold()
    anchors = [
        any(str(alias).casefold() in folded for alias in aliases)
        for aliases in case.get("required", [])
    ]
    url_items = [s for s in notes if isinstance(s, dict) and s.get("url")]
    valid_urls = [
        s for s in url_items
        if urlsplit(str(s["url"])).scheme in {"http", "https"}
        and bool(urlsplit(str(s["url"])).hostname)
    ]
    primary = any(
        ((urlsplit(str(s["url"])).hostname or "").casefold() == str(domain).casefold() or (urlsplit(str(s["url"])).hostname or "").casefold().endswith("." + str(domain).casefold()))
        for s in valid_urls for domain in case.get("primary_domains", [])
    )
    markers = set(re.findall(r"\[(\d+)\]", document))
    note_ids = {str(item.get("citation_id")) for item in url_items}
    missing_markers = sorted(markers - note_ids)
    dangling = any(not str(s.get("citation_id", "")).strip() for s in url_items)
    native_succeeded = execution.get("status") == "succeeded"
    report_ready = (
        bool(report.get("document_title"))
        and len(str(summary)) >= 40
        and len(sections) >= 1
        and len(document) >= 110
    )
    metadata = result.get("metadata") or {}
    extension = metadata.get("verified_research_extension") or {}
    coverage = (extension.get("coverage_state") or {}).get("verified_coverage_ratio")
    kind = case.get("kind", "answerable")
    is_abstained = any(token in folded for token in ABSTAIN)
    citation_integrity = not missing_markers and not dangling
    technical_pass = bool(
        native_succeeded and report_ready and citation_integrity
        and (kind != "answerable" or len(valid_urls) >= 1)
    )
    quality_flags = []
    if kind == "answerable":
        if not all(anchors):
            quality_flags.append("missing_expected_fact")
        if not primary:
            quality_flags.append("missing_primary_source")
        try:
            verified_ratio = float(coverage)
        except (ValueError, TypeError):
            verified_ratio = 0.0
        if verified_ratio < 1.0:
            quality_flags.append("insufficient_verified_coverage")
        if not markers:
            quality_flags.append("no_inline_citation")
        if any(phrase in str(summary).casefold() for phrase in (
            "does not establish", "requires corroboration", "cannot confirm",
            "cannot determine", "insufficient evidence to identify",
        )):
            quality_flags.append("explicit_answer_incomplete")
    elif not is_abstained:
        quality_flags.append("unsupported_question_not_abstained")
    quality_screen_pass = technical_pass and not quality_flags
    return {
        "quality_screen_pass": quality_screen_pass,
        "quality_flags": quality_flags,
        "native_succeeded": native_succeeded,
        "report_ready": report_ready,
        "technical_pass": technical_pass,
        "kind": kind,
        "source_notes": len(notes),
        "valid_source_urls": len(valid_urls),
        "primary_source_present": primary,
        "citations_in_text": len(markers),
        "dangling_citation_ids": missing_markers,
        "citation_integrity": citation_integrity,
        "gold_anchor_recall": round(sum(anchors) / len(anchors), 4) if anchors else None,
        "gold_anchor_hits": anchors,
        "abstention_cue_present": is_abstained if kind == "unanswerable" else None,
        "verified_requirement_coverage": coverage,
        "sections": len(sections),
        "document_characters": len(document),
        "source_domains": sorted({
            urlsplit(str(s["url"])).hostname for s in valid_urls
        }),
        "provider_events": len(metadata.get("provider_events") or []),
        "provider_errors": sum(
            1 for e in metadata.get("provider_events") or []
            if isinstance(e, dict) and e.get("status") == "error"
        ),
    }


def _atomic_json(path: Path, item: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".writing")
    tmp.write_text(json.dumps(item, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    os.replace(tmp, path)


def _load(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


async def _run_case(client: aiohttp.ClientSession, sem: asyncio.Semaphore, case: dict) -> dict:
    """Submit exactly once; resume polling existing execution on later invocations."""
    async with sem:
        case_id = case["id"]
        path = RUN_DIR / (case_id + ".json")
        receipt = _load(path)
        if receipt.get("final") and receipt.get("execution_id"):
            receipt["score"] = score_result(case, receipt["final"])
            _atomic_json(path, receipt)
            print(f"REUSED {case_id} status={receipt.get('status')} quality={receipt['score']['quality_screen_pass']}", flush=True)
            return receipt
        if not receipt.get("execution_id") and "submission_error" not in receipt:
            body = {
                "input": {
                    "query": case["query"],
                    **CASES["profile"],
                },
                "run_metadata": {
                    "display_name": "AFDR Native Bench / " + case_id,
                    "labels": ["afdr-native-eval", case["domain"]],
                },
            }
            # Native AgentField endpoint only. POST is deliberately never retried:
            # HTTP ambiguity could otherwise mint a second execution.
            try:
                async with client.post(
                    f"{SERVER}/api/v1/execute/async/{TARGET}",
                    json=body,
                    timeout=aiohttp.ClientTimeout(total=25),
                ) as response:
                    data = await response.json(content_type=None)
                    if response.status != 202 or not data.get("execution_id"):
                        raise RuntimeError(f"admission HTTP {response.status}: {str(data)[:180]}")
                receipt = {
                    "case_id": case_id, "domain": case["domain"],
                    "query": case["query"], "execution_id": data["execution_id"],
                    "run_id": data.get("run_id"), "status": data.get("status"),
                    "native_endpoint": f"/api/v1/execute/async/{TARGET}",
                    "admitted_at": time.time(), "source": "AgentField REST",
                }
                _atomic_json(path, receipt)
                print(f"ACCEPTED {case_id} {data['execution_id']}", flush=True)
            except Exception as exc:
                receipt = {
                    "case_id": case_id, "submission_error": repr(exc),
                    "admission_ambiguous": True, "status": "submission_unverified",
                }
                _atomic_json(path, receipt)
                print(f"SUBMISSION_UNVERIFIED {case_id} {type(exc).__name__}", flush=True)
                return receipt

        if "submission_error" in receipt:
            return receipt
        execution_id = receipt["execution_id"]
        started = time.monotonic()
        polling_errors = 0
        while time.monotonic() - started <= MAX_SECONDS:
            try:
                async with client.get(
                    f"{SERVER}/api/v1/executions/{execution_id}",
                    timeout=aiohttp.ClientTimeout(total=18),
                ) as response:
                    if response.status != 200:
                        raise RuntimeError(f"readback HTTP {response.status}")
                    execution = await response.json(content_type=None)
            except Exception:
                polling_errors += 1
                if polling_errors > 12:
                    receipt["polling_errors"] = polling_errors
                    _atomic_json(path, receipt)
                    print(f"READBACK_BLOCKED {case_id}", flush=True)
                    return receipt
                await asyncio.sleep(min(8, polling_errors * 2))
                continue
            if execution.get("status") in {"succeeded", "failed", "cancelled"}:
                receipt["final"] = execution
                receipt["status"] = execution["status"]
                receipt["completed_at"] = time.time()
                receipt["duration_ms"] = execution.get("duration_ms")
                receipt["score"] = score_result(case, execution)
                # A separate read after completion verifies AgentField durability,
                # not a copy of a local Python return value.
                async with client.get(
                    f"{SERVER}/api/v1/executions/{execution_id}",
                    timeout=aiohttp.ClientTimeout(total=18),
                ) as reread:
                    receipt["server_readback_http"] = reread.status
                    second = await reread.json(content_type=None) if reread.status == 200 else {}
                    receipt["server_readback_matches"] = (
                        second.get("execution_id") == execution_id
                        and second.get("status") == execution["status"]
                        and second.get("result") == execution.get("result")
                    )
                _atomic_json(path, receipt)
                print(
                    f"TERMINAL {case_id} {execution['status']} "
                    f"technical={receipt['score']['technical_pass']} "
                    f"anchor={receipt['score']['gold_anchor_recall']} "
                    f"sources={receipt['score']['valid_source_urls']}",
                    flush=True,
                )
                return receipt
            if int(time.monotonic() - started) % 30 < 4:
                print(f"IN_PROGRESS {case_id} {execution.get('status')}", flush=True)
            await asyncio.sleep(4)

        receipt["status"] = "poll_timeout"
        receipt["elapsed_s"] = round(time.monotonic() - started, 1)
        receipt["poll_timeout_not_terminal"] = True
        _atomic_json(path, receipt)
        print(f"POLL_TIMEOUT {case_id} existing={execution_id}", flush=True)
        return receipt


def test_frozen_domains_and_quality_rubric() -> None:
    cases = CASES["cases"]
    assert len(cases) >= 10
    assert len({c["id"] for c in cases}) == len(cases)
    assert len({c["domain"] for c in cases}) >= 9
    assert sum(c["kind"] == "unanswerable" for c in cases) >= 2
    for case in cases:
        assert case["query"].strip() and case["primary_domains"]
        assert case["kind"] in {"answerable", "unanswerable"}


def test_grade_rejects_fabricated_citation_and_missing_source() -> None:
    case = CASES["cases"][0]
    fake = {
        "status": "succeeded",
        "result": {"research_package": {
            "document_title": "RFC 9114",
            "executive_summary": "HTTP/3 uses QUIC, and RFC 9114 is authoritative.",
            "sections": [{"title": "Evidence", "content": "Claim [999] is supported. " * 8}],
            "source_notes": [{"citation_id": 1, "url": "https://www.rfc-editor.org/info/rfc9114/"}],
        }},
    }
    outcome = score_result(case, fake)
    assert outcome["native_succeeded"]
    assert not outcome["technical_pass"]
    assert outcome["dangling_citation_ids"] == ["999"]


@pytest.mark.asyncio
async def test_real_multidomain_agentfield_execute_through_opencodex() -> None:
    if os.getenv("DR_LIVE_BENCH") != "1":
        pytest.skip("External multi-topic AgentField benchmark is explicit opt-in")
    selected = {s.strip() for s in os.getenv("DR_LIVE_BENCH_IDS", "").split(",") if s.strip()}
    cases = [c for c in CASES["cases"] if not selected or c["id"] in selected]
    assert cases, "No selected cases found"
    print(
        f"AFDR_NATIVE_BENCH cases={len(cases)} max_concurrent={MAX_RUNNING} "
        f"timeout_per_case={MAX_SECONDS}s",
        flush=True,
    )
    connector = aiohttp.TCPConnector(limit=MAX_RUNNING * 3)
    async with aiohttp.ClientSession(trust_env=False, connector=connector) as client:
        async with client.get(f"{SERVER}/health", timeout=aiohttp.ClientTimeout(total=8)) as health:
            assert health.status == 200, f"AgentField health HTTP {health.status}"
        semaphore = asyncio.Semaphore(MAX_RUNNING)
        results = await asyncio.gather(*(_run_case(client, semaphore, c) for c in cases))
    summary = {
        "schema": "afdr-bench-summary-v1", "cases": len(cases),
        "completed": sum(bool(r.get("final")) for r in results),
        "succeeded": sum(r.get("status") == "succeeded" for r in results),
        "technical_pass": sum(bool((r.get("score") or {}).get("technical_pass")) for r in results),
        "quality_screen_pass": sum(bool((r.get("score") or {}).get("quality_screen_pass")) for r in results),
        "quality_flags": {r.get("case_id"): (r.get("score") or {}).get("quality_flags") for r in results if (r.get("score") or {}).get("quality_flags")},
        "confirmed_readback": sum(r.get("server_readback_matches") is True for r in results),
        "errors": [r["case_id"] for r in results if not (r.get("score") or {}).get("technical_pass")],
        "anchor_recall": {r.get("case_id"): (r.get("score") or {}).get("gold_anchor_recall") for r in results},
        "primary_source_present": {r.get("case_id"): (r.get("score") or {}).get("primary_source_present") for r in results},
        "abstention": {r.get("case_id"): (r.get("score") or {}).get("abstention_cue_present") for r in results if "negative" in r.get("case_id", "")},
        "output_dir": str(RUN_DIR),
        "note": "Anchor recall and source-domain match are screening proxies, NOT adjudicated factual or citation accuracy.",
    }
    _atomic_json(RUN_DIR / "summary.json", summary)
    print("AFDR_NATIVE_SUMMARY " + json.dumps(summary, ensure_ascii=False), flush=True)
    assert summary["technical_pass"] == len(cases), "At least one native E2E failed: inspect saved receipts"
    assert summary["confirmed_readback"] == len(cases), "Server persistence/readback not confirmed"
    assert summary["quality_screen_pass"] == len(cases), "At least one report has a source/claim/abstention quality blocker"


@pytest.mark.asyncio
async def test_native_client_uses_async_api_and_rereads_without_duplicate_post(tmp_path, monkeypatch):
    """API-contract test: one POST, exact native route, same saved ID on rerun."""
    from aiohttp import web
    monkeypatch.setattr(__import__(__name__, fromlist=["RUN_DIR"]), "RUN_DIR", tmp_path)
    call_count = {"post": 0, "get": 0}
    seen = []
    case = CASES["cases"][0]

    async def start(request):
        call_count["post"] += 1
        seen.append((request.path, await request.json()))
        return web.json_response(
            {"execution_id": "exec_fixture_native_1", "run_id": "run_fixture_1",
             "status": "queued"}, status=202,
        )

    async def read(request):
        call_count["get"] += 1
        return web.json_response({
            "execution_id": "exec_fixture_native_1", "run_id": "run_fixture_1",
            "status": "succeeded", "duration_ms": 200,
            "result": {"research_package": {
                "document_title": "RFC 9114",
                "executive_summary": "RFC 9114 defines HTTP/3 over QUIC with evidence from RFC Editor.",
                "sections": [{"title": "Provenance", "content": "The RFC 9114 standard specifies QUIC transport. [1]"}],
                "source_notes": [{"citation_id": 1, "url": "https://www.rfc-editor.org/info/rfc9114/"}],
            }},
        })

    app = web.Application()
    app.router.add_post("/api/v1/execute/async/" + TARGET, start)
    app.router.add_get("/api/v1/executions/{execution_id}", read)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "127.0.0.1", 0)
    await site.start()
    try:
        port = site._server.sockets[0].getsockname()[1]
        monkeypatch.setattr(__import__(__name__, fromlist=["SERVER"]), "SERVER", f"http://127.0.0.1:{port}")
        async with aiohttp.ClientSession(trust_env=False) as client:
            first = await _run_case(client, asyncio.Semaphore(1), case)
            again = await _run_case(client, asyncio.Semaphore(1), case)
        assert first["score"]["technical_pass"]
        assert first["server_readback_matches"] is True
        assert again["execution_id"] == "exec_fixture_native_1"
        assert call_count["post"] == 1
        assert call_count["get"] >= 2
        assert seen[0][0] == "/api/v1/execute/async/" + TARGET
        assert seen[0][1]["input"]["query"] == case["query"]
    finally:
        await runner.cleanup()


@pytest.mark.asyncio
async def test_native_client_does_not_blindly_retry_rejected_admission(tmp_path, monkeypatch):
    """A second test invocation must not create a duplicate unknown execution."""
    from aiohttp import web
    monkeypatch.setattr(__import__(__name__, fromlist=["RUN_DIR"]), "RUN_DIR", tmp_path)
    counter = {"posts": 0}
    case = CASES["cases"][0]

    async def reject(request):
        counter["posts"] += 1
        return web.json_response({"error": "queue overloaded"}, status=503)

    app = web.Application()
    app.router.add_post("/api/v1/execute/async/" + TARGET, reject)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "127.0.0.1", 0)
    await site.start()
    try:
        port = site._server.sockets[0].getsockname()[1]
        monkeypatch.setattr(__import__(__name__, fromlist=["SERVER"]), "SERVER", f"http://127.0.0.1:{port}")
        async with aiohttp.ClientSession(trust_env=False) as client:
            first = await _run_case(client, asyncio.Semaphore(1), case)
            second = await _run_case(client, asyncio.Semaphore(1), case)
        assert first["admission_ambiguous"] is True
        assert second["status"] == "submission_unverified"
        assert counter["posts"] == 1
    finally:
        await runner.cleanup()


def test_quality_gate_rejects_correct_words_without_verified_primary_evidence() -> None:
    case = CASES["cases"][0]
    record = {
        "status": "succeeded",
        "result": {
            "research_package": {
                "document_title": "HTTP/3 RFC 9114 QUIC",
                "executive_summary": "HTTP/3 is specified by RFC 9114 and uses QUIC transport.",
                "sections": [{"title": "Source", "content": "RFC 9114 defines HTTP/3 over QUIC. [1]"}],
                "source_notes": [{"citation_id": 1, "url": "https://www.geeksforgeeks.org/html/what-is-http"}],
            },
            "metadata": {"verified_research_extension": {"coverage_state": {"verified_coverage_ratio": 0}}},
        },
    }
    grade = score_result(case, record)
    assert grade["technical_pass"] is True
    assert grade["gold_anchor_recall"] == 1.0
    assert grade["quality_screen_pass"] is False
    assert "missing_primary_source" in grade["quality_flags"]
    assert "insufficient_verified_coverage" in grade["quality_flags"]


def test_quality_gate_flags_explicitly_incomplete_answer_despite_anchor_hits() -> None:
    case = next(c for c in CASES["cases"] if c["id"] == "space-apollo11")
    sample = {
        "status": "succeeded",
        "result": {
            "research_package": {
                "document_title": "Apollo 11 landed July 20, 1969",
                "executive_summary": "Neil Armstrong stepped onto the Moon on July 20, 1969. "
                                     "The available evidence does not establish Buzz Aldrin's presence; "
                                     "identifying Buzz Aldrin requires corroboration.",
                "sections": [{"title": "NASA", "content": "NASA landing evidence. [1]"}],
                "source_notes": [{"citation_id": 1, "url": "https://www.nasa.gov/history/apollo-11-mission-overview/"}],
            },
            "metadata": {"verified_research_extension": {"coverage_state": {"verified_coverage_ratio": 1}}},
        },
    }
    grade = score_result(case, sample)
    assert grade["gold_anchor_recall"] == 1.0
    assert grade["quality_screen_pass"] is False
    assert "explicit_answer_incomplete" in grade["quality_flags"]


def test_primary_source_host_matching_rejects_deceptive_suffix() -> None:
    case = next(c for c in CASES["cases"] if c["id"] == "security-aes")
    misleading = {
        "status": "succeeded",
        "result": {
            "research_package": {
                "document_title": "NIST FIPS 197 AES",
                "executive_summary": "AES key lengths include 128, 192 and 256 bits according to FIPS 197.",
                "sections": [{"title": "Security source", "content": "FIPS 197 lists key lengths. [1]"}],
                "source_notes": [{"citation_id": 1, "url": "https://evilnist.gov/fips-197"}],
            },
            "metadata": {"verified_research_extension": {"coverage_state": {"verified_coverage_ratio": 1}}},
        },
    }
    result = score_result(case, misleading)
    assert result["primary_source_present"] is False
    assert "missing_primary_source" in result["quality_flags"]


def test_out_of_scope_disclaimer_does_not_fail_complete_answer() -> None:
    case = next(c for c in CASES["cases"] if c["id"] == "geology-valdivia")
    complete = {
        "status": "succeeded",
        "result": {
            "research_package": {
                "document_title": "Largest recorded Chilean earthquake",
                "executive_summary": "In 1960, Valdivia in Chile experienced a magnitude 9.5 earthquake, the largest instrumentally recorded earthquake.",
                "sections": [{"title": "Limit of instrumental measurements",
                              "content": "This does not establish any ranking for earthquakes before instruments existed. [1]"}],
                "source_notes": [{"citation_id": 1, "url": "https://earthquake.usgs.gov/earthquakes/eventpage/official19600522191120_30/region-info"}],
            },
            "metadata": {"verified_research_extension": {"coverage_state": {"verified_coverage_ratio": 1}}},
        },
    }
    grade = score_result(case, complete)
    assert grade["quality_screen_pass"] is True
