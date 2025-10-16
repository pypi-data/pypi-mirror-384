# rag_pipeline.py

import os
from ragchunker.file_ingestion import auto_load
from ragchunker.chunking import RAGChunker
from ragchunker.provenance import (
    enrich_chunks_from_texts,
    attach_provenance_to_documents,
)
from ragchunker.embeddings import EmbeddingClient
from ragchunker.storage import (
    save_chunks_jsonl,
    save_embeddings_jsonl,
    save_embeddings_npy,
    build_and_save_faiss_index,
)

def run_rag_pipeline(
    data_dir: str,
    output_dir: str,
    chunk_strategy: str = "semantic",
    chunk_size: int = 800,
    overlap: int = 100,
    embed_model: str = "all-MiniLM-L6-v2",
    embed_provider: str = "sentence-transformers",
    project: str = "ragchunker-demo",
    dataset: str = "sample",
    device: str = "cpu",
    openai_api_key: str = None,  # optional API key for OpenAI
):
    """
    Run full RAG Chunking + Embedding pipeline.

    Args:
        data_dir (str): Folder with source documents.
        output_dir (str): Folder to save chunks and embeddings.
        chunk_strategy (str): Chunking strategy, e.g., 'semantic'.
        chunk_size (int): Maximum characters per chunk.
        overlap (int): Overlap between chunks.
        embed_model (str): Embedding model name.
        embed_provider (str): Embedding provider ('sentence-transformers', 'openai', etc.)
        project (str): Project name for provenance.
        dataset (str): Dataset name for provenance.
        device (str): Device to use for embeddings ('cpu' or 'cuda').
        openai_api_key (str, optional): OpenAI API key if using OpenAI provider.
    """
    os.makedirs(output_dir, exist_ok=True)

    # 1️⃣ Load documents
    print(f"\n[1] Loading documents from: {data_dir}")
    docs = auto_load(data_dir)
    print(f"Loaded {len(docs)} documents")

    # 2️⃣ Chunking
    print(f"\n[2] Chunking documents ({chunk_strategy}, size={chunk_size}, overlap={overlap})...")
    chunker = RAGChunker(strategy=chunk_strategy, chunk_size=chunk_size, overlap=overlap)
    all_chunk_docs = []

    for doc in docs:
        chunk_texts = chunker.chunk(doc.content)
        enriched = enrich_chunks_from_texts(doc, chunk_texts, strategy=chunk_strategy)
        all_chunk_docs.extend(enriched)

    print(f"Generated {len(all_chunk_docs)} chunks total")

    # 3️⃣ Provenance
    print("\n[3] Attaching provenance...")
    all_chunk_docs = attach_provenance_to_documents(
        all_chunk_docs, project=project, dataset=dataset
    )
    chunks_path = os.path.join(output_dir, "chunks.jsonl")
    save_chunks_jsonl(all_chunk_docs, chunks_path)
    print(f"✅ Saved chunks to {chunks_path}")

    # 4️⃣ Embeddings
    print(f"\n[4] Generating embeddings ({embed_model})...")
    emb_client = EmbeddingClient(
        provider=embed_provider,
        model=embed_model,
        device=device,
        batch_size=64,
        openai_api_key=openai_api_key  # passes API key if needed
    )
    embedding_results = emb_client.embed_documents(all_chunk_docs)
    items = emb_client.format_for_vectorstore(embedding_results)

    # 5️⃣ Save embeddings
    print("\n[5] Saving embeddings...")
    emb_jsonl_path = os.path.join(output_dir, "embeddings.jsonl")
    emb_npy_dir = os.path.join(output_dir, "embeddings_numpy")

    save_embeddings_jsonl(items, emb_jsonl_path)
    save_embeddings_npy(items, emb_npy_dir)

    # 6️⃣ FAISS index
    try:
        index_path = os.path.join(output_dir, "faiss.index")
        build_and_save_faiss_index(items, index_path)
        print(f"✅ FAISS index saved to {index_path}")
    except ImportError:
        print("⚠️ faiss not installed; skipping FAISS index build")

    print("\n✅ Pipeline complete!")
    return {
        "chunks_path": chunks_path,
        "embeddings_jsonl": emb_jsonl_path,
        "embeddings_numpy_dir": emb_npy_dir,
        "faiss_index": index_path if os.path.exists(os.path.join(output_dir, "faiss.index")) else None,
    }
