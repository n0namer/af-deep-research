"""Independent r27 epistemic release gate.

This file is intentionally product-read-only: it verifies source/evidence rules
and does not call providers, send tokens, or mutate CrewSync/native task state.
"""
from __future__ import annotations

import hashlib
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import pytest

from skills.search.fusion import canonicalize_url


@dataclass(frozen=True)
class Citation:
    url: str
    source_class: str
    provenance_group: str
    content_sha256: str


def citation_identity(citation: Citation) -> tuple[str, str, str]:
    """Return stable identity fields required for primary-source evidence."""
    return (
        canonicalize_url(citation.url),
        citation.source_class,
        citation.content_sha256,
    )


def independent_primary_citations(citations: Iterable[Citation]) -> tuple[Citation, ...]:
    """Keep admissible primary citations independent by provenance group."""
    seen_groups: set[str] = set()
    result: list[Citation] = []
    for citation in citations:
        if citation.source_class != "primary":
            continue
        if citation.provenance_group in seen_groups:
            continue
        seen_groups.add(citation.provenance_group)
        result.append(citation)
    return tuple(result)


def provider_failover(statuses: Iterable[int]) -> str:
    """A 503 provider is skipped; a later healthy provider remains usable."""
    for status in statuses:
        if status == 200:
            return "PRIMARY_AVAILABLE"
        if status == 503:
            continue
        return "PROVIDER_ERROR"
    return "NO_PROVIDER"


def release_decision(*, golden_answer: str | None, citations: Iterable[Citation],
                     provider_statuses: Iterable[int]) -> str:
    primary = independent_primary_citations(citations)
    if not golden_answer:
        return "BLOCKED_MISSING_GOLDEN"
    if provider_failover(provider_statuses) != "PRIMARY_AVAILABLE":
        return "BLOCKED_PROVIDER"
    if not primary:
        return "BLOCKED_PRIMARY_CITATION"
    return "READY_CANDIDATE_UNACCEPTED"


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _primary(url: str, group: str, content: str) -> Citation:
    return Citation(url, "primary", group, _sha(content))


def test_primary_citation_identity_and_current_git_fingerprint():
    citation = _primary(
        "HTTPS://Example.test/record/?utm_source=feed",
        "official-record-1",
        "The primary record states the tested proposition.",
    )
    assert citation_identity(citation) == (
        "https://example.test/record",
        "primary",
        citation.content_sha256,
    )
    head = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], text=True
    ).strip()
    assert re.fullmatch(r"[0-9a-f]{40}", head)


def test_derivative_sources_do_not_count_as_independent():
    citations = (
        _primary("https://official.test/a", "upstream-a", "authoritative"),
        Citation(
            "https://mirror.test/a", "derivative", "upstream-a",
            _sha("copied authoritative"),
        ),
        _primary("https://official.test/b", "upstream-b", "independent"),
    )
    selected = independent_primary_citations(citations)
    assert [item.provenance_group for item in selected] == [
        "upstream-a", "upstream-b"
    ]
    assert release_decision(
        golden_answer="expected answer",
        citations=citations,
        provider_statuses=(200,),
    ) == "READY_CANDIDATE_UNACCEPTED"


def test_provider_503_failover_is_not_acceptance():
    citation = _primary("https://official.test/a", "upstream-a", "authoritative")
    assert provider_failover((503, 200)) == "PRIMARY_AVAILABLE"
    assert release_decision(
        golden_answer="expected answer",
        citations=(citation,),
        provider_statuses=(503, 200),
    ) == "READY_CANDIDATE_UNACCEPTED"


def test_missing_golden_answer_blocks_even_with_sources_and_provider():
    citation = _primary("https://official.test/a", "upstream-a", "authoritative")
    assert release_decision(
        golden_answer=None,
        citations=(citation,),
        provider_statuses=(200,),
    ) == "BLOCKED_MISSING_GOLDEN"

def test_provider_503_without_fallback_blocks():
    citation = _primary("https://official.test/a", "upstream-a", "authoritative")
    assert release_decision(
        golden_answer="expected answer",
        citations=(citation,),
        provider_statuses=(503,),
    ) == "BLOCKED_PROVIDER"
