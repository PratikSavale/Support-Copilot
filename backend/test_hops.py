import asyncio
from ai.rag_pipeline import get_rag_engine

async def main():
    rag = get_rag_engine()
    
    # 1. Let's see what's in the DB
    results = await rag.search("testing")
    for r in results:
         print("DB Contains:", r['metadata'].get('source_title'))
         
    # 2. Ask a question
    print("--------------------------------")
    query = "What happens if I put 1000 items in a HashMap with hashCode 1?"
    resp, sources = await rag.generate_response(query, results)
    print("Response:", resp)
    print("Sources:", [s['title'] for s in sources])

asyncio.run(main())
