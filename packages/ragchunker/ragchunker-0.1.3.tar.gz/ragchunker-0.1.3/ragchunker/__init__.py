# ragchunker/__init__.py
"""
ragchunker: A modular package for Retrieval-Augmented Generation (RAG) preprocessing.
Features file ingestion, chunking, provenance tracking, embedding generation, and storage.
"""
__version__ = "0.1.0"

from .file_ingestion import auto_load, load_single, Document
from .chunking import RAGChunker
from .provenance import (
    enrich_chunks_from_texts,
    attach_provenance_to_documents,
    serialize_documents_to_jsonl,
    load_documents_from_jsonl,
    merge_adjacent_small_chunks,
)
from .embeddings import EmbeddingClient, EmbeddingResult
from .storage import (
    save_chunks_jsonl,
    load_chunks_jsonl,
    save_chunks_parquet,
    save_chunks_sqlite,
    save_embeddings_jsonl,
    save_embeddings_npy,
    build_and_save_faiss_index,
    load_faiss_index,
    push_to_pinecone,
    push_to_chroma,
)
from .rag_pipeline import run_rag_pipeline