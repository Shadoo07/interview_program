
from pydantic import BaseModel, Field


class JDAnalysisRequest(BaseModel):
    jd_content: str = Field(..., description="Job description content to analyze")


class JDAnalysisResult(BaseModel):
    position_title: str = Field(..., description="Position title")
    position_type: str = Field(..., description="Position category")
    required_skills: list[str] = Field(default_factory=list, description="Required technical skills")
    nice_to_have_skills: list[str] = Field(default_factory=list, description="Nice-to-have skills")
    responsibilities: list[str] = Field(default_factory=list, description="Job responsibilities")
    requirements: list[str] = Field(default_factory=list, description="Requirements")
    plus_points: list[str] = Field(default_factory=list, description="Bonus points")
    experience_requirement: str = Field("", description="Experience requirement")
    education_requirement: str = Field("", description="Education requirement")
    summary: str = Field("", description="Position summary")


class JDAnalysisResponse(BaseModel):
    code: int = Field(200, description="Response code")
    message: str = Field("success", description="Response message")
    data: JDAnalysisResult | None = Field(None, description="JD analysis result")
