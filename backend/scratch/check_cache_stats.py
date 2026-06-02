import asyncio
from ai.chroma_utils import get_chroma_client, get_collection

async def main():
    client = get_chroma_client()
    collection = get_collection(client, "semantic_cache")
    
    print("\n--- ⚡ Semantic Cache Stats ---")
    print(f"Total Cache Entries: {collection.count()}")
    
    results = collection.get()
    ids = results.get("ids", [])
    documents = results.get("documents", [])
    metadatas = results.get("metadatas", [])
    
    if ids:
        print("\n--- 💾 Cached Queries & Hits ---")
        for i in range(len(ids)):
            meta = metadatas[i]
            print(f"[{i+1}] Query: '{documents[i]}'")
            print(f"    Hash: {ids[i]}")
            print(f"    Hits: {meta.get('hit_count', 0)}")
            print(f"    Source ID: {meta.get('source_id', 'None')}")
            print(f"    Response preview: {str(meta.get('cached_response', ''))[:80]}...")
            print("-" * 40)
    else:
        print("\nCache is currently empty. Query something on the UI and click 👍 to populate it!")

if __name__ == "__main__":
    asyncio.run(main())
