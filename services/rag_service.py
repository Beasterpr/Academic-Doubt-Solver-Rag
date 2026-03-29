from langchain_chroma import Chroma

from core.models import embedding_model
from loaders.document_loader import load_documents, split_documents_rag
from chains.rag_chain import build_rag_chain


# RAG SERVICE

def preprocessing(paths, urls):
    """Load, split, and index documents into ChromaDB. Returns (db, num_docs, num_chunks)."""

    docs = load_documents(paths, urls)
    chunks = split_documents_rag(docs)

    db = Chroma.from_documents(
        chunks,
        embedding_model(),
    )

    return db, len(docs), len(chunks)
