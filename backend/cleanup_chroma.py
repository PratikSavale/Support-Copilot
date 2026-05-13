import chromadb
from config.settings import get_settings

def main():
    settings = get_settings()
    client = chromadb.HttpClient(host=settings.CHROMA_HOST, port=settings.CHROMA_PORT)
    collection = client.get_collection(settings.CHROMA_COLLECTION)
    
    # Get all documents
    all_data = collection.get()
    metadatas = all_data.get("metadatas", [])
    ids_to_delete = []
    
    for i, meta in enumerate(metadatas):
        if meta and meta.get("source_id", "").startswith("fallback_"):
            ids_to_delete.append(all_data["ids"][i])
            
    if ids_to_delete:
        print(f"Deleting {len(ids_to_delete)} fallback chunks...")
        collection.delete(ids=ids_to_delete)
        print("Done.")
    else:
        print("No fallback chunks found.")

if __name__ == "__main__":
    main()
