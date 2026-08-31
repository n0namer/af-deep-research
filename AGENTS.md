# AGENTS.md

## Repository entry point

AF Deep Research owns the research product/runtime source. The active development lane may differ from default `main`; resolve the intended branch and CURRENT permanent DEV source before mutation.

Read the material subset of `PLAN.md`, `README.md`, relevant `reasoners/`, `tests/` and runtime entry code. For verified-research work, HTTP/execution success is not semantic acceptance: requirement coverage, source admissibility, exact-source entailment and final-claim verification are separate gates. After reload, prove the loaded reasoner/schema identity.

## Fast Verified Engineering

Canonical organization standard: `n0namer/server-ops:docs/standards/FAST_VERIFIED_ENGINEERING.md`.

Objective: minimize **time-to-verified-running-change**, not time-to-patch or time-to-merge.

Before material mutation: read applicable SoT and `ERRORS.md` when present; resolve `Project North Star -> Phase Goal -> gate/DoD -> next bounded move`; observe exact source/dirty state and runtime identity when relevant; define scope, rollback and required evidence.

Keep design SoT, source state, loaded runtime, concrete execution, deterministic validation and functional/semantic outcome separate. Code-on-disk != loaded runtime; tests != deploy proof; health/HTTP 200 or `succeeded` != acceptance.

Route for speed: runtime-bound defects use an already opted-in permanent DEV target with bounded stale-safe patch -> affected check -> same-runtime reload if needed -> canary/log evidence. Source-bound/multi-file work prefers an exact-SHA isolated Coding Station workspace. GitHub/CI/deploy is the canonicalization/release boundary, not the default inner debug loop.

Never rewrite an already verified fix when moving lanes; preserve the exact owned delta, base/file identity, validation evidence, runtime evidence and rollback where capabilities allow.

Validation ladder: `syntax/static -> affected tests -> related regression -> full required suite -> runtime smoke/integration -> semantic/business/E2E`.

Use narrow-to-broad diagnostics: structured execution evidence -> execution-scoped logs -> bounded target logs -> broader service/node logs. Correlate with source/runtime identity and execution/request IDs.

Production live editing is forbidden by default. Preserve unrelated state. On timeout/ambiguous mutation, inspect post-state before retrying.

Final status is exactly `DONE | PARTIAL | BLOCKED | FAILED | EVIDENCE_MISSING`; DONE requires every task-specific DoD evidence item.