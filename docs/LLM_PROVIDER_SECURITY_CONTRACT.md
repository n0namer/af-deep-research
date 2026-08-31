# Deep Research — LLM Provider & Security Profile

Status: canonical repo-local provider profile
Cross-component contract: `n0namer/universal-solver:main/docs/architecture/llm-provider-security-contract.md`

## Role

Deep Research is the current reference implementation for the Gonka/OpenAI-compatible provider pattern used by the AgentField fleet.

## Proven configuration pattern

Runtime shape:

```text
DEFAULT_MODEL = openai/<Gonka model>
OPENAI_API_KEY = <Gonka secret from runtime secret store>
OPENAI_BASE_URL = <Gonka OpenAI-compatible endpoint>
```

Universal Solver currently supplies this shape for Deep Research through its permanent DEV/runtime topology.

## Evidence anchors

- `69974f184719dfb837f855106c14b95c452f8685` — dynamic model/key overrides preserve configured `api_base`.
- `2c02ffd41897b75566cba1070fc3d45589d00ce3` — OpenAI-compatible calls use first-class AI configuration with `OPENAI_API_KEY` and configured `api_base`.

These commits are the reference for the invariant that a key/model override MUST NOT discard the custom provider base URL.

## Security requirements

- Never commit or print Gonka/OpenAI-compatible secret values.
- Repository docs/examples record variable names and placeholders only.
- Runtime secret injection is owned by the deployment/secret-store plane.
- Provider fallbacks MUST NOT silently route a call to OpenRouter/Anthropic when Gonka is selected.
- Logs should prove provider/model/base identity without exposing credentials.
- `.env.example` is an example surface, not CURRENT runtime proof; if its defaults differ from deployment reality, deployment evidence wins and the example should be updated separately.

## Acceptance

A Deep Research provider-path change is accepted only when:

1. intended source/runtime identity is known;
2. configured model is in the intended OpenAI-compatible namespace;
3. `OPENAI_API_KEY` and `OPENAI_BASE_URL` survive dynamic/runtime overrides;
4. a real model call reaches the intended provider;
5. no unintended OpenRouter/Anthropic fallback appears in execution/log evidence;
6. a Deep Research canary returns a semantically valid result.

Process health or HTTP success alone is insufficient.

## Known documentation drift

`.env.example` currently presents OpenRouter-centric defaults while the permanent runtime uses the Gonka/OpenAI-compatible path. Treat this as documentation drift, not proof of the active provider. Any future cleanup should update the existing example in place rather than creating a parallel config document.
