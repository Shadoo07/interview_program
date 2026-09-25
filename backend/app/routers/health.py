from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.core.model_presets import list_model_presets
from app.database import SessionLocal
from app.services.llm_service import llm_service
from app.services.rag_service import rag_service
from app.services.vector_store import is_postgres_enabled

router = APIRouter()


@router.get("/check")
async def health_check():
    return {
        "code": 200,
        "message": "success",
        "data": {
            "status": "healthy",
            "service": "AI Resume Coach API",
            "version": "1.0.0",
        },
    }


@router.get("/llm-config")
async def get_llm_config():
    """Return current LLM configuration."""
    config_info = llm_service.get_config_info()
    return {
        "code": 200,
        "message": "success",
        "data": config_info,
    }


@router.get("/ready")
async def readiness_check():
    db_status = check_database()
    ok = db_status["ok"]
    payload = {
        "code": 200 if ok else 503,
        "message": "success" if ok else "service not ready",
        "data": {
            "status": "ready" if ok else "degraded",
            "database": db_status,
            "vector_store": {
                "postgres_enabled": is_postgres_enabled(),
                "pgvector_required": is_postgres_enabled(),
            },
            "llm": {
                "configured": llm_service.is_available(),
                "stats": llm_service.stats,
            },
            "rag": {
                "stats": rag_service.stats,
            },
        },
    }
    return JSONResponse(status_code=200 if ok else 503, content=payload)


@router.get("/observability")
async def observability_snapshot():
    return {
        "code": 200,
        "message": "success",
        "data": {
            "llm": llm_service.get_config_info(),
            "rag": rag_service.stats,
            "database": check_database(),
        },
    }


@router.get("/llm-models")
async def get_llm_models():
    """Return selectable LLM model presets."""
    return {
        "code": 200,
        "message": "success",
        "data": list_model_presets(),
    }


@router.get("/llm-test")
async def test_llm_connection():
    """Call the configured model once to verify connectivity."""
    return {
        "code": 200,
        "message": "success",
        "data": {
            **llm_service.get_config_info(),
            "test": llm_service.test_connection(),
        },
    }


def check_database() -> dict:
    db = SessionLocal()
    try:
        db.execute(text("SELECT 1"))
        pgvector = None
        if is_postgres_enabled():
            pgvector = bool(
                db.execute(text("SELECT 1 FROM pg_extension WHERE extname = 'vector'")).scalar()
            )
        return {"ok": True, "pgvector": pgvector}
    except Exception as exc:
        return {"ok": False, "error": str(exc), "pgvector": False if is_postgres_enabled() else None}
    finally:
        db.close()
