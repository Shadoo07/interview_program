from fastapi import APIRouter, File, UploadFile
from fastapi.responses import JSONResponse

from app.schemas.resume_schema import (
    FileUploadResponse,
    ResumeParseRequest,
    ResumeParseResponse,
    ResumeStructureAPIResponse,
    ResumeStructureRequest,
)
from app.services import resume_service

router = APIRouter()


@router.post("/upload", response_model=FileUploadResponse)
def upload_resume(file: UploadFile = File(...)):
    try:
        # Starlette 在解析完 multipart 后会把文件指针复位到 0
        # （formparsers 中的 `await part.file.seek(0)`），因此这里可以同步读取。
        # 端点已改为 def，整体在线程池中执行，不再阻塞事件循环。
        content = file.file.read()
        result = resume_service.upload_resume(content, file.filename)
        return {
            "code": 200,
            "message": "success",
            "data": {
                "file_id": result.file_id,
                "original_filename": result.original_filename,
                "file_size": result.file_size,
                "file_type": result.file_type
            }
        }
    except ValueError as e:
        return JSONResponse(
            status_code=400,
            content={"code": 400, "message": str(e), "data": None}
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"code": 500, "message": f"Upload failed: {e!s}", "data": None}
        )


@router.post("/parse", response_model=ResumeParseResponse)
def parse_resume(request: ResumeParseRequest):
    try:
        result = resume_service.parse_resume(request.file_id)
        return {
            "code": 200,
            "message": "success",
            "data": {
                "file_id": result.file_id,
                "raw_text": result.raw_text
            }
        }
    except FileNotFoundError:
        return JSONResponse(
            status_code=404,
            content={"code": 404, "message": "File not found", "data": None}
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"code": 500, "message": f"Parse failed: {e!s}", "data": None}
        )


@router.post("/structure", response_model=ResumeStructureAPIResponse)
def structure_resume(request: ResumeStructureRequest):
    try:
        result = resume_service.structure_resume(request.raw_text)
        return {
            "code": 200,
            "message": "success",
            "data": result.model_dump()
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"code": 500, "message": f"Structure failed: {e!s}", "data": None}
        )
