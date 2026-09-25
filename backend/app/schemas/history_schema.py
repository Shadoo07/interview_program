from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class HistorySaveRequest(BaseModel):
    resume_filename: str | None = Field(None, description="简历文件名")
    raw_text: str | None = Field(None, description="简历原始文本")
    resume_data: dict | None = Field(None, description="简历结构化数据")
    jd_text: str | None = Field(None, description="JD原始文本")
    jd_data: dict | None = Field(None, description="JD分析结果")
    match_result: dict | None = Field(None, description="匹配度分析结果")
    diagnose_result: dict | None = Field(None, description="诊断结果")
    rewrite_result: dict | None = Field(None, description="简历改写结果")
    interview_questions: dict | None = Field(None, description="面试问题")


class HistoryRecord(BaseModel):
    id: int = Field(..., description="记录ID")
    resume_filename: str | None = Field(None, description="简历文件名")
    raw_text: str | None = Field(None, description="简历原始文本")
    resume_data: dict[str, Any] | None = Field(None, description="简历结构化数据")
    jd_text: str | None = Field(None, description="JD原始文本")
    jd_data: dict[str, Any] | None = Field(None, description="JD分析结果")
    match_result: dict[str, Any] | None = Field(None, description="匹配度分析结果")
    diagnose_result: dict[str, Any] | None = Field(None, description="诊断结果")
    rewrite_result: dict[str, Any] | None = Field(None, description="简历改写结果")
    interview_questions: dict[str, Any] | None = Field(None, description="面试问题")
    created_at: datetime = Field(..., description="创建时间")


class HistoryListResponse(BaseModel):
    code: int = Field(200, description="响应码")
    message: str = Field("success", description="响应消息")
    data: list | None = Field(None, description="历史记录列表")


class HistoryDetailResponse(BaseModel):
    code: int = Field(200, description="响应码")
    message: str = Field("success", description="响应消息")
    data: HistoryRecord | None = Field(None, description="历史记录详情")


class HistorySaveResponse(BaseModel):
    code: int = Field(200, description="响应码")
    message: str = Field("success", description="响应消息")
    data: dict | None = Field(None, description="保存结果")


class HistoryDeleteResponse(BaseModel):
    code: int = Field(200, description="响应码")
    message: str = Field("success", description="响应消息")
    data: dict | None = Field(None, description="删除结果")
