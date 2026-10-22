from reasoners.deep_research_ext.runtime_provider import resolve_runtime_provider
from pathlib import Path


COMPOSE_FILE = Path(__file__).parents[1] / "docker-compose.yml"
ENV_EXAMPLE_FILE = Path(__file__).parents[1] / ".env.example"


def _active_env_example() -> dict[str, str]:
    environment = {}
    for line in ENV_EXAMPLE_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, value = line.split("=", 1)
        environment[name] = value
    return environment


def test_windows_defaults_use_local_opencodex_and_luna():
    result = resolve_runtime_provider({}, platform="win32")
    assert result.provider == "opencodex"
    assert result.model == "openai/gpt-5.6-luna"
    assert result.api_base == "http://127.0.0.1:10109/v1"
    assert result.reasoning_effort == "low"


def test_unix_defaults_use_fcm_fast_coding():
    result = resolve_runtime_provider({}, platform="linux")
    assert result.provider == "fcm"
    assert result.model == "openai/fcm:fast-coding"
    assert result.api_base is None
    assert result.reasoning_effort is None


def test_copied_env_example_preserves_platform_defaults():
    environment = _active_env_example()

    windows = resolve_runtime_provider(environment, platform="win32")
    unix = resolve_runtime_provider(environment, platform="linux")

    assert "DEFAULT_MODEL" not in environment
    assert windows.provider == "opencodex"
    assert windows.model == "openai/gpt-5.6-luna"
    assert unix.provider == "fcm"
    assert unix.model == "openai/fcm:fast-coding"


def test_unix_fcm_uses_canonical_broker_environment():
    result = resolve_runtime_provider(
        {
            "LLM_BROKER_BASE_URL": "http://127.0.0.1:29280/v1",
            "LLM_BROKER_API_KEY": "broker-key",
        },
        platform="linux",
    )
    assert result.api_base == "http://127.0.0.1:29280/v1"
    assert result.api_key == "broker-key"


def test_windows_broker_override_uses_launcher_managed_route():
    result = resolve_runtime_provider(
        {
            "LLM_BROKER_BASE_URL": "http://127.0.0.1:10110/v1",
            "LLM_BROKER_API_KEY": "broker-key",
        },
        platform="win32",
    )
    assert result.provider == "broker"
    assert result.model == "openai/gpt-5.6-luna"
    assert result.api_base == "http://127.0.0.1:10110/v1"
    assert result.api_key == "broker-key"
    assert result.reasoning_effort == "low"


def test_compose_leaves_model_unset_and_passes_broker_environment():
    compose = COMPOSE_FILE.read_text(encoding="utf-8")
    assert "DEFAULT_MODEL=${DEFAULT_MODEL:-}" in compose
    assert "LLM_BROKER_BASE_URL=${LLM_BROKER_BASE_URL:-}" in compose
    assert "LLM_BROKER_API_KEY=${LLM_BROKER_API_KEY:-}" in compose


def test_agentfield_entrypoint_preserves_assigned_registration_port():
    compose = COMPOSE_FILE.read_text(encoding="utf-8")
    main = (COMPOSE_FILE.parent / "main.py").read_text(encoding="utf-8")
    env_example = ENV_EXAMPLE_FILE.read_text(encoding="utf-8")
    assert "AGENTFIELD_STRICT_PORT=${AGENTFIELD_STRICT_PORT:-1}" in compose
    assert 'app.serve(host="0.0.0.0", auto_port=False, ws="websockets")' in main
    assert "AGENTFIELD_STRICT_PORT=1" in env_example


def test_explicit_model_and_provider_endpoint_override_platform_defaults():
    result = resolve_runtime_provider(
        {"DEFAULT_MODEL": "custom/model", "PROVIDER_BASE_URL": "https://provider.example/v1", "OPENAI_API_KEY": "key"},
        platform="win32",
    )
    assert result.model == "custom/model"
    assert result.api_base == "https://provider.example/v1"
    assert result.api_key == "key"
    assert result.provider == "configured"


def test_explicit_ollama_endpoint_wins_and_supports_ollama_model():
    result = resolve_runtime_provider(
        {"OLLAMA_BASE_URL": "http://ollama.example", "OLLAMA_MODEL": "qwen2.5"},
        platform="linux",
    )
    assert result.provider == "ollama"
    assert result.api_base == "http://ollama.example"
    assert result.model == "ollama/qwen2.5"


def test_explicit_model_also_applies_to_ollama_without_rewriting_it():
    result = resolve_runtime_provider(
        {"OLLAMA_BASE_URL": "http://ollama.example", "DEFAULT_MODEL": "ollama/custom"},
        platform="win32",
    )
    assert result.model == "ollama/custom"
