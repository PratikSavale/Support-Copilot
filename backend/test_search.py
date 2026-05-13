import asyncio
import os
from ai.rag_pipeline import get_rag_engine
from config.database import async_session_factory
from models.knowledge_source import KnowledgeSource
from sqlalchemy import select

async def main():
    rag = get_rag_engine()
    
    # Check what sources we have
    async with async_session_factory() as db:
        res = await db.execute(select(KnowledgeSource))
        sources = list(res.scalars().all())
        for s in sources:
            print(f"Source: {s.title} ({s.status}) - {s.chunk_count} chunks")
            
    # Search for accordion
    query = "Give me specifics for carbon react accordion?"
    results = await rag.search(query)
    
    print(f"\nSearch results for '{query}':")
    for r in results:
        print(f"- {r['similarity']:.4f} | {r['metadata'].get('source_title')} | {r['content'][:100]}...")
        
    print("\nTesting agentic RAG generation...")
    resp, sources = await rag.generate_response(query, results)
    print(f"Resp: {resp}")
    print(f"Sources: {sources}")

if __name__ == "__main__":
    asyncio.run(main())
