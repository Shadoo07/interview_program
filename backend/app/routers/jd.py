from fastapi import APIRouter

from app.schemas.jd_schema import JDAnalysisRequest, JDAnalysisResponse
from app.services.jd_service import analyze_jd

router = APIRouter(tags=["JD Analysis"])


@router.post("/analyze", response_model=JDAnalysisResponse)
async def analyze_jd_endpoint(request: JDAnalysisRequest):
    try:
        if not request.jd_content or len(request.jd_content.strip()) < 10:
            return JDAnalysisResponse(
                code=400,
                message="JD内容不能为空或过短（至少10个字符）",
                data=None
            )

        result = analyze_jd(request.jd_content)
        return JDAnalysisResponse(
            code=200,
            message="success",
            data=result
        )

    except ValueError as e:
        return JDAnalysisResponse(
            code=400,
            message=str(e),
            data=None
        )
    except Exception as e:
        return JDAnalysisResponse(
            code=500,
            message=f"分析过程发生错误: {e!s}",
            data=None
        )
