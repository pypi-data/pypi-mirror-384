# ragchunker/provenance.py
"""
Metadata & Provenance Layer for ragchunker

Features:
- Compute file checksum (SHA256)
- Token counting (tiktoken optional, fallback to whitespace)
- Language detection (langdetect optional)
- Convert chunk texts into Document dataclass instances with rich metadata
- Serialize/deserialize JSONL for indexed chunks

Integrates with:
- Document dataclass from ragchunker.file_ingestion
- Chunk texts produced by your chunking module
"""

from __future__ import annotations
import os
import io
import json
import uuid
import hashlib
import logging
from datetime import datetime
from typing import List, Dict, Optional, Any, Tuple

# Import Document from ingestion module
try:
    from ragchunker.file_ingestion import Document
except Exception:
    # For safety if running module directly or tests in isolation
    from file_ingestion import Document  # type: ignore

logger = logging.getLogger("ragchunker.provenance")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO)

# Try to import tiktoken for accurate token counts (optional)
try:
    import tiktoken

    TIKTOKEN_AVAILABLE = True
    # choose a safe default encoding (cl100k_base is common for OpenAI)
    try:
        _DEFAULT_ENCODING = tiktoken.get_encoding("cl100k_base")
    except Exception:
        try:
            _DEFAULT_ENCODING = tiktoken.encoding_for_model("gpt-4o")
        except Exception:
            _DEFAULT_ENCODING = None
except Exception:
    tiktoken = None
    TIKTOKEN_AVAILABLE = False
    _DEFAULT_ENCODING = None

# Optional language detector
try:
    from langdetect import detect as langdetect_detect

    LANGDETECT_AVAILABLE = True
except Exception:
    langdetect_detect = None
    LANGDETECT_AVAILABLE = False


# --------------------------
# Utility functions
# --------------------------
def compute_file_sha256(path: str, chunk_size: int = 8 * 1024 * 1024) -> Optional[str]:
    """
    Compute SHA256 for a file. Returns hex digest or None if file not found.
    """
    if not path or not os.path.isfile(path):
        return None
    h = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            while True:
                data = f.read(chunk_size)
                if not data:
                    break
                h.update(data)
        return h.hexdigest()
    except Exception as e:
        logger.exception("Failed to compute SHA256 for %s: %s", path, e)
        return None


def count_tokens(text: str) -> int:
    """
    Return token estimate. Prefer tiktoken for accuracy if available.
    Falls back to whitespace token count as approximation.
    """
    if not text:
        return 0
    if TIKTOKEN_AVAILABLE and _DEFAULT_ENCODING is not None:
        try:
            return len(_DEFAULT_ENCODING.encode(text))
        except Exception:
            # fallback if encoding fails
            pass
    # fallback approximation
    return max(1, len(text.split()))


def safe_detect_language(text: str) -> Optional[str]:
    """
    Attempt language detection if langdetect installed. If not available or detection fails, returns None.
    """
    if not text or not LANGDETECT_AVAILABLE:
        return None
    try:
        lang = langdetect_detect(text)
        return lang
    except Exception:
        return None


def _generate_chunk_uuid(parent_id: str, idx: int) -> str:
    """
    Deterministic-ish chunk id using parent id + index + uuid4 suffix.
    """
    base = f"{parent_id}:{idx}"
    # short uuid for readability
    short = uuid.uuid4().hex[:8]
    return f"{base}:{short}"


# --------------------------
# Core Provenance functions
# --------------------------
def enrich_chunks_from_texts(
    parent_doc: Document,
    chunk_texts: List[str],
    strategy: Optional[str] = None,
    source_path: Optional[str] = None,
    compute_checksum: bool = True,
    include_language: bool = True,
) -> List[Document]:
    """
    Turn a list of chunk texts (strings) derived from parent_doc.content into
    Document objects with rich provenance metadata.

    Metadata added per chunk:
      - parent_id: original Document.id
      - parent_source: parent_doc.metadata.get('source') or source_path
      - chunk_index: integer index (0-based)
      - chunk_id: generated id
      - char_start, char_end: character range in parent text if mappable (may be approximate)
      - token_count: estimated token count
      - checksum: file checksum for parent source (if available & compute_checksum True)
      - created_at: ISO timestamp
      - strategy: provided strategy string (e.g., "semantic", "fixed")
      - language: detected language code (if langdetect available)
    """
    chunks_out: List[Document] = []
    parent_text = (parent_doc.content or "").strip()
    parent_len = len(parent_text)
    source = source_path or parent_doc.metadata.get("source")
    checksum = None
    if compute_checksum and source and isinstance(source, str) and os.path.isfile(source):
        checksum = compute_file_sha256(source)

    # We'll try to map each chunk to a char range in parent text using an advancing cursor.
    cursor = 0

    for idx, ctext in enumerate(chunk_texts):
        if ctext is None:
            ctext = ""
        ctext = ctext.strip()
        chunk_id = _generate_chunk_uuid(parent_doc.id, idx)
        # attempt to find exact substring starting from cursor
        char_start = None
        char_end = None
        if parent_text and ctext:
            # find the first occurrence >= cursor
            found = parent_text.find(ctext, cursor)
            if found != -1:
                char_start = found
                char_end = found + len(ctext)
                cursor = char_end  # advance cursor
            else:
                # fallback: approximate placement using cursor
                char_start = cursor
                char_end = cursor + len(ctext)
                cursor = char_end
                # but clamp to parent_len
                if char_start > parent_len:
                    char_start = parent_len
                if char_end > parent_len:
                    char_end = parent_len

        token_count = count_tokens(ctext)
        language = safe_detect_language(ctext) if include_language else None

        metadata: Dict[str, Any] = dict(parent_id=parent_doc.id,
                                       parent_source=source,
                                       chunk_index=idx,
                                       chunk_id=chunk_id,
                                       token_count=token_count,
                                       created_at=datetime.utcnow().isoformat() + "Z",
                                       strategy=strategy or parent_doc.metadata.get("strategy"),
                                       checksum=checksum,
                                       language=language)

        if char_start is not None:
            metadata["char_start"] = int(char_start)
            metadata["char_end"] = int(char_end)

        # preserve any original metadata that seems useful (page, slide, row, etc.)
        for k in ("page", "slide_index", "row_index", "sheet", "timestamp"):
            if k in parent_doc.metadata:
                metadata.setdefault(k, parent_doc.metadata.get(k))

        chunks_out.append(Document(content=ctext, metadata=metadata))

    return chunks_out


def attach_provenance_to_documents(
    docs: List[Document],
    project: Optional[str] = None,
    dataset: Optional[str] = None,
    run_id: Optional[str] = None,
    compute_checksums: bool = True,
) -> List[Document]:
    """
    Add/normalize top-level provenance fields to each Document in `docs`.
    This mutates a copy of docs and returns it.
    Fields added:
      - project, dataset, run_id
      - ingested_at
      - if doc.metadata has 'source' and compute_checksums True, adds 'checksum'
    """
    out: List[Document] = []
    resolved_run_id = run_id or uuid.uuid4().hex
    for d in docs:
        meta = dict(d.metadata) if d.metadata else {}
        meta.setdefault("project", project)
        meta.setdefault("dataset", dataset)
        meta.setdefault("run_id", resolved_run_id)
        meta.setdefault("ingested_at", datetime.utcnow().isoformat() + "Z")
        source = meta.get("source")
        if compute_checksums and source and isinstance(source, str) and os.path.isfile(source):
            meta.setdefault("checksum", compute_file_sha256(source))
        out.append(Document(id=d.id, content=d.content, metadata=meta))
    return out


# --------------------------
# Serialization helpers
# --------------------------
def _document_to_jsonable(doc: Document) -> Dict[str, Any]:
    return {
        "id": doc.id,
        "content": doc.content,
        "metadata": doc.metadata or {},
    }


def serialize_documents_to_jsonl(docs: List[Document], out_path: str) -> str:
    """
    Write documents to JSONL. Returns path written.
    """
    try:
        os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            for d in docs:
                f.write(json.dumps(_document_to_jsonable(d), ensure_ascii=False) + "\n")
        logger.info("Wrote %d documents to %s", len(docs), out_path)
        return out_path
    except Exception as e:
        logger.exception("Failed to write JSONL to %s: %s", out_path, e)
        raise


def load_documents_from_jsonl(path: str) -> List[Document]:
    """
    Load JSONL into Document objects (inverse of serialize).
    """
    if not os.path.isfile(path):
        raise FileNotFoundError(path)
    out: List[Document] = []
    with open(path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            try:
                obj = json.loads(line)
                doc_id = obj.get("id") or uuid.uuid4().hex
                content = obj.get("content", "")
                metadata = obj.get("metadata", {}) or {}
                out.append(Document(id=doc_id, content=content, metadata=metadata))
            except Exception as e:
                logger.exception("Failed to parse line %d in %s: %s", i + 1, path, e)
    return out


# --------------------------
# Small utilities
# --------------------------
def merge_adjacent_small_chunks(docs: List[Document], min_tokens: int = 16) -> List[Document]:
    """
    Merge adjacent chunks if they are too small (measured by token count).
    Returns a new list of Documents.
    """
    if not docs:
        return []
    merged: List[Document] = []
    buffer_doc = None
    for d in docs:
        tokens = count_tokens(d.content or "")
        if buffer_doc is None:
            buffer_doc = Document(id=d.id, content=d.content or "", metadata=dict(d.metadata or {}))
            continue
        if tokens < min_tokens:
            # merge into buffer
            buffer_doc.content = (buffer_doc.content or "") + "\n\n" + (d.content or "")
            # merge metadata: keep earliest created_at
            try:
                ca_buf = buffer_doc.metadata.get("created_at")
                ca_new = d.metadata.get("created_at")
                if ca_new and (not ca_buf or ca_new < ca_buf):
                    buffer_doc.metadata["created_at"] = ca_new
            except Exception:
                pass
        else:
            # flush buffer and start new
            merged.append(buffer_doc)
            buffer_doc = Document(id=d.id, content=d.content or "", metadata=dict(d.metadata or {}))
    if buffer_doc is not None:
        merged.append(buffer_doc)
    return merged
