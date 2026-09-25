from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

os.environ["DATABASE_URL"] = "sqlite:///./rag_eval_tmp.db"
os.environ["EMBEDDING_ENABLE_REMOTE"] = "false"

BACKEND_ROOT = Path(__file__).resolve().parents[2]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

from app.database import Base  # noqa: E402
from app.models.knowledge_base import KnowledgeChunk, KnowledgeDocument  # noqa: E402
from app.services.embedding_service import get_embeddings  # noqa: E402
from app.services.knowledge_service import (  # noqa: E402
    ensure_knowledge_schema,
    search_knowledge_by_keyword,
    sha256_text,
)
from app.services.vector_store import get_vector_store  # noqa: E402
from app.utils.knowledge_utils import split_text_into_semantic_chunks  # noqa: E402

ROOT = Path(__file__).resolve().parent
CASES_PATH = ROOT / "cases" / "rag_eval_cases.json"
REPORT_DIR = ROOT / "reports"


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate RAG retrieval hit rate.")
    parser.add_argument("--cases", default=str(CASES_PATH))
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument("--write-report", action="store_true")
    args = parser.parse_args()

    cases = json.loads(Path(args.cases).read_text(encoding="utf-8"))
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = Path(tmp_dir) / "rag_eval.db"
        engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
        TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        Base.metadata.create_all(bind=engine)

        try:
            with TestingSessionLocal() as db:
                ensure_knowledge_schema(db)
                results = []
                for case in cases:
                    reset_case_data(db)
                    seed_documents(db, case["documents"])
                    retrieved = search_knowledge_by_keyword(
                        db,
                        case["query"],
                        top_k=args.top_k,
                        use_vector=True,
                        rerank=True,
                        role_family=case.get("role_family", ""),
                    )
                    result = evaluate_case(case, retrieved)
                    results.append(result)
        finally:
            engine.dispose()

    summary = summarize(results, args.top_k)
    print(f"RAG evaluation: hit@1={summary['hit_at_1']:.2f} hit@{args.top_k}={summary['hit_at_k']:.2f} mrr={summary['mrr']:.2f}")
    for item in results:
        status = "PASS" if item["hit_at_k"] else "FAIL"
        print(f"- [{status}] {item['id']} rank={item['rank']} top={item['top_document']} citation={item['top_citation']}")

    if args.write_report:
        write_reports(summary, results)

    return 0 if summary["hit_at_k"] >= 1.0 and summary["hit_at_1"] >= 0.67 else 1


def reset_case_data(db) -> None:
    db.query(KnowledgeChunk).delete()
    db.query(KnowledgeDocument).delete()
    db.commit()


def seed_documents(db, documents: list[dict[str, Any]]) -> None:
    vector_store = get_vector_store(db)
    for document in documents:
        chunks = split_text_into_semantic_chunks(document["content"])
        doc = KnowledgeDocument(
            filename=document["filename"],
            file_type="txt",
            file_path="",
            source_type=document.get("source_type", "general"),
            tags=json.dumps(document.get("tags", []), ensure_ascii=False),
            role_family=document.get("role_family", ""),
            version=document.get("version", "v1"),
            status=document.get("status", "published"),
            content_hash=sha256_text(document["content"]),
            total_chunks=len(chunks),
        )
        db.add(doc)
        db.flush()

        embeddings = get_embeddings([chunk.content for chunk in chunks])
        for index, chunk in enumerate(chunks):
            row = KnowledgeChunk(
                document_id=doc.id,
                content=chunk.content,
                chunk_index=index,
                content_hash=sha256_text(chunk.content),
                section_title=chunk.section_title,
                char_start=chunk.char_start,
                char_end=chunk.char_end,
                token_count=chunk.token_count,
            )
            db.add(row)
            db.flush()
            vector_store.upsert_embedding(row.id, doc.id, embeddings[index], row.content_hash)
    db.commit()


def evaluate_case(case: dict[str, Any], retrieved) -> dict[str, Any]:
    expected_doc = case["expected_doc"]
    rank = None
    for index, item in enumerate(retrieved, 1):
        if item.document_name == expected_doc:
            rank = index
            break
    top = retrieved[0] if retrieved else None
    return {
        "id": case["id"],
        "query": case["query"],
        "expected_doc": expected_doc,
        "rank": rank,
        "hit_at_1": rank == 1,
        "hit_at_k": rank is not None,
        "mrr": 0 if rank is None else 1 / rank,
        "top_document": top.document_name if top else "",
        "top_citation": top.citation if top else "",
        "results": [item.model_dump() for item in retrieved],
    }


def summarize(results: list[dict[str, Any]], top_k: int) -> dict[str, Any]:
    total = len(results) or 1
    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "case_count": len(results),
        "top_k": top_k,
        "hit_at_1": sum(1 for item in results if item["hit_at_1"]) / total,
        "hit_at_k": sum(1 for item in results if item["hit_at_k"]) / total,
        "mrr": sum(item["mrr"] for item in results) / total,
    }


def write_reports(summary: dict[str, Any], results: list[dict[str, Any]]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    payload = {"summary": summary, "results": results}
    (REPORT_DIR / "rag_latest.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# RAG Retrieval Evaluation",
        "",
        f"- Generated at: `{summary['generated_at']}`",
        f"- Cases: `{summary['case_count']}`",
        f"- Hit@1: `{summary['hit_at_1']:.2f}`",
        f"- Hit@{summary['top_k']}: `{summary['hit_at_k']:.2f}`",
        f"- MRR: `{summary['mrr']:.2f}`",
        "",
        "| Case | Expected | Rank | Top Document | Citation |",
        "| --- | --- | ---: | --- | --- |",
    ]
    for item in results:
        lines.append(
            f"| `{item['id']}` | `{item['expected_doc']}` | `{item['rank']}` | "
            f"`{item['top_document']}` | `{item['top_citation']}` |"
        )
    (REPORT_DIR / "rag_latest.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
