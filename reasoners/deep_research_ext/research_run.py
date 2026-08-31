from __future__ import annotations

import json
import os
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Tuple

SCHEMA_VERSION = "0.1"
DEFAULT_RUN_ROOT = "/e2e/deep-research-runs"


@dataclass(frozen=True)
class ResearchRun:
    run_id: str
    query: str
    stage: str
    checkpoint_seq: int
    status: str
    created_at: float
    updated_at: float
    schema_version: str = SCHEMA_VERSION
    replay_source_run_id: Optional[str] = None
    source_ids: Tuple[str, ...] = ()
    evidence_summary: Mapping[str, Any] = field(default_factory=dict)
    coverage_state: Mapping[str, Any] = field(default_factory=dict)
    open_gap_ids: Tuple[str, ...] = ()
    conflicts: Tuple[str, ...] = ()
    budgets: Mapping[str, Any] = field(default_factory=dict)
    payload: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "ResearchRun":
        data = dict(value)
        for key in ("source_ids", "open_gap_ids", "conflicts"):
            data[key] = tuple(data.get(key) or ())
        return cls(**data)


class ResearchRunStore:
    def __init__(self, root: Optional[str] = None):
        self.root = Path(root or os.getenv("DR_RESEARCH_RUN_DIR", DEFAULT_RUN_ROOT))

    def path_for(self, run_id: str) -> Path:
        safe = "".join(ch for ch in run_id if ch.isalnum() or ch in {"-", "_", "."})
        if not safe or safe != run_id:
            raise ValueError("unsafe run_id")
        return self.root / f"{safe}.json"

    def save(self, run: ResearchRun) -> Path:
        self.root.mkdir(parents=True, exist_ok=True)
        path = self.path_for(run.run_id)
        tmp = path.with_suffix(path.suffix + f".tmp-{os.getpid()}-{uuid.uuid4().hex[:8]}")
        raw = json.dumps(run.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        with open(tmp, "w", encoding="utf-8") as handle:
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, path)
        return path

    def load(self, run_id: str) -> Optional[ResearchRun]:
        path = self.path_for(run_id)
        if not path.exists():
            return None
        with open(path, "r", encoding="utf-8") as handle:
            return ResearchRun.from_dict(json.load(handle))


def current_agentfield_identity() -> Tuple[Optional[str], Optional[str]]:
    try:
        from agentfield.execution_context import get_current_context
        context = get_current_context()
    except Exception:
        context = None
    if context is None:
        return None, None
    return getattr(context, "run_id", None), getattr(context, "replay_source_run_id", None)


def begin_research_run(query: str, *, store: Optional[ResearchRunStore] = None) -> Tuple[ResearchRunStore, ResearchRun]:
    store = store or ResearchRunStore()
    agentfield_run_id, replay_source_run_id = current_agentfield_identity()
    run_id = agentfield_run_id or f"dr_{int(time.time() * 1000)}_{uuid.uuid4().hex[:8]}"
    existing = store.load(run_id)
    if existing is not None:
        if existing.query != query:
            raise ValueError("run_id already exists for a different query")
        return store, existing
    replay_source = store.load(replay_source_run_id) if replay_source_run_id else None
    if replay_source is not None and replay_source.query != query:
        raise ValueError("replay source run belongs to a different query")
    now = time.time()
    inherited_payload = dict(replay_source.payload) if replay_source is not None else {}
    has_research_package = isinstance(inherited_payload.get("research_package"), dict)
    run = ResearchRun(
        run_id=run_id,
        query=query,
        stage="research_package_ready" if has_research_package else "started",
        checkpoint_seq=0,
        status="running",
        created_at=now,
        updated_at=now,
        replay_source_run_id=replay_source_run_id,
        source_ids=tuple(replay_source.source_ids) if replay_source is not None else (),
        evidence_summary=dict(replay_source.evidence_summary) if replay_source is not None else {},
        coverage_state=dict(replay_source.coverage_state) if replay_source is not None else {},
        open_gap_ids=tuple(replay_source.open_gap_ids) if replay_source is not None else (),
        conflicts=tuple(replay_source.conflicts) if replay_source is not None else (),
        budgets=dict(replay_source.budgets) if replay_source is not None else {},
        payload=inherited_payload,
    )
    store.save(run)
    return store, run


def checkpoint_research_run(
    store: ResearchRunStore,
    run: ResearchRun,
    *,
    stage: str,
    status: Optional[str] = None,
    source_ids: Optional[Tuple[str, ...]] = None,
    evidence_summary: Optional[Mapping[str, Any]] = None,
    coverage_state: Optional[Mapping[str, Any]] = None,
    open_gap_ids: Optional[Tuple[str, ...]] = None,
    conflicts: Optional[Tuple[str, ...]] = None,
    budgets: Optional[Mapping[str, Any]] = None,
    payload: Optional[Mapping[str, Any]] = None,
) -> ResearchRun:
    updated = ResearchRun(
        run_id=run.run_id,
        query=run.query,
        stage=stage,
        checkpoint_seq=run.checkpoint_seq + 1,
        status=status or run.status,
        created_at=run.created_at,
        updated_at=time.time(),
        schema_version=run.schema_version,
        replay_source_run_id=run.replay_source_run_id,
        source_ids=tuple(source_ids if source_ids is not None else run.source_ids),
        evidence_summary=dict(evidence_summary if evidence_summary is not None else run.evidence_summary),
        coverage_state=dict(coverage_state if coverage_state is not None else run.coverage_state),
        open_gap_ids=tuple(open_gap_ids if open_gap_ids is not None else run.open_gap_ids),
        conflicts=tuple(conflicts if conflicts is not None else run.conflicts),
        budgets=dict(budgets if budgets is not None else run.budgets),
        payload=dict(payload if payload is not None else run.payload),
    )
    store.save(updated)
    return updated


def next_resume_stage(run: ResearchRun) -> str:
    order = {
        "started": "research",
        "research_package_ready": "evidence_verification",
        "evidence_verified": "synthesis",
        "synthesis_ready": "final_verification",
        "completed": "done",
        "failed": "inspect_failure",
    }
    return order.get(run.stage, "inspect_checkpoint")
