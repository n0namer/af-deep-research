from urllib.parse import urlparse


def normalize_host(url: str) -> str:
    host = (urlparse(str(url or "")).hostname or "").lower().strip(".")
    return host[4:] if host.startswith("www.") else host


def provenance_group(url: str) -> str:
    """Conservative publisher lineage key; exact-host based, no fake independence claims."""
    return normalize_host(url) or "unknown"


def classify_source(url: str) -> str:
    host = normalize_host(url)
    if host in {"rfc-editor.org", "datatracker.ietf.org", "ietf.org"} or host.endswith(".ietf.org"):
        return "primary_standard"
    if host.endswith(".gov") or host.endswith(".gov.uk") or host.endswith(".europa.eu"):
        return "government_or_regulator"
    if host == "github.com" or host.endswith(".github.com"):
        return "source_repository"
    if host == "arxiv.org" or host.endswith(".arxiv.org"):
        return "preprint_repository"
    if any(host.endswith(suffix) for suffix in ("acm.org", "ieee.org", "nature.com", "science.org", "springer.com")):
        return "academic_publisher"
    if not host:
        return "unknown"
    return "web_source"
