import asyncio
from sqlalchemy import text
from config.database import engine
from models.base import Base
import models # ensure all models are imported

async def create_tables():
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.create_all)
    print("Tables created successfully")

if __name__ == "__main__":
    asyncio.run(create_tables())
