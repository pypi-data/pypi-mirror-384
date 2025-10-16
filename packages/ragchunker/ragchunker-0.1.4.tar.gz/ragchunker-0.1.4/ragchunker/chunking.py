"""
chunking.py
------------
This module provides multiple chunking strategies for RAG preprocessing:
1. Fixed-length chunking (by tokens or characters)
2. Semantic chunking (by sentence meaning)
3. Recursive chunking (hierarchical by sections)

Author: Muhammad Usama
"""

import re
import nltk
from typing import List, Dict, Union
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
import numpy as np

# === Ensure Required NLTK Data ===
try:
    nltk.data.find("tokenizers/punkt")
    nltk.data.find("tokenizers/punkt_tab")
except LookupError:
    nltk.download("punkt")
    nltk.download("punkt_tab")

# === Core Class ===

class RAGChunker:
    def __init__(self, strategy: str = "fixed", chunk_size: int = 500, overlap: int = 50):
        """
        strategy: 'fixed', 'semantic', or 'recursive'
        chunk_size: number of tokens/chars per chunk
        overlap: how much overlap to keep between chunks (for fixed strategy)
        """
        self.strategy = strategy
        self.chunk_size = chunk_size
        self.overlap = overlap

        if strategy == "semantic":
            self.model = SentenceTransformer("all-MiniLM-L6-v2")

    # === Helper Functions ===
    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences using NLTK."""
        sentences = nltk.sent_tokenize(text)
        return [s.strip() for s in sentences if s.strip()]

    # === Fixed Chunking ===
    def chunk_fixed(self, text: str) -> List[str]:
        """Chunk text into fixed-length pieces (characters-based)."""
        chunks = []
        start = 0
        while start < len(text):
            end = min(start + self.chunk_size, len(text))
            chunks.append(text[start:end])
            start += self.chunk_size - self.overlap
        return chunks

    # === Semantic Chunking ===
    def chunk_semantic(self, text: str, similarity_threshold: float = 0.75) -> List[str]:
        """
        Group semantically related sentences into meaningful chunks using embeddings.
        """
        sentences = self._split_sentences(text)
        if not sentences:
            return []

        embeddings = self.model.encode(sentences)
        chunks = []
        current_chunk = [sentences[0]]

        for i in range(1, len(sentences)):
            sim = cosine_similarity(
                [embeddings[i - 1]], [embeddings[i]]
            )[0][0]
            if sim > similarity_threshold:
                current_chunk.append(sentences[i])
            else:
                chunks.append(" ".join(current_chunk))
                current_chunk = [sentences[i]]
        if current_chunk:
            chunks.append(" ".join(current_chunk))
        return chunks

    # === Recursive Chunking ===
    def chunk_recursive(self, text: str) -> List[str]:
        """
        Hierarchical splitting by section markers (#, ##, ###, etc.)
        Ideal for markdown or long structured docs.
        """
        pattern = r"(?m)^#+\s"
        sections = re.split(pattern, text)
        chunks = []
        for section in sections:
            section = section.strip()
            if not section:
                continue
            if len(section) > self.chunk_size:
                chunks.extend(self.chunk_fixed(section))
            else:
                chunks.append(section)
        return chunks

    # === Main Chunk Interface ===
    def chunk(self, data: Union[str, Dict, List]) -> List[str]:
        """
        Entry point for chunking any text or structured data.
        """
        text = str(data)
        if self.strategy == "fixed":
            return self.chunk_fixed(text)
        elif self.strategy == "semantic":
            return self.chunk_semantic(text)
        elif self.strategy == "recursive":
            return self.chunk_recursive(text)
        else:
            raise ValueError(f"Unknown strategy: {self.strategy}")
