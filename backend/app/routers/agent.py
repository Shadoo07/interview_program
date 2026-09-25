from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.agent import DiagnoseRequest, DiagnoseResponse

router = APIRouter()

@router.post("/diagnose", response_model=DiagnoseResponse)
async def diagnose_resume(request: DiagnoseRequest, db: Session = Depends(get_db)):
    from app.services.agent_service import diagnose_resume
    try:
        result = diagnose_resume(request.resume_text, request.jd_content, db)
        return {
            "code": 200,
            "message": "success",
            "data": result
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"code": 500, "message": f"Diagnose error: {e!s}", "data": None}
        )
