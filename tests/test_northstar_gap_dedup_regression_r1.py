import asyncio
from types import SimpleNamespace

import pytest

from reasoners.deep_research_ext import gap_research
from reasoners.deep_research_ext.gap_research import GapQuery, GapQueryPlan


def _contract(*requirement_ids: str):
    return SimpleNamespace(
        query="Compare the primary-source record.",
        source_strictness="primary_only",
        requirements=[
            SimpleNamespace(
                requirement_id=requirement_id,
                question=f"What is the official record for {requirement_id}?",
                required_source_class="primary",
            )
            for requirement_id in requirement_ids
        ],
    )


def _coverage(*requirement_ids: str):
    return SimpleNamespace(
        requirements=[
            SimpleNamespace(requirement_id=requirement_id, status="missing")
            for requirement_id in requirement_ids
        ]
    )


def _ledger(*claims):
    return SimpleNamespace(claims=list(claims))


def _output(*articles):
    return SimpleNamespace(source_articles=list(articles), article_evidence=[])


def _article(article_id: int, url: str):
    return {"id": article_id, "url": url, "content": "Official primary-source record"}


def _install_ledger_pipeline(monkeypatch):
    claim = SimpleNamespace(status="verified", support_state="source_entailed")

    def build_evidence_ledger(package, _):
        return _ledger(claim) if package.get("source_articles") else _ledger()

    async def identity_mapping(*, ledger, **_kwargs):
        return ledger

    async def identity_verification(*, ledger, **_kwargs):
        return ledger

    def merge_ledgers(existing, extra):
        return _ledger(*existing.claims, *extra.claims)

    monkeypatch.setattr(gap_research, "build_evidence_ledger", build_evidence_ledger)
    monkeypatch.setattr(gap_research, "map_claims_to_requirements", identity_mapping)
    monkeypatch.setattr(gap_research, "verify_ledger_claims", identity_verification)
    monkeypatch.setattr(gap_research, "merge_evidence_ledgers", merge_ledgers)


def _run_round(*, contract, coverage, planner, executor, package=None, ledger=None, source_budget=3):
    return asyncio.run(
        gap_research.run_gap_research_round(
            contract=contract,
            coverage=coverage,
            ledger=ledger or _ledger(),
            research_package=package or {"source_articles": [], "article_evidence": []},
            stream_executor=executor,
            ai_call=planner,
            source_strictness="primary_only",
            source_budget=source_budget,
        )
    )


def test_equivalent_gap_is_scheduled_once_but_distinct_gap_is_preserved(monkeypatch):
    _install_ledger_pipeline(monkeypatch)

    async def planner(**_kwargs):
        return GapQueryPlan(
            gaps=[
                GapQuery(requirement_id="R1", queries=[" Official   R1 ", "official r1"]),
                GapQuery(requirement_id="R1", queries=["official R1"]),
                GapQuery(requirement_id="R1", queries=["R1 archive"]),
            ]
        )

    scheduled_queries = []

    async def executor(_name, queries, *_args, **_kwargs):
        scheduled_queries.append(queries)
        return _output()

    _, _, trace = _run_round(
        contract=_contract("R1"),
        coverage=_coverage("R1"),
        planner=planner,
        executor=executor,
        source_budget=2,
    )

    assert scheduled_queries == [["Official R1"], ["R1 archive"]]
    assert trace.attempted_requirements == ["R1", "R1"]


def test_equivalent_query_for_wrong_owner_does_not_suppress_owned_gap(monkeypatch):
    _install_ledger_pipeline(monkeypatch)

    async def planner(**_kwargs):
        return GapQueryPlan(
            gaps=[
                GapQuery(requirement_id="FOREIGN", queries=["official R1"]),
                GapQuery(requirement_id="R1", queries=[" official   r1 "]),
            ]
        )

    calls = []

    async def executor(name, queries, *_args, **_kwargs):
        calls.append((name, queries))
        return _output()

    _, _, trace = _run_round(
        contract=_contract("R1"),
        coverage=_coverage("R1"),
        planner=planner,
        executor=executor,
    )

    assert calls == [("VerifiedGap_R1", ["official r1"])]
    assert trace.attempted_requirements == ["R1"]


def test_crash_replay_schedules_equivalent_gap_once_per_atomic_attempt(monkeypatch):
    _install_ledger_pipeline(monkeypatch)

    async def planner(**_kwargs):
        return GapQueryPlan(
            gaps=[
                GapQuery(requirement_id="R1", queries=["official R1"]),
                GapQuery(requirement_id="R1", queries=[" official   r1 "]),
            ]
        )

    attempts = 0

    async def executor(*_args, **_kwargs):
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise RuntimeError("deterministic retrieval crash")
        return _output(_article(1, "https://official.example/r1"))

    checkpoint_package = {"source_articles": [], "article_evidence": []}
    checkpoint_ledger = _ledger()

    with pytest.raises(RuntimeError, match="deterministic retrieval crash"):
        _run_round(
            contract=_contract("R1"),
            coverage=_coverage("R1"),
            planner=planner,
            executor=executor,
            package=checkpoint_package,
            ledger=checkpoint_ledger,
            source_budget=1,
        )

    assert attempts == 1
    assert checkpoint_package == {"source_articles": [], "article_evidence": []}
    assert checkpoint_ledger.claims == []

    recovered_package, _, recovered_trace = _run_round(
        contract=_contract("R1"),
        coverage=_coverage("R1"),
        planner=planner,
        executor=executor,
        package=checkpoint_package,
        ledger=checkpoint_ledger,
        source_budget=1,
    )

    assert attempts == 2
    assert [article["url"] for article in recovered_package["source_articles"]] == [
        "https://official.example/r1"
    ]
    assert recovered_trace.new_source_count == 1
