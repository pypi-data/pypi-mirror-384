# ragchunker/embeddings.py
"""
Embedding Compatibility Layer for ragchunker

Supports:
- OpenAI Embeddings (openai package + OPENAI_API_KEY)
- Sentence-Transformers local embeddings (sentence_transformers)
- Optional FAISS helpers for creating/searching an index (if faiss is installed)

Main class: EmbeddingClient
Usage examples at bottom of file.
"""

from __future__ import annotations
import os
import time
import logging
from typing import List, Iterable, Optional, Dict, Any, Tuple
from dataclasses import dataclass

# Optional third-party libraries
try:
    import openai
except Exception:
    openai = None

try:
    from sentence_transformers import SentenceTransformer
except Exception:
    SentenceTransformer = None

try:
    import numpy as np
except Exception:
    raise ImportError("numpy is required for embeddings module. Install with: pip install numpy")

# Optional faiss
try:
    import faiss
except Exception:
    faiss = None

# Import Document dataclass from ingestion module
try:
    from ragchunker.file_ingestion import Document
except Exception:
    # fallback if run as script in isolation
    from file_ingestion import Document  # type: ignore

logger = logging.getLogger("ragchunker.embeddings")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO)


@dataclass
class EmbeddingResult:
    id: str
    vector: List[float]
    metadata: Dict[str, Any]


class EmbeddingClient:
    """
    Unified client for generating embeddings with pluggable backends.

    provider: "openai" or "sentence-transformers"
    model: model name string for the chosen provider
    device: for sentence-transformers (e.g., 'cpu' or 'cuda')
    batch_size: default batching for provider
    """

    def __init__(
        self,
        provider: str = "sentence-transformers",
        model: Optional[str] = None,
        device: str = "cpu",
        batch_size: int = 32,
        openai_api_key: Optional[str] = None,
    ):
        self.provider = provider.lower()
        self.batch_size = int(batch_size)
        self.device = device

        if self.provider == "openai":
            if openai is None:
                raise ImportError("openai library is required for OpenAI embeddings. Install: pip install openai")
            # choose default model if none provided
            self.model = model or os.environ.get("OPENAI_EMBEDDING_MODEL") or "text-embedding-3-small"
            # configure API key
            key = openai_api_key or os.environ.get("OPENAI_API_KEY")
            if not key:
                raise ValueError("OPENAI_API_KEY environment variable or openai_api_key argument is required for OpenAI provider")
            openai.api_key = key

        elif self.provider == "sentence-transformers":
            # default local model
            self.model = model or "all-MiniLM-L6-v2"
            if SentenceTransformer is None:
                raise ImportError("sentence-transformers is required for local embeddings. Install: pip install sentence-transformers")
            # load model (deferred until first use to avoid long import on init if not needed)
            self._st_model: Optional[SentenceTransformer] = None

        else:
            raise ValueError("Unsupported provider. Choose 'openai' or 'sentence-transformers'")

    # -------------------------
    # Internal helpers
    # -------------------------
    def _ensure_st_model(self):
        if getattr(self, "_st_model", None) is None:
            logger.info("Loading SentenceTransformer model: %s (device=%s)", self.model, self.device)
            self._st_model = SentenceTransformer(self.model, device=self.device)

    # -------------------------
    # Public embed methods
    # -------------------------
    def embed_texts(self, texts: Iterable[str], show_progress: bool = False) -> List[List[float]]:
        """
        Embed a list/iterable of texts and return list of vector lists (float).
        """

        texts_list = list(texts)
        n = len(texts_list)
        if n == 0:
            return []

        if self.provider == "sentence-transformers":
            self._ensure_st_model()
            # encode in batches
            all_vecs = []
            for i in range(0, n, self.batch_size):
                batch = texts_list[i : i + self.batch_size]
                vecs = self._st_model.encode(batch, show_progress_bar=False, convert_to_numpy=True)
                # ensure 2D
                vecs = np.array(vecs)
                for v in vecs:
                    all_vecs.append(v.astype(float).tolist())
            return all_vecs

        elif self.provider == "openai":
            if openai is None:
                raise ImportError("openai package not installed.")
            all_vecs = []
            for i in range(0, n, self.batch_size):
                batch = texts_list[i : i + self.batch_size]
                try:
                    # Updated for OpenAI Python >=1.0.0
                    resp = openai.embeddings.create(model=self.model, input=batch)
                except Exception as e:
                    logger.exception("OpenAI embedding request failed: %s", e)
                    time.sleep(1.0)
                    resp = openai.embeddings.create(model=self.model, input=batch)
                # resp.data is aligned with batch
                for item in resp.data:
                    vec = item.embedding
                    all_vecs.append([float(x) for x in vec])
            return all_vecs


        else:
            raise RuntimeError("Unsupported provider configured")

    def embed_documents(self, docs: List[Document], text_getter: Optional[Any] = None) -> List[EmbeddingResult]:
        """
        Given a list of Document objects, return a list of EmbeddingResult(id, vector, metadata).
        text_getter: optional callable(doc) -> str to extract text from a Document (defaults to doc.content)
        """
        if not docs:
            return []

        getter = text_getter or (lambda d: d.content or "")
        texts = [getter(d) for d in docs]
        vectors = self.embed_texts(texts)

        results = []
        for doc, vec in zip(docs, vectors):
            results.append(EmbeddingResult(id=doc.id, vector=vec, metadata=dict(doc.metadata or {})))
        return results

    # -------------------------
    # Helpers for vector stores
    # -------------------------
    @staticmethod
    def format_for_vectorstore(embeddings: List[EmbeddingResult]) -> List[Dict[str, Any]]:
        """
        Convert list of EmbeddingResult to vector-store-friendly dicts:
        [{'id': id, 'vector': [...], 'metadata': {...}}, ...]
        """
        out = []
        for e in embeddings:
            out.append({"id": e.id, "vector": e.vector, "metadata": e.metadata or {}})
        return out

    # -------------------------
    # Simple FAISS helpers (optional)
    # -------------------------
    def build_faiss_index(self, embeddings: List[EmbeddingResult], metric: str = "inner_product") -> Tuple[Any, List[str]]:
        """
        Build a simple FAISS index from embeddings.
        Returns (index, id_order_list)
        - metric: 'inner_product' (dot) or 'l2'
        Note: FAISS must be installed for this to work.
        """
        if faiss is None:
            raise ImportError("faiss is required for FAISS helpers. Install faiss (cpu) via: pip install faiss-cpu")

        if not embeddings:
            raise ValueError("No embeddings provided")

        # convert to numpy matrix
        vecs = np.array([e.vector for e in embeddings]).astype("float32")
        dim = vecs.shape[1]

        if metric == "inner_product":
            index = faiss.IndexFlatIP(dim)
            # normalize for IP to behave like cosine if desired (user can normalize externally)
        elif metric == "l2":
            index = faiss.IndexFlatL2(dim)
        else:
            raise ValueError("Unsupported metric. Use 'inner_product' or 'l2'")

        index.add(vecs)
        ids = [e.id for e in embeddings]
        return index, ids

    @staticmethod
    def faiss_search(index: Any, ids: List[str], query_vectors: List[List[float]], top_k: int = 4) -> List[List[Tuple[str, float]]]:
        """
        Search FAISS index with query_vectors. Returns list per query of (id, score) tuples.
        ids: list mapping index positions -> external ids
        """
        if faiss is None:
            raise ImportError("faiss is required for FAISS helpers. Install faiss-cpu")

        q = np.array(query_vectors).astype("float32")
        # Handle metrics automatically by index type (we assume index uses appropriate metric)
        D, I = index.search(q, top_k)  # D: distances/scores, I: indices
        results = []
        for row_scores, row_idx in zip(D.tolist(), I.tolist()):
            row = []
            for idx_pos, score in zip(row_idx, row_scores):
                if idx_pos < 0:
                    continue
                external_id = ids[idx_pos]
                row.append((external_id, float(score)))
            results.append(row)
        return results


# -------------------------
# Simple usage examples (do not run on import; for docs)
# -------------------------
def _example_openai_usage():
    """
    Example (OpenAI): requires OPENAI_API_KEY env var set.
    """
    client = EmbeddingClient(provider="openai", model="text-embedding-3-small", batch_size=16)
    texts = ["Hello world", "This is a test", "Another sentence"]
    vectors = client.embed_texts(texts)
    print("Vectors:", len(vectors), len(vectors[0]))


def _example_sentence_transformers_usage():
    client = EmbeddingClient(provider="sentence-transformers", model="all-MiniLM-L6-v2", device="cpu", batch_size=64)
    texts = ["Hello world", "This is a test", "Another sentence"]
    vectors = client.embed_texts(texts)
    print("Vectors:", len(vectors), len(vectors[0]))


# End of file
