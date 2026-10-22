# Search provider matrix — release-neutral observation

Status: candidate evidence; independent acceptance remains UNACCEPTED.

The companion test uses the repository's concrete Brave, Tavily, Firecrawl,
and Perplexity adapters with isolated fake HTTP sessions by default. It checks
the two fixed research domains: RFC 9110 via \`rfc-editor.org\`, and Python
3.13 via \`python.org\`. Results must be unique, HTTPS, and include the
requested primary bucket.

Negative cases reject empty, fabricated, non-HTTPS, credential-bearing, and
missing-domain observations. Jina and Serper are explicitly outside this
matrix; Exa has no registered repository adapter. These are honest unsupported
cases, not claims about those external services.

Live requests run only when \`REAL_NETWORK_TESTS=1\` (also \`true\`/\`yes\`)
and the corresponding key is already in the process environment. The test
does not load \`.env\`, print keys, or print raw provider error bodies.
Missing keys are skipped with an explicit reason. Any live result is only
adapter evidence for the fixed queries, not a completed research report.
