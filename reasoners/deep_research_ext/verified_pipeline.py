import asyncio
import copy
import hashlib
import re
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Awaitable, Callable, Dict, Optional


class VerifiedSourceReportError(ValueError):
    """Raised when a verified-source report cannot be accepted safely."""


_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True)
class GroundedFact:
    fact_id: str
    source_id: str
    source_sha256: str

    def __post_init__(self):
        for field_name, value in (("fact_id", self.fact_id), ("source_id", self.source_id)):
            if not isinstance(value, str) or not value.strip():
                raise VerifiedSourceReportError(f"{field_name} must be a non-empty string")
        if not isinstance(self.source_sha256, str) or not _SHA256_RE.fullmatch(self.source_sha256):
            raise VerifiedSourceReportError("source_sha256 must be a lowercase SHA-256 hex digest")


@dataclass(frozen=True)
class VerifiedSourceReport:
    report_id: str
    query: str
    source_ids: tuple[str, ...]
    revision: int
    payload: dict[str, Any]
    source_revision: str = "legacy"
    source_owner: str = "legacy"
    source_file_sha256: str = ""
    facts: tuple[GroundedFact, ...] = ()
    abstained_requirement_ids: tuple[str, ...] = ()
    dto_version: str = "r10"

    def __post_init__(self):
        if not isinstance(self.report_id, str) or not self.report_id.strip():
            raise VerifiedSourceReportError("report_id must be a non-empty string")
        if not isinstance(self.query, str) or not self.query.strip():
            raise VerifiedSourceReportError("query must be a non-empty string")
        if isinstance(self.revision, bool) or not isinstance(self.revision, int) or self.revision < 1:
            raise VerifiedSourceReportError("revision must be a positive integer")
        if not self.source_ids or any(not isinstance(item, str) or not item.strip() for item in self.source_ids):
            raise VerifiedSourceReportError("source_ids must contain non-empty strings")
        if len(set(self.source_ids)) != len(self.source_ids):
            raise VerifiedSourceReportError("source_ids must be unique")
        if not isinstance(self.payload, dict):
            raise VerifiedSourceReportError("payload must be a mapping")
        if not isinstance(self.source_revision, str) or not self.source_revision.strip():
            raise VerifiedSourceReportError("source_revision must be a non-empty string")
        if not isinstance(self.source_owner, str) or not self.source_owner.strip():
            raise VerifiedSourceReportError("source_owner must be a non-empty string")
        if self.source_file_sha256 and not _SHA256_RE.fullmatch(self.source_file_sha256):
            raise VerifiedSourceReportError("source_file_sha256 must be a lowercase SHA-256 hex digest")
        if len({fact.fact_id for fact in self.facts}) != len(self.facts):
            raise VerifiedSourceReportError("facts must have unique fact_id values")
        if any(fact.source_id not in self.source_ids for fact in self.facts):
            raise VerifiedSourceReportError("facts must reference declared source_ids")
        if len(set(self.abstained_requirement_ids)) != len(self.abstained_requirement_ids):
            raise VerifiedSourceReportError("abstained_requirement_ids must be unique")
        if self.dto_version != "r10":
            raise VerifiedSourceReportError("unsupported DTO version")


def _clone_report(report):
    return copy.deepcopy(report)


def source_file_sha256(path):
    """Return the immutable SHA-256 identity of a source file."""
    digest = hashlib.sha256()
    try:
        with Path(path).open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as exc:
        raise VerifiedSourceReportError("source file cannot be hashed") from exc
    return digest.hexdigest()


def build_verified_source_report(*, report_id, query, source_ids, revision, payload):
    """Construct and validate the exact DTO used at the persistence boundary."""
    if not isinstance(source_ids, (list, tuple)):
        raise VerifiedSourceReportError("source_ids must be a list or tuple")
    return VerifiedSourceReport(
        report_id=report_id,
        query=query,
        source_ids=tuple(source_ids),
        revision=revision,
        payload=copy.deepcopy(payload) if isinstance(payload, dict) else payload,
    )


def build_grounded_verified_report(*, report_id, query, source_revision, source_owner,
                                   source_file_sha256, facts, payload,
                                   abstained_requirement_ids=(), revision=1):
    """Build the r10 source-bound DTO without invoking an external provider."""
    if not isinstance(facts, (list, tuple)) or not facts:
        raise VerifiedSourceReportError("facts must be a non-empty list or tuple")
    if not isinstance(source_file_sha256, str) or not _SHA256_RE.fullmatch(source_file_sha256):
        raise VerifiedSourceReportError("source_file_sha256 must be a lowercase SHA-256 hex digest")
    normalized_facts = []
    for fact in facts:
        if isinstance(fact, GroundedFact):
            normalized_facts.append(fact)
        elif isinstance(fact, dict):
            normalized_facts.append(GroundedFact(**fact))
        else:
            raise VerifiedSourceReportError("facts must contain GroundedFact values or mappings")
    normalized_facts = tuple(normalized_facts)
    source_ids = tuple(dict.fromkeys(fact.source_id for fact in normalized_facts))
    return VerifiedSourceReport(
        report_id=report_id,
        query=query,
        source_ids=source_ids,
        revision=revision,
        payload=copy.deepcopy(payload) if isinstance(payload, dict) else payload,
        source_revision=source_revision,
        source_owner=source_owner,
        source_file_sha256=source_file_sha256,
        facts=normalized_facts,
        abstained_requirement_ids=tuple(abstained_requirement_ids),
    )


def replay_verified_source_report(existing, candidate):
    """Apply a monotonic, idempotent revision without duplicating a terminal effect."""
    if not isinstance(candidate, VerifiedSourceReport):
        raise VerifiedSourceReportError("candidate must be a VerifiedSourceReport")
    if existing is None:
        return candidate, True
    if not isinstance(existing, VerifiedSourceReport):
        raise VerifiedSourceReportError("stored report has an invalid type")
    existing_identity = (
        existing.report_id, existing.query, existing.source_ids, existing.source_revision,
        existing.source_owner, existing.source_file_sha256, existing.facts,
        existing.abstained_requirement_ids, existing.dto_version,
    )
    candidate_identity = (
        candidate.report_id, candidate.query, candidate.source_ids, candidate.source_revision,
        candidate.source_owner, candidate.source_file_sha256, candidate.facts,
        candidate.abstained_requirement_ids, candidate.dto_version,
    )
    if existing.source_owner != candidate.source_owner:
        raise VerifiedSourceReportError("report owner does not match stored report owner")
    if existing_identity != candidate_identity:
        raise VerifiedSourceReportError("report identity does not match stored report")
    if candidate.revision < existing.revision:
        return existing, False
    if candidate.revision == existing.revision:
        if candidate.payload != existing.payload:
            raise VerifiedSourceReportError("revision payload conflicts with stored report")
        return existing, False
    if candidate.revision != existing.revision + 1:
        raise VerifiedSourceReportError("report revision must advance by one")
    return candidate, True


def persist_verified_source_report(store, candidate):
    """Persist once per accepted revision and return the canonical stored DTO."""
    if not isinstance(candidate, VerifiedSourceReport):
        raise VerifiedSourceReportError("candidate must be a VerifiedSourceReport")
    if hasattr(store, "load"):
        existing = store.load(candidate.report_id)
    elif hasattr(store, "get"):
        existing = store.get(candidate.report_id)
    else:
        raise VerifiedSourceReportError("store must provide load() or get()")
    canonical, changed = replay_verified_source_report(existing, candidate)
    if not changed:
        return canonical
    if hasattr(store, "save"):
        store.save(canonical)
    elif hasattr(store, "set"):
        store.set(canonical.report_id, canonical)
    else:
        raise VerifiedSourceReportError("store must provide save() or set()")
    return canonical


class DurableVerifiedSourceReportStore:
    """Small durable-boundary adapter with owner and effect fencing."""

    def __init__(self):
        self._reports = {}
        self._effects = set()
        self._lock = threading.RLock()

    def load(self, report_id):
        with self._lock:
            report = self._reports.get(report_id)
            return _clone_report(report) if report is not None else None

    def save(self, report, *, owner=None, expected_revision=None):
        with self._lock:
            existing = self._reports.get(report.report_id)
            if owner is not None and owner != report.source_owner:
                raise VerifiedSourceReportError("source owner does not match report owner")
            if existing is not None and existing.source_owner != report.source_owner:
                raise VerifiedSourceReportError("source owner does not match stored report")
            if expected_revision is not None and (existing is None or existing.revision != expected_revision):
                raise VerifiedSourceReportError("stored report revision is stale")
            self._reports[report.report_id] = _clone_report(report)
            return _clone_report(report)

    def record_effect(self, effect_id, *, report_id, owner, revision):
        if not isinstance(effect_id, str) or not effect_id.strip():
            raise VerifiedSourceReportError("effect_id must be a non-empty string")
        with self._lock:
            report = self._reports.get(report_id)
            if report is None:
                raise VerifiedSourceReportError("report must be persisted before recording an effect")
            if report.source_owner != owner:
                raise VerifiedSourceReportError("source owner does not match stored report")
            if report.revision != revision:
                raise VerifiedSourceReportError("effect revision is stale")
            if effect_id in self._effects:
                return False
            self._effects.add(effect_id)
            return True

    def effect_count(self):
        with self._lock:
            return len(self._effects)


def _validate_grounded_document_payload(candidate):
    """Reject unsupported or foreign evidence before persisting a grounded document."""
    payload = candidate.payload
    # Older, still supported r10 receipts contain document+claims instead of
    # the later document+citations+evidence envelope. Normalize both to one
    # exact owned-fact validation path, without trusting caller-supplied IDs.
    if "document" in payload and "claims" in payload and "citations" not in payload and "evidence" not in payload:
        claims = payload["claims"]
        if not isinstance(claims, list) or not claims:
            raise VerifiedSourceReportError("document requires owned claims")
        derived_evidence = []
        derived_citations = []
        for claim in claims:
            if not isinstance(claim, dict) or not isinstance(claim.get("text"), str):
                raise VerifiedSourceReportError("invalid document claim")
            derived_evidence.append({
                "fact_id": claim.get("fact_id"),
                "source_id": claim.get("source_id"),
                "text": claim["text"],
                "source_sha256": hashlib.sha256(claim["text"].encode("utf-8")).hexdigest(),
            })
            derived_citations.append({"fact_id": claim.get("fact_id"), "source_id": claim.get("source_id")})
        payload = {**payload, "citations": derived_citations, "evidence": derived_evidence}
    fields = {"document", "citations", "evidence"}
    if not {"document", "evidence"}.intersection(payload):
        return
    if not fields.issubset(payload):
        raise VerifiedSourceReportError("document requires citations and evidence")
    document = payload["document"]
    citations, evidence = payload["citations"], payload["evidence"]
    if not isinstance(document, str) or not document.strip():
        raise VerifiedSourceReportError("invalid document text")
    if not isinstance(citations, list) or not isinstance(evidence, list) or not citations or not evidence:
        raise VerifiedSourceReportError("missing document citations or evidence")
    owned = {(f.fact_id, f.source_id): f.source_sha256 for f in candidate.facts}
    eligible = {}
    for item in evidence:
        if not isinstance(item, dict):
            raise VerifiedSourceReportError("invalid evidence item")
        key = (item.get("fact_id"), item.get("source_id"))
        content = item.get("text")
        digest = item.get("source_sha256")
        if key not in owned or not isinstance(content, str) or not content.strip():
            raise VerifiedSourceReportError("unowned or empty evidence")
        if digest != owned[key] or hashlib.sha256(content.encode("utf-8")).hexdigest() != digest:
            raise VerifiedSourceReportError("evidence hash mismatch")
        if key in eligible:
            raise VerifiedSourceReportError("duplicate evidence identity")
        eligible[key] = content
    cited = set()
    for citation in citations:
        if not isinstance(citation, dict):
            raise VerifiedSourceReportError("invalid citation")
        key = (citation.get("fact_id"), citation.get("source_id"))
        if key not in eligible:
            raise VerifiedSourceReportError("citation references foreign source or fact")
        cited.add(key)
    markers = re.findall(r"\[([^\]]+)\]", document)
    if any(source not in {s for _, s in cited} for source in markers):
        raise VerifiedSourceReportError("document references foreign source")
    documented = " ".join(re.sub(r"\[[^\]]+\]", "", document).split())
    evidence_text = " ".join(" ".join(text.split()) for key, text in eligible.items() if key in cited)
    if documented != evidence_text:
        raise VerifiedSourceReportError("document asserts unsupported material")


def persist_grounded_verified_report(store, candidate, *, owner, cancellation=None, effect_id=None):
    """Persist a grounded report exactly once, then optionally fence one terminal effect."""
    if not isinstance(candidate, VerifiedSourceReport) or not candidate.facts:
        raise VerifiedSourceReportError("candidate must be a grounded VerifiedSourceReport")
    if owner != candidate.source_owner:
        raise VerifiedSourceReportError("source owner does not match report owner")
    _validate_grounded_document_payload(candidate)
    _raise_if_cancelled(cancellation)
    existing = store.load(candidate.report_id)
    canonical, changed = replay_verified_source_report(existing, candidate)
    if changed:
        if isinstance(store, DurableVerifiedSourceReportStore):
            canonical = store.save(canonical, owner=owner, expected_revision=existing.revision if existing else None)
        elif hasattr(store, "save"):
            store.save(_clone_report(canonical))
        else:
            raise VerifiedSourceReportError("store must provide save()")
    _raise_if_cancelled(cancellation)
    effect_applied = None
    if effect_id is not None:
        if not isinstance(store, DurableVerifiedSourceReportStore):
            raise VerifiedSourceReportError("effect fencing requires DurableVerifiedSourceReportStore")
        effect_applied = store.record_effect(
            effect_id, report_id=canonical.report_id, owner=owner, revision=canonical.revision,
        )
    return canonical, changed, effect_applied


def resume_grounded_verified_report(store, report_id, *, owner, source_file_sha256):
    """Reload a report only when owner and immutable source identity still match."""
    report = store.load(report_id)
    if report is None:
        raise VerifiedSourceReportError("grounded report was not found")
    if report.source_owner != owner:
        raise VerifiedSourceReportError("source owner does not match stored report")
    if report.source_file_sha256 != source_file_sha256:
        raise VerifiedSourceReportError("source file SHA does not match stored report")
    return report


def _is_cancelled(cancellation):
    if cancellation is None:
        return False
    if callable(cancellation):
        return bool(cancellation())
    if hasattr(cancellation, "is_set"):
        return bool(cancellation.is_set())
    return bool(cancellation)


def _raise_if_cancelled(cancellation):
    if _is_cancelled(cancellation):
        raise asyncio.CancelledError("verified source report cancelled")

from .coverage import assess_candidate_coverage
from .evidence_ledger import build_evidence_ledger
from .evaluation import count_prompt_injection_success, count_source_reference_integrity_failures
from .final_verifier import verify_final_document
from .gap_research import run_gap_research_round, unresolved_requirement_ids
from .models import ExtensionTrace
from .requirement_mapping import map_claims_to_requirements
from .research_run import begin_research_run, checkpoint_research_run
from .provider_telemetry import provider_events_snapshot
from .stopping import assess_stopping
from .synthesis_guard import build_evidence_only_gap_response, requires_programmatic_abstention
from .verification_bridge import verify_ledger_claims


def _semantic_snapshot(
    coverage,
    final_verification=None,
    *,
    ledger=None,
    contract=None,
    delivered_contradiction_ids=(),
    delivered_premise_challenge_ids=(),
    document_package=None,
    research_package=None,
    evidence_only_delivery=False,
):
    disputed_requirement_ids = set()
    if ledger is not None:
        disputed_requirement_ids = {
            requirement_id
            for claim in ledger.claims
            if claim.status == "disputed" and claim.support_state == "source_entailed"
            for requirement_id in claim.requirement_ids
        }
    requirement_states = {
        item.requirement_id: (
            "contradicted" if item.requirement_id in disputed_requirement_ids
            else ("supported" if item.status == "verified" else "unresolved")
        )
        for item in coverage.requirements
    }
    premise_requirement_ids = set()
    if contract is not None:
        premise_requirement_ids = {
            item.requirement_id for item in contract.requirements
            if getattr(item, "role", "answer") == "premise_check"
        }
    contradicted_premise_ids = premise_requirement_ids.intersection(disputed_requirement_ids)
    snapshot = {
        "requirement_states": requirement_states,
        "unsupported_material_claims": None,
        "fabricated_artifacts": None,
        "citation_entailment_ratio": None,
        "silent_contradiction_loss": (
            len(disputed_requirement_ids - set(delivered_contradiction_ids))
            if ledger is not None else None
        ),
        "false_premise_adoption": (
            len(contradicted_premise_ids - set(delivered_premise_challenge_ids))
            if contract is not None and ledger is not None else None
        ),
        "prompt_injection_success": None,
    }
    if document_package is not None and research_package is not None:
        snapshot["fabricated_artifacts"] = count_source_reference_integrity_failures(document_package, research_package)
        snapshot["prompt_injection_success"] = count_prompt_injection_success(document_package, research_package)
    if evidence_only_delivery:
        snapshot["unsupported_material_claims"] = 0
        snapshot["citation_entailment_ratio"] = 1.0
    elif final_verification is not None:
        unsupported = len(final_verification.unsupported_claims)
        total = int(final_verification.material_claim_count or 0)
        supported = int(final_verification.supported_claim_count or 0)
        snapshot["unsupported_material_claims"] = unsupported
        snapshot["citation_entailment_ratio"] = 1.0 if total == 0 else round(supported / total, 6)
    return snapshot


async def execute_verified_pipeline(
    *,
    trace: ExtensionTrace,
    prepare_research_package: Callable[..., Awaitable[Any]],
    generate_document_from_package: Callable[..., Awaitable[Any]],
    stream_executor: Optional[Callable[..., Awaitable[Any]]] = None,
    upstream_kwargs: Dict[str, Any],
    ai_call=None,
    run_store=None,
    research_run=None,
    cancellation=None,
    report_store=None,
    report_id=None,
    report_revision=1,
) -> Any:
    started = time.time()
    _raise_if_cancelled(cancellation)
    if run_store is None or research_run is None:
        run_store, research_run = begin_research_run(upstream_kwargs["query"])
    _raise_if_cancelled(cancellation)
    cached_package = research_run.payload.get("research_package") if research_run.stage != "started" else None
    if isinstance(cached_package, dict):
        package = dict(cached_package)
        research_phase_metadata = dict(research_run.payload.get("research_phase_metadata") or {})
        research_phase_metadata["resumed_from_checkpoint"] = True
        research_phase_metadata["research_run_id"] = research_run.run_id
    else:
        research = await prepare_research_package(
            query=upstream_kwargs["query"],
            mode=upstream_kwargs["mode"],
            research_focus=upstream_kwargs["research_focus"],
            research_scope=upstream_kwargs["research_scope"],
            max_research_loops=upstream_kwargs["max_research_loops"],
            num_parallel_streams=upstream_kwargs["num_parallel_streams"],
            source_strictness=upstream_kwargs["source_strictness"],
            model=upstream_kwargs.get("model"),
            api_key=upstream_kwargs.get("api_key"),
        )
        package = dict(research.research_package)
        research_phase_metadata = dict(getattr(research, "metadata", {}) or {})
        source_ids = tuple(str(item.get("id")) for item in package.get("source_articles", []) if item.get("id") is not None)
        research_run = checkpoint_research_run(
            run_store, research_run, stage="research_package_ready", source_ids=source_ids,
            payload={"research_package": package, "research_phase_metadata": research_phase_metadata, "provider_events": provider_events_snapshot()},
        )
    _raise_if_cancelled(cancellation)
    ledger = build_evidence_ledger(package, [])
    ledger = await map_claims_to_requirements(
        ledger=ledger,
        contract=trace.answer_contract,
        ai_call=ai_call,
        model=upstream_kwargs.get("model"),
        api_key=upstream_kwargs.get("api_key"),
    )
    _raise_if_cancelled(cancellation)
    ledger = await verify_ledger_claims(
        ledger=ledger,
        research_package=package,
        source_strictness=upstream_kwargs["source_strictness"],
        model=upstream_kwargs.get("model"),
        api_key=upstream_kwargs.get("api_key"),
        ai_call=ai_call,
    )
    coverage = assess_candidate_coverage(trace.answer_contract, ledger)
    gap_round_traces = []
    max_gap_rounds = max(0, int(upstream_kwargs.get("max_gap_rounds", 0) or 0))
    if stream_executor is not None and max_gap_rounds > 0 and coverage.verified_coverage_ratio < 1.0:
        for _ in range(max_gap_rounds):
            package, ledger, gap_trace = await run_gap_research_round(
                contract=trace.answer_contract,
                coverage=coverage,
                ledger=ledger,
                research_package=package,
                stream_executor=stream_executor,
                ai_call=ai_call,
                source_strictness=upstream_kwargs["source_strictness"],
                model=upstream_kwargs.get("model"),
                api_key=upstream_kwargs.get("api_key"),
            )
            gap_round_traces.append(gap_trace)
            coverage = assess_candidate_coverage(trace.answer_contract, ledger)
            if coverage.verified_coverage_ratio >= 1.0 or gap_trace.novelty_exhausted:
                break

    stopping = assess_stopping(
        coverage,
        novelty_evaluated=bool(gap_round_traces),
        novelty_exhausted=bool(gap_round_traces and gap_round_traces[-1].novelty_exhausted),
    )
    ext = trace.model_dump()
    ext["mode"] = "verified_phase_checkpoint"
    ext["evidence_ledger_summary"] = ledger.summary()
    ext["coverage_state"] = coverage.model_dump()
    ext["stopping_assessment"] = stopping.model_dump()
    ext["gap_rounds"] = [item.model_dump() for item in gap_round_traces]
    research_run = checkpoint_research_run(
        run_store, research_run, stage="evidence_verified",
        evidence_summary=ledger.summary(), coverage_state=coverage.model_dump(),
        open_gap_ids=tuple(unresolved_requirement_ids(coverage)),
        payload={"research_package": package, "research_phase_metadata": research_phase_metadata},
    )
    base_metadata = {
        "total_orchestration_time_seconds": round(time.time() - started, 2),
        "research_phase_metadata": research_phase_metadata,
                "provider_events": provider_events_snapshot(),
        "research_run": {"run_id": research_run.run_id, "checkpoint_seq": research_run.checkpoint_seq, "stage": research_run.stage},
        "verified_research_extension": ext,
    }

    if requires_programmatic_abstention(upstream_kwargs["source_strictness"], coverage):
        ext["mode"] = "programmatic_partial_abstention"
        preview_response = build_evidence_only_gap_response(
            contract=trace.answer_contract, ledger=ledger, coverage=coverage, metadata=base_metadata,
        )
        research_run = checkpoint_research_run(
            run_store, research_run, stage="completed", status="completed",
            evidence_summary=ledger.summary(), coverage_state=coverage.model_dump(),
            open_gap_ids=tuple(unresolved_requirement_ids(coverage)),
            payload={
                "research_package": package,
                "research_phase_metadata": research_phase_metadata,
                "provider_events": provider_events_snapshot(),
                "terminal_mode": ext["mode"],
                "semantic_snapshot": _semantic_snapshot(
                    coverage, ledger=ledger, contract=trace.answer_contract,
                    delivered_contradiction_ids=(
                        (base_metadata.get("verified_research_extension") or {}).get("contradictions", {}).get("requirement_ids", [])
                    ),
                    delivered_premise_challenge_ids=(
                        (base_metadata.get("verified_research_extension") or {}).get("premise_checks", {}).get("challenged_requirement_ids", [])
                    ),
                    document_package=preview_response.research_package, research_package=package,
                    evidence_only_delivery=True,
                ),
            },
        )
        base_metadata["research_run"] = {"run_id": research_run.run_id, "checkpoint_seq": research_run.checkpoint_seq, "stage": research_run.stage}
        return build_evidence_only_gap_response(
            contract=trace.answer_contract, ledger=ledger, coverage=coverage, metadata=base_metadata,
        )

    _raise_if_cancelled(cancellation)
    document = await generate_document_from_package(
        package=package,
        main_query=upstream_kwargs["query"],
        tension_lens=upstream_kwargs["tension_lens"],
        source_strictness=upstream_kwargs["source_strictness"],
        evidence_style=upstream_kwargs["evidence_style"],
        analysis_depth=upstream_kwargs["analysis_depth"],
        model=upstream_kwargs.get("model"),
        api_key=upstream_kwargs.get("api_key"),
    )
    metadata = dict(getattr(document, "metadata", {}) or {})
    metadata.update(base_metadata)
    research_run = checkpoint_research_run(
        run_store, research_run, stage="synthesis_ready",
        evidence_summary=ledger.summary(), coverage_state=coverage.model_dump(),
        open_gap_ids=tuple(unresolved_requirement_ids(coverage)),
        payload={
            "research_package": package,
            "research_phase_metadata": research_phase_metadata,
                "provider_events": provider_events_snapshot(),
            "document_package": getattr(document, "research_package", {}),
        },
    )
    metadata["research_run"] = {"run_id": research_run.run_id, "checkpoint_seq": research_run.checkpoint_seq, "stage": research_run.stage}

    _raise_if_cancelled(cancellation)
    final_verification = None
    if (upstream_kwargs["source_strictness"] or "").strip().lower() in {"strict", "verified-only", "verified_only"}:
        _raise_if_cancelled(cancellation)
        final_verification = await verify_final_document(
            document_package=document.research_package,
            research_package=package,
            source_strictness=upstream_kwargs["source_strictness"],
            ai_call=ai_call,
            model=upstream_kwargs.get("model"),
            api_key=upstream_kwargs.get("api_key"),
        )
        ext["final_verification"] = final_verification.model_dump()
        if not final_verification.passed:
            ext["mode"] = "post_generation_rejected"
            preview_response = build_evidence_only_gap_response(
                contract=trace.answer_contract, ledger=ledger, coverage=coverage, metadata=metadata,
            )
            research_run = checkpoint_research_run(
                run_store, research_run, stage="completed", status="completed",
                evidence_summary=ledger.summary(), coverage_state=coverage.model_dump(),
                open_gap_ids=tuple(unresolved_requirement_ids(coverage)),
                payload={
                    "research_package": package,
                    "research_phase_metadata": research_phase_metadata,
                "provider_events": provider_events_snapshot(),
                    "document_package": getattr(document, "research_package", {}),
                    "terminal_mode": ext["mode"],
                    "final_verification": final_verification.model_dump(),
                    "semantic_snapshot": _semantic_snapshot(
                        coverage, ledger=ledger, contract=trace.answer_contract,
                        delivered_contradiction_ids=(
                            (metadata.get("verified_research_extension") or {}).get("contradictions", {}).get("requirement_ids", [])
                        ),
                        delivered_premise_challenge_ids=(
                            (metadata.get("verified_research_extension") or {}).get("premise_checks", {}).get("challenged_requirement_ids", [])
                        ),
                        document_package=preview_response.research_package, research_package=package,
                        evidence_only_delivery=True,
                    ),
                },
            )
            metadata["research_run"] = {"run_id": research_run.run_id, "checkpoint_seq": research_run.checkpoint_seq, "stage": research_run.stage}
            return build_evidence_only_gap_response(
                contract=trace.answer_contract,
                ledger=ledger,
                coverage=coverage,
                metadata=metadata,
            )

    _raise_if_cancelled(cancellation)
    if report_store is not None:
        if not report_id:
            raise VerifiedSourceReportError("report_id is required when report_store is provided")
        source_ids = tuple(str(item.get("id")) for item in package.get("source_articles", []) if item.get("id") is not None)
        report = build_verified_source_report(
            report_id=report_id,
            query=upstream_kwargs["query"],
            source_ids=source_ids,
            revision=report_revision,
            payload={
                "document_package": getattr(document, "research_package", {}),
                "coverage_state": coverage.model_dump(),
                "final_verification": final_verification.model_dump() if final_verification is not None else None,
            },
        )
        persisted_report = persist_verified_source_report(report_store, report)
        metadata["verified_source_report"] = {
            "report_id": persisted_report.report_id,
            "revision": persisted_report.revision,
            "source_ids": list(persisted_report.source_ids),
        }

    research_run = checkpoint_research_run(
        run_store, research_run, stage="completed", status="completed",
        evidence_summary=ledger.summary(), coverage_state=coverage.model_dump(),
        open_gap_ids=tuple(unresolved_requirement_ids(coverage)),
        payload={
            "research_package": package,
            "research_phase_metadata": research_phase_metadata,
                "provider_events": provider_events_snapshot(),
            "document_package": getattr(document, "research_package", {}),
            "terminal_mode": "verified_document",
            "final_verification": final_verification.model_dump() if final_verification is not None else None,
            "semantic_snapshot": _semantic_snapshot(
                coverage, final_verification, ledger=ledger, contract=trace.answer_contract,
                document_package=getattr(document, "research_package", {}), research_package=package,
            ),
        },
    )
    metadata["research_run"] = {"run_id": research_run.run_id, "checkpoint_seq": research_run.checkpoint_seq, "stage": research_run.stage}
    if hasattr(document, "model_copy"):
        return document.model_copy(update={"metadata": metadata})
    document.metadata = metadata
    return document
