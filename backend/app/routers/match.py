from fastapi import APIRouter

from app.schemas.match_schema import MatchAnalysisRequest, MatchAnalysisResponse
from app.services.match_service import analyze_match

router = APIRouter(tags=["Match Analysis"])


@router.post("/analyze", response_model=MatchAnalysisResponse)
async def analyze_match_endpoint(request: MatchAnalysisRequest):
    try:
        if not request.resume_data or not request.jd_data:
            return MatchAnalysisResponse(
                code=400,
                message="简历数据和JD数据不能为空",
                data=None
            )

        result = analyze_match(request.resume_data, request.jd_data)
        return MatchAnalysisResponse(
            code=200,
            message="success",
            data=result
        )

    except ValueError as e:
        return MatchAnalysisResponse(
            code=400,
            message=str(e),
            data=None
        )
    except Exception as e:
        return MatchAnalysisResponse(
            code=500,
            message=f"分析过程发生错误: {e!s}",
            data=None
        )
