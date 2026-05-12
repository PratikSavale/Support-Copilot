import asyncio
from sqlalchemy import select
from config.database import async_session_factory
from models.knowledge_source import KnowledgeSource

async def list_sources():
    async with async_session_factory() as db:
        result = await db.execute(select(KnowledgeSource))
        sources = result.scalars().all()
        for s in sources:
            print(f"ID: {s.id} | Status: {s.status} | URL: {s.url}")

if __name__ == "__main__":
    asyncio.run(list_sources())
