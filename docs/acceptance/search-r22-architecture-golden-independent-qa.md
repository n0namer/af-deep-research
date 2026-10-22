# Search R22 architecture golden independent QA

Status: CANDIDATE / UNACCEPTED

## Scope and source of truth

This is a fresh oracle for the existing \`search-r16\` architecture contract. It reads live primary sources, recomputes hashes, and checks documented signatures and topology. It does not replace or promote the BMad acceptance artifact.

The baseline/as-of is \`e10580c89eac7a4f6efb50c921ae9107ce8ad8dc\`; a different baseline or an \`ACCEPTED*\` status is rejected.

## Checks

- Four positive assertions cover source identity, six live signatures, Mermaid topology, and contract status/as-of.
- Four negative assertions reject a forged source hash, forged topology node, stale as-of/promoted status, and signature drift.
- The topology check requires recognizable Mermaid nodes and rejects undocumented contract node vocabulary; it does not infer Graphify/ArchSteer claims.

## Validation receipt

\`python -m pytest -q tests/test_search_r22_architecture_golden_qa.py\`

\`node --test docs/architecture/search-r16-contract.test.mjs\`

A denied, missing, or dependency-blocked runner is infrastructure-blocked, not PASS.

## Limitations

This is independent source-policy/oracle evidence, not product acceptance. It does not prove runtime provider behavior, Graphify/ArchSteer integration, or CrewSync terminal state.
