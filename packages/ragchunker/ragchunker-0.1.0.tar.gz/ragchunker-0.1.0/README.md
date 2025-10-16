# ragchunker

A modular Python package for Retrieval-Augmented Generation (RAG) preprocessing. It supports:

- **File Ingestion**: Load documents from various formats (TXT, PDF, DOCX, PPTX, images with OCR, audio with Whisper, CSV/Excel/Parquet, HTML, JSON, ZIP/TAR).
- **Chunking**: Split documents into chunks using fixed-length, semantic, or recursive strategies.
- **Provenance**: Track metadata, checksums, and token counts for chunks.
- **Embeddings**: Generate embeddings using Sentence-Transformers or OpenAI.
- **Storage**: Save chunks and embeddings to JSONL, Parquet, SQLite, NumPy, or FAISS; optional integration with Pinecone or ChromaDB.

## Installation

Install the core package:

```bash
pip install ragchunker



For Testing:

from ragchunker.rag_pipeline import run_rag_pipeline

result = run_rag_pipeline(
    data_dir="data",                # Folder with your PDFs, docs, or txt files
    output_dir="output",            # Where JSONL, Chunks and embeddings will be saved
    chunk_strategy="semantic",      # or "fixed", "recursive"
    chunk_size=800,
    overlap=100,
    embed_model="all-MiniLM-L6-v2", # or any other
    embed_provider="sentence-transformers",
    openai_api_key=None                    # or "sk-your-openai-key" if using OpenAI
)

print("\n✅ Pipeline executed successfully!")


result = run_rag_pipeline(
    data_dir="data",                # Folder with your PDFs, docs, or txt files
    output_dir="output",            # Where JSONL, Chunks and embeddings will be saved
    chunk_strategy="semantic",      # or "fixed", "recursive"
    chunk_size=800,
    overlap=100,
    embed_model="text-embedding-3-small", # or any other
    embed_provider="openai",
    openai_api_key="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"                   # or "sk-your-openai-key" if using OpenAI
)

print("\n✅ Pipeline executed successfully!")