
from pydantic import BaseModel, Field


class FileUploadData(BaseModel):
    file_id: str = Field(..., description="Unique file identifier")
    original_filename: str = Field(..., description="Original filename")
    file_size: int = Field(..., description="File size in bytes")
    file_type: str = Field(..., description="File extension")


class FileUploadResponse(BaseModel):
    code: int = Field(200, description="Response code")
    message: str = Field("success", description="Response message")
    data: FileUploadData | None = Field(None, description="Uploaded file data")


class ResumeParseRequest(BaseModel):
    file_id: str = Field(..., description="File ID from upload response")


class ResumeParseData(BaseModel):
    file_id: str = Field(..., description="File ID")
    raw_text: str = Field(..., description="Extracted raw text from resume")


class ResumeParseResponse(BaseModel):
    code: int = Field(200, description="Response code")
    message: str = Field("success", description="Response message")
    data: ResumeParseData | None = Field(None, description="Resume parse result")


class ResumeStructureRequest(BaseModel):
    raw_text: str = Field(..., description="Raw resume text to structure")


class BasicInfo(BaseModel):
    name: str | None = Field(None, description="Candidate name")
    phone: str | None = Field(None, description="Phone number")
    email: str | None = Field(None, description="Email address")
    school: str | None = Field(None, description="University/school")
    major: str | None = Field(None, description="Major")
    degree: str | None = Field(None, description="Degree")


class EducationEntry(BaseModel):
    school: str | None = Field(None, description="School name")
    major: str | None = Field(None, description="Major")
    degree: str | None = Field(None, description="Degree")
    duration: str | None = Field(None, description="Duration e.g. 2020-2024")
    gpa: str | None = Field(None, description="GPA if available")
    description: str | None = Field(None, description="Additional description")


class ProjectEntry(BaseModel):
    name: str = Field(..., description="Project name")
    role: str | None = Field(None, description="Your role in the project")
    duration: str | None = Field(None, description="Project duration")
    description: str = Field(..., description="Project description")
    technologies: list[str] = Field(default_factory=list, description="Technologies used")
    highlights: list[str] = Field(default_factory=list, description="Project highlights/achievements")


class SkillEntry(BaseModel):
    category: str = Field(..., description="Skill category e.g. Programming Languages, Frameworks")
    items: list[str] = Field(..., description="List of skills in this category")


class InternshipEntry(BaseModel):
    company: str = Field(..., description="Company name")
    position: str | None = Field(None, description="Position title")
    duration: str | None = Field(None, description="Duration")
    description: str = Field(..., description="Work description")
    achievements: list[str] = Field(default_factory=list, description="Key achievements")


class AwardEntry(BaseModel):
    name: str = Field(..., description="Award name")
    level: str | None = Field(None, description="Award level e.g. National, Provincial, School")
    date: str | None = Field(None, description="Date received")
    description: str | None = Field(None, description="Award description")


class SummaryEntry(BaseModel):
    content: str = Field(..., description="Summary content")


class ResumeStructureResponse(BaseModel):
    basic_info: BasicInfo = Field(..., description="Basic personal information")
    education: list[EducationEntry] = Field(default_factory=list, description="Education background")
    projects: list[ProjectEntry] = Field(default_factory=list, description="Project experiences")
    skills: list[SkillEntry] = Field(default_factory=list, description="Technical skills")
    internships: list[InternshipEntry] = Field(default_factory=list, description="Internship experiences")
    awards: list[AwardEntry] = Field(default_factory=list, description="Awards and honors")
    summary: SummaryEntry | None = Field(None, description="Personal summary")


class ResumeStructureAPIResponse(BaseModel):
    code: int = Field(200, description="Response code")
    message: str = Field("success", description="Response message")
    data: ResumeStructureResponse | None = Field(None, description="Structured resume result")


class APIResponse(BaseModel):
    code: int = Field(200, description="Response code")
    message: str = Field("success", description="Response message")
    data: dict | None = Field(None, description="Response data")
