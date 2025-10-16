# tests/test_embeddings.py
"""
Unit tests for ragchunker.embeddings module.
Tests embedding generation and FAISS indexing (if available).
"""
import pytest
from ragchunker.file_ingestion import Document
from ragchunker.embeddings import EmbeddingClient, EmbeddingResult

SAMPLE_TEXT = "This is a test document."

def test_sentence_transformers_embedding():
    """Test sentence-transformers embedding generation."""
    try:
        client = EmbeddingClient(provider="sentence-transformers", model="all-MiniLM-L6-v2", device="cpu")
        doc = Document(content=SAMPLE_TEXT)
        results = client.embed_documents([doc])
        assert len(results) == 1
        assert isinstance(results[0], EmbeddingResult)
        assert len(results[0].vector) > 0
    except ImportError:
        pytest.skip("sentence-transformers not installed")

def test_format_for_vectorstore():
    """Test formatting embeddings for vector store."""
    result = EmbeddingResult(id="1", vector=[0.1, 0.2], metadata={"source": "test"})
    formatted = EmbeddingClient.format_for_vectorstore([result])
    assert len(formatted) == 1
    assert formatted[0]["id"] == "1"
    assert formatted[0]["vector"] == [0.1, 0.2]
    assert formatted[0]["metadata"] == {"source": "test"}

def test_faiss_index():
    """Test FAISS index building (skipped if faiss not installed)."""
    try:
        import faiss
        client = EmbeddingClient(provider="sentence-transformers", model="all-MiniLM-L6-v2")
        doc = Document(content=SAMPLE_TEXT)
        embeddings = client.embed_documents([doc])
        index, ids = client.build_faiss_index(embeddings)
        assert len(ids) == 1
        assert ids[0] == embeddings[0].id
    except ImportError:
        pytest.skip("faiss or sentence-transformers not installed")