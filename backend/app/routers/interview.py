from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.schemas.interview_schema import (
    QUESTION_TYPE_LABELS,
    QUESTION_TYPES,
    InterviewQuestionsRequest,
    InterviewQuestionsResponse,
)
from app.services.interview_service import (
    generate_interview_questions,
    generate_self_intro_stream,
    generate_with_llm,
    generate_with_rules,
)
from app.services.llm_service import llm_service
from app.utils.sse_utils import sse_event

router = APIRouter(tags=["Interview Questions"])


@router.post("/questions", response_model=InterviewQuestionsResponse)
def generate_questions_endpoint(request: InterviewQuestionsRequest):
    try:
        if not request.resume_data or not request.jd_data:
            return InterviewQuestionsResponse(
                code=400,
                message="简历数据和JD数据不能为空",
                data=None
            )

        if request.question_types:
            for qt in request.question_types:
                if qt not in QUESTION_TYPES:
                    return InterviewQuestionsResponse(
                        code=400,
                        message=f"不支持的问题类型: {qt}",
                        data=None
                    )

        result = generate_interview_questions(
            request.resume_data,
            request.jd_data,
            request.raw_text,
            request.rewrite_result,
            request.question_types
        )

        return InterviewQuestionsResponse(
            code=200,
            message="success",
            data=result
        )

    except ValueError as e:
        return InterviewQuestionsResponse(
            code=400,
            message=str(e),
            data=None
        )
    except Exception as e:
        return InterviewQuestionsResponse(
            code=500,
            message=f"生成过程发生错误: {e!s}",
            data=None
        )


@router.post("/questions/stream")
async def generate_questions_stream_endpoint(request: InterviewQuestionsRequest):
    if not request.resume_data or not request.jd_data:
        return StreamingResponse(
            iter([sse_event("error", {"message": "简历数据和JD数据不能为空"})]),
            media_type="text/event-stream"
        )

    question_types = request.question_types or list(QUESTION_TYPE_LABELS.keys())
    if request.question_types:
        for qt in request.question_types:
            if qt not in QUESTION_TYPES:
                return StreamingResponse(
                    iter([sse_event("error", {"message": f"不支持的问题类型: {qt}"})]),
                    media_type="text/event-stream"
                )

    resume_data = request.resume_data
    jd_data = request.jd_data

    def event_generator():
        try:
            yield sse_event("progress", {"step": "generating_questions"})

            if llm_service.is_available():
                questions_result = generate_with_llm(resume_data, jd_data, question_types)
            else:
                questions_result = None

            if not questions_result:
                questions_result = generate_with_rules(resume_data, jd_data, question_types)

            yield sse_event("progress", {"step": "generating_self_intro"})

            intro_buffer = ""
            if llm_service.is_available():
                for chunk in generate_self_intro_stream(resume_data, jd_data):
                    intro_buffer += chunk
                    yield sse_event("chunk", {"content": chunk, "field": "self_intro"})
            else:
                intro_buffer = questions_result.self_intro or ""

            questions_result.self_intro = intro_buffer
            yield sse_event("done", {"result": questions_result.model_dump()})

        except Exception as e:
            yield sse_event("error", {"message": f"生成过程发生错误: {e!s}"})

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get("/types", response_model=dict)
def get_question_types():
    from app.schemas.interview_schema import QUESTION_TYPE_LABELS
    return {"code": 200, "data": QUESTION_TYPE_LABELS}
