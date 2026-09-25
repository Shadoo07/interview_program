import json
from typing import Any

from sqlalchemy.orm import Session

from app.models.history import AnalysisHistory
from app.schemas.history_schema import HistoryRecord, HistorySaveRequest


def save_history(db: Session, request: HistorySaveRequest) -> int:
    history = AnalysisHistory(
        resume_filename=request.resume_filename,
        raw_text=request.raw_text,
        resume_data=json.dumps(request.resume_data) if request.resume_data else None,
        jd_text=request.jd_text,
        jd_data=json.dumps(request.jd_data) if request.jd_data else None,
        match_result=json.dumps(request.match_result) if request.match_result else None,
        diagnose_result=json.dumps(request.diagnose_result) if request.diagnose_result else None,
        rewrite_result=json.dumps(request.rewrite_result) if request.rewrite_result else None,
        interview_questions=json.dumps(request.interview_questions) if request.interview_questions else None
    )

    db.add(history)
    db.commit()
    db.refresh(history)

    return history.id


def get_history_list(db: Session, limit: int = 20) -> list[HistoryRecord]:
    records = db.query(AnalysisHistory).order_by(AnalysisHistory.created_at.desc()).limit(limit).all()
    return [_model_to_record(record) for record in records]


def get_history_detail(db: Session, history_id: int) -> HistoryRecord | None:
    record = db.query(AnalysisHistory).filter(AnalysisHistory.id == history_id).first()
    if record:
        return _model_to_record(record)
    return None


def delete_history(db: Session, history_id: int) -> bool:
    record = db.query(AnalysisHistory).filter(AnalysisHistory.id == history_id).first()
    if record:
        db.delete(record)
        db.commit()
        return True
    return False


def _model_to_record(model: AnalysisHistory) -> HistoryRecord:
    return HistoryRecord(
        id=model.id,
        resume_filename=model.resume_filename,
        raw_text=model.raw_text,
        resume_data=_parse_json(model.resume_data),
        jd_text=model.jd_text,
        jd_data=_parse_json(model.jd_data),
        match_result=_parse_json(model.match_result),
        diagnose_result=_parse_json(model.diagnose_result),
        rewrite_result=_parse_json(model.rewrite_result),
        interview_questions=_parse_json(model.interview_questions),
        created_at=model.created_at
    )


def _parse_json(data: str | None) -> dict[str, Any] | None:
    if not data:
        return None
    try:
        return json.loads(data)
    except json.JSONDecodeError:
        return None
