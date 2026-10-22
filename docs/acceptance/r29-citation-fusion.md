# R29 Citation Fusion Acceptance

Status: CANDIDATE / UNACCEPTED

## Scope and source evidence

This bounded change strengthens skills/search/fusion.py::canonicalize_url for independent citation identity:

- blank or malformed URLs do not become citation identities;
- scheme and hostname are case-insensitive;
- default HTTP/HTTPS ports are removed while meaningful ports remain;
- dot-segment paths are resolved;
- fragments and known tracking parameters remain excluded;
- meaningful query parameters remain part of identity.

The fusion contract remains reciprocal-rank fusion over canonical URL keys. The representative result still preserves the longer evidence content and records provider ranks.

## Focused validation

Requested command:

    python -m pytest -q tests/test_r29_citation_fusion.py

Actual scoped runner receipt:

    status=BLOCKED
    code=PYTHON_VENV_UNAVAILABLE
    engine=python:pytest
    source_identity_sha256=6bed5b14d4fff995eec3b2db5c8adbbd588322635f5fb09c16d137df817f3ba1
    exit_code=null
    stderr="A regular local .venv Python executable is required."

No PASS is claimed. The test contains one positive fusion case and four adversarial negative/boundary cases, but native pytest execution is pending an authorized environment with the required local .venv.

## Remaining

Independent QA/reducer must rerun the exact pytest command, inspect the final source/test hashes, and perform the required CrewSync terminal readback. No production deployment, commit, or task acceptance is performed here.
