from langchain_text_splitters import RecursiveCharacterTextSplitter

from talentscreen.config import get_settings


def semantic_chunk(text: str, metadata: dict | None = None) -> list[dict]:
    """Semantic chunking with overlap — Docling/Unstructured output → retrieval chunks."""
    settings = get_settings()
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    docs = splitter.create_documents([text], metadatas=[metadata or {}])
    return [
        {
            "text": doc.page_content,
            "metadata": doc.metadata,
            "token_count": len(doc.page_content.split()),
        }
        for doc in docs
    ]
