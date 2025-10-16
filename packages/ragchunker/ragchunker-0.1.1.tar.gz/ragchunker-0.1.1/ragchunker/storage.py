# ragchunker/storage.py
"""
Output & Storage helpers for ragchunker

Provides:
- save_chunks_jsonl / load_chunks_jsonl
- save_chunks_parquet
- save_chunks_sqlite
- save_embeddings_jsonl
- save_embeddings_npy (and ids.txt)
- build_and_save_faiss_index / load_faiss_index
- optional push_to_pinecone, push_to_chroma (SDKs optional)

Design goals:
- Clear logging, helpful error messages
- Optional dependencies only required when using a feature
- Works with Document dataclass from ragchunker.file_ingestion
"""

from __future__ import annotations
import os
import json
import logging
import sqlite3
from typing import List, Dict, Any, Optional, Tuple, Iterable
from dataclasses import asdict

import numpy as np

# optional imports
try:
    import pandas as pd
except Exception:
    pd = None

try:
    import faiss
except Exception:
    faiss = None

try:
    import pinecone
except Exception:
    pinecone = None

try:
    import chromadb
    from chromadb.utils import embedding_functions
except Exception:
    chromadb = None

# Import Document & EmbeddingResult if available
try:
    from ragchunker.file_ingestion import Document
except Exception:
    # fallback for isolated testing
    from file_ingestion import Document  # type: ignore

logger = logging.getLogger("ragchunker.storage")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO)


# -------------------------
# Chunk storage
# -------------------------
def save_chunks_jsonl(docs: List[Document], out_path: str) -> str:
    """
    Save Document objects to JSONL (one JSON per line).
    Each line: {"id":..., "content": "...", "metadata": {...}}
    """
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as fw:
        for d in docs:
            obj = {"id": d.id, "content": d.content, "metadata": d.metadata or {}}
            fw.write(json.dumps(obj, ensure_ascii=False) + "\n")
    logger.info("Saved %d documents to %s", len(docs), out_path)
    return out_path


def load_chunks_jsonl(path: str) -> List[Document]:
    """Load JSONL produced by save_chunks_jsonl"""
    if not os.path.isfile(path):
        raise FileNotFoundError(path)
    out: List[Document] = []
    with open(path, "r", encoding="utf-8") as fr:
        for i, line in enumerate(fr):
            try:
                obj = json.loads(line)
                doc_id = obj.get("id") or None
                content = obj.get("content", "")
                metadata = obj.get("metadata", {}) or {}
                out.append(Document(id=doc_id, content=content, metadata=metadata))
            except Exception as e:
                logger.exception("Failed to parse JSONL line %d in %s: %s", i + 1, path, e)
    logger.info("Loaded %d documents from %s", len(out), path)
    return out


def save_chunks_parquet(docs: List[Document], out_path: str) -> str:
    """
    Save docs to Parquet using pandas. Each row: id, content, metadata (json string)
    Requires pandas + pyarrow (if writing parquet).
    """
    if pd is None:
        raise ImportError("pandas is required to save parquet. Install: pip install pandas pyarrow")

    rows = []
    for d in docs:
        rows.append({"id": d.id, "content": d.content, "metadata": json.dumps(d.metadata or {})})
    df = pd.DataFrame(rows)
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    df.to_parquet(out_path, index=False)
    logger.info("Saved %d documents to parquet %s", len(rows), out_path)
    return out_path


def save_chunks_sqlite(docs: List[Document], db_path: str, table_name: str = "chunks") -> str:
    """
    Save docs to SQLite. Creates a simple table: id TEXT PRIMARY KEY, content TEXT, metadata JSON TEXT
    """
    os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute(f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            id TEXT PRIMARY KEY,
            content TEXT,
            metadata TEXT
        )
    """)
    upsert_sql = f"INSERT OR REPLACE INTO {table_name} (id, content, metadata) VALUES (?, ?, ?)"
    rows = []
    for d in docs:
        rows.append((d.id, d.content, json.dumps(d.metadata or {})))
    cur.executemany(upsert_sql, rows)
    conn.commit()
    conn.close()
    logger.info("Saved %d documents to sqlite %s (table=%s)", len(rows), db_path, table_name)
    return db_path


# -------------------------
# Embedding storage
# -------------------------
def save_embeddings_jsonl(items: Iterable[Dict[str, Any]], out_path: str) -> str:
    """
    Save embeddings to JSONL.
    items: iterable of dicts with keys: 'id', 'vector', 'metadata'
    """
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    count = 0
    with open(out_path, "w", encoding="utf-8") as fw:
        for it in items:
            id_ = it.get("id")
            vec = it.get("vector") or it.get("embedding") or []
            # serialize vector safely
            try:
                serial_vec = [float(x) for x in np.asarray(vec).reshape(-1)]
            except Exception:
                serial_vec = []
            out_obj = {"id": id_, "vector": serial_vec, "metadata": it.get("metadata", {})}
            fw.write(json.dumps(out_obj, ensure_ascii=False) + "\n")
            count += 1
    logger.info("Saved %d embeddings to %s", count, out_path)
    return out_path


def save_embeddings_npy(items: Iterable[Dict[str, Any]], out_dir: str) -> Dict[str, str]:
    """
    Save embeddings to a single numpy .npy file and ids.txt.
    Returns dict with paths {"npy":..., "ids":...}
    """
    os.makedirs(out_dir, exist_ok=True)
    ids = []
    vecs = []
    for it in items:
        ids.append(str(it.get("id")))
        vec = it.get("vector") or it.get("embedding") or []
        vecs.append(np.asarray(vec, dtype=np.float32))
    if len(vecs) == 0:
        raise ValueError("No vectors found in items")
    mat = np.stack(vecs, axis=0)
    npy_path = os.path.join(out_dir, "embeddings.npy")
    ids_path = os.path.join(out_dir, "ids.txt")
    np.save(npy_path, mat)
    with open(ids_path, "w", encoding="utf-8") as f:
        for _id in ids:
            f.write(f"{_id}\n")
    logger.info("Saved %d vectors to %s and ids to %s", mat.shape[0], npy_path, ids_path)
    return {"npy": npy_path, "ids": ids_path}


def load_embeddings_npy(npy_path: str, ids_path: str) -> Tuple[np.ndarray, List[str]]:
    """Load back numpy embeddings and ids"""
    if not os.path.isfile(npy_path):
        raise FileNotFoundError(npy_path)
    if not os.path.isfile(ids_path):
        raise FileNotFoundError(ids_path)
    mat = np.load(npy_path)
    with open(ids_path, "r", encoding="utf-8") as f:
        ids = [l.strip() for l in f if l.strip()]
    logger.info("Loaded %d vectors from %s", mat.shape[0], npy_path)
    return mat, ids


# -------------------------
# FAISS helpers
# -------------------------
def build_and_save_faiss_index(items: Iterable[Dict[str, Any]], index_path: str, metric: str = "inner_product") -> Tuple[str, List[str]]:
    """
    Build FAISS index from items (each must contain 'vector' and 'id').
    Saves index to index_path (faiss.write_index) and ids to index_path + '.ids'.
    Returns (index_path, ids_path)
    """
    if faiss is None:
        raise ImportError("faiss is required to build index. Install: pip install faiss-cpu")

    # collect vectors and ids
    ids = []
    vecs = []
    for it in items:
        ids.append(str(it.get("id")))
        vecs.append(np.asarray(it.get("vector"), dtype=np.float32))
    if len(vecs) == 0:
        raise ValueError("No vectors to index")

    mat = np.stack(vecs, axis=0)
    dim = mat.shape[1]
    if metric == "inner_product":
        index = faiss.IndexFlatIP(dim)
    elif metric == "l2":
        index = faiss.IndexFlatL2(dim)
    else:
        raise ValueError("Unsupported metric; use 'inner_product' or 'l2'")

    index.add(mat)
    os.makedirs(os.path.dirname(index_path) or ".", exist_ok=True)
    faiss.write_index(index, index_path)
    ids_path = index_path + ".ids"
    with open(ids_path, "w", encoding="utf-8") as f:
        for _id in ids:
            f.write(f"{_id}\n")
    logger.info("Saved FAISS index to %s and ids to %s (n=%d, dim=%d)", index_path, ids_path, mat.shape[0], dim)
    return index_path, ids_path


def load_faiss_index(index_path: str) -> Tuple[Any, List[str]]:
    """Load FAISS index and ids file."""
    if faiss is None:
        raise ImportError("faiss is required to load index.")
    if not os.path.isfile(index_path):
        raise FileNotFoundError(index_path)
    index = faiss.read_index(index_path)
    ids_path = index_path + ".ids"
    if not os.path.isfile(ids_path):
        raise FileNotFoundError(ids_path)
    with open(ids_path, "r", encoding="utf-8") as f:
        ids = [l.strip() for l in f if l.strip()]
    logger.info("Loaded FAISS index from %s (n_ids=%d)", index_path, len(ids))
    return index, ids


# -------------------------
# Optional push adapters (Pinecone, Chroma)
# -------------------------
def push_to_pinecone(items: Iterable[Dict[str, Any]], index_name: str, api_key: Optional[str] = None, environment: Optional[str] = None, upsert_batch: int = 100) -> None:
    """
    Push items to Pinecone index. items must be dicts {'id','vector','metadata'}.
    Requires pinecone-client installed and API key.
    """
    if pinecone is None:
        raise ImportError("pinecone-client is required. Install: pip install pinecone-client")

    key = api_key or os.environ.get("PINECONE_API_KEY")
    env = environment or os.environ.get("PINECONE_ENVIRONMENT")
    if not key:
        raise ValueError("Pinecone API key required (api_key arg or PINECONE_API_KEY env var)")

    pinecone.init(api_key=key, environment=env)
    # create index if not exists (simple flat index)
    if index_name not in pinecone.list_indexes():
        example_vec = next(iter(items))["vector"]
        dim = len(example_vec)
        pinecone.create_index(index_name, dimension=dim)

    idx = pinecone.Index(index_name)
    batch = []
    count = 0
    for it in items:
        vec = it.get("vector")
        meta = it.get("metadata", {})
        batch.append((str(it.get("id")), vec, meta))
        if len(batch) >= upsert_batch:
            idx.upsert(vectors=batch)
            count += len(batch)
            batch = []
    if batch:
        idx.upsert(vectors=batch)
        count += len(batch)
    logger.info("Pushed %d items to Pinecone index '%s'", count, index_name)


def push_to_chroma(items: Iterable[Dict[str, Any]], persist_directory: str = "chroma_db", collection_name: str = "ragchunker") -> None:
    """
    Push embeddings to local ChromaDB. Requires chromadb package.
    """
    if chromadb is None:
        raise ImportError("chromadb is required for Chroma adapter. Install: pip install chromadb")

    os.makedirs(persist_directory, exist_ok=True)
    client = chromadb.Client()
    # create collection
    coll = client.create_collection(name=collection_name)
    ids = []
    vectors = []
    metadatas = []
    for it in items:
        ids.append(str(it.get("id")))
        vectors.append(list(np.asarray(it.get("vector")).astype(float)))
        metadatas.append(it.get("metadata", {}))
    coll.add(ids=ids, embeddings=vectors, metadatas=metadatas)
    # Chroma persistence depends on client; this simple API may vary by chromadb version
    logger.info("Pushed %d items to Chroma collection '%s' (persist=%s)", len(ids), collection_name, persist_directory)


# -------------------------
# Small helpers
# -------------------------
def ensure_metadata_serializable(meta: Dict[str, Any]) -> Dict[str, Any]:
    """Make metadata JSON-serializable by converting non-serializable items to strings."""
    out = {}
    for k, v in (meta or {}).items():
        try:
            json.dumps(v)
            out[k] = v
        except Exception:
            out[k] = str(v)
    return out


# -------------------------
# Example usage (for docs only)
# -------------------------
if __name__ == "__main__":
    # quick local demo (requires numpy and optionally pandas/faiss)
    from ragchunker.file_ingestion import Document  # type: ignore

    docs = [Document(content="Hello world", metadata={"source": "demo.txt"}), Document(content="Another doc", metadata={"source": "demo.txt"})]
    save_chunks_jsonl(docs, "output/demo_chunks.jsonl")

    # embeddings demo
    items = [{"id": "1", "vector": [0.1, 0.2, 0.3], "metadata": {"a": 1}}, {"id": "2", "vector": [0.3, 0.2, 0.1], "metadata": {"a": 2}}]
    save_embeddings_jsonl(items, "output/demo_embeddings.jsonl")
    save_embeddings_npy(items, "output/emb_npy")
    if faiss is not None:
        build_and_save_faiss_index(items, "output/demo.index")
    logger.info("storage demo finished")
