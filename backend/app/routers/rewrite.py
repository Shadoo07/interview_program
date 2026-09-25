from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.schemas.rewrite_schema import REWRITE_MODES, ResumeRewriteRequest, ResumeRewriteResponse
from app.services.llm_service import llm_service
from app.services.rewrite_service import (
    analyze_original_resume,
    generate_notes,
    rewrite_resume,
    rewrite_with_llm_stream,
)
from app.utils.sse_utils import sse_event

router = APIRouter(tags=["Resume Rewrite"])


@router.post("/rewrite", response_model=ResumeRewriteResponse)
async def rewrite_resume_endpoint(request: ResumeRewriteRequest):
    try:
        if not request.resume_data or not request.jd_data:
            return ResumeRewriteResponse(
                code=400,
                message="简历数据和JD数据不能为空",
                data=None
            )

        if not request.raw_text or len(request.raw_text.strip()) < 20:
            return ResumeRewriteResponse(
                code=400,
                message="简历原始文本过短",
                data=None
            )

        if request.rewrite_mode not in REWRITE_MODES:
            return ResumeRewriteResponse(
                code=400,
                message=f"不支持的改写模式，请选择：{', '.join(REWRITE_MODES)}",
                data=None
            )

        result = rewrite_resume(
            request.resume_data,
            request.jd_data,
            request.raw_text,
            request.rewrite_mode,
            request.match_result,
            request.diagnose_result
        )

        return ResumeRewriteResponse(
            code=200,
            message="success",
            data=result
        )

    except ValueError as e:
        return ResumeRewriteResponse(
            code=400,
            message=str(e),
            data=None
        )
    except Exception as e:
        return ResumeRewriteResponse(
            code=500,
            message=f"改写过程发生错误: {e!s}",
            data=None
        )


@router.post("/rewrite/stream")
async def rewrite_resume_stream_endpoint(request: ResumeRewriteRequest):
    if not request.resume_data or not request.jd_data:
        return StreamingResponse(
            iter([sse_event("error", {"message": "简历数据和JD数据不能为空"})]),
            media_type="text/event-stream"
        )

    if not request.raw_text or len(request.raw_text.strip()) < 20:
        return StreamingResponse(
            iter([sse_event("error", {"message": "简历原始文本过短"})]),
            media_type="text/event-stream"
        )

    if request.rewrite_mode not in REWRITE_MODES:
        return StreamingResponse(
            iter([sse_event("error", {"message": f"不支持的改写模式，请选择：{', '.join(REWRITE_MODES)}"})]),
            media_type="text/event-stream"
        )

    resume_data = request.resume_data
    jd_data = request.jd_data
    raw_text = request.raw_text
    rewrite_mode = request.rewrite_mode
    match_result = request.match_result

    def event_generator():
        try:
            yield sse_event("progress", {"step": "analyzing"})
            original_analysis = analyze_original_resume(resume_data, jd_data, match_result)

            if llm_service.is_available():
                yield sse_event("progress", {"step": "rewriting"})
                content_buffer = ""
                for chunk in rewrite_with_llm_stream(
                    resume_data, jd_data, raw_text, rewrite_mode, original_analysis
                ):
                    content_buffer += chunk
                    yield sse_event("chunk", {"content": chunk})

                reasons = [
                    "基于AI分析，针对目标岗位优化",
                    "突出与岗位匹配的技能和经验",
                    "优化语言表达，提升专业度",
                    "保持真实，不编造经历"
                ]
                notes = generate_notes(rewrite_mode)

                from app.schemas.rewrite_schema import ResumeRewriteResult
                result = ResumeRewriteResult(
                    original_analysis=original_analysis,
                    rewritten_content=content_buffer,
                    rewrite_reasons=reasons,
                    project_experience_text="请查看改写后的简历内容",
                    notes=notes
                )
            else:
                from app.services.rewrite_service import rewrite_with_rules
                content, reasons, project_text = rewrite_with_rules(resume_data, jd_data, rewrite_mode)
                notes = generate_notes(rewrite_mode)
                from app.schemas.rewrite_schema import ResumeRewriteResult
                result = ResumeRewriteResult(
                    original_analysis=original_analysis,
                    rewritten_content=content,
                    rewrite_reasons=reasons,
                    project_experience_text=project_text,
                    notes=notes
                )

            yield sse_event("done", {"result": result.model_dump()})

        except Exception as e:
            yield sse_event("error", {"message": f"改写过程发生错误: {e!s}"})

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get("/modes", response_model=dict)
async def get_rewrite_modes():
    from app.schemas.rewrite_schema import REWRITE_MODE_LABELS
    return {"code": 200, "data": REWRITE_MODE_LABELS}
