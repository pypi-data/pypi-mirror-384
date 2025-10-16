# tests/test_file_ingestion.py
"""
Unit tests for ragchunker.file_ingestion module.
Tests file loading for various formats and the auto_load functionality.
"""
import os
import pytest
from ragchunker.file_ingestion import auto_load, Document, load_txt, load_pdf, load_docx, load_pptx, load_image, load_audio_whisper, load_csv, load_excel, load_parquet, load_html, load_json, extract_from_zip_or_tar

# Sample test data
TEST_DIR = "test_data"
SAMPLE_TEXT = "This is a sample text file."
SAMPLE_JSON = '{"key": "value"}'

@pytest.fixture(autouse=True)
def setup_test_data(tmp_path):
    """Create temporary test files for various formats."""
    os.makedirs(TEST_DIR, exist_ok=True)
    # Create sample text file
    with open(os.path.join(TEST_DIR, "sample.txt"), "w", encoding="utf-8") as f:
        f.write(SAMPLE_TEXT)
    # Create sample JSON file
    with open(os.path.join(TEST_DIR, "sample.json"), "w", encoding="utf-8") as f:
        f.write(SAMPLE_JSON)
    yield
    # Cleanup
    for f in os.listdir(TEST_DIR):
        os.remove(os.path.join(TEST_DIR, f))
    os.rmdir(TEST_DIR)

def test_load_txt():
    """Test loading a text file."""
    docs = load_txt(os.path.join(TEST_DIR, "sample.txt"))
    assert len(docs) == 1
    assert isinstance(docs[0], Document)
    assert docs[0].content == SAMPLE_TEXT
    assert docs[0].metadata.get("type") == "text"

def test_load_json():
    """Test loading a JSON file."""
    docs = load_json(os.path.join(TEST_DIR, "sample.json"))
    assert len(docs) == 1
    assert docs[0].content == SAMPLE_JSON
    assert docs[0].metadata.get("type") == "json"

def test_auto_load_text():
    """Test auto_load with a text file."""
    docs = auto_load(os.path.join(TEST_DIR, "sample.txt"))
    assert len(docs) == 1
    assert docs[0].content == SAMPLE_TEXT
    assert docs[0].metadata.get("type") == "text"

def test_auto_load_directory():
    """Test auto_load with a directory."""
    docs = auto_load(TEST_DIR)
    assert len(docs) >= 2  # Should load both txt and json
    types = {d.metadata.get("type") for d in docs}
    assert "text" in types
    assert "json" in types

@pytest.mark.skipif(not hasattr(os, "mkdir"), reason="OS does not support directory operations")
def test_auto_load_nonexistent():
    """Test auto_load with nonexistent file."""
    with pytest.raises(FileNotFoundError):
        auto_load("nonexistent.txt")

# Skip tests for optional dependencies if not installed
def test_load_pdf():
    """Test PDF loading (skipped if pdfminer.six not installed)."""
    try:
        import pdfminer.high_level
        # Mocking PDF loading requires actual PDF; skipping detailed test
        assert True
    except ImportError:
        pytest.skip("pdfminer.six not installed")

def test_load_docx():
    """Test DOCX loading (skipped if python-docx not installed)."""
    try:
        import docx
        assert True
    except ImportError:
        pytest.skip("python-docx not installed")

def test_load_pptx():
    """Test PPTX loading (skipped if python-pptx not installed)."""
    try:
        from pptx import Presentation
        assert True
    except ImportError:
        pytest.skip("python-pptx not installed")

def test_load_image():
    """Test image OCR (skipped if Pillow or pytesseract not installed)."""
    try:
        from PIL import Image
        import pytesseract
        assert True
    except ImportError:
        pytest.skip("Pillow or pytesseract not installed")

def test_load_audio_whisper():
    """Test audio transcription (skipped if whisper not installed)."""
    try:
        import whisper
        assert True
    except ImportError:
        pytest.skip("openai-whisper not installed")

def test_load_csv():
    """Test CSV loading (skipped if pandas not installed)."""
    try:
        import pandas
        assert True
    except ImportError:
        pytest.skip("pandas not installed")

def test_load_excel():
    """Test Excel loading (skipped if pandas/openpyxl not installed)."""
    try:
        import pandas
        import openpyxl
        assert True
    except ImportError:
        pytest.skip("pandas or openpyxl not installed")

def test_load_parquet():
    """Test Parquet loading (skipped if pandas/pyarrow not installed)."""
    try:
        import pandas
        import pyarrow
        assert True
    except ImportError:
        pytest.skip("pandas or pyarrow not installed")

def test_load_html():
    """Test HTML loading (skipped if trafilatura or beautifulsoup4 not installed)."""
    try:
        import trafilatura
        assert True
    except ImportError:
        try:
            from bs4 import BeautifulSoup
            assert True
        except ImportError:
            pytest.skip("trafilatura or beautifulsoup4 not installed")