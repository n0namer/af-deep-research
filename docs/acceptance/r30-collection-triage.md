# R30 collection triage acceptance

## Source of truth and scope

This artifact records the isolated collection oracle for
`af-deep-research:v2-r29-collection-triage-20261015-r1`. It does not modify
the original r29 tests or production modules.

## Owner-keyed repair plan

- **async extractor owner:** repair the native pytest fixture/callback contract
  so the async extractor is invoked with its declared keyword-only context;
  reject positional binding.
- **dynamic dataclass loader owner:** insert the dynamically created module into
  `sys.modules` before executing its dataclass body; remove it on teardown.
- **verified pipeline import owner:** execute the verifier as a package module
  (or provide an explicit package context) so relative imports resolve; reject
  top-level execution without `__package__`.

## Oracle

The six tests provide three positive executable import/signature checks and
three negative checks for the corresponding invalid collection patterns. The
r29 files remain read-only. Run:

`.venv/Scripts/python.exe -m pytest -q tests/test_r30_collection_triage.py`

Expected evidence is the exact pytest exit code, collected/pass counts, and
source SHA256 for both authorized files.
