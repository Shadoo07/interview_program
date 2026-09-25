
from pydantic import BaseModel, Field


class DimensionScore(BaseModel):
    dimension: str = Field(..., description="维度名称")
    score: int = Field(..., description="维度评分 (0-100)")
    max_score: int = Field(100, description="维度满分")
    weight: float = Field(..., description="权重")
    matched_keywords: list[str] = Field(default_factory=list, description="匹配的关键词")
    missing_keywords: list[str] = Field(default_factory=list, description="缺失的关键词")


class MatchAnalysisResult(BaseModel):
    overall_score: int = Field(..., description="总体匹配度评分 (0-100)")
    dimension_scores: list[DimensionScore] = Field(default_factory=list, description="各维度评分")
    matched_keywords: list[str] = Field(default_factory=list, description="所有匹配的关键词")
    missing_keywords: list[str] = Field(default_factory=list, description="所有缺失的关键词")
    weak_points: list[str] = Field(default_factory=list, description="简历短板")
    suggestions: list[str] = Field(default_factory=list, description="优化建议")
    match_level: str = Field(..., description="匹配等级：优秀/良好/一般/较差")


class MatchAnalysisRequest(BaseModel):
    resume_data: dict = Field(..., description="简历结构化数据")
    jd_data: dict = Field(..., description="JD分析结果数据")


class MatchAnalysisResponse(BaseModel):
    code: int = Field(200, description="响应码")
    message: str = Field("success", description="响应消息")
    data: MatchAnalysisResult | None = Field(None, description="匹配度分析结果")
