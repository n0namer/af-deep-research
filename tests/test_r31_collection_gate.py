from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COLLECTION_TARGETS = (
    "tests/test_r30_collection_triage.py",
    "tests/test_r30_native_smoke.py",
)
REPAIRED_R29_TARGETS = (
    "tests/test_r29_abstention_e2e.py",
    "tests/test_r29_arch_c4_graphify.py",
    "tests/test_r29_primary_source_eval.py",
)


def _collect(*paths: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q", *paths],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=30,
    )


def _assert_collects(path: str) -> None:
    result = _collect(path)
    output = result.stdout + result.stderr
    assert result.returncode == 0, output
    assert "ERROR collecting" not in output
    assert "test_" in result.stdout


def test_r29_r30_collection_gate_accepts_current_targets():
    result = _collect(*COLLECTION_TARGETS)
    output = result.stdout + result.stderr
    assert result.returncode == 0, output
    assert "ERROR collecting" not in output
    assert result.stdout.count("test_") >= 10


def test_r29_abstention_collection_succeeds_after_syntax_repair():
    _assert_collects(REPAIRED_R29_TARGETS[0])


def test_r29_arch_collection_succeeds_after_package_registration_repair():
    _assert_collects(REPAIRED_R29_TARGETS[1])


def test_r29_primary_source_collection_succeeds_after_import_repair():
    _assert_collects(REPAIRED_R29_TARGETS[2])
