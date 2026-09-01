from __future__ import annotations

import re
import time
from contextvars import ContextVar
from typing import Any, Dict, List, Optional

_EVENTS: ContextVar[Optional[List[Dict[str, Any]]]] = ContextVar("deep_research_provider_events", default=None)


def reset_provider_events() -> None:
    _EVENTS.set([])


def _events() -> List[Dict[str, Any]]:
    current = _EVENTS.get()
    if current is None:
        current = []
        _EVENTS.set(current)
    return current


def classify_provider_error(exc: BaseException) -> str:
    name = type(exc).__name__.lower()
    message = str(exc).lower()
    if "rate" in name or "rate limit" in message or "429" in message:
        return "rate_limit"
    if "auth" in name or "invalid api key" in message or "401" in message:
        return "auth"
    if "timeout" in name or "timed out" in message:
        return "timeout"
    if "json" in name or "validation" in name or "malformed" in message:
        return "malformed_response"
    if "connection" in name or "transport" in name or "network" in message:
        return "transport"
    return "provider_error"


def record_provider_event(*, operation: str, status: str, latency_seconds: float, model: Optional[str] = None, error_class: Optional[str] = None) -> None:
    _events().append({
        "operation": operation,
        "status": status,
        "latency_seconds": round(float(latency_seconds), 4),
        "model": model,
        "error_class": error_class,
        "recorded_at": time.time(),
    })


def provider_events_snapshot() -> List[Dict[str, Any]]:
    return [dict(item) for item in _events()]
