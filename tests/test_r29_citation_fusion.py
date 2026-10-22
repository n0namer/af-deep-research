"""Focused acceptance tests for canonical citation URL fusion."""

from skills.search.base import SearchResponse, SearchResult
from skills.search.fusion import canonicalize_url, fuse_search_responses


def result(url: str, title: str = "Source") -> SearchResult:
    return SearchResult(title=title, url=url, content="independent evidence")


def test_fusion_merges_equivalent_source_urls_and_preserves_evidence():
    response = fuse_search_responses(
        [
            SearchResponse(
                results=[result("HTTPS://Example.com:443/a/../article/?utm_source=x#section")],
                query_used="q",
                provider="alpha",
            ),
            SearchResponse(
                results=[result("https://example.com/article", "Longer source")],
                query_used="q",
                provider="beta",
            ),
        ]
    )

    assert len(response.results) == 1
    assert response.results[0].canonical_url == "https://example.com/article"
    assert response.results[0].retrieval_providers == ["alpha", "beta"]
    assert response.results[0].provider_ranks == {"alpha": 1, "beta": 1}
    assert response.results[0].title == "Longer source"


def test_blank_url_is_not_a_citation_identity():
    assert canonicalize_url("") == ""
    assert canonicalize_url("   ") == ""


def test_tracking_parameters_and_fragments_do_not_create_new_identity():
    assert canonicalize_url(
        "https://example.com/article?utm_medium=x&fbclid=abc#evidence"
    ) == "https://example.com/article"


def test_default_ports_and_dot_segments_do_not_create_new_identity():
    assert canonicalize_url("HTTPS://EXAMPLE.COM:443/a/./b/../article/") == (
        "https://example.com/article"
    )


def test_meaningful_query_parameters_remain_distinct():
    assert canonicalize_url("https://example.com/article?version=1") != (
        canonicalize_url("https://example.com/article?version=2")
    )
