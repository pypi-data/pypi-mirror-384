# tests/test_provenance.py
"""
Unit tests for ragchunker.provenance module.
Tests metadata enrichment, checksums, token counting, and serialization.
"""
import os
import pytest
from ragchunker.file_ingestion import Document
from ragchunker.provenance import (
    enrich_chunks_from_texts,
    attach_provenance_to_documents,
    compute_file_sha256,
    count_tokens,
    serialize_documents_to_jsonl,
    load_documents_from_jsonl,
)

SAMPLE_TEXT = "Sample text for testing."
TEST_FILE = "test_data/sample.txt"

@pytest.fixture(autouse=True)
def setup_test_data(tmp_path):
    """Create temporary test file."""
    os.makedirs("test_data", exist_ok=True)
    with open(TEST_FILE, "w", encoding="utf-8") as f:
        f.write(SAMPLE_TEXT)
    yield
    os.remove(TEST_FILE)
    os.rmdir("test_data")

def test_enrich_chunks():
    """Test enriching chunks with metadata."""
    doc = Document(content=SAMPLE_TEXT, metadata={"source": TEST_FILE})
    chunks = [SAMPLE_TEXT[:10], SAMPLE_TEXT[10:]]
    enriched = enrich_chunks_from_texts(doc, chunks, strategy="fixed")
    assert len(enriched) == 2
    assert enriched[0].metadata["chunk_index"] == 0
    assert enriched[0].metadata["parent_id"] == doc.id
    assert enriched[0].metadata["checksum"] is not None

def test_compute_checksum():
    """Test file checksum computation."""
    checksum = compute_file_sha256(TEST_FILE)
    assert checksum is not None
    assert len(checksum) == 64  # SHA256 hex length

def test_count_tokens():
    """Test token counting."""
    count = count_tokens(SAMPLE_TEXT)
    assert count > 0
    assert isinstance(count, int)

def test_serialize_load_jsonl(tmp_path):
    """Test JSONL serialization and deserialization."""
    doc = Document(content=SAMPLE_TEXT, metadata={"source": TEST_FILE})
    out_path = tmp_path / "test.jsonl"
    serialize_documents_to_jsonl([doc], str(out_path))
    loaded = load_documents_from_jsonl(str(out_path))
    assert len(loaded) == 1
    assert loaded[0].content == SAMPLE_TEXT
    assert loaded[0].metadata["source"] == TEST_FILE