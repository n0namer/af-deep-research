# Basefive R14 — Source Drift and Architecture Decision

Status: CANDIDATE / UNACCEPTED · 2026-10-14

## Task and Gate

- Task: `af-deep-research:v2-r14b-archsteer-graphify-c4-contracts-20261014-r1`
- Attempt: `attempt-bb33ba0f-ca7e-4d4e-aec3-b47c1fdfe69d`
- Session: `manual-20261014-basefive-architecture-r14b-af-d-3c42bb0a5220c71f`
- Target root: `D:/Users/NIKITA/Documents/DEV/universal-solver-site/af-deep-research`
- FACT: Existing SoT `docs/acceptance/c4-releasegate-reducer-frontier-20261013.md` blocks product acceptance pending original C4 receipts, interfaces and native failure/restart E2E proof. This supplement does not replace or promote that artifact.
- FACT: Baseline Git `e10580c89eac7a4f6efb50c921ae9107ce8ad8dc` is launcher evidence; branch/dirty state were not independently queried. The six architecture targets did not exist before this attempt.

## Measurable Local DoD

1. Three source-grounded C4 levels, with logical rather than invented deployment boundaries.
2. JSON fingerprints, actual Python signatures, DTO fields/types/defaults, and inventory comparison for the two authorized source files.
3. Explicit Go/package blind spots and stale/missing Graphify APIs; no completeness claim from missing inventory entries.
4. Node built-in tests accept the real slice and reject stale hashes, schema/API/DTO drift, fabricated Mermaid topology, self-acceptance and hidden coverage gaps.
5. Repair failures caused by this change, retest, self-review all six scoped outputs, then publish one typed UNACCEPTED result. Independent acceptance remains external.

## Source Fingerprints

These hashes are scoped-reader observations and are recomputed from raw file bytes by the Node suite, unlike the historical comparison receipts below.

| Source | SHA-256 |
| --- | --- |
| `reasoners/deep_research_ext/research_run.py` | `a4caa1f2d1ea2f4d70d3039fa3b2eac8371dde530ee0ebe5ec9537a602ac36ea` |
| `reasoners/deep_research_ext/verified_pipeline.py` | `97cf7e84e8f62c1190d1b5a6c4ac59be6d175e336be8dd1db3b64b9ea81dbd87` |
| `.archsteer/model.json` | `ba854b09ce33e4095e370dd0f82d80d60683ea69b193e59bb47a887287c9f539` |
| `.archsteer/architecture.md` | `66b01056637fc68119270cf62e871d297803e2fbadcaebb3b0cfed406b0a8680` |
| `graphify-out/graph.json` | `40bfff7919e18ba5b929abf1565680ce8fb055c8e2e1d36b3ccd967e5a9705ec` |
| `docs/acceptance/c4-releasegate-reducer-frontier-20261013.md` | `e776f4091b4e24a2091e97d08ea6f215fbe2b1ed548d1e13b5fed75fb09538ce` |

FACT: The reducer's recorded historical hashes (`713caa8e…5681d4c` for research_run and `1ea0b249…6a872d1f` for verified_pipeline) differ from the current source. Those prior receipts cannot establish current-source correctness. The cause/timing of those changes is not verified in this scope.

## Inventory Versus Source

| Dimension | ArchSteer | Graphify | Direct source / disposition |
| --- | --- | --- | --- |
| Representation | Schema `1.0.0`, 141 components, all marked Python, short commit `e10580c` | Nodes/edges/hyperedges with source paths and locations | Same commit label alone cannot identify dirty source bytes. Pin both inventories separately. |
| research_run API names | All 15 top-level names match current source | Missing 8 top-level names | Missing both error types, `_unique_strings`, provider/evidence receipt helpers and `resume_research_run`; exact set in JSON. |
| verified_pipeline API names | All 16 top-level names match current source | Missing 14 top-level names | Only `_semantic_snapshot` and `execute_verified_pipeline` are represented as top-level symbols besides the module node. DTOs, grounded builders, stores, replay/persistence/resume and cancellation helpers are absent. |
| Locations | Names/imports, not an API signature contract | `ResearchRun` L16; checkpoint L122; execute L82 | Raw Node line splitting finds L29, L197, L366 respectively. Contract captures indexed and actual locations; no manual offset assumption. |
| API/DTO compatibility | Exported names only; no exact signatures or DTO field/default contract | Symbol labels/locations do not describe current DTO boundaries | Direct declarations bind run schema `0.1`, report DTO `r10`, three dataclass field/type/default inventories and seven boundary signatures. |
| Go/package coverage | Zero `.go`, `go.mod` or `go.sum` component paths | Zero such node source paths | **UNVERIFIED**: no authorized Go source or package manifest was read. Inventory absence does not prove no Go in the repository or in external AgentField dependencies. |

FACT: The ArchSteer document calls itself generated and includes tests/skill code among entry points and an unassigned layer map. It is a navigation inventory, not a curated deployment specification. No generated model/document was edited.

## API and DTO Findings

- FACT: `ResearchRun` is a frozen dataclass with schema `0.1`; deserialization checks schema and stage, but it is not a full typed JSON validator. Store save separately checks nonnegative sequence. Optional legacy source revision/owner remain accepted where the code allows `None`.
- FACT: `checkpoint_research_run` checks persisted identity, stale sequence, requested revision and owner before creating the next sequence. File replacement is atomic at the path level; read/check/write is not a distributed CAS, and there is no writer lock in the inspected store.
- FACT: `resume_research_run` returns terminal state, report, provider/evidence IDs and gap summary. The orchestrator does not invoke this resume helper or short-circuit on completed status in the inspected function. This is not proof of idempotent terminal delivery under restart.
- FACT: `GroundedFact` validates nonblank IDs and lowercase SHA-256. `VerifiedSourceReport` enforces `r10`, positive integer (not boolean) revision, unique source IDs, fact references and other identity checks.
- FACT: The grounded builder requires nonempty facts and a file hash; the legacy builder defaults source revision/owner to `legacy`, file hash to empty and facts to empty. The orchestrator calls the legacy builder/persistence path, not grounded persistence. A shared `r10` DTO label does not imply equivalent source grounding.
- FACT: Report replay compares identity, permits identical same-revision replay, retains older stored revisions, rejects conflicting same-revision payloads and skipped forward revisions. Grounded persistence checks owner/cancellation and can fence an effect; resumed grounded reports check owner and file SHA.
- FACT: `DurableVerifiedSourceReportStore` uses a dict, a set and `threading.RLock`; it is **process memory only**, despite its name. Its effects/reports do not establish disk-backed restart durability. No persistence adapter was invented or wired by this documentation task.

## ADR — R14 Source Evidence Overlay

**Decision (proposed, UNACCEPTED):** Treat source fingerprints and exact declarations as the authority for this bounded contract slice. Use ArchSteer for names/import context and Graphify for provisional navigation only. Preserve three C4 levels in the authorized architecture files, with every node and edge bound to an inspected source anchor and fingerprint. Keep grounded APIs disconnected from the orchestrator where no actual call exists. Represent deployment and Go/package coverage as unverified rather than inferred.

**Alternatives rejected:** Regenerating generated inventories (outside write scope); trusting a commit label as a byte identity; representing the named durable store as a database; asserting Go absence from zero indexed files; treating static Node checks as Python/native E2E proof.

**Consequences:** Source byte changes require a deliberate contract refresh and review. Even harmless formatting changes can invalidate fingerprints. Regex declaration extraction is a deliberately bounded static method, not a Python AST/parser or runtime substitute. Mermaid is validated as a restricted `flowchart LR` grammar and exact topology, not with a renderer. Broad architecture acceptance still requires independent source/runtime evidence.

## Checks and Repair Evidence

Command: `node --test docs/architecture/basefive-r14-contract.test.mjs`, executed through `go_wave.run_project_tests`, engine `node:test`.

- Baseline inventory probe: PASS, exit 0, 1/1; established model/graph shapes, names and Go inventory counts.
- Initial contract run: FAIL, exit 1, 14/24 pass. Root cause was this attempt's hand-counted actual locations, not a production code failure. Positive validation failed on `29 !== 30`, preventing downstream negative tests from reaching their intended rejection points.
- Diagnostic run: FAIL, exit 1, 14/24; emitted exact source locations L29/L197/L366. No denied-tool retry occurred.
- Repair: corrected only JSON actual locations; unchanged source fingerprints and strict test expectations.
- Post-repair run: PASS, exit 0, 24/24. Signature, DTO, source-hash, topology and negative-boundary checks all reached their intended assertions.
- Final expanded suite additionally checks rehashed DTO/default changes, lost ArchSteer exports, lost Graphify symbols, document limitations and six-file hygiene/fingerprints. Its fresh receipt is emitted by the authorized runner; no result is inferred from this prose.

## Self-Review and Remaining Gates

- FACT: Six authorized architecture files only; no production behavior, dependencies, native tasks, claims, leases, generated inventory, acceptance SoT or Git remote state changed.
- FACT: Static anchors are source-backed inspection evidence. Guard presence is not a proof that Python rejects malformed DTOs at runtime. Negative fixture assertions exercise this Node contract validator, not a rewritten Python implementation.
- FACT: All output files must be below the repository's 500-line limit; a final hygiene test checks this and credential assignment patterns. Tests do not invoke shells, Python, network, providers or write fixtures.
- BLOCKED method steps: BMad config resolver, arbitrary configuration discovery, separate spec/sprint/deferred writes, Git diff/status commands and independent review agents are unavailable or outside the task authority. The trusted task supplies the specification and current gate. No competing PLAN/spec or reviewer artifact was created; no complete BMad workflow claim is made.
- UNVERIFIED: Mermaid renderer, live Python integration/restart behavior, whole-repository/Go/package completeness, native task-to-result negative E2E, branch/dirty state and independent QA acceptance.
- Next gate: Independent reviewer validates these six artifacts and consumes the original C4/runtime receipts through the existing acceptance frontier. Any repair must reuse this original task/thread; no duplicate implementation or self-acceptance.

## Work Sizing

Initial useful-work estimate: investigation 5 + artifacts/validator 8 + focused negatives 4 + repair 2 + review/evidence 3 = 22 minutes; external coordination not requested. Actual test-engine receipts include durations, but total wall-clock work was not independently measured. Finish when the bounded evidence is complete, not when an invented duration expires.
