# tests/test_chunking.py
"""
Unit tests for ragchunker.chunking module.
Tests fixed, semantic, and recursive chunking strategies.
"""
import pytest
from ragchunker.chunking import RAGChunker

SAMPLE_TEXT = "This is sentence one. This is sentence two. This is a longer sentence three to test chunking."

def test_fixed_chunking():
    """Test fixed-length chunking."""
    chunker = RAGChunker(strategy="fixed", chunk_size=20, overlap=5)
    chunks = chunker.chunk(SAMPLE_TEXT)
    assert len(chunks) > 1
    assert all(len(c) <= 20 for c in chunks)
    assert chunks[0].startswith("This is sentence one")

def test_semantic_chunking():
    """Test semantic chunking (skipped if sentence-transformers not installed)."""
    try:
        from sentence_transformers import SentenceTransformer
        chunker = RAGChunker(strategy="semantic", chunk_size=100)
        chunks = chunker.chunk(SAMPLE_TEXT)
        assert len(chunks) >= 1
        assert any("sentence one" in c for c in chunks)
    except ImportError:
        pytest.skip("sentence-transformers not installed")

def test_recursive_chunking():
    """Test recursive chunking with markdown-like text."""
    text = "# Section 1\nText here.\n## Subsection\nMore text.\n# Section 2\nAnother text."
    chunker = RAGChunker(strategy="recursive", chunk_size=50)
    chunks = chunker.chunk(text)
    assert len(chunks) > 1
    assert any("Section 1" in c for c in chunks)
    assert any("Section 2" in c for c in chunks)

def test_invalid_strategy():
    """Test invalid chunking strategy."""
    with pytest.raises(ValueError):
        chunker = RAGChunker(strategy="invalid")
        chunker.chunk(SAMPLE_TEXT)