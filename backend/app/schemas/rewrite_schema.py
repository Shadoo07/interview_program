
from pydantic import BaseModel, Field


class ResumeRewriteRequest(BaseModel):
    resume_data: dict = Field(..., description="简历结构化数据")
    jd_data: dict = Field(..., description="JD分析结果数据")
    raw_text: str = Field(..., description="简历原始文本")
    rewrite_mode: str = Field(..., description="改写模式")
    match_result: dict | None = Field(None, description="匹配度分析结果")
    diagnose_result: dict | None = Field(None, description="诊断结果")


class ResumeRewriteResult(BaseModel):
    original_analysis: str = Field(..., description="原始问题分析")
    rewritten_content: str = Field(..., description="改写后的简历内容")
    rewrite_reasons: list[str] = Field(default_factory=list, description="改写理由")
    project_experience_text: str = Field("", description="可直接复制的项目经历文本")
    notes: list[str] = Field(default_factory=list, description="注意事项")


class ResumeRewriteResponse(BaseModel):
    code: int = Field(200, description="响应码")
    message: str = Field("success", description="响应消息")
    data: ResumeRewriteResult | None = Field(None, description="简历改写结果")


REWRITE_MODES = [
    "big_company_intern",
    "backend_developer",
    "ai_developer",
    "project_enhance",
    "hr_friendly",
    "one_page"
]

REWRITE_MODE_LABELS = {
    "big_company_intern": "大厂实习投递版",
    "backend_developer": "后端开发岗位版",
    "ai_developer": "AI应用开发岗位版",
    "project_enhance": "项目经历强化版",
    "hr_friendly": "HR初筛友好版",
    "one_page": "简洁一页版"
}
