from reasoners.deep_research_ext.evaluation import (
    EvalObservation,
    evaluate_hard_gates,
    fixture_index,
    mutate_corpus_remove_documents,
    pilot_frozen_corpora,
    replay_frozen_fixture,
)
from skills.search.base import SearchResponse, SearchResult
from skills.search.fusion import canonicalize_url, fuse_search_responses


def _result(title, url, content):
    return SearchResult(title=title, url=url, content=content)


def _independent_admissible_sources(documents):
    return {
        (doc.source_class, doc.provenance_group)
        for doc in documents
        if doc.admissible
    }


def test_fusion_canonical_dedup_and_rrf_are_deterministic_across_provider_order():
    first = SearchResponse(
        provider="alpha",
        query_used="q",
        results=[
            _result("Article", "HTTPS://Example.org/story/?utm_source=x", "short"),
            _result("Other", "https://other.example/a", "other"),
        ],
    )
    second = SearchResponse(
        provider="beta",
        query_used="q",
        results=[
            _result("Article mirror URL", "https://example.org/story", "longer"),
            _result("Other", "https://other.example/a?fbclid=discard", "other"),
        ],
    )
    left = fuse_search_responses([first, second], max_results=10)
    right = fuse_search_responses([second, first], max_results=10)
    assert canonicalize_url(first.results[0].url) == canonicalize_url(second.results[0].url)
    assert [(r.canonical_url, r.rrf_score) for r in left.results] == [
        (r.canonical_url, r.rrf_score) for r in right.results
    ]
    article = next(r for r in left.results if r.canonical_url == "https://example.org/story")
    assert article.retrieval_providers == ["alpha", "beta"]
    assert article.provider_ranks == {"alpha": 1, "beta": 1}


def test_semantic_snapshot_does_not_count_mirrors_or_proxy_publications_as_independent():
    corpus = pilot_frozen_corpora()["DR-P06"]
    assert _independent_admissible_sources(corpus.documents) == {
        ("primary_official", "product-primary")
    }
    assert sum(doc.admissible for doc in corpus.documents) == 1
    assert sum(doc.provenance_group == "same-upstream" for doc in corpus.documents) == 5
    fixture = fixture_index()["DR-P06"]
    mutated = mutate_corpus_remove_documents(corpus, ["PROD-primary"])
    replay = replay_frozen_fixture(fixture, mutated)
    assert replay.gate.passed is False
    assert replay.used_document_ids == ()
    assert _independent_admissible_sources(mutated.documents) == set()


def test_primary_bucket_is_required_and_fabricated_source_negatives_fail_closed():
    fixture = fixture_index()["DR-P06"]
    corpus = pilot_frozen_corpora()["DR-P06"]
    baseline = replay_frozen_fixture(fixture, corpus)
    assert baseline.gate.passed is True
    assert baseline.observation.requirement_states == {"R1": "supported", "R2": "supported"}
    fabricated = EvalObservation(
        requirement_states={"R1": "supported", "R2": "supported"},
        fabricated_artifacts=1,
    )
    result = evaluate_hard_gates(fixture, fabricated)
    assert result.passed is False
    assert "fabricated_artifacts=1" in result.failures
    no_primary = replay_frozen_fixture(
        fixture, mutate_corpus_remove_documents(corpus, ["PROD-primary"])
    )
    assert no_primary.gate.passed is False


def test_two_provider_hits_to_one_upstream_article_are_one_semantic_source():
    responses = [
        SearchResponse(
            provider="provider-a",
            results=[_result("Original", "https://publisher.example/report", "facts")],
        ),
        SearchResponse(
            provider="provider-b",
            results=[_result("Syndicated copy", "https://wire.example/report-copy", "same facts")],
        ),
    ]
    fused = fuse_search_responses(responses)
    assert len(fused.results) == 2
    assert len({r.canonical_url for r in fused.results}) == 2
    corpus = pilot_frozen_corpora()["DR-P06"]
    assert len(_independent_admissible_sources(corpus.documents)) == 1
    assert all(
        doc.provenance_group == "same-upstream"
        for doc in corpus.documents
        if doc.document_id.startswith("PROD-copy-")
    )


def test_fabricated_or_non_primary_sources_cannot_make_a_missing_primary_fact_green():
    fixture = fixture_index()["DR-P06"]
    corpus = pilot_frozen_corpora()["DR-P06"]
    fabricated_only = tuple(
        doc for doc in corpus.documents if doc.document_id != "PROD-primary"
    )
    replay = replay_frozen_fixture(
        fixture,
        type(corpus)(
            fixture_id=corpus.fixture_id,
            version="1.0+fabricated-only",
            documents=fabricated_only,
        ),
    )
    assert replay.gate.passed is False
    assert replay.observation.requirement_states == {"R1": "unresolved", "R2": "unresolved"}
