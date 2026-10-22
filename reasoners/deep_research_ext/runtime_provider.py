"""Platform-aware defaults for the Deep Research LLM runtime."""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from typing import Mapping, Optional

OPENCODEX_BASE_URL = "http://127.0.0.1:10109/v1"
WINDOWS_MODEL = "openai/gpt-5.6-luna"
UNIX_MODEL = "openai/fcm:fast-coding"


@dataclass(frozen=True)
class RuntimeProvider:
    model: str
    api_key: Optional[str]
    api_base: Optional[str]
    provider: str
    reasoning_effort: Optional[str] = None


def _first(environment: Mapping[str, str], *names: str) -> Optional[str]:
    for name in names:
        value = environment.get(name)
        if value and value.strip():
            return value.strip()
    return None


def resolve_runtime_provider(
    environment: Optional[Mapping[str, str]] = None,
    platform: Optional[str] = None,
) -> RuntimeProvider:
    """Resolve provider settings; explicit settings override platform defaults."""
    env = os.environ if environment is None else environment
    host_platform = sys.platform if platform is None else platform
    explicit_model = _first(env, "DEFAULT_MODEL", "DR_MODEL", "MODEL")
    explicit_reasoning = _first(
        env,
        "DR_REASONING_EFFORT",
        "MODEL_REASONING_EFFORT",
        "OPENAI_REASONING_EFFORT",
    )
    api_key = _first(env, "OPENAI_API_KEY", "OPENROUTER_API_KEY", "API_KEY")

    ollama_base = _first(env, "OLLAMA_BASE_URL")
    if ollama_base:
        model = explicit_model or _first(env, "OLLAMA_MODEL") or "ollama/llama3.2"
        if model and not model.startswith("ollama/") and not explicit_model:
            model = f"ollama/{model}"
        return RuntimeProvider(model, api_key, ollama_base, "ollama", explicit_reasoning)

    explicit_base = _first(
        env,
        "PROVIDER_BASE_URL",
        "PROVIDER_ENDPOINT",
        "LLM_API_BASE",
        "OPENAI_BASE_URL",
        "OPENROUTER_BASE_URL",
    )
    if explicit_base:
        model = explicit_model or _first(env, "PROVIDER_MODEL") or "openrouter/deepseek/deepseek-chat-v3.1"
        return RuntimeProvider(model, api_key, explicit_base, "configured", explicit_reasoning)

    # The broker variables are the portable, launcher-managed route.  Check
    # them before applying the Windows development default so a local canary
    # can use its assigned in-memory credential without changing global auth.
    broker_base = _first(env, "LLM_BROKER_BASE_URL", "FCM_BASE_URL", "FCM_ENDPOINT")
    if broker_base:
        return RuntimeProvider(
            explicit_model or _first(env, "FCM_MODEL") or (WINDOWS_MODEL if host_platform.startswith("win") else UNIX_MODEL),
            _first(env, "LLM_BROKER_API_KEY") or api_key,
            broker_base,
            "broker",
            explicit_reasoning or ("low" if host_platform.startswith("win") else None),
        )

    if host_platform.startswith("win"):
        return RuntimeProvider(
            explicit_model or WINDOWS_MODEL,
            api_key,
            _first(env, "OPENCODEX_BASE_URL") or OPENCODEX_BASE_URL,
            "opencodex",
            explicit_reasoning or "low",
        )

    return RuntimeProvider(
        explicit_model or _first(env, "FCM_MODEL") or UNIX_MODEL,
        api_key,
        None,
        "fcm",
        explicit_reasoning,
    )
