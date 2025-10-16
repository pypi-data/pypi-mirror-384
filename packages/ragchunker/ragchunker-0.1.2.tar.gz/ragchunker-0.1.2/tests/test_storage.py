# tests/test_storage.py
"""
Unit tests for ragchunker.storage module.
Tests JSONL, Parquet, SQLite, and FAISS storage functions.
"""
import os
import pytest
import numpy as np
from ragchunker.file_ingestion import Document
from ragchunker.storage import (
    save_chunks_jsonl,
    load_chunks_jsonl,
    save_chunks_parquet,
    save_chunks_sqlite,
    save_embeddings_jsonl,
    save_embeddings_npy,
    load_embeddings_npy,
    build_and_save_faiss_index,
    load_faiss_index,
)

SAMPLE_TEXT = "Sample storage test."
TEST_DIR = "test_data"

@pytest.fixture(autouse=True)
def setup_test_data(tmp_path):
    """Create temporary directory for storage tests."""
    os.makedirs(TEST_DIR, exist_ok=True)
    yield
    for f in os.listdir(TEST_DIR):
        os.remove(os.path.join(TEST_DIR, f))
    os.rmdir(TEST_DIR)

def test_save_load_jsonl():
    """Test saving and loading chunks as JSONL."""
    doc = Document(content=SAMPLE_TEXT, metadata={"source": "test.txt"})
    path = os.path.join(TEST_DIR, "chunks.jsonl")
    save_chunks_jsonl([doc], path)
    loaded = load_chunks_jsonl(path)
    assert len(loaded) == 1
    assert loaded[0].content == SAMPLE_TEXT
    assert loaded[0].metadata["source"] == "test.txt"

def test_save_parquet():
    """Test saving chunks as Parquet (skipped if pandas not installed)."""
    try:
        import pandas
        doc = Document(content=SAMPLE_TEXT, metadata={"source": "test.txt"})
        path = os.path.join(TEST_DIR, "chunks.parquet")
        save_chunks_parquet([doc], path)
        assert os.path.exists(path)
    except ImportError:
        pytest.skip("pandas not installed")

def test_save_sqlite():
    """Test saving chunks to SQLite."""
    doc = Document(content=SAMPLE_TEXT, metadata={"source": "test.txt"})
    path = os.path.join(TEST_DIR, "chunks.db")
    save_chunks_sqlite([doc], path)
    assert os.path.exists(path)
    conn = sqlite3.connect(path)
    cur = conn.cursor()
    cur.execute("SELECT content FROM chunks")
    content = cur.fetchone()[0]
    assert content == SAMPLE_TEXT
    conn.close()

def test_save_load_embeddings_npy():
    """Test saving and loading embeddings as NumPy arrays."""
    items = [{"id": "1", "vector": [0.1, 0.2], "metadata": {"source": "test"}}]
    paths = save_embeddings_npy(items, TEST_DIR)
    mat, ids = load_embeddings_npy(paths["npy"], paths["ids"])
    assert len(ids) == 1
    assert ids[0] == "1"
    assert np.allclose(mat[0], [0.1, 0.2])

def test_faiss_index():
    """Test building and loading FAISS index (skipped if faiss not installed)."""
    try:
        import faiss
        items = [{"id": "1", "vector": [0.1, 0.2], "metadata": {}}]
        index_path, ids_path = build_and_save_faiss_index(items, os.path.join(TEST_DIR, "test.index"))
        index, ids = load_faiss_index(index_path)
        assert len(ids) == 1
        assert ids[0] == "1"
    except ImportError:
        pytest.skip("faiss not installed")