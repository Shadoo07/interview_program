#!/bin/sh
set -e

python init_db.py

if [ "${SEED_KNOWLEDGE_ON_START:-true}" = "true" ]; then
  python scripts/seed_knowledge.py
fi

exec uvicorn app.main:app --host 0.0.0.0 --port 8000
