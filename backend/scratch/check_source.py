import asyncio
import uuid
from sqlalchemy import select
from config.database import async_session_factory
from models.knowledge_source import KnowledgeSource

async def check_source(source_id: str):
    async with async_session_factory() as db:
        source = await db.get(KnowledgeSource, uuid.UUID(source_id))
        if source:
            print(f"ID: {source.id}")
            print(f"URL: {source.url}")
            print(f"Status: {source.status}")
        else:
            print("Source not found")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        asyncio.run(check_source(sys.argv[1]))
    else:
        print("Please provide source_id")
