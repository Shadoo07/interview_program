from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.database import Base, SessionLocal, engine  # noqa: E402
from app.models import history, knowledge_base  # noqa: F401,E402
from app.models.knowledge_base import KnowledgeDocument  # noqa: E402
from app.services.knowledge_service import (  # noqa: E402
    ensure_knowledge_schema,
    sha256_text,
    upload_knowledge_document,
)

SEED_DIR = ROOT / "seed" / "knowledge"


def parse_seed_markdown(path: Path) -> tuple[dict, str]:
    text = path.read_text(encoding="utf-8")
    metadata = {
        "source_type": "general",
        "tags": [],
        "role_family": "",
        "version": "v1",
        "status": "published",
    }
    if text.startswith("---"):
        _, raw_meta, body = text.split("---", 2)
        for line in raw_meta.splitlines():
            if ":" not in line:
                continue
            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip()
            if key == "tags":
                metadata[key] = [item.strip() for item in value.split(",") if item.strip()]
            else:
                metadata[key] = value
        text = body.strip()
    return metadata, text


def seed() -> int:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    imported = 0
    skipped = 0
    try:
        ensure_knowledge_schema(db)
        for path in sorted(SEED_DIR.glob("*.md")):
            metadata, content = parse_seed_markdown(path)
            content_hash = sha256_text(content)
            exists = db.query(KnowledgeDocument).filter(KnowledgeDocument.content_hash == content_hash).first()
            if exists:
                skipped += 1
                continue
            upload_knowledge_document(db, content.encode("utf-8"), path.name, metadata)
            imported += 1
    finally:
        db.close()

    print(f"Knowledge seed complete: imported={imported}, skipped={skipped}, dir={SEED_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(seed())
