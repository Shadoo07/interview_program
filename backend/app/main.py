import time
import uuid

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logging import configure_logging, get_logger
from app.routers import agent, health, history, interview, jd, knowledge, match, resume, rewrite

configure_logging()
logger = get_logger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="AI Resume & Interview Coaching Agent for College Students",
    version="1.0.0"
)


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    start = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception as exc:
        duration_ms = int((time.perf_counter() - start) * 1000)
        logger.exception(
            "request_failed",
            extra={
                "event": "http_request",
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": 500,
                "duration_ms": duration_ms,
                "error": str(exc),
            },
        )
        raise
    duration_ms = int((time.perf_counter() - start) * 1000)
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time-Ms"] = str(duration_ms)
    logger.info(
        "request_completed",
        extra={
            "event": "http_request",
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": duration_ms,
        },
    )
    return response

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api/health", tags=["Health"])
app.include_router(resume.router, prefix="/api/resume", tags=["Resume"])
app.include_router(rewrite.router, prefix="/api/resume", tags=["Resume Rewrite"])
app.include_router(jd.router, prefix="/api/jd", tags=["JD Analysis"])
app.include_router(match.router, prefix="/api/match", tags=["Match Analysis"])
app.include_router(agent.router, prefix="/api/agent", tags=["AI Agent"])
app.include_router(interview.router, prefix="/api/interview", tags=["Interview"])
app.include_router(history.router, prefix="/api/history", tags=["History"])
app.include_router(knowledge.router, prefix="/api/knowledge", tags=["Knowledge"])

@app.get("/")
async def root():
    return {"message": "Welcome to AI Resume Coach API"}
