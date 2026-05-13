import asyncio
from ai.chroma_utils import get_chroma_client, get_collection
from config.settings import get_settings

async def main():
    settings = get_settings()
    client = get_chroma_client()
    col = get_collection(client, settings.CHROMA_COLLECTION)
    docs = col.get(where={"source_title": "Javaaa"})
    print(f"Total chunks found: {len(docs.get('documents', []))}")
    if docs.get('documents'):
        for i in range(min(3, len(docs['documents']))):
            print(f"--- Chunk {i} ---")
            print(docs['documents'][i][:300])
            print("...")

asyncio.run(main())
