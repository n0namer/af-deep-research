# R29 Final Fact Verifier

Status: CANDIDATE / UNACCEPTED

The final verifier now rejects repeated citation markers before candidate fact
construction, preserving exact citation identity and preventing duplicate markers
from collapsing into one accepted fact.

Focused evidence:
- Positive: exact fact ID with allowed, source-supported assessment passes.
- Negatives: missing citation, duplicate citation identity, unknown citation,
  wrong fact ID, and unsupported evidence fail closed.
- Command: python -m pytest -q tests/test_r29_final_fact_verifier.py

Independent QA/reducer and authoritative CrewSync terminal readback remain required.
