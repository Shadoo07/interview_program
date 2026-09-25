from __future__ import annotations

import hashlib
import json
import os
from collections import OrderedDict
from typing import Any

from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

from app.models.knowledge_base import KnowledgeChunk, KnowledgeDocument
from app.schemas.knowledge_schema import KnowledgeSearchResult, KnowledgeVersionSummary
from app.services.embedding_service import get_embeddings, get_single_embedding
from app.services.rerank_service import RerankOptions, rerank_results
from app.services.vector_store import get_vector_store, is_postgres_enabled
from app.utils.knowledge_utils import (
    get_file_type,
    parse_document,
    save_uploaded_file,
    split_text_into_semantic_chunks,
)

UPLOAD_DIR = "uploads/knowledge"


class KnowledgeIngestError(RuntimeError):
    """Raised when a knowledge document fails to ingest (parse / chunk / embed / persist)."""


def upload_knowledge_document(
    db: Session,
    file_bytes: bytes,
    filename: str,
    metadata: dict[str, Any] | None = None,
) -> KnowledgeDocument:
    """Upload, chunk, embed, and index a knowledge document."""
    ensure_knowledge_schema(db)
    metadata = metadata or {}
    file_type = get_file_type(filename)
    file_path, saved_filename = save_uploaded_file(file_bytes, filename, UPLOAD_DIR)

    try:
        content = parse_document(file_path, file_type)
        chunks = split_text_into_semantic_chunks(content)
        content_hash = sha256_text(content)

        doc = KnowledgeDocument(
            filename=saved_filename,
            file_type=file_type,
            file_path=file_path,
            total_chunks=len(chunks),
            source_type=metadata.get("source_type", "general"),
            tags=json.dumps(metadata.get("tags", []), ensure_ascii=False),
            role_family=metadata.get("role_family", ""),
            version=metadata.get("version", "v1"),
            status=metadata.get("status", "published"),
            content_hash=content_hash,
        )
        db.add(doc)
        db.flush()

        chunk_texts = [chunk.content for chunk in chunks]
        embeddings = get_embeddings(chunk_texts)
        vector_store = get_vector_store(db)
        for idx, text_chunk in enumerate(chunks):
            chunk_hash = sha256_text(text_chunk.content)
            chunk = KnowledgeChunk(
                document_id=doc.id,
                content=text_chunk.content,
                chunk_index=idx,
                content_hash=chunk_hash,
                section_title=text_chunk.section_title,
                char_start=text_chunk.char_start,
                char_end=text_chunk.char_end,
                token_count=text_chunk.token_count,
            )
            db.add(chunk)
            db.flush()
            if idx < len(embeddings):
                vector_store.upsert_embedding(chunk.id, doc.id, embeddings[idx], chunk_hash)

        db.commit()
        db.refresh(doc)
        return doc
    except Exception as exc:
        db.rollback()
        if os.path.exists(file_path):
            os.remove(file_path)
        raise KnowledgeIngestError(f"Document processing failed: {exc}") from exc


def get_knowledge_documents(db: Session) -> list[KnowledgeDocument]:
    ensure_knowledge_schema(db)
    return db.query(KnowledgeDocument).order_by(KnowledgeDocument.created_at.desc()).all()


def get_knowledge_versions(db: Session) -> list[KnowledgeVersionSummary]:
    ensure_knowledge_schema(db)
    docs = db.query(KnowledgeDocument).all()
    grouped: dict[tuple[str, str, str, str], KnowledgeVersionSummary] = {}
    for doc in docs:
        key = (
            doc.version or "v1",
            doc.source_type or "general",
            doc.role_family or "",
            doc.status or "published",
        )
        item = grouped.get(key)
        if item is None:
            item = KnowledgeVersionSummary(
                version=key[0],
                source_type=key[1],
                role_family=key[2],
                status=key[3],
                document_count=0,
                chunk_count=0,
                latest_created_at=doc.created_at,
            )
            grouped[key] = item
        item.document_count += 1
        item.chunk_count += int(doc.total_chunks or 0)
        if doc.created_at and (item.latest_created_at is None or doc.created_at > item.latest_created_at):
            item.latest_created_at = doc.created_at
    return sorted(grouped.values(), key=lambda item: item.latest_created_at or "", reverse=True)


def update_knowledge_document_metadata(
    db: Session,
    doc_id: int,
    metadata: dict[str, Any],
) -> KnowledgeDocument | None:
    ensure_knowledge_schema(db)
    doc = db.query(KnowledgeDocument).filter(KnowledgeDocument.id == doc_id).first()
    if not doc:
        return None

    for field_name in ["source_type", "role_family", "version", "status"]:
        if metadata.get(field_name) is not None:
            setattr(doc, field_name, str(metadata[field_name]))
    if metadata.get("tags") is not None:
        doc.tags = json.dumps(metadata["tags"], ensure_ascii=False)
    db.commit()
    db.refresh(doc)
    return doc


def delete_knowledge_document(db: Session, doc_id: int) -> bool:
    ensure_knowledge_schema(db)
    doc = db.query(KnowledgeDocument).filter(KnowledgeDocument.id == doc_id).first()
    if not doc:
        return False

    vector_store = get_vector_store(db)
    vector_store.delete_document(doc_id)

    if doc.file_path and os.path.exists(doc.file_path):
        try:
            os.remove(doc.file_path)
        except OSError as exc:
            print(f"Failed to remove knowledge file {doc.file_path}: {exc}")

    db.delete(doc)
    db.commit()
    return True


def search_knowledge_by_keyword(
    db: Session,
    keyword: str,
    top_k: int = 5,
    use_vector: bool = True,
    rerank: bool = True,
    role_family: str = "",
    version: str = "",
) -> list[KnowledgeSearchResult]:
    ensure_knowledge_schema(db)
    candidates: list[KnowledgeSearchResult] = []
    if use_vector:
        candidates.extend(search_knowledge_by_vector(db, keyword, top_k * 4, role_family=role_family, version=version))
    candidates.extend(search_knowledge_by_text(db, keyword, top_k * 4, role_family=role_family, version=version))

    merged = merge_results(candidates)
    if rerank:
        merged = rerank_results(keyword, merged, RerankOptions(role_family=role_family, version=version))
    else:
        merged.sort(key=lambda item: item.score, reverse=True)
    return merged[:top_k]


def search_knowledge_by_vector(
    db: Session,
    query: str,
    top_k: int = 5,
    role_family: str = "",
    version: str = "",
) -> list[KnowledgeSearchResult]:
    query_embedding = get_single_embedding(query)
    if not query_embedding:
        return []

    vector_store = get_vector_store(db)
    try:
        matches = vector_store.search(query_embedding, top_k)
    except Exception as exc:
        print(f"Vector search failed, fallback to keyword search: {exc}")
        return []

    chunk_ids = [int(item["chunk_id"]) for item in matches]
    if not chunk_ids:
        return []
    chunks_query = db.query(KnowledgeChunk).filter(KnowledgeChunk.id.in_(chunk_ids))
    chunks = filter_chunk_query(chunks_query, role_family=role_family, version=version).all()
    chunk_map = {chunk.id: chunk for chunk in chunks}
    results = []
    for item in matches:
        chunk = chunk_map.get(int(item["chunk_id"]))
        if not chunk:
            continue
        results.append(to_search_result(chunk, float(item.get("score", 0))))
    return results[:top_k]


def search_knowledge_by_text(
    db: Session,
    keyword: str,
    top_k: int = 5,
    role_family: str = "",
    version: str = "",
) -> list[KnowledgeSearchResult]:
    results = []
    chunks_query = db.query(KnowledgeChunk)
    chunks_query = filter_chunk_query(chunks_query, role_family=role_family, version=version)
    chunks_query = apply_text_filters(chunks_query, keyword)
    chunks = chunks_query.order_by(KnowledgeChunk.created_at.desc()).limit(top_k).all()
    for chunk in chunks:
        results.append(to_search_result(chunk, calculate_keyword_score(chunk.content, keyword)))
    results.sort(key=lambda item: item.score, reverse=True)
    return results[:top_k]


def merge_results(results: list[KnowledgeSearchResult]) -> list[KnowledgeSearchResult]:
    merged: OrderedDict[int, KnowledgeSearchResult] = OrderedDict()
    for item in results:
        existing = merged.get(item.chunk_id)
        if existing is None or item.score > existing.score:
            merged[item.chunk_id] = item
    return list(merged.values())


def filter_chunk_query(query, role_family: str = "", version: str = ""):
    query = query.join(KnowledgeDocument)
    query = query.filter(KnowledgeDocument.status == "published")
    if role_family:
        query = query.filter(KnowledgeDocument.role_family == role_family)
    if version:
        query = query.filter(KnowledgeDocument.version == version)
    return query


def apply_text_filters(query, keyword: str):
    tokens = extract_search_terms(keyword)
    if not tokens:
        return query
    conditions = [KnowledgeChunk.content.like(f"%{token}%") for token in tokens[:12]]
    return query.filter(conditions[0] if len(conditions) == 1 else text_or_conditions(conditions))


def text_or_conditions(conditions):
    from sqlalchemy import or_

    return or_(*conditions)


def to_search_result(chunk: KnowledgeChunk, score: float) -> KnowledgeSearchResult:
    doc = chunk.document
    citation = build_citation(doc, chunk)
    return KnowledgeSearchResult(
        chunk_id=chunk.id,
        document_id=chunk.document_id,
        document_name=doc.filename,
        chunk_index=chunk.chunk_index,
        section_title=chunk.section_title or "",
        content=chunk.content,
        score=round(float(score), 4),
        retrieval_score=round(float(score), 4),
        rerank_score=0,
        citation=citation,
        source_type=doc.source_type or "general",
        tags=parse_tags(doc.tags),
        role_family=doc.role_family or "",
        version=doc.version or "v1",
        status=doc.status or "published",
        content_hash=chunk.content_hash or "",
    )


def calculate_keyword_score(text_value: str, keyword: str) -> float:
    text_lower = text_value.lower()
    terms = extract_search_terms(keyword)
    if not terms:
        return 0.0
    matched = 0
    weighted = 0.0
    for term in terms:
        count = text_lower.count(term.lower())
        if count:
            matched += 1
            weighted += min(count, 3) * min(len(term) / 8, 1)
    coverage = matched / len(terms)
    density = weighted / max(len(terms), 1)
    return min(1.0, 0.75 * coverage + 0.25 * density)


def extract_search_terms(keyword: str) -> list[str]:
    import re

    terms = re.findall(r"[A-Za-z0-9_+#.-]+|[\u4e00-\u9fff]{2,}", keyword.lower())
    stop_words = {"岗位", "要求", "能力", "熟悉", "负责", "项目", "经验", "相关"}
    return [term for term in terms if term not in stop_words][:40]


def build_citation(doc: KnowledgeDocument, chunk: KnowledgeChunk) -> str:
    section = chunk.section_title or "main"
    if section == "正文":
        section = "main"
    return f"{doc.filename} | section={section} | chunk={chunk.chunk_index + 1} | version={doc.version or 'v1'}"


def ensure_knowledge_schema(db: Session) -> None:
    """Add metadata columns for older local SQLite/Postgres databases."""
    inspector = inspect(db.bind)
    table_names = set(inspector.get_table_names())
    if "knowledge_documents" not in table_names or "knowledge_chunks" not in table_names:
        return

    doc_columns = {column["name"] for column in inspector.get_columns("knowledge_documents")}
    chunk_columns = {column["name"] for column in inspector.get_columns("knowledge_chunks")}
    doc_additions = {
        "source_type": "VARCHAR(50) DEFAULT 'general'",
        "tags": "TEXT DEFAULT '[]'",
        "role_family": "VARCHAR(50) DEFAULT ''",
        "version": "VARCHAR(50) DEFAULT 'v1'",
        "status": "VARCHAR(30) DEFAULT 'published'",
        "content_hash": "VARCHAR(64) DEFAULT ''",
    }
    chunk_additions = {
        "content_hash": "VARCHAR(64) DEFAULT ''",
        "section_title": "VARCHAR(255) DEFAULT ''",
        "char_start": "INTEGER DEFAULT 0",
        "char_end": "INTEGER DEFAULT 0",
        "token_count": "INTEGER DEFAULT 0",
    }

    for name, definition in doc_additions.items():
        if name not in doc_columns:
            db.execute(text(f"ALTER TABLE knowledge_documents ADD COLUMN {name} {definition}"))
    for name, definition in chunk_additions.items():
        if name not in chunk_columns:
            db.execute(text(f"ALTER TABLE knowledge_chunks ADD COLUMN {name} {definition}"))
    db.commit()

    if is_postgres_enabled():
        vector_store = get_vector_store(db)
        vector_store.ensure_schema()


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def parse_tags(raw: str | None) -> list[str]:
    if not raw:
        return []
    try:
        value = json.loads(raw)
    except json.JSONDecodeError:
        return []
    if not isinstance(value, list):
        return []
    return [str(item) for item in value]
