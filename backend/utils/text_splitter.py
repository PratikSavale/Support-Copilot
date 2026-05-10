"""Text splitter utility for RAG chunking."""

try:
    # LangChain 0.2+ package split
    from langchain_text_splitters import RecursiveCharacterTextSplitter
except ImportError:  # pragma: no cover - fallback for older environments
    from langchain.text_splitter import RecursiveCharacterTextSplitter


class TextSplitter:
    """Split long text into overlapping chunks."""

    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 100) -> None:
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""],
        )

    def split_text(self, text: str) -> list[str]:
        return self.splitter.split_text(text)

    def create_chunks_with_metadata(
        self, text: str, source_id: str, source_title: str = ""
    ) -> list[dict]:
        chunks = self.split_text(text)
        return [
            {
                "content": chunk,
                "metadata": {
                    "source_id": source_id,
                    "source_title": source_title,
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                },
            }
            for i, chunk in enumerate(chunks)
        ]
