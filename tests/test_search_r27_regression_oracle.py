"""R27 independent regression oracle for current search and durable-report contracts.

This file intentionally imports the public package interfaces used by production code
and exercises deterministic in-memory implementations without provider/network mocks.
"""
import asyncio
import hashlib

import pytest

from skills.search.base import SearchResponse, SearchResult
from skills.search import search_with_provider
from skills.search.fusion import fuse_search_responses
from reasoners.deep_research_ext.verified_pipeline import (
    DurableVerifiedSourceReportStore,
    GroundedFact,
    VerifiedSourceReportError,
    build_grounded_verified_report,
    persist_grounded_verified_report,
    resume_grounded_verified_report,
)


FUSION_SHA = "c7c0684e8d5d55df099ebf7690bfceafff78e79fe4ad15a6265ecb29a5a5625c"


def _response(provider, *items):
    return SearchResponse(
        provider=provider,
        query_used="r27 regression",
        results=[
            SearchResult(title=title, url=url, content=content)
            for title, url, content in items
        ],
        total_results=len(items),
    )


def _report(owner="owner-r27", source_sha=None):
    source_sha = source_sha or hashlib.sha256(b"r27-source").hexdigest()
    return build_grounded_verified_report(
        report_id="report-r27",
        query="durable cancellation",
        source_revision="r27-source",
        source_owner=owner,
        source_file_sha256=source_sha,
        facts=(GroundedFact("fact-1", "source-1", source_sha),),
        payload={"answer": "source-grounded"},
    )


def test_fusion_positive_dedupes_tracking_variants_and_keeps_real_provider_ranks():
    result = fuse_search_responses(
        [
            _response(
                "brave",
                ("Canonical", "HTTPS://Example.com/report/?utm_source=r27", "short"),
            ),
            _response(
                "tavily",
                ("Canonical copy", "https://example.com/report", "longer"),
            ),
        ]
    )

    assert len(result.results) == 1
    item = result.results[0]
    assert item.canonical_url == "https://example.com/report"
    assert item.retrieval_providers == ["brave", "tavily"]
    assert item.provider_ranks == {"brave": 1, "tavily": 1}
    assert item.content == "longer"


def test_fusion_excludes_empty_urls_instead_of_creating_fake_evidence():
    result = fuse_search_responses(
        [_response("brave", ("missing", "", "not a retrievable URL"))]
    )

    assert result.results == []


def test_unknown_single_provider_is_refused_by_public_search_interface():
    with pytest.raises(ValueError, match="Unknown provider"):
        asyncio.run(search_with_provider("r27 query", "not-configured"))


def test_cancelled_persistence_raises_cancelled_error_and_does_not_write():
    store = DurableVerifiedSourceReportStore()

    with pytest.raises(asyncio.CancelledError):
        persist_grounded_verified_report(
            store, _report(), owner="owner-r27", cancellation=lambda: True
        )

    assert store.load("report-r27") is None
    assert store.effect_count() == 0


def test_cancelled_effect_fencing_does_not_apply_terminal_effect():
    store = DurableVerifiedSourceReportStore()
    candidate = _report()
    with pytest.raises(asyncio.CancelledError):
        persist_grounded_verified_report(
            store,
            candidate,
            owner="owner-r27",
            cancellation=lambda: store.load("report-r27") is not None,
            effect_id="terminal-r27",
        )

    assert store.load("report-r27") is not None
    assert store.effect_count() == 0


def test_resume_rejects_current_report_with_different_source_identity():
    store = DurableVerifiedSourceReportStore()
    candidate = _report()
    persist_grounded_verified_report(store, candidate, owner="owner-r27")

    other_sha = hashlib.sha256(b"drifted-source").hexdigest()
    with pytest.raises(VerifiedSourceReportError, match="source file SHA"):
        resume_grounded_verified_report(
            store,
            "report-r27",
            owner="owner-r27",
            source_file_sha256=other_sha,
        )


def test_fusion_source_sha_is_current_and_not_the_r26_fixture():
    with open("skills/search/fusion.py", encoding="utf-8") as source:
        assert hashlib.sha256(source.read().encode()).hexdigest() == FUSION_SHA
