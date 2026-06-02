import asyncio
import logging
import os
from dotenv import load_dotenv

# Load .env before importing backend modules
load_dotenv(os.path.join(os.path.dirname(__file__), 'backend', '.env'))

from backend.services.knowledge_service import KnowledgeService

logging.basicConfig(level=logging.INFO)

async def main():
    service = KnowledgeService()
    success = await service.ingest_source("035e8872-169f-43c4-b15a-81c73bd44083")
    print(f"Ingestion success: {success}")

asyncio.run(main())
