"""Regression contract for trustworthy primary-source identity, without real APIs."""
import pytest
from doc_generation_pipeline import _classify_source, _source_allowed_by_policy


@pytest.mark.parametrize("url", [
    "https://www.who.int/news/item/vaccine",
    "https://who.int/publications/report",
    "https://eur-lex.europa.eu/eli/reg/2016/679/oj",
    "https://www.eur-lex.europa.eu/legal-content/EN/TXT/",
    "https://www.ipcc.ch/report/ar6/syr/",
    "https://peps.python.org/pep-0703/",
    "https://www.iau.org/public/themes/pluto/",
    "https://rfc-editor.org/info/rfc9114/",
])
def test_recognizes_exact_institutional_primary_sources(url):
    source_type, confidence = _classify_source(url)
    assert source_type == "primary_doc"
    assert confidence >= 0.95
    assert _source_allowed_by_policy(source_type, "verified-only")


@pytest.mark.parametrize("url", [
    "https://evilwho.int/something",
    "https://who.int.attacker.example/something",
    "https://eur-lex.europa.eu.evil.example/eli/reg/",
    "https://ipcc.ch.example.com/report/",
    "https://fakepeps.python.org.evil.example/pep-0703/",
    "https://iau.org.attacker.example/source/",
    "https://reuters-blogs.example.net/opinion",
    "https://fakenews.gov.evil.example/news",
    "https://who.int@evil.example.com/news",
    "https://evil.example.com/path/https://who.int/",
])
def test_deceptive_source_domains_are_not_promoted(url):
    source_type, _ = _classify_source(url)
    assert source_type not in {"primary_doc", "gov", "reputable_media", "peer_reviewed"}


@pytest.mark.parametrize("url", [
    "https://www.nasa.gov/mission/",
    "https://www.nist.gov/publications/",
    "https://earthquake.usgs.gov/earthquakes/",
    "https://www.rfc-editor.org/rfc/rfc9000/",
    "https://www.ietf.org/archive/id/draft/",
    "https://doi.org/10.1038/example",
])
def test_existing_official_sources_remain_admissible(url):
    source_type, _ = _classify_source(url)
    assert _source_allowed_by_policy(source_type, "verified-only")


@pytest.mark.parametrize("url", ["", "not_a_url", "javascript:alert(1)", "file:///C:/secret", "https://"])
def test_unusable_or_missing_urls_are_never_trusted(url):
    source_type, _ = _classify_source(url)
    assert source_type == "blog"
    assert not _source_allowed_by_policy(source_type, "verified-only")
