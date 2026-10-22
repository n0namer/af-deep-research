# R29 Native E2E Release Gate

Status: CANDIDATE / UNACCEPTED

## Scope and source identity

This bounded gate verifies the real local restart/report persistence boundary for a
research question. It uses the repository implementations directly and does not
claim external provider/network acceptance.

Source-bound evidence read through the authorized project reader:

| Source | Current SHA-256 |
| --- | --- |
| `reasoners/deep_research_ext/research_run.py` | `87c193a386be13daa2b89dceac6b749a87ae9b47efd84b18bd598017c6e9e8c3` |
| `reasoners/deep_research_ext/verified_pipeline.py` | `97cf7e84e8f62c1190d1b5a6c4ac59be6d175e336be8dd1db3b64b9ea81dbd87` |
| `reasoners/deep_research_ext/final_verifier.py` | `d812e7f1b4f9b5375c5e0473076c84d8251b2e92e9aa42ae0d84be41f1b16e4f` |
| `docs/architecture/basefive-r14-contracts.json` | `7d81581ed610a64337712806f7fb2edf4d6fc85d981cbfbdc692d267e79afc66` |
| Prior C4 acceptance artifact | `e776f4091b4e24a2091e97d08ea6f215fbe2b1ed548d1e13b5fed75fb09538ce` |

## Gate matrix

- Positive: real question -> durable run checkpoints -> terminal resume trace -> grounded r10 report -> report restart.
- Negative 1: stale source revision is rejected.
- Negative 2: stale checkpoint sequence is rejected.
- Negative 3: wrong report owner and wrong source SHA are rejected.
- Negative 4: duplicate grounded fact IDs are rejected.
- No provider/network call is faked or counted as a full external E2E acceptance.

## Validation

Requested command:

`python -m pytest -q tests/test_r29_native_e2e_release.py`

The scoped runner must provide the actual pytest exit code and output. A denied or
unavailable Python runner is INFRA BLOCKED and must not be converted to PASS.

## Limitations and handoff

The current readable C4 artifact remains CANDIDATE/UNACCEPTED and explicitly records
missing original C4 producer/independent-QA receipts and missing native task-to-result
CrewSync readback. This file supplies the bounded source-level restart/report gate;
independent QA/reducer and coordinator terminal readback remain required.
