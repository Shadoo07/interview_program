from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.services.knowledge_service import search_knowledge_by_keyword

logger = get_logger(__name__)


class RAGService:
    def __init__(self) -> None:
        self.stats = {
            "retrievals": 0,
            "success": 0,
            "failures": 0,
            "last_error": None,
            "last_result_count": 0,
            "last_citations": [],
        }

    def retrieve_knowledge(
        self,
        db: Session,
        query: str,
        top_k: int = 5,
        role_family: str = "",
        version: str = "",
    ) -> list[dict]:
        self.stats["retrievals"] += 1
        try:
            results = search_knowledge_by_keyword(
                db,
                query,
                top_k=top_k,
                use_vector=True,
                rerank=True,
                role_family=role_family,
                version=version,
            )
            payload = [item.model_dump() for item in results]
            self.stats["success"] += 1
            self.stats["last_error"] = None
            self.stats["last_result_count"] = len(payload)
            self.stats["last_citations"] = [item.get("citation", "") for item in payload]
            logger.info(
                "rag_retrieval_success",
                extra={
                    "event": "rag_retrieval",
                    "ok": True,
                    "top_k": top_k,
                    "result_count": len(payload),
                },
            )
            return payload
        except Exception as exc:
            self.stats["failures"] += 1
            self.stats["last_error"] = str(exc)
            self.stats["last_citations"] = []
            logger.warning(
                "rag_retrieval_failed",
                extra={
                    "event": "rag_retrieval",
                    "ok": False,
                    "top_k": top_k,
                    "result_count": 0,
                    "error": str(exc),
                },
            )
            return []

    def build_context_block(
        self,
        db: Session,
        query: str,
        top_k: int = 5,
        role_family: str = "",
        version: str = "",
    ) -> str:
        results = self.retrieve_knowledge(db, query, top_k, role_family=role_family, version=version)
        if not results:
            return ""
        lines = ["RAG 检索上下文（回答时优先引用 citation）："]
        for index, item in enumerate(results, 1):
            lines.append(
                f"[{index}] citation={item.get('citation')} source={item.get('document_name')} "
                f"type={item.get('source_type')} role={item.get('role_family')} "
                f"version={item.get('version')} score={item.get('score')}\n{item.get('content')}"
            )
        return "\n\n".join(lines)

    def split_document(self, text: str, chunk_size: int = 700) -> list[str]:
        from app.utils.knowledge_utils import split_text_into_chunks

        return split_text_into_chunks(text, chunk_size=chunk_size)


rag_service = RAGService()
