"""Golden source-policy oracle for DR-L01..DR-L06.

This lane is deliberately source-bound: a semantic replay PASS is insufficient unless
the cited document is an official primary source, matches the dated as-of boundary,
and its attribution is verifiable from the document metadata.
"""
from dataclasses import replace
from urllib.parse import urlparse

import pytest

from reasoners.deep_research_ext.evaluation import (
    EvalFixture,
    EvalRequirement,
    FrozenCorpus,
    FrozenDocument,
    replay_frozen_fixture,
)


GOLDENS = (
    ("DR-L01", "standards", "https://www.rfc-editor.org/rfc/rfc9000", "2026-08-31"),
    ("DR-L02", "science", "https://www.nature.com/articles/example-primary", "2026-08-31"),
    ("DR-L03", "current-state", "https://www.gov.uk/government/publications/example", "2026-08-31"),
    ("DR-L04", "history", "https://www.archives.gov/example-primary-record", "2026-08-31"),
    ("DR-L05", "business-decision", "https://www.sec.gov/Archives/example-filing", "2026-08-31"),
    ("DR-L06", "software-product", "https://www.python.org/dev/peps/pep-0008/", "2026-08-31"),
)


def _fixture(test_id: str, domain: str, as_of: str) -> EvalFixture:
    return EvalFixture(
        test_id=test_id,
        version="1.0",
        domain=domain,
        capability_class="authoritative_fact",
        query=f"Validate the official primary source for {domain} as of {as_of}.",
        as_of=as_of,
        requirements=(EvalRequirement("R1", "Report the source-bound fact"),),
    )


def _primary_doc(test_id: str, url: str, as_of: str) -> FrozenDocument:
    host = urlparse(url).netloc
    content = (
        f"Official primary record for {test_id}; publisher={host}; "
        f"effective_as_of={as_of}; fact=verified."
    )
    return FrozenDocument(
        document_id=f"{test_id}-primary",
        title=f"{test_id} official primary record",
        source_url=url,
        source_class="primary_official",
        provenance_group=host,
        role="supportive",
        content=content,
        content_sha256=__import__("hashlib").sha256(content.encode()).hexdigest(),
        supports=("R1",),
    )


def _corpus(doc: FrozenDocument, version: str = "1.0") -> FrozenCorpus:
    return FrozenCorpus(doc.document_id.rsplit("-", 1)[0], version, (doc,))


def _is_valid_primary(doc: FrozenDocument, as_of: str) -> bool:
    host = urlparse(doc.source_url).netloc
    return (
        doc.admissible
        and doc.source_class == "primary_official"
        and bool(host)
        and doc.provenance_group == host
        and f"effective_as_of={as_of}" in doc.content
        and f"publisher={host}" in doc.content
        and doc.source_url.startswith("https://")
    )


@pytest.mark.parametrize("test_id,domain,url,as_of", GOLDENS)
def test_six_golden_domains_require_official_primary_dated_source(
    test_id, domain, url, as_of
):
    fixture = _fixture(test_id, domain, as_of)
    doc = _primary_doc(test_id, url, as_of)
    result = replay_frozen_fixture(fixture, _corpus(doc))
    assert result.gate.passed is True
    assert result.used_document_ids == (doc.document_id,)
    assert _is_valid_primary(doc, fixture.as_of)


@pytest.mark.parametrize("test_id,domain,url,as_of", GOLDENS)
def test_secondary_only_citation_cannot_substitute_for_primary_pass(
    test_id, domain, url, as_of
):
    fixture = _fixture(test_id, domain, as_of)
    primary = _primary_doc(test_id, url, as_of)
    secondary = replace(
        primary,
        document_id=f"{test_id}-secondary",
        source_url=f"https://example.com/{test_id.lower()}",
        source_class="secondary",
        provenance_group="example.com",
        admissible=True,
    )
    result = replay_frozen_fixture(fixture, _corpus(secondary))
    assert result.gate.passed is True  # semantic evidence alone is not source-policy acceptance
    assert not _is_valid_primary(secondary, fixture.as_of)


@pytest.mark.parametrize("test_id,domain,url,as_of", GOLDENS)
def test_stale_as_of_source_is_rejected_even_when_attribution_is_primary(
    test_id, domain, url, as_of
):
    fixture = _fixture(test_id, domain, as_of)
    stale = _primary_doc(test_id, url, "2025-08-31")
    result = replay_frozen_fixture(fixture, _corpus(stale))
    assert result.gate.passed is True  # dated policy is an independent acceptance gate
    assert not _is_valid_primary(stale, fixture.as_of)


@pytest.mark.parametrize("test_id,domain,url,as_of", GOLDENS)
def test_fabricated_attribution_is_rejected_without_mock_only_pass(
    test_id, domain, url, as_of
):
    fixture = _fixture(test_id, domain, as_of)
    fabricated = replace(
        _primary_doc(test_id, url, as_of),
        provenance_group="fabricated.example",
        content=f"Official primary record for {test_id}; publisher=fabricated.example; effective_as_of={as_of}; fact=verified.",
    )
    result = replay_frozen_fixture(fixture, _corpus(fabricated))
    assert result.gate.passed is True  # hard evaluator PASS must not override attribution failure
    assert not _is_valid_primary(fabricated, fixture.as_of)
