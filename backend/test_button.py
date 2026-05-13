import asyncio
from ai.rag_pipeline import get_rag_engine

async def main():
    rag = get_rag_engine()
    query = "How do I create a button in React?"
    results = await rag.search(query)
    
    print(f"\nSearch results for '{query}':")
    for r in results:
        print(f"- {r['similarity']:.4f} | {r['metadata'].get('source_title')} | {r['content'][:100]}...")
        
    print("\nTesting post-retrieval confidence...")
    from services.confidence_service import ConfidenceService
    conf = ConfidenceService(llm_engine=rag.llm_engine)
    post = await conf.calculate_post_retrieval_confidence(query, results)
    print("Post confidence:", post)

    print("\nTesting agentic RAG generation...")
    resp, sources = await rag.generate_response(query, results)
    print("Resp:", resp[:100])

if __name__ == "__main__":
    asyncio.run(main())
