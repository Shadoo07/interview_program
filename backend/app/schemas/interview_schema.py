
from pydantic import BaseModel, Field


class QuestionItem(BaseModel):
    question: str = Field(..., description="面试问题")
    focus_point: str = Field(..., description="考察点")
    answer_guide: str = Field(..., description="参考回答思路")
    notes: str = Field(..., description="回答注意事项")
    difficulty: str = Field(..., description="难度等级：简单/中等/困难")


class QuestionCategory(BaseModel):
    category: str = Field(..., description="问题分类")
    description: str = Field("", description="分类描述")
    questions: list[QuestionItem] = Field(default_factory=list, description="问题列表")


class InterviewQuestionsResult(BaseModel):
    source: str = Field("rules", description="生成来源: ai / rules")
    project_deep_dive: list[QuestionItem] = Field(default_factory=list, description="项目深挖问题")
    tech_theory: list[QuestionItem] = Field(default_factory=list, description="技术八股问题")
    system_design: list[QuestionItem] = Field(default_factory=list, description="场景设计问题")
    project_difficulties: list[QuestionItem] = Field(default_factory=list, description="项目难点追问")
    hr_general: list[QuestionItem] = Field(default_factory=list, description="HR综合问题")
    self_intro: str = Field("", description="自我介绍优化建议")


class InterviewQuestionsRequest(BaseModel):
    resume_data: dict = Field(..., description="简历结构化数据")
    jd_data: dict = Field(..., description="JD分析结果数据")
    raw_text: str | None = Field(None, description="简历原始文本")
    rewrite_result: dict | None = Field(None, description="改写结果")
    question_types: list[str] | None = Field(None, description="问题类型列表")


class InterviewQuestionsResponse(BaseModel):
    code: int = Field(200, description="响应码")
    message: str = Field("success", description="响应消息")
    data: InterviewQuestionsResult | None = Field(None, description="面试问题结果")


QUESTION_TYPES = [
    "project_deep_dive",
    "tech_theory",
    "system_design",
    "project_difficulties",
    "hr_general",
    "self_intro"
]

QUESTION_TYPE_LABELS = {
    "project_deep_dive": "项目深挖问题",
    "tech_theory": "技术八股问题",
    "system_design": "场景设计问题",
    "project_difficulties": "项目难点追问",
    "hr_general": "HR综合问题",
    "self_intro": "自我介绍优化建议"
}
