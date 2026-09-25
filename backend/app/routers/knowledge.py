from __future__ import annotations

import json

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.knowledge_schema import (
    KnowledgeDeleteResponse,
    KnowledgeDocumentResponse,
    KnowledgeListResponse,
    KnowledgeMetadataUpdateRequest,
    KnowledgeSearchRequest,
    KnowledgeSearchResponse,
    KnowledgeUploadResponse,
    KnowledgeVersionListResponse,
)
from app.services.knowledge_service import (
    delete_knowledge_document,
    get_knowledge_documents,
    get_knowledge_versions,
    parse_tags,
    search_knowledge_by_keyword,
    update_knowledge_document_metadata,
    upload_knowledge_document,
)

router = APIRouter(tags=["Knowledge"])


@router.post("/upload", response_model=KnowledgeUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    source_type: str = Form("general"),
    tags: str = Form("[]"),
    role_family: str = Form(""),
    version: str = Form("v1"),
    status: str = Form("published"),
    db: Session = Depends(get_db),
):
    """Upload a knowledge document with optional metadata."""
    try:
        file_bytes = await file.read()
        metadata = {
            "source_type": source_type,
            "tags": parse_tags_input(tags),
            "role_family": role_family,
            "version": version,
            "status": status,
        }
        doc = upload_knowledge_document(db, file_bytes, file.filename or "knowledge.txt", metadata)
        return KnowledgeUploadResponse(code=200, data=to_document_response(doc))
    except Exception as exc:
        return KnowledgeUploadResponse(code=500, message=str(exc))


@router.get("/list", response_model=KnowledgeListResponse)
async def list_documents(db: Session = Depends(get_db)):
    """List knowledge documents."""
    try:
        docs = get_knowledge_documents(db)
        return KnowledgeListResponse(code=200, data=[to_document_response(doc) for doc in docs])
    except Exception as exc:
        return KnowledgeListResponse(code=500, message=str(exc))


@router.get("/versions", response_model=KnowledgeVersionListResponse)
async def list_versions(db: Session = Depends(get_db)):
    """List knowledge version groups."""
    try:
        return KnowledgeVersionListResponse(code=200, data=get_knowledge_versions(db))
    except Exception as exc:
        return KnowledgeVersionListResponse(code=500, message=str(exc))


@router.patch("/{doc_id}", response_model=KnowledgeUploadResponse)
async def update_document_metadata(
    doc_id: int,
    request: KnowledgeMetadataUpdateRequest,
    db: Session = Depends(get_db),
):
    """Update document metadata, including version and review status."""
    try:
        doc = update_knowledge_document_metadata(db, doc_id, request.model_dump(exclude_unset=True))
        if not doc:
            return KnowledgeUploadResponse(code=404, message="Document not found")
        return KnowledgeUploadResponse(code=200, data=to_document_response(doc))
    except Exception as exc:
        return KnowledgeUploadResponse(code=500, message=str(exc))


@router.delete("/{doc_id}", response_model=KnowledgeDeleteResponse)
async def delete_document(doc_id: int, db: Session = Depends(get_db)):
    """Delete a knowledge document."""
    try:
        success = delete_knowledge_document(db, doc_id)
        if not success:
            return KnowledgeDeleteResponse(code=404, message="Document not found")
        return KnowledgeDeleteResponse(code=200, data={"id": doc_id})
    except Exception as exc:
        return KnowledgeDeleteResponse(code=500, message=str(exc))


@router.post("/search", response_model=KnowledgeSearchResponse)
async def search_knowledge(request: KnowledgeSearchRequest, db: Session = Depends(get_db)):
    """Hybrid search: vector retrieval + keyword recall + rerank."""
    try:
        results = search_knowledge_by_keyword(
            db,
            request.keyword,
            request.top_k,
            request.use_vector,
            rerank=request.rerank,
            role_family=request.role_family,
            version=request.version,
        )
        return KnowledgeSearchResponse(code=200, data=results)
    except Exception as exc:
        return KnowledgeSearchResponse(code=500, message=str(exc))


def to_document_response(doc) -> KnowledgeDocumentResponse:
    return KnowledgeDocumentResponse(
        id=doc.id,
        filename=doc.filename,
        file_type=doc.file_type,
        total_chunks=doc.total_chunks,
        created_at=doc.created_at,
        source_type=doc.source_type or "general",
        tags=parse_tags(doc.tags),
        role_family=doc.role_family or "",
        version=doc.version or "v1",
        status=doc.status or "published",
    )


def parse_tags_input(raw: str) -> list[str]:
    try:
        value = json.loads(raw)
        if isinstance(value, list):
            return [str(item) for item in value]
    except json.JSONDecodeError:
        pass
    return [item.strip() for item in raw.split(",") if item.strip()]
