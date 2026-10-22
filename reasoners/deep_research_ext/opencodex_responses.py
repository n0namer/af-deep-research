"""OpenCodex Responses API transport for AF Deep Research structured AI calls.

Keeps the native AgentField orchestration unchanged.  Used only when
DR_LLM_TRANSPORT=opencodex; fail closed on HTTP and schema errors.
"""
import os

import aiohttp


async def call_opencodex_responses(
    *,
    user: str,
    schema=None,
    system: str | None = None,
    model: str | None = None,
    base_url: str | None = None,
    timeout_seconds: float = 180,
    max_tokens: int = 8192,
):
    if not isinstance(user, str) or not user.strip():
        raise ValueError("OpenCodex response requires a nonempty user prompt")
    endpoint = (base_url or os.getenv("DR_OPENCODEX_BASE_URL") or "http://127.0.0.1:10110/v1").rstrip("/") + "/responses"
    resolved_model = str(model or os.getenv("DEFAULT_MODEL") or "gpt-6-luna")
    if resolved_model.startswith("openai/"):
        resolved_model = resolved_model[len("openai/"):]
    inputs = []
    if system:
        inputs.append({"role": "system", "content": [{"type": "input_text", "text": system}]})
    inputs.append({"role": "user", "content": [{"type": "input_text", "text": user}]})
    body = {
        "model": resolved_model,
        "input": inputs,
        "max_output_tokens": max(32, int(max_tokens)),
        "stream": False,
    }
    if schema is not None:
        if not hasattr(schema, "model_json_schema"):
            raise TypeError("OpenCodex structured output requires a Pydantic model")
        body["text"] = {"format": {
            "type": "json_schema",
            "name": schema.__name__,
            "schema": schema.model_json_schema(),
            "strict": False,
        }}
    timeout = aiohttp.ClientTimeout(total=float(timeout_seconds))
    async with aiohttp.ClientSession(timeout=timeout, trust_env=False) as client:
        async with client.post(endpoint, json=body) as response:
            if response.status != 200:
                # Never log credentials or the source contents.
                raise RuntimeError(f"OpenCodex Responses returned HTTP {response.status}")
            payload = await response.json()
    if payload.get("status") != "completed":
        raise RuntimeError(f"OpenCodex Responses did not complete: {payload.get('status')}")
    chunks = [
        part.get("text", "")
        for item in payload.get("output", [])
        for part in item.get("content", [])
        if part.get("type") == "output_text"
    ]
    content = "".join(chunks).strip()
    if not content:
        raise RuntimeError("OpenCodex Responses returned no output_text")
    if schema is not None:
        return schema.model_validate_json(content)
    return content
