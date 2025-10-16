# tests/test_rag_pipeline.py
"""
Integration tests for ragchunker.rag_pipeline module.
Tests the full RAG pipeline with mocked inputs.
"""
import os
import pytest
from ragchunker.rag_pipeline import run_rag_pipeline
from ragchunker.file_ingestion import Document

TEST_DIR = "test_data"
SAMPLE_TEXT = "This is a test document for the pipeline."

@pytest.fixture(autouse=True)
def setup_test_data(tmp_path):
    """Create temporary test files and output directory."""
    os.makedirs(TEST_DIR, exist_ok=True)
    os.makedirs(os.path.join(TEST_DIR, "output"), exist_ok=True)
    with open(os.path.join(TEST_DIR, "sample.txt"), "w", encoding="utf-8") as f:
        f.write(SAMPLE_TEXT)
    yield
    for f in os.listdir(TEST_DIR):
        if os.path.isdir(os.path.join(TEST_DIR, f)):
            for subf in os.listdir(os.path.join(TEST_DIR, f)):
                os.remove(os.path.join(TEST_DIR, f, subf))
            os.rmdir(os.path.join(TEST_DIR, f))
        else:
            os.remove(os.path.join(TEST_DIR, f))
    os.rmdir(TEST_DIR)

def test_rag_pipeline():
    """Test the full RAG pipeline with semantic chunking."""
    try:
        from sentence_transformers import SentenceTransformer
        output = run_rag_pipeline(
            data_dir=TEST_DIR,
            output_dir=os.path.join(TEST_DIR, "output"),
            chunk_strategy="semantic",
            chunk_size=100,
            overlap=10,
            embed_model="all-MiniLM-L6-v2",
            embed_provider="sentence-transformers",
            device="cpu",
        )
        assert os.path.exists(output["chunks_path"])
        assert os.path.exists(output["embeddings_jsonl"])
        assert os.path.exists(os.path.join(output["embeddings_numpy_dir"], "embeddings.npy"))
    except ImportError:
        pytest.skip("sentence-transformers not installed")