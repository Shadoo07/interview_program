from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text

from app.database import Base


class AnalysisHistory(Base):
    __tablename__ = "analysis_history"

    id = Column(Integer, primary_key=True, index=True)
    resume_filename = Column(String(255))
    raw_text = Column(Text)
    resume_data = Column(Text)
    jd_text = Column(Text)
    jd_data = Column(Text)
    match_result = Column(Text)
    diagnose_result = Column(Text)
    rewrite_result = Column(Text)
    interview_questions = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
