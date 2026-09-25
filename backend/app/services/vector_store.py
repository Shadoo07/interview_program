from __future__ import annotations

import json
import math
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.knowledge_base import KnowledgeChunk


def is_postgres_enabled() -> bool:
    return settings.DATABASE_URL.startswith("postgresql")


def vector_literal(embedding: list[float]) -> str:
    return "[" + ",".join(f"{value:.8f}" for value in embedding) + "]"


class PgVectorStore:
    def __init__(self, db: Session):
        self.db = db
        self.dimensions = settings.EMBEDDING_DIMENSIONS

    def ensure_schema(self) -> None:
        self.db.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        self.db.execute(
            text(
                f"""
                CREATE TABLE IF NOT EXISTS knowledge_embeddings (
                    id SERIAL PRIMARY KEY,
                    chunk_id INTEGER NOT NULL UNIQUE REFERENCES knowledge_chunks(id) ON DELETE CASCADE,
                    document_id INTEGER NOT NULL REFERENCES knowledge_documents(id) ON DELETE CASCADE,
                    content_hash VARCHAR(64),
                    embedding vector({self.dimensions}) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
        )
        self.db.execute(
            text(
                """
                CREATE INDEX IF NOT EXISTS knowledge_embeddings_document_id_idx
                ON knowledge_embeddings (document_id)
                """
            )
        )
        try:
            self.db.execute(
                text(
                    """
                    CREATE INDEX IF NOT EXISTS knowledge_embeddings_embedding_hnsw_idx
                    ON knowledge_embeddings
                    USING hnsw (embedding vector_cosine_ops)
                    """
                )
            )
        except Exception as exc:
            print(f"Create pgvector HNSW index skipped: {exc}")
            self.db.rollback()
            self.db.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        self.db.commit()

    def upsert_embedding(
        self,
        chunk_id: int,
        document_id: int,
        embedding: list[float],
        content_hash: str,
    ) -> None:
        self.ensure_schema()
        self.db.execute(
            text(
                """
                INSERT INTO knowledge_embeddings (chunk_id, document_id, content_hash, embedding)
                VALUES (:chunk_id, :document_id, :content_hash, CAST(:embedding AS vector))
                ON CONFLICT (chunk_id) DO UPDATE SET
                    document_id = EXCLUDED.document_id,
                    content_hash = EXCLUDED.content_hash,
                    embedding = EXCLUDED.embedding
                """
            ),
            {
                "chunk_id": chunk_id,
                "document_id": document_id,
                "content_hash": content_hash,
                "embedding": vector_literal(embedding),
            },
        )

    def search(self, query_embedding: list[float], top_k: int = 5) -> list[dict[str, Any]]:
        self.ensure_schema()
        rows = self.db.execute(
            text(
                """
                SELECT chunk_id, document_id, 1 - (embedding <=> CAST(:embedding AS vector)) AS score
                FROM knowledge_embeddings
                ORDER BY embedding <=> CAST(:embedding AS vector)
                LIMIT :top_k
                """
            ),
            {"embedding": vector_literal(query_embedding), "top_k": top_k},
        ).mappings()
        return [dict(row) for row in rows]

    def delete_document(self, doc_id: int) -> None:
        self.ensure_schema()
        self.db.execute(text("DELETE FROM knowledge_embeddings WHERE document_id = :doc_id"), {"doc_id": doc_id})


class SqliteVectorStore:
    def __init__(self, db: Session):
        self.db = db

    def upsert_embedding(
        self,
        chunk_id: int,
        document_id: int,
        embedding: list[float],
        content_hash: str,
    ) -> None:
        chunk = self.db.query(KnowledgeChunk).filter(KnowledgeChunk.id == chunk_id).first()
        if chunk:
            chunk.embedding = json.dumps({"vector": embedding, "content_hash": content_hash}, ensure_ascii=False)

    def search(self, query_embedding: list[float], top_k: int = 5) -> list[dict[str, Any]]:
        results = []
        chunks = self.db.query(KnowledgeChunk).filter(KnowledgeChunk.embedding.isnot(None)).all()
        for chunk in chunks:
            embedding = read_embedding(chunk.embedding)
            if not embedding:
                continue
            score = cosine_similarity(query_embedding, embedding)
            results.append({"chunk_id": chunk.id, "document_id": chunk.document_id, "score": score})
        results.sort(key=lambda item: item["score"], reverse=True)
        return results[:top_k]

    def delete_document(self, doc_id: int) -> None:
        return None


def get_vector_store(db: Session) -> PgVectorStore | SqliteVectorStore:
    return PgVectorStore(db) if is_postgres_enabled() else SqliteVectorStore(db)


def read_embedding(raw: str | None) -> list[float]:
    if not raw:
        return []
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return []
    if isinstance(data, dict):
        data = data.get("vector", [])
    if not isinstance(data, list):
        return []
    return [float(item) for item in data]


def cosine_similarity(left: list[float], right: list[float]) -> float:
    if not left or not right:
        return 0.0
    size = min(len(left), len(right))
    dot = sum(left[index] * right[index] for index in range(size))
    left_norm = math.sqrt(sum(value * value for value in left[:size]))
    right_norm = math.sqrt(sum(value * value for value in right[:size]))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return dot / (left_norm * right_norm)
