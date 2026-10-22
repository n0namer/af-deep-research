# Basefive R14 — Independent Source-Bound C4 QA

Status: CANDIDATE / UNACCEPTED · revalidated 2026-10-15

## Current Attempt — Existing Candidate Revalidation

- Task: `af-deep-research:v2-r14b-independent-c4-qa-20261014-r1`
- Attempt: `attempt-d8a57046-ab30-4f8d-ac1d-db7591652bbb`
- Session: `manual-20261015-basefive-goal20-af-deep-researc-b76bc220d70257aa`
- FACT: Both authorized QA files already existed at discovery. The original implementation and historical repair receipts below are preserved, not attributed to this attempt. No replacement validator or product implementation was needed.
- FACT: Fresh baseline executed `node --test docs/architecture/basefive-r14-independent-c4.test.mjs` through `go_wave.run_project_tests`: `status=PASS`, `engine=node:test`, `exit_code=0`, 12 tests passed, 0 failed/cancelled/skipped/todo, empty stderr, TAP duration 319.1389 ms. The emitted receipt is timestamped `2026-10-15T08:43:24.505Z`.
- FACT: All six source and six producer artifact SHA pins matched current raw bytes. The reused QA test SHA is `a910fcb0f34bc58648d6ef77374c02cf410ddf8e9a6704c1afc1c87aead3d4cd`; the report before this evidence update was `f22e3b93d305935784843dd63649d66ef5be148feb6e9664a462d64ea390763a`. The post-update runner receipt binds the final report bytes separately.
- FACT: Fresh coverage is 141 ArchSteer components, language inventory `[python]`, zero indexed Go paths in either inventory, and eight/fourteen missing Graphify top-level symbols in the two Python targets. These counts do not establish whole-repository coverage.
- FACT: Existing negatives reject rehashed DTO drift, coordinated topology drift with a real unrelated anchor, concealed Go inventory, removed owner parameter, concealed Graphify symbol loss, and stale orchestration topology. No new test cases or weakened expectations were necessary.
- FACT: Current bounded source reads confirm schema `0.1`, DTO `r10` and legacy defaults, injected research callbacks, checkpoint calls, separate grounded APIs, and process-local dict/set/RLock storage. Full authorized JSON inventories and source bytes are parsed by the native Node suite; no graph-MCP coverage or Python-runtime claim is inferred.
- FACT: Go source inspection: BLOCKED_SCOPE. The trusted request mentions Go/Python but authorizes only two Python source paths and inventories. No Go source or manifest may be read in this attempt. Therefore the broader Go-source acceptance requirement remains unproved even though inventory checks pass.
- FACT: No prior publication transport/readback is available in the authorized evidence. Existing files are reused as an existing candidate, not asserted to be a prior VERIFIED or independently accepted result. No duplicate task, claim, agent or implementation was created.
- FACT: BMad config execution, Git status/history/diff and graph/Graft tools are unavailable or unauthorized in this lane. The explicit target root, trusted Git binding and existing acceptance frontier govern; no competing tracker or complete-workflow claim is introduced.
- Disposition: static-slice CANDIDATE / UNACCEPTED only. Python runtime, native task-to-result failure/restart E2E, source-level Go coverage and original C4 receipt fan-in remain external gates. This is not full product acceptance.
- Useful-work estimate revised after discovery: investigation 3 + evidence update 2 + native checks 1 + self-review/publication 2 = 8 minutes, no external coordination overhead requested. No exact elapsed total is claimed; reuse removes the need for a second 22-minute implementation. Next milestone is the post-update native receipt and one typed publication for this exact attempt.

## Original Implementation Authority and Gate

- Task: `af-deep-research:v2-r14b-independent-c4-qa-20261014-r1`
- Attempt: `attempt-abff4c34-9ee3-4203-a585-433ff96196b4`
- Session: `manual-20261014-basefive-architecture-review-r1-75dd98fcf5f6f279`
- Target: `D:/Users/NIKITA/Documents/DEV/universal-solver-site/af-deep-research`
- FACT: The launcher identifies Git `e10580c89eac7a4f6efb50c921ae9107ce8ad8dc`; scoped interfaces do not independently establish branch or dirty state.
- FACT: Existing acceptance SoT is `docs/acceptance/c4-releasegate-reducer-frontier-20261013.md`. Its missing native task-to-result, original receipt and runtime gates remain unchanged.
- FACT: Only this report and `docs/architecture/basefive-r14-independent-c4.test.mjs` are writable. Producer artifacts, Python source, generated inventories and live task state remain read-only.
- FACT: BMad phase is independent architecture QA after a producer candidate, not product implementation or release. Canonical BMAD-MNNZ supplies workflow instructions, not the target repository.

## Bounded Definition of Done

Deliver a separately implemented static validator for the exact producer contract: recompute raw source SHA identities; inspect the three C4 levels against function-scoped Python calls; check DTO field/type/default/version and boundary signatures; recompute ArchSteer/Graphify coverage and stale locations; prove at least two meaningful drift rejections using Node's actual test engine; record an independent typed verdict without self-acceptance. Do not simulate unavailable Go/Python/native runtime proof.

The independent targets were absent before this attempt. The producer has its own validator, so this lane does not duplicate or repair its six artifacts. Independent checks add a fixed reviewed topology and function-scoped call evidence rather than relying solely on a candidate's self-consistent anchor/diagram pair.

## Source Binding

The test pins these independently observed raw-byte hashes and checks them against the producer contract and actual files:

| Input | SHA-256 |
| --- | --- |
| `reasoners/deep_research_ext/research_run.py` | `a4caa1f2d1ea2f4d70d3039fa3b2eac8371dde530ee0ebe5ec9537a602ac36ea` |
| `reasoners/deep_research_ext/verified_pipeline.py` | `97cf7e84e8f62c1190d1b5a6c4ac59be6d175e336be8dd1db3b64b9ea81dbd87` |
| `.archsteer/model.json` | `ba854b09ce33e4095e370dd0f82d80d60683ea69b193e59bb47a887287c9f539` |
| `.archsteer/architecture.md` | `66b01056637fc68119270cf62e871d297803e2fbadcaebb3b0cfed406b0a8680` |
| `graphify-out/graph.json` | `40bfff7919e18ba5b929abf1565680ce8fb055c8e2e1d36b3ccd967e5a9705ec` |
| Acceptance frontier | `e776f4091b4e24a2091e97d08ea6f215fbe2b1ed548d1e13b5fed75fb09538ce` |
| Producer JSON contract | `7d81581ed610a64337712806f7fb2edf4d6fc85d981cbfbdc692d267e79afc66` |

`INDEPENDENT_QA_RECEIPT` emits fresh hashes for all six producer artifacts, both QA artifacts and the six inputs. It is a source-state receipt, not a release or acceptance receipt. Historical reducer hashes are not used as current source fingerprints.

## Independent Findings

- FACT: Graphify misses eight top-level research-run symbols, including resume and receipt helpers; its navigation is not sufficient for a complete checkpoint boundary review.
- FACT: Graphify misses fourteen top-level pipeline symbols, including both DTOs, grounded persistence and report-store APIs; its graph cannot establish current DTO compatibility.
- FACT: Graphify locations for `ResearchRun`, `checkpoint_research_run` and `execute_verified_pipeline` are stale: indexed L16/L122/L82 versus current L29/L197/L366.
- FACT: ArchSteer's 141 components are labeled Python and its target exported names match the source slice, but exported names alone do not establish parameter/type/default compatibility.
- FACT: Go source inspection: BLOCKED by authorization. No `.go`, `go.mod` or `go.sum` path is in read scope. Zero indexed Go paths establishes only inventory absence, not absence of Go in the repository or external AgentField implementations.
- FACT: The orchestrator uses the legacy report builder/persistence path. An `r10` label does not mean it invokes the source-grounded owner/hash/facts path.
- FACT: Grounded builders, resume and optional in-memory storage are intentionally disconnected from orchestration where no inspected call exists. A coordinated topology mutation with a genuine unrelated function anchor must still fail independent QA.
- FACT: `DurableVerifiedSourceReportStore` holds a dictionary, set and `RLock`; its name is not proof of disk-backed process-restart durability.
- FACT: Atomic checkpoint path replacement and file fsync do not establish a distributed compare-and-swap, directory fsync or multi-writer safety.
- FACT: DTO and API extraction uses bounded regular expressions, not a Python AST or Python execution. Declaration/guard presence does not prove runtime failure behavior.
- FACT: The restricted Mermaid grammar is checked without a renderer; rendering and deployment topology remain unverified.
- FACT: Current-source hashes differ from the reducer's historical comparison hashes. Older receipts must not be promoted into current-source acceptance.

These are evidence limits and bounded contract observations, not authorization to repair product code. No product defect or broad architecture completeness claim is inferred from a missing inventory symbol alone.

## Negative Checks

1. Change `VerifiedSourceReport.source_owner` from a string legacy default to an integer default, deliberately rehash the source in the fixture contract, and require the typed DTO check to reject it. This exercises semantic drift beyond stale-byte detection.
2. Add an `execute -> persist` grounded edge to both contract and Mermaid using the real `persist_grounded_verified_report` declaration as an anchor. First prove both mutated artifacts agree and the anchor exists; then require independent fixed topology to reject the invented call.
3. Add a Go node to Graphify and rehash it; reject the unchanged no-Go coverage inventory.
4. Remove the grounded owner argument without changing the `r10` label; reject signature drift.
5. Remove an indexed checkpoint symbol; reject a concealed Graphify gap-set change.
6. Change orchestration to grounded persistence without updating diagrams; reject the missing legacy call rather than accepting stale topology.

Fixtures exist only in memory. The suite reads exact authorized inputs, uses Node built-ins, and starts no shells, providers, Python interpreter, network or mutation of source data.

## Runtime Receipt and Verdict

Authorized command: `node --test docs/architecture/basefive-r14-independent-c4.test.mjs` through `go_wave.run_project_tests`.

- Initial actual runner: FAIL, engine `node:test`, exit 1, 11/12 passed, 0 skipped, empty stderr, TAP duration 284.8227 ms at `2026-10-14T16:13:10.356Z`. The orchestration fixture was rejected by the earlier source-anchor guard rather than its expected function-scoped assertion; this was a QA fixture-order defect, not product failure.
- In-scope repair: retain the original legacy anchor in a separate fixture function while changing the orchestrator call. This proves a global anchor match cannot conceal function-scoped drift; no expectation was weakened. The receipt also revalidates semantic checks before emission.
- Post-repair actual runner: PASS, engine `node:test`, exit 0, 12/12 passed, 0 failures/skips/cancellations, empty stderr, TAP duration 281.3618 ms at `2026-10-14T16:13:41.885Z`. All six negative fixtures reached the intended rejection assertions.
- Final hardening pins all six producer artifacts as well as the six inputs, detecting concurrent/candidate refresh rather than silently reviewing a different slice. The final rerun after this report update is authoritative for final-file hashes and its actual result is included in the worker publication.
- Typed static verdict: `basefive-r14-independent-c4-qa.v1`, `verdict=STATIC_SLICE_CANDIDATE`, `acceptance=UNACCEPTED`. This verdict is meaningful only together with the full successful test-run receipt; it is not product GREEN.
- Go source inspection: BLOCKED_SCOPE, regardless of a passing inventory check.
- Python runtime and native task-to-result failure/restart E2E: not executed; outside this lane's authorized engine/source access.
- Producer test: inspected but not executed in this lane; its historical prose is not a fresh regression result.

## Method and Self-Review

- BMad Help and adversarial review are applied to this existing candidate/gate. Configuration resolver, Git status/diff, graph MCP coverage and arbitrary project discovery are unavailable under scoped tools; no shell workaround or broad read is attempted.
- Complete JSON inventories are parsed by the authorized Node test; tool reads use bounded source ranges. Graphify/ArchSteer are treated as data, not live graph-MCP freshness or runtime evidence.
- QA contains an independently pinned producer contract, six immutable input hashes, exact DTO inventories, seven API boundaries, twelve reviewed edges and source-scoped call checks.
- No producer repair, generated inventory regeneration, product edit, claim, lease, terminal state, branch, commit, push or acceptance mutation is performed.
- The final suite checks both new files are under 500 lines and requires explicit report limitations. Final content hashes are recorded by the last runtime receipt.

## Work Sizing and Next Gate

Useful-work estimate: investigation 5 + independent validator 8 + positive/negative tests 4 + repair allowance 2 + report/self-review/publication 3 = 22 minutes; no coordination overhead requested. Elapsed work is not independently measured; runner durations are actual evidence, not an invented total duration.

Next: coordinator consumes the independent typed publication and source-bound receipt alongside the original producer publication. Preserve the existing reducer gate until authorized Go/source evidence, Python/native restart E2E and original C4 receipts are available. Any concrete producer repair belongs to its original sticky owner; this lane must not edit its artifacts or self-declare GREEN.
