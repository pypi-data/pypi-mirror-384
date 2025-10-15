from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from typing import Iterable, List, Sequence
from urllib import request

import numpy as np

from code_graph_rag_mcp.config.models import EmbedConfig

EMBED_ENDPOINT_ENV = "CODE_GRAPH_RAG_EMBED_ENDPOINT"


@dataclass(slots=True)
class EmbeddingResult:
    vectors: np.ndarray
    model: str


class EmbeddingError(RuntimeError):
    pass


class EmbeddingClient:
    """Wrapper around EmbeddingGemma with local CPU fallback."""

    def __init__(self, config: EmbedConfig | None = None) -> None:
        self.config = config or EmbedConfig()
        self.endpoint = os.environ.get(EMBED_ENDPOINT_ENV) or self.config.endpoint
        if self.endpoint:
            self._backend = _RemoteEmbeddingBackend(self.endpoint, self.config)
        else:
            self._backend = _LocalEmbeddingBackend(self.config)

    def embed(self, texts: Sequence[str]) -> EmbeddingResult:
        if not texts:
            raise EmbeddingError("No texts provided for embedding")
        vectors = self._backend.embed(texts)
        return EmbeddingResult(vectors=vectors, model=self.config.model)


class _LocalEmbeddingBackend:
    def __init__(self, config: EmbedConfig) -> None:
        self.config = config
        self.dim = config.dim

    def embed(self, texts: Sequence[str]) -> np.ndarray:
        vectors = np.vstack([self._hash_to_vec(text) for text in texts])
        return vectors.astype(np.float32)

    def _hash_to_vec(self, text: str) -> np.ndarray:
        # Deterministic pseudo-embedding as a placeholder until the real model is integrated.
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        repeats = (self.dim + len(digest) - 1) // len(digest)
        data = (digest * repeats)[: self.dim]
        vec = np.frombuffer(data, dtype=np.uint8).astype(np.float32)
        norm = np.linalg.norm(vec) or 1.0
        return vec / norm


class _RemoteEmbeddingBackend:
    def __init__(self, endpoint: str, config: EmbedConfig) -> None:
        self.endpoint = endpoint
        self.config = config

    def embed(self, texts: Sequence[str]) -> np.ndarray:
        payload = json.dumps({
            "model": self.config.model,
            "texts": list(texts),
        }).encode("utf-8")
        http_request = request.Request(
            self.endpoint,
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        try:
            with request.urlopen(http_request) as response:
                body = response.read()
        except Exception as exc:  # pragma: no cover - network failure path
            raise EmbeddingError(f"Failed to fetch embeddings from {self.endpoint}: {exc}") from exc

        data = json.loads(body.decode("utf-8"))
        vectors = np.asarray(data.get("vectors"))
        if vectors.ndim == 1:
            vectors = np.expand_dims(vectors, axis=0)
        if vectors.shape[1] != self.config.dim:
            raise EmbeddingError(
                f"Expected dimension {self.config.dim} from remote endpoint, got {vectors.shape[1]}"
            )
        return vectors.astype(np.float32)


__all__ = ["EmbeddingClient", "EmbeddingResult", "EmbeddingError", "EMBED_ENDPOINT_ENV"]
