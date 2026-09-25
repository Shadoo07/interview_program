
from pydantic import BaseModel, Field


class DiagnoseRequest(BaseModel):
    resume_text: str = Field(..., description="Resume text content")
    jd_content: str = Field(..., description="Job description content")


class StrengthItem(BaseModel):
    point: str = Field(..., description="Strength point")
    detail: str = Field(..., description="Strength detail")


class WeaknessItem(BaseModel):
    point: str = Field(..., description="Weakness point")
    detail: str = Field(..., description="Weakness detail")


class ImprovementItem(BaseModel):
    area: str = Field(..., description="Improvement area")
    suggestion: str = Field(..., description="Actionable suggestion")
    priority: str = Field(..., description="Priority level")


class EvidenceItem(BaseModel):
    claim: str = Field(..., description="Conclusion or diagnosis claim")
    evidence: str = Field(..., description="Resume/JD evidence supporting the claim")
    source: str = Field("inference", description="Evidence source: resume, jd, or inference")


class PerspectiveDiagnosis(BaseModel):
    role: str = Field(..., description="Agent role name")
    score: int = Field(..., ge=0, le=100, description="Role-specific score")
    summary: str = Field(..., description="Role-specific summary")
    evidence: list[EvidenceItem] = Field(default_factory=list, description="Evidence chains")
    risks: list[str] = Field(default_factory=list, description="Role-specific risks")
    suggestions: list[str] = Field(default_factory=list, description="Role-specific suggestions")


class ValidationResult(BaseModel):
    passed: bool = Field(True, description="Whether the diagnosis passed consistency checks")
    issues: list[str] = Field(default_factory=list, description="Validation issues")
    fixed: bool = Field(False, description="Whether the result was auto-fixed")


class JobFamilyProfile(BaseModel):
    family_id: str = Field(..., description="Detected job family id")
    title: str = Field(..., description="Detected job family title")
    confidence: float = Field(..., ge=0, le=1, description="Profile confidence")
    core_skills: list[str] = Field(default_factory=list, description="Core skills for this job family")
    preferred_skills: list[str] = Field(default_factory=list, description="Preferred skills")
    project_evidence_requirements: list[str] = Field(default_factory=list, description="Expected project evidence")
    interview_focus: list[str] = Field(default_factory=list, description="Interview focus areas")
    resume_keywords: list[str] = Field(default_factory=list, description="Resume keywords")
    risk_signals: list[str] = Field(default_factory=list, description="Common risk signals")
    scoring_weights: dict[str, float] = Field(default_factory=dict, description="Rubric scoring weights")
    matched_signals: list[str] = Field(default_factory=list, description="Signals used to infer the profile")


class ProjectDeepDive(BaseModel):
    project_name: str = Field(..., description="Project name")
    relevance_score: int = Field(..., ge=0, le=100, description="Relevance to the job profile")
    role_assessment: str = Field("", description="Assessment of the candidate role and contribution")
    technical_depth: str = Field("", description="Assessment of technical depth")
    evidence_gaps: list[str] = Field(default_factory=list, description="Missing evidence in the project")
    likely_followups: list[str] = Field(default_factory=list, description="Likely interviewer follow-up questions")
    answer_strategy: list[str] = Field(default_factory=list, description="Recommended answer strategy")
    rewrite_suggestions: list[str] = Field(default_factory=list, description="Resume rewrite suggestions")
    risk_level: str = Field("medium", description="Risk level: low, medium, or high")


class KnowledgeReference(BaseModel):
    chunk_id: int = Field(..., description="Knowledge chunk id")
    document_id: int = Field(..., description="Knowledge document id")
    document_name: str = Field(..., description="Knowledge document name")
    chunk_index: int = Field(0, description="Knowledge chunk index")
    section_title: str = Field("", description="Section title")
    content: str = Field(..., description="Retrieved content")
    score: float = Field(..., description="Similarity score")
    retrieval_score: float = Field(0, description="Initial retrieval score")
    rerank_score: float = Field(0, description="Rerank score")
    citation: str = Field("", description="Displayable source citation")
    source_type: str = Field("general", description="Knowledge source type")
    tags: list[str] = Field(default_factory=list, description="Knowledge tags")
    role_family: str = Field("", description="Related role family")
    version: str = Field("v1", description="Knowledge version")
    status: str = Field("published", description="Knowledge review status")


class DiagnoseResult(BaseModel):
    overall_assessment: str = Field(..., description="Overall assessment")
    strengths: list[StrengthItem] = Field(default_factory=list, description="Resume strengths")
    weaknesses: list[WeaknessItem] = Field(default_factory=list, description="Resume weaknesses")
    improvements: list[ImprovementItem] = Field(default_factory=list, description="Improvement suggestions")
    career_advice: str = Field("", description="Career advice")
    interview_tips: list[str] = Field(default_factory=list, description="Interview tips")
    source: str | None = Field(None, description="Result source: ai or rules")

    rubric_version: str = Field("resume-diagnosis-v1", description="Diagnosis rubric version")
    overall_score: int | None = Field(None, ge=0, le=100, description="Rubric-based overall score")
    perspectives: list[PerspectiveDiagnosis] = Field(default_factory=list, description="Multi-agent results")
    evidence_chains: list[EvidenceItem] = Field(default_factory=list, description="Key evidence chains")
    validation: ValidationResult | None = Field(None, description="LLM output validation result")
    job_profile: JobFamilyProfile | None = Field(None, description="Detected job family capability profile")
    project_deep_dives: list[ProjectDeepDive] = Field(default_factory=list, description="Project deep-dive analysis")
    rag_references: list[KnowledgeReference] = Field(default_factory=list, description="Retrieved RAG references")


class DiagnoseResponse(BaseModel):
    code: int = Field(200, description="Response code")
    message: str = Field("success", description="Response message")
    data: DiagnoseResult | None = Field(None, description="Diagnose result")
