from __future__ import annotations

import json
import os
import functools
from contextlib import contextmanager
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Tuple

SCHEMA_VERSION = "0.1"
DEFAULT_RUN_ROOT = "/e2e/deep-research-runs"
CHECKPOINT_STAGES = (
    "started", "query", "contract_ready", "retrieval", "research_package_ready", "ledger",
    "evidence_verified", "coverage", "synthesis", "synthesis_ready",
    "final_review", "completed", "failed",
)


class ResearchRunCheckpointError(ValueError):
    """Raised when a persisted run cannot be safely resumed."""


class StaleResearchRunError(ResearchRunCheckpointError):
    """Raised when a checkpoint belongs to a different source revision."""


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
    source_revision: Optional[str] = None
    source_owner: Optional[str] = None
    source_ids: Tuple[str, ...] = ()
    evidence_ids: Tuple[str, ...] = ()
    evidence_summary: Mapping[str, Any] = field(default_factory=dict)
    coverage_state: Mapping[str, Any] = field(default_factory=dict)
    open_gap_ids: Tuple[str, ...] = ()
    conflicts: Tuple[str, ...] = ()
    stage_history: Tuple[str, ...] = ()
    budgets: Mapping[str, Any] = field(default_factory=dict)
    payload: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "ResearchRun":
        if not isinstance(value, Mapping):
            raise ResearchRunCheckpointError("checkpoint must contain an object")
        data = dict(value)
        data.setdefault("source_revision", None)
        data.setdefault("source_owner", None)
        data.setdefault("evidence_ids", ())
        data.setdefault("stage_history", ())
        for key in ("source_ids", "evidence_ids", "open_gap_ids", "conflicts", "stage_history"):
            data[key] = tuple(data.get(key) or ())
        if data.get("schema_version") != SCHEMA_VERSION:
            raise ResearchRunCheckpointError("unsupported checkpoint schema")
        if data.get("stage") not in CHECKPOINT_STAGES:
            raise ResearchRunCheckpointError("unknown checkpoint stage")
        try:
            return cls(**data)
        except (TypeError, ValueError) as exc:
            raise ResearchRunCheckpointError("invalid checkpoint fields") from exc


class ResearchRunStore:
    def __init__(self, root: Optional[str] = None):
        self.root = Path(root or os.getenv("DR_RESEARCH_RUN_DIR", DEFAULT_RUN_ROOT))

    def path_for(self, run_id: str) -> Path:
        safe = "".join(ch for ch in run_id if ch.isalnum() or ch in {"-", "_", "."})
        if not safe or safe != run_id:
            raise ValueError("unsafe run_id")
        return self.root / f"{safe}.json"

    @contextmanager
    def lock_run(self, run_id: str):
        """Serialize the complete checkpoint read/compare/write across OS processes."""
        lock_path = self.path_for(run_id).with_suffix(".json.lock")
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        with open(lock_path, "a+b") as stream:
            stream.seek(0, os.SEEK_END)
            if stream.tell() == 0:
                stream.write(b"\0")
                stream.flush()
            stream.seek(0)
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(stream.fileno(), msvcrt.LK_LOCK, 1)
            else:
                import fcntl
                fcntl.flock(stream.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                stream.seek(0)
                if os.name == "nt":
                    msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    fcntl.flock(stream.fileno(), fcntl.LOCK_UN)

    def save(self, run: ResearchRun) -> Path:
        if run.stage not in CHECKPOINT_STAGES:
            raise ResearchRunCheckpointError("unknown checkpoint stage")
        if run.checkpoint_seq < 0:
            raise ResearchRunCheckpointError("checkpoint sequence must be non-negative")
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

    def load(self, run_id: str, *, source_revision: Optional[str] = None) -> Optional[ResearchRun]:
        path = self.path_for(run_id)
        if not path.exists():
            return None
        try:
            with open(path, "r", encoding="utf-8") as handle:
                run = ResearchRun.from_dict(json.load(handle))
        except (OSError, json.JSONDecodeError, ResearchRunCheckpointError) as exc:
            if isinstance(exc, ResearchRunCheckpointError):
                raise
            raise ResearchRunCheckpointError(f"corrupt checkpoint: {run_id}") from exc
        if source_revision is not None and run.source_revision not in {None, source_revision}:
            raise StaleResearchRunError(
                f"checkpoint {run_id} belongs to source revision {run.source_revision!r}, not {source_revision!r}"
            )
        return run


def _unique_strings(values: Any) -> Tuple[str, ...]:
    result = []
    seen = set()
    for value in values or ():
        item = str(value)
        if item and item not in seen:
            seen.add(item)
            result.append(item)
    return tuple(result)


def current_agentfield_identity() -> Tuple[Optional[str], Optional[str]]:
    try:
        from agentfield.execution_context import get_current_context
        context = get_current_context()
    except Exception:
        context = None
    if context is None:
        return None, None
    return getattr(context, "run_id", None), getattr(context, "replay_source_run_id", None)


def begin_research_run(
    query: str,
    *,
    store: Optional[ResearchRunStore] = None,
    source_revision: Optional[str] = None,
    source_owner: Optional[str] = None,
) -> Tuple[ResearchRunStore, ResearchRun]:
    store = store or ResearchRunStore()
    agentfield_run_id, replay_source_run_id = current_agentfield_identity()
    run_id = agentfield_run_id or f"dr_{int(time.time() * 1000)}_{uuid.uuid4().hex[:8]}"
    existing = store.load(run_id, source_revision=source_revision)
    if existing is not None:
        if existing.query != query:
            raise ValueError("run_id already exists for a different query")
        if source_owner is not None and existing.source_owner not in {None, source_owner}:
            raise ResearchRunCheckpointError("run_id already exists for a different source owner")
        return store, existing
    replay_source = store.load(replay_source_run_id) if replay_source_run_id else None
    if replay_source is not None and replay_source.query != query:
        raise ValueError("replay source run belongs to a different query")
    if replay_source is not None and source_revision is not None and replay_source.source_revision not in {None, source_revision}:
        raise StaleResearchRunError(
            f"replay source belongs to source revision {replay_source.source_revision!r}, not {source_revision!r}"
        )
    if replay_source is not None and source_owner is not None and replay_source.source_owner not in {None, source_owner}:
        raise ResearchRunCheckpointError(
            f"replay source belongs to source owner {replay_source.source_owner!r}, not {source_owner!r}"
        )
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
        source_revision=source_revision or (replay_source.source_revision if replay_source is not None else None),
        source_owner=source_owner or (replay_source.source_owner if replay_source is not None else None),
        source_ids=tuple(replay_source.source_ids) if replay_source is not None else (),
        evidence_ids=tuple(replay_source.evidence_ids) if replay_source is not None else (),
        evidence_summary=dict(replay_source.evidence_summary) if replay_source is not None else {},
        coverage_state=dict(replay_source.coverage_state) if replay_source is not None else {},
        open_gap_ids=tuple(replay_source.open_gap_ids) if replay_source is not None else (),
        conflicts=tuple(replay_source.conflicts) if replay_source is not None else (),
        stage_history=(tuple(replay_source.stage_history) if replay_source is not None and replay_source.stage_history else ("started",)),
        budgets=dict(replay_source.budgets) if replay_source is not None else {},
        payload=inherited_payload,
    )
    store.save(run)
    return store, run


def _atomic_run_checkpoint(func):
    @functools.wraps(func)
    def wrapped(store, run, *args, **kwargs):
        with store.lock_run(run.run_id):
            return func(store, run, *args, **kwargs)
    return wrapped


@_atomic_run_checkpoint
def checkpoint_research_run(
    store: ResearchRunStore,
    run: ResearchRun,
    *,
    stage: str,
    status: Optional[str] = None,
    source_revision: Optional[str] = None,
    source_owner: Optional[str] = None,
    expected_checkpoint_seq: Optional[int] = None,
    source_ids: Optional[Tuple[str, ...]] = None,
    evidence_ids: Optional[Tuple[str, ...]] = None,
    evidence_summary: Optional[Mapping[str, Any]] = None,
    coverage_state: Optional[Mapping[str, Any]] = None,
    open_gap_ids: Optional[Tuple[str, ...]] = None,
    conflicts: Optional[Tuple[str, ...]] = None,
    budgets: Optional[Mapping[str, Any]] = None,
    payload: Optional[Mapping[str, Any]] = None,
) -> ResearchRun:
    if stage not in CHECKPOINT_STAGES:
        raise ResearchRunCheckpointError(f"unknown checkpoint stage: {stage}")
    persisted = store.load(run.run_id, source_revision=source_revision)
    current = persisted or run
    if persisted is not None and (
        persisted.query != run.query
        or persisted.created_at != run.created_at
        or persisted.replay_source_run_id != run.replay_source_run_id
        or (persisted.source_revision is not None and run.source_revision is not None and persisted.source_revision != run.source_revision)
        # The persisted owner is part of the CAS identity.  Comparing exact
        # values also fences a stale unowned in-memory snapshot from adopting
        # a checkpoint that another owner has since claimed.
        or persisted.source_owner != run.source_owner
    ):
        raise ResearchRunCheckpointError("checkpoint owner mismatch")
    if persisted is not None and current.checkpoint_seq != run.checkpoint_seq:
        raise ResearchRunCheckpointError("checkpoint sequence is stale")
    if expected_checkpoint_seq is not None and current.checkpoint_seq != expected_checkpoint_seq:
        raise ResearchRunCheckpointError("checkpoint sequence is stale")
    if source_revision is not None and current.source_revision not in {None, source_revision}:
        raise StaleResearchRunError(f"checkpoint belongs to source revision {current.source_revision!r}, not {source_revision!r}")
    if source_owner is not None and current.source_owner not in {None, source_owner}:
        raise ResearchRunCheckpointError(f"checkpoint belongs to source owner {current.source_owner!r}, not {source_owner!r}")
    resolved_revision = source_revision if source_revision is not None else current.source_revision
    resolved_owner = source_owner if source_owner is not None else current.source_owner
    history = tuple(current.stage_history or ())
    if not history or history[-1] != stage:
        history = history + (stage,)
    next_payload = dict(payload if payload is not None else current.payload)
    provider_call_ids = _unique_strings(recorded_provider_call_ids(current) + tuple((payload or {}).get("provider_call_ids") or ()))
    next_evidence_ids = _unique_strings(tuple(current.evidence_ids) + tuple(evidence_ids or ()) + tuple((payload or {}).get("evidence_ids") or ()))
    if provider_call_ids:
        next_payload["provider_call_ids"] = list(provider_call_ids)
    if next_evidence_ids:
        next_payload["evidence_ids"] = list(next_evidence_ids)
    updated = ResearchRun(
        run_id=current.run_id,
        query=current.query,
        stage=stage,
        checkpoint_seq=current.checkpoint_seq + 1,
        status=status or current.status,
        created_at=current.created_at,
        updated_at=time.time(),
        schema_version=current.schema_version,
        replay_source_run_id=current.replay_source_run_id,
        source_revision=resolved_revision,
        source_owner=resolved_owner,
        source_ids=_unique_strings(source_ids if source_ids is not None else current.source_ids),
        evidence_ids=next_evidence_ids,
        evidence_summary=dict(evidence_summary if evidence_summary is not None else current.evidence_summary),
        coverage_state=dict(coverage_state if coverage_state is not None else current.coverage_state),
        open_gap_ids=_unique_strings(open_gap_ids if open_gap_ids is not None else current.open_gap_ids),
        conflicts=_unique_strings(conflicts if conflicts is not None else current.conflicts),
        stage_history=history,
        budgets=dict(budgets if budgets is not None else current.budgets),
        payload=next_payload,
    )
    store.save(updated)
    return updated


def next_resume_stage(run: ResearchRun) -> str:
    return {
        "started": "research", "query": "retrieval", "retrieval": "ledger",
        "contract_ready": "research", "research_package_ready": "evidence_verification",
        "ledger": "coverage", "evidence_verified": "synthesis", "coverage": "final_review",
        "synthesis": "final_review", "synthesis_ready": "final_verification",
        "final_review": "done", "completed": "done", "failed": "inspect_failure",
    }.get(run.stage, "inspect_checkpoint")


def recorded_provider_call_ids(run: ResearchRun) -> Tuple[str, ...]:
    values = run.payload.get("provider_call_ids", ()) if isinstance(run.payload, Mapping) else ()
    return _unique_strings(values)


def provider_call_already_recorded(run: ResearchRun, call_id: str) -> bool:
    return str(call_id) in set(recorded_provider_call_ids(run))


def recorded_evidence_ids(run: ResearchRun) -> Tuple[str, ...]:
    payload_values = run.payload.get("evidence_ids", ()) if isinstance(run.payload, Mapping) else ()
    return _unique_strings(tuple(run.evidence_ids) + tuple(payload_values or ()))


def evidence_already_recorded(run: ResearchRun, evidence_id: str) -> bool:
    return str(evidence_id) in set(recorded_evidence_ids(run))


def resume_research_run(
    store: ResearchRunStore,
    run_id: str,
    *,
    source_revision: Optional[str] = None,
    source_owner: Optional[str] = None,
) -> Tuple[ResearchRun, Dict[str, Any]]:
    run = store.load(run_id, source_revision=source_revision)
    if run is None:
        raise FileNotFoundError(f"research run not found: {run_id}")
    if source_owner is not None and run.source_owner not in {None, source_owner}:
        raise ResearchRunCheckpointError(f"checkpoint belongs to source owner {run.source_owner!r}, not {source_owner!r}")
    terminal = run.status == "completed" or run.stage == "completed"
    report = run.payload.get("report") if isinstance(run.payload, Mapping) else None
    return run, {
        "next_stage": next_resume_stage(run),
        "missing_gap_ids": tuple(run.open_gap_ids) if not terminal else (),
        "provider_call_ids": recorded_provider_call_ids(run),
        "evidence_ids": recorded_evidence_ids(run),
        "source_revision": run.source_revision,
        "source_owner": run.source_owner,
        "terminal": terminal,
        "partial_abstention": bool(run.payload.get("partial_abstention")) if isinstance(run.payload, Mapping) else False,
        "report": report,
        "conflicts": tuple(run.conflicts),
    }


def refresh_research_run_payload(store: ResearchRunStore, run_id: str, payload_patch: Mapping[str, Any]) -> ResearchRun:
    current = store.load(run_id)
    if current is None:
        raise FileNotFoundError(f"research run not found: {run_id}")
    merged_payload = dict(current.payload)
    merged_payload.update(dict(payload_patch))
    updated = ResearchRun(
        run_id=current.run_id, query=current.query, stage=current.stage,
        checkpoint_seq=current.checkpoint_seq, status=current.status,
        created_at=current.created_at, updated_at=time.time(), schema_version=current.schema_version,
        replay_source_run_id=current.replay_source_run_id, source_revision=current.source_revision,
        source_owner=current.source_owner, source_ids=current.source_ids, evidence_ids=current.evidence_ids,
        evidence_summary=current.evidence_summary, coverage_state=current.coverage_state,
        open_gap_ids=current.open_gap_ids, conflicts=current.conflicts,
        stage_history=current.stage_history, budgets=current.budgets, payload=merged_payload,
    )
    store.save(updated)
    return updated
