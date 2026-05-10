import pytest
from httpx import ASGITransport, AsyncClient

from main import app


@pytest.mark.asyncio
async def test_chat_stubs_return_501() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.post("/api/v1/chat/sessions", json={})
        assert r.status_code == 501

        r = await client.post(
            "/api/v1/chat/sessions/00000000-0000-0000-0000-000000000000/messages",
            json={"message": "hi"},
        )
        assert r.status_code == 501

        r = await client.get("/api/v1/chat/sessions")
        assert r.status_code == 501

        r = await client.get(
            "/api/v1/chat/sessions/00000000-0000-0000-0000-000000000000"
        )
        assert r.status_code == 501


@pytest.mark.asyncio
async def test_knowledge_and_tickets_stubs_return_501() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.post(
            "/api/v1/knowledge/sources",
            json={"url": "https://example.com/docs"},
        )
        assert r.status_code == 501

        r = await client.get("/api/v1/knowledge/sources")
        assert r.status_code == 501

        r = await client.get("/api/v1/tickets")
        assert r.status_code == 501

        r = await client.get(
            "/api/v1/tickets/00000000-0000-0000-0000-000000000000"
        )
        assert r.status_code == 501

        r = await client.get("/api/v1/analytics/overview")
        assert r.status_code == 501
