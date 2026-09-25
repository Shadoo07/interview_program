from datetime import datetime

from pydantic import BaseModel, Field


class KnowledgeChunkResponse(BaseModel):
    id: int
    content: str
    chunk_index: int
    document_id: int
    section_title: str = ""
    char_start: int = 0
    char_end: int = 0
    token_count: int = 0
    created_at: datetime


class KnowledgeDocumentResponse(BaseModel):
    id: int
    filename: str
    file_type: str
    total_chunks: int
    created_at: datetime
    source_type: str = "general"
    tags: list[str] = Field(default_factory=list)
    role_family: str = ""
    version: str = "v1"
    status: str = "published"


class KnowledgeUploadResponse(BaseModel):
    code: int = Field(200)
    message: str = Field("success")
    data: KnowledgeDocumentResponse | None = None


class KnowledgeListResponse(BaseModel):
    code: int = Field(200)
    message: str = Field("success")
    data: list[KnowledgeDocumentResponse] = Field(default_factory=list)


class KnowledgeSearchRequest(BaseModel):
    keyword: str = Field(..., min_length=1)
    top_k: int = Field(5, ge=1, le=20)
    use_vector: bool = Field(True)
    rerank: bool = Field(True)
    role_family: str = Field("", description="Optional role family boost, e.g. ai_application")
    version: str = Field("", description="Optional knowledge version filter")


class KnowledgeSearchResult(BaseModel):
    chunk_id: int
    document_id: int
    document_name: str
    chunk_index: int = 0
    section_title: str = ""
    content: str
    score: float
    retrieval_score: float = 0
    rerank_score: float = 0
    citation: str = ""
    source_type: str = "general"
    tags: list[str] = Field(default_factory=list)
    role_family: str = ""
    version: str = "v1"
    status: str = "published"
    content_hash: str = ""


class KnowledgeMetadataUpdateRequest(BaseModel):
    source_type: str | None = None
    tags: list[str] | None = None
    role_family: str | None = None
    version: str | None = None
    status: str | None = None


class KnowledgeVersionSummary(BaseModel):
    version: str
    source_type: str = "general"
    role_family: str = ""
    status: str = "published"
    document_count: int = 0
    chunk_count: int = 0
    latest_created_at: datetime | None = None


class KnowledgeVersionListResponse(BaseModel):
    code: int = Field(200)
    message: str = Field("success")
    data: list[KnowledgeVersionSummary] = Field(default_factory=list)


class KnowledgeSearchResponse(BaseModel):
    code: int = Field(200)
    message: str = Field("success")
    data: list[KnowledgeSearchResult] = Field(default_factory=list)


class KnowledgeDeleteResponse(BaseModel):
    code: int = Field(200)
    message: str = Field("success")
    data: dict | None = None
