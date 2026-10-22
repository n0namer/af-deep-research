"""Guard native Deep Research inference transport: OpenCodex Responses, not Chat Completions."""
import asyncio

import pytest
from aiohttp import web
from pydantic import BaseModel

from reasoners.deep_research_ext.opencodex_responses import call_opencodex_responses


class Fact(BaseModel):
    fact_id: str
    source_id: int


@pytest.mark.asyncio
async def test_calls_opencodex_responses_and_validates_model():
    seen = []

    async def handle(request):
        body = await request.json()
        seen.append((request.path, body))
        return web.json_response({
            "status": "completed",
            "output": [{"type": "message", "content": [
                {"type": "output_text", "text": '{"fact_id":"f1","source_id":9}'}
            ]}],
        })

    app = web.Application()
    app.router.add_post("/v1/responses", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "127.0.0.1", 0)
    await site.start()
    try:
        port = site._server.sockets[0].getsockname()[1]
        value = await call_opencodex_responses(
            base_url=f"http://127.0.0.1:{port}/v1",
            model="gpt-6-luna", system="Verify facts.", user="One fact",
            schema=Fact, timeout_seconds=8,
        )
        assert value == Fact(fact_id="f1", source_id=9)
        assert seen[0][0] == "/v1/responses"
        assert seen[0][1]["text"]["format"]["type"] == "json_schema"
        assert seen[0][1]["model"] == "gpt-6-luna"
    finally:
        await runner.cleanup()


@pytest.mark.asyncio
async def test_rejects_missing_required_source_identity():
    async def handle(request):
        return web.json_response({
            "status": "completed",
            "output": [{"type": "message", "content": [
                {"type": "output_text", "text": '{"fact_id":"f1"}'}
            ]}],
        })

    app = web.Application()
    app.router.add_post("/v1/responses", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "127.0.0.1", 0)
    await site.start()
    try:
        port = site._server.sockets[0].getsockname()[1]
        with pytest.raises(Exception, match="source_id"):
            await call_opencodex_responses(
                base_url=f"http://127.0.0.1:{port}/v1",
                model="gpt-6-luna", user="One fact", schema=Fact, timeout_seconds=8,
            )
    finally:
        await runner.cleanup()
