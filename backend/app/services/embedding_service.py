from __future__ import annotations

import hashlib
import math
import re
from collections.abc import Iterable

from langchain_openai import OpenAIEmbeddings

from app.core.config import settings


class EmbeddingService:
    """OpenAI-compatible embedding wrapper with deterministic local fallback."""

    def __init__(self) -> None:
        self.provider = settings.EMBEDDING_PROVIDER
        self.api_key = settings.EMBEDDING_API_KEY or settings.OPENAI_API_KEY
        self.base_url = settings.EMBEDDING_API_BASE or settings.OPENAI_API_BASE
        self.model_name = settings.EMBEDDING_MODEL_NAME
        self.dimensions = settings.EMBEDDING_DIMENSIONS
        self.remote_enabled = settings.EMBEDDING_ENABLE_REMOTE

    def is_remote_available(self) -> bool:
        return bool(self.remote_enabled and self.api_key and self.api_key.strip())

    def _build_model(self) -> OpenAIEmbeddings:
        return OpenAIEmbeddings(
            model=self.model_name,
            api_key=self.api_key,
            base_url=self.base_url,
            dimensions=self.dimensions,
            # Non-OpenAI compatible services (DashScope/Qwen, BGE, ...) only accept
            # an array of strings. LangChain defaults to encoding the input with
            # tiktoken and sending token ids, which they reject with
            # "input must be an array of strings".
            check_embedding_ctx_length=False,
        )

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        if self.is_remote_available():
            try:
                embeddings = self._build_model().embed_documents(texts)
                return [normalize_vector(vector, self.dimensions) for vector in embeddings]
            except Exception as exc:
                print(f"Embedding remote call failed, fallback to local hashing: {exc}")
        return [hash_embedding(text, self.dimensions) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        if self.is_remote_available():
            try:
                return normalize_vector(self._build_model().embed_query(text), self.dimensions)
            except Exception as exc:
                print(f"Embedding query failed, fallback to local hashing: {exc}")
        return hash_embedding(text, self.dimensions)


def hash_embedding(text: str, dimensions: int) -> list[float]:
    """Deterministic embedding for local tests and no-key development."""
    vector = [0.0] * dimensions
    tokens = tokenize(text)
    if not tokens:
        return vector
    for token in tokens:
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        index = int.from_bytes(digest[:4], "big") % dimensions
        sign = 1.0 if digest[4] % 2 == 0 else -1.0
        vector[index] += sign
    return l2_normalize(vector)


def tokenize(text: str) -> list[str]:
    words = re.findall(r"[A-Za-z0-9_+#.-]+|[\u4e00-\u9fff]", text.lower())
    return [word for word in words if word.strip()]


def normalize_vector(vector: Iterable[float], dimensions: int) -> list[float]:
    values = [float(item) for item in vector]
    if len(values) > dimensions:
        values = values[:dimensions]
    elif len(values) < dimensions:
        values.extend([0.0] * (dimensions - len(values)))
    return l2_normalize(values)


def l2_normalize(vector: list[float]) -> list[float]:
    norm = math.sqrt(sum(value * value for value in vector))
    if norm == 0:
        return vector
    return [value / norm for value in vector]


embedding_service = EmbeddingService()


def get_embeddings(texts: list[str]) -> list[list[float]]:
    return embedding_service.embed_documents(texts)


def get_single_embedding(text: str) -> list[float]:
    return embedding_service.embed_query(text)
