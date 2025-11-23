# src/film_gap/nlp/embeddings.py

from __future__ import annotations

from sentence_transformers import SentenceTransformer
import numpy as np


# Load MiniLM once at import time
_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")


def embed_text(text: str) -> np.ndarray:
    """
    Embed text using MiniLM (returns 384-dim numpy array).
    Returns a zero-vector for empty text.
    """
    if not text or not text.strip():
        return np.zeros(384, dtype=float)

    emb = _model.encode(text, convert_to_numpy=True)
    return emb.astype(float)


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """
    Return cosine similarity between two vectors in [-1, 1].
    """
    if a.shape != b.shape or a.size == 0:
        return 0.0

    denom = np.linalg.norm(a) * np.linalg.norm(b)
    if denom == 0:
        return 0.0

    return float(np.dot(a, b) / denom)
