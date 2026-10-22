# A55 emergency rescue inventory — 2026-10-22

Purpose: preserve the latest AF Deep Research work from the failing A55 disk **without merging diverged development branches**. All refs below are independently confirmed against GitHub API Git refs, not merely local tracking refs.

## Confirmed cloud snapshots

| Area | GitHub branch | Cloud commit SHA |
| --- | --- | --- |
| Latest combined AF Deep Research source, tests, and current working content | `rescue/a55-live-snapshot-20261022` | `3578ebf8f9d597006262c194d9716649cfa5bd76` |
| Alternative AFRT Deep Research runtime implementation | `rescue/a55-afrt-runtime-20261022` | `e7cb1bce7d8926b4bf110d577e18ccb93f1ae21a` |
| Integrated P0 branch | `recovery/a55-20261022/afdr-p0-integration-latest` | `26897d223d88862f4b61bf5e15a39122e2237da5` |
| Official source authority/classification improvements | `recovery/a55-20261022/afdr-bmad-primary-sources-latest` | `97a3916aaa9c3b3873716f4a09098f8b809a67ed` |
| Exact source review | `recovery/a55-20261022/afdr-p0-review-latest` | `4c2e325ec85d7eae8e85d2ae9788fa2d2c962b29` |
| Strict publication branch | `recovery/a55-20261022/afdr-p0-strict-publication-20261020` | `760bb8e6e599388b7d0cb624b99994eaea812e1d` |
| Independent strict QA snapshot | `recovery/a55-20261022/afdr-p0-strict-independent-qa-20261020` | `d854c650bf15980e1bcf1b22152937c4d4b7e584` |

The A55 source repo was in `rescue/a55-live-snapshot-20261022` at commit `3578ebf` (committed October 22, 2026 at 20:53 local). The alternative runtime rescue commit `e7cb1bc` was recorded at 20:55 local. No merge into `dev` or `main` has been performed.

## Current protected exclusions, known limitations

- Main A55 rescue worktree has one remaining untracked local file: `.mcp.json`. **Intentionally excluded as potentially credential-bearing**.
- P0 exact review worktree also has an untracked `.codex/` directory; do not blindly publish its contents.
- Alternative runtime has untracked diagnostic outputs under `.r2-runtime-runs/`, `.r3-runtime-runs/`, `.r5-runtime-runs/`, `.swarm/`, `.claude-flow/` and `.codex/`, plus `RESULT_*.json` and `.graphify-code/tests/`. These are not confirmed cloud-backed and may contain sensitive local state. Review and sanitize separately before sharing.
- Legacy B03 research-search worktree has untracked tooling directories and a changed `.gitignore`, not automatically imported into the main rescue branch.
- On October 22 at approximately 21:14 local, A55 `git ls-remote` to GitHub failed with OpenSSL `SSL_ERROR_SYSCALL`, whereas the VP49 host was able to reach GitHub. All GitHub refs listed above were independently verified through the connected GitHub API.
- The combined snapshot contains important `opencodex_responses.py`, native AgentField benchmark tests, the 12-case golden fixture, current federated-search test, and acceptance evidence. It intentionally does not certify functional correctness or independent QA.
- Never overwrite `dev`/`main` or force-push these refs as part of recovery. Decide integration after A55 hardware is secured.

## Recovery recommendation

1. Clone `https://github.com/n0namer/af-deep-research.git` on a healthy computer; fetch all branches.
2. Start from `rescue/a55-live-snapshot-20261022` as the full working snapshot, then inspect each specialized ref above for improvements using Git compare and worktrees. Do not assume the union is already integrated.
3. Re-run the existing pytest suite and a small real AgentField E2E; evaluate strict grounded report behavior independently.
4. Recover required untracked diagnostic artifacts and local secrets from an encrypted, access-controlled backup if still obtainable; **never commit plaintext secrets to GitHub**.

This manifest was authored by the recovery assistant after SHA-by-SHA cloud verification and pushed through the connected GitHub API because direct HTTPS from A55 was unavailable.
